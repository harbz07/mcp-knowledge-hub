-- Add client scoping to contexts and create client/event tables

-- Ensure a table exists for client metadata
CREATE TABLE IF NOT EXISTS clients (
    id TEXT PRIMARY KEY,
    label TEXT,
    created_at TEXT NOT NULL
);

-- Add client scoping to contexts
ALTER TABLE contexts ADD COLUMN client_id TEXT NOT NULL DEFAULT 'public';
CREATE INDEX IF NOT EXISTS idx_contexts_client_timestamp ON contexts(client_id, timestamp DESC);

-- Events hub to capture structured event payloads per client
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    happened_at TEXT NOT NULL,
    place TEXT,
    who TEXT NOT NULL,
    why TEXT,
    effects TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_client_time ON events(client_id, happened_at DESC);
