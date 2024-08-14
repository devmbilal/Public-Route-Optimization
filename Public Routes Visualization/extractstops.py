import requests
import csv
import math
import os
import networkx as nx
import googlemaps
import folium
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt

API_KEY = 'AIzaSyA9B-sHX-s-SOeuYKRsNHwCUuywzXvLHc0'
STOPS_FIlENAME = 'bus_stops.csv'
GRAPH_FILENAME = 'isb_pt_net.graphml'
gmaps = googlemaps.Client(key=API_KEY)

def _get_bus_stops(api_key, latitude, longitude, radius, keyword):
    """
    This function extracts and returns a list of bus stops around a given latitude-longitude point within the given radius.

    Params:
        api_key -- API key
        latitude -- latitude of the target point on map.
        longitude -- longitude of the target point on map.
        radius -- radius of the circular area around the point that will be scanned for bus stops
        keyword -- key word that is used to make query to Google Maps AIP, e.g. 'public transport'

    Returns:
        List of dictionaries; Each dictionary contains data for one bus stop.
    """
    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    bus_stops = []

    params = {
        'location': f"{latitude},{longitude}",
        'radius': radius,
        'keyword': keyword,
        'key': api_key 
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data['status'] != 'OK':
        #print('Error occurred:', data['status'])
        return bus_stops

    for result in tqdm(data['results'], leave=False):
        try:
            compound_code = result['plus_code']['compound_code']
        except:
            compound_code = None
        try:
            vicinity = result['vicinity']
        except:
            vicinity = None

        stop = {
            'name': result['name'],
            'latitude': result['geometry']['location']['lat'],
            'longitude': result['geometry']['location']['lng'],
            'compound_code': compound_code,
            'vicinity' : vicinity,
            'place_id': result['place_id']
        }

        if (compound_code and 'Islamabad' in compound_code) or (vicinity and'Islamabad' in vicinity):
            bus_stops.append(stop)
    return bus_stops
def _get_origions(start_latitude, start_longitude, num_intervals):
    """
    This function returns a list of lat-long points, forming a grid in north-east direction starting from given lat-long point.

    Params:
        start_latitude -- latitude value of starting point
        start_longitude -- longitude value of starting point
        num_intervals -- number of points in grid's each side

    Returns:
        List of lat-long points (tuples)
    """
    delta_latitude = 2 / 111  # Change in latitude for 2km interval
    delta_longitude = 2 / (111 * math.cos(math.radians(start_latitude)))  # Change in longitude for 2km interval
    origions = []

    for i in range(num_intervals):
        latitude = start_latitude + i * delta_latitude
        for j in tqdm(range(num_intervals), leave=False):
            longitude = start_longitude + j * delta_longitude
            origions.append((latitude, longitude))
    return origions
def navigate_square_area(start_latitude, start_longitude, num_intervals, api_key):
    """
    This function returns a list of bus stops in a rectangular area on map stretched towards north-east direction from the starting point.

    Params:
        start_latitude -- latitude value of starting point
        start_longitude -- longitude value of starting point
        num_intervals -- number of points the grid is stretched towards both sides (north and east)
        api_key -- API key

    Returns:
        List of dictionaries; Each dictionary contains data for one bus stop.
    """
    delta_latitude = 2 / 111  # Change in latitude for 2km interval
    delta_longitude = 2 / (111 * math.cos(math.radians(start_latitude)))  # Change in longitude for 2km interval

    bus_stops = []
    for i in tqdm(range(num_intervals)):
        latitude = start_latitude + i * delta_latitude
        for j in tqdm(range(num_intervals), leave=False):
            longitude = start_longitude + j * delta_longitude
            # Retrieve bus stops for the current lat-long location
            stops = _get_bus_stops(api_key, latitude, longitude, 2000, 'public transport')
            bus_stops.extend(stops)
    # Get unique bus stops
    unique_bus_stops = []
    unique_stops_ids = []
    for bus_stop in bus_stops:
        if bus_stop['place_id'] not in unique_stops_ids:
            unique_bus_stops.append(bus_stop)
            unique_stops_ids.append(bus_stop['place_id'])
    return unique_bus_stops

def get_distance(source_lat, source_lon, dest_lat, dest_lon):
    """
    Function to get the distance between two coordinates using Google Maps API
    """
    directions = gmaps.directions((source_lat, source_lon), (dest_lat, dest_lon), mode="driving")
    if directions:
        return directions[0]['legs'][0]['distance']['value']
    return None

def create_network_graph(csv_file):
    """
    Read stops data (nodes) from CSV file, extract edge data from Google Map and create network graph.
    """
    df = pd.read_csv(csv_file, sep='|')

    G = nx.Graph()
    for _, row in tqdm(df.iterrows(), desc="Adding nodes...", unit=' Nodes'):
        place_id = row['place_id']
        G.add_node(place_id, name=row['name'], latitude=row['latitude'], longitude=row['longitude'],
                   compound_code=row['compound_code'], vicinity=row['vicinity'])
    print(str(len(df)) + " Nodes have been added to Graph successfuly!")
    nodes = G.nodes()
    for src_node in tqdm(nodes, desc="Adding edges...", unit=' Nodes'):
        for dest_node in tqdm(nodes, leave=False):
            if src_node != dest_node and not G.has_edge(src_node, dest_node):
                src_lat, src_lon = G.nodes[src_node]['latitude'], G.nodes[src_node]['longitude']
                dest_lat, dest_lon = G.nodes[dest_node]['latitude'], G.nodes[dest_node]['longitude']
                distance = get_distance(src_lat, src_lon, dest_lat, dest_lon)
                if distance:
                    G.add_edge(src_node, dest_node, distance=distance, is_route = False, route_id = '', fare = 0)
    print(str(len(nodes) * len(nodes)) + " Edges have been added to Graph successfuly!")
    return G

def visualise_graph_map(graph, corners):
    print('Preparing Graph for visualization...')
    # Create a folium map centered at a specific location (e.g., the average of all latitude-longitude points)
    map_center = [sum(node[1]['latitude'] for node in graph.nodes(data=True)) / len(graph.nodes()),
                  sum(node[1]['longitude'] for node in graph.nodes(data=True)) / len(graph.nodes())]
    folium_map = folium.Map(location=map_center, zoom_start=13)

    # Plot area of interest
    folium.PolyLine(corners, color="blue").add_to(folium_map)
    # Add nodes to the map with latitude-longitude positions
    for node, data in graph.nodes(data=True):
        lat, lon = data['latitude'], data['longitude']
        folium.Marker([lat, lon], popup=data['name']).add_to(folium_map)

    # Add edges (shortest path) to the map (extensively expensive in case of fully connected graph)
    # for edge in tqdm(graph.edges(data=True)):
    #     src_node, dest_node, _ = edge
    #     src_lat, src_lon = graph.nodes[src_node]['latitude'], graph.nodes[src_node]['longitude']
    #     dest_lat, dest_lon = graph.nodes[dest_node]['latitude'], graph.nodes[dest_node]['longitude']
    #     directions = gmaps.directions((src_lat, src_lon), (dest_lat, dest_lon), mode="driving")
    #     if directions:
    #         path_coordinates = [(step['start_location']['lat'], step['start_location']['lng']) for step in directions[0]['legs'][0]['steps']]
    #         folium.PolyLine(path_coordinates, color="blue").add_to(folium_map)

    # Display the map in the browser
    folium_map.save('graph_map.html')

def visualise_graph_plt(G):
    # Get the circular layout positions for the nodes
    pos = nx.circular_layout(G)
    # Set node and edge colors, and node size
    node_color = 'blue'

    edge_color = 'gray'
    node_size = 50
    # Create a new figure and axis
    plt.figure(figsize=(10, 8))
    ax = plt.gca()
    # Draw the graph
    nx.draw(G, pos, with_labels=False, node_size=node_size, node_color=node_color, edge_color=edge_color, width=0.05, ax=ax)
    ax.set_title('Islamabad Buss Stops : Fully Connected Graph (Circular Layout)')  # Add your desired title here
    ax.axis('off')  # Turn off the axis for a cleaner look

    plt.savefig('fully_connected_graph.png', format='png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":    
    start_latitude = 33.351247  # Starting latitude
    start_longitude = 72.772021  # Starting longitude
    num_intervals = 30  # Number of intervals in each direction (total 30 x 30 = 900 points)

    # Lat_long points forming a grid that cover area of interest
    origions = _get_origions(start_latitude, start_longitude, num_intervals)
    corners = [origions[0], origions[num_intervals-1], origions[num_intervals*num_intervals-1], origions[num_intervals*num_intervals-num_intervals], origions[0]]
    
    # If bus stops data (.csv) does not exist, crawl it from Google Map
    if not os.path.exists(STOPS_FIlENAME):
        print("Bus Stops data not found! Crawling it from Google Maps...")
        bus_stops = navigate_square_area(start_latitude, start_longitude, num_intervals, API_KEY)

        # Write bus stops to a CSV file
        with open(STOPS_FIlENAME, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=bus_stops[0].keys(), delimiter='|')
            writer.writeheader()
            writer.writerows(bus_stops)

        print(str(len(bus_stops)) + ' Bus stops have been saved to', STOPS_FIlENAME)

    # Construct graph if .graphml file does not exist.
    if not os.path.exists(GRAPH_FILENAME):
        # Create Network Graph nodes out of Bus stops data
        graph = create_network_graph(STOPS_FIlENAME)
        # Save the graph to GraphML file
        nx.write_graphml(graph, "isb_pt_net.graphml")

    graph = nx.read_graphml(GRAPH_FILENAME)

    # Visualise Graph
    visualise_graph_map(graph, corners)
    #visualise_graph_plt(graph)