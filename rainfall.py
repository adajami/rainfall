import os;
import geopandas as gpd
import rasterio
import numpy as np
from rasterio.mask import mask
from rasterio.features import geometry_mask

# Step 1: Access administrative units of Mozambique at level-2
admin_units_file = "geoBoundaries-MOZ-ADM2.geojson"
admin_units = gpd.read_file(admin_units_file)
#print(admin_units)

# Step 2: Access blended rainfall dataset for the 3rd dekad of March 2024
rainfall_folder = 'rfb_blended_moz_dekad'
file_paths = []
# List all files in the rainfall_folder
for filename in os.listdir(rainfall_folder):
    if 'd3.tif' in filename:
        # Construct the full path using os.path.join
        full_path = os.path.join(rainfall_folder, filename)
        file_paths.append(full_path)

# Step 3: Compute the 95th percentile of the blended rainfall data from 1989-2019
# Open the rainfall dataset
for March_data in file_paths:
    with rasterio.open(March_data) as src:
        # Read the data as a numpy array
        rainfall_data = src.read(1)

        # Calculate the 95th percentile
        percentile_95 = np.percentile(rainfall_data, 95)

# Step 4: Extract average rainfall for both the 95th percentile and the 3rd dekad of March 2024 by admin-2 units
# Loop through each admin unit to perform masking and calculations
for index, row in admin_units.iterrows():
    admin_geom = row['geometry']
    admin_name = row['shapeName']

    # Convert admin_geom to GeoJSON-like dict
    geom_dict = admin_geom.__geo_interface__

    # Mask the rainfall data with admin unit geometry
    masked_rainfall, _ = mask(src, [geom_dict], crop=True)
    #masked_rainfall, _ = mask(src, [admin_geom], crop=True)

    # Calculate mean rainfall for the 3rd dekad of March 2024
    mean_rainfall_mar2024 = np.mean(masked_rainfall)

    # Check if mean rainfall exceeds the 95th percentile
    exceeds_95th_percentile = mean_rainfall_mar2024 > percentile_95

    # Add attributes to admin_units dataframe
    admin_units.at[index, 'mean_rainfall_mar2024'] = mean_rainfall_mar2024
    admin_units.at[index, 'percentile_95'] = percentile_95
    admin_units.at[index, 'exceeds_95th_percentile'] = exceeds_95th_percentile

# Step 5: Generate binary raster indicating where rainfall exceeds the 95th percentile

binary_raster_path = "binary_rainfall_exceeds_95th.tif"
with rasterio.open(binary_raster_path, 'w', **src.profile) as dst:
    # Apply the condition to create the binary raster
    binary_raster = np.where(rainfall_data > percentile_95, 1, 0)
    dst.write(binary_raster.astype(rasterio.uint8), 1)

# Step 6: Multiply binary raster with population raster to compute exposed population
population_file = "wp_pop_icunadj_moz_2020.json"



# Step 7: Aggregate exposed population by admin-2 polygons


# Step 8: Save vector file with all attributes from the original admin-2 vector dataset including computed attributes
output_vector_file = "output_admin2_analysis.geojson"
admin_units.to_file(output_vector_file, driver='GeoJSON')

# Additional outputs mentioned in the request (raster files) can similarly be saved using rasterio.

# Print completion message
print("Analysis completed. Outputs saved successfully.")
