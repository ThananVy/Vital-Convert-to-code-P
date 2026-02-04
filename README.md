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
