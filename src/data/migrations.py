"""
Database migrations to add card gameplay data.
"""
import sqlite3


def migrate_add_gameplay_fields(db_path: str = "data/collection.db"):
    """Add gameplay-related fields to cards table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(cards)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    migrations = []
    
    if 'mana_cost' not in existing_columns:
        migrations.append("ALTER TABLE cards ADD COLUMN mana_cost TEXT")
    
    if 'cmc' not in existing_columns:
        migrations.append("ALTER TABLE cards ADD COLUMN cmc REAL")
    
    if 'colors' not in existing_columns:
        migrations.append("ALTER TABLE cards ADD COLUMN colors TEXT")
    
    if 'color_identity' not in existing_columns:
        migrations.append("ALTER TABLE cards ADD COLUMN color_identity TEXT")
    
    if 'type_line' not in existing_columns:
        migrations.append("ALTER TABLE cards ADD COLUMN type_line TEXT")
    
    if 'card_types' not in existing_columns:
        migrations.append("ALTER TABLE cards ADD COLUMN card_types TEXT")
    
    if 'subtypes' not in existing_columns:
        migrations.append("ALTER TABLE cards ADD COLUMN subtypes TEXT")
    
    if 'oracle_text' not in existing_columns:
        migrations.append("ALTER TABLE cards ADD COLUMN oracle_text TEXT")
    
    # Execute migrations
    for migration in migrations:
        print(f"Executing: {migration}")
        cursor.execute(migration)
    
    conn.commit()
    conn.close()
    
    if migrations:
        print(f"✓ Added {len(migrations)} new columns")
    else:
        print("✓ All columns already exist")


if __name__ == "__main__":
    print("Running database migration...")
    migrate_add_gameplay_fields()
    print("Migration complete!")