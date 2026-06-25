"""
Functions for reprojecting various data
"""

import geopandas as gpd 
import cartopy.crs as ccrs
import pandas as pd
import argparse

def project_polygon(gdf, target_crs):
    """
    Safely projects a geopandas GeoDataFrame in EPSG:4326 into a given projection, using Cartopy
    Returns a GeoDataFrame
    Uses Cartopy because geopandas can really hate doing this itself
    """
    src_crs = ccrs.Geodetic()
    visible = []
    for poly in gdf.geometry:
        clean = target_crs.project_geometry(poly, src_crs=src_crs)
        if not clean.is_empty:
            visible.append(clean)
    gdf_new = gpd.GeoDataFrame(geometry=visible, crs=target_crs.proj4_init)
    return gdf_new
    
def project_csv(inp, out, crs_proj):
    """
    Reprojects a CSV of lat/lon points into a given CRS
    """
    df = pd.read_csv(inp)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326")
    gdf_reprojected = gdf.to_crs(crs_proj)
    gdf_reprojected.to_file(out, driver="GeoJSON")

def project_geojson(inp, out, crs_proj):
    """
    Reprojects a GeoJSON in geodetic coordinates into a given CRS
    """
    gdf = gpd.read_file(inp)
    reprojected = gdf.to_crs(crs_proj)
    reprojected.to_file(out, driver="GeoJSON")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("type", help="csv or geojson", type=str)
    parser.add_argument("source", help="input file", type=str)
    parser.add_argument("destination", help="destination file", type=str)
    parser.add_argument("crs", help="target crs", type=str)
    args = parser.parse_args()

    match args.type:
        case "csv":
            project_csv(args.source, args.destination, args.crs)
        case "geojson":
            project_geojson(args.source, args.destination, args.crs)
        case _:
            print("Unrecognized type")
