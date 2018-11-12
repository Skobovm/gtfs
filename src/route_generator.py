from collections import namedtuple
import json

Trip = namedtuple('Trip', ['route_id','service_id','trip_id','direction_id','block_id','shape_id','direction','wheelchair_accessible','schd_trip_id'])
Shape = namedtuple('Shape', ['shape_id','shape_pt_lat','shape_pt_lon','shape_pt_sequence','shape_dist_traveled'])


def main():
    paths = {}
    trips = {}
    shapes = {}

    with open('/Users/mskobov/repos/gtfs/data/chicago/trains/shapes.txt', 'r') as shape_f:
        line = shape_f.readline().replace('\n', '')

        # Skip the first one
        line = shape_f.readline().replace('\n', '')

        while line:
            components = line.split(',')
            shape = Shape(*components)

            if shape.shape_id not in shapes:
                shapes[shape.shape_id] = []
            shapes[shape.shape_id].append(shape)

            line = shape_f.readline().replace('\n', '')

    with open('/Users/mskobov/repos/gtfs/data/chicago/trains/trips.txt', 'r') as trip_f:
        line = trip_f.readline().replace('\n', '')

        # Skip the first one
        line = trip_f.readline().replace('\n', '')

        while line:
            components = line.split(',')
            trip = Trip(*components)

            if trip.shape_id in shapes:
                if trip.route_id not in paths:
                    paths[trip.route_id] = {}

                if trip.shape_id not in paths[trip.route_id]:
                    paths[trip.route_id][trip.shape_id] = shapes[trip.shape_id]
            else:
                print('Shape doesnt exist')

            line = trip_f.readline().replace('\n', '')

    for route in paths:
        shapes = paths[route]
        shapes_to_remove = []

        for shape_1 in shapes:
            for shape_2 in shapes:
                if shape_1 == shape_2:
                    continue

                if len(shapes[shape_1]) == len(shapes[shape_2]):
                    # Same length - double check the coords
                    if shapes[shape_1][0].shape_pt_lat == shapes[shape_2][-1].shape_pt_lat:
                        # Same path, remove one
                        if shape_1 not in shapes_to_remove and shape_2 not in shapes_to_remove:
                            shapes_to_remove.append(shape_2)

        for shape in shapes_to_remove:
            shapes.pop(shape)


    with open('/Users/mskobov/repos/gtfs/data/chicago/trains/paths.json', 'w') as path_f:
        path_f.write(json.dumps(paths))

if __name__ == '__main__':
    main()