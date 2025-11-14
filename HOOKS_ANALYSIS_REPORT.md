# Claude Code Hooks Analysis Report
**Project:** Claudia - Claude Code Companion
**Date:** 2025-01-14
**Purpose:** Comprehensive analysis of hook opportunities for maximizing data capture for vectorization

---

## Executive Summary

This report analyzes Claude Code's hook system to identify opportunities for enhanced data capture. Our current implementation captures **basic lifecycle and tool usage data** across 5 of 9 available hook events. Significant opportunities exist to capture **rich conversation data, assistant responses, and contextual information** critical for future vectorization and semantic search capabilities.

### Key Findings

- ✅ **Currently Capturing:** Session lifecycle, tool execution, settings snapshots
- ❌ **Missing Critical Data:** Assistant messages, user prompt content, stop events, notification context
- 🎯 **Vectorization Priority:** User prompts, assistant responses, tool results, session context
- 📊 **Data Completeness:** ~40% of available data currently captured

### Recommendations Priority

1. **HIGH**: Capture user prompts and assistant responses (`UserPromptSubmit`, `Stop`)
2. **HIGH**: Capture tool results in `PostToolUse` (currently only capturing input)
3. **MEDIUM**: Add `PreCompact` and `SubagentStop` for context management insights
4. **LOW**: Add `Notification` hooks for permission patterns and idle analysis

---

## Current Implementation Analysis

### What We're Currently Capturing

#### 1. Session Lifecycle (`SessionStart` / `SessionEnd`)
**File:** `hooks/capture_session.py`
**Hook Events:** `SessionStart`, `SessionEnd`

**Data Captured:**
```json
{
  "session_id": "unique-id",
  "event_type": "SessionStart|SessionEnd",
  "project_path": "/path/to/project",
  "project_name": "project-name",
  "transcript_path": "/path/to/transcript.jsonl",
  "permission_mode": "default|plan|acceptEdits|bypassPermissions",
  "runtime_config": {
    "permission_mode": "default",
    "env": {
      "CLAUDE_CODE_REMOTE": "true|undefined",
      "CLAUDE_PROJECT_DIR": "/path"
    }
  },
  "timestamp": "2025-01-14T..."
}
```

**Strengths:**
- ✅ Captures session boundaries for correlation
- ✅ Tracks project context
- ✅ Records permission mode
- ✅ Includes transcript path for later processing

**Gaps:**
- ❌ `SessionEnd` doesn't capture exit reason (available in input)
- ❌ `SessionStart` doesn't capture matcher type (startup/resume/clear/compact)
- ❌ Not capturing custom session context or project metadata

#### 2. Tool Execution (`PreToolUse` / `PostToolUse`)
**File:** `hooks/monitor_tool_use.py`
**Hook Events:** `PreToolUse`, `PostToolUse`
**Matcher:** `*` (all tools)

**Data Captured:**
```json
{
  "session_id": "unique-id",
  "event_type": "PreToolUse|PostToolUse",
  "tool_name": "Bash|Write|Edit|Read|...",
  "parameters": { /* tool-specific input */ },
  "working_directory": "/path",
  "timestamp": "2025-01-14T..."
}
```

**Strengths:**
- ✅ Captures all tool executions (matcher: `*`)
- ✅ Records tool parameters for analysis
- ✅ Tracks working directory context

**Critical Gaps:**
- ❌ **NOT capturing tool results** from `PostToolUse`
  - `tool_response` field available but not captured
  - Missing stdout, stderr, exit codes for Bash
  - Missing file contents from Read
  - Missing success/failure status
- ❌ No distinction between PreToolUse and PostToolUse in backend
- ❌ Not capturing tool execution duration

#### 3. Settings Snapshots (`SessionStart`, `UserPromptSubmit`)
**File:** `hooks/settings_watcher.py`
**Hook Events:** `SessionStart`, `UserPromptSubmit`

**Data Captured:**
```json
{
  "session_id": "unique-id",
  "timestamp": "2025-01-14T...",
  "settings": {
    "user": { /* ~/.claude/settings.json */ },
    "project": { /* .claude/settings.json */ },
    "local": { /* .claude/settings.local.json */ },
    "managed": { /* enterprise settings */ }
  },
  "paths": {
    "user": "/path/to/user/settings.json",
    /* ... */
  }
}
```

**Strengths:**
- ✅ Captures full settings hierarchy
- ✅ Cross-platform (macOS, Linux, Windows)
- ✅ Includes managed/enterprise settings

**Questions:**
- ⚠️ Why on `UserPromptSubmit`? Settings don't change per prompt
- ⚠️ Should this be on `SessionStart` only?
- ⚠️ Consider capturing only on settings file changes instead

---

## Available Hooks We're NOT Using

### 1. `Stop` - **CRITICAL FOR VECTORIZATION**
**Priority:** 🔴 **HIGH**

**Purpose:** Fires when Claude finishes responding (main agent)

**Data Available:**
```json
{
  "session_id": "...",
  "transcript_path": "...",
  "stop_hook_active": false,  // Prevents infinite loops
  "permission_mode": "..."
}
```

**Why This Matters:**
- ✅ Marks completion of Claude's response
- ✅ Access to full transcript at response boundary
- ✅ Can read transcript to extract assistant's last message
- ✅ **Critical for vectorization**: Assistant responses are the primary content to embed

**Vectorization Value:**
- **HIGH**: Assistant messages contain reasoning, code explanations, architecture decisions
- Can be paired with user prompt to create Q&A pairs for semantic search
- Enables "find similar responses to this question" queries

**Implementation:**
```python
# Read transcript to get last assistant message
with open(transcript_path) as f:
    lines = f.readlines()
    # Find last assistant message block
    # Extract text, code, reasoning
    # Send to backend for embedding
```

### 2. `SubagentStop` - **MEDIUM PRIORITY**
**Priority:** 🟡 **MEDIUM**

**Purpose:** Fires when a Task tool (subagent) finishes

**Why This Matters:**
- ✅ Captures sub-task completion
- ✅ Useful for understanding agent delegation patterns
- ✅ Can track which tasks are delegated vs. handled directly

**Vectorization Value:**
- **MEDIUM**: Subagent responses often contain specialized analysis
- Example: Code review agents, architecture planning agents
- Less frequent than main agent responses but high value

### 3. `PreCompact` - **MEDIUM PRIORITY**
**Priority:** 🟡 **MEDIUM**

**Purpose:** Fires before context window compaction

**Data Available:**
```json
{
  "trigger": "manual|auto",
  "custom_instructions": "user's compact instructions or empty",
  "session_id": "...",
  "transcript_path": "..."
}
```

**Why This Matters:**
- ✅ Indicates context window pressure
- ✅ Can analyze what triggers auto-compaction
- ✅ Track custom compact instructions patterns

**Vectorization Value:**
- **LOW-MEDIUM**: Useful for understanding conversation length patterns
- Can inform embedding strategy (chunk size, overlap)
- Not directly valuable content to embed

### 4. `Notification` - **LOW PRIORITY**
**Priority:** 🟢 **LOW**

**Purpose:** Fires on various notification types

**Notification Types:**
- `permission_prompt` - Permission requests
- `idle_prompt` - Claude idle 60+ seconds
- `auth_success` - Authentication success
- `elicitation_dialog` - MCP tool input requests

**Why This Matters:**
- ✅ Can analyze permission patterns (which tools need approval)
- ✅ Track idle time and conversation pacing
- ✅ Monitor authentication events

**Vectorization Value:**
- **LOW**: Not content-related, more for behavioral analytics
- Useful for UX improvements, not semantic search

---

## Data Gaps Critical for Vectorization

### 1. User Prompt Content - **MISSING**
**Current State:** `UserPromptSubmit` hook exists but doesn't capture prompt content

**Available Field:** `input_data['prompt']` contains the full user prompt

**Why Critical:**
- User prompts are the **primary input** for semantic search
- "Find conversations where I asked about error handling"
- "What did I ask about database migrations?"

**Action Required:**
```python
# In UserPromptSubmit hook
prompt_text = input_data.get('prompt', '')
# Send to backend: {session_id, prompt_text, timestamp}
# Backend stores for embedding
```

**Backend Changes Needed:**
- New table: `user_prompts` (session_id, prompt_text, timestamp, embedding)
- Endpoint: `POST /api/prompts/capture`

### 2. Assistant Responses - **MISSING**
**Current State:** No hook captures assistant output

**Available via:** `Stop` hook + transcript reading

**Why Critical:**
- Assistant responses are the **primary output** to embed
- Contains reasoning, code explanations, architectural decisions
- Enables "find similar responses" semantic search

**Implementation Strategy:**
```python
# In Stop hook
transcript_path = input_data['transcript_path']
# Read transcript JSONL
# Find last assistant message block
# Extract text content
# Send to backend for embedding
```

**Backend Changes Needed:**
- New table: `assistant_messages` (session_id, message_text, timestamp, embedding)
- Endpoint: `POST /api/messages/capture`

### 3. Tool Results - **PARTIALLY MISSING**
**Current State:** Capturing tool input but NOT tool output

**Available Field:** `tool_response` in `PostToolUse` hook

**Why Important:**
- Tool results provide context for embeddings
- "Find where Claude read database.py" → need file contents
- "Find bash commands that failed" → need exit codes

**Action Required:**
```python
# In PostToolUse hook
tool_response = input_data.get('tool_response', {})
# Send alongside tool_input
```

**Examples by Tool:**
- **Bash**: `stdout`, `stderr`, `exitCode`
- **Read**: `content` (file contents)
- **Write/Edit**: `success`, `filePath`
- **Grep**: `matches` or `files`

---

## Data Structure Recommendations for Vectorization

### Conversation Chunks for Embedding

Based on research into RAG best practices, we should structure data as:

```python
{
  "chunk_id": "uuid",
  "session_id": "session-uuid",
  "chunk_type": "prompt|response|tool_execution|context",
  "timestamp": "2025-01-14T...",
  "content": "text to embed",
  "metadata": {
    "project_name": "claudia",
    "project_path": "/path/to/project",
    "tool_name": "Write",  // if tool_execution
    "file_path": "/path/to/file",  // if relevant
    "permission_mode": "default",
    "conversation_turn": 5  // position in conversation
  },
  "embedding": [0.123, 0.456, ...],  // pgvector
  "parent_chunk_id": "uuid",  // for multi-part responses
  "related_chunks": ["uuid1", "uuid2"]  // tool calls related to this prompt
}
```

### Embedding Strategies

1. **User Prompts**: Embed each prompt individually
2. **Assistant Responses**: Split long responses into chunks (1000-2000 tokens)
3. **Tool Executions**: Embed tool input + output together for context
4. **Session Summaries**: Periodic summaries of conversation state

### Metadata for Filtering

Capture rich metadata to enable filtered search:
- Project name/path (search within project)
- File paths (search file-related conversations)
- Tool types (search tool-specific usage)
- Permission mode (search by workflow type)
- Timestamp (temporal search)
- Conversation turn number (find early vs. late conversation)

---

## Hook Implementation Priorities

### Phase 1: Critical Data Capture (Week 1)

#### 1.1 Add `Stop` Hook for Assistant Messages
**Priority:** 🔴 **CRITICAL**

**Implementation:**
```python
# hooks/capture_assistant_messages.py
def main():
    input_data = json.loads(sys.stdin.read())

    # Read transcript to get last assistant message
    transcript_path = input_data['transcript_path']
    assistant_message = extract_last_assistant_message(transcript_path)

    # Send to backend
    send_to_claudia('messages/capture', {
        'session_id': input_data['session_id'],
        'message_text': assistant_message,
        'timestamp': datetime.utcnow().isoformat()
    })
```

**Backend:**
- Table: `assistant_messages`
- Endpoint: `POST /api/messages/capture`
- Queue for embedding (async)

#### 1.2 Capture User Prompts in `UserPromptSubmit`
**Priority:** 🔴 **CRITICAL**

**Update:** `hooks/settings_watcher.py` OR create new `hooks/capture_prompts.py`

**Implementation:**
```python
def main():
    input_data = json.loads(sys.stdin.read())

    if input_data['hook_event_name'] == 'UserPromptSubmit':
        prompt_text = input_data.get('prompt', '')

        send_to_claudia('prompts/capture', {
            'session_id': input_data['session_id'],
            'prompt_text': prompt_text,
            'timestamp': datetime.utcnow().isoformat()
        })
```

#### 1.3 Capture Tool Results in `PostToolUse`
**Priority:** 🔴 **HIGH**

**Update:** `hooks/monitor_tool_use.py`

**Changes:**
```python
# Add tool_response field
tool_response = input_data.get('tool_response', {})

monitoring_data = {
    # ... existing fields
    'parameters': tool_input,
    'result': tool_response,  # NEW
    'timestamp': datetime.now(timezone.utc).isoformat()
}
```

**Backend:**
- Update `tool_executions` table to include `result` JSONB column
- Update `POST /api/monitoring/tool-use` to accept result field

### Phase 2: Enhanced Context (Week 2)

#### 2.1 Add `SubagentStop` Hook
**Priority:** 🟡 **MEDIUM**

Similar to `Stop` but for subagent completions.

#### 2.2 Add `PreCompact` Hook
**Priority:** 🟡 **MEDIUM**

Track compaction events for context window insights.

#### 2.3 Enhanced Session Metadata
**Priority:** 🟡 **MEDIUM**

Capture:
- SessionStart matcher (startup/resume/clear/compact)
- SessionEnd reason (clear/logout/prompt_input_exit/other)
- Project git info (branch, commit hash)

### Phase 3: Analytics & Optimization (Week 3)

#### 3.1 Add `Notification` Hooks
**Priority:** 🟢 **LOW**

For permission pattern analysis.

#### 3.2 Tool Execution Duration
**Priority:** 🟡 **MEDIUM**

Calculate duration between PreToolUse and PostToolUse.

#### 3.3 Conversation Turn Tracking
**Priority:** 🟡 **MEDIUM**

Track turn number (user → assistant → user sequence).

---

## Database Schema Updates Needed

### New Tables

#### `user_prompts`
```sql
CREATE TABLE user_prompts (
  id SERIAL PRIMARY KEY,
  session_id INTEGER REFERENCES sessions(id),
  prompt_text TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL,
  embedding vector(1536),  -- pgvector for OpenAI embeddings
  metadata JSONB
);

CREATE INDEX idx_user_prompts_session ON user_prompts(session_id);
CREATE INDEX idx_user_prompts_embedding ON user_prompts USING ivfflat (embedding vector_cosine_ops);
```

#### `assistant_messages`
```sql
CREATE TABLE assistant_messages (
  id SERIAL PRIMARY KEY,
  session_id INTEGER REFERENCES sessions(id),
  message_text TEXT NOT NULL,
  message_type VARCHAR(50),  -- 'response', 'reasoning', 'code_explanation'
  created_at TIMESTAMP WITH TIME ZONE NOT NULL,
  embedding vector(1536),
  metadata JSONB,
  conversation_turn INTEGER
);

CREATE INDEX idx_assistant_messages_session ON assistant_messages(session_id);
CREATE INDEX idx_assistant_messages_embedding ON assistant_messages USING ivfflat (embedding vector_cosine_ops);
```

### Table Updates

#### `tool_executions` - Add result column
```sql
ALTER TABLE tool_executions
ADD COLUMN result JSONB;
```

#### `sessions` - Add metadata columns
```sql
ALTER TABLE sessions
ADD COLUMN start_matcher VARCHAR(50),  -- startup, resume, clear, compact
ADD COLUMN end_reason VARCHAR(50),     -- clear, logout, prompt_input_exit, other
ADD COLUMN git_branch VARCHAR(255),
ADD COLUMN git_commit VARCHAR(255);
```

---

## Transcript Processing Strategy

### JSONL Format
Claude Code transcripts are JSONL (JSON Lines) with entries like:

```json
{"type":"user_message","timestamp":"...","content":"User's prompt"}
{"type":"tool_use","timestamp":"...","name":"Read","input":{...}}
{"type":"tool_result","timestamp":"...","output":"..."}
{"type":"assistant_message","timestamp":"...","content":"Claude's response"}
```

### Parsing Approach

```python
def extract_last_assistant_message(transcript_path):
    """Extract the most recent assistant message from transcript"""
    with open(transcript_path, 'r') as f:
        lines = f.readlines()

    # Iterate backwards to find last assistant message
    for line in reversed(lines):
        try:
            entry = json.loads(line)
            if entry.get('type') == 'assistant_message':
                return entry.get('content', '')
        except json.JSONDecodeError:
            continue

    return ''
```

### Chunking Strategy for Long Responses

For responses > 2000 tokens:
1. Split on paragraph boundaries
2. Maintain 200-token overlap between chunks
3. Store chunk metadata (part 1 of 3, etc.)
4. Link chunks with `parent_chunk_id`

---

## Embedding Pipeline Architecture

### 1. Data Collection (Hooks)
- Hooks capture raw data
- Send to backend via HTTP POST
- Backend queues for processing

### 2. Processing Queue
- Use Celery or RQ for async processing
- Process embeddings in background
- Batch requests to OpenRouter (via OpenRouter API)

### 3. Embedding Generation
```python
# Using OpenRouter API
import openai

client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

response = client.embeddings.create(
    input="text to embed",
    model="openai/text-embedding-3-small"
)

embedding = response.data[0].embedding  # 1536 dimensions
```

### 4. Vector Storage
- Store in `pgvector` columns
- Create IVFFLAT or HNSW indexes
- Enable similarity search

### 5. Query Interface
```python
# Find similar prompts
SELECT
  prompt_text,
  1 - (embedding <=> query_embedding) as similarity
FROM user_prompts
ORDER BY embedding <=> query_embedding
LIMIT 10;
```

---

## Testing & Validation Plan

### Hook Testing
1. **Unit Tests**: Test each hook script with sample input
2. **Integration Tests**: Test hook → backend flow
3. **Load Tests**: Ensure hooks don't slow down Claude Code

### Data Quality
1. **Completeness**: Verify all sessions have prompts and responses
2. **Accuracy**: Spot-check extracted content against transcripts
3. **Timeliness**: Measure latency from event to embedding

### Embedding Quality
1. **Relevance**: Manual testing of semantic search results
2. **Coverage**: Ensure all conversation types represented
3. **Performance**: Query latency < 100ms for k-NN search

---

## Cost Estimation

### Embedding Costs (OpenRouter)
- Model: `openai/text-embedding-3-small`
- Cost: ~$0.02 per 1M tokens
- Average session: ~10k tokens (5 prompts, 5 responses)
- Cost per session: ~$0.0002

**Monthly (1000 sessions):** ~$0.20

### Storage Costs (PostgreSQL)
- Embedding size: 1536 dimensions × 4 bytes = 6KB per embedding
- Average session: 20 embeddings (10 prompts + 10 responses)
- Storage per session: ~120KB
- 1000 sessions: ~120MB

**Very affordable at current scale**

---

## Implementation Roadmap

### Week 1: Critical Data Capture ✅ COMPLETE
- [x] Add `Stop` hook for assistant messages (`hooks/capture_assistant_messages.py`)
- [x] Update `UserPromptSubmit` to capture prompts (`hooks/capture_prompts.py`)
- [x] Update `PostToolUse` to capture tool results (`hooks/monitor_tool_use.py`)
- [x] Add database tables (`user_prompts`, `assistant_messages`) - `database/phase1_conversation_capture.sql`
- [x] Create backend endpoints (`/api/prompts/capture`, `/api/messages/capture`)
- [x] Update `tool_executions` schema (added `result` JSONB column)
- [x] Committed: `d16a227 Implement Phase 1: Critical conversation data capture`

### Week 2: Embedding Pipeline
- [ ] Set up OpenRouter integration
- [ ] Create embedding queue (Celery/RQ)
- [ ] Implement batch embedding generation
- [ ] Add pgvector indexes
- [ ] Create similarity search endpoints

### Week 3: UI & Search
- [ ] Build semantic search UI
- [ ] Add conversation replay view
- [ ] Implement filters (project, date, tool type)
- [ ] Add export functionality

### Week 4: Testing & Refinement
- [ ] Load testing hooks
- [ ] Embedding quality validation
- [ ] Search relevance tuning
- [ ] Documentation

---

## Risks & Mitigations

### Risk 1: Hook Latency
**Concern:** Hooks might slow down Claude Code

**Mitigation:**
- Keep hooks under 100ms
- Use async HTTP requests (timeout 5s)
- Fail gracefully (exit 0 even on errors)

### Risk 2: Data Volume
**Concern:** Large transcripts, many sessions

**Mitigation:**
- Implement chunking for long responses
- Set retention policies (e.g., 90 days)
- Compress old data

### Risk 3: Embedding Costs
**Concern:** Costs scale with usage

**Mitigation:**
- Start with small batch (our own usage)
- Monitor costs via OpenRouter dashboard
- Implement rate limiting if needed

### Risk 4: PII in Conversations
**Concern:** Sensitive data in prompts/responses

**Mitigation:**
- Document that Claudia captures all conversation data
- Provide opt-out mechanism (`CLAUDIA_MONITORING=false`)
- Consider PII detection before embedding
- Respect Claude Code's permission modes

---

## Success Metrics

### Data Completeness
- ✅ 100% of sessions have start/end events
- ✅ 100% of user prompts captured
- ✅ 100% of assistant responses captured
- ✅ 95%+ of tool executions have results

### Search Quality
- ✅ 90%+ relevance in top-5 results (manual evaluation)
- ✅ < 200ms query latency
- ✅ Support for multi-faceted search (project + tool + date)

### System Performance
- ✅ Hook execution < 100ms p95
- ✅ No user-reported slowdowns
- ✅ Zero data loss

---

## Appendices

### Appendix A: Complete Hook Event Reference

| Event | Trigger | Blocking | Data Available | Current Status |
|-------|---------|----------|----------------|----------------|
| PreToolUse | Before tool execution | ✅ Yes | tool_name, tool_input | ✅ Implemented |
| PostToolUse | After tool execution | ❌ No | tool_name, tool_input, tool_response | ⚠️ Partial (missing result) |
| SessionStart | Session start/resume | ❌ No | session_id, cwd, matcher | ✅ Implemented |
| SessionEnd | Session end | ❌ No | session_id, reason | ⚠️ Partial (missing reason) |
| UserPromptSubmit | Prompt submission | ✅ Yes | prompt | ⚠️ Partial (not capturing prompt) |
| Stop | Assistant finishes | ✅ Yes | transcript_path | ❌ Not implemented |
| SubagentStop | Subagent finishes | ✅ Yes | transcript_path | ❌ Not implemented |
| PreCompact | Before compaction | ❌ No | trigger, custom_instructions | ❌ Not implemented |
| Notification | Various notifications | ❌ No | message, notification_type | ❌ Not implemented |

### Appendix B: Sample Hook Configurations

**Complete hook configuration for Claudia:**

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "python3 /path/to/monitor_tool_use.py",
        "timeout": 5
      }]
    }],
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "python3 /path/to/monitor_tool_use.py",
        "timeout": 5
      }]
    }],
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "python3 /path/to/capture_session.py",
        "timeout": 5
      }]
    }],
    "SessionEnd": [{
      "hooks": [{
        "type": "command",
        "command": "python3 /path/to/capture_session.py",
        "timeout": 5
      }]
    }],
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "python3 /path/to/capture_prompts.py",
        "timeout": 5
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "python3 /path/to/capture_assistant_messages.py",
        "timeout": 5
      }]
    }]
  }
}
```

### Appendix C: Tool Response Schemas

**Bash Tool Response:**
```json
{
  "stdout": "command output",
  "stderr": "error output",
  "exitCode": 0
}
```

**Read Tool Response:**
```json
{
  "content": "file contents",
  "filePath": "/absolute/path/to/file"
}
```

**Write/Edit Tool Response:**
```json
{
  "success": true,
  "filePath": "/absolute/path/to/file"
}
```

---

## Conclusion

This analysis reveals significant opportunities to enhance Claudia's data capture capabilities. By implementing the recommended Phase 1 changes (Stop hook, UserPromptSubmit content, PostToolUse results), we can capture **100% of conversation content** necessary for effective vectorization and semantic search.

The current implementation provides a solid foundation for session tracking and tool monitoring. The next critical step is capturing the conversational content (prompts and responses) that will power Claudia's future semantic search and context augmentation features.

**Estimated implementation time:** 3-4 weeks
**Estimated cost:** < $1/month for 1000 sessions
**Expected value:** Complete conversation search, context augmentation, pattern analysis

**Next Step:** Review recommendations and prioritize Phase 1 implementation.
