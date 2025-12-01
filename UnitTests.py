import unittest
import tempfile
import csv
import json
import io
import os
from contextlib import redirect_stdout
from unittest.mock import patch

import matplotlib
matplotlib.use("Agg")  # non-GUI backend for testing

from DataAnalyzer import DataAnalyzer
from FishLandings import (
    FishLanding,
    get_fish_landings_in_specified_year,
    get_all_fish_landings,
    get_landings_by_year,
)
from PollutionRecords import (
    WaterQualityRecord,
    load_water_quality_csv,
    get_oxygen_records_by_year,
)

# Adjust this import if your main script has a different filename
from main import (
    save_yearly_summary,
    save_metrics,
    interpret_correlation,
    visualize_trends,
    print_analysis_report,
)


# ---------- helpers ----------

def make_sample_analyzer():
    fish_list = [
        FishLanding("Finfish", 2000, "Anchovy", 100),
        FishLanding("Finfish", 2000, "Sardine", 300),
        FishLanding("Crustaceans", 2001, "Crab", 500),
        FishLanding("Finfish", 2001, "Anchovy", 200),
        FishLanding("Finfish", 2002, "Tuna", 400),
    ]

    water_list = [
        WaterQualityRecord("S1", "2000-06-01 00:00:00", 6.0, None, 2000),
        WaterQualityRecord("S2", "2000-07-01 00:00:00", 4.0, None, 2000),
        WaterQualityRecord("S1", "2001-06-01 00:00:00", 5.0, None, 2001),
        WaterQualityRecord("S1", "2002-06-01 00:00:00", 7.0, None, 2002),
        WaterQualityRecord("S2", "2002-07-01 00:00:00", 5.0, None, 2002),
    ]

    analyzer = DataAnalyzer(fish_list, water_list)
    return analyzer, fish_list, water_list


def make_small_analyzer():
    fish = [
        FishLanding("Finfish", 2000, "A", 100),
        FishLanding("Finfish", 2001, "A", 200),
    ]
    water = [
        WaterQualityRecord("S1", "2000-01-01 00:00:00", 5.0, None, 2000),
        WaterQualityRecord("S1", "2001-01-01 00:00:00", 6.0, None, 2001),
    ]
    return DataAnalyzer(fish, water)


# ---------- DataAnalyzer tests ----------

class TestDataAnalyzer(unittest.TestCase):

    def test_total_fish_landings_per_year_all(self):
        analyzer, _, _ = make_sample_analyzer()
        totals = analyzer.total_fish_landings_per_year()
        self.assertEqual(totals, {2000: 400, 2001: 700, 2002: 400})

    def test_total_fish_landings_per_year_category(self):
        analyzer, _, _ = make_sample_analyzer()
        totals = analyzer.total_fish_landings_per_year("Finfish")
        self.assertEqual(totals, {2000: 400, 2001: 200, 2002: 400})

    def test_average_fish_landings_per_year(self):
        analyzer, _, _ = make_sample_analyzer()
        avg = analyzer.average_fish_landings_per_year()
        self.assertEqual(avg[2000], 200.0)  # (100 + 300) / 2
        self.assertEqual(avg[2001], 350.0)  # (500 + 200) / 2
        self.assertEqual(avg[2002], 400.0)  # 400 / 1

    def test_total_fish_category_landings_overall(self):
        analyzer, _, _ = make_sample_analyzer()
        total_all = analyzer.total_fish_category_landings_overall()
        self.assertEqual(total_all, 1500)  # 100+300+500+200+400
        total_finfish = analyzer.total_fish_category_landings_overall("Finfish")
        self.assertEqual(total_finfish, 1000)  # 100+300+200+400

    def test_average_oxygen_per_year(self):
        analyzer, _, _ = make_sample_analyzer()
        oxy = analyzer.average_oxygen_per_year()
        self.assertEqual(oxy[2000], 5.0)  # (6+4)/2
        self.assertEqual(oxy[2001], 5.0)
        self.assertEqual(oxy[2002], 6.0)  # (7+5)/2

    def test_compare_species_between_years(self):
        analyzer, _, _ = make_sample_analyzer()
        comp = analyzer.compare_species_between_years(2000, 2001)

        self.assertEqual(comp["year1"], 2000)
        self.assertEqual(comp["year2"], 2001)
        self.assertEqual(comp["year1_total"], 400)
        self.assertEqual(comp["year2_total"], 700)

        changes = comp["species_changes"]

        # Anchovy
        self.assertEqual(changes["Anchovy"]["year1_pounds"], 100)
        self.assertEqual(changes["Anchovy"]["year2_pounds"], 200)
        self.assertEqual(changes["Anchovy"]["change"], 100)
        self.assertEqual(changes["Anchovy"]["percent_change"], 100.0)

        # Sardine only in 2000
        self.assertEqual(changes["Sardine"]["year1_pounds"], 300)
        self.assertEqual(changes["Sardine"]["year2_pounds"], 0)
        self.assertEqual(changes["Sardine"]["change"], -300)

        # Crab only in 2001
        self.assertEqual(changes["Crab"]["year1_pounds"], 0)
        self.assertEqual(changes["Crab"]["year2_pounds"], 500)
        self.assertEqual(changes["Crab"]["change"], 500)
        self.assertIsNone(changes["Crab"]["percent_change"])

    def test_compare_total_landings_between_years(self):
        analyzer, _, _ = make_sample_analyzer()
        comp = analyzer.compare_total_landings_between_years(2000, 2001)
        self.assertEqual(comp["year1_total"], 400)
        self.assertEqual(comp["year2_total"], 700)
        self.assertEqual(comp["change"], 300)
        self.assertEqual(comp["percent_change"], 75.0)

    def test_compare_total_landings_between_years_category(self):
        analyzer, _, _ = make_sample_analyzer()
        comp = analyzer.compare_total_landings_between_years(2000, 2001, "Finfish")
        self.assertEqual(comp["year1_total"], 400)
        self.assertEqual(comp["year2_total"], 200)
        self.assertEqual(comp["change"], -200)
        self.assertEqual(comp["percent_change"], -50.0)

    def test_compare_oxygen_levels_between_years(self):
        analyzer, _, _ = make_sample_analyzer()
        comp = analyzer.compare_oxygen_levels_between_years(2000, 2002)
        self.assertEqual(comp["year1_avg_oxygen"], 5.0)
        self.assertEqual(comp["year2_avg_oxygen"], 6.0)
        self.assertEqual(comp["change"], 1.0)
        self.assertEqual(comp["percent_change"], 20.0)

    def test_calc_pearson_linear_positive(self):
        fish = [
            FishLanding("Finfish", 2000, "A", 10),
            FishLanding("Finfish", 2001, "A", 20),
            FishLanding("Finfish", 2002, "A", 30),
        ]
        water = [
            WaterQualityRecord("S1", "2000", 1.0, None, 2000),
            WaterQualityRecord("S1", "2001", 2.0, None, 2001),
            WaterQualityRecord("S1", "2002", 3.0, None, 2002),
        ]
        analyzer = DataAnalyzer(fish, water)
        r, n = analyzer.calc_pearson()
        self.assertEqual(n, 3)
        self.assertAlmostEqual(r, 1.0, places=7)

    def test_calc_pearson_zero_variance(self):
        analyzer, _, _ = make_sample_analyzer()
        for r in analyzer.water_list:
            r.dissolved_oxygen = 5.0
        r, n = analyzer.calc_pearson()
        self.assertEqual(n, 3)
        self.assertEqual(r, 0.0)

    def test_get_joined_yearly_data(self):
        analyzer, _, _ = make_sample_analyzer()
        joined = analyzer.get_joined_yearly_data()
        years = [row["year"] for row in joined]
        self.assertEqual(years, [2000, 2001, 2002])

    def test_get_summary_stats(self):
        analyzer, fish_list, water_list = make_sample_analyzer()
        stats = analyzer.get_summary_stats()
        self.assertEqual(stats["total_fish_records"], len(fish_list))
        self.assertEqual(stats["total_water_records"], len(water_list))
        self.assertEqual(stats["common_years"], 3)
        self.assertTrue(isinstance(stats["pearson_correlation"], float))


# ---------- FishLandings tests ----------

class TestFishLandings(unittest.TestCase):

    def test_fishlanding_repr(self):
        fl = FishLanding("Finfish", 1999, "Tuna", 500)
        rep = repr(fl)
        self.assertIn("Finfish", rep)
        self.assertIn("Tuna", rep)
        self.assertIn("500", rep)

    def test_get_landings_by_year(self):
        landings = [
            FishLanding("Finfish", 2000, "A", 10),
            FishLanding("Finfish", 2000, "B", 20),
            FishLanding("Finfish", 2001, "C", 30),
        ]
        by_year = get_landings_by_year(landings)
        self.assertEqual(by_year, {2000: 30, 2001: 30})

    def test_get_fish_landings_in_specified_year_invalid(self):
        data = get_fish_landings_in_specified_year(1979)
        self.assertIsNone(data)
        data = get_fish_landings_in_specified_year(2003)
        self.assertIsNone(data)

    @patch("FishLandings.pd.read_excel")
    def test_get_fish_landings_in_specified_year_valid(self, mock_read_excel):
        import pandas as pd

        df = pd.DataFrame(
            [
                {"Category": "Finfish Something", "Species": "Anchovy", "Total Landings": 100},
                {"Category": "Finfish Something", "Species": "Sardine", "Total Landings": "Confidential"},
                {"Category": "Total Finfish", "Species": "Anchovy", "Total Landings": 999},
                {"Category": "Finfish Something", "Species": "", "Total Landings": 50},
                {"Category": "Finfish Something", "Species": "SkipZero", "Total Landings": 0},
            ]
        )
        mock_read_excel.return_value = df

        result = get_fish_landings_in_specified_year(1990)
        self.assertEqual(len(result), 1)
        rec = result[0]
        self.assertEqual(rec.year, 1990)
        self.assertEqual(rec.category, "Something")
        self.assertEqual(rec.species, "Anchovy")
        self.assertEqual(rec.pounds, 100)

    @patch("FishLandings.get_fish_landings_in_specified_year")
    def test_get_all_fish_landings(self, mock_get_year):
        mock_get_year.side_effect = [
            [FishLanding("Finfish", 1980, "A", 10)],
            [FishLanding("Finfish", 1981, "B", 20), FishLanding("Finfish", 1981, "C", 30)],
            None,  # 1982
        ]
        all_landings = get_all_fish_landings(1980, 1982)
        self.assertEqual(len(all_landings), 3)
        years = sorted({l.year for l in all_landings})
        self.assertEqual(years, [1980, 1981])
        total = sum(l.pounds for l in all_landings)
        self.assertEqual(total, 60)


# ---------- PollutionRecords tests ----------

class TestPollutionRecords(unittest.TestCase):

    def test_water_quality_record_repr_and_is_low(self):
        rec = WaterQualityRecord("Station A", "2000-01-01 00:00:00", 4.5, None, 2000)
        r = repr(rec)
        self.assertIn("Station A", r)
        self.assertTrue(rec.is_low_oxygen())
        self.assertFalse(rec.is_low_oxygen(threshold=4.0))

    def test_get_oxygen_records_by_year(self):
        records = [
            WaterQualityRecord("A", "2000", 5.0, None, 2000),
            WaterQualityRecord("A", "2000", 6.0, None, 2000),
            WaterQualityRecord("A", "2001", 7.0, None, 2001),
        ]
        by_year = get_oxygen_records_by_year(records)
        self.assertEqual(by_year[2000], [5.0, 6.0])
        self.assertEqual(by_year[2001], [7.0])

    def test_load_water_quality_csv_filters_and_parses(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "field_results.csv")
            fieldnames = ["county_name", "parameter", "fdr_result", "sample_date", "station_name"]
            rows = [
                {
                    "county_name": "Santa Barbara",
                    "parameter": "DissolvedOxygen",
                    "fdr_result": "5.5",
                    "sample_date": "2000-01-02 10:00:00",
                    "station_name": "Station A",
                },
                {
                    "county_name": "Santa Barbara",
                    "parameter": "Temperature",
                    "fdr_result": "10.0",
                    "sample_date": "2000-01-02 10:00:00",
                    "station_name": "Station B",
                },
                {
                    "county_name": "Ventura",
                    "parameter": "DissolvedOxygen",
                    "fdr_result": "6.0",
                    "sample_date": "2001-01-02 10:00:00",
                    "station_name": "Station C",
                },
                {
                    "county_name": "Santa Barbara",
                    "parameter": "DissolvedOxygen",
                    "fdr_result": "not-a-number",
                    "sample_date": "2001-01-02 10:00:00",
                    "station_name": "Station D",
                },
            ]
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)

            records = load_water_quality_csv(path, county="Santa Barbara")
            self.assertEqual(len(records), 1)
            rec = records[0]
            self.assertEqual(rec.station_name, "Station A")
            self.assertEqual(rec.dissolved_oxygen, 5.5)
            self.assertEqual(rec.year, 2000)


# ---------- main helper functions tests ----------

class TestMainHelpers(unittest.TestCase):

    def test_interpret_correlation(self):
        self.assertIn("negligible", interpret_correlation(0.0))
        self.assertIn("weak", interpret_correlation(0.2))
        self.assertIn("moderate", interpret_correlation(0.4))
        self.assertIn("strong", interpret_correlation(0.6))
        self.assertIn("very strong", interpret_correlation(0.8))
        self.assertIn("positive", interpret_correlation(0.5))
        self.assertIn("negative", interpret_correlation(-0.5))

    def test_save_yearly_summary_creates_csv(self):
        analyzer = make_small_analyzer()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "data", "processed", "yearly_summary_test.csv")
            save_yearly_summary(analyzer, out_path)
            self.assertTrue(os.path.exists(out_path))

            with open(out_path, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            self.assertEqual(len(rows), 2)
            years = sorted(int(r["year"]) for r in rows)
            self.assertEqual(years, [2000, 2001])

    def test_save_metrics_creates_json(self):
        analyzer = make_small_analyzer()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "data", "processed", "metrics_test.json")
            save_metrics(analyzer, out_path)
            self.assertTrue(os.path.exists(out_path))

            with open(out_path) as f:
                data = json.load(f)

            self.assertIn("pearson_correlation", data)
            self.assertIn("years_analyzed", data)
            self.assertIn("interpretation", data)

    def test_visualize_trends_saves_png(self):
        analyzer = make_small_analyzer()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "results", "plot.png")

            # prevent GUI popups
            with patch("matplotlib.pyplot.show"):
                visualize_trends(analyzer, save_path=out_path)

            self.assertTrue(os.path.exists(out_path))

    def test_print_analysis_report_outputs_text(self):
        analyzer = make_small_analyzer()
        buf = io.StringIO()
        with redirect_stdout(buf):
            print_analysis_report(analyzer)
        output = buf.getvalue()
        self.assertIn("FISH LANDINGS AND COASTAL POLLUTION ANALYSIS REPORT", output)
        self.assertIn("CORRELATION ANALYSIS", output)
        self.assertIn("YEARLY SUMMARY", output)


if __name__ == "__main__":
    unittest.main()