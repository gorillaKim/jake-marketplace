---
title: 플러그인 제작 가이드
aliases:
  - create-plugin
  - plugin-development-guide
  - 플러그인 제작 가이드
  - 플러그인 만들기
  - plugin-authoring
tags:
  - guide
  - plugin
  - claude-code
  - marketplace
  - development
created: 2026-03-27
updated: 2026-03-27
---

<!-- docsmith: auto-generated 2026-03-27 -->

# 플러그인 제작 가이드

jake-marketplace에 새 플러그인을 추가하는 방법을 설명합니다. 독자는 플러그인 개발자입니다.

> **최소 버전 요구사항**: Claude Code **1.0.33** 이상 필요합니다. `claude --version`으로 확인하세요.
> Task 도구는 버전 2.1.63에서 Agent로 이름이 변경되었으며, 기존 `Task()` 별칭도 지원됩니다.

---

## 디렉토리 구조

Claude Code 플러그인은 다음 레이아웃을 따릅니다.

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # 플러그인 매니페스트 (필수)
├── skills/
│   └── <skill-name>/
│       └── SKILL.md
├── agents/
│   └── <agent-name>.md
├── commands/                # 레거시 (지원됨)
├── hooks/
│   └── hooks.json
├── .mcp.json                # MCP 서버 설정
├── .lsp.json                # LSP 서버 설정
├── settings.json            # 플러그인 활성화 시 적용될 기본 설정
└── README.md
```

> **중요**: `commands/`, `agents/`, `skills/`, `hooks/`는 `.claude-plugin/` 안이 아닌 **플러그인 루트**에 위치해야 합니다. 안에 넣으면 인식되지 않습니다.

---

## plugin.json 작성

`.claude-plugin/plugin.json`은 플러그인의 유일한 필수 파일입니다.

```json
{
  "name": "my-plugin",
  "description": "플러그인 설명",
  "version": "1.0.0",
  "author": {
    "name": "이름",
    "email": "이메일"
  },
  "homepage": "https://...",
  "repository": "https://...",
  "license": "MIT"
}
```

### 필드 설명

| 필드 | 필수 | 타입 | 설명 |
|------|------|------|------|
| `name` | 필수 | string | 고유 식별자 (kebab-case). **스킬 네임스페이스 접두사**가 됨 |
| `description` | 선택 | string | 플러그인 설명 |
| `version` | 선택 | string | 시맨틱 버전 (예: `"1.0.0"`) |
| `author` | 선택 | object | `{ name, email }` |
| `homepage` | 선택 | string | 문서 URL |
| `repository` | 선택 | string | 소스코드 URL |
| `license` | 선택 | string | 라이센스 (예: `"MIT"`) |

---

## 스킬 네임스페이싱

`plugin.json`의 `name` 필드가 모든 스킬과 에이전트의 네임스페이스 접두사가 됩니다. 이름을 변경하면 모든 스킬의 호출 경로가 함께 변경되므로 신중하게 결정해야 합니다.

| 리소스 | 호출 방법 |
|--------|-----------|
| 스킬 | `/my-plugin:skill-name` |
| 에이전트 @-mention | `@agent-my-plugin:agent-name` |

예시: `name: "skill-doctor"` → `/skill-doctor:dashboard`, `/skill-doctor:diagnose`

---

## 플러그인 구성 요소

### settings.json

플러그인 활성화 시 적용될 기본 설정입니다. 현재 `agent` 키만 지원됩니다.

```json
{ "agent": "security-reviewer" }
```

### hooks/hooks.json

라이프사이클 훅을 정의합니다.

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "npm run lint:fix" }
        ]
      }
    ]
  }
}
```

### 플러그인 에이전트 보안 제한

플러그인 `agents/` 안에 정의된 에이전트는 보안상 다음 필드가 **무시**됩니다.

- `hooks`
- `mcpServers`
- `permissionMode`

이 기능이 필요하다면 사용자 레벨(`~/.claude/`) 또는 프로젝트 레벨(`.claude/`)에서 에이전트를 정의해야 합니다.

---

## 설치 및 로컬 테스트

```bash
# 개발 중 로컬 테스트
claude --plugin-dir ./my-plugin

# 다중 플러그인 동시 로드
claude --plugin-dir ./plugin-one --plugin-dir ./plugin-two

# 변경사항 적용 (재시작 불필요)
/reload-plugins
```

---

## jake-marketplace 등록

jake-marketplace에 플러그인을 추가하는 절차입니다.

### 1. 플러그인 폴더 생성

```
plugins/<plugin-name>/
```

### 2. `.claude-plugin/plugin.json` 작성

위의 [plugin.json 작성](#pluginjson-작성) 섹션을 참고합니다.

### 3. `skills/`, `agents/`, `hooks/` 구성

각 구성 요소를 플러그인 루트에 배치합니다.

### 4. `.claude-plugin/marketplace.json` 목록에 등록

마켓플레이스 루트의 `.claude-plugin/marketplace.json`에 플러그인을 추가합니다.

```json
{
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./plugins/my-plugin",
      "description": "플러그인 설명",
      "version": "1.0.0",
      "category": "developer-tools"
    }
  ]
}
```

---

## 설치 및 배포

```bash
# 마켓플레이스 등록
/plugin marketplace add gorillaProject/jake-marketplace

# 개별 플러그인 설치
/plugin install my-plugin@jake-plugins

# 업데이트
/plugin marketplace update
/plugin uninstall my-plugin
/plugin install my-plugin@jake-plugins

# 제거
/plugin uninstall my-plugin
```

마켓플레이스에서 설치된 플러그인은 `~/.claude/plugins/cache/`에 복사됩니다.

---

## 기존 플러그인 참고

| 플러그인 | 특징 |
|---------|------|
| `skill-doctor` | Hook+Agent 하이브리드, Python 스크립트, 자동 시그널 수집 |
| `gtm-tag` | 서브에이전트 파이프라인, 템플릿 기반 분석 |
| `obsidian-nexus` | MCP 연동, CLI 참조 문서 분리 |

---

## 관련 문서

- [[스킬 작성 가이드]]
- [[에이전트 작성 가이드]]
- [[마켓플레이스 운영 가이드]]
- [[설계 결정 기록]]
- [[plugin.json 스키마 레퍼런스]]
