"""Quick script to check SQLite data."""
from src.core.database import get_catalog_stamps

stamps = get_catalog_stamps()
print(f"Total stamps in SQLite: {len(stamps)}\n")
for s in stamps[:10]:
    print(f"ID: {s.colnect_id}")
    print(f"  Country: {s.country}")
    print(f"  Year: {s.year}")
    print(f"  Title: {s.title[:50]}...")
    print()
