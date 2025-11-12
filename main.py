import time
from typing import Any

import musicbrainzngs
import networkx

musicbrainzngs.set_useragent("musicgraph", "0.1", "riley@rileyflynn.me")
musicbrainzngs.set_rate_limit()

ROOT_ARTIST_ID = "c39e3739-f8a2-48e4-9485-880c3b721879"
MAX_ARTIST_DISTANCE = 7

graph = networkx.DiGraph()

resp = musicbrainzngs.get_artist_by_id(ROOT_ARTIST_ID, includes=["artist-rels"])

visited_nodes = set()
pending_nodes: set[str] = set()


def get_artist_by_id(
    artist_id: str,
) -> Any:
    tries = 0

    while tries < 10:
        try:
            resp = musicbrainzngs.get_artist_by_id(artist_id, includes=["artist-rels"])
            return resp
        except musicbrainzngs.NetworkError:
            time.sleep(0.5)
            tries += 1


def walk_node(artist_id: str):
    if artist_id in visited_nodes:
        return
    visited_nodes.add(artist_id)

    if artist_id in graph:
        distance = networkx.shortest_path_length(
            graph.to_undirected(), ROOT_ARTIST_ID, artist_id
        )
        if distance > MAX_ARTIST_DISTANCE:
            print(f"Skipping {artist_id} at distance {distance}")
            return

    resp = get_artist_by_id(artist_id)
    artist_name = resp["artist"]["name"]

    if artist_id not in graph:
        graph.add_node(artist_id, label=artist_name)

    rels = resp["artist"].get("artist-relation-list", [])
    for rel in rels:
        target_id = rel["artist"]["id"]
        rel_type = rel["type"]

        edge = (
            (artist_id, target_id)
            if rel["direction"] == "forward"
            else (target_id, artist_id)
        )

        graph.add_node(target_id, label=rel["artist"]["name"])
        graph.add_edge(*edge, label=rel_type)

        if target_id not in visited_nodes:
            pending_nodes.add(target_id)


pending_nodes.add(ROOT_ARTIST_ID)

while pending_nodes:
    print(f"{len(visited_nodes)} visited, {len(pending_nodes)} pending")
    current_node = pending_nodes.pop()
    walk_node(current_node)

networkx.nx_pydot.write_dot(graph, "graph.dot")
