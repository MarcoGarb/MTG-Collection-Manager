"""
Check CSV column names to fix the importer.
"""
import pandas as pd

csv_path = "data/all cards.csv"
df = pd.read_csv(csv_path)

print("=" * 60)
print("CSV COLUMNS FOUND:")
print("=" * 60)
for i, col in enumerate(df.columns, 1):
    print(f"{i:2}. '{col}'")

print("\n" + "=" * 60)
print("SAMPLE ROW (first card):")
print("=" * 60)
first_row = df.iloc[0]
for col in df.columns:
    print(f"{col:25} = {first_row[col]}")