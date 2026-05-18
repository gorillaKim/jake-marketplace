---
name: work-journaling
description: Engram 이슈를 처리하는 작업자가 작업 전·중·후에 코멘트/노트/상태를 기록하는 표준 절차. v0.3.0 부터 issue_claim/issue_release 와 agent_id 의무 포함. engram-worker spawn 시 자동 로드. 트리거 — "engram 작업", "issue 처리", "워커 시작", "이슈 작업", "작업 기록", "journaling".
---

# Work Journaling

## 목적

Engram 이슈를 처리하는 동안 **무엇을 / 누가 / 왜 / 어디서 막혔는지** 가 영구적으로 남도록 한다.
이 스킬을 따르면 사용자가 demo 단계에서 검토할 때 변경 의도와 검증 포인트를 한 화면에서 볼 수 있다.

## 적용 대상

- `engram-worker` 가 자기 이슈를 처리하는 모든 시점.
- (선택) 사용자가 직접 한 이슈를 처리할 때도 권장.

## agent_id 의무 (필수)

모든 `mcp__engram__*` 호출에 `agent_id` 를 명시한다. worker 의 경우 호출자가 주입한 값을 그대로 사용:

```
<model>@<sessionShortId>-issue<issueId>
```

agent_id 가 없으면 `history_by_agent` 가 작동하지 못해 멀티 에이전트 추적이 사라진다.

## 절대 순서 (Step 0 → Step 6)

이 순서를 어기면 work-journaling 위반. 각 단계는 mcp 호출 응답을 본인 응답에 인용해 증거를 남긴다.

### Step 0 — 코멘트/caveat 검토 (mcp 첫 호출, 스킵 금지)

```
note_list(issue_id=<issue_id>, note_type="comment", include_resolved=false)
note_list(issue_id=<issue_id>, note_type="caveat", include_resolved=false)
```

- 코멘트 상위 10건 검토. 질문성("Q:" 접두어, "?" 종결, "어떻게/왜/언제/어디" 의문문) 발견 시:
  ```
  note_add(issue_id, note_type="comment", author="agent", agent_id=<self>,
           summary="A: <답변>", detail=<상세>)
  note_resolve(<원본 질문 노트 id>)
  ```
- 답변 불가 시 사용자에게 보고 후 작업 보류.
- 작업에 영향 주는 caveat 가 있으면 우선 처리/우회 전략 결정.

> **이 단계는 worker 의 가장 첫 mcp 호출**. issue_claim 보다 먼저.

### Step 1 — 컨텍스트 적재

```
session_restore(project_key)
issue_get(id=<issue_id>, include_tasks=true, include_notes=true)
```

- `issue.assigned_agent` 가 본인이 아닌 다른 값이면 즉시 종료.
- `session_restore.active_caveats` 광역 caveat 검토.

### Step 2 — 점유 (issue_claim, CAS)

```
issue_claim(id=<issue_id>, agent_id=<self>)
```

응답 분기:
- **성공**: `status="working"`, `assigned_agent=<self>`. 다음 단계.
- **거부**: `"already held by another agent"` → 즉시 종료. retry 금지.

⚠️ `issue_update(status="working")` 직접 호출 금지. 반드시 `issue_claim` 사용.

### Step 3 — 작업 중 기록

발생 유형별 `note_add` (author="agent", agent_id=<self>):

| 발생 | note_type | 예시 summary |
|------|-----------|--------------|
| 의도된 설계 결정 | `decision` | "캐시 키에 user_id 포함 — multi-tenant 격리" |
| 작업 중 발견한 사실 | `discovery` | "기존 X 모듈이 이미 Y 기능을 가짐" |
| 블로커 (다른 이슈 대기) | `blocker_detail` | "결제 모듈 #128 완료 후 가능" |
| 같은 실수 반복 방지 | `caveat` | "이 RPC 는 1초 timeout 이 너무 짧음" |
| 외부 참조 | `reference` | "RFC 7234 §5.2" |

task 진행:
```
task_update(id=<task_id>, status="finished", agent_id=<self>)
task_insert_after(prev_id=<id>, title=...)
```

### Step 4 — Demo Gate (자체 검증, 필수)

demo 전이 전 모두 통과:

1. `task_list(issue_id, status="required")` 결과 = 빈 배열.
2. `task_test_list(issue_id)` 항목이 있으면 모두 `checked`.
3. 코드 변경이 있었으면 `Bash("git diff --name-only HEAD")` 결과 1개 이상.

미통과 시 demo 전이 금지. caveat note 로 사유 기록 후 Step 6 (release ready) 으로 안전 복귀.

### Step 5 — Demo 진입 (issue_release)

자체 검증 통과 후:

```
note_add(issue_id, note_type="context", author="agent", agent_id=<self>,
         summary="검토 가이드: <한 줄 핵심>",
         detail="확인 항목:\n- ...\n변경 파일:\n- <path> (이유)\n수동 확인:\n- <칸반 X 동작>\n남은 한계:\n- <있다면>\n증거:\n- <git diff/test 결과 또는 mcp 호출 응답 인용>")

issue_release(id=<issue_id>, agent_id=<self>, transition_to="demo")
```

⚠️ `issue_update(status="demo")` 직접 호출 금지. 반드시 `issue_release` 사용 (ownership 해제 + 전이 동시).

### Step 6 — 세션 정리 (자기 claim 안전 회수)

```
1. issue_get(id=<issue_id>) → assigned_agent, status 확인
2. 만약 assigned_agent == <self> 이고 status == "working" 이면:
     issue_release(id=<issue_id>, agent_id=<self>, transition_to="ready")
     note_add(issue_id, note_type="caveat", author="agent", agent_id=<self>,
              summary="비정상 종료 — ready 환원", detail=<마지막 상태/이유>)
3. session_end(project_key)
```

정상 demo 진입의 경우 Step 5 에서 이미 release 됐으므로 (2) 는 no-op.

## 사용자 코멘트와 agent 노트의 분리

- 사용자 댓글 = `note_type="comment"`, `author="user"` (CommentSection 노출).
- agent 검토 가이드 = `note_type="context"`, `author="agent"`.
- agent 가 코멘트에 답변할 때만 `note_type="comment"`, `author="agent"`.

## 호출 결과 인용 의무 (Anti-Hallucination)

각 mcp 호출 직후 응답 JSON 의 핵심 필드(id, status, assigned_agent, error)를 본인 응답에 인용.
호출 없이 ID 발명/placeholder 보고 금지.

## 금지

- `issue_update(status="finished" | "cancelled")` — 사용자 전용.
- `issue_update(status="working" | "demo")` — `issue_claim` / `issue_release` 사용.
- 사용자 코멘트(`comment` + `author="user"`)에 대한 `note_resolve` 금지.
- task status="cancelled" 로 우회 금지 — caveat + ready 환원 후 보고.
- agent_id 누락 금지.
- Step 0~6 순서 건너뛰기 금지.
