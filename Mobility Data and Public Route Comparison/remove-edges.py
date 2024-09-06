import networkx as nx

# Read the GEXF file
graph = nx.read_gexf('area_network_graph.gexf')

# Remove all edges from the graph
graph.clear_edges()

# Write the modified graph (with only nodes) back to a new GEXF file
nx.write_gexf(graph, 'remove-edges.gexf')

print("Edges removed. Only nodes with their attributes are kept.")
