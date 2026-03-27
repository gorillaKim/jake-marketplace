---
title: 에이전트 작성 가이드
aliases:
  - create-agent
  - agent-writing-guide
  - 에이전트 작성 가이드
  - 에이전트 만들기
  - subagent-guide
tags:
  - guide
  - agent
  - subagent
  - claude-code
  - plugin
  - frontmatter
created: 2026-03-27
updated: 2026-03-27
---

<!-- docsmith: auto-generated 2026-03-27 -->

# 에이전트 작성 가이드

Claude Code 서브에이전트(agent.md)를 올바르게 작성하는 방법을 설명합니다. 독자는 플러그인 개발자입니다.

## Team 에이전트 vs Sub 에이전트

이 마켓플레이스에서 에이전트는 역할에 따라 두 가지 유형으로 구분됩니다.

### Team 에이전트 (사용자 직접 소통)

- 사용자와 직접 대화합니다.
- `AskUserQuestion` 도구를 사용하여 판단에 필요한 정보를 수집합니다.
- 모호한 상황에서 사용자에게 명확하게 질의합니다.
- 모든 판단과 결정을 이 단계에서 완료하여 Sub 에이전트에게 전달합니다.

예시: `gtm-analyzer` (컴포넌트 매핑 모호성, 파라미터 출처 불명 시 사용자 질의), `docsmith-analyzer` (문서 범위 인터뷰)

### Sub 에이전트 (자동 실행, 순수 실행)

- 사용자와 직접 소통하지 않습니다.
- Team 에이전트로부터 받은 명확한 지시대로만 실행합니다.
- 판단이 필요한 상황이 발생하면 중단하고 보고합니다.

예시: `gtm-implementer` (분석 결과 JSON 기반 코드 삽입), `docsmith-writer` (문서 목록 기반 파일 생성)

## 파일 위치

```
agents/<agent-name>.md
```

### 발견 우선순위

| 위치 | 범위 | 우선순위 |
|------|------|---------|
| `--agents` CLI 플래그 (JSON) | 현재 세션만 | 1 (최고) |
| `.claude/agents/` | 현재 프로젝트 | 2 |
| `~/.claude/agents/` | 모든 프로젝트 | 3 |
| `<plugin>/agents/` | 플러그인 활성화 프로젝트 | 4 (최저) |

## 에이전트 파일 포맷

```markdown
---
name: code-reviewer
description: Reviews code for quality and best practices
tools: Read, Glob, Grep
model: sonnet
---

You are a code reviewer. When invoked, analyze the code...
```

## Frontmatter 필드 전체 목록

| 필드 | 필수 | 설명 |
|------|------|------|
| `name` | **예** | 소문자·하이픈 고유 식별자 |
| `description` | **예** | Claude가 위임 여부 결정에 사용. "언제 이 에이전트에 위임해야 하는지" 명확히 작성 |
| `tools` | 아니오 | 허용 도구 allowlist. 미지정 시 전체 상속. 최소 권한 원칙 적용 |
| `disallowedTools` | 아니오 | 차단 도구 denylist |
| `model` | 아니오 | `sonnet` / `opus` / `haiku` / 전체 모델ID / `inherit` |
| `permissionMode` | 아니오 | `default` / `acceptEdits` / `dontAsk` / `bypassPermissions` / `plan` |
| `maxTurns` | 아니오 | 최대 에이전틱 턴 수 |
| `skills` | 아니오 | 시작 시 컨텍스트에 주입할 스킬 목록 |
| `mcpServers` | 아니오 | 에이전트 전용 MCP 서버 |
| `hooks` | 아니오 | 에이전트 라이프사이클 훅 |
| `memory` | 아니오 | `user` / `project` / `local` — 크로스 세션 메모리 |
| `background` | 아니오 | `true`이면 항상 백그라운드 실행 |
| `effort` | 아니오 | `low` / `medium` / `high` / `max` |
| `isolation` | 아니오 | `worktree` — 임시 git worktree에서 격리 실행 |
| `initialPrompt` | 아니오 | `--agent`로 메인 스레드 실행 시 자동 제출되는 첫 턴 프롬프트 |

## 모델 선택 기준

| 모델 | 용도 |
|------|------|
| `haiku` | 경량 작업: 단순 검색, 파일 읽기, 메타데이터 조회 |
| `sonnet` | 표준 작업: 코드 분석, 문서 작성, 일반 처리 |
| `opus` | 복잡한 작업: 아키텍처 결정, 심층 분석 |

## 내장 서브에이전트

Claude Code가 기본으로 제공하는 서브에이전트입니다. 별도 정의 없이 사용 가능합니다.

| 에이전트명 | 모델 | 도구 | 용도 |
|-----------|------|------|------|
| `Explore` | Haiku | 읽기 전용 | 코드베이스 탐색 |
| `Plan` | 상속 | 읽기 전용 | 플랜 모드 리서치 |
| `general-purpose` | 상속 | 전체 | 복잡한 다단계 작업 |
| `Bash` | 상속 | 터미널 | 별도 컨텍스트 명령 실행 |

## 플러그인 에이전트 제약 (중요)

플러그인 `agents/` 디렉토리의 에이전트는 보안상 다음 필드를 **무시**합니다.

- `hooks`
- `mcpServers`
- `permissionMode`

이 기능이 필요한 경우 사용자 레벨(`~/.claude/agents/`) 또는 프로젝트 레벨(`.claude/agents/`)에서 에이전트를 정의해야 합니다.

## 메모리 스코프

| 스코프 | 저장 경로 |
|--------|----------|
| `user` | `~/.claude/agent-memory/<agent-name>/` |
| `project` | `.claude/agent-memory/<agent-name>/` |
| `local` | `.claude/agent-memory-local/<agent-name>/` |

## 파일 구조 예시

```markdown
---
name: my-analyzer
description: 분석 작업을 담당하는 Team 에이전트 (분석, analyze, 코드 분석)
model: sonnet
tools:
  - Read
  - Glob
  - Grep
  - AskUserQuestion
---

# My Analyzer

당신은 ... 를 분석하는 에이전트입니다.

## 원칙

- 코드에서 확인한 사실만 보고합니다 (추측 금지)
- 모호한 상황에서는 AskUserQuestion으로 사용자에게 질의합니다

## 워크플로우

### Phase 1: 분석

...

### Phase 2: 결과 전달

...
```

## 생성 체크리스트

- [ ] `agents/<name>.md` 경로 확인
- [ ] frontmatter에 `name`, `description` 필수 포함
- [ ] `tools` 최소 권한 원칙 적용 (필요한 도구만)
- [ ] `model` 작업 복잡도에 맞게 선택
- [ ] `effort` 작업 강도에 맞게 선택 (선택사항)
- [ ] 플러그인 에이전트에 `hooks`, `mcpServers`, `permissionMode` 미사용
- [ ] Team vs Sub 역할 명확히 구분
- [ ] Sub 에이전트는 `AskUserQuestion` 미사용
- [ ] `initialPrompt` 필요 시 `--agent` 실행 전용으로만 사용

## 실제 예시 참고

| 에이전트 | 경로 | 유형 | 특징 |
|---------|------|------|------|
| `gtm-analyzer` | `plugins/gtm-tag/agents/gtm-analyzer.md` | Team | 사용자 직접 소통, 모든 결정 사전 해결 |
| `gtm-implementer` | `plugins/gtm-tag/agents/gtm-implementer.md` | Sub | JSON 기반 순수 실행 |
| `docsmith-analyzer` | `plugins/obsidian-nexus/agents/docsmith-analyzer.md` | Team | 인터뷰 3회 이내 |
| `docsmith-writer` | `plugins/obsidian-nexus/agents/docsmith-writer.md` | Sub | 템플릿 기반 문서 생성 |
| `librarian` | `plugins/obsidian-nexus/agents/librarian.md` | Sub | haiku 모델, 문서 관리 |
| `skill-doctor` | `plugins/skill-doctor/agents/skill-doctor.md` | Team | 진단 및 에스컬레이션 |

## 관련 문서

- [[플러그인 제작 가이드]]
- [[스킬 작성 가이드]]
- [[설계 결정 기록]]
