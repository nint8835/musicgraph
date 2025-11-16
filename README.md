# musicgraph

Graph relationships between artists based on the data in the MusicBrainz database

## Requirements:

- MusicBrainz DB dump created using their Docker example, and tweaked to be exposed to the local machine
- The following incides / views manually created:

  ```sql
  CREATE INDEX idx_recording_id_include_artist_credit
  ON recording(id)
  INCLUDE (artist_credit);

  CREATE MATERIALIZED VIEW artist_graph_edges AS
    SELECT
        l_artist_artist.entity0,
        l_artist_artist.entity1,
        link_type.name AS relationship
    FROM
        l_artist_artist
        JOIN link ON link.id = l_artist_artist."link"
        JOIN link_type ON link_type.id = link.link_type
    UNION
    SELECT DISTINCT
        l_artist_recording.entity0,
        artist.id AS entity1,
        'credited on release' AS relationship
    FROM
        l_artist_recording
        JOIN recording ON recording.id = l_artist_recording.entity1
        JOIN artist_credit_name ON artist_credit_name.artist_credit = recording.artist_credit
        JOIN artist ON artist.id = artist_credit_name.artist
    WHERE
        l_artist_recording.entity0 <> artist.id
    UNION
    SELECT
        acn1.artist AS entity0,
        acn2.artist AS entity1,
        'released a song with' AS relationship
    FROM
        artist_credit_name acn1
        JOIN artist_credit_name acn2 ON acn1.artist_credit = acn2.artist_credit
    WHERE
        acn1.artist < acn2.artist;

  CREATE INDEX idx_artist_graph_edges_e0 ON artist_graph_edges (entity0);
  CREATE INDEX idx_artist_graph_edges_e1 ON artist_graph_edges (entity1);
  ```
