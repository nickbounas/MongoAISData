from fastapi import APIRouter, Depends, Query
from datetime import datetime, date
from typing import List
from repository import DynamicDataRepository
from utils import get_start_end_day, transform_comma_polygon, transform_list_comma_polygon

router = APIRouter()

@router.get("/vessels-last-position", tags=["get-vessels"])
async def get_vessels_last_position(
    day: datetime,
    bottom_left_x: float,
    bottom_left_y: float,  
    top_right_x: float,
    top_right_y: float,
    dynamic_data_repo: DynamicDataRepository = Depends()) -> dict:
    
    box = [[bottom_left_y, bottom_left_x] , [top_right_y, top_right_x]]
    from_date, to_date = get_start_end_day(day)

    return await dynamic_data_repo.get_vessel_at_box_on(box=box, from_date=from_date, to_date=to_date)
    

@router.get("/adjazent-vessels", tags=["get-adjazent-vessels"])
async def get_adjazent_vessels(
    when: datetime,
    coordinates: List[float] = Query(None), 
    range_in_m: float = 5000,
    dynamic_data_repo: DynamicDataRepository = Depends()
    ) -> List[dict]:

    return await dynamic_data_repo.get_vessels_in_range(coordinates=coordinates, when=when, range_in_m=range_in_m)

@router.get("/vessel-trajectory", tags=["get-adjazent-vessels"])
async def get_vessel_trajectory(
    mmsi: int,
    from_date: datetime,
    to_date: datetime,
    dynamic_data_repo: DynamicDataRepository = Depends()
    ) -> List[dict]:

    return await dynamic_data_repo.get_vessel_trajectory_in_timedelta(mmsi=mmsi, from_date=from_date, to_date=to_date)

@router.get("/vessels-in-polygon", tags=["get-adjazent-vessels"])
async def get_vessels_in_polygon(
    from_date: datetime,
    to_date: datetime,
    polygon: List[str] = Query(None),
    grouped: bool = True,
    skip_aggregation: bool = True,
    dynamic_data_repo: DynamicDataRepository = Depends()
    ) -> List[dict]:

    polygon = transform_comma_polygon(polygon=polygon)

    data, count = await dynamic_data_repo.get_vessels_in_polygon(polygon=polygon, from_date=from_date, to_date=to_date, grouped=grouped, skip_aggregation=skip_aggregation)

    return {
        'count': count,
        'data': data
    }

@router.get("/vessels-trajectories-by-country", tags=["get-adjazent-vessels"])
async def get_vessel_trajectory_by_country(
    country: str,
    from_date: datetime,
    to_date: datetime,
    dynamic_data_repo: DynamicDataRepository = Depends()
    ) -> List[dict]:

    return await dynamic_data_repo.get_vessel_trajectories_by_country(country=country, from_date=from_date, to_date=to_date)

@router.get("/similar-trajectories", tags=["similar-trajectories"])
async def get_similar_trajectories(
    mmsi: int,
    from_date: datetime,
    to_date: datetime,
    distance: float = 5,
    dynamic_data_repo: DynamicDataRepository = Depends()
    ) -> List[dict]:

    return await dynamic_data_repo.get_similar_trajectories2(mmsi=mmsi, from_date=from_date, to_date=to_date, distance_in_km=distance)

@router.get("/custom-similar", tags=["custom-similar"])
async def get_custom_similar(
    mmsi: int,
    from_date: datetime,
    to_date: datetime,
    distance: float = 5,
    dynamic_data_repo: DynamicDataRepository = Depends()
    ) -> List[dict]:

    return await dynamic_data_repo.get_similar_trajectories(mmsi=mmsi, from_date=from_date, to_date=to_date, distance_in_km=distance)

@router.get("/knn", tags=["knn"])
async def knn(
    mmsi: int,
    when: datetime,
    max_distance: float = 1000,
    dt: int = 1,
    k: int = None,
    dynamic_data_repo: DynamicDataRepository = Depends()
    ) -> List[dict]:

    return await dynamic_data_repo.knn(mmsi=mmsi, when=when, max_distance=max_distance, dt=dt, k=k)

@router.get("/vessel", tags=["knn"])
async def get_vessel_at(
    mmsi: int,
    when: datetime,
    dynamic_data_repo: DynamicDataRepository = Depends()
    ) -> List[dict]:

    return await dynamic_data_repo.get_vessel_at(mmsi=mmsi, when=when)

@router.get("/distance-join", tags=["distance-join"])
async def distance_join(
    polygon: str,
    when: datetime,
    dt: int = 1, #minutes,
    distance: float = 600, # in m
    dynamic_data_repo: DynamicDataRepository = Depends()
    ) -> List[dict]:
    polygon = transform_list_comma_polygon(polygon_str=polygon)

    return await dynamic_data_repo.distance_join(polygon=polygon, when=when, dt=dt, distance=distance)

@router.get("/complex", tags=["distance-join"])
async def complex(
    points: str,
    start: datetime,
    dt: int,
    radius: float,
    dynamic_data_repo: DynamicDataRepository = Depends()
    ) -> List[dict]:
    points = transform_list_comma_polygon(polygon_str=points)[0]

    return await dynamic_data_repo.complex(points=points, start=start, dt=dt, radius=radius)