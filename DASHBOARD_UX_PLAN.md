# Dashboard UX Implementation Plan

**Project:** Claudia - Claude Code Companion
**Date:** 2025-01-14
**Purpose:** Detailed implementation plan for session-centric dashboard with conversation views

---

## Overview

Implement session-specific detail views showing conversation history, tool executions, and metadata when a session is selected. This transforms the dashboard from a global-only view to a session-centric interface that properly reflects the database hierarchy.

**Current State:**
- Dashboard shows only global statistics and activity
- No way to view session-specific data (prompts, messages, tools)
- Wasted whitespace (max-width: 1400px constraint)
- New data not displayed (source, reason, embeddings, claudia_metadata)

**Target State:**
- Session selection via horizontal tabs
- Session-specific conversation view, tool execution list, and metadata panel
- Full-width layout utilizing available screen space
- All database-captured data visible in UI

---

## Data Hierarchy

Understanding what data is global vs. session-specific:

### Global Data
- Overall statistics (total sessions, tools executed, unique projects)
- System health status
- Global settings (not session-specific)
- Cross-session activity feed (when no session selected)

### Session-Specific Data
- **Conversation:** User prompts + assistant messages (chronological)
- **Tool Executions:** Parameters, results, errors, duration
- **Session Metadata:** source, reason, duration, is_active, transcript_path
- **Runtime Config:** Permission mode, environment overrides
- **Settings Snapshots:** Settings hierarchy at session start
- **Claudia Metadata:** first_seen_at, internal tracking

---

## Database Schema (Already Exists)

All required data is already captured and stored:

### Tables Available

**claude_sessions:**
- Basic fields: `id`, `session_id`, `project_path`, `project_name`
- Timestamps: `started_at`, `ended_at`, `is_active`
- Lifecycle: `source` (startup|resume|clear|compact), `reason` (exit|logout|etc)
- JSONB: `session_metadata`, `claudia_metadata`
- Relationships: tool_executions, user_prompts, assistant_messages, settings_snapshots

**user_prompts:**
- Fields: `id`, `session_id`, `prompt_text`, `created_at`
- Vector: `embedding` (1536 dimensions)
- Metadata: `metadata` JSONB
- Indexed: session_id, created_at, embedding (IVFFLAT)

**assistant_messages:**
- Fields: `id`, `session_id`, `message_text`, `conversation_turn`, `created_at`
- Vector: `embedding` (1536 dimensions)
- Metadata: `metadata` JSONB
- Indexed: session_id, created_at, conversation_turn, embedding (IVFFLAT)

**tool_executions:**
- Fields: `id`, `session_id`, `tool_name`, `parameters`, `result`, `error`, `executed_at`, `duration_ms`
- JSONB indexes on parameters and result

**settings_snapshots:**
- Fields: `id`, `session_id`, `settings_json`, `hierarchy_level`, `file_path`, `captured_at`
- Hierarchy levels: 'user', 'project', 'local', 'managed'

---

## Backend Implementation

### Missing API Endpoints

Current state: `GET /api/sessions/{session_id}` only returns session metadata, NOT related data (prompts, messages, tools).

**Required New Endpoints:**

#### 1. Get Session Prompts
```
GET /api/sessions/{session_id}/prompts
```
**Response:**
```typescript
{
  prompts: UserPrompt[]
}

interface UserPrompt {
  id: string
  session_id: string
  prompt_text: string
  created_at: string
  embedding: number[] | null
  metadata: Record<string, unknown>
}
```

#### 2. Get Session Messages
```
GET /api/sessions/{session_id}/messages
```
**Response:**
```typescript
{
  messages: AssistantMessage[]
}

interface AssistantMessage {
  id: string
  session_id: string
  message_text: string
  conversation_turn: number
  created_at: string
  embedding: number[] | null
  metadata: Record<string, unknown>
}
```

#### 3. Get Session Tools
```
GET /api/sessions/{session_id}/tools?tool_name=<optional>&has_error=<optional>
```
**Query Params:**
- `tool_name` (optional): Filter by specific tool
- `has_error` (optional): Filter by error status

**Response:**
```typescript
{
  tools: ToolExecution[]
}

interface ToolExecution {
  id: string
  session_id: string
  tool_name: string
  parameters: Record<string, unknown> | null
  result: Record<string, unknown> | null
  error: string | null
  executed_at: string | null
  duration_ms: number | null
}
```

#### 4. Get Session Conversation
```
GET /api/sessions/{session_id}/conversation
```
**Response:**
```typescript
{
  conversation: ConversationEntry[]
}

interface ConversationEntry {
  type: 'prompt' | 'message'
  id: string
  text: string
  timestamp: string
  turn?: number  // Only for messages
  has_embedding: boolean
}
```

### Service Layer Methods

Add to `backend/app/services/session_tracker.py`:

```python
async def get_session_prompts(
    self,
    db: AsyncSession,
    session_id: str
) -> List[UserPromptModel]:
    """Get all user prompts for a session, ordered chronologically"""
    result = await db.execute(
        select(UserPromptModel)
        .where(UserPromptModel.session_id == session_id)
        .order_by(UserPromptModel.created_at)
    )
    return list(result.scalars().all())

async def get_session_messages(
    self,
    db: AsyncSession,
    session_id: str
) -> List[AssistantMessageModel]:
    """Get all assistant messages for a session, ordered by turn"""
    result = await db.execute(
        select(AssistantMessageModel)
        .where(AssistantMessageModel.session_id == session_id)
        .order_by(AssistantMessageModel.conversation_turn)
    )
    return list(result.scalars().all())

async def get_session_tools(
    self,
    db: AsyncSession,
    session_id: str,
    tool_name: Optional[str] = None,
    has_error: Optional[bool] = None
) -> List[ToolExecutionModel]:
    """Get tool executions with optional filtering"""
    query = select(ToolExecutionModel).where(
        ToolExecutionModel.session_id == session_id
    )

    if tool_name:
        query = query.where(ToolExecutionModel.tool_name == tool_name)

    if has_error is not None:
        if has_error:
            query = query.where(ToolExecutionModel.error.isnot(None))
        else:
            query = query.where(ToolExecutionModel.error.is_(None))

    query = query.order_by(ToolExecutionModel.executed_at)
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_session_conversation(
    self,
    db: AsyncSession,
    session_id: str
) -> List[Dict[str, Any]]:
    """Get merged conversation timeline (prompts + messages)"""
    prompts = await self.get_session_prompts(db, session_id)
    messages = await self.get_session_messages(db, session_id)

    # Merge and sort by timestamp
    conversation = []

    for prompt in prompts:
        conversation.append({
            'type': 'prompt',
            'id': str(prompt.id),
            'text': prompt.prompt_text,
            'timestamp': prompt.created_at.isoformat(),
            'has_embedding': prompt.embedding is not None
        })

    for message in messages:
        conversation.append({
            'type': 'message',
            'id': str(message.id),
            'text': message.message_text,
            'timestamp': message.created_at.isoformat(),
            'turn': message.conversation_turn,
            'has_embedding': message.embedding is not None
        })

    # Sort chronologically
    conversation.sort(key=lambda x: x['timestamp'])
    return conversation
```

---

## Frontend Implementation

### TypeScript Types

Add to `frontend/src/types/index.ts`:

```typescript
export interface UserPrompt {
  id: string
  session_id: string
  prompt_text: string
  created_at: string
  embedding: number[] | null
  metadata: Record<string, unknown>
}

export interface AssistantMessage {
  id: string
  session_id: string
  message_text: string
  conversation_turn: number
  created_at: string
  embedding: number[] | null
  metadata: Record<string, unknown>
}

export interface ToolExecution {
  id: string
  session_id: string
  tool_name: string
  parameters: Record<string, unknown> | null
  result: Record<string, unknown> | null
  error: string | null
  executed_at: string | null
  duration_ms: number | null
}

export interface ConversationEntry {
  type: 'prompt' | 'message'
  id: string
  text: string
  timestamp: string
  turn?: number
  has_embedding: boolean
}
```

### API Client Methods

Add to `frontend/src/services/api.ts`:

```typescript
async getSessionPrompts(sessionId: string): Promise<UserPrompt[]> {
  const response = await this.get(`/sessions/${sessionId}/prompts`)
  return response.prompts
}

async getSessionMessages(sessionId: string): Promise<AssistantMessage[]> {
  const response = await this.get(`/sessions/${sessionId}/messages`)
  return response.messages
}

async getSessionTools(
  sessionId: string,
  filters?: { tool_name?: string; has_error?: boolean }
): Promise<ToolExecution[]> {
  const params = new URLSearchParams()
  if (filters?.tool_name) params.append('tool_name', filters.tool_name)
  if (filters?.has_error !== undefined) params.append('has_error', String(filters.has_error))

  const response = await this.get(`/sessions/${sessionId}/tools?${params}`)
  return response.tools
}

async getSessionConversation(sessionId: string): Promise<ConversationEntry[]> {
  const response = await this.get(`/sessions/${sessionId}/conversation`)
  return response.conversation
}
```

### Store Updates

Add to `frontend/src/stores/monitoring.ts`:

```typescript
// State
const sessionPrompts = ref<UserPrompt[]>([])
const sessionMessages = ref<AssistantMessage[]>([])
const sessionTools = ref<ToolExecution[]>([])
const sessionConversation = ref<ConversationEntry[]>([])
const loadingDetails = ref(false)

// Actions
async function fetchSessionDetails(sessionId: string) {
  loadingDetails.value = true
  try {
    const [prompts, messages, tools, conversation] = await Promise.all([
      apiClient.getSessionPrompts(sessionId),
      apiClient.getSessionMessages(sessionId),
      apiClient.getSessionTools(sessionId),
      apiClient.getSessionConversation(sessionId)
    ])

    sessionPrompts.value = prompts
    sessionMessages.value = messages
    sessionTools.value = tools
    sessionConversation.value = conversation
  } catch (err) {
    console.error('Error fetching session details:', err)
    error.value = 'Failed to load session details'
  } finally {
    loadingDetails.value = false
  }
}

// Watch for session selection changes
watch(selectedSessionId, async (newSessionId) => {
  if (newSessionId) {
    await fetchSessionDetails(newSessionId)
  } else {
    // Clear session details when no selection
    sessionPrompts.value = []
    sessionMessages.value = []
    sessionTools.value = []
    sessionConversation.value = []
  }
})
```

### Component: ConversationView.vue

**Purpose:** Display chronological conversation (prompts + messages)

**Features:**
- Chronological timeline of user prompts and assistant responses
- Conversation turn numbers for messages
- Embedding status indicator (embedded vs pending)
- Timestamps with relative formatting
- Empty state for sessions without conversation data
- Design tokens for all styling

**Template Structure:**
```vue
<template>
  <div class="panel">
    <div class="panel-header">
      <h2>Conversation</h2>
      <span class="count-badge">{{ conversation.length }} entries</span>
    </div>

    <div v-if="conversation.length === 0" class="empty-state">
      <p>No conversation data for this session</p>
      <p class="hint">Prompts and responses will appear here</p>
    </div>

    <div v-else class="conversation-timeline">
      <div
        v-for="entry in conversation"
        :key="entry.id"
        :class="['entry', `entry-${entry.type}`]"
      >
        <div class="entry-icon">{{ getIcon(entry.type) }}</div>
        <div class="entry-content">
          <div class="entry-header">
            <span class="entry-label">{{ getLabel(entry) }}</span>
            <span v-if="entry.has_embedding" class="embedding-badge">
              Embedded
            </span>
          </div>
          <div class="entry-text">{{ entry.text }}</div>
          <div class="entry-meta">{{ formatTimestamp(entry.timestamp) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
```

### Component: ToolExecutionList.vue

**Purpose:** Display detailed tool execution log

**Features:**
- List view with expandable rows for parameters/results
- Error highlighting with visual treatment
- Duration display (ms)
- Filter by tool type (optional enhancement)
- Truncate large results, expand on click
- Design tokens for all styling

**Template Structure:**
```vue
<template>
  <div class="panel">
    <div class="panel-header">
      <h2>Tool Executions</h2>
      <span class="count-badge">{{ tools.length }}</span>
    </div>

    <div v-if="tools.length === 0" class="empty-state">
      <p>No tool executions for this session</p>
    </div>

    <div v-else class="tools-list">
      <div
        v-for="tool in tools"
        :key="tool.id"
        :class="['tool-item', { 'has-error': tool.error }]"
        @click="toggleExpanded(tool.id)"
      >
        <div class="tool-header">
          <span class="tool-name">{{ tool.tool_name }}</span>
          <span v-if="tool.error" class="error-badge">Error</span>
          <span v-if="tool.duration_ms" class="duration">
            {{ tool.duration_ms }}ms
          </span>
        </div>

        <div v-if="isExpanded(tool.id)" class="tool-details">
          <div v-if="tool.parameters" class="detail-section">
            <h4>Parameters</h4>
            <pre>{{ formatJSON(tool.parameters) }}</pre>
          </div>
          <div v-if="tool.result" class="detail-section">
            <h4>Result</h4>
            <pre>{{ formatJSON(tool.result) }}</pre>
          </div>
          <div v-if="tool.error" class="detail-section error">
            <h4>Error</h4>
            <pre>{{ tool.error }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
```

### Component: SessionDetailPanel.vue

**Purpose:** Display session metadata

**Features:**
- Source, reason (if ended), duration, is_active status
- Transcript path with link (if available)
- Runtime config overrides display
- Claudia metadata (first_seen_at)
- Design tokens for all styling

**Template Structure:**
```vue
<template>
  <div class="panel">
    <div class="panel-header">
      <h2>Session Details</h2>
    </div>

    <div class="details-grid">
      <div class="detail-item">
        <span class="detail-label">Status</span>
        <span :class="['detail-value', session.is_active ? 'active' : 'inactive']">
          {{ session.is_active ? 'Active' : 'Ended' }}
        </span>
      </div>

      <div class="detail-item">
        <span class="detail-label">Source</span>
        <span class="detail-value">
          <span :class="['source-badge', `source-${session.source}`]">
            {{ session.source }}
          </span>
        </span>
      </div>

      <div v-if="!session.is_active && session.reason" class="detail-item">
        <span class="detail-label">End Reason</span>
        <span class="detail-value">{{ session.reason }}</span>
      </div>

      <div class="detail-item">
        <span class="detail-label">Duration</span>
        <span class="detail-value">{{ formatDuration(session.duration_seconds) }}</span>
      </div>

      <div v-if="session.transcript_path" class="detail-item full-width">
        <span class="detail-label">Transcript</span>
        <code class="detail-value monospace">{{ session.transcript_path }}</code>
      </div>

      <div v-if="session.claudia_metadata?.first_seen_at" class="detail-item">
        <span class="detail-label">First Seen</span>
        <span class="detail-value">{{ formatTimestamp(session.claudia_metadata.first_seen_at) }}</span>
      </div>
    </div>
  </div>
</template>
```

### Dashboard Layout Update

Update `frontend/src/views/Dashboard.vue`:

```vue
<template>
  <div class="dashboard">
    <header class="header">
      <!-- Existing header -->
    </header>

    <!-- Stats grid (always visible) -->
    <div class="stats-grid">
      <!-- Existing stats cards -->
    </div>

    <!-- Session tabs (when sessions exist) -->
    <SessionTabs v-if="activeSessions.length > 0" />

    <!-- Main content area - conditional based on selection -->
    <div v-if="!selectedSessionId" class="global-view">
      <!-- Global overview (existing panels grid) -->
      <div class="panels-grid">
        <SessionsPanel :sessions="activeSessions" :loading="isLoading" />
        <ActivityFeed :events="recentActivity" />
        <SettingsPanel :settings="settings" />
      </div>
    </div>

    <div v-else class="session-view">
      <!-- Session-specific details -->
      <div class="session-layout">
        <div class="session-main">
          <SessionDetailPanel :session="selectedSession" />
          <ConversationView :conversation="sessionConversation" />
        </div>
        <div class="session-sidebar">
          <ToolExecutionList :tools="sessionTools" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.session-layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--space-lg);
}

.session-main {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

@media (max-width: 968px) {
  .session-layout {
    grid-template-columns: 1fr;
  }
}
</style>
```

---

## Implementation Order

### Phase 2.1: Backend API (Day 1)
1. Add service methods to `session_tracker.py`
2. Add 4 new endpoints to `main.py`
3. Test endpoints with curl/Postman
4. Verify data returned correctly

### Phase 2.2: Frontend Types & API (Day 1)
1. Add TypeScript interfaces to `types/index.ts`
2. Add API client methods to `services/api.ts`
3. Test API calls in browser console

### Phase 2.3: Store Integration (Day 2)
1. Add state variables to monitoring store
2. Add `fetchSessionDetails()` action
3. Add watcher for `selectedSessionId` changes
4. Test store updates on session selection

### Phase 2.4: SessionDetailPanel Component (Day 2)
1. Create component with metadata display
2. Test with selected session
3. Commit when working

### Phase 2.5: ToolExecutionList Component (Day 3)
1. Create component with expandable tool rows
2. Implement expand/collapse interaction
3. Add error highlighting
4. Test with sessions that have errors
5. Commit when working

### Phase 2.6: ConversationView Component (Day 3-4)
1. Create component with conversation timeline
2. Implement entry type styling (prompt vs message)
3. Add embedding status indicators
4. Test with sessions with/without conversation data
5. Commit when working

### Phase 2.7: Dashboard Layout (Day 4)
1. Update Dashboard.vue with conditional rendering
2. Implement session-view layout
3. Test switching between global and session views
4. Verify responsive behavior
5. Final commit for Phase 2

---

## Testing Strategy

### Backend Testing
1. **Endpoint testing:** Use curl or Postman to verify each endpoint
2. **Data validation:** Verify returned data matches database
3. **Error handling:** Test with invalid session_id
4. **Performance:** Check query times with large datasets

### Frontend Testing
1. **Component isolation:** Test each component individually via MCP Chrome DevTools
2. **Empty states:** Verify all components handle no data gracefully
3. **Real data:** Test with actual session data
4. **Errors:** Test API failure scenarios
5. **Interactions:** Test expand/collapse, selection, filtering

### Integration Testing
1. **Full flow:** Select session → verify all panels update
2. **Real-time updates:** Verify WebSocket updates session details
3. **Navigation:** Test switching between sessions
4. **Clear selection:** Test "All" button clears session view
5. **Responsive:** Test at different screen sizes

### MCP Chrome DevTools Checklist
- [ ] SessionDetailPanel displays metadata correctly
- [ ] ToolExecutionList shows tools with expand/collapse working
- [ ] ConversationView displays chronological conversation
- [ ] Empty states show appropriate messages
- [ ] Error states display clearly (failed tools, API errors)
- [ ] Switching sessions updates all panels
- [ ] "All" button returns to global view
- [ ] Design tokens used throughout (no hardcoded styles)

---

## Key Considerations

### Design Tokens
All styling uses CSS variables from `frontend/src/styles/tokens.css`:
- Colors: `--color-*`
- Spacing: `--space-*`
- Typography: `--font-*`
- Borders: `--radius-*`
- Shadows: `--shadow-*`
- Animation: `--duration-*`, `--easing-*`

### Empty States
Every component must handle:
- No data available (e.g., session without conversation)
- Loading states while fetching
- Error states when API fails

### Large Data Handling
- Tool results can be very large → truncate and expand on click
- Long conversations → consider virtualized scrolling if needed
- JSON formatting → pretty-print with syntax highlighting

### Real-time Updates
WebSocket should update session details when:
- New prompts captured
- New messages captured
- New tools executed
- Session status changes (ends)

### Session Selection Persistence
Current: Only in memory (lost on refresh)
Future: Consider URL params or localStorage

---

## Success Criteria

- [ ] All 4 backend endpoints working and tested
- [ ] All 3 frontend components created and functional
- [ ] Dashboard switches between global and session views
- [ ] Session selection persists across component updates
- [ ] All data displays correctly (prompts, messages, tools, metadata)
- [ ] Empty states handle missing data gracefully
- [ ] Error states show clearly (API failures, tool errors)
- [ ] Design tokens used exclusively (no hardcoded styles)
- [ ] Responsive layout works at all screen sizes
- [ ] Verified via MCP Chrome DevTools before each commit
- [ ] Real-time updates work (WebSocket integration)

---

## Next Steps After Phase 2

### Phase 3: Search & Semantic Features
- Create SemanticSearchPanel.vue
- Integrate with existing search endpoints
- Display search results with similarity scores
- Show embedding status and model info

### Phase 4: Layout Refinement
- Implement responsive breakpoints
- Add collapsible panels
- Polish transitions and interactions
- Move global settings to separate page

---

## Related Documentation

- Database Schema: `database/init.sql`
- API Reference: `docs/api/endpoints.md`
- Hook System: `HOOKS_ANALYSIS_REPORT.md`
- Frontend Conventions: `frontend/CLAUDE.md`
- Backend Conventions: `backend/CLAUDE.md`
