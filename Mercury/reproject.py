import numpy as np
from shapely.geometry import Polygon, Point
import geopandas as gpd 
import shapely

import hemispheres

rad=2439400
lon0=-90
lat0=0
crs=f"+proj=ortho +lat_0={lat0} +lon_0={lon0} +a={rad} +b={rad} +units=m +no_defs"
hem_center = (0, 0)
polygon = hemispheres.generate_polygon(hem_center)
gdf = gpd.GeoDataFrame(geometry=[polygon], crs="EPSG:4326")

horizon = Point(lon0,lat0).buffer(89.9, quad_segs=32)
gdf_horizon = gpd.GeoDataFrame(geometry=[horizon], crs="EPSG:4326")

#gdf_ortho = gdf.to_crs(crs)
clipped = gpd.clip(gdf, gdf_horizon)
final = clipped.to_crs(crs)
print(final['geometry'])
final.to_file("out.GeoJSON", driver="GeoJSON")
