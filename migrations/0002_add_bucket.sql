-- Add bucket support for agent-specific and shared storage
ALTER TABLE contexts ADD COLUMN bucket TEXT NOT NULL DEFAULT 'shared';

CREATE INDEX IF NOT EXISTS idx_contexts_bucket ON contexts(bucket);
CREATE INDEX IF NOT EXISTS idx_contexts_bucket_source ON contexts(bucket, source);
