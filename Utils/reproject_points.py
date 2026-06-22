"""
Reprojects a CSV of lat/lon points into a given CRS
"""

import geopandas as gpd
import pandas as pd
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="source file, must be a csv with a longitude field and latitude field", type=str)
    parser.add_argument("output_file", help="output geojson file, should ideally have .geojson extension", type=str)
    parser.add_argument("crs", help="target crs", type=str)
    args = parser.parse_args()
    
    df = pd.read_csv(args.input_file)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326")
    gdf_reprojected = gdf.to_crs(args.crs)
    gdf_reprojected.to_file(args.output_file, driver="GeoJSON")
    print(f"Successfully projected points into CRS: {args.crs} to file: {args.output_file}")