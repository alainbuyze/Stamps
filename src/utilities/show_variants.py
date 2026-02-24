"""Show details of stamps with same titles to see differences."""
from src.core.database import get_catalog_stamps

stamps = get_catalog_stamps()

# Find stamps with title containing "Ariane" as example
ariane = [s for s in stamps if "Ariane" in s.title]
print("Ariane stamps (likely different denominations):")
for s in ariane:
    print(f"  ID: {s.colnect_id}")
    print(f"  URL: {s.colnect_url}")
    print(f"  Catalog codes: {s.catalog_codes}")
    print()
