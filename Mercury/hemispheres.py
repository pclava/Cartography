import numpy as np
import csv
import cartopy.crs as ccrs
from shapely.geometry import Polygon, mapping
import shapely
import json
import argparse
import matplotlib.pyplot as plt
import sys

from numpy import cos as cos
from numpy import sin as sin

# NOTE: points are given in (longitude, latitude) with longitude from 0 to 2pi and latitude from -pi/2 to +pi/2

# Returns cartesian vector given a latitude and longitude
def vector(point):
    p = point[:, 1]
    l = point[:, 0]
    x = cos(p)*cos(l)
    y = cos(p)*sin(l)
    z = sin(p)
    return np.column_stack((x,y,z))

# Inverse of vector(), returns latitude and longitude given a cartesian vector
def coords(vector):
    p = np.arcsin(vector[2])
    l = np.arctan2(vector[1], vector[0])
    return np.array([l, p])

# Rotates a cartesian vector by (lon, pi/2 - lat)
# Given the north pole (0,0,1), rotates it to the coordinates (lon, lat)
def rotate(vector, point):
    l = point[0]
    p = point[1]
    x = vector @ np.array([cos(l)*sin(p), -sin(l), cos(l)*cos(p)]) 
    y = vector @ np.array([sin(l)*sin(p), cos(l), sin(l)*cos(p)])
    z = vector @ np.array([-cos(p), 0, sin(p)])
    return np.array([x,y,z])

def create_great_circle(center, resolution=360):
    # Initial set of points along equator, in spherical coords
    lons = np.linspace(0, 2*np.pi, num=resolution)
    lats = np.zeros_like(lons)
    unrotated = np.column_stack((lons, lats))

    # Equatorial points, in cartesian coords
    vectors = vector(unrotated)

    # Rotate vectors
    rotated = rotate(vectors, center)
    return rotated

def longitude(x):
    try: x = float(x)
    except: raise argparse.ArgumentTypeError(f"Invalid longitude {x}")
    if x < 0 or x >= 360: raise argparse.ArgumentTypeError(f"Invalid longitude {x}")
    return np.radians(x)

def latitude(x):
    try: x = float(x)
    except: raise argparse.ArgumentTypeError(f"Invalid latitude {x}")
    if x < -90 or x > 90: raise argparse.ArgumentTypeError(f"Invalid latitude {x}")
    return np.radians(x)

def plot(points):
    ortho_proj = ccrs.Orthographic(central_longitude=0, central_latitude=0)
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(1, 1, 1, projection=ortho_proj)
    ax.coastlines()
    ax.set_global()
    lons, lats = np.degrees(points)
    ax.scatter(lons, lats, color='red', marker='o', s=100,
           transform=ccrs.PlateCarree(), zorder=5)
    plt.show()

def clip_to_visible(points, pov, resolution=360):
    # Note: visible is simply the equator from the pov
    center = np.array([pov[0], pov[1]])
    rotated = create_great_circle(center, resolution=resolution)
    visible_equator = coords(rotated).transpose()
    
    hemisphere = Polygon(np.degrees(points))
    visible = Polygon(np.degrees(visible_equator))

    hemisphere_gdf = gpd.GeoDataFrame(geometry=[hemisphere], crs="EPSG:4326")
    visible_gdf = gpd.GeoDataFrame(geometry=[visible], crs="EPSG:4326")

def save(points, path):
    #polygon = Polygon(np.degrees(points))
    #geojson = {
    #    "type": "Feature",
    #    "properties": {},
    #    "geometry": mapping(polygon)
    #}
    #geojson_string = json.dumps(geojson, indent=4)
    #with open(path, 'w', encoding='utf-8') as file:
    #    file.write(geojson_string)
    header = np.array(['longitude', 'latitude'])
    points = np.vstack((header, points.transpose()))
    with open(path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(points)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("center_longitude", help="longitude of center point, from 0 to 360", type=longitude)
    parser.add_argument("center_latitude", help="latitude of center point, from -90 to 90", type=latitude)
    parser.add_argument("-resolution", help="number of points to calculate", type=int, default=360)
    parser.add_argument("-export", help="file to export to", type=str)
    args = parser.parse_args()

    center = np.array([args.center_longitude, args.center_latitude])
    rotated = create_great_circle(center, resolution=args.resolution)
    rotated_coords = coords(rotated)
#    plot(rotated_coords)

    if args.export:
        save(rotated_coords, args.export)
