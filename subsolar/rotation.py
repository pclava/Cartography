import numpy as np
import math

"""
Class and functions to model rotation and planet-centric measurements
"""

# Required to rotate pole vector, given relative to Earth's equator, into an ecliptic frame of reference
earth_tilt = math.radians(23.4392811)
# Rotation matrix earth equatorial frame to ecliptic frame
equatorial_matrix = np.array([
    [1,0,0],
    [0, np.cos(earth_tilt), np.sin(earth_tilt)],
    [0, -1*np.sin(earth_tilt), np.cos(earth_tilt)]])

class Rotation:
    def __init__(self, period, axial_tilt_deg, pole_ra, pole_decl, orbit):
        self.Tr = period                            # sidereal rotational period (days)
        self.tilt = math.radians(axial_tilt_deg)    # axial tilt relative to orbital plane (radians)
        self.va = (np.pi * 2) / self.Tr             # angular velocity (radians/day)
        self.pra = math.radians(pole_ra)            # right ascension of the north pole
        self.pdecl = math.radians(pole_decl)        # declination of the north pole
        self.orbit = orbit                          # Orbit object
        self.time_step = self.orbit.time_step       # Time step (equal to orbital period / resolution)
        self.angle_step = self.va * self.time_step  # Angular distance covered in one time step by rotation

        # Normal vector to object's orbital plane. For Earth, should be (0,0,1)
        self.orbital_normal = np.array([
            np.sin(self.orbit.i)*np.sin(self.orbit.o),
            -1*np.sin(self.orbit.i)*np.cos(self.orbit.o),
            np.cos(self.orbit.i)
        ]) 

        # Object's pole vector, relative to Earth's equatorial plane
        earth_pv = np.array([
            np.cos(self.pdecl)*np.cos(self.pra),
            np.cos(self.pdecl)*np.sin(self.pra),
            np.sin(self.pdecl)
        ])
        ecl_pv = equatorial_matrix @ earth_pv   # Relative to ecliptic

        # Object's north pole in ecliptic frame, centered on object. Defines object's equatorial plane
        self.pole = ecl_pv / np.linalg.norm(ecl_pv)
        self.x_0 = np.cross(self.pole, np.array([0,0,1])) / np.linalg.norm(np.cross(self.pole, np.array([0,0,1])))
        self.y_0 = np.cross(self.pole, self.x_0) / np.linalg.norm(np.cross(self.pole, self.x_0))

        # Sanity check: calculate the angle between calculated orbital plane and provided equatorial plane
        # Should equal closely the axial tilt
        print("Estimated axial tilt (if this does not equal the axial tilt, something has gone terribly wrong):", math.degrees(np.arccos(np.dot(self.pole, self.orbital_normal))))

    @classmethod
    def from_dict(cls, data: dict, orbit):
        return cls(data["rot_period"], data["tilt"], data["pole_ra"], data["pole_decl"], orbit)

    # Vector of the sun in ecliptic, object-centric frame
    def sun_vector(self, day):
        ecliptic = self.orbit.ecliptic_coords(self.orbit.m_from_day(day))
        return -1 * ecliptic

    # Returns angle on a given day
    def angle_t(self, day, start=0):
        return (start + day * self.va)  % (2 * np.pi)

    # Returns angle at a given time step
    def angle_n(self, n, start=0):
        return angle_t(n*self.time_step, start=start)

    # Declination is 90deg - angle between sun and pole. Declination is the latitude of the subsolar point
    def declination(self, day):
        sun_vector = self.sun_vector(day)
        sun_mag = np.linalg.norm(sun_vector, axis=0)
        dot = self.pole @ sun_vector
        return np.arcsin(dot / sun_mag)

    # This is not exactly local hour angle, but I'm calling it that. It's the longitude of the subsolar point
    # Calculates angle between fixed vectors spanning equatorial plane, and sun vector, subtracting current angle of rotation
    def local_hour_angle(self, day, start=0):
        sun = self.sun_vector(day)
        dot = self.pole @ sun
        proj = sun - self.pole[:, None] * dot
        proj_mag = np.linalg.norm(proj, axis=0)
        doty = self.y_0 @ proj
        dotx = self.x_0 @ proj
        return (np.arctan2(doty, dotx) + np.pi - self.angle_t(day, start=start)) % (2 * np.pi)
