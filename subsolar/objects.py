"""
Pre-defined objects. Add an object here to model its behavior
-------

# Quantities and their units:

sma: semi-major axis (billions of meters, millions of kilometers)
inclination: (in degrees to the ecliptic)
lan: longitude of the ascending node (in degrees)
aop: argument of perihelion (in degrees)
period: orbital period (in days)
rot_period: sidereal rotational period (in days)
tilt: axial tilt relative to object's orbital plane (in degrees)
pole_ra: north pole right ascension (in degrees, relative to earth's equatorial plane)
pole_decl: north pole declination (in degrees, relative to earth's equatorial plane)
"""

objects = {
    "mercury": {
        "sma": 58,
        "eccentricity": 0.2056,
        "inclination": 7,
        "lan": 48,
        "aop": 29,
        "period": 87.9691,
        "rot_period": 58.646,
        "tilt": 0.034,
        "pole_ra": 281.01,
        "pole_decl": 61.41
    },
    "earth": {
        "sma": 149.6,
        "eccentricity": 0.0167,
        "inclination": 0,
        "lan": 348.739,
        "aop": 114.2,
        "period": 365.256363004,
        "rot_period": 0.99726968,
        "tilt": 23.439,
        "pole_ra": 0,
        "pole_decl": 90
    }
 }
