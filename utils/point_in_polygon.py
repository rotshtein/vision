import math


def is_object_in_polygon(points, polygon):
    for point in points:
        if is_point_in_polygon(point, polygon):
            return True
    return False


def is_point_in_polygon(point, polygon):
    polygon_length = len(polygon)
    i = 0
    inside = False
    point_x = point.x
    point_y = point.y
    end_point = polygon[polygon_length - 1]
    end_x = end_point.x
    end_y = end_point.y
    while i < polygon_length:
        start_x = end_x
        start_y = end_y
        end_point = polygon[i]
        i += 1
        end_x = end_point.x
        end_y = end_point.y
        point_y_inside_segment = ((end_y > point_y) ^ (start_y > point_y))  # ? point_y inside[start_y; end_y] segment ?
        denominator = (start_y - end_y)
        if denominator != 0:
            under_segment = ((point_x - end_x) < (point_y - end_y) * (
                    start_x - end_x) / denominator)  # is under the segment?
        else:
            under_segment = False
        _inside = point_y_inside_segment and under_segment
        inside ^= _inside
    return inside


class Point:
    def __init__(self, x, y) -> None:
        super().__init__()
        self.x = x
        self.y = y

    def __str__(self):
        return str([self.x, self.y])


def rotate_and_translate_polygon(polygon: [Point], angle):
    polygon_res = []
    for point in polygon:
        polygon_res.append(translate(rotate(point, angle)))
    return polygon_res


def rotate(point, angle, origin=Point(0, 0)):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    The angle should be given in radians.
    """
    ox = origin.x
    oy = origin.y
    px = point.x * -1 # multiply -1 since point is in 4th quarter
    py = point.y * -1
    angle = math.radians(angle)
    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return Point(int(qx), int(qy))


def translate(point, translate_x=0, translate_y=300):
    p = Point((point.x + translate_x), (point.y + translate_y)) # translate y by 300 since point is in 4th quarter
    return p


point1 = Point(0.1, 99.9)
polygon1 = [Point(0, 0), Point(0, 100), Point(100, 100), Point(100, 0)]
assert is_point_in_polygon(point1, polygon1) is True

print(translate(rotate(Point(150, 150), 90), 0, 300))
print(translate(rotate(Point(300, 0), 90), 0, 300))

rotate_and_translate_polygon(polygon1, 90)
print(polygon1)
