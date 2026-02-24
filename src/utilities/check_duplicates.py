"""Check for duplicate stamps in SQLite."""
from collections import Counter
from src.core.database import get_catalog_stamps

stamps = get_catalog_stamps()

# Check by colnect_id
id_counts = Counter(s.colnect_id for s in stamps)
duplicates_by_id = {k: v for k, v in id_counts.items() if v > 1}

# Check by title (might catch different IDs for same stamp)
title_counts = Counter(s.title for s in stamps)
duplicates_by_title = {k: v for k, v in title_counts.items() if v > 1}

print(f"Total stamps: {len(stamps)}")
print(f"\nDuplicate colnect_ids: {len(duplicates_by_id)}")
for cid, count in duplicates_by_id.items():
    print(f"  {cid}: {count} entries")

print(f"\nDuplicate titles: {len(duplicates_by_title)}")
for title, count in duplicates_by_title.items():
    # Find the stamps with this title
    matching = [s for s in stamps if s.title == title]
    print(f"  '{title[:50]}...'")
    for s in matching:
        print(f"    ID: {s.colnect_id}, Year: {s.year}, Country: {s.country}")
