import pandas as pd
from geopy.distance import geodesic
from scipy.spatial import cKDTree
import numpy as np

# ==============================
# CONFIGURATION
# ==============================
DISTANCE_THRESHOLD = 0.1  # km → flag if within 100 meters

# ==============================
# STEP 1: Load and clean data
# ==============================
print("📂 Loading data...")
df = pd.read_excel('Original Source\MaterData 04-02-26.xlsx', dtype=str)

# Convert coordinates to numeric
df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
df = df.dropna(subset=['Latitude', 'Longitude']).copy()

# Keep only secured shops
df['is_secured'] = df['Prospect Code'].notna() & (df['Prospect Code'].str.strip() != '')
secured = df[df['is_secured']].copy().reset_index(drop=True)

print(f"✅ Found {len(secured)} secured shops.")

if len(secured) < 2:
    print("⚠️ Not enough secured shops to compare.")
    exit()

# ==============================
# Helper: Scale longitude
# ==============================
def scale_lon(lat, lon):
    return lon * np.cos(np.radians(lat))

# ==============================
# STEP 2: Build KDTree for secured shops (self-comparison)
# ==============================
secured_scaled = np.column_stack([
    secured['Latitude'].values,
    scale_lon(secured['Latitude'].values, secured['Longitude'].values)
])
tree = cKDTree(secured_scaled)

# Query nearest neighbor (k=2: self + nearest other)
_, indices = tree.query(secured_scaled, k=2)
nearest_other_idx = indices[:, 1]  # skip self

# ==============================
# STEP 3: Compute exact distances and flag duplicates
# ==============================
results = []

for i in range(len(secured)):
    row = secured.iloc[i]
    other_row = secured.iloc[nearest_other_idx[i]]
    
    # Compute real distance
    p1 = (row['Latitude'], row['Longitude'])
    p2 = (other_row['Latitude'], other_row['Longitude'])
    distance_km = geodesic(p1, p2).kilometers
    
    # Name similarity check
    name1 = str(row['New Shop Name']).lower().strip()
    name2 = str(other_row['New Shop Name']).lower().strip()
    name_similar = (name1 in name2) or (name2 in name1)
    
    is_suspicious = (distance_km <= DISTANCE_THRESHOLD) and name_similar

    results.append({
        'Customer ID A': row['Customer ID'],
        'Shop Name A': row['New Shop Name'],
        'Prospect Code A': row['Prospect Code'],
        'Latitude A': row['Latitude'],
        'Longitude A': row['Longitude'],
        
        'Customer ID B': other_row['Customer ID'],
        'Shop Name B': other_row['New Shop Name'],
        'Prospect Code B': other_row['Prospect Code'],
        'Latitude B': other_row['Latitude'],
        'Longitude B': other_row['Longitude'],
        
        'Distance (km)': round(distance_km, 3),
        'Names Similar': name_similar,
        'Suspicious Duplicate': is_suspicious
    })

# ==============================
# STEP 4: Save only suspicious pairs
# ==============================
result_df = pd.DataFrame(results)

# Filter to only suspicious duplicates
suspicious_df = result_df[result_df['Suspicious Duplicate']].copy()

output_file = 'suspicious_secured_duplicates_04-02-26.xlsx'
suspicious_df.to_excel(output_file, index=False)

print(f"\n🔍 Found {len(suspicious_df)} suspicious duplicate pairs among secured shops.")
print(f"📁 Saved to '{output_file}'")

if not suspicious_df.empty:
    print("\n📊 Preview:")
    print(suspicious_df[['Customer ID A', 'Shop Name A', 'Customer ID B', 'Shop Name B', 'Distance (km)']].head())
else:
    print("✅ No suspicious duplicates found among secured shops.")