import json

KML_TEMPLATE_FILE = '/Users/mskobov/repos/gtfs/src/kml_template.xml'
LINE_KML_TEMPLATE_FILE = '/Users/mskobov/repos/gtfs/src/line_kml_template.xml'
JOINT_TEMPLATE_FILE = '/Users/mskobov/repos/gtfs/src/line_string_template.xml'

COLORS = {
    'Blue': 'F04614',
    'Brn': '143C78',
    'G': '14B400',
    'Org': '1478FA',
    'P': '780078',
    'Pink': '783CF0',
    'Red': '1400FF',
    'Y': '14F0FF'
}

def main():
    with open('/Users/mskobov/repos/gtfs/data/chicago/trains/paths.json', 'r') as path_f:
        paths = json.loads(path_f.read())

    with open(KML_TEMPLATE_FILE) as kml_temp:
        kml_template = kml_temp.read()


    for route in paths:
        for shape in paths[route]:
            coordinates = []
            for coord in paths[route][shape]:
                coordinates.append('%s,%s,100' % (coord[2], coord[1]))

            coord_string = '\n          '.join(coordinates)
            kml_file_str = kml_template.replace('__COORDS__', coord_string).replace('__COLOR__', COLORS[route]).replace('__NAME__', route)

            with open('/Users/mskobov/repos/gtfs/data/chicago/trains/paths/%s_%s.kml' % (route, shape), 'w') as kml_file:
                kml_file.write(kml_file_str)

def joint_vertex_generator():
    with open('/Users/mskobov/repos/gtfs/data/chicago/trains/joint_vertices.json', 'r') as v_f:
        joint_vertices = json.loads(v_f.read())

    with open(LINE_KML_TEMPLATE_FILE) as kml_temp:
        kml_template = kml_temp.read()

    with open(JOINT_TEMPLATE_FILE) as joint_temp:
        line_template = joint_temp.read()

    line_strings = []
    curr_route = None
    curr_line_coords = []
    for coord in joint_vertices:
        route = json.dumps(joint_vertices[coord][1]).replace('"', '').replace('[', '').replace(']', '')

        if route != curr_route:
            # Create line string
            if curr_line_coords:
                coord_string = '\n          '.join(curr_line_coords)
                line_str = line_template.replace('__COORDS__', coord_string).replace('__NAME__', curr_route)
                line_strings.append(line_str)

            # Reset
            curr_line_coords = []
            # Start a new route
            curr_route = route

        coord_components = coord.split(',')
        curr_line_coords.append('%s,%s,100' % (coord_components[1], coord_components[0]))

    kml_file_str = kml_template.replace('__LINESTRINGS__', '\n'.join(line_strings))
    with open('/Users/mskobov/repos/gtfs/data/chicago/trains/paths/joint_routes.kml', 'w') as kml_file:
        kml_file.write(kml_file_str)


if __name__ == "__main__":
    #main()
    joint_vertex_generator()