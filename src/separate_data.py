from collections import namedtuple

routes = [
"Red",
"P",
"Y",
"Blue",
"Pink",
"G",
"Org",
"Brn",
]

Trip = namedtuple('Trip', ['route_id','service_id','trip_id','direction_id','block_id','shape_id','direction','wheelchair_accessible','schd_trip_id'])


def main():
    service_ids = {}
    shape_ids = {}
    trip_ids = {}
    stop_ids = {}

    # Read and change the trips
    with open('/Users/mskobov/repos/gtfs/data/chicago/trips.txt', 'r') as orig_f:
        with open('/Users/mskobov/repos/gtfs/data/chicago/trains/trips.txt', 'w') as trains_f:
            line = orig_f.readline()
            trains_f.write(line)
            trains_f.write('\n')

            while line:
                line = orig_f.readline().replace('\n', '')
                components = line.split(',')
                if components[0] in routes:
                    trains_f.write(line)
                    trains_f.write('\n')
                    trip = Trip(*components)

                    if trip.shape_id not in shape_ids:
                        shape_ids[trip.shape_id] = trip

                    if trip.service_id not in service_ids:
                        service_ids[trip.service_id] = trip

                    if trip.trip_id not in trip_ids:
                        trip_ids[trip.trip_id] = trip

    # Read shapes data
    with open('/Users/mskobov/repos/gtfs/data/chicago/shapes.txt', 'r') as orig_f:
        with open('/Users/mskobov/repos/gtfs/data/chicago/trains/shapes.txt', 'w') as trains_f:
            line = orig_f.readline().replace('\n', '')
            trains_f.write(line)
            trains_f.write('\n')
            components = line.split(',')
            Shape = namedtuple('Shape', components)

            while line:
                line = orig_f.readline().replace('\n', '')
                components = line.split(',')

                if len(components) == 1:
                    break

                shape = Shape(*components)

                if shape.shape_id in shape_ids:
                    trains_f.write(line)
                    trains_f.write('\n')

    with open('/Users/mskobov/repos/gtfs/data/chicago/stop_times.txt', 'r') as orig_f:
        with open('/Users/mskobov/repos/gtfs/data/chicago/trains/stop_times.txt', 'w') as trains_f:
            line = orig_f.readline()
            trains_f.write(line)
            trains_f.write('\n')
            components = line.replace('\n', '').split(',')
            StopTime = namedtuple('StopTime', components)

            while line:
                line = orig_f.readline().replace('\n', '')
                components = line.split(',')
                if len(components) == 1:
                    break
                stop_time = StopTime(*components)

                if stop_time.trip_id in trip_ids:
                    trains_f.write(line)
                    trains_f.write('\n')

                    if stop_time.stop_id not in stop_ids:
                        stop_ids[stop_time.stop_id] = stop_time

    with open('/Users/mskobov/repos/gtfs/data/chicago/stops.txt', 'r') as orig_f:
        with open('/Users/mskobov/repos/gtfs/data/chicago/trains/stops.txt', 'w') as trains_f:
            line = orig_f.readline().replace('\n', '')
            trains_f.write(line)
            trains_f.write('\n')
            components = line.split(',')
            Stop = namedtuple('Stop', components)

            while line:
                line = orig_f.readline()
                components = line.split(',')
                if len(components) == 1:
                    break

                if len(components) >= 10:
                    final_components = []
                    start_index = None
                    for i in range(len(components)):
                        if components[i].startswith('"') and not components[i].endswith('"'):
                            start_index = i
                        elif components[i].endswith('"') and not components[i].startswith('"'):
                            component = ', '.join(components[start_index:i+1])
                            final_components.append(component)
                            start_index = None
                        elif not start_index:
                            final_components.append(components[i])
                    components = final_components

                stop = Stop(*components)

                if stop.stop_id in stop_ids:
                    trains_f.write(line)
                    trains_f.write('\n')

    print('Done')


if __name__ == '__main__':
    main()