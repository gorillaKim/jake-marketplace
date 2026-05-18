---
name: solo-track
description: 메인 에이전트가 서브에이전트(worker) 호출 없이 직접 작업할 때 Engram 으로 라이프사이클 트래킹하는 스킬. 가벼운 작업도 issue/task/note 로 기록한다. analyzer/leader/worker 분리가 오버킬인 1~3 task 한 PR 분량에 적합. 트리거 — "트래킹", "기록하면서", "이슈로 진행", "solo track", "engram 으로 기록", "흔적 남기면서".
---

# Solo Track

## 목적

서브에이전트 spawn 없이 **메인 에이전트 자신이 직접 작업** 할 때, 그 작업을 Engram 의 이슈/태스크/노트 라이프사이클로 트래킹한다. analyzer/leader/worker 3-agent 분리가 오버킬인 가벼운 작업 (1~3 task, 한 PR 이하) 에 적합.

## 언제 사용하나

| 시나리오 | solo-track | engram-leader (UC2~4) | 직접 처리 |
|---------|-----------|---------------------|---------|
| 단일 task 텍스트 편집 | ❌ | ❌ | ✅ |
| 1~3 task 한 PR 분량 + **기록은 남기고 싶음** | ✅ | ⚠️ over | ❌ |
| 다중 PR / 여러 모듈 | ❌ | ✅ | ❌ |
| 멀티 LLM 라우팅 필요 | ❌ | ✅ | ❌ |
| 큰 요구사항 분할 후 진행 | ❌ (intake → analyzer) | (그 다음) | ❌ |

## intake-as-issue 와의 관계

- `intake-as-issue` 가 "다단계 작업" 판단 → `engram-analyzer` 서브에이전트 (UC1).
- "단발성/단순" 판단 → 직접 처리 (이슈 등록 없음).
- "작아도 트래킹은 하고 싶다" → **사용자가 명시적으로 solo-track 호출** 또는 "트래킹하면서 처리해줘" 발화 시 intake 게이트 우회하고 곧장 solo-track.

## agent_id 명명

메인 에이전트 본인:
```
main@<sessionShortId>-issue<issueId>
```

모든 mcp 호출에 위 agent_id 의무 포함. `history_by_agent("main@*")` 로 solo-track 활동 추적.

## 흐름 (Step A → Step E)

메인 에이전트가 단일 actor 로 전 단계 수행. v0.4.0 Hybrid 패턴의 worker/leader 분리가 한 actor 안으로 압축된 형태.

### Step A — 진입 분기 (continue vs new)

호출 받은 시점에 사용자가 `issue_id` 를 명시했는지 확인:

- **명시함** → **Step A.continue** (이어 작업)
- **명시 안 함** → **Step A.new** (새 이슈 등록)

---

#### Step A.continue — 이어 작업 (이전 다른 agent 가 만든/처리하던 이슈)

worker 의 Step 0~1 절차와 동일하게 **반드시 다음 5개 read 호출을 순서대로** 수행. 단일 actor 라도 기존 흔적은 명시적으로 검토해야 안전:

```
1. note_list(issue_id=N, note_type="comment", include_resolved=false)
2. note_list(issue_id=N, note_type="caveat", include_resolved=false)
3. session_restore(project_key)                            # 광역 caveat
4. issue_get(id=N, include_tasks=true, include_notes=true) # description + 모든 task + 모든 note
5. history_for(entity_type="issue", entity_id=N)           # 이전 agent 들의 작업 흔적
```

**상태별 분기**:

| `issue.status` | `issue.assigned_agent` | 행동 |
|--------------|----------------------|------|
| `required` | — | analyzer 가 ready 로 올려야 함 → 사용자에게 보고 후 종료 |
| `ready` | null | `issue_claim(N, agent_id="main@<sess>-issue<N>")` → Step B 진입 |
| `working` | == self (이전 본인) | `issue_release(ready)` 후 재 claim, 또는 사용자 확인 후 그대로 진행 |
| `working` | != self (다른 agent) | **다른 워커 점유 중**. claim 시도 금지. `history_by_agent(<해당 agent>)` 로 정말 일하는지 alongside check. 사용자에게 보고 후 종료 (필요 시 사용자가 `issue_release(force=true, agent_id="user")` 로 강제 회수) |
| `demo` / `finished` / `cancelled` | — | 작업 불가. 사용자에게 보고 후 종료 |

**질문성 코멘트 처리**: `"Q:" 접두어`, `"?" 종결`, 의문문 발견 시 즉시 답변:
```
note_add(issue_id=N, note_type="comment", author="agent", agent_id=<self>,
         summary="A: <답변>", detail=<상세>)
note_resolve(<원본 노트 id>)
```

**기존 task / note 검토 의무**:
- `status="required"` task 의 title 점검 → 이어 처리할 next task 결정.
- 최신 `decision` / `discovery` / `blocker_detail` note 검토 → 이전 agent 의 결정/발견 인지.
- 영향 주는 caveat 가 있으면 우선 처리/우회 전략 수립.

검토 후 claim 가능 판정이면 → Step B 진입 (코드 작업).

---

#### Step A.new — Pre-work: 이슈 등록 + 점유

```
# 1) project_key 결정 (analyzer 절차)
Bash("git config --get remote.origin.url") → repo 이름
session_restore() → 활성 프로젝트 매칭 → project_key 확정

# 2) 활성 스프린트
sprint_current() → sprint_id

# 3) 적합 에픽
epic_list(project_key) → 적합 에픽 찾기
  → 없으면 epic_create(project_key, title, description) 신규 생성

# 4) 이슈 생성
issue_create(epic_id, sprint_id, title, description, priority="low|medium|high")
  → issue_id 받기

# 5) task 등록 (1~3개)
task_create(issue_id=N, title="...") x 1~3

# 6) (선택) 분할 근거 note
note_add(issue_id=N, note_type="decision", author="agent",
         agent_id="main@<sess>-issue<N>",
         summary="solo-track 으로 진행", detail="<왜 1 이슈로 충분한지>")

# 7) ready → working (CAS 점유)
issue_update(id=N, status="ready", agent_id="main@<sess>-issue<N>")
issue_claim(id=N, agent_id="main@<sess>-issue<N>")
  → status="working", assigned_agent="main@<sess>-issue<N>"
```

### Step B — Work: 코드 작업 + 기록

각 task 에 대해:

1. 실제 작업 (Read/Edit/Write/Bash).
2. 발견/결정/블로커:
   ```
   note_add(issue_id=N,
            note_type=discovery|decision|blocker_detail|caveat|reference,
            author="agent",
            agent_id="main@<sess>-issue<N>",
            summary="...", detail="...")
   ```
3. 새 task 발견:
   ```
   task_insert_after(prev_id=<id>, title="...")
   ```
4. task 완료:
   ```
   task_update(id=<task_id>, status="finished",
               agent_id="main@<sess>-issue<N>")
   ```

### Step C — Demo Gate 자체 검증 (필수)

다음 셋 모두 통과해야 Step D 진행:

```
task_list(issue_id=N, status="required")  → 빈 배열인가
task_test_list(issue_id=N)                → 항목이 있으면 모두 checked 인가
Bash("git diff --name-only HEAD")         → 코드 변경이 있는 작업이면 1개 이상
```

**미통과 시** caveat note 후 ready 환원 (Step B 계속 또는 종료):

```
note_add(issue_id=N, note_type="caveat", agent_id="main@<sess>-issue<N>",
         summary="Demo gate 미통과", detail="<항목>")
issue_release(id=N, agent_id="main@<sess>-issue<N>", transition_to="ready")
session_end(project_key)
→ 사용자에게 보고
```

### Step D — Demo 진입

검증 통과 시:

```
note_add(issue_id=N, note_type="context", author="agent",
         agent_id="main@<sess>-issue<N>",
         summary="검토 가이드: <한 줄 핵심>",
         detail="확인 항목:\n- ...\n변경 파일:\n- <path> (이유)\n수동 확인:\n- <칸반 X 동작>\n남은 한계:\n- <있다면>\n증거:\n- git diff: <파일>\n- task_test: <pass/n/a>")

issue_release(id=N, agent_id="main@<sess>-issue<N>", transition_to="demo")
```

### Step E — Cleanup

```
session_end(project_key)
```

사용자에게 짧게 보고 + 데스크톱 칸반에서 demo → finished 처리 안내.

## 작업 중단 (blocker 발견)

```
note_add(issue_id=N, note_type="blocker_detail", agent_id="main@<sess>-issue<N>",
         summary="#<블로커> 에 의해 막힘", detail="<원인>")

issue_link(source_id=<블로커>, target_id=N, link_type="blocks")

issue_release(id=N, agent_id="main@<sess>-issue<N>", transition_to="ready")
session_end(project_key)

→ 사용자에게 보고 후 종료
```

## 호출 결과 인용 의무 (Anti-Hallucination)

메인 에이전트가 단일 actor 로 모든 호출을 하므로 v0.4.0 Hybrid 의 **leader evidence 검증 안전망이 없다**. 대신:

1. 각 mcp 호출 직후 응답 JSON 의 핵심 필드(id, status, error)를 응답에 인용.
2. Step C 의 git diff 검증을 **반드시 실제 Bash 호출** 로 수행.
3. 사용자가 같은 대화 안에 있으니 거짓말은 사후 즉시 발견 가능 — 메인 컨텍스트의 자연스러운 검증.

## 금지

- `issue_update(status="finished" | "cancelled")` — 사용자 전용.
- `note_resolve` on 사용자 코멘트(`author="user"`) — 사용자가 직접 종결.
- `agent_id` 인자 누락 금지.
- Step C (Demo Gate) 생략 후 release(demo) 금지.
- task 가 어렵다고 status="cancelled" 우회 금지 — caveat + ready 환원으로 보고.

## 출력 형식 (사용자에게 마지막 보고)

```
[solo-track] Engram issue #<N> 처리 완료 → demo 진입.

epic: #<E> · <epic_title>
issue: #<N> · <title> (priority: <p>)
tasks: #<t1>/#<t2>/... (모두 finished)
notes:
  - decision #<id>: <summary>
  - discovery #<id>: <summary>  (있으면)
  - context #<id>: 검토 가이드

agent_id: main@<sess>-issue<N>
변경 파일:
  - <path1>
  - <path2>

사용자 다음 단계:
  - 데스크톱 칸반에서 #<N> 의 demo → finished 로 옮겨 종결.
```

## 동작 예 (한 사이클)

사용자: *"이 함수 리네이밍하면서 트래킹해줘"*

```
1. Pre-work:
   - epic_list → "리팩터링" 에픽 찾음 (id=4)
   - issue_create(epic_id=4, title="X 함수 리네이밍", priority="low") → #142
   - task_create(#142, "ast-grep 으로 사용처 찾기")
   - task_create(#142, "rename + 호출자 업데이트")
   - issue_update(#142, ready, agent_id="main@a4b2-issue142")
   - issue_claim(#142, agent_id="main@a4b2-issue142") → working ✓

2. Work:
   - Bash("ast-grep ...") + Edit x N + task_update(finished) x 2
   - note_add(discovery, agent_id, "테스트 파일에서도 사용 중 — 함께 업데이트")

3. Demo Gate:
   - task_list(#142, required) = [] ✓
   - Bash("git diff --name-only HEAD") = [src/x.ts, src/y.ts, tests/x.test.ts] ✓

4. Demo 진입:
   - note_add(#142, context, agent_id, "검토 가이드: X 함수를 Y 로 리네이밍...")
   - issue_release(#142, agent_id, transition_to="demo") → demo ✓

5. Cleanup:
   - session_end(project_key)

보고:
   [solo-track] Engram issue #142 처리 완료 → demo 진입.
   agent_id: main@a4b2-issue142
   변경 파일: 3개
   사용자 다음 단계: 칸반에서 #142 demo → finished.
```
