---
name: work-journaling
description: Engram 이슈를 처리하는 worker + leader 가 따르는 표준 절차. v0.4.0 부터 worker = 코드 작업 + note 직접 / leader = 상태 전이 + evidence 자체 검증으로 호출 권한 분리. WORKER_RESULT 양식으로 인계. 트리거 — "engram 작업", "issue 처리", "워커 시작", "이슈 작업", "작업 기록", "journaling".
---

# Work Journaling (v0.4.0 — Hybrid)

## 목적

Engram 이슈 처리 중 **무엇을 / 누가 / 왜 / 어디서 막혔는지** 가 영구적으로 남도록 한다.
v0.4.0 부터 **worker 와 leader 의 호출 권한이 분리** 되어 sub-agent fake call 위험을 물리적으로 차단한다.

## 호출 주체 매트릭스

| 호출 | worker | leader |
|------|--------|--------|
| `issue_claim` (점유) | ❌ | ✅ (spawn 전) |
| `issue_release` (전이) | ❌ | ✅ (검증 후) |
| `issue_update` (상태) | ❌ | ✅ (예외 시) |
| `issue_link` (의존성) | ❌ | ✅ (worker 가 blocker 보고하면) |
| `task_update(finished)` | ❌ | ✅ (WORKER_RESULT 받아 일괄) |
| `task_create` | ❌ (analyzer 만) | ❌ (analyzer 만) |
| `task_insert_after` (새 task 발견) | ✅ | ❌ |
| `task_test_check_bulk` | ✅ | ✅ |
| `note_add(comment)` (질문 답변) | ✅ | ❌ |
| `note_add(discovery)` | ✅ | ❌ |
| `note_add(decision)` | ✅ | ❌ |
| `note_add(blocker_detail)` | ✅ | ✅ (leader 도 worker 보고 받아 추가) |
| `note_add(caveat)` (실시간 주의) | ✅ | ✅ (검증 실패 / stalled 경고) |
| `note_add(context)` (검토 가이드) | ❌ | ✅ (WORKER_RESULT 받아) |
| `note_add(reference, [SKILL])` (스킬 발동 추적) | ✅ | ❌ |
| `note_add(reference, [RULE])` (룰 적용 감사) | ✅ | ❌ |
| `note_resolve` (질문 종결) | ✅ | ❌ |
| `session_end` | ❌ | ✅ (사이클 끝) |

## worker 절대 순서 (Step 0 → Step 4)

### Step 0 — 코멘트/caveat 검토 (mcp 첫 호출, 스킵 금지)

```
note_list(issue_id, note_type="comment", include_resolved=false)
note_list(issue_id, note_type="caveat", include_resolved=false)
```

질문성 코멘트 답변:
```
note_add(issue_id, note_type="comment", author="agent", agent_id=<self>,
         summary="A: <답변>", detail=...)
note_resolve(<원본 노트 id>)
```

답변 불가 시 작업 보류 → `WORKER_RESULT.status="blocked"`.

### Step 1 — 컨텍스트 적재 + 점유 확인

```
session_restore(project_key)
issue_get(id=<issue_id>, include_tasks=true, include_notes=true)
```

**필수**: `issue.assigned_agent == <self>` 확인. 다르면 `WORKER_RESULT.status="abandoned"` 즉시 보고 후 종료.

`session_restore.active_caveats` 광역 caveat 검토.

### Step 2 — 코드 작업

각 task 별 실제 작업 (Read/Edit/Write/Bash). 발견/결정 발생 시 즉시:

```
note_add(issue_id, note_type=discovery|decision|blocker_detail|caveat|reference,
         author="agent", agent_id=<self>, summary=..., detail=...)
```

새 task 발견 시 `task_insert_after`. task 완료 시 **내부 finished 목록에 task_id 만 적어둠** — `task_update` 호출 금지.

### Step 2.5 — Incoming Comment 체크 (매 task 진입 직전 1회, v0.4.1)

worker 가 작업 중 leader 가 추가한 `Q: stalled` 같은 질문 코멘트를 놓치지 않도록, **매 task 진입 직전 1회** (또는 한 task 가 5분 이상 걸리면 중간 1회) 다음을 호출:

```python
new_comments = note_list(issue_id=N, note_type="comment", include_resolved=false)
for c in new_comments:
    if c.summary.startswith("Q: stalled") or "아직 작업 중" in c.summary:
        note_add(
            issue_id=N,
            note_type="comment", author="agent", agent_id=<self>,
            summary=f"A: 작업 중, 현재 task #<id> 진행 중",
            detail=f"<현재 어느 단계인지 짧게>"
        )
        note_resolve(c.id)
```

**체크 빈도**: 매 task 진입 직전 1회. 너무 자주 호출하면 토큰 낭비 — task 사이 호출이 충분.

**한계 (Claude Code 동기 모델)**: worker spawn 1회 안에서만 응답 가능. spawn 끝난 워커는 다음 leader 사이클에 재 spawn 돼야 응답 가능. engram 측 SSE 가 들어오기 전엔 사용자 답변이 주된 경로.

### Step 3 — Demo Gate 자체 수집

```
task_list(issue_id, status="required")  → 남은 task 수
task_test_list(issue_id)                → checked 여부
Bash("git status --porcelain | awk '{print $2}'")  → 변경+신규 파일 목록 (untracked 포함)
```

결과를 WORKER_RESULT.evidence 에 인용.

### Step 4 — WORKER_RESULT 보고 (마지막 출력)

마지막 응답의 마지막 코드 블록으로 YAML 출력:

```yaml
WORKER_RESULT:
  status: demo_ready  # | blocked | abandoned
  agent_id: <self>
  issue_id: <N>
  tasks_finished: [11, 12]
  tasks_new: []
  evidence:
    required_tasks_remaining: 0
    test_check_pass: true
    git_diff_files: ["src/...", "tests/..."]
  context_note:
    summary: "검토 가이드: <한 줄>"
    detail: |
      확인 항목: ...
      변경 파일: ...
      수동 확인: ...
      남은 한계: ...
      증거: task_list=[], test_pass=true, diff=2
  blocker_detail: null  # blocked 일 때만 채움
```

## [SKILL] / [RULE] 접두어 컨벤션

worker 가 스킬 발동 또는 caveat 룰 적용 시 `reference` 타입 노트로 즉시 기록한다.

### 스킬 발동 노트 (`[SKILL]`)

```
note_add(issue_id, note_type="reference", author="agent", agent_id=<self>,
         summary="[SKILL] <skill-name> — <호출|스킵>, <적절|불필요|필수였으나 누락>",
         detail="목적: <왜 발동했는가>\n결과: <스킬이 반환한 것 또는 효과>\n판단: <이 작업에 적절했는가, 이유>")
```

적절 발동 예시:
```
summary: "[SKILL] work-journaling — 호출, 적절"
detail: |
  목적: 워커 표준 절차 확인
  결과: Step 0-4 흐름 재확인
  판단: 이슈 작업 진입 시 필수 — 적절
```

불필요 발동 예시:
```
summary: "[SKILL] sprint-retro — 호출, 불필요"
detail: |
  목적: 현재 스프린트 상태 파악 시도
  결과: 스프린트 회고 문서 생성 흐름 시작됨
  판단: 이 이슈는 코드 수정 작업, 회고와 무관 — 불필요 발동
```

### 룰 적용 감사 노트 (`[RULE AUDIT]`) — Step 1 active_caveats 검토 후 1회

```
note_add(issue_id, note_type="reference", author="agent", agent_id=<self>,
         summary="[RULE AUDIT] 광역 규칙 <N>건 검토",
         detail="<각 caveat 별 한 줄>\n- <요약> → 적용함|해당없음|주의 관찰")
```

예시:
```
summary: "[RULE AUDIT] 광역 규칙 2건 검토"
detail: |
  - PR 크기 100줄 제한 → 적용함 (커밋 단위 분리 예정)
  - 테스트 커버리지 80% 유지 → 해당없음 (문서 전용 이슈)
```

active_caveats 가 0건이면 `summary="[RULE AUDIT] 광역 규칙 없음"` 한 줄로 기록 (생략 불가).

---

## leader 절대 순서 (WORKER_RESULT 받은 후)

### 1) 파싱 + evidence 자체 검증 (필수)

```
required_remaining = task_list(issue_id, status="required")
tests = task_test_list(issue_id)
actual_diff = Bash("git status --porcelain | awk '{print $2}'")
```

worker.evidence 와 일치 안 하면 검증 실패. 이게 안티-할루시네이션 마지막 안전망.

### 2) status 별 처리

#### demo_ready (검증 통과)

```
for tid in WORKER_RESULT.tasks_finished:
    task_update(id=tid, status="finished", agent_id=engram-leader@<sess>)

note_add(issue_id, note_type="context", agent_id=engram-leader@<sess>,
         summary=WORKER_RESULT.context_note.summary,
         detail=WORKER_RESULT.context_note.detail)

issue_release(id=issue_id, agent_id=<worker_agent_id>, transition_to="demo")
```

#### demo_ready (검증 실패)

```
note_add(caveat, summary="Demo gate fail: <항목>", detail=<불일치 내역>)
issue_release(transition_to="ready", agent_id=<worker_agent_id>)
```

#### blocked

```
issue_link(source_id=blocker, target_id=issue, link_type="blocks")
note_add(blocker_detail, summary=..., detail=...)
issue_release(transition_to="ready", agent_id=<worker_agent_id>)
```

#### abandoned

```
note_add(caveat, summary="worker abandoned", detail=...)
issue_release(transition_to="ready", agent_id=<worker_agent_id>)
```

### 3) Cleanup

```
session_end(project_key)
```

(여러 이슈 처리 사이클이면 마지막에 한 번)

## 사용자 코멘트와 agent 노트의 분리

- 사용자 댓글 = `note_type="comment"`, `author="user"` (CommentSection 노출).
- agent 검토 가이드 = `note_type="context"`, `author="agent"` (**leader 만 작성**).
- agent 가 코멘트에 답변할 때만 `note_type="comment"`, `author="agent"` (worker 가 답변).

## 호출 결과 인용 의무 (Anti-Hallucination)

worker 와 leader 모두 mcp 호출 직후 응답 JSON 핵심 필드를 본인 응답에 인용.
WORKER_RESULT.evidence.git_diff_files 는 반드시 실제 `Bash("git status --porcelain | awk '{print $2}'"`)` 결과.
**leader 가 동일 Bash 호출로 재검증** → 차이 발견 시 release(demo) 거부.

## 금지

### worker
- `issue_claim`, `issue_release`, `issue_update` 호출 금지.
- `task_update`, `task_create`, `session_end` 호출 금지.
- 사용자 코멘트(`author="user"`) `note_resolve` 금지.
- `agent_id` 누락 금지.
- WORKER_RESULT 양식 위반 금지.
- Step 0~4 순서 건너뛰기 금지.

### leader
- worker 의 직접 호출 영역 (discovery/decision/blocker_detail/caveat note) 침범 금지.
- demo→finished, *→cancelled 전이 절대 금지.
- WORKER_RESULT evidence 자체 검증 없이 release(demo) 호출 금지.
- agent_id 누락 금지.
