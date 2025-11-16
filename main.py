import networkx
import psycopg
import pydot

ROOT_ARTIST_GUID = "c39e3739-f8a2-48e4-9485-880c3b721879"
# Target artist for pathfinding to be logged separately
PATHFINDING_TARGET_ARTIST_GUID = "0356daee-ec48-4495-bc3e-460b8a5eacad"
MAX_ARTIST_DISTANCE = 15

conn = psycopg.connect(
    "user=musicbrainz password=musicbrainz dbname=musicbrainz_db host=localhost"
)

graph = networkx.Graph()

visited_nodes: set[int] = set()
pending_nodes: set[int] = set()
distance: dict[int, int] = {}


def resolve_artist(guid: str) -> int:
    return conn.execute("SELECT id FROM artist WHERE gid = %s", (guid,)).fetchone()[0]


def sanitize_artist_name(name: str) -> str:
    return pydot.make_quoted(name.replace("\\", "\\\\"))


root_artist_id = resolve_artist(ROOT_ARTIST_GUID)


def walk_node(artist_id: int) -> None:
    if artist_id in visited_nodes:
        return
    visited_nodes.add(artist_id)

    if artist_id in distance:
        artist_distance = distance[artist_id]
        # if artist_distance > MAX_ARTIST_DISTANCE:
        #     return
    else:
        name, guid = conn.execute(
            "SELECT name, gid FROM artist WHERE id = %s", (artist_id,)
        ).fetchone()
        graph.add_node(artist_id, label=sanitize_artist_name(name), guid=guid)

    rels = conn.execute(
        """
        SELECT
            l_artist_artist.entity0,
            l_artist_artist.entity1,
            link_type.name,
            a0."name",
            a0.gid,
            a1."name",
            a1.gid
        FROM
            l_artist_artist
            JOIN link ON link.id = l_artist_artist."link"
            JOIN link_type ON link_type.id = link.link_type
            JOIN artist a0 ON a0.id = l_artist_artist.entity0
            JOIN artist a1 ON a1.id = l_artist_artist.entity1
        WHERE
            (l_artist_artist.entity0 = %s OR l_artist_artist.entity1 = %s)
            AND link_type.name NOT IN ('parent', 'sibling', 'married', 'involved with', 'teacher', 'named after artist')
        """,
        (artist_id, artist_id),
    ).fetchall()

    for (
        entity0,
        entity1,
        rel_type,
        artist_0,
        artist_0_guid,
        artist_1,
        artist_1_guid,
    ) in rels:
        if not graph.has_node(entity0):
            graph.add_node(
                entity0, label=sanitize_artist_name(artist_0), guid=artist_0_guid
            )
        if not graph.has_node(entity1):
            graph.add_node(
                entity1, label=sanitize_artist_name(artist_1), guid=artist_1_guid
            )
        if not graph.has_edge(entity0, entity1):
            graph.add_edge(entity0, entity1, label=rel_type)

        other_artist_id = entity1 if entity0 == artist_id else entity0
        if other_artist_id not in visited_nodes:
            pending_nodes.add(other_artist_id)
            distance[other_artist_id] = distance[artist_id] + 1


pending_nodes.add(root_artist_id)
distance[root_artist_id] = 0

while pending_nodes:
    if len(visited_nodes) % 1000 == 0:
        print(f"{len(visited_nodes)} visited, {len(pending_nodes)} pending")
    current_node = pending_nodes.pop()
    walk_node(current_node)

networkx.nx_pydot.write_dot(graph, "graph.dot")


path = networkx.shortest_path(
    graph,
    resolve_artist(ROOT_ARTIST_GUID),
    resolve_artist(PATHFINDING_TARGET_ARTIST_GUID),
)

for i in range(len(path) - 2 + 1):
    from_node, to_node = path[i], path[i + 1]
    edge_data = graph.get_edge_data(from_node, to_node)
    rel_type = edge_data["label"]
    from_name = graph.nodes[from_node]["label"]
    to_name = graph.nodes[to_node]["label"]
    print(f"{from_name} <--[{rel_type}]--> {to_name}")
