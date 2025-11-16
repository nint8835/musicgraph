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


artists = conn.execute("SELECT id, gid, name FROM artist").fetchall()
for artist_id, artist_gid, artist_name in artists:
    graph.add_node(
        artist_id,
        gid=artist_gid,
        label=sanitize_artist_name(artist_name),
    )

connections = conn.execute(
    "SELECT entity0, entity1, relationship FROM artist_graph_edges"
).fetchall()
for entity0, entity1, relationship in connections:
    graph.add_edge(
        entity0,
        entity1,
        label=relationship,
    )


with open("graph.pkl", "wb") as f:
    pickle.dump(graph, f)
