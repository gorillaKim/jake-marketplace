---
name: solo-track
description: 메인 에이전트가 서브에이전트(worker) 호출 없이 직접 작업할 때 Engram 으로 라이프사이클 트래킹하는 스킬. 가벼운 작업도 issue/task/note 로 기록한다. analyzer/leader/worker 분리가 오버킬인 1~3 task 한 PR 분량에 적합. 트리거 — "트래킹", "기록하면서", "이슈로 진행", "solo track", "engram 으로 기록", "흔적 남기면서".
---

# Solo Track

## 목적

**병렬 worker 를 spawn 하지 않고 메인 에이전트 자신이 직접 작업** 할 때, 그 작업을 Engram 의 이슈/태스크/노트 라이프사이클로 트래킹한다. analyzer/leader/worker 3-agent 분리가 오버킬인 작업에 적합 — 이슈가 여러 개라도 직렬로 처리하면 되는 한 가능한 한 solo 를 쓴다(팀은 [진짜 복잡한 예외](../../README.md#실행-모드-라우팅-solo-track-vs-팀)에만).

> **단, 리뷰는 예외 — solo 라도 리뷰 패스는 `engram-reviewer` 서브에이전트를 spawn 한다** (Step D.5). 작성자(메인)와 리뷰어를 다른 컨텍스트로 분리해 자기 승인(self-approve)을 막기 위함. "solo" 는 *병렬 worker 를 안 띄운다*는 뜻이지 *모든 서브에이전트를 안 띄운다*는 뜻이 아니다.

## 언제 사용하나

| 시나리오 | solo-track | engram-leader (UC2~4) | 직접 처리 |
|---------|-----------|---------------------|---------|
| 단일 task 텍스트 편집 | ❌ | ❌ | ✅ |
| 1~3 task 한 PR 분량 + **기록은 남기고 싶음** | ✅ | ⚠️ over | ❌ |
| 다중 PR / 여러 모듈 | ❌ | ✅ | ❌ |
| 멀티 LLM 라우팅 필요 | ❌ | ✅ | ❌ |
| 큰 요구사항 분할 후 진행 | ❌ (intake → analyzer) | (그 다음) | ❌ |

> 판단 기준 SSOT: [실행 모드 라우팅 (solo-track vs 팀)](../../README.md#실행-모드-라우팅-solo-track-vs-팀). intake-as-issue / analyzer 가 이 기준으로 `solo` 를 추천하면 본 스킬로 진입한다 (analyzer 가 이미 이슈를 만든 경우 `issue_id` 를 받아 Step A.continue).

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
3. session_restore(project_key, compact=true)             # 광역 caveat (오리엔테이션 → compact)
4. issue_get(id=N, include_tasks=true, include_notes=true) # description + 모든 task + 모든 note (작업 대상 → 풀로드 유지)
5. history_for(entity_type="issue", entity_id=N, limit=30) # 이전 agent 들의 작업 흔적 (limit 명시)
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

session_restore 의 active_caveats 검토 후 즉시 기록:

```
note_add(issue_id=N, note_type="reference", author="agent", agent_id=<self>,
         summary="[RULE AUDIT] 광역 규칙 <N>건 검토",
         detail="<caveat 별 한 줄: 요약 → 적용함|해당없음|주의 관찰>")
```

active_caveats 가 0건이면 `summary="[RULE AUDIT] 광역 규칙 없음"` 으로 기록 (생략 불가).

검토 후 claim 가능 판정이면 → Step B 진입 (코드 작업).

---

#### Step A.new — Pre-work: 이슈 등록 + 점유

```
# 1) project_key 결정 (analyzer 절차)
Bash("git config --get remote.origin.url") → repo 이름
session_restore(compact=true) → 활성 프로젝트 매칭 → project_key 확정

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
3. 스킬 발동 시 즉시:
   ```
   note_add(issue_id=N, note_type="reference", author="agent",
            agent_id="main@<sess>-issue<N>",
            summary="[SKILL] <skill-name> — <호출|스킵>, <적절|불필요|필수였으나 누락>",
            detail="목적: ...\n결과: ...\n판단: ...")
   ```
   불필요 발동이라고 판단되면 "불필요" 로 표기.
4. 새 task 발견:
   ```
   task_insert_after(prev_id=<id>, title="...")
   ```
5. task 완료:
   ```
   task_update(id=<task_id>, status="finished",
               agent_id="main@<sess>-issue<N>")
   ```

### Step C — Demo Gate 자체 검증 및 피드백 작성 (필수)

다음 셋 모두 통과하고 스킬/하네스 평가 노트를 작성해야 Step D 진행:

```
task_list(issue_id=N, status="required")                    → 빈 배열인가
task_test_list(issue_id=N)                                  → 항목이 있으면 모두 checked 인가
Bash("git status --porcelain | awk '{print $2}'")           → 변경+신규 파일 목록 (untracked 포함)
```

**[EVALUATION] 피드백 기록 (의무)**:
데모 진입 전에 반드시 현재 실행 하네스, 스킬 사용 적절성, Engram 시스템 편의성을 평가하는 `[EVALUATION]` 노트를 `note_add(note_type="reference")`로 작성합니다.

```
note_add(issue_id=N, note_type="reference", author="agent", agent_id="main@<sess>-issue<N>",
         summary="[EVALUATION] <피드백 핵심 요약>",
         detail="하네스 평가: ...\n사용한 스킬 평가: ...\nEngram 사용 피드백: ...\n개선 제안: ...")
```

> ⚠️ `git diff --name-only HEAD` 대신 `git status --porcelain` 사용 — 신규(untracked) 파일은 git diff 에 나타나지 않아 문서 작성 이슈에서 false-fail 이 납니다.

**이슈 성격별 git 체크 기준**:

| 이슈 성격 | git 체크 |
|----------|---------|
| 코드 변경 | 결과 1개 이상 필수 |
| 문서 전용 (신규 .md/.yaml 추가) | 결과 1개 이상 필수 (신규 파일 실재 확인) |
| 설정/메타/분석만 | 선택적 — context note 로 대체 가능 |

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
         detail="확인 항목:\n- ...\n변경 파일:\n- <path> (이유)\n수동 확인:\n- <칸반 X 동작>\n남은 한계:\n- <있다면>\n증거:\n- git diff: <파일>\n- task_test: <pass/n/a>\n- evaluation_note: added\n스킬/룰: rules=<N>건 적용, skills=<M>건 발동 (<불필요 건수>건 불필요)\n불필요 스킬: <이름 목록 또는 없음>")

issue_release(id=N, agent_id="main@<sess>-issue<N>", transition_to="demo")
```

### Step D.5 — 리뷰 (서브에이전트 spawn 필수)

solo 라도 **작성자 != 리뷰어** 원칙을 지킨다. demo 진입 후 메인 에이전트가 직접 LGTM 하지 말고 **`engram-reviewer` 를 spawn** 해 독립 리뷰 패스를 받는다:

```
Agent(subagent_type='engram-orchestrator:engram-reviewer',
      prompt="issue_id=N 리뷰. project_key=<P>. demo 상태 이슈를 코드 레벨에서 검토하고 LGTM | CHANGES_REQUESTED 판정.")
```

- **LGTM** → reviewer 가 context note 기록 → Step E 진행, 사용자에게 "리뷰 통과, demo→finished 사용자 종결" 안내.
- **CHANGES_REQUESTED** → reviewer 가 caveat note + `issue_release(ready|working)` 로 환원. 메인은 그 피드백으로 **Step B 로 복귀**해 수정 후 다시 Step C~D.5.
- reviewer 는 절대 `finished` 로 전이하지 않는다(사용자 전용). 메인도 마찬가지.
- **UI 이슈 자동 커버**: 이슈가 UI 성격(레이아웃/모달/반응형 등 + 검증 URL)이면 engram-reviewer 가 내부에서 `ui-qa-reviewer` 를 spawn 해 실제 브라우저 검증까지 수행한다. solo 측 추가 작업 없음. 로그인이 필요하면 reviewer 가 사용자에게 로그인을 요청한다.

> 자기 자신(메인 컨텍스트)이 리뷰를 겸하지 않는다 — self-approve 금지. 이 spawn(engram-reviewer)이 solo 모드의 유일한 (그리고 필수) 서브에이전트 호출이다 (UI 이슈면 reviewer 가 ui-qa-reviewer 를 중첩 spawn).

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

메인 에이전트가 단일 actor 로 작업 단계 호출을 하므로 v0.4.0 Hybrid 의 **leader evidence 검증 안전망이 작업 단계엔 없다** (리뷰 단계는 Step D.5 의 `engram-reviewer` 가 독립 검증으로 복원). 작업 단계 보강:

1. 각 mcp 호출 직후 응답 JSON 의 핵심 필드(id, status, error)를 응답에 인용.
2. Step C 의 git diff 검증을 **반드시 실제 Bash 호출** 로 수행.
3. 사용자가 같은 대화 안에 있으니 거짓말은 사후 즉시 발견 가능 — 메인 컨텍스트의 자연스러운 검증.

## 금지

- `issue_update(status="finished" | "cancelled")` — 사용자 전용.
- `note_resolve` on 사용자 코멘트(`author="user"`) — 사용자가 직접 종결.
- `agent_id` 인자 누락 금지.
- Step C (Demo Gate) 생략 후 release(demo) 금지.
- [EVALUATION] 피드백 노트 생략 후 release(demo) 금지.
- task 가 어렵다고 status="cancelled" 우회 금지 — caveat + ready 환원으로 보고.
- **Step B 작업 중 발견·결정·참조 내용 `note_add` 생략 금지** — 새로운 발견/결정이 생길 때 즉시 기록. 작업 완료 후 몰아서 쓰는 것 금지.
- **required task 가 1개라도 남으면 `release(demo)` 절대 금지** — Step C 에서 `task_list(required)=[]` 확인 전 demo 진입 불가. 미완료 task 가 있으면 반드시 작업 완수 후 진행하거나 caveat + ready 환원.
- **메인이 직접 LGTM 금지 (self-approve 금지)** — Step D.5 의 `engram-reviewer` spawn 을 생략하고 메인 컨텍스트가 스스로 리뷰 통과 처리하면 안 된다. 작성자와 리뷰어는 다른 컨텍스트여야 한다.

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
review: engram-reviewer → LGTM (또는 CHANGES_REQUESTED → 수정 후 재리뷰)

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
   - Bash("git status --porcelain | awk '{print $2}'") = [src/x.ts, src/y.ts, tests/x.test.ts] ✓

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
