---
title: "plan vs specs 역할 명확화 및 session-devlog 개선"
aliases:
  - plan-specs-clarification
  - plan-specs-역할-명확화
  - devlog-session-improvement
tags:
  - devlog
  - feature
  - obsidian-nexus
  - plugin
created: "2026-04-01"
updated: "2026-04-01"
---

<!-- docsmith: auto-generated 2026-04-01 -->

# plan vs specs 역할 명확화 및 session-devlog 개선

## 배경

프로젝트 문서 작성 과정에서 `plan`과 `specs`의 역할이 혼재되어 있었다. session-devlog 스킬이 `.omc/plans/` 디렉토리를 탐색할 기준이 없었고, plan 타입이 별도의 문서 타입으로 취급되어 devlog가 오염될 수 있는 구조였다. 이를 바로잡기 위해 두 개념의 책임 범위를 명확히 구분하고, 스킬 동작 방식을 개선했다.

## 변경 내용

### 주요 변경사항

- **`skills/session-devlog/SKILL.md`**: `.omc/plans/` 탐색 로직에 3단계 판단 기준(대화 참조 파일명 > 오늘 날짜 생성/수정 > 키워드 매칭) 추가. plan→문서 전환 기준 테이블 삽입. `AskUserQuestion` 단계에 미완성 계획 "저장하지 않음" 알림 추가
- **`skills/onboard/SKILL.md`**: `docs/` 구조 트리에 `specs/` 항목 추가 (프로젝트 루트 기준 주석 포함)
- **`docs/writing-conventions.md` 신규 생성**: "plan은 문서 타입이 아니다" 원칙을 팀 공유 컨벤션 문서로 확립

### 핵심 원칙 확립

| 개념 | 성격 | 저장 위치 | 문서 타입 |
|------|------|-----------|-----------|
| plan | 작업 접근 방식 (일시적) | `.omc/plans/` | 해당 없음 |
| specs | 결과물 정의 (영속적) | `specs/{LogicName}/` | techspec / decision |

- plan 타입은 별도 문서 타입이 아님 → `techspec` / `decision` / `devlog`로 흡수
- "계획만 세우고 구현 아직" 상태에서는 devlog를 저장하지 않음 (devlog 오염 방지)

### 영향 범위

- `skills/session-devlog` 스킬 동작 방식
- `skills/onboard` 문서 구조 안내
- 프로젝트 전반의 문서 작성 컨벤션 (`docs/writing-conventions.md`)

## 결과

- `.omc/plans/` 탐색 기준이 명확해져 session-devlog 스킬이 관련 계획 파일을 일관되게 찾을 수 있게 됨
- plan 타입 혼용 제거로 devlog 품질 향상
- `writing-conventions.md`가 신규 팀원 온보딩 및 스킬 참조 문서로 활용 가능

## 교훈

- critic 리뷰에서 "plans/ 탐색 기준 없음"과 "위키링크 경로 오류" 두 가지를 포착 — 구체적 판단 기준을 명시하는 것이 모호한 지침보다 실질적으로 중요하다
- 프로젝트 소스 파일을 먼저 수정한 뒤 캐시에 동기화하는 것이 올바른 순서. 이번 세션에서 역순으로 시작해 교정하는 과정이 발생했으므로 향후 작업 순서를 고정한다

## 관련 문서

- [[docs/writing-conventions]]
- [[skills/session-devlog/SKILL]]
- [[skills/onboard/SKILL]]
