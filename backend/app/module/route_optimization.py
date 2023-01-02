import json
import math
import numpy as np
import re
from datetime import datetime, timedelta
import vroom
import uuid


def parse_timedelta(time_string: str) -> timedelta:
    # Compile the regular expression
    pattern = re.compile(r"^(?:(\d+)\sday(?:s)?,\s)?(\d{2}):(\d{2})(?::(\d{2}))?$")

    # Use the regular expression to match the time string
    match = pattern.match(time_string)

    # If the time string doesn't match the pattern, return an invalid timedelta
    if not match:
        return timedelta()

    # Extract the number of days, hours, minutes, and seconds from the match
    days = int(match.group(1) or 0)
    hours = int(match.group(2))
    minutes = int(match.group(3))
    seconds = int(match.group(4) or 0)

    # Return a timedelta representing the duration
    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds).seconds


def haversine(angle):
    h = math.sin(angle / 2) ** 2
    return h


def distance(lat1, long1, lat2, long2):
    # Note: The formula used in this function is not exact, as it assumes
    # the Earth is a perfect sphere.

    # Mean radius of Earth in miles
    radius_earth = 6371000

    # Convert latitude and longitude to
    # spherical coordinates in radians.
    degrees_to_radians = math.pi / 180.0
    phi1 = lat1 * degrees_to_radians
    phi2 = lat2 * degrees_to_radians
    lambda1 = long1 * degrees_to_radians
    lambda2 = long2 * degrees_to_radians
    dphi = phi2 - phi1
    dlambda = lambda2 - lambda1

    a = haversine(dphi) + math.cos(phi1) * math.cos(phi2) * haversine(dlambda)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius_earth * c
    return d


def make_matrix(coordinates):

    distance_matrix = np.zeros(
        (np.size(coordinates, 0), np.size(coordinates, 0))
    )  # create an empty matrix for distance between all locations

    for index in range(0, np.size(coordinates, 0)):
        src = coordinates[index]

        for ind in range(0, np.size(coordinates, 0)):
            dst = coordinates[ind]
            distance_matrix[index, ind] = distance(src[0], src[1], dst[0], dst[1])

    return distance_matrix, [[int(j / 2) for j in i] for i in distance_matrix]


def convert_step(idx_step, step, data_hub):
    arrival = step.pop("arrival")
    load = step.pop("load")
    try:
        description = step.pop("description", None)
        if description is not None:
            step["detail"] = json.loads(description)
    except:
        pass
    if step["location_index"] == 0:
        step["detail"] = dict(
            hubid=data_hub.hubid,
            name=data_hub.name,
            address=data_hub.address,
            open=data_hub.open,
            close=data_hub.close,
            longitude=data_hub.longitude,
            latitude=data_hub.latitude,
            id=data_hub.id,
        )
    del step["violations"]
    departure = arrival + step["service"] + step["waiting_time"]
    step["arrival"] = "{:02}:{:02}:{:02}".format(
        arrival // 3600, arrival % 3600 // 60, arrival % 60
    )
    step["departure"] = "{:02}:{:02}:{:02}".format(
        departure // 3600, departure % 3600 // 60, departure % 60
    )
    step["vehicle_load"] = [
        {**data_hub.constraints[idx], **{"value": i}} for idx, i in enumerate(load)
    ]
    if step["location_index"] == 0:
        step["hub_id"] = data_hub.id

    return step


def convert_unassigned(job):
    try:
        description = job.pop("description", None)
        if description is not None:
            job["detail"] = json.loads(description)
    except:
        pass
    return job


def convert_route(route, data_hub):
    step = route.pop("steps")
    delivery = route.pop("delivery")
    amount = route.pop("amount")
    description = route.pop("description", None)

    del route["pickup"]
    del route["violations"]

    route["steps"] = [convert_step(idx, s, data_hub) for idx, s in enumerate(step)]
    route["delivery"] = [
        {**data_hub.constraints[idx], **{"value": i}} for idx, i in enumerate(delivery)
    ]
    route["amount"] = [
        {**data_hub.constraints[idx], **{"value": i}} for idx, i in enumerate(amount)
    ]
    if description:
        route["detail"] = json.loads(description)
    return route


def create_break(break_item):
    return vroom.Break(
        id=break_item["id"],
        time_windows=[
            vroom.TimeWindow(
                parse_timedelta(break_item["start"]), parse_timedelta(break_item["end"])
            )
        ],
        service=int(break_item.get("service_time", 30) * 60),
        description=break_item["name"],
    )


def create_vehicle(vehicle_item):
    del vehicle_item["hub"]
    return vroom.Vehicle(
        id=vehicle_item["id"],
        start=0,
        end=0,
        profile=vehicle_item.get("profile", "car"),
        skills=set([i["id"] for i in vehicle_item.get("tag", None)]),
        capacity=[i["value"] for i in vehicle_item.get("capacity", [])],
        time_window=[
            parse_timedelta(vehicle_item.get("start", "00:00:00")),
            parse_timedelta(vehicle_item.get("end", "23:59:59")),
        ],
        breaks=[create_break(i) for i in vehicle_item.get("vehicle_break", [])],
        description=json.dumps(vehicle_item),
    )


def create_job(idx, job_item):
    del job_item["hub"]
    del job_item["geom"]
    return vroom.Job(
        id=job_item["id"],
        location=idx + 1,
        service=int(job_item.get("service_time", 30) * 60),
        skills=set([i["id"] for i in job_item.get("tag", None)]),
        delivery=[i["value"] for i in job_item.get("demand", [])],
        time_windows=[
            [
                parse_timedelta(job_item.get("open", "00:00:00")),
                parse_timedelta(job_item.get("close", "23:59:59")),
            ]
        ],
        description=json.dumps(job_item),
    )


async def route_optimization(data):
    data_hub = data
    data_visites = data.visites
    data_vehicles = data.vehicles

    problem_instance = vroom.Input(amount_size=len(data.constraints))
    coordinates = [[data_hub.latitude, data_hub.longitude]]
    [coordinates.append([i["latitude"], i["longitude"]]) for i in data_visites]
    problem_instance.set_durations_matrix(
        profile="car",
        matrix_input=make_matrix(coordinates)[1],
    )

    problem_instance.add_vehicle(
        [create_vehicle(vehicle_item) for vehicle_item in data_vehicles]
    )
    problem_instance.add_job(
        [create_job(idx, job_item) for idx, job_item in enumerate(data_visites)]
    )
    solution = problem_instance.solve(exploration_level=5, nb_threads=8)

    result = solution.to_dict()
    summary = result.pop("summary")
    routes = result.pop("routes")
    result["routes"] = [convert_route(route, data_hub) for route in routes]
    delivery = summary.pop("delivery")
    amount = summary.pop("amount")
    del summary["pickup"]
    del summary["violations"]
    summary["delivery"] = [
        {**data_hub.constraints[idx], **{"value": i}} for idx, i in enumerate(delivery)
    ]
    summary["amount"] = [
        {**data_hub.constraints[idx], **{"value": i}} for idx, i in enumerate(amount)
    ]
    unassigned = result.pop("unassigned")
    result["unassigned"] = [convert_unassigned(i) for i in unassigned]
    result["summary"] = summary
    result["code"] = str(uuid.uuid1())
    result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return result
