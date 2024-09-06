import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import folium
import copy

def graph_to_excel(G, output_file):
    # Extract nodes and their latitude and longitude
    nodes = [(node, data['latitude'], data['longitude']) for node, data in G.nodes(data=True)]
    area_df = pd.DataFrame(nodes, columns=['AREA', 'LATITUDE', 'LONGITUDE'])

    # Initialize matrices for Matrix, Distance_Matrix, and Google_Travel_Distance
    areas = area_df['AREA']
    matrix_df = pd.DataFrame(index=areas, columns=areas)
    distance_df = pd.DataFrame(index=areas, columns=areas)
    google_distance_df = pd.DataFrame(index=areas, columns=areas)

    # Populate the matrices with edge attributes
    for u, v, data in G.edges(data=True):
        matrix_df.loc[u, v] = data.get('percent_travelers', None)
        distance_df.loc[u, v] = data.get('haversine_distance', None)
        if data.get('is_valid', True):
            google_distance_df.loc[u, v] = data.get('google_distance', None)
        else:
            google_distance_df.loc[u, v] = 0

    # Create a Pandas Excel writer to handle multiple sheets
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        # Write the Matrix sheet
        matrix_df.to_excel(writer, sheet_name='Matrix')

        # Write the Area_Coordinates sheet
        area_df.to_excel(writer, sheet_name='Area_Coordinates', index=False)

        # Write the Distance_Matrix sheet
        distance_df.to_excel(writer, sheet_name='Distance_Matrix')

        # Write the Google_Travel_Distance sheet
        google_distance_df.to_excel(writer, sheet_name='Google_Travel_Distance')

    print(f"Graph data saved to {output_file}")

def plot_graph(G):
    # Visualize the graph
    plt.figure(figsize=(10, 10))

    # Extract latitude and longitude for each node for layout
    pos = {node: (G.nodes[node]['longitude'], G.nodes[node]['latitude']) for node in G.nodes}

    # Draw the graph
    nx.draw(G, pos, with_labels=True, node_size=500, node_color='skyblue', font_size=8, font_weight='bold')

    # Draw edge labels
    edge_labels = {(u, v): f"{d['percent_travelers']}%" for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)

    plt.title("Network Graph of Areas")
    plt.show()

def plot_graph_with_google_maps_overlay(G, output_html="graph_map.html"):
    # Create a Folium map centered at the average location
    avg_lat = sum(nx.get_node_attributes(G, 'latitude').values()) / len(G)
    avg_lon = sum(nx.get_node_attributes(G, 'longitude').values()) / len(G)
    graph_map = folium.Map(location=[avg_lat, avg_lon], zoom_start=10)

    # Add nodes as circles
    for node, data in G.nodes(data=True):
        folium.Circle(
            location=[data['latitude'], data['longitude']],
            radius=300,  # Adjust radius as needed
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.6,
            popup=(f"Node: {node}<br>"
                   f"Latitude: {data['latitude']}<br>"
                   f"Longitude: {data['longitude']}")
        ).add_to(graph_map)

    # Add edges as lines with popup attributes, considering the 'visible' attribute
    for u, v, data in G.edges(data=True):
        # Check if the edge should be visible
        if data.get('is_valid', True):  # Default to True if 'visible' is not set
            lat_lon_u = [G.nodes[u]['latitude'], G.nodes[u]['longitude']]
            lat_lon_v = [G.nodes[v]['latitude'], G.nodes[v]['longitude']]
            
            folium.PolyLine(
                locations=[lat_lon_u, lat_lon_v],
                color="blue",
                weight=1,
                popup=(f"Edge: {u} -> {v}<br>"
                       f"Travelers: {data.get('percent_travelers', 'N/A')}%<br>"
                       f"Haversine Distance: {data.get('haversine_distance', 'N/A')} km<br>"
                       f"Google Distance: {data.get('google_distance', 'N/A')} km")
            ).add_to(graph_map)

    # Save the map to an HTML file
    graph_map.save(output_html)
    print(f"Graph map saved as {output_html}")

def display_graph_characteristics(G):
    # Filter the graph to include only visible edges
    visible_edges = [(u, v) for u, v, data in G.edges(data=True) if data.get('is_valid', True)]
    G_visible = nx.Graph()
    G_visible.add_edges_from(visible_edges)
    
    # Calculate graph density considering only visible edges
    density = nx.density(G_visible)

    # Print the graph characteristics
    print("Graph Characteristics (Considering 'is_valid' attribute if present):")
    print(f"Total number of nodes: {G.number_of_nodes()}")
    print(f"Total number of edges: {G.number_of_edges()}")
    print(f"Total number of valid edges: {len(visible_edges)}")
    print(f"Graph density (considering visible edges): {density:.4f}")

    # Optionally, you can also calculate and display other characteristics
    # For example: average degree, clustering coefficient, etc.
    avg_degree = sum(dict(G_visible.degree()).values()) / G_visible.number_of_nodes()
    print(f"Average degree (considering visible edges): {avg_degree:.2f}")

def set_edge_validity(G, attribute_name, condition_func):
    """
    Sets an edge visibility attribute based on a condition applied to an edge attribute.

    Parameters:
    - G: The NetworkX graph.
    - attribute_name: The name of the edge attribute to evaluate.
    - condition_func: A function that takes an attribute value and returns True if the edge should be visible.
    """
    # Add a visibility attribute to each edge based on the condition
    for u, v, data in G.edges(data=True):
        # Check if the edge has the attribute
        if attribute_name in data:
            # Apply the condition function to determine visibility
            is_valid = condition_func(data[attribute_name])
        else:
            # If the attribute is missing, set visibility to False
            is_valid = False
        
        # Add or update the visibility attribute
        G[u][v]['is_valid'] = is_valid

def google_distance_condition(value):
    return value <= 11.48

def update_graph_edges(G, attribute_name, value=0.0):
    # Create a deep copy of the graph
    edges_to_remove = []
    for u, v, data in G.edges(data=True):
        if not data.get('is_valid', True):
            # data[attribute_name] = value
            edges_to_remove.append((u, v))
        # Remove the is_valid attribute from the edge
        if 'is_valid' in data:
            del data['is_valid']
    G.remove_edges_from(edges_to_remove)

if __name__ == "__main__":
    # Load the Excel file
    file_path = 'output_matrix_with_coordinates_and_distance_google.xlsx'  # replace with your file path
    matrix_df = pd.read_excel(file_path, sheet_name='Matrix', index_col=0)
    distance_df = pd.read_excel(file_path, sheet_name='Distance_Matrix', index_col=0)
    google_distance_df = pd.read_excel(file_path, sheet_name='Google_Travel_Distance', index_col=0)
    area_df = pd.read_excel(file_path, sheet_name='Area_Coordinates')

    # Create a directed graph
    G = nx.DiGraph()

    # Add nodes with latitude and longitude as attributes
    for _, row in area_df.iterrows():
        G.add_node(row['AREA'], latitude=row['LATITUDE'], longitude=row['LONGITUDE'])

    # Add edges with attributes from the Matrix, Distance_Matrix, and Google_Travel_Distance sheets
    for home_area in matrix_df.index:
        for work_area in matrix_df.columns:
            if not pd.isna(matrix_df.loc[home_area, work_area]):
                G.add_edge(
                    home_area, 
                    work_area, 
                    percent_travelers=matrix_df.loc[home_area, work_area],
                    haversine_distance=distance_df.loc[home_area, work_area],
                    google_distance=google_distance_df.loc[home_area, work_area]
                )

    # set_edge_validity(G, 'google_distance', google_distance_condition)
    display_graph_characteristics(G)
    plot_graph_with_google_maps_overlay(G)
    # graph_to_excel(G, 'matrix.xlsx')
    # update_graph_edges(G, 'google_distance')
    graph_to_excel(G, 'matrix.xlsx')
    # Save the graph to a file (optional)
    nx.write_gexf(G, "od_graph.gexf")
    print('Graph saved to area_network_graph.gexf')
