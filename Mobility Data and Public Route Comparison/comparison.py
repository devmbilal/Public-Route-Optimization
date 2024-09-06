import networkx as nx
import folium

def plot_graph_with_google_maps_overlay(G, output_html="graph_map.html"):
    # Calculate average latitude and longitude for centering the map
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

    # Add edges as lines
    for u, v, data in G.edges(data=True):
        lat_lon_u = [G.nodes[u]['latitude'], G.nodes[u]['longitude']]
        lat_lon_v = [G.nodes[v]['latitude'], G.nodes[v]['longitude']]
        
        folium.PolyLine(
            locations=[lat_lon_u, lat_lon_v],
            color="blue",
            weight=2,
            opacity=0.6,
            popup=(f"Edge: {u} -> {v}<br>"
                   f"Travelers: {data.get('percent_travelers', 'N/A')}%<br>"
                   f"Haversine Distance: {data.get('haversine_distance', 'N/A')} km<br>"
                   f"Google Distance: {data.get('google_distance', 'N/A')} km")
        ).add_to(graph_map)

    # Save the map to an HTML file
    graph_map.save(output_html)
    print(f"Graph map saved as {output_html}")

# Read the GEXF file and plot the graph
input_gexf = 'output_graph_with_edges.gexf'  # Replace with your GEXF file path
graph = nx.read_gexf(input_gexf)
plot_graph_with_google_maps_overlay(graph, output_html="graph_map.html")

