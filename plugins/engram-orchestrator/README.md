# engram-orchestrator

Engram MCP 위에서 동작하는 **이슈 분석 / 리딩 / 처리** 에이전트 오케스트레이션 플러그인.

## 무엇을 하는가

```
[사용자 작업 요청]
        │
        ▼
[intake-as-issue]   ── "이슈로 만들어 처리할까요?" 확인
        │ yes
        ▼
[engram-analyzer]   ── 작업을 여러 이슈로 분할
                      · 적합 에픽 매핑/생성
                      · task 다수 등록
                      · blocks 의존성 설정
                      · required → ready 까지만 전이
        │
        ▼
[engram-leader]     ── 활성 스프린트의 ready 이슈 큐 조회
                      · 각 이슈에 engram-worker spawn
                      · stalled_issues 로 정체 감시 (기본 10분)
                      · caveat 노트 + 사용자 알림
        │
        ▼
[engram-worker]     ── 단일 이슈 처리 (ready → working → demo)
[work-journaling]      · 작업 전 comment 10개 검토 + 질문 답변
                       · 발견/결정/블로커는 note_add
                       · demo 직전 검토 가이드(note context)
        │
        ▼
[사용자 검토]        ── demo → finished (사용자만, agent 금지)
```

## 제공

- **Agents** (3)
  - `engram-analyzer` — 작업 분할 / 이슈/태스크/blocks 등록
  - `engram-leader` — ready 큐 분배 + working 정체 감시
  - `engram-worker` — 단일 이슈 처리 (ready → working → demo)
- **Skills** (2)
  - `intake-as-issue` — 사용자 작업 요청을 이슈로 등록할지 게이트
  - `work-journaling` — 코멘트 답변 / 노트 기록 / 상태 전이 표준

## 전제 의존성

이 플러그인은 [Engram](../../../) MCP 서버에 의존한다. 먼저 다음을 준비해야 한다:

1. **Engram 바이너리 빌드 + 설치**
   ```bash
   git clone <engram-repo>
   cd engram
   cargo install --path crates/engram-mcp --bin engram-mcp
   cargo install --path crates/engram-cli  --bin engram
   ```

2. **MCP 서버 등록** — `~/.claude/settings.json`:
   ```json
   {
     "mcpServers": {
       "engram": {
         "command": "engram-mcp",
         "type": "stdio"
       }
     }
   }
   ```

3. **이 플러그인 활성화** — `~/.claude/settings.json`:
   ```json
   {
     "enabledPlugins": {
       "engram-orchestrator@jake-plugins": true
     }
   }
   ```

## 사용 예

### 자동 흐름

사용자가 작업을 요청한다:

> "결제 영수증을 PDF 로 다운받을 수 있게 만들어줘"

→ `intake-as-issue` 가 트리거 → "이슈로 만들어 처리할까요?" → 예 →
`engram-analyzer` 가 이슈 2~3건으로 분할 + 의존성 설정 + ready 상태로 등록 →
사용자가 `engram-leader` 호출 → 각 이슈가 `engram-worker` 로 spawn → 차례로 demo 도달 →
사용자가 칸반에서 demo → finished.

### 단일 이슈 직접 처리

```
사용자: "이슈 #142 작업해줘"
→ Agent(subagent_type=engram-worker, prompt='Engram issue #142 처리. work-journaling 따르기.')
```

### 정체 모니터링

```
사용자: "지금 막힌 이슈 있어?"
→ Agent(subagent_type=engram-leader, prompt='project_key=xxx, 정체 감시만 한 사이클')
```

## 상태 전이 가드 (Demo Gate)

모든 에이전트는 다음을 **절대 호출하지 않는다**:

- `issue_update(status="finished")` — 사용자 검토 완료 신호
- `issue_update(status="cancelled")` — 사용자 작업 포기 신호

이 게이트는 코드로 강제되지 않고 **agent 프롬프트 + `.claude/rules/agent-demo-gate.md`** (engram 레포)
로 관리된다. 위반 시 `history.changed_by='agent'` 로 추적되어 사후 감사 가능.

## 함께 자주 쓰는 도구

- Engram MCP `stalled_issues` — leader 의 정체 감지 단일 호출 (이 플러그인 0.1.0 과 함께 추가)
- Engram MCP `note_type="comment"` — 사용자↔에이전트 대화 (CommentSection UI 와 정합)

## 버전

- 0.1.0 — 초기 릴리스 (analyzer + leader + worker + intake + work-journaling)
