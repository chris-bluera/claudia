-- Claudia Database Schema
-- PostgreSQL with pgvector extension

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create schema
CREATE SCHEMA IF NOT EXISTS claudia;
SET search_path TO claudia, public;

-- Sessions table: Track Claude Code sessions
CREATE TABLE claude_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    project_path TEXT,
    project_name VARCHAR(255),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sessions_active ON claude_sessions(is_active);
CREATE INDEX idx_sessions_project ON claude_sessions(project_path);
CREATE INDEX idx_sessions_started ON claude_sessions(started_at DESC);

-- Hook configurations table
CREATE TABLE hook_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    event_type VARCHAR(100) NOT NULL,
    matcher VARCHAR(255),
    hook_type VARCHAR(50) DEFAULT 'command',  -- 'command' or 'prompt'
    script_template TEXT,
    config JSONB DEFAULT '{}',
    enabled BOOLEAN DEFAULT true,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_hooks_event ON hook_configs(event_type);
CREATE INDEX idx_hooks_enabled ON hook_configs(enabled);

-- Hook executions log
CREATE TABLE hook_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hook_id UUID REFERENCES hook_configs(id) ON DELETE SET NULL,
    session_id UUID REFERENCES claude_sessions(id) ON DELETE CASCADE,
    event_type VARCHAR(100),
    matcher VARCHAR(255),
    input_data JSONB,
    output_data JSONB,
    exit_code INTEGER,
    duration_ms INTEGER,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_hook_exec_session ON hook_executions(session_id);
CREATE INDEX idx_hook_exec_time ON hook_executions(executed_at DESC);

-- Settings snapshots table
CREATE TABLE settings_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES claude_sessions(id) ON DELETE CASCADE,
    settings_json JSONB NOT NULL,
    hierarchy_level VARCHAR(50), -- 'user', 'project', 'local', 'managed'
    file_path TEXT,
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_settings_session ON settings_snapshots(session_id);
CREATE INDEX idx_settings_level ON settings_snapshots(hierarchy_level);

-- Tool executions table
CREATE TABLE tool_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES claude_sessions(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    parameters JSONB,
    result JSONB,
    error TEXT,
    executed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER
);

CREATE INDEX idx_tools_session ON tool_executions(session_id);
CREATE INDEX idx_tools_name ON tool_executions(tool_name);
CREATE INDEX idx_tools_time ON tool_executions(executed_at DESC);

-- Conversation events table (parsed from transcripts)
CREATE TABLE conversation_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES claude_sessions(id) ON DELETE CASCADE,
    event_type VARCHAR(50), -- 'user_prompt', 'assistant_response', 'tool_call', etc
    content TEXT,
    metadata JSONB,
    sequence_number INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conv_session ON conversation_events(session_id, sequence_number);
CREATE INDEX idx_conv_type ON conversation_events(event_type);
CREATE INDEX idx_conv_time ON conversation_events(timestamp DESC);

-- Claude focus/context tracking
CREATE TABLE claude_focus (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES claude_sessions(id) ON DELETE CASCADE,
    focus_type VARCHAR(50), -- 'task', 'context', 'goal'
    content TEXT,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_focus_session ON claude_focus(session_id, is_active);
CREATE INDEX idx_focus_priority ON claude_focus(priority DESC);

-- Embeddings table (for pgvector - future semantic search)
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(50), -- 'conversation', 'code', 'documentation', etc
    source_id UUID, -- Reference to source record
    content TEXT,
    embedding vector(1536), -- OpenAI ada-002 dimensions
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_embeddings_source ON embeddings(source_type, source_id);
CREATE INDEX idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops);

-- Patterns table (for recognized development patterns)
CREATE TABLE patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    pattern_type VARCHAR(50), -- 'workflow', 'error_resolution', 'refactoring', etc
    frequency INTEGER DEFAULT 1,
    example_sessions JSONB DEFAULT '[]',
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_patterns_type ON patterns(pattern_type);
CREATE INDEX idx_patterns_tags ON patterns USING GIN (tags);

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update trigger to relevant tables
CREATE TRIGGER update_claude_sessions_updated_at
    BEFORE UPDATE ON claude_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_hook_configs_updated_at
    BEFORE UPDATE ON hook_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_patterns_updated_at
    BEFORE UPDATE ON patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Initial data or settings can go here
INSERT INTO hook_configs (name, description, event_type, matcher, script_template, enabled)
VALUES
    ('Monitor Tool Use', 'Track all tool executions', 'PreToolUse', '*',
     'echo "Tool: $1" >> claudia-monitor.log', true),
    ('Session Tracker', 'Track session lifecycle', 'SessionStart', '*',
     'curl -X POST http://localhost:8000/api/session-start', true);

-- Grant permissions (adjust as needed)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA claudia TO claudia;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA claudia TO claudia;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA claudia TO claudia;