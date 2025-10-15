-- schema.sql
-- Create the contexts table for storing shared knowledge
CREATE TABLE IF NOT EXISTS contexts (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    tags TEXT DEFAULT '[]', -- JSON array of tags
    source TEXT NOT NULL,   -- Which LLM/tool created this
    timestamp TEXT NOT NULL,
    metadata TEXT DEFAULT '{}', -- JSON object for additional data
    bucket TEXT NOT NULL DEFAULT 'shared' -- Logical storage bucket (shared or agent-specific)
);

-- Create indexes for faster searching
CREATE INDEX IF NOT EXISTS idx_contexts_timestamp ON contexts(timestamp);
CREATE INDEX IF NOT EXISTS idx_contexts_source ON contexts(source);
CREATE INDEX IF NOT EXISTS idx_contexts_content ON contexts(content);
CREATE INDEX IF NOT EXISTS idx_contexts_bucket ON contexts(bucket);
CREATE INDEX IF NOT EXISTS idx_contexts_bucket_source ON contexts(bucket, source);

-- Example data (optional - remove if you don't want sample data)
INSERT OR IGNORE INTO contexts (id, content, tags, source, timestamp, metadata, bucket) VALUES
(
    'sample-1',
    'This is a sample context entry showing how LLMs can share knowledge through this hub.',
    '["example", "demo", "setup"]',
    'claude-setup',
    datetime('now'),
    '{"importance": "low", "category": "system"}',
    'shared'
);