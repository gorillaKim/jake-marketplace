---
title: "obsidian-nexus techspec 문서 타입 지원 추가"
aliases:
  - obsidian-nexus-techspec-support
  - techspec 지원 추가
  - techspec devlog
tags:
  - devlog
  - feature
  - plugin
  - obsidian-nexus
created: "2026-04-01"
updated: "2026-04-01"
---

<!-- docsmith: auto-generated 2026-04-01 -->

# obsidian-nexus techspec 문서 타입 지원 추가

## 배경

obsidian-nexus 플러그인의 docsmith 에이전트가 기존에 지원하던 문서 타입(overview, architecture, guides, devlog, integrations, context)은 설계 문서나 기술 명세 수준의 스펙을 다루지 못했다. xpert-na-web 등 실제 프로젝트에서 `specs/` 디렉토리 패턴이 이미 사용되고 있었으나, docsmith 파이프라인이 이를 감지하거나 생성하는 기능이 없었다. 이를 해결하기 위해 `techspec` 문서 타입을 신규 추가했다.

## 변경 내용

### 주요 변경사항

- `templates/techspec.md` 신규 생성 — 범용 기술 명세 템플릿. 인터페이스 정의(Props/API/CLI args), 동작 명세, 예외 처리, 데이터 흐름 섹션을 포함
- `templates/techspec-prompt.md` 신규 생성 — Claude 스펙 생성 프롬프트 보존용. `.spec.md`와 쌍을 이루는 `.prompt.md` 파일로 관리
- `agents/docsmith-analyzer.md` 수정 — Phase 1 감지 휴리스틱에 `specs/` 디렉토리 패턴 6가지 추가, Phase 2 갭 분석 리포트에 `[specs/]` 카테고리 추가
- `agents/docsmith-writer.md` 수정 — `specs/` 카테고리 작성 지침 추가. `.spec.md` + `.prompt.md` 쌍 생성 방식 명시
- `skills/session-devlog/SKILL.md` 수정 — techspec 타입 감지 테이블 추가, Step 4 동적 템플릿 라우팅(타입별 템플릿 경로 매핑) 추가, 반복 패턴 감지 시 스킬화 제안 HTML 주석 삽입 지시 추가

### 영향 범위

- docsmith 파이프라인 전체 (analyzer → writer 흐름)
- session-devlog 스킬의 템플릿 라우팅 로직
- `specs/{LogicName}/{LogicName}.spec.md` 중첩 폴더 패턴으로 인덱싱되는 모든 볼트

## 결과

- docsmith-analyzer가 `specs/` 디렉토리를 감지하고 갭 분석에 반영하게 됨
- docsmith-writer가 `.spec.md` + `.prompt.md` 쌍을 생성할 수 있게 됨
- session-devlog 스킬이 세션 내용에 따라 적절한 템플릿으로 자동 라우팅됨
- 스킬화 제안이 HTML 주석으로 문서에 삽입되어 Obsidian 렌더링에서 숨겨지면서도 `/skill-doctor:suggest` 파싱 대상이 됨

## 교훈

- critic 리뷰가 pipeline 단절 버그를 포착했다. 초안에서 docsmith-writer만 수정하고 docsmith-analyzer를 누락했는데, 구현 전 critic 리뷰 단계가 이를 잡아냈다. 리뷰를 구현 이후로 미루면 이미 작성된 코드를 되돌려야 하는 비용이 발생한다.
- 템플릿 경로가 하드코딩된 구조에서는 새 문서 타입을 추가할 때 라우팅 로직도 반드시 함께 업데이트해야 한다. 한 곳만 수정하면 파이프라인이 조용히 깨진다.
- "Props 인터페이스"를 "인터페이스 정의 (Props/API/CLI args)"로 범용화한 결정은 백엔드/CLI 로직에도 같은 템플릿을 재사용할 수 있게 해준다. 프론트엔드 중심 용어를 도메인 중립 용어로 바꾸는 것이 플러그인 범용성을 높인다.

## 관련 문서

- [[obsidian-nexus docsmith-analyzer]]
- [[obsidian-nexus docsmith-writer]]
- [[session-devlog skill]]

<!-- 💡 스킬화 제안
작업: 플랜 → critic 리뷰 → 수정 → 구현 사이클
이유: 이번 세션에서도 2회 반복. critic 에이전트 호출 + 플랜 수정 + 구현 순서가 정형화되어 있어 스킬로 만들면 진입 장벽을 낮추고 리뷰 누락을 방지할 수 있음
-->
