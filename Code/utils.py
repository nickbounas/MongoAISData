from datetime import datetime, date, timedelta
from typing import List
from shapely.geometry import LineString, Polygon
from exceptions import ApplicationException

def get_start_end_day(day: datetime):
    start = day.replace(hour=0, minute=0, second=0)
    end = start + timedelta(1)

    return start, end

def transform_list_comma_polygon(polygon_str: str):

    def transform_pair(pair):
        pair = pair.strip().split(",")
        return [float(c) for c in pair]
    
    polygon = polygon_str.strip().split("\n")

    return [ [transform_pair(pair) for pair in polygon] ]

def transform_comma_polygon(polygon: List):

    def transform_pair(pair):
        pair = pair.strip().split(",")
        return [float(c) for c in pair]

    return [ [transform_pair(pair) for pair in polygon] ]

def km_to_rads(km: float) -> float:
    return km / 111.12

def polygon_from_line_string(line_string: List[List], distance: float) -> List[List]:
   
    line_string = LineString([ (pair[0], pair[1]) for pair in line_string])

    buffer = line_string.buffer(km_to_rads(distance), cap_style=3)

    coords = buffer.__geo_interface__

    # if len(coords['coordinates']) > 1:
    #     raise ApplicationException(400, "Trajectory to complex.....try to lower timedelta")
    
    tupple_to_list = []
    for rings in coords['coordinates']:
        tupple_to_list.append(list(map(list, rings)))
    
    # return {
    #     'type': 'Polygon',
    #     'coordinates': [tupple_to_list]
    # }

    return tupple_to_list




