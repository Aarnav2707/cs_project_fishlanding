"""
Fish Landings and Coastal Pollution Analysis

This program analyzes the relationship between fish landings in Santa Barbara
and dissolved oxygen levels in coastal waters to examine the potential impact
of coastal pollution on fish populations.

Authors: Aarnav Rai and Cole Nicholson
Course: CSC-101, Prof. Anita Rathi
"""

import csv
import json
import os

from unicodedata import category

from FishLandings import get_all_fish_landings, FishLanding
from PollutionRecords import load_water_quality_csv, WaterQualityRecord
from DataAnalyzer import DataAnalyzer


def save_yearly_summary(analyzer: DataAnalyzer, filepath: str,category=None):
    """
    Save yearly summary data to a CSV file.
    
    Args:
        analyzer: DataAnalyzer instance with loaded data
        filepath: Path to output CSV file
    """
    joined_data = analyzer.get_joined_yearly_data(category)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['year', 'fish_pounds', 'avg_dissolved_oxygen'])
        writer.writeheader()
        writer.writerows(joined_data)
    
    print(f"Saved yearly summary to: {filepath}")


def save_metrics(analyzer: DataAnalyzer, filepath: str,category=None):
    """
    Save analysis metrics to a JSON file.
    
    Args:
        analyzer: DataAnalyzer instance with loaded data
        filepath: Path to output JSON file
    """
    correlation, n_years = analyzer.calc_pearson(category)
    
    metrics = {
        "pearson_correlation": round(correlation, 4),
        "years_analyzed": n_years,
        "interpretation": interpret_correlation(correlation)
    }

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Saved metrics to: {filepath}")


def interpret_correlation(r: float) -> str:
    """
    Interpret the Pearson correlation coefficient.
    
    Args:
        r: Correlation coefficient (-1 to 1)
    
    Returns:
        Human-readable interpretation string
    """
    abs_r = abs(r)
    
    if abs_r < 0.1:
        strength = "negligible"
    elif abs_r < 0.3:
        strength = "weak"
    elif abs_r < 0.5:
        strength = "moderate"
    elif abs_r < 0.7:
        strength = "strong"
    else:
        strength = "very strong"
    
    direction = "positive" if r > 0 else "negative"
    
    if abs_r < 0.1:
        return f"There is {strength} correlation between fish landings and dissolved oxygen levels."
    else:
        return (f"There is a {strength} {direction} correlation (r={r:.4f}) between "
                f"fish landings and dissolved oxygen levels.")


def visualize_trends(analyzer: DataAnalyzer, save_path: str = None,category=None):
    """
    Create a visualization showing fish landings and dissolved oxygen trends.
    
    Args:
        analyzer: DataAnalyzer instance with loaded data
        save_path: Optional path to save the figure
    """
    import matplotlib.pyplot as plt
    
    joined_data = analyzer.get_joined_yearly_data(category)
    
    if not joined_data:
        print("No overlapping data to visualize.")
        return
    
    years = [d['year'] for d in joined_data]
    fish_pounds = [d['fish_pounds'] for d in joined_data]
    oxygen_levels = [d['avg_dissolved_oxygen'] for d in joined_data]
    
    # Create figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))
    
    # Plot fish landings on primary y-axis
    color1 = '#2E86AB'  # Blue
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Fish Landings (millions of lbs)', color=color1, fontsize=12)
    line1 = ax1.plot(years, [p / 1_000_000 for p in fish_pounds], 
                     color=color1, linewidth=2, marker='o', markersize=6, label='Fish Landings')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_ylim(bottom=0)
    
    # Create secondary y-axis for dissolved oxygen
    ax2 = ax1.twinx()
    color2 = '#E94F37'  # Red
    ax2.set_ylabel('Avg Dissolved Oxygen (mg/L)', color=color2, fontsize=12)
    line2 = ax2.plot(years, oxygen_levels, color=color2, linewidth=2, 
                     marker='s', markersize=6, linestyle='--', label='Dissolved Oxygen')
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_ylim(bottom=0)
    
    # Add title and correlation info
    correlation, n_years = analyzer.calc_pearson(category)

    plt.title(f'Santa Barbara ({category}) Landings vs. Dissolved Oxygen Levels\n'
              f'Pearson Correlation: r = {correlation:.4f} (n = {n_years} years)\n'
              f'{interpret_correlation(correlation)}',
              fontsize=14, fontweight='bold')

    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')
    
    # Add grid
    ax1.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved visualization to: {save_path}")
    
    plt.show()


def print_analysis_report(analyzer: DataAnalyzer,category=None):
    """
    Print a detailed analysis report to the console.
    
    Args:
        analyzer: DataAnalyzer instance with loaded data
    """
    print("\n" + "=" * 60)
    print("FISH LANDINGS AND COASTAL POLLUTION ANALYSIS REPORT")
    print("Santa Barbara County, California")
    print("=" * 60)
    
    stats = analyzer.get_summary_stats(category)
    
    print(f"\n--- DATA SUMMARY ---")
    print(f"Fish landing records: {stats['total_fish_records']:,}")
    print(f"Water quality records: {stats['total_water_records']:,}")
    #print(f"Total fish landed: {stats['total_fish_pounds']:,} lbs")
    print(f"Total fish landed: {stats['total_fish_category_pounds']:,} lbs")
    print(f"Fish data years: {min(stats['fish_years'])} - {max(stats['fish_years'])}")
    print(f"Water data years: {min(stats['water_years'])} - {max(stats['water_years'])}")
    print(f"Overlapping years for analysis: {stats['common_years']}")
    
    correlation, n_years = analyzer.calc_pearson(category)
    print(f"\n--- CORRELATION ANALYSIS ---")
    print(f"Pearson correlation coefficient: {correlation:.4f}")
    print(f"Years analyzed: {n_years}")
    print(f"\nInterpretation: {interpret_correlation(correlation)}")
    
    # Show yearly summary
    joined_data = analyzer.get_joined_yearly_data(category)
    print(f"\n--- YEARLY SUMMARY (first 10 years) ---")
    print(f"{'Year':<8} {'Fish (lbs)':<15} {'Avg DO (mg/L)':<15}")
    print("-" * 40)
    for row in joined_data[:10]:
        print(f"{row['year']:<8} {row['fish_pounds']:>12,} {row['avg_dissolved_oxygen']:>12.2f}")
    
    if len(joined_data) > 10:
        print(f"... and {len(joined_data) - 10} more years")
    
    # Compare first and last years
    if len(joined_data) >= 2:
        first_year = joined_data[0]['year']
        last_year = joined_data[-1]['year']
        
        fish_comparison = analyzer.compare_total_landings_between_years(first_year, last_year)
        oxygen_comparison = analyzer.compare_oxygen_levels_between_years(first_year, last_year)
        
        print(f"\n--- TREND COMPARISON ({first_year} vs {last_year}) ---")
        print(f"Fish landings change: {fish_comparison['change']:+,} lbs "
              f"({fish_comparison['percent_change']:+.1f}%)" if fish_comparison['percent_change'] else "")
        print(f"Dissolved oxygen change: {oxygen_comparison['change']:+.2f} mg/L "
              f"({oxygen_comparison['percent_change']:+.1f}%)" if oxygen_comparison['percent_change'] else "")
    
    print("\n" + "=" * 60)


def main():
    """Main entry point for the analysis program."""
    print("=" * 60)
    print("Fish Landings and Coastal Pollution Analysis")
    print("Aarnav Rai and Cole Nicholson - CSC-101")
    print("=" * 60)
    category_types = ["Finfish","Crustaceans","Echinoderms","Mollusks"]
    # Load fish landings data (1980-2002)
    print("\nLoading fish landings data...")
    fish_data = get_all_fish_landings(1980, 2002)
    print(f"Total fish records loaded: {len(fish_data)}")
    
    # Load water quality data
    print("\nLoading water quality data...")
    water_data = load_water_quality_csv("field_results.csv", county="Santa Barbara")
    print(f"Total water quality records loaded: {len(water_data)}")
    
    if not fish_data or not water_data:
        print("Error: Could not load data. Please check file paths.")
        return
    
    # Create analyzer
    analyzer = DataAnalyzer(fish_data, water_data)


    for category in category_types:
        # Print analysis report
        print_analysis_report(analyzer,category)
    
        # Save outputs
        yearly_summary_path = "data/processed/yearly_summary_" + category + ".csv"
        results_path = "data/processed/results_" + category + ".csv"
        save_yearly_summary(analyzer, yearly_summary_path,category)
        save_metrics(analyzer,results_path, category)
    
        # Generate visualization
        print("\nGenerating visualization...")
        visualize_path="results/fish_oxygen_trends_" + category + ".png"
        visualize_trends(analyzer,visualize_path, category)
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
