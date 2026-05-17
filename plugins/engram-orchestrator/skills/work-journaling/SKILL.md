---
name: work-journaling
description: Engram 이슈를 처리하는 작업자가 작업 전·중·후에 코멘트/노트/상태를 기록하는 표준 절차. engram-worker spawn 시 자동 로드되거나 사용자가 명시 호출. 트리거 키워드 — "engram 작업", "issue 처리", "워커 시작", "이슈 작업", "작업 기록", "journaling".
---

# Work Journaling

## 목적

Engram 이슈를 처리하는 동안 **무엇을 / 왜 / 어디서 막혔는지** 가 영구적으로 남도록 한다.
이 스킬을 따르면 사용자가 demo 단계에서 검토할 때 변경 의도와 검증 포인트를 한 화면에서 볼 수 있다.

## 적용 대상

- `engram-worker` 가 자기 이슈를 처리하는 모든 시점.
- (선택) 사용자가 직접 한 이슈를 처리할 때도 같은 절차를 권장.

## 작업 전

1. 컨텍스트 적재:
   ```
   session_restore(project_key)
   issue_get(id=<issue_id>)
   task_list(issue_id=<issue_id>)
   ```
2. 코멘트 검토 — **반드시 작업 시작 전에**:
   ```
   note_list(issue_id=<issue_id>, note_type="comment", include_resolved=false)
   ```
   - 최신 created_at 기준 상위 10건을 검토한다.
   - 질문성 코멘트(접두어 "Q:", "?" 종결, "어떻게/왜/언제/어디" 의문문) 발견 시:
     ```
     note_add(issue_id, note_type="comment", author="agent",
              summary="A: <답변 한 줄>", detail=<상세 근거>)
     note_resolve(<원본 질문 노트 id>)
     ```
   - 답변할 수 없는 질문이면 답변 대신 사용자에게 보고 후 작업 보류.

3. 기존 caveat 검토:
   ```
   note_list(issue_id=<issue_id>, note_type="caveat", include_resolved=false)
   ```
   - 작업에 영향 주는 caveat 이 있으면 우선 해결 또는 우회 전략 수립.

## 작업 시작

```
issue_update(id=<issue_id>, status="working")
```

## 작업 중 기록

발생 유형별로 `note_add` 호출 (author 는 항상 "agent"):

| 발생 | note_type | 예시 summary |
|------|-----------|--------------|
| 의도된 설계 결정 | `decision` | "캐시 키에 user_id 포함 — multi-tenant 격리" |
| 작업 중 발견한 사실 | `discovery` | "기존 X 모듈이 이미 Y 기능을 가짐" |
| 블로커 (다른 이슈 대기) | `blocker_detail` | "결제 모듈 #128 완료 후 가능" |
| 같은 실수 반복 방지 | `caveat` | "이 RPC 는 1초 timeout 이 너무 짧음" |
| 외부 참조 | `reference` | "RFC 7234 §5.2" |

각 task 완료마다:
```
task_update(id=<task_id>, status="finished")
```

새로 발견된 작업:
```
task_insert_after(prev_id=<id>, title=..., source="agent_discovered")
```

## 작업 종료 (demo 진입)

모든 task 가 finished 가 되면, **demo 전이 직전에** 검토 가이드를 남긴다:

```
note_add(issue_id, note_type="context", author="agent",
         summary="검토 가이드: <한 줄 핵심>",
         detail="확인 항목:\n  - ...\n변경 파일:\n  - path/to/file.rs (이유: ...)\n수동 확인:\n  - 칸반에서 <X> 동작\n남은 한계:\n  - <있다면>")
issue_update(id=<issue_id>, status="demo")
```

여기서 작업 종료. **finished / cancelled 전이는 절대 호출하지 않는다** — 사용자 권한.

## 사용자 코멘트와 agent 노트의 분리

- 사용자가 남기는 댓글 = `note_type="comment"`, `author="user"` (데스크톱 CommentSection 으로 노출).
- agent 가 작성하는 검토 가이드 = `note_type="context"`, `author="agent"`.
- agent 가 코멘트에 답변할 때만 `note_type="comment"`, `author="agent"`.

이 규칙으로 사용자의 코멘트 조회가 agent 의 검토 가이드/내부 노트로 오염되지 않는다.

## 금지

- `issue_update(status="finished" | "cancelled")` 호출 금지.
- 사용자 코멘트(`comment` + `author="user"`)에 대한 `note_resolve` 금지 — 사용자가 직접 종결.
- 한 task 가 어렵다고 status="cancelled" 로 우회 금지 — caveat + ready 환원 후 보고.
