import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.merge import merge
from rasterio.features import geometry_mask
from rasterstats import zonal_stats
import pandas as pd

# Define paths to input data
admin2_file = 'geoBoundaries-MOZ-ADM2_simplified.geojson'
rainfall_folder = 'rfb_blended_moz_dekad'
population_raster = 'moz_ppp_2020_UNadj_constrained.tif'

# Define output paths for raster and vector files
output_folder = 'output'
output_vector = os.path.join(output_folder, 'output_vector.geojson')
output_raster_march2024 = os.path.join(output_folder, 'rainfall_march2024.tif')
output_raster_95th_percentile = os.path.join(output_folder, 'rainfall_95th_percentile.tif')
output_raster_exposed_population = os.path.join(output_folder, 'exposed_population.tif')

# Step 1: Compute 95th Percentile for March 2024
percentile_95th = 100.0 
def calculate_percentile(raster_files):
    arrays = [rasterio.open(raster_file).read(1) for raster_file in raster_files]
    stacked = np.stack(arrays)
    percentile = np.percentile(stacked, 95, axis=0)
    return percentile



file_paths = []
# List all files in the rainfall_folder
for filename in os.listdir(rainfall_folder):
    if 'd3.tif' in filename:
        # Construct the full path using os.path.join
        full_path = os.path.join(rainfall_folder, filename)
        file_paths.append(full_path)
        #print(full_path)

percentile_95th = calculate_percentile(file_paths)

# Write 95th percentile raster to disk
with rasterio.open(file_paths[0]) as src:
    profile = src.profile
    profile.update(dtype=rasterio.float32, count=1, compress='lzw')
    with rasterio.open(output_raster_95th_percentile, 'w', **profile) as dst:
        dst.write(percentile_95th.astype(rasterio.float32), 1)

# Step 2: Extract Admin-2 Average Rainfall

admin2 = gpd.read_file(admin2_file)

def calculate_average_rainfall(raster_file):
    admin = []
    with rasterio.open(raster_file) as src:
        affine = src.transform
        admin['average_rainfall'] = zonal_stats(admin2.geometry, src.read(1), affine=affine, stats='mean')
    return admin

admin2_march2024 = calculate_average_rainfall(file_paths[0])

# Calculate boolean if rainfall exceeds 95th percentile
admin2_march2024['exceeds_95th_percentile'] = admin2_march2024['average_rainfall'] > percentile_95th

# Step 3: Generate Vector Output

admin2_march2024.to_file(output_vector, driver='GeoJSON')

# Step 4: Raster Operations - Binary Raster for Exceedance

binary_raster = np.zeros_like(percentile_95th)
binary_raster[admin2_march2024['exceeds_95th_percentile'].values] = 1

# Write binary raster to disk
with rasterio.open(file_paths[0]) as src:
    profile = src.profile
    profile.update(dtype=rasterio.float32, count=1, compress='lzw')
    with rasterio.open(output_raster_march2024, 'w', **profile) as dst:
        dst.write(binary_raster.astype(rasterio.float32), 1)

# Step 5: Calculate Exposed Population

with rasterio.open(population_raster) as pop_src:
    pop_array = pop_src.read(1)
    affine = pop_src.transform
    pop_exposed = binary_raster * pop_array
    exposed_stats = zonal_stats(admin2.geometry, pop_exposed, affine=affine, stats='sum')

admin2['exposed_population'] = [stat['sum'] for stat in exposed_stats]

# Write exposed population to raster
with rasterio.open(population_raster) as src:
    profile = src.profile
    profile.update(dtype=rasterio.float32, count=1, compress='lzw')
    with rasterio.open(output_raster_exposed_population, 'w', **profile) as dst:
        dst.write(exposed_population.astype(rasterio.float32), 1)
