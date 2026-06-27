from Utils import reproject
import pandas as pd
import geopandas as gpd

ortho1_crs = "+proj=ortho +lat_0=15 +lon_0=-90 +R=2439400 +units=m +no_defs"
src = "../DATA/nomenclature.csv"
out = "../DATA/projected_names.geojson"

df = pd.read_csv(src)
# Transform longitudes because they are measured in degrees west and we need them in degrees east 
df['Center          Longitude'] = df['Center          Longitude'].apply(lambda x: -x if x <= 180 else 360-x)
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['Center          Longitude'], df['Center Latitude']), crs="EPSG:4236")
reproj = gdf.to_crs(ortho1_crs)
reproj.to_file(out, driver="GeoJSON")
