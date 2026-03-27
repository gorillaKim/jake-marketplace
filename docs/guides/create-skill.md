---
title: 스킬 작성 가이드
aliases:
  - create-skill
  - skill-writing-guide
  - 스킬 작성 가이드
  - 스킬 만들기
  - SKILL.md 작성법
tags:
  - guide
  - skill
  - claude-code
  - plugin
  - frontmatter
  - skill-authoring
created: 2026-03-27
updated: 2026-03-27
---

<!-- docsmith: auto-generated 2026-03-27 -->

# 스킬 작성 가이드

Claude Code 스킬(`SKILL.md`)을 올바르게 작성하는 방법을 설명합니다. 독자는 플러그인 및 스킬 개발자입니다.

> **참고**: `skills/` 방식이 기존 `commands/` 방식보다 권장됩니다. 동명 충돌 시 skill이 command보다 우선합니다.

## 스킬이란

스킬은 사용자가 `/plugin-name:skill-name` 형태로 직접 트리거하거나, Claude가 자동으로 호출하는 자동화 단위입니다. `SKILL.md` 파일 하나로 정의됩니다.

## 디렉토리 구조

스킬은 세 가지 위치에 배치할 수 있습니다.

```
~/.claude/skills/<skill-name>/SKILL.md       # 개인 (모든 프로젝트)
.claude/skills/<skill-name>/SKILL.md         # 프로젝트 전용
<plugin>/skills/<skill-name>/SKILL.md        # 플러그인 내
```

스킬 폴더 내부 구조:

```
my-skill/
├── SKILL.md           # 필수 진입점
├── template.md        # 선택: 보조 템플릿
├── examples/          # 선택
└── scripts/           # 선택
```

플러그인 내 스킬은 자동으로 네임스페이스 접두사가 붙습니다 (예: `/plugin-name:skill-name`).

## Frontmatter 필드

```yaml
---
name: my-skill
description: 스킬 설명 (트리거 키워드, trigger-keyword, 한글트리거)
argument-hint: "[선택 인자]"
disable-model-invocation: false
user-invocable: true
allowed-tools:
  - Bash
  - Read
model: claude-sonnet-4-5
effort: medium
context: fork
agent: my-agent
hooks:
  - event: PostSkillRun
    command: echo "done"
paths:
  - "src/**/*.ts"
shell: bash
---
```

| 필드 | 필수 | 설명 |
|------|------|------|
| `name` | 권장 아님 | 소문자·숫자·하이픈, 최대 64자. 미지정 시 디렉토리명 사용. `/slash-command`명으로 사용됨 |
| `description` | 권장 | Claude 자동 호출 여부 결정에 사용. **트리거 키워드를 괄호 안에 포함 권장** |
| `argument-hint` | No | 자동완성 힌트. 예: `[issue-number]` |
| `disable-model-invocation` | No | `true`이면 수동 `/name`으로만 실행 가능. Claude 자동 호출 불가 |
| `user-invocable` | No | `false`이면 `/` 메뉴에서 숨김. Claude만 발동 가능 |
| `allowed-tools` | No | 권한 프롬프트 없이 사용 가능한 도구 목록 |
| `model` | No | 이 스킬 실행 시 사용할 모델 |
| `effort` | No | `low` / `medium` / `high` / `max` (Opus 4.6 전용) |
| `context` | No | `fork` 설정 시 격리된 서브에이전트에서 실행 |
| `agent` | No | `context: fork` 시 사용할 서브에이전트 타입 |
| `hooks` | No | 스킬 라이프사이클 훅 |
| `paths` | No | 특정 파일 패턴에서만 활성화되는 glob |
| `shell` | No | `bash`(기본) 또는 `powershell` |

## 발동 제어 매트릭스

| Frontmatter | 사용자 호출 | Claude 자동 호출 |
|---|---|---|
| (기본, 필드 없음) | 가능 | 가능 |
| `disable-model-invocation: true` | 가능 | 불가 |
| `user-invocable: false` | 불가 | 가능 |

## 스트링 치환 변수

스킬 본문에서 사용할 수 있는 내장 변수입니다.

| 변수 | 설명 |
|------|------|
| `$ARGUMENTS` | 호출 시 전달된 모든 인자 (전체 문자열) |
| `$ARGUMENTS[N]` | N번째 인자 (0부터 시작) |
| `$N` | `$ARGUMENTS[N]` 단축형 |
| `${CLAUDE_SESSION_ID}` | 현재 세션 ID |
| `${CLAUDE_SKILL_DIR}` | SKILL.md가 위치한 디렉토리 절대경로 |
| `${CLAUDE_PLUGIN_ROOT}` | 플러그인 루트 디렉토리 (플러그인 내 스킬만 사용 가능) |

## 동적 컨텍스트 주입

`` `!command` `` 문법으로 셸 명령 실행 결과를 스킬 실행 전 본문에 주입할 수 있습니다.

```yaml
---
name: pr-summary
context: fork
agent: Explore
---
현재 PR 변경사항:
- PR diff: `!gh pr diff`
- 변경된 파일: `!gh pr diff --name-only`
```

플러그인 내 스크립트를 활용하는 예시:

```markdown
현재 스킬 목록:
`!python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py list --format json`
```

## 필수 섹션 구성

모든 스킬은 다음 섹션을 포함하는 것을 권장합니다.

### 1. 실행 절차 섹션

```markdown
## 실행 절차

### 1. 첫 번째 단계

설명.

### 2. 두 번째 단계

CLI 명령 예시:

\```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py <command>
\```
```

- 절차는 `### 1.`, `### 2.` 번호로 명확하게 구분합니다.
- CLI 명령어는 반드시 코드 블록으로 감쌉니다.
- `${CLAUDE_PLUGIN_ROOT}` 또는 `${CLAUDE_SKILL_DIR}`로 내부 경로를 참조합니다.

### 2. 시그널 기록 섹션

skill-doctor의 자동 셀프힐링이 작동하려면 반드시 포함해야 합니다.

```markdown
## 시그널 기록

> **자동 수집 (Hook+Agent)**: 도구 실패, 사용자 메시지 등 raw 이벤트를 Hook이 수집하고,
> Stop 시 Claude가 유의미한 시그널만 판별하여 DB에 기록합니다.
> **수동 보조**: redo, manual_fix, clarify, blocked는 hook으로 감지하기 어려우므로,
> 발생 시 `/skill-doctor:record`로 수동 기록하면 데이터 품질이 향상됩니다.
```

### 3. 다음 단계 추천 섹션

AskUserQuestion 도구로 후속 액션을 제안합니다.

```markdown
## 다음 단계 추천

\```yaml
questions:
  - question: '작업이 완료되었습니다. 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: '옵션 A'
        description: '설명'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
\```
```

## AskUserQuestion 사용

사용자에게 구조화된 질문을 할 때 AskUserQuestion 도구를 사용합니다.

```yaml
questions:
  - question: '질문 내용'
    header: '섹션 헤더'
    options:
      - label: '선택지 라벨'
        description: '선택지 설명'
    multiSelect: false   # true면 복수 선택 가능
```

## 생성 체크리스트

- [ ] `skills/<name>/SKILL.md` 경로 확인
- [ ] frontmatter에 `name`, `description` 포함
- [ ] description에 트리거 키워드 괄호 포함
- [ ] 발동 제어 의도에 맞게 `disable-model-invocation` / `user-invocable` 설정
- [ ] 필요한 경우 `context: fork` + `agent` 지정
- [ ] 절차를 번호 매기기(`### 1.`, `### 2.`)로 명확하게 작성
- [ ] CLI 명령어는 코드 블록으로 감싸기
- [ ] `${CLAUDE_PLUGIN_ROOT}` 또는 `${CLAUDE_SKILL_DIR}`로 경로 참조
- [ ] **`## 시그널 기록` 섹션 포함** (skill-doctor 셀프힐링 필수)
- [ ] `## 다음 단계 추천` — AskUserQuestion으로 후속 액션 제안

## 실제 예시 참고

| 스킬 | 경로 | 특징 |
|------|------|------|
| skill-doctor:create | `plugins/skill-doctor/skills/create/SKILL.md` | AskUserQuestion 구조화 질문 |
| skill-doctor:record | `plugins/skill-doctor/skills/record/SKILL.md` | 시그널 타입별 분기 처리 |
| obsidian-nexus:onboard | `plugins/obsidian-nexus/skills/onboard/SKILL.md` | 에이전트 위임 패턴 |

## 관련 문서

- [[플러그인 제작 가이드]]
- [[에이전트 작성 가이드]]
- [[설계 결정 기록]]
- [[스킬 폴더 구조]]
