from pyproj import CRS, Transformer
import numpy as np
from shapely.geometry import Polygon
from shapely.validation import explain_validity
import shapely

import hemispheres

def transformer(lon0, lat0):
    ortho = CRS.from_proj4(
        f"+proj=ortho +lat_0={lat0} +lon_0={lon0} +a=2439400 +b=2439400 +units=m +no_defs")
    wgs84 = CRS.from_epsg(4326)
    return Transformer.from_crs(wgs84, ortho, always_xy=True)
    
def to_polygon(bounds, viewpoint):
    lon0=viewpoint[0]
    lat0=viewpoint[1]
    transf = transformer(lon0, lat0)
    
    # Get latlon coordinates and transform to x,y
    lons = [pt[0] for pt in bounds]
    lats = [pt[1] for pt in bounds]
    xs, ys = transf.transform(lons, lats)
    
    # Sanitize coords
    coords = list(zip(xs,ys))
    coords = [(x,y) for x,y in coords if np.isfinite(x) and np.isfinite(y)]
    if coords[0] != coords[-1]: coords.append(coords[0])
    
    poly = Polygon(coords)
    if not poly.is_valid:
        reason = explain_validity(poly)
        raise ValueError(f"Invalid polygon {reason}")
    
    return poly

if __name__ == "__main__":
    center = np.array([0, 0])
    rotated = hemispheres.create_great_circle(center)
    rotated_coords = np.degrees(hemispheres.coords(rotated).transpose())
    
    polygon = to_polygon(rotated_coords, np.array([-90, 0]))
    geojson = shapely.to_geojson(polygon, indent=2)
    with open("test.geojson", 'w', encoding='utf-8') as file:
        file.write(geojson)