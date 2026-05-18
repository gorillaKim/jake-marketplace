# engram-orchestrator

Engram MCP 위에서 동작하는 **이슈 분석 / 리딩 / 처리** 에이전트 오케스트레이션 플러그인.

## 무엇을 하는가

```
[사용자 작업 요청]
        │
        ▼
[intake-as-issue]   ── "이슈로 만들어 처리할까요?" 확인 (다단계 작업만 트리거)
        │ yes
        ▼
[engram-analyzer]   ── 작업을 여러 이슈로 분할
                      · 적합 에픽 매핑/생성
                      · task 다수 등록
                      · blocks 의존성 설정
                      · required → ready 까지만 전이
                      · agent_id 의무
        │
        ▼
[engram-leader]     ── 활성 스프린트의 ready 이슈 큐 조회
                      · agent_id 명시적 주입 후 worker spawn
                      · stalled_issues + AskUserQuestion 으로 release/handoff 액션
                      · active_workers 인식해 중복 spawn 방지
        │
        ▼
[engram-worker]     ── 단일 이슈 처리 (issue_claim → working → issue_release(demo))
[work-journaling]      · Step 0: 코멘트/caveat 검토 (mcp 첫 호출)
                       · Step 1: 컨텍스트 적재
                       · Step 2: issue_claim (CAS 점유)
                       · Step 3: task 진행
                       · Step 4: Demo gate (task finished + test check + git diff)
                       · Step 5: 검토 가이드 note + issue_release(transition_to="demo")
                       · Step 6: 자기 claim 안전 회수 + session_end
        │
        ▼
[사용자 검토]        ── demo → finished (사용자만, agent 금지)
```

## 제공

- **Agents** (3) — `tools` 필드는 명시 나열 (Claude Code 가 와일드카드 미지원).
  - `engram-analyzer` — 작업 분할 / 이슈·태스크·blocks 등록 (MCP create/update + Bash)
  - `engram-leader` — ready 큐 분배 + 정체 감시 + 사용자 액션 (MCP read + AskUserQuestion + Agent)
  - `engram-worker` — 단일 이슈 처리 (MCP 전체 + claim/release + Read/Write/Edit/Bash/Grep/Glob)
- **Skills** (2)
  - `intake-as-issue` — 다단계 작업 요청만 이슈화 게이트
  - `work-journaling` — Step 0~6 표준 절차 (claim/release + agent_id 의무 + anti-hallucination 인용 의무)

## 전제 의존성

이 플러그인은 [Engram](../../../) MCP **v0.3 이상** 에 의존한다 (issue_claim/issue_release/agent_id/history_* 활용).

### 옵션 A — Engram 데스크톱 앱 (권장, HTTP)

```bash
claude mcp add --scope user --transport http engram http://127.0.0.1:3456/mcp
```

또는 `~/.claude.json` 의 `mcpServers` 에 직접 추가:

```json
{
  "mcpServers": {
    "engram": {
      "type": "http",
      "url": "http://127.0.0.1:3456/mcp"
    }
  }
}
```

> ⚠️ Claude Code CLI 인식 위치는 `~/.claude.json` 의 `mcpServers`.
> `~/.claude/settings.json` 의 `mcpServers` 는 무시되니 혼동 주의.

### 옵션 B — stdio 바이너리 직접 빌드

```bash
git clone <engram-repo>
cd engram
cargo install --path crates/engram-mcp --bin engram-mcp
```

### 플러그인 활성화

`~/.claude/settings.json`:
```json
{
  "enabledPlugins": {
    "engram-orchestrator@jake-plugins": true
  }
}
```

설정 변경 후 **Claude Code 재시작 필요**.

## Use Cases

이 플러그인이 지원하는 표준 시나리오들. 멀티 에이전트 병렬 운영을 가정하지만 단일 에이전트 환경에서도 동일하게 동작한다.

---

### UC1 — 사용자 요청을 이슈로 등록 (Intake → Analyzer)

**상황**: 사용자가 자연어로 비정형 작업 요청. 다단계 변경이 명백한 경우.

> "결제 영수증을 PDF 로 다운받을 수 있게 만들어줘"

**흐름**:

1. `intake-as-issue` 자동 트리거 → `AskUserQuestion("이슈로 만들어 처리할까요?")` 사용자 확인.
2. 예 → `engram-analyzer` spawn (`engram-analyzer@<sess>` agent_id 주입).
3. analyzer 가 적합 에픽 찾거나 생성 → 이슈 2~3건 분할 (`issue_create` + `sprint_id`) → `task_create` 등록 → `issue_link(blocks)` 의존성 → `note_add(decision)` → 모든 신규 이슈 `issue_update(status="ready", agent_id=...)` 전이.
4. 호출자에게 `epic_id, issue_ids[]` 보고.

**다음 단계**:

```
사용자: "방금 만든 #128/#129/#130 처리해줘"
→ engram-leader 호출 (UC3 으로 이어짐)
```

> ❗ 단발성 편집 / 단순 조회 / "그냥 해줘" 명시 시 intake 게이트가 트리거 안 됨 → 곧바로 처리.

---

### UC2 — 단일 이슈 직접 처리 (한 워커가 한 이슈)

**상황**: 이미 등록된 이슈 1개를 처리하려고 사용자가 명시.

```
사용자: "이슈 #142 작업해줘"

→ Agent(
    subagent_type='engram-orchestrator:engram-worker',
    prompt=(
      'Engram issue #142 처리.\n'
      'project_key=jake-marketplace\n'
      'agent_id=claude-opus@a4b2c8-issue142\n'
      'work-journaling 스킬 Step 0~6 따르세요.'
    )
  )
```

**worker 의 Step 0~6**:

| Step | 호출 | 효과 |
|------|------|------|
| 0 | `note_list(comment/caveat)` | 코멘트 검토 + 질문 답변 |
| 1 | `session_restore` + `issue_get` | 컨텍스트 + 광역 caveat 확인 |
| 2 | `issue_claim(142, agent_id)` | **CAS 점유** → working |
| 3 | `task_next` 루프 + `task_update(finished, agent_id)` | 실제 작업 |
| 4 | task/test/diff 자체 검증 | Demo gate |
| 5 | `note_add(context)` + `issue_release(transition_to="demo")` | ownership 해제 + 전이 |
| 6 | 자기 claim 안전 회수 + `session_end` | 좀비 예방 |

이후 사용자가 데스크톱 칸반에서 `demo → finished` 로 종결.

---

### UC3 — 여러 이슈 동시 병렬 (단일 모델 N 워커)

**상황**: ready 큐에 이슈가 여러 개. claude 만으로 동시 처리.

```
사용자: "ready 큐 비워줘"

→ Agent(
    subagent_type='engram-orchestrator:engram-leader',
    prompt='project_key=jake-marketplace. ready 큐 분배 한 사이클.'
  )
```

**leader 동작**:

1. `sprint_current()` + `issue_list(status="ready")` + `my_blocked_issues()` 조회.
2. `session_restore.active_workers` 로 이미 점유 중인 이슈 식별 → 중복 spawn 방지.
3. blocked / 점유 중 이슈 제외하고 N 개 선택. 각각:

   ```
   agent_id = f"claude-opus@{sessionShort}-issue{issue_id}"
   Agent(
     subagent_type='engram-orchestrator:engram-worker',
     prompt=f'Engram issue #{issue_id}. agent_id={agent_id}. work-journaling 따라.'
   )
   ```

4. **한 응답 안에서 병렬 spawn**. 단, description 키워드 매칭으로 동일 파일/모듈 가능성이 높은 이슈는 순차로.
5. 각 워커가 `issue_claim` CAS 로 점유. **같은 이슈에 두 워커가 못 들어옴** — 두 번째 claim 은 `"already held by another agent"` 거부.

**병렬 안전성 보장**: `issue_claim` CAS + leader 의 `active_workers` 인식 + 파일 충돌 휴리스틱.

---

### UC4 — 멀티 LLM 라우팅 (claude + codex + gemini)

**상황**: 모델별 강점에 맞춰 분배. 예: claude=깊은 리팩터링, codex=테스트 작성, gemini=빠른 프로토타입.

이 플러그인 자체는 Claude Code 의 `Agent` 만 spawn. **codex/gemini 는 별도 CLI (omc-teams, /ccg 등) 와 결합**.

leader 가 issue description 의 키워드/tag 로 모델 선택:

```
# leader 가 issue #N 의 description 검토 후 분기

if "[test]" 또는 "테스트" in description:
  Bash("omc team 1:codex 'Engram #N. agent_id=codex-gpt5@<sess>-issueN. work-journaling 따라.'")

elif "[prototype]" 또는 "프로토타입" in description:
  Bash("omc team 1:gemini 'Engram #N. agent_id=gemini-2.5@<sess>-issueN. work-journaling 따라.'")

else:
  Agent(
    subagent_type='engram-orchestrator:engram-worker',
    prompt='Engram #N. agent_id=claude-opus@<sess>-issueN. work-journaling 따라.'
  )
```

**공통 규약**: 모든 모델의 워커가 동일한 `work-journaling Step 0~6` + `issue_claim`/`issue_release` 사용. `agent_id` 만 모델별로 달라 `history_by_agent` 로 모델별 활동량 추적 가능.

```
사용자 회고: "어제 codex 가 처리한 이슈만 보여줘"
→ history_by_agent(agent_id="codex-gpt5@*")
```

> ⚠️ engram MCP 에 `agent_register` / capability tag 가 없어서, 라우팅 룰은 leader 측 휴리스틱.

---

### UC5 — 광역 규칙 공지 (project / sprint / epic scope caveat)

**상황**: "결제 모듈 손대지 마", "마이그레이션 직전이라 schema 변경 금지" 같은 광역 규칙.

사용자가 직접 호출:

```
note_add(
  scope="project",
  project_key="jake-marketplace",
  note_type="caveat",
  author="user",
  agent_id="user",
  summary="결제 모듈 코드 변경은 사전 승인 필요",
  detail="2주간 마이그레이션 진행 중. src/payment/** 수정 시 #PR 댓글로 사전 확인."
)
```

**전파**: 어느 워커가 어느 이슈를 잡든 Step 1 의 `session_restore(project_key)` 응답에 `active_caveats[]` 로 자동 노출 → 워커가 검토 후 위반 시 caveat 노트 + 작업 보류.

**스프린트/에픽 단위**:

```
note_add(scope="sprint", scope_target_id=<sprint_id>, ...)
note_add(scope="epic", scope_target_id=<epic_id>, ...)
```

**해제**: `note_resolve(<note_id>, agent_id="user")` — 사용자만.

---

### UC6 — 정체 이슈 회수 (stalled → release / handoff / force)

**상황**: 한 워커가 죽거나 느려져 working 상태 N 분 이상 정체. 좀비 lease.

```
사용자: "지금 막힌 이슈 있어?"

→ Agent(subagent_type='engram-orchestrator:engram-leader',
        prompt='project_key=jake-marketplace. 정체 감시.')
```

**leader 동작**:

1. `stalled_issues({project_key, threshold_minutes: 10})` 호출.
2. 정체 이슈마다:
   - 중복 caveat 확인 → 없으면 `note_add(caveat, agent_id=engram-leader@...)`.
   - `history_by_agent(agent_id=<해당 워커>)` 로 진짜 죽었는지 다른 데서 일하는지 점검.
3. **`AskUserQuestion`** 으로 사용자 액션:

   ```
   "#125 'X' 가 14분 정체 중. 점유 워커: codex-gpt5@xxx. 어떻게 처리할까요?"
     - release (ready 환원)
     - handoff (새 워커로 재시도)
     - 그대로 두기
   ```

4. **release**: `issue_release(125, agent_id=<해당 워커>, transition_to="ready")`. 
   - 권한 거부 응답이면 `issue_release(..., force=true, agent_id=engram-leader@...)` 로 강제 회수. audit 은 leader agent_id 로 남음.
5. **handoff**: 위 release → 새 agent_id 로 다른 모델 worker spawn (UC4 와 결합 가능).

**지속 감시**: `/loop 10m /engram-orchestrator:engram-leader project_key=xxx` 와 결합하면 데스크톱 알림 없이도 정체 자동 발견.

---

### UC7 — 사후 활동 추적 / 데일리 다이제스트

**상황**: 어제 / 지난 1시간 동안 누가 무엇을 했는지 한눈에. 멀티 LLM 환경의 디버깅/조정 핵심.

```
# 1) 크로스 엔티티 최근 변경 (issue 전이 + task 완료 + note 추가)
history_recent({since_minutes: 1440, limit: 100})

# 2) 특정 에이전트만 필터
history_by_agent({agent_id: "claude-opus@a4b2c8-issue142", limit: 50})

# 3) 한 이슈의 전체 라이프사이클 (시간순)
history_for({entity_type: "issue", entity_id: 128})
```

**활용 패턴**:

| 시점 | 호출 | 가치 |
|------|------|------|
| 매일 아침 점검 | `history_recent(since_minutes=1440)` | 어제 demo 진입 / ready 환원 / caveat 발생 요약 |
| 모델별 활동량 비교 | `history_by_agent(claude-opus@*)`, `(codex-gpt5@*)`, `(gemini-2.5@*)` | 어느 모델이 가장 많은 작업 처리했는지 |
| 이슈 사후 감사 | `history_for(issue, N)` | claim → working → demo release 전체 흐름 + 누가 했는지 |
| 사고 조사 | `history_for(issue, N)` 후 의심 transition 의 `changed_by` 확인 | 누가 언제 잘못된 전이 시도했는지 |

> ⚠️ `agent_id` 명명 규칙 (`<model>@<sess>-issue<id>`) 을 지키면 history 분석이 비로소 의미를 가진다. agent_id 누락 시 `changed_by="agent"` 로 통일되어 추적 불가.

---

## 핵심 안전 장치 (v0.3.0)

### Claim/Release 패턴

- worker Step 2: `issue_claim(id, agent_id)` — CAS 점유. 두 워커가 같은 이슈 동시에 못 잡음.
- worker Step 5: `issue_release(id, agent_id, transition_to="demo")` — ownership 해제 + 전이 동시.
- worker Step 6 (안전망): 종료 직전 자기 claim 이 남아 있으면 `transition_to="ready"` 로 자동 release.

### agent_id 의무

모든 변경 호출에 `<model>@<session>-issue<id>` 형식 식별자 포함.
→ `history_by_agent` / `history_for` / `history_recent` 가 의미 있게 동작.

### Demo Gate (자체 검증)

worker Step 4: task finished + test check + git diff 1개 이상이 통과해야 demo 전이.
미통과 시 caveat + ready 환원.

### Stalled 처리 (leader)

`stalled_issues` 발견 시 `AskUserQuestion` 으로 release/handoff/그대로 액션 받아 처리.
engram 의 lease 갱신 미지원을 사용자 승인 + leader 의 `issue_release` 호출로 우회.

## 상태 전이 가드 (Demo Gate)

모든 에이전트는 다음을 **절대 호출하지 않는다**:

- `issue_update(status="finished")` — 사용자 검토 완료 신호
- `issue_update(status="cancelled")` — 사용자 작업 포기 신호

이 게이트는 코드로 강제되지 않고 **agent 프롬프트 + work-journaling Step 4 자체 검증** 으로 관리된다.
위반은 `history_by_agent` 로 추적되어 사후 감사 가능.

## Anti-Hallucination 규칙

모든 agent/스킬은 mcp 호출 직후 응답의 핵심 필드(id, status, assigned_agent, error)를 본인 응답에 인용해야 한다.
호출 없이 ID 발명/placeholder 보고 금지.

## 알려진 한계 (멀티 에이전트 병렬 시나리오)

engram MCP v0.3 기준 현재 한계:

- **task 레벨 claim 없음**: 한 이슈 안 N task 를 여러 agent 가 동시 처리 시 race. 회피책: leader 의 분배 단위를 이슈로 강제 (이 플러그인 기본 동작).
- **lease 자동 만료 없음**: 죽은 워커가 잡은 이슈는 stalled_issues 발견 + 사용자 승인 후 leader 가 release. 자동 회수는 워커 Step 6 의 자기 회수 안전망에 의존.
- **push 알림 없음**: stalled/status_change 이벤트가 외부로 push 되지 않아 leader 가 polling. `/loop` 와 결합 권장.
- **project_create MCP 없음**: 새 프로젝트는 데스크톱 UI 에서 먼저 생성해야 함.

위 한계는 engram 측에 SSE / task_claim_next / issue_renew 가 들어오면 해소되며,
플러그인 측 후속 업데이트로 따라간다.

## 함께 자주 쓰는 도구

- Engram MCP `stalled_issues` — leader 의 정체 감지 단일 호출
- Engram MCP `history_recent / history_by_agent / history_for` — 멀티 에이전트 사후 추적
- Engram MCP `note_type="comment"` — 사용자 ↔ 에이전트 대화 (CommentSection UI 와 정합)

## 버전

- **0.3.0** — issue_claim/issue_release 패턴 채택 (Step 2/5), agent_id 명명 규칙 + 의무 주입, leader 의 stalled AskUserQuestion 액션화 (release/handoff), worker Step 6 자기 claim 안전 회수, history_* 도구 활용.
- 0.2.0 — tools 와일드카드 → 명시 나열, work-journaling Step 0~6, demo gate 자체 검증, anti-hallucination 인용 의무, project_key 결정 절차, intake 트리거 게이트 강화, README HTTP 우선.
- 0.1.0 — 초기 릴리스.
