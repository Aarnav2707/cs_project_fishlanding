"""
DataAnalyzer module for analyzing fish landings and water quality data.

This module provides the DataAnalyzer class which combines fish landing data
with water quality measurements to find correlations between fish populations
and dissolved oxygen levels.
"""

import math
from FishLandings import FishLanding
from PollutionRecords import WaterQualityRecord


class DataAnalyzer:
    """
    Analyzes fish landings and water quality data to find correlations.
    
    Attributes:
        fish_list: List of FishLanding objects
        water_list: List of WaterQualityRecord objects
    """
    
    def __init__(self, fish_list: list[FishLanding], water_list: list[WaterQualityRecord]):
        """
        Initialize the DataAnalyzer with fish and water quality data.
        
        Args:
            fish_list: List of FishLanding objects
            water_list: List of WaterQualityRecord objects
        """
        self.fish_list = fish_list
        self.water_list = water_list
    
    def total_fish_landings_per_year(self, category=None) -> dict[int, int]:
        """
        Calculate total fish landings (in pounds) for each year.
        
        Returns:
            Dictionary mapping year to total pounds landed
        """
        by_year = {}
        for landing in self.fish_list:
            if category:
                if landing.category != category:
                    continue
            if landing.year not in by_year:
                by_year[landing.year] = 0
            by_year[landing.year] += landing.pounds
        return by_year
    
    def average_fish_landings_per_year(self) -> dict[int, float]:
        """
        Calculate average fish landings per species for each year.
        
        Returns:
            Dictionary mapping year to average pounds per species
        """
        totals = {}
        counts = {}
        
        for landing in self.fish_list:
            if landing.year not in totals:
                totals[landing.year] = 0
                counts[landing.year] = 0
            totals[landing.year] += landing.pounds
            counts[landing.year] += 1
        
        return {year: totals[year] / counts[year] for year in totals}

    def total_fish_category_landings_overall(self, category=None) -> dict[int, int]:
        """
         Calculate total fish landings across all years.

        Returns:
            Dictionary mapping year to total pounds landed
        """
        total_pounds=0
        for landing in self.fish_list:
            if category:
                if landing.category != category:
                    continue
            total_pounds  += landing.pounds
        return total_pounds


    '''
    def total_fish_landings_overall(self, category=None) -> int:
        """
        Calculate total fish landings across all years.
        
        Returns:
            Total pounds landed across all years
        """
        return sum(landing.pounds for landing in self.fish_list)
    '''

    def average_oxygen_per_year(self) -> dict[int, float]:
        """
        Calculate average dissolved oxygen level for each year.
        
        Returns:
            Dictionary mapping year to average dissolved oxygen (mg/L)
        """
        totals = {}
        counts = {}
        
        for record in self.water_list:
            if record.year not in totals:
                totals[record.year] = 0.0
                counts[record.year] = 0
            totals[record.year] += record.dissolved_oxygen
            counts[record.year] += 1
        
        return {year: totals[year] / counts[year] for year in totals}
    
    def compare_species_between_years(self, year1: int, year2: int) -> dict:
        """
        Compare fish landings between two years by species.
        
        Args:
            year1: First year to compare
            year2: Second year to compare
        
        Returns:
            Dictionary with comparison results including species changes
        """
        year1_data = {}
        year2_data = {}
        
        for landing in self.fish_list:
            if landing.year == year1:
                year1_data[landing.species] = landing.pounds
            elif landing.year == year2:
                year2_data[landing.species] = landing.pounds
        
        all_species = set(year1_data.keys()) | set(year2_data.keys())
        
        comparison = {
            "year1": year1,
            "year2": year2,
            "year1_total": sum(year1_data.values()),
            "year2_total": sum(year2_data.values()),
            "species_changes": {}
        }
        
        for species in all_species:
            pounds1 = year1_data.get(species, 0)
            pounds2 = year2_data.get(species, 0)
            change = pounds2 - pounds1
            pct_change = ((pounds2 - pounds1) / pounds1 * 100) if pounds1 > 0 else None
            
            comparison["species_changes"][species] = {
                "year1_pounds": pounds1,
                "year2_pounds": pounds2,
                "change": change,
                "percent_change": pct_change
            }
        
        return comparison
    
    def compare_total_landings_between_years(self, year1: int, year2: int, category=None) -> dict:
        """
        Compare total fish landings between two years.
        
        Args:
            year1: First year
            year2: Second year
        
        Returns:
            Dictionary with total landings comparison
        """
        totals = self.total_fish_landings_per_year(category)
        
        total1 = totals.get(year1, 0)
        total2 = totals.get(year2, 0)
        change = total2 - total1
        pct_change = ((total2 - total1) / total1 * 100) if total1 > 0 else None
        
        return {
            "year1": year1,
            "year2": year2,
            "year1_total": total1,
            "year2_total": total2,
            "change": change,
            "percent_change": pct_change
        }
    
    def compare_oxygen_levels_between_years(self, year1: int, year2: int) -> dict:
        """
        Compare average dissolved oxygen levels between two years.
        
        Args:
            year1: First year
            year2: Second year
        
        Returns:
            Dictionary with oxygen level comparison
        """
        averages = self.average_oxygen_per_year()
        
        avg1 = averages.get(year1, 0)
        avg2 = averages.get(year2, 0)
        change = avg2 - avg1
        pct_change = ((avg2 - avg1) / avg1 * 100) if avg1 > 0 else None
        
        return {
            "year1": year1,
            "year2": year2,
            "year1_avg_oxygen": avg1,
            "year2_avg_oxygen": avg2,
            "change": change,
            "percent_change": pct_change
        }
    
    def calc_pearson(self, category=None) -> tuple[float, int]:
        """
        Calculate Pearson correlation coefficient between fish landings and dissolved oxygen.
        
        Uses only years where both fish and water quality data are available.
        
        Returns:
            Tuple of (correlation coefficient, number of years analyzed)
        """

        fish_by_year = self.total_fish_landings_per_year(category)
        oxygen_by_year = self.average_oxygen_per_year()
        
        # Find common years
        common_years = sorted(set(fish_by_year.keys()) & set(oxygen_by_year.keys()))
        
        if len(common_years) < 2:
            return (0.0, len(common_years))
        
        # Get paired values
        fish_values = [fish_by_year[year] for year in common_years]
        oxygen_values = [oxygen_by_year[year] for year in common_years]

        n = len(common_years)
        
        # Calculate means
        fish_mean = sum(fish_values) / n
        oxygen_mean = sum(oxygen_values) / n
        
        # Calculate Pearson correlation
        numerator = sum((fish_values[i] - fish_mean) * (oxygen_values[i] - oxygen_mean) 
                       for i in range(n))
        
        fish_variance = sum((x - fish_mean) ** 2 for x in fish_values)
        oxygen_variance = sum((x - oxygen_mean) ** 2 for x in oxygen_values)
        
        denominator = math.sqrt(fish_variance * oxygen_variance)
        
        if denominator == 0:
            return (0.0, n)
        
        correlation = numerator / denominator

        return (correlation, n)
    
    def get_joined_yearly_data(self, category=None) -> list[dict]:
        """
        Get combined yearly data for fish landings and water quality.
        
        Returns:
            List of dictionaries with year, fish_pounds, and avg_oxygen
        """
        fish_by_year = self.total_fish_landings_per_year(category)
        oxygen_by_year = self.average_oxygen_per_year()
        
        common_years = sorted(set(fish_by_year.keys()) & set(oxygen_by_year.keys()))
        
        joined_data = []
        for year in common_years:
            joined_data.append({
                "year": year,
                "fish_pounds": fish_by_year[year],
                "avg_dissolved_oxygen": round(oxygen_by_year[year], 2)
            })
        
        return joined_data
    
    def get_summary_stats(self,category=None) -> dict:
        """
        Get summary statistics for the analysis.
        
        Returns:
            Dictionary with summary statistics
        """
        fish_by_year = self.total_fish_landings_per_year(category)
        oxygen_by_year = self.average_oxygen_per_year()
        correlation, n_years = self.calc_pearson(category)
        
        return {
            "total_fish_records": len(self.fish_list),
            "total_water_records": len(self.water_list),
            "fish_years": sorted(fish_by_year.values()),
            "water_years": sorted(oxygen_by_year.keys()),
            "common_years": n_years,
            #"total_fish_pounds": self.total_fish_landings_overall(),
            "total_fish_category_pounds": self.total_fish_category_landings_overall("Finfish"),
            "pearson_correlation": round(correlation, 4)
        }


if __name__ == "__main__":
    # Test with sample data
    from FishLandings import get_fish_landings_in_specified_year
    from PollutionRecords import load_water_quality_csv
    
    print("Testing DataAnalyzer...")
    category = None
    # Load sample data
    fish_data = get_fish_landings_in_specified_year(1990)
    water_data = load_water_quality_csv("field_results.csv")
    
    if fish_data and water_data:
        analyzer = DataAnalyzer(fish_data, water_data)
        stats = analyzer.get_summary_stats(category)
        print(f"Summary: {stats}")
