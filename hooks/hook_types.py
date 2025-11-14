"""
Type definitions for Claude Code hook inputs.
Based on official Claude Code documentation and examples from:
- reference/claude-code/claude-code-official-repo/examples/hooks/
- reference/claude-code/claude-code-docs/06-reference/05-hooks-reference.md
"""
from typing import TypedDict, Any, Literal, Optional


# Common fields present in all hook events
class BaseHookInput(TypedDict):
    """Base hook input fields common to all events"""
    session_id: str
    transcript_path: str
    cwd: str
    permission_mode: Literal["default", "plan", "acceptEdits", "bypassPermissions"]
    hook_event_name: str


# PreToolUse and PostToolUse events
class ToolUseHookInput(BaseHookInput):
    """Hook input for PreToolUse and PostToolUse events"""
    hook_event_name: Literal["PreToolUse", "PostToolUse"]
    tool_name: str
    tool_input: dict[str, Any]  # Tool-specific parameters
    tool_response: Optional[dict[str, Any]]  # Only present in PostToolUse


# SessionStart event
class SessionStartInput(BaseHookInput):
    """Hook input for SessionStart event"""
    hook_event_name: Literal["SessionStart"]
    source: Literal["startup", "resume", "clear", "compact"]


# SessionEnd event
class SessionEndInput(BaseHookInput):
    """Hook input for SessionEnd event"""
    hook_event_name: Literal["SessionEnd"]
    reason: str


# UserPromptSubmit event
class UserPromptSubmitInput(BaseHookInput):
    """Hook input for UserPromptSubmit event"""
    hook_event_name: Literal["UserPromptSubmit"]
    prompt: str


# Notification event
class NotificationInput(BaseHookInput):
    """Hook input for Notification event"""
    hook_event_name: Literal["Notification"]
    message: str
    notification_type: Literal[
        "permission_prompt",
        "idle_prompt",
        "auth_success",
        "elicitation_dialog"
    ]


# Stop event
class StopInput(BaseHookInput):
    """Hook input for Stop event"""
    hook_event_name: Literal["Stop"]
    stop_hook_active: bool


# PreCompact event
class PreCompactInput(BaseHookInput):
    """Hook input for PreCompact event"""
    hook_event_name: Literal["PreCompact"]
    trigger: Literal["manual", "auto"]
    custom_instructions: str


# Union of all possible hook inputs
HookInput = (
    ToolUseHookInput
    | SessionStartInput
    | SessionEndInput
    | UserPromptSubmitInput
    | NotificationInput
    | StopInput
    | PreCompactInput
)


# Common tool_input structures for different tools
class BashToolInput(TypedDict):
    """tool_input structure for Bash tool"""
    command: str
    description: Optional[str]
    timeout: Optional[int]


class WriteToolInput(TypedDict):
    """tool_input structure for Write tool"""
    file_path: str
    content: str


class EditToolInput(TypedDict):
    """tool_input structure for Edit tool"""
    file_path: str
    old_string: str
    new_string: str
    replace_all: Optional[bool]


class ReadToolInput(TypedDict):
    """tool_input structure for Read tool"""
    file_path: str
    offset: Optional[int]
    limit: Optional[int]
