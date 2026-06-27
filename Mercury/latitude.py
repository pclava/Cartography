"""
Creates latitude lines
"""

import numpy as np
import geopandas as gpd
from shapely.geometry import LineString

separation = 1
resolution = int(178/separation)

lons = np.linspace(-180, 180, num=360)
lats = np.linspace(-89, 89, num=resolution+1)
x,y = np.meshgrid(lons, lats)
grid = np.stack((x,y), axis=-1)

geometries = [LineString(i) for i in grid]
gdf = gpd.GeoDataFrame(geometry=geometries, crs="EPSG:4326")
gdf.to_file("../DATA/latitudes.geojson", driver="GeoJSON")
