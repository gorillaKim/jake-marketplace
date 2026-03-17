#!/usr/bin/env python3
"""skill-doctor signal collector — hybrid hook + agent signal detection.

Phase 1 (hooks): Accumulate raw events in active/{session_id}.json
Phase 2 (Stop hook): Inject raw events into Claude's context via additionalContext
Phase 3 (agent): Claude classifies signals, attributes cause_type, and records to DB

Usage (called by hooks, not directly):
  echo '{"hook_event_name":"PostToolUseFailure",...}' | python3 signal-collector.py
"""

import json
import sys
import time
from pathlib import Path

DATA_DIR = Path.home() / ".claude" / "skill-doctor"
ACTIVE_DIR = DATA_DIR / "active"

# ── Phase 1: Raw event accumulation ────────────────────────────────────────


def get_session_file(session_id):
    ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    return ACTIVE_DIR / f"{session_id}.json"


def load_session(session_id):
    f = get_session_file(session_id)
    if f.exists():
        try:
            return json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"skill": None, "raw_events": [], "started_at": time.time()}


def save_session(session_id, data):
    f = get_session_file(session_id)
    f.write_text(json.dumps(data, ensure_ascii=False))


def cleanup_session(session_id):
    f = get_session_file(session_id)
    try:
        f.unlink()
    except OSError:
        pass


def handle_post_tool_use_failure(data, session):
    """Accumulate raw tool failure event — no classification yet."""
    is_interrupt = data.get("is_interrupt", False)
    tool_name = data.get("tool_name", "")
    error = ""

    tool_response = data.get("tool_response")
    if isinstance(tool_response, dict):
        error = tool_response.get("stderr", "") or tool_response.get("error", "")
    elif isinstance(tool_response, str):
        error = tool_response
    if not error:
        error = data.get("error", "")

    session["raw_events"].append({
        "event": "tool_failure",
        "tool": tool_name,
        "error": error[:300],
        "is_interrupt": is_interrupt,
        "ts": time.time(),
    })


def handle_user_prompt_submit(data, session):
    """Accumulate user message — agent will judge if it's a correction."""
    prompt = data.get("prompt", "")
    if not prompt or len(prompt.strip()) < 3:
        return
    session["raw_events"].append({
        "event": "user_message",
        "text": prompt[:300],
        "ts": time.time(),
    })


def handle_subagent_start(data, session):
    agent_type = data.get("agent_type", "")
    if agent_type:
        session["skill"] = agent_type


def handle_subagent_stop(data, session):
    agent_type = data.get("agent_type", "")
    if agent_type and not session.get("skill"):
        session["skill"] = agent_type


# ── Phase 2: Stop — inject raw events into Claude context ──────────────────


def handle_stop(data, session, session_id):
    """On Stop: inject accumulated raw events as additionalContext for Claude to classify."""
    skill = session.get("skill")
    raw_events = session.get("raw_events", [])

    # No skill identified = not a skill execution (general conversation) — discard
    if not skill:
        cleanup_session(session_id)
        return output_continue()

    # Nothing to review
    if not raw_events:
        cleanup_session(session_id)
        return output_continue()

    # Build context for Claude to classify
    context = build_classification_context(skill, raw_events)
    cleanup_session(session_id)

    # Return additionalContext — injected as system-reminder into Claude's context
    print(json.dumps({
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": context,
        }
    }))
    sys.exit(0)


def build_classification_context(skill, raw_events):
    """Build the context string that tells Claude to classify signals."""
    skill_label = skill or "(스킬명 미확인)"
    event_summary = []

    for i, ev in enumerate(raw_events[-10:], 1):  # max 10 events
        if ev["event"] == "tool_failure":
            if ev.get("is_interrupt"):
                event_summary.append(f"  {i}. [INTERRUPT] {ev['tool']} — 사용자 인터럽트")
            else:
                event_summary.append(f"  {i}. [TOOL_ERROR] {ev['tool']} — {ev['error'][:150]}")
        elif ev["event"] == "user_message":
            event_summary.append(f"  {i}. [USER_MSG] \"{ev['text'][:100]}\"")

    events_text = "\n".join(event_summary)

    return f"""[skill-doctor] 이 세션에서 아래 이벤트가 감지되었습니다.
스킬: {skill_label}

{events_text}

위 이벤트 중 **스킬 품질과 관련된 유의미한 시그널**이 있다면, 아래 JSON을 Write 도구로 저장해주세요.
경로: ~/.claude/skill-doctor/tmp/sd-session-{int(time.time())}.json

```json
{{
  "skill": "{skill or '스킬명'}",
  "signals": [
    {{"type": "tool_error|correct|redo|cancelled", "context": "한줄 설명", "cause_type": "ambiguous_instruction|missing_precondition|scope_exceeded|error_handling|output_mismatch|insufficient_context|user_preference|external_issue", "cause_detail": "구체적 원인"}}
  ]
}}
```

저장 후: `python3 ${{CLAUDE_PLUGIN_ROOT}}/scripts/cli.py record --file <path>`

**판단 기준**:
- 정상적인 탐색 실패(grep 결과 없음, 파일 존재 확인 등)는 시그널이 아닙니다 — 무시하세요.
- 사용자의 단순 대화나 질문은 correction이 아닙니다 — 무시하세요.
- 스킬 프롬프트의 모호성/누락으로 인한 실패만 스킬 측 cause_type으로 기록하세요.
- 유의미한 시그널이 없으면 아무것도 하지 마세요."""


def output_continue():
    """Default passthrough output."""
    print(json.dumps({"continue": True, "suppressOutput": True}))
    sys.exit(0)


# ── Main ───────────────────────────────────────────────────────────────────


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            output_continue()
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        output_continue()

    event = data.get("hook_event_name", "")
    session_id = data.get("session_id", "unknown")
    session = load_session(session_id)

    if event == "PostToolUseFailure":
        handle_post_tool_use_failure(data, session)
        save_session(session_id, session)

    elif event == "UserPromptSubmit":
        handle_user_prompt_submit(data, session)
        save_session(session_id, session)

    elif event == "SubagentStart":
        handle_subagent_start(data, session)
        save_session(session_id, session)

    elif event == "SubagentStop":
        handle_subagent_stop(data, session)
        save_session(session_id, session)

    elif event == "Stop":
        handle_stop(data, session, session_id)

    elif event == "SessionEnd":
        # SessionEnd — just cleanup, no context injection possible
        cleanup_session(session_id)

    output_continue()


if __name__ == "__main__":
    main()
