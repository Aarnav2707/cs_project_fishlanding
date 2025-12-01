from typing import Any
import pandas as pd

class FishLanding:
    """Class representing a fish landing record for a specific species and year."""
    
    def __init__(self, category: str, year: int, species: str, pounds: int):
        self.category = category
        self.year = year
        self.species = species
        self.pounds = pounds
    
    def __repr__(self):
        return (f"FishLanding(category={self.category}, year={self.year}, "
                f"species={self.species}, pounds={self.pounds})")


def get_fish_landings_in_specified_year(year: int) -> list[FishLanding] | None:
    """
    Load fish landings data for a specified year from the corresponding Excel file.
    
    Uses the 'Total Landings' column (column O) for more complete data, as monthly
    columns often contain 'Confidential' values.
    
    Args:
        year: Year to load (must be between 1980 and 2002)
    
    Returns:
        List of FishLanding objects, or None if year is invalid
    """
    if year < 1980 or year > 2002:
        print(f"Invalid year: {year}. Must be between 1980 and 2002.")
        return None
    
    results = []
    data_table = pd.read_excel(f"MonthlyPoundsSantaBarbara_{year}.xlsx")
    
    for index, row in data_table.iterrows():
        category = row["Category"]
        species = row.get("Species", "")
        
        # Skip summary rows (they don't have species)
        if pd.isna(species) or species == "":
            continue
        
        # Skip if category is a total/summary row
        if "Total" in str(category) or "Other" in str(category):
            continue

        category = category.split()[-1]
        # Get total landings from the "Total Landings" column
        total_landings = row.get("Total Landings", 0)
        
        # Skip if total is Confidential or not a valid number
        if total_landings == "Confidential" or pd.isna(total_landings):
            continue
        
        try:
            pounds = int(total_landings)
        except (ValueError, TypeError):
            continue
        
        # Skip zero landings
        if pounds <= 0:
            continue
        
        results.append(FishLanding(category, year, species, pounds))
    
    return results


def get_all_fish_landings(start_year: int = 1980, end_year: int = 2002) -> list[FishLanding]:
    """
    Load fish landings data for all years in the specified range.
    
    Args:
        start_year: First year to load (default 1980)
        end_year: Last year to load (default 2002)
    
    Returns:
        List of all FishLanding objects across all years
    """
    all_landings = []
    
    for year in range(start_year, end_year + 1):
        year_landings = get_fish_landings_in_specified_year(year)
        if year_landings:
            all_landings.extend(year_landings)
            print(f"  Loaded {len(year_landings)} species records for {year}")
    
    return all_landings


def get_landings_by_year(landings: list[FishLanding]) -> dict[int, int]:
    """
    Aggregate fish landings by year (total pounds per year).
    
    Args:
        landings: List of FishLanding objects
    
    Returns:
        Dictionary mapping year to total pounds
    """
    by_year = {}
    for landing in landings:
        if landing.year not in by_year:
            by_year[landing.year] = 0
        by_year[landing.year] += landing.pounds
    return by_year


if __name__ == "__main__":
    # Test loading a single year
    '''
    https://wildlife.ca.gov/Conservation/Marine/Data-Management-Research/MFDE/Commercial-Landings
    '''
    print("Testing : Loading 1990 data:")
    landings_1990 = get_fish_landings_in_specified_year(1990)
    if landings_1990:
        print(f"  Found {len(landings_1990)} species with data")
        total = sum(l.pounds for l in landings_1990)
        print(f"  Total pounds: {total:,}")
        print("\n  Top 5 species by pounds:")
        sorted_landings = sorted(landings_1990, key=lambda x: x.pounds, reverse=True)[:5]
        for l in sorted_landings:
            print(f"    {l.species}: {l.pounds:,} lbs")
