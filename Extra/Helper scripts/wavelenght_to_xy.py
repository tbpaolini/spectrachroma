import colour
from pprint import pprint

cmfs = colour.MSDS_CMFS['CIE 1931 2 Degree Standard Observer']

wavelenghts = (450, 470, 480, 520, 540, 560, 580, 600, 620, 700)

points = {}
for i in wavelenghts:
    point_XYZ = colour.wavelength_to_XYZ(i, cmfs)
    point_xy = colour.XYZ_to_xy(point_XYZ)
    points.update({i: tuple(point_xy)})

pprint(points)