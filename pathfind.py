import networkx
import psycopg

graph = networkx.nx_pydot.read_dot("graph.dot").to_undirected()

FROM = "0356daee-ec48-4495-bc3e-460b8a5eacad"
TO = "0c502791-4ee9-4c5f-9696-0602b721ff3b"

conn = psycopg.connect(
    "user=musicbrainz password=musicbrainz dbname=musicbrainz_db host=localhost"
)


def resolve_artist(guid: str) -> int:
    return str(
        conn.execute("SELECT id FROM artist WHERE gid = %s", (guid,)).fetchone()[0]
    )


path = networkx.shortest_path(graph, resolve_artist(FROM), resolve_artist(TO))


for i in range(len(path) - 2 + 1):
    from_node, to_node = path[i], path[i + 1]
    edge_data = graph.get_edge_data(from_node, to_node)
    rel_type = edge_data["label"]
    from_name = graph.nodes[from_node]["label"]
    to_name = graph.nodes[to_node]["label"]
    print(f"{from_name} --[{rel_type}]--> {to_name}")
