from Mercury import hemispheres
from Utils import reproject
import geopandas as gpd
import argparse
import cartopy.crs as ccrs

def point(string):
    v = string.split(',')
    if len(v) != 2: 
        raise argparse.ArgumentTypeError(f"Point should have exactly two values, got {len(v)}")
    return tuple(map(float, v))
    
def main(planet_radius, viewpoint, hemisphere_center, path):
    target_globe = ccrs.Globe(ellipse=None, semimajor_axis=planet_radius, semiminor_axis=planet_radius)
    ortho_crs = ccrs.Orthographic(central_longitude=viewpoint[0], central_latitude=viewpoint[1], globe=target_globe)
    ortho_string = ortho_crs.proj4_init
    print("Defined orthographic CRS")
    
    polygon = hemispheres.generate_polygon(hemisphere_center)
    gdf = gpd.GeoDataFrame(geometry=[polygon], crs="EPSG:4326")
    print("Loaded hemisphere polygon")
    
    visible_gdf = reproject.project_polygon(gdf, ortho_crs)
    print("Reprojected hemisphere")
    
    visible_gdf.to_file(path, driver="GeoJSON")
    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--viewpoint", type=point, help="Orthographic viewpoint. Provide as comma-separated longitude,latitude")
    parser.add_argument("--hemisphere_center", type=point, help="Center of hemisphere. Provide as comma-separated longitude,latitude")
    parser.add_argument("--export", type=str, help="Output path. Will output as a GeoJSON file")
    parser.add_argument("--radius", help="Radius of target planet, in meters", type=int, default=2439400)
    args = parser.parse_args()
    
    main(args.radius, args.viewpoint, args.hemisphere_center, args.export)