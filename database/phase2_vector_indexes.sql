-- Phase 2: Vector Indexes for Performance
-- Creates vector similarity search indexes on embeddings columns

-- Note: IVFFLAT indexes should be created AFTER data is populated for better index quality
-- The number of lists should be approximately sqrt(row_count)
-- Starting with 100 lists, can be adjusted based on data volume

-- Vector index for user_prompts
-- Uses cosine distance operator for semantic similarity
CREATE INDEX IF NOT EXISTS idx_user_prompts_embedding
ON claudia.user_prompts
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Vector index for assistant_messages
CREATE INDEX IF NOT EXISTS idx_assistant_messages_embedding
ON claudia.assistant_messages
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Add comments
COMMENT ON INDEX claudia.idx_user_prompts_embedding IS 'IVFFLAT index for semantic similarity search on user prompts';
COMMENT ON INDEX claudia.idx_assistant_messages_embedding IS 'IVFFLAT index for semantic similarity search on assistant messages';

-- Performance note: For better performance with larger datasets, consider:
-- 1. Increasing lists parameter: lists = CEIL(SQRT(row_count))
-- 2. Upgrading to HNSW indexes (available in pgvector 0.5.0+):
--    CREATE INDEX USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
