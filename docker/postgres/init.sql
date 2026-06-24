-- ApplyTrack — PostgreSQL initialization.
-- Runs once when the container data volume is first created.
-- Subsequent container restarts skip this file (data volume already exists).

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
