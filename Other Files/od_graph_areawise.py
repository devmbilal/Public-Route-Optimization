import networkx as nx
import random

def display_edge_info(G, edge):
    u, v = edge
    # Display node attributes for both nodes
    print(f"Node {u} attributes:")
    for attr, value in G.nodes[u].items():
        print(f"  {attr}: {value}")
    
    print(f"\nNode {v} attributes:")
    for attr, value in G.nodes[v].items():
        print(f"  {attr}: {value}")
    
    # Display edge attributes
    print(f"\nEdge attributes between {u} and {v}:")
    for attr, value in G[u][v].items():
        print(f"  {attr}: {value}")
    print("-" * 50)

if __name__ == "__main__":
    gexf_file = "area_network_graph.gexf"
    # Read the graph from the GEXF file
    G = nx.read_gexf(gexf_file)

    # Randomly select two edges from the graph
    edge_list = random.sample(list(G.edges()), 2)

    # Display information for each selected edge
    for edge in edge_list:
        display_edge_info(G, edge)