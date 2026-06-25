"""
Generates a hemisphere centered on a given coordinate
"""

import numpy as np
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

def generate_points(center, resolution=1000):
    center = np.array(center)
    rotated = create_great_circle(center, resolution=resolution)
    return coords(rotated).transpose()

def polygon(points, center):
    return Polygon(np.degrees(points.transpose()))

def generate_polygon(center, resolution=1000):
    points = generate_points(np.radians(center), resolution=resolution)
    return Polygon(np.degrees(points))

def plot(points, center):
    fig = plt.figure(figsize=(8, 8))
    proj = ccrs.Orthographic()
    proj._threshold /= 100.
    ax = fig.add_subplot(1, 1, 1, projection=proj)
    ax.coastlines()
    ax.set_global()
    lons, lats = np.degrees(points)
    poly = polygon(points, center)
    # IMPORTANT: points MUST be in Geodetic to correctly process and draw the hemisphere
    # Cartopy will spit out a warning but it is safe to ignore.
    ax.add_geometries([poly], crs=ccrs.Geodetic(), facecolor = 'b', edgecolor='black', alpha=0.5)
    ax.scatter(lons, lats, color='red', marker='o', s=1, transform=ccrs.PlateCarree(), zorder=5)
    plt.show()

def save(points, path):
    polygon = Polygon(np.degrees(points))
    geojson = {
        "type": "Feature",
        "properties": {},
        "geometry": mapping(polygon)
    }
    geojson_string = json.dumps(geojson, indent=4)
    with open(path, 'w', encoding='utf-8') as file:
        file.write(geojson_string)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("center_longitude", help="longitude of center point, from 0 to 360", type=longitude)
    parser.add_argument("center_latitude", help="latitude of center point, from -90 to 90", type=latitude)
    parser.add_argument("-resolution", help="number of points to calculate", type=int, default=360)
    parser.add_argument("-export", help="file to export to", type=str)
    parser.add_argument("-plot", help="plot some data", action="store_true")
    args = parser.parse_args()

    center = np.array([args.center_longitude, args.center_latitude])
    rotated_coords = generate_points(center, resolution=args.resolution)

    if args.export:
        save(rotated_coords, args.export)
    if args.plot:
        plot(rotated_coords.transpose(), center)
