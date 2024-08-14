import csv
import requests
import networkx as nx
import folium
from tqdm import tqdm
import googlemaps
from jinja2 import Template
import polyline
from pyproj import Transformer
from folium import plugins
import os


API_KEY = 'AIzaSyD6NQgAw8rJbMfkCnYY6Y4zC_2W3ZUIMj8'
gmaps = googlemaps.Client(key=API_KEY)


# Read CSV file and construct a graph
def create_graph_from_csv(filename, G):
    route_id = filename.split('/')[-1].split('.')[0]
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)  # Skip the header row
        
        # add edges as stops are ordered in list
        edges = []
        last_place = None
        for row in csvreader:
            if row[0].startswith('//'):
                continue  # Skip comment lines
            place_name = row[0]
            latitude = float(row[1])
            longitude = float(row[2])
            G.add_node(place_name, latitude = latitude, longitude = longitude, routeId = route_id)
            if last_place:
                last_place_name = last_place[0]
                last_place_latitude = float(last_place[1])
                last_place_longitude = float(last_place[2])              
                url = f"https://maps.googleapis.com/maps/api/distancematrix/json?units=metric&origins={last_place_latitude},{last_place_longitude}&destinations={latitude},{longitude}&key={API_KEY}"
                response = requests.get(url)
                data = response.json()
                    
                if data['status'] == 'OK':
                    distance = data['rows'][0]['elements'][0]['distance']['value']
                edges.append((last_place_name, place_name, {'distance': distance, 'isRoute': True, 'isRouteShift': False}))
            last_place = row
        G.add_edges_from(edges)
        return G

def visualise_graph_map_folium(graph):
    print('Preparing Graph for visualization...')
    # Create a folium map centered at a specific location (e.g., the average of all latitude-longitude points)
    print(graph.nodes(data = True)[0][1])
    map_center = [sum(node[1]['latitude'] for node in graph.nodes(data=True)) / len(graph.nodes()),
                  sum(node[1]['longitude'] for node in graph.nodes(data=True)) / len(graph.nodes())]
    folium_map = folium.Map(location=map_center, zoom_start=13)

    # Add nodes to the map with latitude-longitude positions
    for node, data in graph.nodes(data=True):
        lat, lon = data['latitude'], data['longitude']
        folium.Marker([lat, lon], popup=node).add_to(folium_map)

    # Add edges (shortest path) to the map (extensively expensive in case of fully connected graph)
    for edge in tqdm(graph.edges(data=True)):
        src_node, dest_node, _ = edge
        src_lat, src_lon = graph.nodes[src_node]['latitude'], graph.nodes[src_node]['longitude']
        dest_lat, dest_lon = graph.nodes[dest_node]['latitude'], graph.nodes[dest_node]['longitude']
        directions = gmaps.directions((src_lat, src_lon), (dest_lat, dest_lon), mode="driving")
        if directions:
            path_coordinates = [(step['start_location']['lat'], step['start_location']['lng']) for step in directions[0]['legs'][0]['steps']]
            folium.PolyLine(path_coordinates, color="blue").add_to(folium_map)

    # Display the map in the browser
    folium_map.save('graph_map.html')

def get_route_polyline(start, end, mode):
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start[0]},{start[1]}&destination={end[0]},{end[1]}&mode={mode}&key={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "routes" in data and len(data["routes"]) > 0:
        return data["routes"][0]["overview_polyline"]["points"]
    return None

def google_to_openstreetmap(latitude, longitude):
    # Define the transformation using the appropriate EPSG codes
    google_maps_epsg = 4326  # WGS 84
    openstreetmap_epsg = 900913  # WGS 84 Web Mercator
    
    transformer = Transformer.from_crs(google_maps_epsg, openstreetmap_epsg, always_xy=True)
    
    # Perform the transformation
    openstreetmap_coordinates = transformer.transform(longitude, latitude)
    
    return openstreetmap_coordinates

def visualise_graph_map_folium_v2(graph):
    print('Preparing Graph for visualization...')
    # Create a folium map centered at a specific location (e.g., the average of all latitude-longitude points)
    map_center = [sum(node[1]['latitude'] for node in graph.nodes(data=True)) / len(graph.nodes()),
                  sum(node[1]['longitude'] for node in graph.nodes(data=True)) / len(graph.nodes())]
    folium_map = folium.Map(location=map_center, zoom_start=12)
    #folium.plugins.GoogleMaps(google_api_key=API_KEY).add_to(folium_map)

    # Define the URL pattern for Google Maps tiles
    google_maps_url = f'https://maps.googleapis.com/maps/api/staticmap?center={map_center[0]},{map_center[1]}&zoom={13}&size=256x256&maptype=roadmap&key={API_KEY}'
    # Define the custom tile layer using the Google Maps URL
    custom_tile_layer = folium.TileLayer(
        tiles=google_maps_url,
        attr='Google Maps',
        name='Google Maps',
        overlay=True,
        control=True
    )
    #custom_tile_layer.add_to(folium_map)

    # Add nodes to the map with latitude-longitude positions
    for node, data in graph.nodes(data=True):
        lat, lon = data['latitude'], data['longitude']
        folium.Marker((lat, lon), popup=node).add_to(folium_map)

     # Add edges (traveling route) to the map (extensively expensive in case of fully connected graph)
    for edge in tqdm(graph.edges(data=True)):
        src_node, dest_node, edge_data = edge
        src_lat, src_lon = graph.nodes[src_node]['latitude'], graph.nodes[src_node]['longitude']
        dest_lat, dest_lon = graph.nodes[dest_node]['latitude'], graph.nodes[dest_node]['longitude']
        if edge_data['isRoute']:
            route_polyline = get_route_polyline((src_lat, src_lon), (dest_lat, dest_lon), 'driving')
            folium.PolyLine(polyline.decode(route_polyline), color="blue").add_to(folium_map)
        elif edge_data['isRouteShift']:
            route_polyline = get_route_polyline((src_lat, src_lon), (dest_lat, dest_lon), 'walking')
            folium.PolyLine(polyline.decode(route_polyline), color="red").add_to(folium_map)

    # Save the map as an HTML file
    folium_map.save("./graph_with_google_maps.html")
    print('Map saved as "graph_with_google_maps.html"')



def get_route_coordinates(src_lat, src_lon, dest_lat, dest_lon):
    directions = gmaps.directions((src_lat, src_lon), (dest_lat, dest_lon), mode="driving")
    if directions:
        route = directions[0]["legs"][0]["steps"]
        return [(step["start_location"]["lat"], step["start_location"]["lng"]) for step in route]
    return []

def visualise_graph_map(graph):
    print('Preparing Graph for visualization...')
    
    # Create an HTML template for the Leaflet map
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Graph Map</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <style>
            #map {
                height: 500px;
            }
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <script>
            var map = L.map('map').setView([{{ center_lat }}, {{ center_lon }}], 13);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);

            {% for node in nodes %}
            L.marker([{{ node.lat }}, {{ node.lon }}]).addTo(map)
                .bindPopup("{{ node.label }}");
            {% endfor %}
            
            {% for edge in edges %}
            var latlngs = [
                {% for coord in edge.coords %}
                [{{ coord[0] }}, {{ coord[1] }}],
                {% endfor %}
            ];
            L.polyline(latlngs, {color: 'red'}).addTo(map);
            {% endfor %}
        </script>
    </body>
    </html>
    """

    # Create lists to store node and edge information
    nodes_data = [{'lat': data['latitude'], 'lon': data['longitude'], 'label': node}
                  for node, data in graph.nodes(data=True)]
    edges_data = []

    # Calculate the center of the map
    center_lat = sum(node['lat'] for node in nodes_data) / len(nodes_data)
    center_lon = sum(node['lon'] for node in nodes_data) / len(nodes_data)

    for src_node, dest_node, _ in graph.edges(data=True):
        src_lat, src_lon = graph.nodes[src_node]['latitude'], graph.nodes[src_node]['longitude']
        dest_lat, dest_lon = graph.nodes[dest_node]['latitude'], graph.nodes[dest_node]['longitude']
        route_coords = get_route_coordinates(src_lat, src_lon, dest_lat, dest_lon)
        edges_data.append({'coords': route_coords})

    # Fill in the HTML template with data
    html_content = Template(html_template).render(center_lat=center_lat, center_lon=center_lon,
                                                  nodes=nodes_data, edges=edges_data)

    # Write the HTML content to a file
    with open('graph_map_leaflet.html', 'w') as f:
        f.write(html_content)

def calculate_walking_distance(origin, destination):

    # Request the walking distance and duration
    distance_matrix = gmaps.distance_matrix(
        origin,
        destination,
        mode="walking"
    )

    # Extract the walking distance in meters and duration in seconds
    walking_distance = distance_matrix['rows'][0]['elements'][0]['distance']['value']
    walking_duration = distance_matrix['rows'][0]['elements'][0]['duration']['value']

    # Convert distance to kilometers and duration to minutes
    walking_distance_km = walking_distance / 1000
    walking_duration_min = walking_duration / 60

    return walking_distance, walking_duration

def add_route_shift_edges(G):
    walking_edges = []
    graph_components = list(nx.weakly_connected_components(G))
    for src_component in graph_components:
        min_dists_pair = []
        for src_item in tqdm(src_component):
            walking_distances_pairwise = [(src_item, dest_item, calculate_walking_distance((G.nodes[src_item]['latitude'], G.nodes[src_item]['longitude']),(G.nodes[dest_item]['latitude'], G.nodes[dest_item]['longitude']))[0])
             for dest_component in graph_components if src_component != dest_component
                               for dest_item in dest_component]
            min_dists_pairs = min(walking_distances_pairwise, key=lambda x: x[2])
            min_dists_pair.append(min_dists_pairs)
        min_dist_pair = min(min_dists_pair, key=lambda x: x[2])
        walking_edges.append((min_dist_pair[0], min_dist_pair[1], {'distance': min_dist_pair[2], 'isRouteShift': True, 'isRoute': False}))
    print(walking_edges)
    G.add_edges_from(walking_edges)
    return G
# Main function
if __name__ == "__main__":
    graph = nx.DiGraph()

    # folder_path = os.path.join(os.getcwd(), 'routes')
    folder_path = r'G:\Route Optimization\Routes CSV'
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]
    csv_paths = [os.path.join(folder_path, csv_file) for csv_file in csv_files]

    for route_csv in csv_paths:
        graph = create_graph_from_csv(route_csv, graph)
    ###graph = add_route_shift_edges(graph)

    nx.write_graphml(graph, "isb_pt_net.graphml")
    visualise_graph_map_folium_v2(graph)