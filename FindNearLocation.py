import pandas as pd
from geopy.distance import geodesic
from scipy.spatial import cKDTree
import numpy as np

# ==============================
# CONFIGURATION (you can adjust these)
# ==============================
DISTANCE_THRESHOLD_UNSEC = 0.1  # km → flag unsecured duplicates within 100 meters
DISTANCE_THRESHOLD_SECURE = 50.0  # km → only consider secured shops within this range (optional, not enforced yet)

# ==============================
# STEP 1: Load and clean data
# ==============================
print("📂 Loading data...")
df = pd.read_excel('Original Source\MaterData 04-02-26.xlsx', dtype=str)

# Convert coordinates to numeric
df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
df = df.dropna(subset=['Latitude', 'Longitude']).copy()

# Identify secured vs unsecured
df['is_secured'] = df['Prospect Code'].notna() & (df['Prospect Code'].str.strip() != '')
secured = df[df['is_secured']].copy()
unsecured = df[~df['is_secured']].copy()

print(f"✅ Found {len(secured)} secured shops and {len(unsecured)} unsecured shops.")

if unsecured.empty:
    print("⚠️ No unsecured shops to process.")
    exit()

# Reset index for safe iteration
unsecured = unsecured.reset_index(drop=True)

# ==============================
# Helper: Scale longitude for spatial indexing
# ==============================
def scale_lon(lat, lon):
    """Scale longitude by cosine of latitude to approximate equal-distance grid."""
    return lon * np.cos(np.radians(lat))

# ==============================
# STEP 2: Build KDTree for SECURED shops
# ==============================
if not secured.empty:
    secured_scaled = np.column_stack([
        secured['Latitude'].values,
        scale_lon(secured['Latitude'].values, secured['Longitude'].values)
    ])
    tree_secured = cKDTree(secured_scaled)
else:
    tree_secured = None

# ==============================
# STEP 3: Process each unsecured shop
# ==============================
results = []

if not secured.empty:
    # Scale unsecured coords
    unsecured_scaled = np.column_stack([
        unsecured['Latitude'].values,
        scale_lon(unsecured['Latitude'].values, unsecured['Longitude'].values)
    ])

    # Query top 5 secured candidates
    distances_5, indices_5 = tree_secured.query(unsecured_scaled, k=5)

    for idx_pos in range(len(unsecured)):
        row = unsecured.iloc[idx_pos]
        shop_point = (row['Latitude'], row['Longitude'])

        # Find true closest among top 5
        min_dist = float('inf')
        best_sec_row = None

        for idx in indices_5[idx_pos]:
            sec_row = secured.iloc[idx]
            sec_point = (sec_row['Latitude'], sec_row['Longitude'])
            dist = geodesic(shop_point, sec_point).kilometers
            if dist < min_dist:
                min_dist = dist
                best_sec_row = sec_row

        # Name similarity check
        shop_name = str(row['New Shop Name']).lower().strip()
        sec_name = str(best_sec_row['New Shop Name']).lower().strip()
        name_similar = (shop_name in sec_name) or (sec_name in shop_name)

        recommendation = "Flag as Suspicious" if name_similar else "Assign Code P"

        results.append({
            'Customer ID': row['Customer ID'],
            'New Shop Name': row['New Shop Name'],
            'Latitude': row['Latitude'],
            'Longitude': row['Longitude'],
            'closest_secured_id': best_sec_row['Customer ID'],
            'closest_secured_name': best_sec_row['New Shop Name'],
            'distance_to_secured_km': round(min_dist, 3),
            'recommendation': recommendation
        })
else:
    # No secured shops → fill with placeholders
    for idx_pos in range(len(unsecured)):
        row = unsecured.iloc[idx_pos]
        results.append({
            'Customer ID': row['Customer ID'],
            'New Shop Name': row['New Shop Name'],
            'Latitude': row['Latitude'],
            'Longitude': row['Longitude'],
            'closest_secured_id': None,
            'closest_secured_name': None,
            'distance_to_secured_km': None,
            'recommendation': "No secured shops available"
        })

# Convert to DataFrame
result_df = pd.DataFrame(results)

# ==============================
# STEP 4: Check for duplicates WITHIN unsecured shops
# ==============================
print("🔍 Checking for duplicates among unsecured shops...")

if len(unsecured) > 1:
    unsecured_scaled_self = np.column_stack([
        unsecured['Latitude'].values,
        scale_lon(unsecured['Latitude'].values, unsecured['Longitude'].values)
    ])
    tree_unsec = cKDTree(unsecured_scaled_self)

    # k=2: first is self, second is nearest other
    _, indices_self = tree_unsec.query(unsecured_scaled_self, k=2)
    nearest_other_idx = indices_self[:, 1]

    # Compute exact distances
    unsec_distances = []
    for i in range(len(unsecured)):
        p1 = (unsecured.iloc[i]['Latitude'], unsecured.iloc[i]['Longitude'])
        p2 = (unsecured.iloc[nearest_other_idx[i]]['Latitude'], unsecured.iloc[nearest_other_idx[i]]['Longitude'])
        d = geodesic(p1, p2).kilometers
        unsec_distances.append(d)

    # Add to result
    result_df['nearest_unsec_id'] = unsecured.iloc[nearest_other_idx]['Customer ID'].values
    result_df['nearest_unsec_name'] = unsecured.iloc[nearest_other_idx]['New Shop Name'].values
    result_df['distance_to_nearest_unsec_km'] = np.round(unsec_distances, 3)

    # Flag unsecured duplicates
    def is_unsec_duplicate(row):
        if pd.isna(row['distance_to_nearest_unsec_km']):
            return False
        if row['distance_to_nearest_unsec_km'] > DISTANCE_THRESHOLD_UNSEC:
            return False
        name1 = str(row['New Shop Name']).lower().strip()
        name2 = str(row['nearest_unsec_name']).lower().strip()
        return (name1 in name2) or (name2 in name1)

    result_df['is_unsec_duplicate'] = result_df.apply(is_unsec_duplicate, axis=1)

    # Update final recommendation
    def update_final_recommendation(row):
        if row['is_unsec_duplicate']:
            return "Flag as Unsecured Duplicate"
        return row['recommendation']

    result_df['recommendation'] = result_df.apply(update_final_recommendation, axis=1)

else:
    result_df['nearest_unsec_id'] = None
    result_df['nearest_unsec_name'] = None
    result_df['distance_to_nearest_unsec_km'] = None
    result_df['is_unsec_duplicate'] = False

# ==============================
# STEP 5: Save results
# ==============================
output_file = 'SuspectMasterData 04-02-26.xlsx'
result_df.to_excel(output_file, index=False)

print(f"\n🎉 Done! Results saved to '{output_file}'")
print("\n📊 Preview:")
print(result_df[['Customer ID', 'New Shop Name', 'recommendation', 'distance_to_secured_km', 'distance_to_nearest_unsec_km']].head(10))