import pickle
from functools import lru_cache

import networkx
import psycopg
import pydot

conn = psycopg.connect(
    "user=musicbrainz password=musicbrainz dbname=musicbrainz_db host=localhost",
    prepare_threshold=0,
    prepared_max=None,
)

graph = networkx.Graph()


@lru_cache(maxsize=None)
def sanitize_artist_name(name: str) -> str:
    return pydot.make_quoted(name.replace("\\", "\\\\"))


BATCH_SIZE = 250000

print("Fetching artists...")
offset = 0
total_artists = 0
while True:
    artists = conn.execute(
        f"SELECT id, gid, name FROM artist LIMIT {BATCH_SIZE} OFFSET {offset}"
    ).fetchall()

    if not artists:
        break

    for artist_id, artist_gid, artist_name in artists:
        graph.add_node(
            artist_id,
            gid=artist_gid,
            label=sanitize_artist_name(artist_name),
        )

    total_artists += len(artists)
    offset += BATCH_SIZE
    print(f"Processed {total_artists} artists...")

print(f"Finished processing {total_artists} artists")

print("\nFetching artist connections...")
offset = 0
total_connections = 0
while True:
    connections = conn.execute(
        f"SELECT entity0, entity1, relationship FROM artist_graph_edges LIMIT {BATCH_SIZE} OFFSET {offset}"
    ).fetchall()

    if not connections:
        break

    for entity0, entity1, relationship in connections:
        graph.add_edge(
            entity0,
            entity1,
            label=relationship,
        )

    total_connections += len(connections)
    offset += BATCH_SIZE
    print(f"Processed {total_connections} connections...")

print(f"Finished processing {total_connections} connections")


with open("graph.pkl", "wb") as f:
    pickle.dump(graph, f)
