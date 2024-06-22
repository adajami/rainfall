import os
import geopandas as gpd
import xarray as xr
import rioxarray
import numpy as np
import pandas as pd
import json

# Load simplified administrative boundaries
admin_boundaries = gpd.read_file("geoBoundaries-MOZ-ADM2_simplified.geojson")

# Load STAC metadata for rainfall
with open("rfb_blended_moz_dekad.json") as f:
    rainfall_stac_metadata = json.load(f)

# Extract the asset URL for rfb band
# rfb_url = rainfall_stac_metadata['item_assets']['rfb'] #['href']

rainfall_folder = 'rfb_blended_moz_dekad'
file_paths = []
# List all files in the rainfall_folder
for filename in os.listdir(rainfall_folder):
    if 'd3.tif' in filename:
        # Construct the full path using os.path.join
        full_path = os.path.join(rainfall_folder, filename)
        file_paths.append(full_path)

# Load blended rainfall data using the rfb URL
rainfall_ds = xr.open_rasterio(file_paths)

# Compute 95th percentile for historical data (1989-2019)
historical_rainfall = rainfall_ds.sel(time=slice('1989-01-01', '2019-12-31'))
percentile_95 = historical_rainfall.quantile(0.95, dim='time')

# Extract rainfall for 3rd dekad of March 2024
rainfall_2024_03_21 = rainfall_ds.sel(time='2024-03-21')

# Calculate average rainfall over admin-2 boundaries for both datasets
admin_boundaries = admin_boundaries.to_crs(rainfall_2024_03_21.rio.crs)
rainfall_2024_avg = rainfall_2024_03_21.rio.clip(admin_boundaries.geometry).mean(dim=['x', 'y'])
percentile_95_avg = percentile_95.rio.clip(admin_boundaries.geometry).mean(dim=['x', 'y'])

# Add attributes to admin boundaries GeoDataFrame
admin_boundaries['avg_rainfall_2024_03_21'] = rainfall_2024_avg.values
admin_boundaries['avg_percentile_95'] = percentile_95_avg.values
admin_boundaries['exceeds_95th'] = admin_boundaries['avg_rainfall_2024_03_21'] > admin_boundaries['avg_percentile_95']

# Save outputs
rainfall_2024_03_21.rio.to_raster("output/rainfall_2024_03_21.tif")
percentile_95.rio.to_raster("output/percentile_95.tif")
admin_boundaries.to_file("output/admin_boundaries_with_rainfall.shp")
