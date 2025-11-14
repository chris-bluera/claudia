-- Phase 1: Conversation Capture Migration
-- Adds tables and columns for capturing user prompts, assistant messages, and tool results
-- For vectorization and semantic search

-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create user_prompts table for capturing user input
CREATE TABLE IF NOT EXISTS claudia.user_prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES claudia.claude_sessions(id) ON DELETE CASCADE,
    prompt_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    embedding vector(1536),  -- OpenAI text-embedding-3-small dimensions
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create assistant_messages table for capturing Claude's responses
CREATE TABLE IF NOT EXISTS claudia.assistant_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES claudia.claude_sessions(id) ON DELETE CASCADE,
    message_text TEXT NOT NULL,
    conversation_turn INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    embedding vector(1536),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Add result column to tool_executions for capturing tool output
ALTER TABLE claudia.tool_executions
ADD COLUMN IF NOT EXISTS result JSONB;

-- Add session metadata columns for enhanced context
ALTER TABLE claudia.claude_sessions
ADD COLUMN IF NOT EXISTS start_matcher VARCHAR(50),  -- startup, resume, clear, compact
ADD COLUMN IF NOT EXISTS end_reason VARCHAR(50);     -- clear, logout, prompt_input_exit, other

-- Create indexes for performance

-- Session-based queries (most common)
CREATE INDEX IF NOT EXISTS idx_user_prompts_session ON claudia.user_prompts(session_id);
CREATE INDEX IF NOT EXISTS idx_assistant_messages_session ON claudia.assistant_messages(session_id);

-- Time-based queries
CREATE INDEX IF NOT EXISTS idx_user_prompts_created ON claudia.user_prompts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_assistant_messages_created ON claudia.assistant_messages(created_at DESC);

-- Conversation turn tracking
CREATE INDEX IF NOT EXISTS idx_assistant_messages_turn ON claudia.assistant_messages(conversation_turn);

-- Vector similarity search indexes (IVFFLAT for now, can upgrade to HNSW later)
-- Note: These will be created after data is populated for better index quality
-- CREATE INDEX idx_user_prompts_embedding ON claudia.user_prompts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
-- CREATE INDEX idx_assistant_messages_embedding ON claudia.assistant_messages USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- JSONB indexes for metadata queries
CREATE INDEX IF NOT EXISTS idx_user_prompts_metadata ON claudia.user_prompts USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_assistant_messages_metadata ON claudia.assistant_messages USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_tool_executions_result ON claudia.tool_executions USING GIN (result);

-- Add comments for documentation
COMMENT ON TABLE claudia.user_prompts IS 'User prompts captured from UserPromptSubmit hook for semantic search';
COMMENT ON TABLE claudia.assistant_messages IS 'Assistant responses captured from Stop hook for semantic search';
COMMENT ON COLUMN claudia.tool_executions.result IS 'Tool execution results from PostToolUse hook (stdout, stderr, files, etc.)';
COMMENT ON COLUMN claudia.claude_sessions.start_matcher IS 'Session start type: startup, resume, clear, or compact';
COMMENT ON COLUMN claudia.claude_sessions.end_reason IS 'Session end reason: clear, logout, prompt_input_exit, or other';
