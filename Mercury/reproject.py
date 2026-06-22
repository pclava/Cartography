import geopandas as gpd
from shapely.geometry import Point
import shapely
import warnings
import numpy as np

lat0 = 0
lon0 = -90
rad = 2439400

path = "test.geojson"
out = "testprojected.geojson"
crs=f"+proj=ortho +lat_0={lat0} +lon_0={lon0} +a={rad} +b={rad} +units=m +no_defs"
aeqd=f"+proj=aeqd +lat_0={lat0} +lon_0={lon0} +a={rad} +b={rad} +units=m +no_defs"

center = gpd.GeoSeries([Point(lon0, lat0)], crs="EPSG:4326").to_crs(aeqd)
radm = (rad * np.pi / 2) * 0.999
hemisphere = gpd.GeoDataFrame(geometry=center.buffer(radm), crs=aeqd).to_crs("EPSG:4326")

gdf = gpd.read_file(path)
clipped = gdf.overlay(hemisphere, how='intersection')
clipped.to_file("clipped.geojson")
projected = clipped.to_crs(crs)
projected.to_file("projected.geojson")