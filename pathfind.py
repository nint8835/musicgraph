import pickle
from collections import defaultdict

import networkx
import psycopg

conn = psycopg.connect(
    "user=musicbrainz password=musicbrainz dbname=musicbrainz_db host=localhost",
    prepare_threshold=0,
    prepared_max=None,
)


def resolve_artist(guid: str) -> int:
    return conn.execute(
        "SELECT id FROM artist WHERE gid = %s",
        (guid,),
    ).fetchone()[0]


with open("graph.pkl", "rb") as f:
    graph = pickle.load(f)

ROOT_ARTIST_ID = "aba64937-3334-4c65-90a1-4e6b9d4d7ada"
TARGET_ARTIST_ID = "84825fb6-c98c-4b43-a184-c7f70619f355"

# Weigh certain artists higher to attempt to avoid them, for example certain giant collaborations
artist_link_factors: dict[int, float] = defaultdict(
    lambda: 1.0,
    {
        # 1,000 UK Artists
        resolve_artist("ef96a7c5-cfe5-43e0-a65f-0262e7f44630"): 100
    },
)

# Weight certain types of links higher to attempt to avoid them
link_type_weight_factors: dict[str, float] = defaultdict(
    lambda: 1.0,
    {
        # The data has A LOT of credits, so weigh them higher to get more interesting paths
        "credited on release": 100,
        # Prefer actual musical relationships over personal ones
        "parent": 50,
        "sibling": 50,
        "married": 50,
        "involved with": 50,
        # Some other less interesting relationships
        "tribute": 20,
        "named after artist": 20,
    },
)

path = networkx.shortest_path(
    graph,
    resolve_artist(ROOT_ARTIST_ID),
    resolve_artist(TARGET_ARTIST_ID),
    weight=lambda u, v, d: artist_link_factors[u]
    * artist_link_factors[v]
    * link_type_weight_factors[d["label"]],
)

for i in range(len(path) - 2 + 1):
    from_node, to_node = path[i], path[i + 1]
    edge_data = graph.get_edge_data(from_node, to_node)
    rel_type = edge_data["label"]
    from_name = graph.nodes[from_node]["label"]
    to_name = graph.nodes[to_node]["label"]
    print(f"{from_name} <--[{rel_type}]--> {to_name}")
