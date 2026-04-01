---
title: 문서 작성 컨벤션
aliases:
  - writing-conventions
  - 문서 작성 원칙
  - 문서 분류 기준
tags:
  - guide
  - conventions
created: "2026-04-01"
updated: "2026-04-01"
---

<!-- docsmith: auto-generated 2026-04-01 -->

# 문서 작성 컨벤션

obsidian-nexus 플러그인의 모든 스킬/에이전트가 공유하는 문서 분류 원칙.

## plan은 문서 타입이 아니다

`.omc/plans/`의 플랜 파일은 작업 접근 방식(여정)을 기록하는 **일시적 아티팩트**.
완료된 작업은 다음 문서 타입으로 흡수됩니다:

| 확정/완료된 내용 | 문서 타입 | 저장 위치 |
|---|---|---|
| 인터페이스·Props·API 확정 | `techspec` | `specs/{Name}/{Name}.spec.md` (프로젝트 루트) |
| 설계 방향 결정 (A vs B) | `decision` | `docs/architecture/decisions/` |
| 구현 완료 기록 | `devlog` | `docs/devlog/YYYY-MM-DD-{slug}.md` |
| 미완성 계획 | (저장 안 함) | `.omc/plans/`에 보존 |

## plan → devlog 흡수 패턴

구현이 완료됐을 때, `.omc/plans/`의 관련 플랜 파일이 있으면:
1. 플랜의 Context 섹션 → devlog "배경" 섹션에 요약
2. 플랜의 설계 결정 → devlog "변경 내용"에 포함
3. 플랜 파일 자체는 그대로 유지 (삭제하지 않음)

## plan vs specs 비교

| | plan | specs |
|---|---|---|
| 역할 | 어떻게 만들 것인가 (여정) | 무엇을 만들었는가 (목적지) |
| 생명주기 | 일시적 — 구현 완료 후 가치 감소 | 영속적 — 유지보수·온보딩 시 계속 참조 |
| 작성 시점 | 구현 전 | 인터페이스 확정 시 |
| 대상 독자 | 작업자 본인/팀 | 코드베이스를 이해하려는 모든 사람 |
| 저장 위치 | `.omc/plans/` | `specs/{LogicName}/` (프로젝트 루트) |

## 관련 문서

- [[docs/README]]
