import networkx
import psycopg

graph = networkx.nx_pydot.read_dot("graph.dot").to_undirected()

FROM = "c39e3739-f8a2-48e4-9485-880c3b721879"
TO = "596ffa74-3d08-44ef-b113-765d43d12738"

conn = psycopg.connect(
    "user=musicbrainz password=musicbrainz dbname=musicbrainz_db host=localhost"
)


def resolve_artist(guid: str) -> int:
    return str(
        conn.execute("SELECT id FROM artist WHERE gid = %s", (guid,)).fetchone()[0]
    )


path = networkx.shortest_path(graph, resolve_artist(FROM), resolve_artist(TO))
print(" -> ".join([graph.nodes[node]["label"] for node in path]))
