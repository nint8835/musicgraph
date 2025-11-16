import pickle

import networkx

with open("graph.pkl", "rb") as f:
    graph = pickle.load(f)

ROOT_ARTIST_ID = 1116838
TARGET_ARTIST_ID = 153

path = networkx.shortest_path(
    graph,
    ROOT_ARTIST_ID,
    TARGET_ARTIST_ID,
)

for i in range(len(path) - 2 + 1):
    from_node, to_node = path[i], path[i + 1]
    edge_data = graph.get_edge_data(from_node, to_node)
    rel_type = edge_data["label"]
    from_name = graph.nodes[from_node]["label"]
    to_name = graph.nodes[to_node]["label"]
    print(f"{from_name} <--[{rel_type}]--> {to_name}")
