The code here models the subsolar point on an object orbiting the sun.
If you drew a line from the sun to the object, the subsolar point is the point
(in lat/lon) where that line intersects the object.

This was made for Mercury, but should in theory work for any object orbiting
any other object.

In order the model the subsolar point, the code also models the orbit and
rotation of the object. The -show_orbit flag shows a (pretty cool) 3d model of
the object's orbit around the central body.
