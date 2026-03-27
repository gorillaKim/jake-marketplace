---
title: 설계 결정 기록
aliases:
  - design-decisions
  - adr
  - 설계 결정 기록
  - 아키텍처 결정
tags:
  - reference
  - agent
  - plugin
  - claude-code
created: 2026-03-27
updated: 2026-03-27
---

<!-- docsmith: auto-generated 2026-03-27 -->

# 설계 결정 기록

jake-marketplace 플러그인 설계 과정에서 내린 주요 결정들을 기록합니다. 독자는 플러그인 개발자입니다.

---

## ADR-001: Hook+Agent 하이브리드 시그널 수집

**플러그인**: skill-doctor

### 컨텍스트

스킬 실행 중 발생하는 문제(도구 실패, 사용자 수정, 재시도 등)를 자동으로 감지하여 스킬 품질을 점진적으로 개선해야 합니다. 순수 에이전트 방식만 사용하면 세션마다 컨텍스트가 초기화되어 크로스 세션 데이터 누적이 불가능합니다.

### 결정

**Hook이 raw 이벤트를 수집하고, 세션 종료 시 Agent가 유의미한 시그널만 판별하여 DB에 기록**하는 하이브리드 방식을 채택했습니다.

`hooks/hooks.json`에 6개 훅 이벤트를 등록합니다.

- `PreToolUse` (Skill matcher): 스킬 실행 시작 감지
- `PostToolUse` (전체): 도구 실행 결과 감지
- `PostToolUseFailure` (전체): 도구 실패 감지
- `UserPromptSubmit` (전체): 사용자 메시지 감지
- `Stop`: 세션 종료 시 최종 판별 및 DB 기록
- `SessionEnd`: 세션 완전 종료 시 처리

### 대안

- **순수 훅 방식**: 빠르지만 판단 로직이 복잡해지고 오탐이 많음
- **순수 에이전트 방식**: 크로스 세션 데이터 누적 불가
- **사용자 수동 기록만**: 누락이 많아 데이터 품질 저하

### 근거

Hook은 시스템 레벨로 모든 이벤트를 놓치지 않고 수집합니다. Agent는 컨텍스트를 이해하여 노이즈를 필터링합니다. 두 방식의 장점을 결합하면 높은 정확도와 자동화를 동시에 달성할 수 있습니다.

---

## ADR-002: 자동 체이닝 파이프라인 (record → diagnose → heal)

**플러그인**: skill-doctor

### 컨텍스트

시그널이 누적될수록 문제를 자동으로 인식하고 수정까지 이어지는 파이프라인이 필요합니다. 사용자가 매번 수동으로 diagnose → heal을 실행하면 부담이 큽니다.

### 결정

CD(Concern Degree) 점수 기반 **점진적 에스컬레이션**을 채택했습니다.

| 누적 횟수 | 자동 동작 |
|----------|----------|
| 1회 | 스킬 프로파일 업데이트 |
| 2회 | 리포트 생성 |
| 3회 | 수정 제안 |
| 4회+ | 자동 적용 추천 |

CD 점수가 50 이상이면 record 완료 후 diagnose를 자동 트리거합니다.

### 시그널 CD 점수 기준

| 타입 | CD 점수 |
|------|---------|
| `cancelled` | +50 |
| `redo` | +40 |
| `manual_fix` | +30 |
| `correct` | +25 |
| `tool_error` | +15 |
| `clarify` | +0 |
| `blocked` | +0 |

사용자 측 원인(`insufficient_context`, `user_preference`, `external_issue`)은 CD 점수에 가산하지 않습니다.

### 근거

즉각적인 자동 수정은 스킬을 의도치 않게 변경할 수 있습니다. 점진적 에스컬레이션은 데이터를 충분히 수집한 후 사용자에게 제어권을 주면서도 자동화 효과를 냅니다.

---

## ADR-003: Team 에이전트 vs Sub 에이전트 역할 분리

**플러그인**: gtm-tag, obsidian-nexus

### 컨텍스트

복잡한 작업을 에이전트 파이프라인으로 처리할 때, 사용자 소통과 실행을 한 에이전트에서 담당하면 책임이 불명확하고 오류 복구가 어렵습니다.

### 결정

에이전트를 역할에 따라 두 유형으로 분리합니다.

**Team 에이전트 (사용자 직접 소통)**
- `AskUserQuestion`을 사용하여 모호성을 사전 해결합니다.
- 모든 판단은 이 단계에서 완료되어야 합니다.
- Sub 에이전트가 받는 지시에 미해결 항목이 없어야 합니다.

**Sub 에이전트 (순수 실행)**
- 사용자와 직접 소통하지 않습니다.
- Team 에이전트의 분석 결과(JSON 또는 명확한 명세)만 받아 실행합니다.
- 판단이 필요한 상황이 발생하면 중단하고 보고합니다.

### 실제 적용

| 플러그인 | Team | Sub |
|---------|------|-----|
| gtm-tag | `gtm-analyzer` | `gtm-implementer`, `gtm-verifier` |
| obsidian-nexus | `docsmith-analyzer` | `docsmith-writer` |
| obsidian-nexus | `librarian` (일부 사용자 소통 포함) | — |

### 근거

Sub 에이전트는 사용자와 소통할 수 없는 환경(백그라운드 실행, 자동 체이닝)에서도 안정적으로 동작해야 합니다. 사용자 소통을 Team 단계에서 집중하면 전체 파이프라인의 예측 가능성이 높아집니다.

---

## ADR-004: MCP 우선, CLI 폴백 전략

**플러그인**: obsidian-nexus

### 컨텍스트

Obsidian 볼트와의 연동 방법으로 MCP(Model Context Protocol)와 CLI(`obs-nexus`) 두 가지 옵션이 있습니다. MCP는 성능이 우수하지만 항상 연결된다는 보장이 없습니다.

### 결정

**MCP를 우선 사용하고, 미연결 환경에서는 CLI로 폴백**합니다.

```
MCP 연결 확인 → 사용 가능하면 nexus_* 도구 사용
                → 불가능하면 obs-nexus CLI 명령 사용
```

MCP 도구는 토큰 효율이 매우 높습니다. 예를 들어 특정 섹션 조회 시 `nexus_get_section`은 전체 문서 Read 대비 토큰을 90% 절약합니다.

### MCP vs CLI 도구 매핑

| 작업 | MCP 도구 | CLI 명령 |
|------|----------|----------|
| 문서 검색 | `nexus_search` | `obs-nexus search` |
| 전체 문서 읽기 | `nexus_get_document` | `obs-nexus doc get` |
| 특정 섹션 | `nexus_get_section` | `obs-nexus doc section` |
| 역방향 링크 | `nexus_get_backlinks` | `obs-nexus doc backlinks` |
| 재인덱싱 | MCP 트리거 | `obs-nexus index` |

### 근거

MCP 전환으로 토큰 사용량이 크게 줄고 응답 속도가 빨라집니다. 그러나 MCP가 항상 연결된다고 가정하면 환경 의존성이 높아지므로, CLI 폴백을 유지하여 독립 실행성을 보장합니다.

---

## ADR-005: 플러그인 에이전트 보안 제약 수용

**플러그인**: 전체

### 컨텍스트

Claude Code는 보안상 플러그인 `agents/` 디렉토리의 에이전트에서 `hooks`, `mcpServers`, `permissionMode` 필드를 무시합니다.

### 결정

이 제약을 수용하고, 해당 기능이 필요한 경우 **사용자에게 수동 설정을 안내**합니다.

- skill-doctor의 Hook은 플러그인의 `hooks/hooks.json`에서 정의합니다 (에이전트 frontmatter가 아닌 플러그인 레벨 훅).
- MCP 연동이 필요한 에이전트는 사용자 레벨(`~/.claude/agents/`)에서 별도 정의를 안내합니다.

### 근거

플러그인 에이전트 보안 제약은 악의적인 플러그인이 시스템 권한을 획득하는 것을 방지합니다. 이 제약을 우회하려 하지 않고 설계 원칙으로 수용합니다.

## 관련 문서

- [[플러그인 제작 가이드]]
- [[에이전트 작성 가이드]]
- [[스킬 작성 가이드]]
- [[마켓플레이스 운영 가이드]]
