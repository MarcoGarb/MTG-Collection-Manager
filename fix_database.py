"""
Fix database schema by adding missing gameplay columns.
"""
import sqlite3
import os

db_path = "data/collection.db"

if not os.path.exists(db_path):
    print(f"❌ Database not found at: {db_path}")
    exit(1)

print(f"Updating database: {db_path}")
print("=" * 60)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get existing columns
cursor.execute("PRAGMA table_info(cards)")
existing_columns = [row[1] for row in cursor.fetchall()]

print(f"\nExisting columns ({len(existing_columns)}):")
for col in existing_columns:
    print(f"  - {col}")

# Define new columns to add
new_columns = {
    'mana_cost': 'TEXT',
    'cmc': 'REAL',
    'colors': 'TEXT',
    'color_identity': 'TEXT',
    'type_line': 'TEXT',
    'card_types': 'TEXT',
    'subtypes': 'TEXT',
    'oracle_text': 'TEXT'
}

print(f"\nAdding missing columns...")
print("-" * 60)

added = 0
for column_name, column_type in new_columns.items():
    if column_name not in existing_columns:
        try:
            sql = f"ALTER TABLE cards ADD COLUMN {column_name} {column_type}"
            print(f"  Adding: {column_name} ({column_type})")
            cursor.execute(sql)
            added += 1
        except Exception as e:
            print(f"  ⚠ Error adding {column_name}: {e}")
    else:
        print(f"  ✓ Already exists: {column_name}")

conn.commit()

# Verify columns were added
cursor.execute("PRAGMA table_info(cards)")
final_columns = [row[1] for row in cursor.fetchall()]

print("\n" + "=" * 60)
print(f"Final column count: {len(final_columns)}")
print(f"Added {added} new columns")

# Check if all gameplay columns exist
missing = []
for col in new_columns.keys():
    if col not in final_columns:
        missing.append(col)

if missing:
    print(f"\n❌ Still missing columns: {', '.join(missing)}")
else:
    print(f"\n✅ All gameplay columns exist!")

conn.close()

print("\nDatabase update complete!")