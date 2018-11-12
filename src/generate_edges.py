# d < 0.001
from collections import namedtuple
import json
import math

# NOTE: This is a STUPID algorithm... a structure should be used to track "regions"

EdgeVertex = namedtuple('EdgeVertex', ['points', 'routes'])

DISTANCE_THRESHOLD = 0.001
REAL_DIST_THRESH = 0.0001

def main():
    joint_vertices = {}

    with open('/Users/mskobov/repos/gtfs/data/chicago/trains/paths.json', 'r') as path_f:
        paths = json.loads(path_f.read())

    first_route = True
    for route in paths:
        if first_route:
            # Add the first route without checking anything
            for shape_id in paths[route]:
                shape = paths[route][shape_id]

                for point in shape:
                    vertex_key = '%s,%s' % (point[1], point[2])
                    vertex = EdgeVertex([(float(point[1]), float(point[2]))], [route])

                    joint_vertices[vertex_key] = vertex

            first_route = False

        else:
            # All other routes
            for shape_id in paths[route]:
                shape = paths[route][shape_id]

                for point in shape:
                    add_point = True
                    point_long = float(point[1])
                    point_lat = float(point[2])
                    for vertex_key in joint_vertices:
                        key_long_str, key_lat_str = vertex_key.split(',')
                        key_long = float(key_long_str)
                        key_lat = float(key_lat_str)

                        if math.fabs(point_long - key_long) < DISTANCE_THRESHOLD and math.fabs(point_lat - key_lat) < DISTANCE_THRESHOLD:
                            # Compute the distance and see if it should be added to the point!
                            distance = math.sqrt(math.pow(point_lat - key_lat, 2) + math.pow(point_long - key_long, 2))
                            if distance < REAL_DIST_THRESH:
                                add_point = False
                                edge_vertex = joint_vertices[vertex_key]

                                if route not in edge_vertex.routes:
                                    edge_vertex.routes.append(route)

                                edge_vertex.points.append((point_long, point_lat))
                                break

                    if add_point:
                        vertex = EdgeVertex([(point_long, point_lat)], [route])
                        new_vertex_key = '%s,%s' % (point_long, point_lat)
                        joint_vertices[new_vertex_key] = vertex

    with open('/Users/mskobov/repos/gtfs/data/chicago/trains/joint_vertices.json', 'w') as f:
        f.write(json.dumps(joint_vertices))

if __name__ == '__main__':
    main()