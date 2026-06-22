"""
Generate a hemisphere polygon for Mercury, output in a specified projected CRS
(e.g. orthographic) as a GeoJSON file ready for QGIS.

Usage:
    python mercury_hemisphere.py --lon 0 --lat 0 \
        --target-crs "+proj=ortho +lat_0=0 +lon_0=-90 +a=2439400 +b=2439400 +units=m +no_defs" \
        --output hemisphere.geojson

Dependencies:
    pip install numpy pyproj
"""

import argparse
import json
import math
import numpy as np
from pyproj import Transformer


# ── Spherical geometry helpers ────────────────────────────────────────────────

def sph2xyz(lon_deg, lat_deg):
    lon = math.radians(lon_deg)
    lat = math.radians(lat_deg)
    return np.array([
        math.cos(lat) * math.cos(lon),
        math.cos(lat) * math.sin(lon),
        math.sin(lat)
    ])


def xyz2lonlat(v):
    v = v / np.linalg.norm(v)
    lat = math.degrees(math.asin(float(np.clip(v[2], -1.0, 1.0))))
    lon = math.degrees(math.atan2(float(v[1]), float(v[0])))
    return lon, lat


def make_orthogonal_basis(center_vec):
    c = center_vec / np.linalg.norm(center_vec)
    ref = np.array([1.0, 0.0, 0.0]) if abs(c[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    perp1 = np.cross(c, ref)
    perp1 /= np.linalg.norm(perp1)
    perp2 = np.cross(c, perp1)
    perp2 /= np.linalg.norm(perp2)
    return perp1, perp2


def generate_boundary_lonlat(center_lon, center_lat, n_points=2000):
    center_vec = sph2xyz(center_lon, center_lat)
    perp1, perp2 = make_orthogonal_basis(center_vec)
    ring = []
    for i in range(n_points):
        angle = 2 * math.pi * i / n_points
        pt = math.cos(angle) * perp1 + math.sin(angle) * perp2
        pt /= np.linalg.norm(pt)
        ring.append(xyz2lonlat(pt))
    return ring


# ── Projection ────────────────────────────────────────────────────────────────

def project_ring(lonlat_ring, transformer):
    """Project ring, returning (x, y) or None for points beyond the limb."""
    result = []
    for lon, lat in lonlat_ring:
        x, y = transformer.transform(lon, lat)
        if math.isfinite(x) and math.isfinite(y):
            result.append((x, y))
        else:
            result.append(None)
    return result


def rotate_to_put_invalid_in_middle(projected):
    """
    Rotate the ring (a circular list) so that the invalid (None) region
    is in the middle of the list, not straddling the start/end boundary.
    This ensures extract_valid_arc sees a single contiguous valid segment.

    Strategy: find the index of the first valid point after the longest
    invalid run, and rotate so that point is at index 0.
    """
    n = len(projected)
    valid_mask = [p is not None for p in projected]

    if all(valid_mask) or not any(valid_mask):
        return projected  # fully valid or fully invalid, no rotation needed

    # Find the longest run of invalid points
    best_start = 0
    best_len = 0
    cur_start = 0
    cur_len = 0
    for i in range(2 * n):  # wrap around once
        if not valid_mask[i % n]:
            if cur_len == 0:
                cur_start = i % n
            cur_len += 1
            if cur_len > best_len:
                best_len = cur_len
                best_start = cur_start
        else:
            cur_len = 0

    # Rotate so the first valid point after the longest invalid run is at index 0
    first_valid_after = (best_start + best_len) % n
    return projected[first_valid_after:] + projected[:first_valid_after]


def extract_valid_arc(projected):
    """
    After rotation, extract the single contiguous valid arc.
    Returns list of (x, y). Any trailing invalid points are ignored.
    """
    arc = []
    for pt in projected:
        if pt is not None:
            arc.append(pt)
        elif arc:
            break  # first invalid point after valid run — done
    return arc


def signed_area(ring):
    """
    Shoelace signed area. Positive = CCW winding in standard math coordinates
    (y increasing upward), which is what projected CRS and GeoJSON exterior
    rings use.
    """
    area = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        area += (x1 * y2 - x2 * y1)
    return area / 2.0


def limb_arc(a_start, a_end, radius, n=300, go_ccw=True):
    """
    Trace n+1 points along the limb circle from a_start to a_end.
    go_ccw=True  → counter-clockwise (angle increases)
    go_ccw=False → clockwise (angle decreases)
    """
    if go_ccw:
        diff = (a_end - a_start) % (2 * math.pi)
    else:
        diff = -((-a_end + a_start) % (2 * math.pi))
    angles = [a_start + diff * i / n for i in range(n + 1)]
    return [(radius * math.cos(a), radius * math.sin(a)) for a in angles]


def build_polygon_in_projected_crs(center_lon, center_lat, transformer,
                                   n_points=2000):
    """
    Build the polygon ring(s) in projected coordinates.

    Returns a list of rings (each a list of (x, y) pairs, closed).
    Usually one ring; empty list if nothing is visible.
    """
    lonlat_ring = generate_boundary_lonlat(center_lon, center_lat, n_points)
    projected = project_ring(lonlat_ring, transformer)

    none_count = sum(1 for p in projected if p is None)

    if none_count == 0:
        # Fully visible — close and return.
        ring = list(projected)
        ring.append(ring[0])
        return [ring]

    if none_count == len(projected):
        print("Warning: hemisphere is entirely outside the projection view.")
        return []

    # Partially visible: rotate so invalid region is in the middle,
    # extract the single valid arc, then close it through the limb.
    rotated = rotate_to_put_invalid_in_middle(projected)
    arc = extract_valid_arc(rotated)

    if len(arc) < 2:
        print("Warning: visible arc is too short to form a polygon.")
        return []

    # Get planet radius in projected units from transformer target CRS
    crs = transformer.target_crs
    radius = crs.ellipsoid.semi_major_metre if (crs and crs.ellipsoid) else 2439400.0

    ang_end   = math.atan2(arc[-1][1], arc[-1][0])
    ang_start = math.atan2(arc[0][1],  arc[0][0])

    # Try both closure directions; keep whichever gives CCW winding (positive
    # signed area). CCW is the correct GeoJSON exterior ring convention and
    # means the interior is the hemisphere, not its complement.
    for go_ccw in (True, False):
        closure = limb_arc(ang_end, ang_start, radius, n=300, go_ccw=go_ccw)
        ring = arc + closure
        ring.append(ring[0])
        if signed_area(ring) > 0:
            return [ring]

    # Fallback — return whatever we have
    return [ring]


# ── GeoJSON output ────────────────────────────────────────────────────────────

def build_geojson(rings, center_lon, center_lat, target_crs_str, n_points):
    if not rings:
        features = []
    else:
        geom_type = "Polygon" if len(rings) == 1 else "MultiPolygon"
        coords = [[[x, y] for x, y in ring] for ring in rings]
        features = [{
            "type": "Feature",
            "geometry": {
                "type": geom_type,
                "coordinates": [coords[0]] if geom_type == "Polygon" else [[[c] for c in coords]]
            },
            "properties": {
                "center_lon": center_lon,
                "center_lat": center_lat,
                "body": "Mercury",
                "description": f"Hemisphere centered at ({center_lon}°, {center_lat}°)",
                "n_boundary_points": n_points,
                "crs": target_crs_str
            }
        }]

    return {
        "type": "FeatureCollection",
        "name": "mercury_hemisphere",
        "features": features
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate a Mercury hemisphere polygon in a projected CRS for QGIS."
    )
    parser.add_argument("--lon", type=float, default=0.0,
                        help="Hemisphere center longitude in degrees (default: 0)")
    parser.add_argument("--lat", type=float, default=0.0,
                        help="Hemisphere center latitude in degrees (default: 0)")
    parser.add_argument(
        "--target-crs",
        type=str,
        default="+proj=ortho +lat_0=0 +lon_0=-90 +a=2439400 +b=2439400 +units=m +no_defs",
        help="Proj4 string for the output CRS (must match your DEM)"
    )
    parser.add_argument("--output", type=str, default="mercury_hemisphere.geojson",
                        help="Output filename (default: mercury_hemisphere.geojson)")
    parser.add_argument("--points", type=int, default=2000,
                        help="Boundary sample points (default: 2000)")
    args = parser.parse_args()

    source_crs = "+proj=longlat +a=2439400 +b=2439400 +no_defs"

    print(f"Center:     lon={args.lon}°, lat={args.lat}°")
    print(f"Target CRS: {args.target_crs}")
    print(f"Points:     {args.points}")

    transformer = Transformer.from_crs(source_crs, args.target_crs, always_xy=True)

    rings = build_polygon_in_projected_crs(
        args.lon, args.lat, transformer, n_points=args.points
    )

    geojson = build_geojson(rings, args.lon, args.lat, args.target_crs, args.points)

    with open(args.output, "w") as f:
        json.dump(geojson, f, indent=2)

    print(f"Saved: {args.output}")
    print()
    print("QGIS: Set the layer CRS to match your target CRS (same as DEM).")
    print("      If the filled area is the wrong half, right-click layer >")
    print("      Properties > Source > toggle 'Force right-hand rule'.")


if __name__ == "__main__":
    main()