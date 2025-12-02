-- schema.sql
-- Create the contexts table for storing shared knowledge
CREATE TABLE IF NOT EXISTS clients (
    id TEXT PRIMARY KEY,
    label TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS contexts (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    tags TEXT DEFAULT '[]', -- JSON array of tags
    source TEXT NOT NULL,   -- Which LLM/tool created this
    timestamp TEXT NOT NULL,
    metadata TEXT DEFAULT '{}', -- JSON object for additional data
    client_id TEXT NOT NULL DEFAULT 'public'
);

-- Create indexes for faster searching
CREATE INDEX IF NOT EXISTS idx_contexts_timestamp ON contexts(timestamp);
CREATE INDEX IF NOT EXISTS idx_contexts_source ON contexts(source);
CREATE INDEX IF NOT EXISTS idx_contexts_content ON contexts(content);
CREATE INDEX IF NOT EXISTS idx_contexts_client_timestamp ON contexts(client_id, timestamp DESC);

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