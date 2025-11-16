# musicgraph

Graph relationships between artists based on the data in the MusicBrainz database

## Requirements:

- MusicBrainz DB dump created using their Docker example, and tweaked to be exposed to the local machine
- The following incides manually created:
  ```sql
  CREATE INDEX idx_recording_id_include_artist_credit
  ON recording(id)
  INCLUDE (artist_credit);
  ```
