import networkx as nx
import pandas as pd
import os
from geopy.distance import geodesic
from tqdm import tqdm  

# Load GEXF file
def load_gexf(file_path):
    print(f"Loading GEXF file from: {file_path}")
    graph = nx.read_gexf(file_path)
    nodes = {node: {'latitude': data['latitude'], 'longitude': data['longitude']} for node, data in graph.nodes(data=True)}
    print(f"Total nodes loaded: {len(nodes)}")
    return graph, nodes

# Load public routes from CSV files
def load_public_routes(directory_path):
    print(f"Loading public routes CSV files from directory: {directory_path}")
    public_routes = {}
    for file in tqdm(os.listdir(directory_path), desc="Loading CSV files"):
        if file.endswith('.csv'):
            route_name = os.path.splitext(file)[0]
            df = pd.read_csv(os.path.join(directory_path, file))
            public_routes[route_name] = df[['Stop Name', 'latitude', 'longitude']].values.tolist()
    print(f"Total routes loaded: {len(public_routes)}")
    return public_routes

# Calculate distance between two points using latitude and longitude
def is_within_distance(coord1, coord2, distance_threshold=1000):
    distance = geodesic(coord1, coord2).meters
    print(f"    Calculated Distance from {coord1} to {coord2}: {distance:.2f} meters")
    return distance <= distance_threshold

def associate_routes_to_nodes(nodes, public_routes):
    print("Associating routes to nodes...")
    node_routes = {node: [] for node in nodes}  # Initialize empty route lists for each node
    
    # Iterate through each node
    for node in tqdm(nodes, desc="Processing Nodes"):
        coord = nodes[node]
        node_coord = (coord['latitude'], coord['longitude'])
        
        print(f"Processing Node: {node} with coordinates: {node_coord}")
        
        # Check each route to see if any stops are within the distance
        for route_name, stops in public_routes.items():
            print(f"  Checking Route: {route_name}")
            
            for stop in stops:
                stop_name, stop_lat, stop_lon = stop
                stop_coord = (stop_lat, stop_lon)  # (latitude, longitude)
                
                print(f"    Stop Name: {stop_name}, Stop Coordinates: {stop_coord}")
                
                # Check if the stop is within the distance threshold
                if is_within_distance(node_coord, stop_coord):
                    print(f"    Route {route_name} is within 500m of Node {node}")
                    
                    # Check if route is already added to node's routes
                    if route_name not in node_routes[node]:
                        node_routes[node].append(route_name)
                        print(f"    Added Route {route_name} to Node {node}")
                    break  # Break to avoid adding the same route multiple times for the same node
        
        # Print node routes for debugging after processing all routes
        print(f"Node {node} has the following associated routes: {node_routes[node]}")
    
    # Print all nodes and their associated routes
    print("\nAll nodes with their associated routes:")
    for node, routes in node_routes.items():
        print(f"Node {node}: {routes}")
    
    return node_routes
# Create edges between nodes with common routes
def create_edges_with_common_routes(node_routes):
    print("Creating edges between nodes with common routes...")
    edges = set()
    nodes = list(node_routes.keys())
    
    for i in tqdm(range(len(nodes)), desc="Processing Nodes for Edges"):
        for j in range(i + 1, len(nodes)):
            if set(node_routes[nodes[i]]) & set(node_routes[nodes[j]]):  # Check for common routes
                edges.add((nodes[i], nodes[j]))
    
    print(f"Total edges created: {len(edges)}")
    return edges

# Append edges to the existing GEXF file
def append_edges_to_gexf(graph, edges, output_path):
    print(f"Appending edges to GEXF file: {output_path}")
    graph.add_edges_from(edges)
    nx.write_gexf(graph, output_path)
    print(f"Edges appended and graph saved to: {output_path}")

def main():
    # Load data
    gexf_file_path = r'F:\Route Optimization\Mobility Data and Public Route Comparison\nodes.gexf'
    public_routes_directory = r'F:\Route Optimization\Mobility Data and Public Route Comparison\Public Routes CSV'
    output_path = 'output_graph_with_edges.gexf'

    # Load nodes from GEXF
    graph, nodes = load_gexf(gexf_file_path)

    # Load public routes from CSV files
    public_routes = load_public_routes(public_routes_directory)

    # Associate routes to nodes
    node_routes = associate_routes_to_nodes(nodes, public_routes)

    # Create edges between nodes with common routes
    edges = create_edges_with_common_routes(node_routes)

    # Append edges to the GEXF file
    append_edges_to_gexf(graph, edges, output_path)

if __name__ == "__main__":
    main()
