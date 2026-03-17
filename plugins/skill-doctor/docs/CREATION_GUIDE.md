# Claude Code 스킬/에이전트/플러그인 생성 가이드

> skill-doctor:create 스킬이 참조하는 표준 명세 문서.
> 출처: https://code.claude.com/docs/en/

---

## 1. 스킬 (SKILL.md)

### 디렉토리 구조
```
skills/<skill-name>/
├── SKILL.md           # 필수 진입점
├── template.md        # 선택: 보조 파일
├── examples/          # 선택
└── scripts/           # 선택
```

### Frontmatter 필드

| 필드 | 필수 | 타입 | 설명 |
|------|------|------|------|
| `name` | 아니오 | string | 소문자+숫자+하이픈, 최대 64자. 미지정 시 디렉토리명 사용 |
| `description` | 권장 | string | 스킬 설명. Claude가 자동 호출 판단에 사용. 미지정 시 첫 번째 문단 사용 |
| `argument-hint` | 아니오 | string | 자동완성 시 표시. 예: `[issue-number]` |
| `disable-model-invocation` | 아니오 | boolean | `true` = Claude 자동 호출 방지. 기본값: `false` |
| `user-invocable` | 아니오 | boolean | `false` = `/` 메뉴에서 숨김 (Claude만 호출 가능). 기본값: `true` |
| `allowed-tools` | 아니오 | string/list | 권한 프롬프트 없이 사용 가능한 도구 |
| `model` | 아니오 | string | 스킬 활성 시 사용할 모델 |
| `context` | 아니오 | string | `fork` = 격리된 서브에이전트 컨텍스트에서 실행 |
| `agent` | 아니오 | string | `context: fork` 시 사용할 에이전트 이름 |
| `hooks` | 아니오 | object | 스킬 라이프사이클 스코프 훅 |

### 사용 가능한 변수

| 변수 | 설명 |
|------|------|
| `$ARGUMENTS` | 호출 시 전달된 모든 인자 |
| `$ARGUMENTS[N]` / `$N` | N번째 인자 (0부터) |
| `${CLAUDE_SESSION_ID}` | 현재 세션 ID |
| `${CLAUDE_SKILL_DIR}` | SKILL.md가 위치한 디렉토리 |
| `${CLAUDE_PLUGIN_ROOT}` | 플러그인 루트 디렉토리 (플러그인 내 스킬만) |

### 호출 제어

| 설정 | 사용자 호출 | Claude 호출 | 컨텍스트 로드 |
|------|------------|------------|--------------|
| (기본) | O | O | description 항상, 전체 내용은 호출 시 |
| `disable-model-invocation: true` | O | X | 컨텍스트에 미포함 |
| `user-invocable: false` | X | O | description 항상 |

### 동적 컨텍스트
`` `!command` `` 문법으로 셸 명령 실행 결과를 스킬 내용에 주입 가능.

### 작성 모범 사례
- description에 트리거 키워드를 괄호로 포함: `(스킬진단, diagnose, health)`
- 절차는 번호 매기기로 명확하게
- CLI 명령어는 코드 블록으로 감싸기
- `${CLAUDE_PLUGIN_ROOT}` 사용하여 플러그인 내부 경로 참조

---

## 2. 에이전트 (agent .md)

### 파일 위치
```
agents/<agent-name>.md
```

### 발견 우선순위

| 위치 | 우선순위 |
|------|---------|
| `--agents` CLI 플래그 | 1 (최고) |
| `.claude/agents/` (프로젝트) | 2 |
| `~/.claude/agents/` (사용자) | 3 |
| 플러그인 `agents/` | 4 (최저) |

### Frontmatter 필드

| 필드 | 필수 | 타입 | 설명 |
|------|------|------|------|
| `name` | **예** | string | 고유 식별자. 소문자+하이픈 |
| `description` | **예** | string | Claude가 위임 판단에 사용 |
| `tools` | 아니오 | string/list | 사용 가능 도구. 미지정 시 전체 상속. `Agent(name)` 형태로 특정 서브에이전트만 허용 가능 |
| `disallowedTools` | 아니오 | string/list | 차단할 도구 |
| `model` | 아니오 | string | `sonnet`, `opus`, `haiku`, 전체 모델ID, 또는 `inherit`. 기본값: `inherit` |
| `permissionMode` | 아니오 | string | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | 아니오 | integer | 최대 에이전틱 턴 수 |
| `skills` | 아니오 | list | 시작 시 프리로드할 스킬 (전체 내용 주입) |
| `mcpServers` | 아니오 | list/object | MCP 서버 정의 |
| `hooks` | 아니오 | object | 라이프사이클 훅 |
| `memory` | 아니오 | string | `user`, `project`, 또는 `local` |
| `background` | 아니오 | boolean | `true` = 백그라운드 실행. 기본값: `false` |
| `isolation` | 아니오 | string | `worktree` = 격리된 git worktree에서 실행 |

### 플러그인 에이전트 제약
보안상 무시되는 필드: `hooks`, `mcpServers`, `permissionMode`

### 메모리 스코프

| 스코프 | 저장 경로 |
|--------|----------|
| `user` | `~/.claude/agent-memory/<agent-name>/` |
| `project` | `.claude/agent-memory/<agent-name>/` |
| `local` | `.claude/agent-memory-local/<agent-name>/` |

### 작성 모범 사례
- description은 "언제 이 에이전트에 위임해야 하는지" 명확히
- tools는 최소 권한 원칙: 필요한 도구만 명시
- model은 작업 복잡도에 맞게 선택 (haiku: 경량, sonnet: 표준, opus: 복잡)

---

## 3. 규칙 (rules/)

### 파일 위치
```
rules/<rule-name>.md
```
하위 디렉토리 재귀 탐색 지원.

### Frontmatter 필드

| 필드 | 필수 | 타입 | 설명 |
|------|------|------|------|
| `paths` | 아니오 | list of strings | glob 패턴. 지정 시 매칭 파일 작업할 때만 로드. 미지정 시 세션 시작 시 무조건 로드 |

### 로드 방식
- `paths` **없음**: 세션 시작 시 무조건 로드 (CLAUDE.md와 동일 우선순위)
- `paths` **있음**: Claude가 매칭 파일을 읽을 때 조건부 로드

### 예시
```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API 개발 규칙
- 모든 엔드포인트에 에러 핸들링 필수
```

### 작성 모범 사례
- 파일 하나에 주제 하나
- 파일명으로 내용을 설명: `testing.md`, `api-design.md`
- 간결하게: 규칙은 매 세션 로드되므로 토큰 절약

---

## 4. 플러그인 구조

### 디렉토리 레이아웃
```
plugin-root/
├── .claude-plugin/           # 매니페스트만 여기에
│   └── plugin.json
├── agents/                   # 에이전트 .md 파일
├── skills/                   # 스킬 (각 <name>/SKILL.md)
│   └── skill-name/
│       └── SKILL.md
├── rules/                    # 자동 로드 규칙
├── hooks/
│   └── hooks.json
├── scripts/                  # 유틸리티 스크립트
├── docs/                     # 문서
├── settings.json             # 기본 설정 (`agent` 키만 지원)
├── .mcp.json                 # MCP 서버 정의
└── .lsp.json                 # LSP 서버 설정
```

> **주의**: `agents/`, `skills/`, `rules/`, `hooks/`는 플러그인 루트에 위치. `.claude-plugin/` 안이 아님.

### plugin.json 스키마

**필수 필드:**

| 필드 | 타입 | 설명 |
|------|------|------|
| `name` | string | 고유 식별자 (kebab-case). 스킬 네임스페이스 접두사 |

**메타데이터 (선택):**

| 필드 | 타입 | 설명 |
|------|------|------|
| `version` | string | 시맨틱 버전 (예: `"1.0.0"`) |
| `description` | string | 플러그인 설명 |
| `author` | object | `{ name, email, url }` |
| `homepage` | string | 문서 URL |
| `repository` | string | 소스코드 URL |
| `license` | string | 라이센스 (예: `"MIT"`) |
| `keywords` | array | 검색 태그 |

**컴포넌트 경로 (선택, 기본 경로를 보충):**

| 필드 | 타입 | 설명 |
|------|------|------|
| `commands` | string/array | 추가 커맨드 파일/디렉토리 |
| `agents` | string/array | 추가 에이전트 파일 |
| `skills` | string/array | 추가 스킬 디렉토리 |
| `hooks` | string/array/object | 훅 설정 |
| `mcpServers` | string/array/object | MCP 설정 |

### 네임스페이싱
플러그인 스킬은 항상 `/plugin-name:skill-name` 형태로 네임스페이싱.
`plugin.json`의 `name`을 변경하면 네임스페이스도 변경.

### 캐싱
마켓플레이스 설치 플러그인은 `~/.claude/plugins/cache/`에 복사됨.
플러그인 루트 외부 경로 접근 불가 — 필요 시 플러그인 내부에 심링크.

### 설치 스코프

| 스코프 | 설정 파일 | 용도 |
|--------|----------|------|
| `user` | `~/.claude/settings.json` | 개인, 기본값 |
| `project` | `.claude/settings.json` | 팀 공유, VCS 포함 |
| `local` | `.claude/settings.local.json` | 프로젝트별, gitignore |

---

## 5. 생성 시 체크리스트

### 스킬 생성 체크리스트
- [ ] `skills/<name>/SKILL.md` 경로 확인
- [ ] frontmatter에 `name`, `description` 포함
- [ ] description에 트리거 키워드 괄호 포함
- [ ] `${CLAUDE_PLUGIN_ROOT}` 또는 `${CLAUDE_SKILL_DIR}` 사용하여 경로 참조
- [ ] 절차를 번호 매기기로 명확하게 작성
- [ ] CLI 명령어는 코드 블록으로 감싸기

### 에이전트 생성 체크리스트
- [ ] `agents/<name>.md` 경로 확인
- [ ] frontmatter에 `name`, `description` **필수** 포함
- [ ] `tools` 최소 권한 원칙 적용
- [ ] `model` 작업 복잡도에 맞게 선택
- [ ] 플러그인 에이전트는 `hooks`, `mcpServers`, `permissionMode` 사용 불가

### 규칙 생성 체크리스트
- [ ] `rules/<name>.md` 경로 확인
- [ ] 파일당 주제 하나
- [ ] 조건부 로드 필요 시 `paths` frontmatter 사용
- [ ] 간결하게 작성 (매 세션 로드됨)
