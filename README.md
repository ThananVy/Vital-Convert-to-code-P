# Find Near Location Script

A Python script to identify trustworthy check-in locations by analyzing GPS coordinates and filtering outliers based on proximity to median/centroid locations.

## 📋 Purpose
Processes customer/store location data to:
- Calculate distances between recorded GPS coordinates
- Identify outlier check-ins (>20 meters from median location)
- Classify locations as **Trusted** (consistent coordinates) or **Fallback** (inconsistent/outlier coordinates)
- Generate cleaned dataset with location quality indicators

## ⚙️ Requirements
- Python 3.8+
- Required packages:
  ```bash
  pip install pandas geopy openpyxl

## 📥 Input File Requirements

### Supported Format
- Excel (.xlsx) recommended

### REQUIRED COLUMNS
Your Excel file **MUST** contain these exact column names:

| Column Name    | Description                                      | Example Values                     |
|----------------|--------------------------------------------------|------------------------------------|
| Customer ID    | Unique shop/customer identifier                  | SHOP001, CUST_123                 |
| New Shop Name  | Shop/store name                                  | ABC Grocery, XYZ Mart             |
| Latitude       | Decimal latitude coordinate                      | 11.5628, 11.5592                  |
| Longitude      | Decimal longitude coordinate                     | 104.9167, 104.9215                |
| Prospect Code  | Security status: blank = unsecured, filled = secured | P123 (secured) or *blank* (unsecured) |

> 🔑 **Critical Rules**:
> - Coordinates must be in **decimal degrees** format (e.g., 11.5628, NOT 11°33'46")
> - `Prospect Code` column determines shop status:
>   - **Blank/empty cell** = Unsecured shop (will be analyzed)
>   - **Any text/value** = Secured shop (used as reference for proximity checks)

## ▶️ How to Run
  ```bash
  uv run FindNearLocation.py
```
  ```bash
  uv run FindSusCodeP_CodeP.py
```

### Configuration (inside script)
Edit these values at the top of `FindNearLocation.py`:
```python
INPUT_FILE = "your_input_file.xlsx"   # Your input filename
OUTPUT_FILE = "shops_to_assign_P.xlsx"  # Output filename (only shops needing Code P)
DISTANCE_THRESHOLD_METERS = 50      # Shops closer than this are considered "too close"
```
