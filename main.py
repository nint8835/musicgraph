import json
import sys

import networkx
import psycopg

ROOT_ARTIST_GUID = "c39e3739-f8a2-48e4-9485-880c3b721879"
MAX_ARTIST_DISTANCE = int(sys.argv[1])

conn = psycopg.connect(
    "user=musicbrainz password=musicbrainz dbname=musicbrainz_db host=localhost"
)

graph = networkx.DiGraph()

visited_nodes: set[int] = set()
pending_nodes: set[int] = set()

nodes: set[str] = set()
node_names: dict[str, str] = {}
links: set[tuple[str, str]] = set()
link_types: dict[tuple[str, str], str] = {}


def resolve_artist(guid: str) -> int:
    return conn.execute("SELECT id FROM artist WHERE gid = %s", (guid,)).fetchone()[0]


root_artist_id = resolve_artist(ROOT_ARTIST_GUID)


def walk_node(artist_id: int) -> None:
    if artist_id in visited_nodes:
        return
    visited_nodes.add(artist_id)

    if artist_id in graph:
        distance = networkx.shortest_path_length(
            graph.to_undirected(), root_artist_id, artist_id
        )
        if distance > MAX_ARTIST_DISTANCE:
            print(f"Skipping {artist_id} at distance {distance}")
            return
    else:
        name = conn.execute(
            "SELECT name FROM artist WHERE id = %s", (artist_id,)
        ).fetchone()[0]
        graph.add_node(artist_id, label=name)
        nodes.add(artist_id)
        node_names[artist_id] = name

    rels = conn.execute(
        """
        SELECT
            l_artist_artist.entity0,
            l_artist_artist.entity1,
            link_type.name,
            a0."name",
            a1."name"
        FROM
            l_artist_artist
            JOIN link ON link.id = l_artist_artist."link"
            JOIN link_type ON link_type.id = link.link_type
            JOIN artist a0 ON a0.id = l_artist_artist.entity0
            JOIN artist a1 ON a1.id = l_artist_artist.entity1
        WHERE
            l_artist_artist.entity0 = %s OR l_artist_artist.entity1 = %s
        """,
        (artist_id, artist_id),
    ).fetchall()

    for entity0, entity1, rel_type, artist_0, artist_1 in rels:
        if not graph.has_node(entity0):
            graph.add_node(entity0, label=artist_0)
            nodes.add(entity0)
            node_names[entity0] = artist_0
        if not graph.has_node(entity1):
            graph.add_node(entity1, label=artist_1)
            nodes.add(entity1)
            node_names[entity1] = artist_1
        if not graph.has_edge(entity0, entity1):
            graph.add_edge(entity0, entity1, label=rel_type)
            links.add((entity0, entity1))
            link_types[(entity0, entity1)] = rel_type

        other_artist_id = entity1 if entity0 == artist_id else entity0
        if other_artist_id not in visited_nodes:
            pending_nodes.add(other_artist_id)


pending_nodes.add(root_artist_id)

while pending_nodes:
    print(f"{len(visited_nodes)} visited, {len(pending_nodes)} pending")
    current_node = pending_nodes.pop()
    walk_node(current_node)

networkx.nx_pydot.write_dot(graph, "graph.dot")

with open(
    f"visualization/graphs/{MAX_ARTIST_DISTANCE}.json", "w", encoding="utf-8"
) as f:
    json.dump(
        {
            "nodes": [{"id": n, "label": node_names[n]} for n in nodes],
            "links": [
                {"source": s, "target": t, "type": link_types[(s, t)]} for s, t in links
            ],
        },
        f,
        indent=2,
        sort_keys=True,
    )
