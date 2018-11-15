
#Ben Kotrc
#1/26/2016
#This script takes an expanded GTFS file and generates a new file,
#route_shapes.json, that contains one geojson MultiLineString for each
#entry in the GTFS routes.txt table. This represents the map shape for
#each route, including possible variations/line branches/etc, simplified
#using the Douglas-Peucker algorithm for a minimal resulting file size.

#Approach:
#For each route,
#1 - Get the set of shapes corresponding to the route;
#2 - Select the longest shape (with the most coordinate pairs);
#3 - Draw a buffer around this longest shape;
#4 - For each remaining shape,
#a - Remove points from the shape within the buffered area,
#b - Add the remaining shape to the longest shape as an additional
#    LineString in the MultiLineString

#Run this from within a directory containing the GTFS csv files.

#pandas lets us use data frames to load and store the GTFS tables
import pandas as pd
#geojson lets us construct and dump geojson objects
import geojson as gj
#shapely lets us manipulate geometric objects
import shapely.geometry as sh
from shapely.ops import nearest_points
import math


LINE_SEPARATION_DISTANCE = 0.0001

class Vertex:
    def __init__(self):
        self.coord = None
        self.routes = []
        self.edges = []
        self.slope = None
        self.orthogonal = None
        self.line = None
        self.offset = None

    def get_point(self, route):
        if not self.line or not self.offset:
            return (self.coord.x, self.coord.y)

        index = self.line.sort_order.index(route)
        offset_x = index * self.offset[0]
        offset_y = index * self.offset[1]

        return (self.coord.x + offset_x, self.coord.y + offset_y)


class Line:
    def __init__(self):
        self.coords = {}
        self.sort_order = []
        self.endpoints = []


#Read relevant GTFS tables to pandas dataframes
stops = pd.read_csv('/Users/mskobov/repos/gtfs/data/chicago/trains/stops.txt')
shapes = pd.read_csv('/Users/mskobov/repos/gtfs/data/chicago/trains/shapes.txt')
routes = pd.read_csv('/Users/mskobov/repos/gtfs/data/chicago/trains/routes.txt')
stop_times = pd.read_csv('/Users/mskobov/repos/gtfs/data/chicago/trains/stop_times.txt')
trips = pd.read_csv('/Users/mskobov/repos/gtfs/data/chicago/trains/trips.txt')

#Join routes table to trips table on route_id
routes_trips = pd.merge(routes, trips, on='route_id', how='inner')
#Join this table to shapes on shape_id
routes_trips_shapes = pd.merge(routes_trips, shapes, on='shape_id',
    how='inner')

#Now we want to get rid of all the columns we don't need
#These are the ones we want:
colsretain = ['route_id',
    'agency_id',
    'route_short_name',
    'route_long_name',
    'shape_id',
    'shape_pt_lat',
    'shape_pt_lon',
    'shape_pt_sequence',
    'shape_dist_traveled']
#These are the ones we have:
colshave = routes_trips_shapes.columns.values
#These are the ones we no longer want
to_drop = list(set(colshave) - set(colsretain))
#Drop them from the dataFrame
routes_trips_shapes = routes_trips_shapes.drop(to_drop, axis=1)

#Since we've thrown out all the columns dealing with trips, there will be a lot
#of duplicate rows. Let's get rid of those.
routes_trips_shapes = routes_trips_shapes.drop_duplicates()

#Create a list to hold each route's shape to write them to file at the end:
route_shape_list = list()

route_multiline_dict = {}

#Go through each route
for route_id in routes_trips_shapes['route_id'].unique():
    #Get the set of shapes corresponding to this route_id
    shape_ids = set(routes_trips_shapes[routes_trips_shapes['route_id']
            == route_id]['shape_id'])
    #First, find the longest shape for this route
    #Call the first shape in this route the longest to start with
    longest = shape_ids.pop()
    shape_ids.add(longest)
    #Keep track of how many points the longest shape has
    longest_pt_num = shapes[shapes['shape_id']
        == longest]['shape_pt_sequence'].count()
    #Go through each shape in this route
    for shape_id in shape_ids:
        #If this shape has more points in this shape with the longest so far
        if shapes[shapes['shape_id']
            == shape_id]['shape_pt_sequence'].count() > longest_pt_num:
            #Designate this shape as the longest
            longest = shape_id
            #And keep track of the number of points
            longest_pt_num = shapes[shapes['shape_id']
            == shape_id]['shape_pt_sequence'].count()
    #End loop through each shape in this route
    #Now that we have the longest shape for the route, create a shapely
    #LineString for this route ID
    multiline = sh.LineString(zip(shapes[shapes['shape_id']
        == longest]['shape_pt_lon'].tolist(),
        shapes[shapes['shape_id'] == longest]['shape_pt_lat'].tolist()))
    #Now let's add the parts of the other shapes that don't overlap with this
    #longest shape to create a MultiLineString collection
    #First create an area within which we'll reject additional points
    #(this buffer--0.0001 deg--is about 30m, or about the width of Mass Ave)
    # Changing the buffer to .00005
    area = multiline.buffer(0.00005)

    # Temporarily do NOT add the shorter shapes

    #Get the set of shapes (other than the longest one) to loop over
    # shorter_shape_ids = shape_ids
    # shorter_shape_ids.remove(longest)



    #Now to go through them, and add only the points from each shape that
    #aren't in the area.
    # for shape_id in shorter_shape_ids:
    #     #Get the current shape as a shapely shape
    #     this_shape = sh.LineString(zip(shapes[shapes['shape_id']
    #         == shape_id]['shape_pt_lon'].tolist(),
    #         shapes[shapes['shape_id'] == shape_id]['shape_pt_lat'].tolist()))
    #     #Is this shape entirely within the existing area?
    #     if not this_shape.within(area):
    #         #If there are points outside the area, add to the MultiLineString
    #         new_part = this_shape.difference(area)
    #         #Now add this new bit to the MultiLineString
    #         multiline = multiline.union(new_part)
    #         #Now update the testing area to include this new line
    #         area = multiline.buffer(0.00005)


    # This adds simplification - don't use this right now
    '''
    #Now we have a shapely MultiLineString object with the lines making
    #up shape of this route. Next, simplify that object:
    tolerance = 0.000025
    simplified_multiline = multiline.simplify(tolerance, preserve_topology=False)
    
    #Turn the MultiLine into a geoJSON feature object, and add it to the list
    #of features that'll be written to file as a featurecollection at the end
    route_shape_list.append(gj.Feature(geometry=simplified_multiline,
        properties={"route_id": route_id}))
    #End of loop through all routes
    '''

    # If it's a multiline, add it, otherwise add iterable
    if isinstance(multiline, sh.LineString):
        route_multiline_dict[route_id] = [multiline]
    else:
        route_multiline_dict[route_id] = multiline

    route_shape_list.append(gj.Feature(geometry=multiline,
                                       properties={"route_id": route_id}))


# Create the geometries that exclude a route, like "not_Blue"

not_geometries = {}
for route_id in route_multiline_dict:
    other_area = None
    for other_route_id in route_multiline_dict:
        if route_id == other_route_id:
            continue

        for line in route_multiline_dict[other_route_id]:
            if not other_area:
                other_area = line.buffer(.0005)
            else:
                other_area = other_area.union(line.buffer(.0005))

    not_geometries[route_id] = other_area



# TODO: Set buffer size to the minimum distance between any two points!

# Tracks the overall global points as a geometry
global_multipoint = sh.MultiPoint()

# Tracks all the "global" vertices
vertices = {}

# Tracks the route -> [vertices]
route_vertex_dict = {}

INTERPOLATED_DISTANCE = 0.0005

for route_id in route_multiline_dict:
    for route_line in route_multiline_dict[route_id]:

        # This is the last vertex created for the line
        previous_vertex = None

        route_vertex_dict[route_id] = []

        for curr_coords in route_line.coords:
            interpolated_points = []
            if previous_vertex:
                this_point = sh.Point(curr_coords)

                if not this_point.intersects(not_geometries[route_id]):
                    # If this point doesn't intersect any other routes, just add it
                    interpolated_points.append(curr_coords)
                else:
                    # delta_x = (curr_coords[0] - previous_vertex.coord.x)
                    # delta_y = (curr_coords[1] - previous_vertex.coord.y)
                    # distance_from_previous = math.sqrt(math.pow(delta_x, 2) + math.pow(delta_y, 2))
                    #
                    # if distance_from_previous > INTERPOLATED_DISTANCE:
                    #     discrete_fit = int(round(distance_from_previous / INTERPOLATED_DISTANCE))
                    #     const_offset_x = delta_x / discrete_fit
                    #     const_offset_y = delta_y / discrete_fit
                    #
                    #     for i in range(0, discrete_fit):
                    #         offset_x = (i + 1) * const_offset_x
                    #         offset_y = (i + 1) * const_offset_y
                    #         interpolated_points.append(((previous_vertex.coord.x + offset_x), (previous_vertex.coord.y + offset_y)))
                    # else:
                    #    interpolated_points.append(curr_coords)
                    interpolated_points.append(curr_coords)
            else:
                interpolated_points.append(curr_coords)

            for int_point in interpolated_points:
                curr_point = sh.Point(int_point)
                point_area = curr_point.buffer(0.00005)

                # This point doesn't exist on the map yet
                if not point_area.intersects(global_multipoint):
                    new_vertex = Vertex()
                    new_vertex.coord = curr_point
                    new_vertex.routes.append(route_id)

                    # Store this vertex as part of global set
                    vertices[(curr_point.x, curr_point.y)] = new_vertex

                    # Add the created vertex to the route
                    route_vertex_dict[route_id].append(new_vertex)

                    # Store this point in the global multipoint
                    global_multipoint = global_multipoint.union(curr_point)

                    if previous_vertex:
                        previous_vertex.edges.append(new_vertex)
                        new_vertex.edges.append(previous_vertex)

                    # Set the new vertex to previous vertex
                    previous_vertex = new_vertex

                else:
                    # This point intersects with the current map!
                    nearest_point = nearest_points(global_multipoint, curr_point)[0]

                    # Get the vertex for it
                    existing_vertex = vertices[(nearest_point.x, nearest_point.y)]

                    # Add the route to this vertex
                    if route_id not in existing_vertex.routes:
                        existing_vertex.routes.append(route_id)

                    if previous_vertex:
                        if previous_vertex not in existing_vertex.edges:
                            existing_vertex.edges.append(previous_vertex)
                        if existing_vertex not in previous_vertex.edges:
                            previous_vertex.edges.append(existing_vertex)

                    # Add this vertex to the route
                    route_vertex_dict[route_id].append(existing_vertex)

                    # Set the found vertex to previous to keep going
                    previous_vertex = existing_vertex

# Maps all the joint lines "G, Pink" -> {coord: vertex}
# Also contains the sorted order!
lines = {}

for coord in vertices:
    vertex = vertices[coord]

    if len(vertex.routes) > 1:
        line_string = ','.join(sorted(vertex.routes))

        if line_string not in lines:
            new_line = Line()
            lines[line_string] = new_line

        # Let the vertex point to the line so it can get the sort order later
        vertex.line = lines[line_string]

        # Get the edges for slope calculation
        same_line_edges = [edge for edge in vertex.edges if sorted(edge.routes) == sorted(vertex.routes)]

        if same_line_edges:
            # If only one exists, we're at the beginning
            if len(same_line_edges) == 1:
                if vertex.coord.x == same_line_edges[0].coord.x:
                    slope = float('-inf')
                    orthogonal = 0
                else:
                    slope = (vertex.coord.y - same_line_edges[0].coord.y) / (vertex.coord.x - same_line_edges[0].coord.x)
                    orthogonal = 0 - (1 / slope) if slope else float('-inf')

                vertex.slope = slope
                vertex.orthogonal = orthogonal

            # If 2 exist, we're in the middle
            elif len(same_line_edges) == 2:
                if same_line_edges[0].coord.x == same_line_edges[1].coord.x:
                    slope = float('-inf')
                    orthogonal = 0
                else:
                    slope = (same_line_edges[0].coord.y - same_line_edges[1].coord.y) / (same_line_edges[0].coord.x - same_line_edges[1].coord.x)
                    orthogonal = 0 - (1/slope) if slope else float('-inf')

                vertex.slope = slope
                vertex.orthogonal = orthogonal

            # If 3+ exist, there's an error somewhere...
            elif len(same_line_edges) == 3:
                print('Hmm... shouldnt have 3...')

            if vertex.slope is not None:
                if vertex.slope == float('-inf'):
                    vertex.offset = (LINE_SEPARATION_DISTANCE, 0)
                elif vertex.slope == 0:
                    vertex.offset = (0, LINE_SEPARATION_DISTANCE)
                else:
                    r = math.sqrt(1 + math.pow(vertex.orthogonal, 2))
                    vertex.offset = (LINE_SEPARATION_DISTANCE/r, LINE_SEPARATION_DISTANCE * vertex.orthogonal / r)

        # Map the vertex to the line as well
        lines[line_string].coords[coord] = vertex

# TODO: Technically, we want to visit every node at every line, to account for cases where some lines
# may be next to one another at multiple points in space. Chicago is relatively simple
for line_name in lines:
    line = lines[line_name]

    for coord in line.coords:
        # We want to find the start of this line (at either direction)
        # Do a super simple check: if this vertex connects to something not in the line, it must be an endpoint
        vertex = line.coords[coord]
        for edge in vertex.edges:
            coord_tuple = (edge.coord.x, edge.coord.y)
            if coord_tuple not in line.coords:
                line.endpoints.append(vertex)
                break


LINE_ORDERING = {
'Brn,G,Org,P,Pink,Red': ["Brn","G","Org","P","Pink","Red"],
'Brn,P,Red': ["Brn","P","Red"],
'P,Red': ["P","Red"],
'P,Red,Y': ["P","Red","Y"],
'G,Org,Red': ["G","Org","Red"],
'G,Red': ["G","Red"],
'P,Y': ["P","Y"],
'Brn,P': ["Brn","P"],
'Blue,Brn,G,Org,P,Pink': ["Blue","Brn","G","Org","P","Pink"],
'Brn,G,Org,P,Pink': ["Brn","G","Org","P","Pink"],
'Brn,Org,P,Pink': ["Brn","Org","P","Pink"],
'Blue,Brn,Org,P,Pink': ["Blue","Brn","Org","P","Pink"],
'G,Pink': ["G","Pink"],
'G,Org': ["G","Org"],
'Brn,Org,P,Pink,Red': ["Brn", "Org", "P", "Pink", "Red"],
'Blue,G,Pink': ["Blue","G","Pink"],
}

for line in lines:
    lines[line].sort_order = LINE_ORDERING[line]

import time
time_ns = time.time_ns()
modified_routes = []
modified_route_points = []
for route in route_vertex_dict:
    route_points = [v.get_point(route) for v in route_vertex_dict[route]]

    route_line = sh.LineString(route_points)

    # for point in route_points:
    #     gj_point = gj.Point((point[0], point[1]))
    #     modified_route_points.append(gj.Point(geometry=gj_point,
    #                                       properties={"route_id": route}))

    modified_routes.append(gj.Feature(geometry=route_line,
                                       properties={"route_id": route}))

print(time.time_ns() - time_ns)


with open('new_route_lines.geojson', 'w') as outfile:
    gj.dump(gj.FeatureCollection(modified_routes), outfile)

with open('new_route_points.geojson', 'w') as outfile:
    gj.dump(gj.FeatureCollection(modified_route_points), outfile)

# for vertex in route_vertex_dict['Blue']:
#     print('[\n %s,\n %s\n],' % vertex.get_point('Blue'))

# TODO: build graph at the same time as line
# for each route, get overlap and non-overlap
# for overlap, find the edges/vertices and add route id to those
# for non overlap, create vertices/edges and add non-overlap to multiline