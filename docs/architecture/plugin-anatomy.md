---
title: 플러그인 해부도
aliases:
  - plugin-anatomy
  - 플러그인 해부도
  - 플러그인 구조
  - plugin-structure
tags:
  - architecture
  - plugin
  - claude-code
  - marketplace
  - reference
created: 2026-03-27
updated: 2026-03-27
---

<!-- docsmith: auto-generated 2026-03-27 -->

# 플러그인 해부도

jake-marketplace 플러그인의 디렉토리 구조와 각 구성 요소의 역할을 정의합니다.
플러그인 개발자가 새 플러그인을 작성할 때 참고하는 구조적 기준입니다.

## 플러그인 루트 구조

```
plugins/{name}/
├── .claude-plugin/
│   └── plugin.json          # 플러그인 메타데이터 (필수)
├── skills/
│   └── {skill-name}/
│       └── SKILL.md          # 스킬 정의 (Claude Code 프롬프트)
├── agents/
│   └── {agent-name}.md       # 에이전트 정의 (model/tools/프롬프트 포함)
├── hooks/
│   └── hooks.json            # Claude Code 이벤트 훅 정의
├── scripts/                  # 플러그인이 사용하는 Python/Shell 스크립트
├── templates/                # 문서·코드 템플릿
├── docs/                     # 플러그인 자체 문서
└── README.md
```

## 구성 요소별 역할

### `.claude-plugin/plugin.json` — 플러그인 메타데이터

마켓플레이스가 플러그인을 인식하는 진입점입니다.

```json
{
  "name": "plugin-name",
  "description": "플러그인 설명",
  "version": "0.1.0",
  "author": {
    "name": "jake",
    "email": "yhkim@madup.com"
  }
}
```

| 필드 | 필수 | 설명 |
|------|------|------|
| `name` | 필수 | 플러그인 식별자. 마켓플레이스 `plugins[]` 배열의 `name`과 일치해야 함 |
| `description` | 필수 | 플러그인 기능 요약 |
| `version` | 필수 | semver 형식 |
| `author` | 선택 | 작성자 정보 |

### `skills/{skill-name}/SKILL.md` — 스킬 정의

Claude Code가 `/plugin:skill-name` 명령으로 실행하는 프롬프트입니다.

**필수 frontmatter:**

```yaml
---
name: skill-name
description: 스킬 설명 (트리거 키워드를 괄호 안에 포함)
---
```

**권장 섹션 구조:**

```markdown
# 스킬 제목

## 실행 절차

### 1. 첫 번째 단계
### 2. 두 번째 단계

## 시그널 기록
```

`description`에는 트리거 키워드를 포함해야 Claude Code가 자동 감지로 스킬을 연결할 수 있습니다.
예: `description: 스킬 진단 (diagnose, 스킬 문제, skill-doctor)`

### `agents/{agent-name}.md` — 에이전트 정의

Claude Code `Agent` 도구로 스폰되는 서브에이전트 또는 팀 에이전트를 정의합니다.

**frontmatter 구조:**

```yaml
---
name: agent-name
description: 에이전트 역할 설명
model: haiku | sonnet | opus
tools:
  - Read
  - Bash
  - Glob
  - Grep
  - AskUserQuestion   # Team 에이전트만 포함
---
```

`AskUserQuestion` 도구 포함 여부가 Team 에이전트와 Sub 에이전트를 구분하는 핵심 기준입니다.
자세한 내용은 [[에이전트 파이프라인 패턴]]을 참고하세요.

### `hooks/hooks.json` — 훅 정의

Claude Code 이벤트에 반응하는 자동 실행 명령을 정의합니다.
자세한 내용은 [[훅 시스템]]을 참고하세요.

### `scripts/` — 보조 스크립트

플러그인이 훅이나 스킬에서 호출하는 외부 프로그램입니다.
skill-doctor의 경우 Python CLI(`cli.py`)와 시그널 수집기(`signal-collector.py`)가 여기에 위치합니다.

환경 변수 `$CLAUDE_PLUGIN_ROOT`가 설치된 플러그인의 루트 경로로 자동 설정됩니다.
스크립트 경로 참조 시 항상 이 변수를 사용합니다:

```bash
python3 "$CLAUDE_PLUGIN_ROOT/scripts/cli.py"
```

### `templates/` — 문서·코드 템플릿

스킬이나 에이전트가 생성하는 출력물의 기준 형식을 정의합니다.
obsidian-nexus 플러그인은 이 디렉토리에 카테고리별 문서 템플릿을 보관합니다.

## 실제 플러그인 비교

| 구성 요소 | skill-doctor | gtm-tag | obsidian-nexus |
|-----------|-------------|---------|----------------|
| skills/ | 9개 (record, diagnose, heal 등) | 4개 (init, sync, tag, doctor) | 5개 (librarian, add 등) |
| agents/ | 2개 (skill-doctor, skill-healer) | 3개 (analyzer, implementer, verifier) | 3개 (librarian, docsmith-analyzer, docsmith-writer) |
| hooks/ | hooks.json (6개 이벤트) | 없음 | 없음 |
| scripts/ | cli.py, signal-collector.py | 없음 | 없음 |
| templates/ | 없음 | 3개 | 8개 |

## 마켓플레이스 등록

최상위 `.claude-plugin/marketplace.json`에 플러그인을 등록합니다:

```json
{
  "plugins": [
    {
      "name": "plugin-name",
      "source": "./plugins/plugin-name",
      "description": "설명",
      "version": "0.1.0",
      "category": "developer-tools"
    }
  ]
}
```

`source` 경로는 `marketplace.json`을 기준으로 한 상대 경로입니다.

## 관련 문서

- [[훅 시스템]]
- [[에이전트 파이프라인 패턴]]
