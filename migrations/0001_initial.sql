-- Initial schema for knowledge hub
CREATE TABLE IF NOT EXISTS contexts (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    tags TEXT DEFAULT '[]',
    source TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    metadata TEXT DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_contexts_timestamp ON contexts(timestamp);
CREATE INDEX IF NOT EXISTS idx_contexts_source ON contexts(source);
CREATE INDEX IF NOT EXISTS idx_contexts_content ON contexts(content);
