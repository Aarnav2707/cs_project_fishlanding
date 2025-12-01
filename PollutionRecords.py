import csv
from datetime import datetime

class WaterQualityRecord:
    """Class containing water quality measurement data."""
    
    def __init__(self, station_name: str, date: str, dissolved_oxygen: float,
                 water_temp: float | None, year: int):
        self.station_name = station_name
        self.date = date
        self.dissolved_oxygen = dissolved_oxygen
        self.water_temp = water_temp
        self.year = year
    
    def __repr__(self):
        return (f"WaterQualityRecord(station={self.station_name}, "
                f"year={self.year}, DO={self.dissolved_oxygen} mg/L)")
    
    def is_low_oxygen(self, threshold: float = 5.0) -> bool:
        """Returns True if dissolved oxygen is below the threshold (default 5.0 mg/L)."""
        return self.dissolved_oxygen < threshold


def load_water_quality_csv(filepath: str, county: str = "Santa Barbara") -> list[WaterQualityRecord]:
    """
    Load water quality data from CSV file, filtering by county and DissolvedOxygen parameter.
    
    Args:
        filepath: Path to the field_results CSV file
        county: County name to filter by (default: "Santa Barbara")
    
    Returns:
        List of WaterQualityRecord objects
    """
    records = []
    
    with open(filepath, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            # Filter by county
            if row['county_name'] != county:
                continue
            
            # Filter by DissolvedOxygen parameter
            if row['parameter'] != 'DissolvedOxygen':
                continue
            
            # Skip if no valid result
            try:
                dissolved_oxygen = float(row['fdr_result'])
            except (ValueError, TypeError):
                continue
            
            # Parse date to extract year
            try:
                date_str = row['sample_date']
                # Date format: "1985-02-12 10:50:00"
                date_obj = datetime.strptime(date_str.split()[0], '%Y-%m-%d')
                year = date_obj.year
            except (ValueError, IndexError):
                continue
            
            # Get water temperature if available (from same sample would need separate lookup)
            # For now, we'll set it to None as temp is in separate rows
            water_temp = None
            
            station_name = row['station_name'].strip()
            
            record = WaterQualityRecord(
                station_name=station_name,
                date=date_str,
                dissolved_oxygen=dissolved_oxygen,
                water_temp=water_temp,
                year=year
            )
            records.append(record)
    
    return records


def get_oxygen_records_by_year(records: list[WaterQualityRecord]) -> dict[int, list[float]]:
    """
    Group dissolved oxygen values by year.
    
    Args:
        records: List of WaterQualityRecord objects
    
    Returns:
        Dictionary mapping year to list of dissolved oxygen values
    """
    by_year = {}
    for record in records:
        if record.year not in by_year:
            by_year[record.year] = []
        by_year[record.year].append(record.dissolved_oxygen)
    return by_year


if __name__ == "__main__":
    # Test loading
    records = load_water_quality_csv("field_results.csv")
    print(f" Testing : Loaded {len(records)} Santa Barbara dissolved oxygen records")
    
    by_year = get_oxygen_records_by_year(records)
    print(f"\nYears with data: {sorted(by_year.keys())}")
    
    for year in sorted(by_year.keys())[:5]:
        values = by_year[year]
        avg = sum(values) / len(values)
        print(f"  {year}: {len(values)} samples, avg DO = {avg:.2f} mg/L")
