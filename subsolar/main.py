import numpy as np
import csv
from objects import objects
import argparse
import sys
import matplotlib.pyplot as plt
import math
from rotation import Rotation
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from numpy import cos as cos
from numpy import sin as sin

# Newton-Raphson Method
def eccentric_anomaly(M_array, e, tolerance=1e-10, max_iterations=100):
    # Function and its derivative
    f = lambda x: x - e*sin(x) - M_array
    df = lambda x: 1 - e*cos(x)
    # Initial guess
    x0 = M_array
    # Updated guess
    x1 = x0 - (f(x0) / df(x0))
    while np.all(abs(x1 - x0) > tolerance):
        x0 = x1
        x1 = x0 - (f(x0) / df(x0))
    return x1

class Orbit:
    """
    SMA: semi-major axis (billions of meters, millions of kilometers)
    eccentricity: eccentricity
    inclination: inclination to ecliptic (degrees)
    lan: longitude of the ascending node (degrees)
    aop: argument of perihelion (degrees)
    period: sidereal orbital period (days)
    """
    def __init__(self, SMA, eccentricity, inclination, lan, aop, period, resolution=360):
        self.resolution = resolution
        a = SMA
        e = eccentricity
        i = math.radians(inclination) + 0.001
        o = math.radians(lan)
        w = math.radians(aop)
        T = period
        self.a = a
        self.i = i
        self.o = o
        self.w = w
        self.e = e
        self.T = T
        b = a * math.sqrt(1 - (e**2))
        self.b = b
        self.time_step = period / resolution

        q0 = np.array([
            cos(o)*cos(w)-sin(o)*sin(w)*cos(i),
            -cos(o)*sin(w)-sin(o)*cos(w)*cos(i),
            sin(o)*sin(i)])
        q1 = np.array([
            sin(o)*cos(w)+cos(o)*sin(w)*cos(i),
            -sin(o)*sin(w)+cos(o)*cos(w)*cos(i),
            -cos(o)*sin(i)])
        q2 = np.array([
            sin(w)*sin(i),
            cos(w)*sin(i),
            cos(i)])
        self.Q = np.array([q0,q1,q2])

        # Get mean anomaly from time
        self.m_from_day = lambda t: t * ((2 * np.pi) / self.T) 

    @classmethod
    def from_dict(cls, data: dict, resolution=360):
        return cls(data["sma"], data["eccentricity"], data["inclination"], data["lan"], data["aop"], data["period"], resolution=resolution)

    # Coordinates aligned with the orbit 
    def local(self, t): # expects mean anomaly
        E = eccentric_anomaly(t, self.e)
        x = self.a * (cos(E) - self.e)
        y = self.a * math.sqrt(1 - (self.e**2)) * sin(E)
        z = t * 0
        return np.array([x,y,z])

    # Coordinates relative to the Ecliptic, centered on the sun
    def ecliptic_coords(self, t): # expects mean anomaly
        local = self.local(t)
        return self.Q @ local

    # Rotates the coordinates into standard 3d space
    def generate_ellipse(self):
        # Even spacing of mean anomalies
        t = np.linspace(0, 2*np.pi, num=self.resolution)
        return self.ecliptic_coords(t)

    def ellipse_path(self):
        x,y,z = self.generate_ellipse()
        return x, y, z

    def true_anomaly(self, t): # expects mean anomaly
        E = eccentric_anomaly(t, self.e)
        p = cos(E) - self.e
        q = 1 - self.e * cos(E)
        cosv = p / q
        v = np.arccos(cosv)
        return np.where(E % (2*np.pi) <= np.pi, v, (2*np.pi)-v)

def linindex(src, index):
    return np.abs(src - index).argmin()

def ellipse(orbit: Orbit):
    x, y, z = orbit.ellipse_path()
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    xr = np.ptp(x)
    yr = np.ptp(y)
    zr = np.ptp(z)
    ax.set_box_aspect((xr, yr, zr))
    sc = ax.scatter(x, y, z)
    ax.scatter(0, 0, 0)
    return

# Exaggerate values. Need a better way to stretch values within a range
def stretch(src, factor=500):
    return src * factor

def plot_rotation_data(rot, time, exaggerate=False, stat="decl"):
    orb = rot.orbit
    title = ""
    match stat:
        case "rot":
            data = rot.angle_t(time)
            title = "Rotation over time"
        case "anomaly":
            data = orb.true_anomaly(orb.m_from_day(time))
            title = "True anomaly over time"
        case "lha":
            data = rot.local_hour_angle(time)
            title = "Subsolar longitude over time"
        case "decl":
            if exaggerate: data = stretch(rot.declination(time))
            else: data = rot.declination(time)
            title = "Declination/subsolar latitude over time"
    plt.ylabel("Degrees")
    plt.xlabel("Days")
    plt.title(title)
    plt.plot(time, np.degrees(data))

def get_subsolar(rot, time, offset=False, exaggerate=False):
    if offset:
        lha = np.degrees(rot.local_hour_angle(time) - np.pi)
    else:
        lha = np.degrees(rot.local_hour_angle(time))
    decl = rot.declination(time)
    if exaggerate: decl = stretch(decl)
    return lha, np.degrees(decl)

def map_subsolar_point(rot, time, offset=False, exaggerate=False):
    lha, decl = get_subsolar(rot, time, offset=offset, exaggerate=exaggerate)
    fig, ax = plt.subplots(figsize=(10,6), subplot_kw={'projection': ccrs.Orthographic()})
    ax.scatter(lha, decl,s=0.5, transform=ccrs.PlateCarree())
    ax.set_aspect('equal')
    ax.set_global()
    ax.coastlines()

def export_subsolar(rot, time, offset, path, exaggerate=False):
    lha, decl = get_subsolar(rot, time, offset=offset, exaggerate=exaggerate)
    points = np.column_stack((lha, decl))
    header = np.array(['longitude', 'latitude'])
    points = np.vstack((header, points))
    with open(path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(points)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("object", help="object to simulate, must correspond to object in objects.py")
    parser.add_argument("-show_orbit", help="show 3d orbital diagram", action="store_true")
    parser.add_argument("-show_subsolar", help="plot the subsolar point on a map", action="store_true")
    parser.add_argument("-export_subsolar", help="export the subsolar point over the time window as a csv", type=str)
    parser.add_argument("-window", help="time window, in days, to simulate", type=int, default=365)
    parser.add_argument("-resolution", help="resolution to simulate (number of time points)", type=int, default=2500)
    parser.add_argument("-exaggerate", help="exaggerate latitudes for the calculation of subsolar point", action="store_true")
    parser.add_argument("-offset", help="offset longitudes to span -180 to 180, rather than 0 to 360", action="store_true")
    parser.add_argument("-plot_data", help="plot data with respect to time", type=str, nargs='?', const="decl")

    args = parser.parse_args()

    time = np.linspace(0, args.window, num=args.resolution)
    try:
        obj = objects[args.object]
        obj_orbit = Orbit.from_dict(obj, resolution=args.resolution)
        obj_rot = Rotation.from_dict(obj, obj_orbit)
    except:
        print("Failed to find object")
        sys.exit()

    if args.show_orbit:
        ellipse(obj_orbit)   
    if args.show_subsolar:
        map_subsolar_point(obj_rot, time, offset=args.offset, exaggerate=args.exaggerate)
    if args.plot_data:
        plot_rotation_data(obj_rot, time, exaggerate=args.exaggerate, stat=args.plot_data)
    if args.export_subsolar != None:
        export_subsolar(obj_rot, time, args.offset, args.export_subsolar, exaggerate=args.exaggerate)

    plt.show()
