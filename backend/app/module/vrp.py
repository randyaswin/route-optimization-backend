from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from functools import partial
from datetime import datetime, timedelta, date

import numpy as np

# from matplotlib import pyplot as plt
import pandas as pd
import psycopg2
import json
import geopandas as gpd
import openrouteservice
from openrouteservice import convert
from shapely.geometry import LineString
from sqlalchemy import *
import math

client = openrouteservice.Client(
    base_url="http://ALBRouting-820236740.ap-southeast-1.elb.amazonaws.com:8080/ors",
    timeout=None,
)


def time_to_decimal(hhmmss):
    hours = 0
    minutes = 0
    seconds = 0
    try:
        [hours, minutes, seconds] = [int(x) for x in str(hhmmss).split(":")]
    except:
        [hours, minutes] = [int(x) for x in str(hhmmss).split(":")]
    x = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    return x


def time_to_decimal2(hhmmss):
    # print(hhmmss)
    [hours, minutes, seconds] = [int(x) for x in str(hhmmss).split(":")]
    x = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    return x


def make_matrix(coordinates, a):

    distance_matrix = np.zeros(
        (np.size(coordinates, 0), np.size(coordinates, 0))
    )  # create an empty matrix for distance between all locations

    for index in range(0, np.size(coordinates, 0)):
        src = coordinates[index]

        for ind in range(0, np.size(coordinates, 0)):
            dst = coordinates[ind]
            distance_matrix[index, ind] = distance(src[0], src[1], dst[0], dst[1])

    return distance_matrix, [[int(j / 12) for j in i] for i in distance_matrix]


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


def haversine(angle):
    h = math.sin(angle / 2) ** 2
    return h


# def make_matrix(coordinates):

#     distance_matrix = np.zeros(
#         (np.size(coordinates, 0), np.size(coordinates, 0)))  # create an empty matrix for distance between all locations

#     for index in range(0, np.size(coordinates, 0)):
#         src = coordinates[index]

#         for ind in range(0, np.size(coordinates, 0)):
#             dst = coordinates[ind]
#             distance_matrix[index, ind] = distance(src[0], src[1], dst[0], dst[1])

#     return distance_matrix, [[int(j/2) for j in i] for i in distance_matrix]


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


def haversine(angle):
    h = math.sin(angle / 2) ** 2
    return h


def make_matrixa(coords, vehicle):
    switcher = {
        "car": "driving-car",
        "truck": "driving-hgv",
        "bike": "cycling-regular",
        "motorcycle": "driving-motorcycle",
        "walking": "foot-walking",
    }
    profile = switcher.get(vehicle, "driving-car")
    coords = [[round(float(i), 6) for i in y] for y in coords]

    matrix = openrouteservice.distance_matrix.distance_matrix(
        client, coords, profile=profile, metrics=["distance", "duration"]
    )

    return matrix["distances"], [[int(j / 10) for j in i] for i in matrix["distances"]]


def route(arr):
    '''
    sql="""
        --ROUTE
        SELECT seq, node, edge, pgr.cost, agg_cost, shape
        FROM pgr_dijkstraVia(
            'SELECT objectid as id, fromnodeid as source, tonodeid as target, cost_len As cost
             FROM idn.road_link WHERE shape && ST_Expand((SELECT ST_Collect(shape) FROM idn.road_link WHERE objectid IN """+str(tuple(arr))+"""),50)',
             (SELECT ARRAY"""+str(arr)+""" node_array),
            directed := false) as pgr
        JOIN idn.road_link r ON pgr.edge = r.objectid
        """
    tbl_admin=gpd.read_postgis(sql, conn, geom_col='shape', crs='epsg:4326')

    return tbl_admin
    '''

    routes = client.directions(arr, profile="driving-car")

    return routes


def build_vehicle_route(manager, routing, plan, visites, veh_number):

    veh_used = routing.IsVehicleUsed(plan, veh_number)
    # print(veh_used)
    # print(veh_number)
    # print('Vehicle {0} is used {1}'.format(veh_number, veh_used))
    if veh_used:
        route = []
        node = routing.Start(veh_number)
        route.append(visites.iloc[manager.IndexToNode(node)])
        while not routing.IsEnd(node):
            route.append(visites.iloc[manager.IndexToNode(node)])
            node = plan.Value(routing.NextVar(node))

        route.append(visites.iloc[manager.IndexToNode(node)])
        return route
    else:
        return None


def set_DateDay(workdays, timeuse, startdate):
    if timeuse == "monthly":
        days = 30
    elif timeuse == "weekly":
        days = 7
    elif timeuse == "twoweeks":
        days = 14
    elif timeuse == "threeweeks":
        days = 21
    else:
        days = 7

    DateDay_list = []
    available_day = []
    startdate = startdate.split("-")
    start_date = date(int(startdate[0]), int(startdate[1]), int(startdate[2]))
    end_date = start_date + timedelta(days=days)
    delta = timedelta(days=1)
    while start_date <= end_date:
        if start_date.strftime("%A").lower() in workdays:
            DateDay_list.append(start_date.strftime("%Y-%m-%d"))
            available_day.append(start_date.strftime("%A").lower())
        start_date += delta
    # print(DateDay_list)
    return DateDay_list, tuple(available_day)


def manhattan_distance(position_1, position_2):
    """Computes the Manhattan distance between two points"""
    return abs(position_1[0] - position_2[0]) + abs(position_1[1] - position_2[1])


def create_distance_evaluator(distance_matrix):
    """Creates callback to return distance between points."""

    def distance_evaluator(manager, from_node, to_node):
        """Returns the manhattan distance between the two nodes"""
        return distance_matrix[manager.IndexToNode(from_node)][
            manager.IndexToNode(to_node)
        ]

    return distance_evaluator


def create_demand_evaluator(data):
    """Creates callback to get demands at each location."""
    _demands = data["demands"]

    def demand_evaluator(manager, node):
        """Returns the demand of the current node"""
        return _demands[manager.IndexToNode(node)]

    return demand_evaluator


def add_capacity_constraints(routing, data, demand_evaluator_index):
    """Adds capacity constraint"""
    capacity = "Capacity"
    routing.AddDimension(
        demand_evaluator_index,
        0,  # null capacity slack
        data["capacity"].to_list(),
        True,  # start cumul to zero
        capacity,
    )


def create_time_evaluator(time_matrix):
    """Creates callback to get total times between locations."""

    def time_evaluator(manager, from_node, to_node):
        """Returns the total time between the two nodes"""
        return time_matrix[manager.IndexToNode(from_node)][manager.IndexToNode(to_node)]

    return time_evaluator


def add_time_window_constraints(
    routing, manager, time_windows, time_evaluator_index, num_vehicles
):
    """Add Global Span constraint"""
    time = "Time"
    horizon = 120
    routing.AddDimension(
        time_evaluator_index,
        horizon,  # allow waiting time
        horizon,  # maximum time per vehicle
        False,  # don't force start cumul to zero since we are giving TW to start nodes
        time,
    )
    time_dimension = routing.GetDimensionOrDie(time)
    # Add time window constraints for each location except depot
    # and 'copy' the slack var in the solution object (aka Assignment) to print it
    for location_idx, time_window in enumerate(time_windows):
        if location_idx == 0:
            continue
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])
        routing.AddToAssignment(time_dimension.SlackVar(index))
    # Add time window constraints for each vehicle start node
    # and 'copy' the slack var in the solution object (aka Assignment) to print it
    for vehicle_id in range(num_vehicles):
        index = routing.Start(vehicle_id)
        time_dimension.CumulVar(index).SetRange(time_windows[0][0], time_windows[0][1])
        routing.AddToAssignment(time_dimension.SlackVar(index))
        # Warning: Slack var is not defined for vehicle's end node
        # routing.AddToAssignment(time_dimension.SlackVar(self.routing.End(vehicle_id)))


class VrpOrtools:
    def __init__(self):
        self.depot = None
        self.max_work_time = None
        self.distance_matrix = None
        self.time_matrix = None
        self.time_windows = None
        self.time_windows = None
        self.demands = None
        self.num_vehicles = None
        self.vehicle_capacities = None
        # self.vehicle_cost = None
        self.starts = None
        self.ends = None
        self.vehicle_load_time = None
        self.vehicle_unload_time = None
        self.depot_capacity = None
        self.orders = None
        self.vehicles = None
        self.manager = None
        self.routing = None
        self.solution = None
        self.average_speed = None
        self.route_list = None
        # self.week = None

    def set_parameter(self, input):
        # self.id_vehicle = input['id_vehicle']
        self.orders = input["visit"].reset_index(drop=True)
        hub = input.get("hub", None)
        # print((type(hub) == pd.DataFrame and hub['longitude'][0] != None))
        if type(hub) == pd.DataFrame and hub["longitude"][0] != None:
            # print('this a')
            self.hub = json.loads(hub.to_json(orient="records"))[0]
        elif type(hub) == pd.DataFrame and hub["longitude"][0] == None:
            # print('this b')
            gdf = gpd.GeoDataFrame(
                self.orders,
                geometry=gpd.points_from_xy(
                    self.orders.longitude, self.orders.latitude
                ),
            )
            j = gdf.geometry.unary_union
            branc_center = j.centroid
            self.hub = {
                "id": 0,
                "longitude": branc_center.x,
                "latitude": branc_center.y,
                "open": hub["open"][0],
                "close": hub["close"][0],
            }
        else:
            # print('this c')
            gdf = gpd.GeoDataFrame(
                self.orders,
                geometry=gpd.points_from_xy(
                    self.orders.longitude, self.orders.latitude
                ),
            )
            j = gdf.geometry.unary_union
            branc_center = j.centroid
            self.hub = {
                "id": 0,
                "longitude": branc_center.x,
                "latitude": branc_center.y,
                "open": "07:00:00",
                "close": "21:00:00",
            }

        self.vehicle = input["vehicle"].reset_index(drop=True)
        # self.week = input['week']
        self.len_vehicle = len(self.vehicle)
        self.time_windows = []
        self.starts = []
        self.ends = []
        self.coordinates = []
        self.coordinates.append([self.hub["longitude"], self.hub["latitude"]])
        for k, l in zip(self.orders["longitude"], self.orders["latitude"]):
            self.coordinates.append([k, l])
        self.service_time = [0]
        self.penalty = [0x7FFFFFFFFFFFFFFF]
        # print(self.orders[['id','requested_at']].to_json(orient='records'))
        self.orders["tw_open"] = self.orders.apply(
            lambda x: time_to_decimal(x["open"]), axis=1
        )
        self.orders["tw_close"] = self.orders.apply(
            lambda x: time_to_decimal(x["close"]), axis=1
        )
        # self.orders['week'] = self.week
        self.depot = 0
        self.distance_matrix, self.time_matrix = make_matrix(
            self.coordinates, self.vehicles
        )
        # self.time_matrix = [[j*2 for j in i] for i in self.time_matrix]
        self.route_list = []
        self.time_windows.append(
            (
                time_to_decimal(self.hub["open"]).seconds,
                time_to_decimal(self.hub["close"]).seconds,
            )
        )
        for i, row in self.orders.iterrows():
            self.time_windows.append((row["tw_open"].seconds, row["tw_close"].seconds))
        for i in range(len(self.vehicle)):
            self.starts.append(0)
        for i in range(len(self.vehicle)):
            self.ends.append(0)
        self.orders["requested_at"] = ""
        self.orders["priority"] = 0x7FFFFFFFFFFFFFFF
        self.service_time = [0] + self.orders.service_time.to_list()
        self.hub["demand"] = 0.0
        self.orders = pd.concat([pd.DataFrame([self.hub]), self.orders]).reset_index()
        #         self.penalty = self.penalty+self.orders['priority'].to_list()
        #         self.priority = json.loads(self.orders.loc[self.orders['requested_at'] != ""]['requested_at'].to_json())
        # print(
        #    "distane_matrix=",
        #    [[int(j) for idx, j in enumerate(i)] for i in self.distance_matrix],
        # )
        # print("time_matrix=", self.time_matrix)
        # print("time_wondows=", self.time_windows)
        # print("demand=", self.orders["demand"].to_list())
        # print("capacity=", self.vehicle["capacity"].to_list())

    def make_route(self):
        if self.solution:
            vehicle_routes = {}
            routing = []

            for veh in range(self.len_vehicle):
                try:
                    vehicle_routes[veh] = build_vehicle_route(
                        self.manager, self.routing, self.solution, self.orders, veh
                    )
                except:
                    pass
            veh_used = [v for v in vehicle_routes if vehicle_routes[v] is not None]
            for vehicle_id in veh_used:
                id_vehicle = []
                vehicle = []
                geom = []
                cost = []
                instruction = []
                from_ids = []
                to_ids = []
                index = self.routing.Start(vehicle_id)
                node_index = 0
                total_distance = 0
                total_time = 0
                total_load = 0
                first = True
                while not self.routing.IsEnd(index):

                    node_index = self.manager.IndexToNode(index)
                    previous_index = index
                    index = self.solution.Value(self.routing.NextVar(index))
                    if first:
                        coord_before = [
                            self.orders["longitude"][node_index],
                            self.orders["latitude"][node_index],
                        ]
                        from_id = int(-1)
                    else:
                        arr_node = []
                        arr_node.append(coord_before)
                        arr_node.append(
                            [
                                self.orders["longitude"][node_index],
                                self.orders["latitude"][node_index],
                            ]
                        )
                        i_route = route(arr_node)
                        total_load += self.orders["demand"][node_index]
                        try:
                            geom.append(
                                LineString(
                                    convert.decode_polyline(
                                        i_route["routes"][0]["geometry"]
                                    )["coordinates"]
                                )
                            )
                            cost.append(i_route["routes"][0]["summary"]["distance"])
                            total_distance += i_route["routes"][0]["summary"][
                                "distance"
                            ]
                            instruction.append(
                                [
                                    {
                                        "type": i["type"],
                                        "instruction": i["instruction"],
                                        "name": i["name"],
                                    }
                                    for i in i_route["routes"][0]["segments"][0][
                                        "steps"
                                    ]
                                ]
                            )
                        except:
                            geom.append(None)
                            cost.append(0)
                            instruction.append(None)
                        from_ids.append(from_id)
                        to_ids.append(self.orders["id"][node_index])
                        id_vehicle.append(self.vehicle.id[vehicle_id])
                        vehicle.append(self.vehicle.name[vehicle_id])
                    total_time += self.distance_matrix[
                        self.manager.IndexToNode(previous_index)
                    ][self.manager.IndexToNode(index)]
                    coord_before = [
                        self.orders["longitude"][node_index],
                        self.orders["latitude"][node_index],
                    ]
                    from_id = int(self.orders["id"][node_index])
                    first = False
                arr_node = []
                arr_node.append(coord_before)
                arr_node.append(
                    [
                        self.orders["longitude"][self.manager.IndexToNode(index)],
                        self.orders["latitude"][self.manager.IndexToNode(index)],
                    ]
                )
                from_ids.append(from_id)
                to_ids.append(int(-1))
                id_vehicle.append(self.vehicle.id[vehicle_id])
                vehicle.append(self.vehicle.name[vehicle_id])
                i_route = route(arr_node)
                try:
                    geom.append(
                        LineString(
                            convert.decode_polyline(i_route["routes"][0]["geometry"])[
                                "coordinates"
                            ]
                        )
                    )
                    cost.append(i_route["routes"][0]["summary"]["distance"])
                    total_distance += i_route["routes"][0]["summary"]["distance"]
                    instruction.append(
                        [
                            {
                                "type": i["type"],
                                "instruction": i["instruction"],
                                "name": i["name"],
                            }
                            for i in i_route["routes"][0]["segments"][0]["steps"]
                        ]
                    )
                except:
                    geom.append(None)
                    cost.append(0)
                    instruction.append(None)

                df = pd.DataFrame(
                    {
                        "vehicle": vehicle,
                        "from_id": from_ids,
                        "to_id": to_ids,
                        "id_vehicle": id_vehicle,
                        "instruction": instruction,
                        "distance": cost,
                        "geometry": geom,
                    }
                )

                paths_gdf = gpd.GeoDataFrame(
                    df, geometry=df.geometry, crs="epsg:4326"
                ).astype({"id_vehicle": "int", "distance": "float"})
                routing.append(
                    {
                        "vehicle_id": int(self.vehicle.id[vehicle_id]),
                        "vehicle_name": self.vehicle.name[vehicle_id],
                        "total_distance": float(total_distance),
                        "total_time": float(total_time),
                        "total_load": float(total_load),
                        "route_data": paths_gdf.reset_index(
                            drop=True
                        ).__geo_interface__,
                    }
                )
            return routing

    def make_points(self):
        vehicle_routes = {}
        vehicle = []
        vehicle_n = []
        name = []
        permintaan = []
        distance = []
        waktu = []
        datang = []
        berangkat = []
        driving_time = []
        longitude = []
        latitude = []
        id_vehicle = []
        seq = []
        id = []
        for veh in range(self.len_vehicle):
            try:
                vehicle_routes[veh] = build_vehicle_route(
                    self.manager, self.routing, self.solution, self.orders, veh
                )
            except:
                pass
        veh_used = [v for v in vehicle_routes if vehicle_routes[v] is not None]
        for vehicle_id in veh_used:
            i_distance = 0
            i_waktu = 0
            i_driving_time = 0
            i_datang = timedelta(seconds=0)
            i_datang2 = 0
            i_berangkat = timedelta(seconds=0)
            i_seq = 1
            req = 0
            index = self.routing.Start(vehicle_id)
            time_dimension = self.routing.GetDimensionOrDie("Time")
            while not self.routing.IsEnd(index):
                node_index = self.manager.IndexToNode(index)
                # print(node_index)
                time_var = time_dimension.CumulVar(index)
                previous_index = index
                index = self.solution.Value(self.routing.NextVar(index))
                if node_index == self.depot:
                    i_berangkat = timedelta(seconds=self.solution.Min(time_var))
                else:
                    i_distance += self.distance_matrix[node_index][
                        self.manager.IndexToNode(index)
                    ]
                    i_waktu += (
                        self.distance_matrix[node_index][
                            self.manager.IndexToNode(index)
                        ]
                        + float(self.service_time[node_index]) * 60
                    )
                    i_driving_time += self.solution.Min(time_var)
                    i_datang = i_berangkat + timedelta(
                        seconds=self.time_matrix[node_index][
                            self.manager.IndexToNode(index)
                        ]
                    )
                    i_berangkat = i_datang + timedelta(
                        seconds=float(self.service_time[node_index]) * 60
                    )
                    i_datang2 = i_datang
                    seq.append(i_seq)
                    i_seq += 1
                    id_vehicle.append(self.orders.id_vehicle[node_index])
                    vehicle.append(self.vehicle[vehicle_id])
                    id.append(self.orders.id[node_index])
                    name.append(self.orders.name[node_index])
                    distance.append(i_distance)
                    waktu.append(i_waktu)
                    datang.append(str(i_datang))
                    berangkat.append(str(i_berangkat))
                    driving_time.append(i_driving_time)
                    longitude.append(self.orders.longitude[node_index])
                    latitude.append(self.orders.latitude[node_index])
                # print(i_berangkat,'////////??????????')

        df = pd.DataFrame(
            {
                "id": id,
                "vehicle": vehicle,
                "id_vehicle": id_vehicle,
                "seq": seq,
                "name": name,
                "datang": datang,
                "berangkat": berangkat,
                "distance": distance,
                "waktu": waktu,
                "driving_time": driving_time,
                "longitude": longitude,
                "latitude": latitude,
            }
        )

        point_gdf = gpd.GeoDataFrame(
            df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="epsg:4326"
        )
        # point_gdf.to_file('point.geojson')
        return point_gdf

    def make_points_all_new(self):
        vehicle_routes = {}
        vehicle = []
        vehicle_n = []
        name = []
        permintaan = []
        waktu = []
        distance = []
        datang = []
        berangkat = []
        driving_time = []
        longitude = []
        latitude = []
        id_vehicle = []
        seq = []
        id = []
        info = []
        for veh in range(self.len_vehicle):
            try:
                vehicle_routes[veh] = build_vehicle_route(
                    self.manager, self.routing, self.solution, self.orders, veh
                )
            except:
                pass
        veh_used = [v for v in vehicle_routes if vehicle_routes[v] is not None]
        print(veh_used)
        for vehicle_id in veh_used:
            i_distance = 0
            i_driving_time = 0
            i_datang = timedelta(seconds=0)
            i_datang2 = 0
            i_berangkat = timedelta(seconds=0)
            i_seq = 0
            i_waktu = 0
            req = 0
            index = self.routing.Start(vehicle_id)
            time_dimension = self.routing.GetDimensionOrDie("Time")
            while not self.routing.IsEnd(index):
                node_index = self.manager.IndexToNode(index)

                time_var = time_dimension.CumulVar(index)
                previous_index = index
                index = self.solution.Value(self.routing.NextVar(index))
                if node_index == self.depot:
                    i_berangkat = timedelta(seconds=self.solution.Min(time_var))
                    seq.append(0)
                    id_vehicle.append(self.vehicle.id[vehicle_id])
                    info.append("hub")
                    id.append(-1)
                    datang.append(str("00:00:00"))
                    berangkat.append(str(i_berangkat))
                    distance.append(i_distance)
                    waktu.append(i_waktu)
                else:
                    # i_waktu += self.time_matrix[node_index][self.manager.IndexToNode(index)] + float(self.service_time[node_index])*60
                    # i_distance += self.routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
                    # i_driving_time += self.solution.Min(time_var)
                    # i_datang = i_berangkat + timedelta(seconds=self.distance_matrix[node_index][self.manager.IndexToNode(index)]/2)
                    # i_berangkat = i_datang + timedelta(seconds=float(self.service_time[node_index])*60)

                    datang.append(str(i_datang))
                    berangkat.append(str(i_berangkat))
                    distance.append(i_distance)
                    waktu.append(i_waktu)

                    info.append("visit")
                    seq.append(i_seq)
                    id.append(self.orders.id[node_index])
                    id_vehicle.append(self.vehicle.id[vehicle_id])

                vehicle.append(self.vehicle.name[vehicle_id])
                name.append(self.orders.name[node_index])
                # print(i_berangkat,'////////??????????')
                driving_time.append(i_driving_time)
                longitude.append(self.orders.longitude[node_index])
                latitude.append(self.orders.latitude[node_index])

                # i_driving_time += self.solution.Min(time_var)
                i_driving_time += self.distance_matrix[
                    self.manager.IndexToNode(previous_index)
                ][self.manager.IndexToNode(index)]
                i_distance = self.routing.GetArcCostForVehicle(
                    previous_index, index, vehicle_id
                )
                # print(self.manager.IndexToNode(previous_index))
                # print(self.manager.IndexToNode(index))
                # print(self.distance_matrix[self.manager.IndexToNode(previous_index)][self.manager.IndexToNode(index)])
                i_waktu = self.distance_matrix[
                    self.manager.IndexToNode(previous_index)
                ][self.manager.IndexToNode(index)]
                # + float(self.service_time[self.manager.IndexToNode(index)])*60

                # i_berangkat += timedelta(seconds=self.solution.Min(time_var))
                # i_datang = i_berangkat - timedelta(seconds=float(self.service_time[self.manager.IndexToNode(index)])*60)
                # i_datang = i_berangkat + timedelta(seconds=self.distance_matrix[node_index][self.manager.IndexToNode(index)]/2)
                # i_datang += i_berangkat + timedelta(seconds=self.distance_matrix[self.manager.IndexToNode(previous_index)][self.manager.IndexToNode(index)])
                # i_berangkat = i_datang + timedelta(seconds=float(self.service_time[self.manager.IndexToNode(index)])*60)
                i_datang = i_berangkat + timedelta(
                    seconds=self.distance_matrix[
                        self.manager.IndexToNode(previous_index)
                    ][self.manager.IndexToNode(index)]
                )
                i_berangkat = i_datang + timedelta(
                    seconds=float(self.service_time[self.manager.IndexToNode(index)])
                    * 60
                )
                i_datang2 = i_datang
                i_seq += 1
            datang.append(str(i_datang))
            vehicle.append(self.vehicle.name[vehicle_id])
            seq.append(0)
            waktu.append(i_waktu)
            info.append("hub")
            id_vehicle.append(self.vehicle.id[vehicle_id])
            id.append(-1)
            name.append(self.orders.name[self.manager.IndexToNode(index)])
            distance.append(i_distance)
            datang[0] = str(i_datang)
            berangkat.append(berangkat[0])
            driving_time.append(i_driving_time)
            # vehstatement = ("""UPDATE vrp_app_saless SET used = true, remain_cap = {} WHERE vrp_app_saless.no = {}""".format(str(self.vehicle_capacities[vehicle_id]-req), str(vehicle_id+1)))
            # cursor2.execute(vehstatement)
            longitude.append(self.orders.longitude[self.manager.IndexToNode(index)])
            latitude.append(self.orders.latitude[self.manager.IndexToNode(index)])
        # print({'id':id,
        #                    'vehicle':vehicle,
        #                    'id_vehicle': id_vehicle,
        #                   'seq':seq,
        #                   'name':name,
        #                   'datang':datang,
        #                   'berangkat':berangkat,
        #                   'waktu': waktu,
        #                   'distance':distance,
        #                   'ket': info,
        #                   'longitude':longitude,
        #                   'latitude':latitude})
        df = pd.DataFrame(
            {
                "id": id,
                "vehicle": vehicle,
                "id_vehicle": id_vehicle,
                "seq": seq,
                "name": name,
                "datang": datang,
                "berangkat": berangkat,
                "waktu": waktu,
                "distance": distance,
                "ket": info,
                "longitude": longitude,
                "latitude": latitude,
            }
        )

        point_gdf = gpd.GeoDataFrame(
            df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="epsg:4326"
        )
        # point_gdf.to_file('point.geojson')
        return point_gdf

    def make_points_all(self):
        vehicle_routes = {}
        vehicle = []
        vehicle_n = []
        name = []
        permintaan = []
        distance = []
        datang = []
        berangkat = []
        driving_time = []
        longitude = []
        latitude = []
        id_vehicle = []
        seq = []
        for veh in range(self.len_vehicle):
            try:
                vehicle_routes[veh] = build_vehicle_route(
                    self.manager, self.routing, self.solution, self.orders, veh
                )
            except:
                pass
        veh_used = [v for v in vehicle_routes if vehicle_routes[v] is not None]
        for vehicle_id in veh_used:
            i_distance = 0
            i_driving_time = 0
            i_datang = timedelta(seconds=0)
            i_datang2 = 0
            i_berangkat = timedelta(seconds=0)
            i_seq = 1
            req = 0
            index = self.routing.Start(vehicle_id)
            time_dimension = self.routing.GetDimensionOrDie("Time")
            while not self.routing.IsEnd(index):
                node_index = self.manager.IndexToNode(index)

                time_var = time_dimension.CumulVar(index)
                previous_index = index
                index = self.solution.Value(self.routing.NextVar(index))
                if node_index == self.depot:
                    i_berangkat = timedelta(seconds=self.solution.Min(time_var))
                    seq.append(0)
                    id_vehicle.append(0)
                else:
                    seq.append(i_seq)
                    i_seq += 1
                    id_vehicle.append(self.orders.id_vehicle[node_index])
                vehicle.append(self.vehicle[vehicle_id])
                name.append(self.orders.name[node_index])
                distance.append(i_distance)
                datang.append(str(i_datang))
                berangkat.append(str(i_berangkat))
                driving_time.append(i_driving_time)
                longitude.append(self.orders.longitude[node_index])
                latitude.append(self.orders.latitude[node_index])
                # print(i_berangkat,'////////??????????')
                i_distance += self.routing.GetArcCostForVehicle(
                    previous_index, index, vehicle_id
                )
                i_driving_time += self.solution.Min(time_var)
                i_datang = i_berangkat + timedelta(
                    seconds=self.distance_matrix[node_index][
                        self.manager.IndexToNode(index)
                    ]
                    / 2
                )
                i_berangkat = i_datang + timedelta(
                    seconds=float(self.service_time[node_index]) * 60
                )
                i_datang2 = i_datang
            datang.append(str(i_datang))
            vehicle.append(self.vehicle[vehicle_id])
            seq.append(0)
            id_vehicle.append(0)
            name.append(self.orders.name[self.manager.IndexToNode(index)])
            distance.append(i_distance)
            berangkat.append(str(timedelta(seconds=0)))
            driving_time.append(i_driving_time)
            # vehstatement = ("""UPDATE vrp_app_saless SET used = true, remain_cap = {} WHERE vrp_app_saless.no = {}""".format(str(self.vehicle_capacities[vehicle_id]-req), str(vehicle_id+1)))
            # cursor2.execute(vehstatement)
            longitude.append(self.orders.longitude[self.manager.IndexToNode(index)])
            latitude.append(self.orders.latitude[self.manager.IndexToNode(index)])
        df = pd.DataFrame(
            {
                "vehicle": vehicle,
                "id_vehicle": id_vehicle,
                "seq": seq,
                "name": name,
                "datang": datang,
                "berangkat": berangkat,
                "distance": distance,
                "driving_time": driving_time,
                "longitude": longitude,
                "latitude": latitude,
            }
        )

        point_gdf = gpd.GeoDataFrame(
            df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="epsg:4326"
        )
        # point_gdf.to_file('point.geojson')
        return point_gdf

    def solving(self):
        # self.manager = pywrapcp.RoutingIndexManager(len(self.distance_matrix), self.len_vehicle, 0)

        time_matrix = [
            [int(j + (float(self.service_time[idx]) * 60)) for idx, j in enumerate(i)]
            for i in self.time_matrix
        ]

        self.manager = pywrapcp.RoutingIndexManager(
            len(time_matrix), self.len_vehicle, 0
        )

        # Create Routing Model.
        self.routing = pywrapcp.RoutingModel(self.manager)

        # Create and register a transit callback.
        def time_callback(from_index, to_index):
            """Returns the travel time between the two nodes."""
            # Convert from self.routing variable Index to time matrix NodeIndex.
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)
            return time_matrix[from_node][to_node]

        transit_callback_index = self.routing.RegisterTransitCallback(time_callback)

        # Define cost of each arc.
        self.routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Add Capacity constraint.
        def demand_callback(from_index):
            """Returns the demand of the node."""
            # Convert from self.routing variable Index to demands NodeIndex.
            from_node = self.manager.IndexToNode(from_index)
            return self.orders["demand"][from_node]

        # demand_callback_index = self.routing.RegisterUnaryTransitCallback(
        #     demand_callback
        # )
        # self.routing.AddDimensionWithVehicleCapacity(
        #     demand_callback_index,
        #     0,  # null capacity slack
        #     self.vehicle["capacity"].to_list(),  # vehicle maximum capacities
        #     True,  # start cumul to zero
        #     "Capacity",
        # )

        # penalty = 1000
        # for node in range(1, len(self.time_windows)):
        #     self.routing.AddDisjunction([self.manager.NodeToIndex(node)], penalty)

        # Add Time Windows constraint.
        time = "Time"
        self.routing.AddDimension(
            transit_callback_index,
            30,  # allow waiting time
            (
                self.time_windows[0][1] - self.time_windows[0][0]
            ),  # maximum time per vehicle
            False,  # Don't force start cumul to zero.
            time,
        )
        time_dimension = self.routing.GetDimensionOrDie(time)

        # Add time window constraints for each location except depot.
        for location_idx, time_window in enumerate(self.time_windows):
            if location_idx == 0:
                continue
            index = self.manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

        # Add time window constraints for each vehicle start node.
        for vehicle_id in range(self.len_vehicle):
            index = self.routing.Start(vehicle_id)
            time_dimension.CumulVar(index).SetRange(
                self.time_windows[0][0], self.time_windows[0][1]
            )

        # Instantiate route start and end times to produce feasible times.
        for i in range(self.len_vehicle):
            self.routing.AddVariableMinimizedByFinalizer(
                time_dimension.CumulVar(self.routing.Start(i))
            )
            self.routing.AddVariableMinimizedByFinalizer(
                time_dimension.CumulVar(self.routing.End(i))
            )

        # Setting first solution heuristic.
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.FromSeconds(2)
        # search_parameters.log_search = True

        # Solve the problem.
        self.solution = self.routing.SolveWithParameters(search_parameters)
        if self.solution:
            pass
