---
title: 용어 사전
aliases:
  - glossary
  - terms
  - 용어 사전
  - 용어집
tags:
  - reference
  - marketplace
  - claude-code
created: 2026-03-27
updated: 2026-03-27
audience: 전체
---

<!-- docsmith: auto-generated 2026-03-27 -->

# 용어 사전

jake-marketplace 및 Claude Code 플러그인 시스템에서 사용하는 핵심 용어를 정리합니다.

## 플러그인 시스템

### 마켓플레이스 (Marketplace)

Claude Code의 외부 플러그인 저장소. `gorillaProject/jake-marketplace`처럼 GitHub 저장소로 등록하며, `/plugin marketplace add` 명령어로 추가합니다.

### 플러그인 (Plugin)

Claude Code에 설치 가능한 스킬/에이전트/훅의 묶음. `plugins/{name}/` 디렉토리 단위로 정의하며, `/plugin install {name}@jake-plugins` 명령어로 설치합니다.

### 스킬 (Skill)

`/plugin-name:skill-name` 형태로 호출하는 Claude 프롬프트 단위. `SKILL.md` 파일에 정의합니다. Claude Code 세션에서 특정 작업 흐름을 실행하는 진입점입니다.

### 에이전트 (Agent)

스킬이 위임하는 서브에이전트. `agents/{name}.md`에 frontmatter(모델, 도구 목록)와 지시문으로 정의합니다. Team 에이전트와 Sub 에이전트로 구분됩니다.

- **Team 에이전트**: 사용자와 `AskUserQuestion`으로 직접 소통 가능
- **Sub 에이전트**: 사용자 상호작용 없이 다른 에이전트/스킬이 위임하여 실행

### 훅 (Hook)

Claude Code의 이벤트(도구 실행, 사용자 메시지 등)에 자동 반응하는 핸들러. `hooks/hooks.json`에 정의합니다. skill-doctor의 시그널 자동 수집에 사용됩니다.

---

## skill-doctor 용어

### 시그널 (Signal)

스킬 실행 중 발생한 문제의 기록 단위. 훅이 수집한 raw 이벤트를 Claude가 분류하여 의미 있는 시그널만 DB에 기록합니다.

### CD Score (Current Difficulty Score)

스킬 실행 1회에 대한 즉시 문제 점수. 높을수록 문제가 심각합니다.

| 시그널 유형 | 점수 |
|------------|------|
| clarify, blocked | 0 |
| tool_error | +15 |
| correct | +25 |
| manual_fix | +30 |
| redo | +40 |
| cancelled | +50 |

CD Score ≥ 30이면 자동으로 `diagnose`를 트리거합니다.

### 에스컬레이션 레벨 (Escalation Level)

동일 원인(`cause_type`)이 별개 세션에서 반복된 횟수.

| 반복 횟수 | 레벨 | 자동 액션 |
|-----------|------|-----------|
| 1회 | 1 | 프로파일 업데이트 |
| 2회 | 2 | 진단 리포트 생성 |
| 3회 | 3 | heal diff 제안 |
| 4회+ | 4 | 자동 적용 추천 |

### Health Score (스킬 건강도)

스킬의 전반적인 품질 지표 (0~100). 미해결 문제, 최근 CD 평균, 구조 이슈를 반영합니다.

```
health_score = max(0, 100
    - (미해결 스킬측 cause_type 수 × 15)
    - (최근 3세션 평균 CD ÷ 3)
    - (구조 이슈 × 5, 최대 -20))
```

### 원인 귀속 (Cause Attribution)

시그널의 원인이 스킬 결함인지 사용자 측 요인인지를 구분하는 분류.

- **스킬 측**: `ambiguous_instruction`, `missing_precondition`, `scope_exceeded`, `error_handling`, `output_mismatch` → CD 가산, 에스컬레이션 대상
- **사용자 측**: `insufficient_context`, `user_preference`, `external_issue` → CD 가산 안 함

### Heal (자가 치유)

에스컬레이션 레벨 3 이상이 된 로컬 스킬의 `SKILL.md`를 자동으로 수정하는 작업. 마켓플레이스 스킬은 heal 불가 (대신 `suggest`로 개선된 로컬 버전 생성).

---

## gtm-tag 용어

### gtm-tracker 모듈

gtm-tag 플러그인에 번들된 경량 TypeScript GTM 트래킹 모듈. `init` 시 프로젝트에 복사됩니다. `createTracker()`, `defineEvents()`, `<GTMTrackerProvider>`, `useTrackEvent()` 등을 제공합니다.

### 이벤트 네이밍 규칙

```
dataLayer 이벤트명: {prefix}_{domain}_{action}
GA4 이벤트명:      {domain}_{action}  (GTM에서 prefix 제거)
```

- **prefix**: 센터별 팀 식별자 (예: `da`, `bm`) — 네임스페이스 분리용
- **domain**: 기능 영역 (예: `ads`, `campaign`)
- **action**: 구체적 동작 (예: `click_download`)

### Host App 공통 변수

`workspace_id`, `user_id` 등 Host App이 페이지 진입 시 dataLayer에 자동 push하는 변수. 개별 이벤트 파라미터에서 제외하여 중복을 방지합니다.

### 배칭 (Batching)

30개 초과 이벤트 처리 시 센터별로 분할하여 순차 실행하는 방식. 각 배치는 `analyzer → implementer` 순서로 처리하고, 전체 완료 후 `verifier`를 1회 실행합니다.

### project-config.md

`/gtm-tag:init`이 생성하는 프로젝트별 설정 파일. gtm-tracker 모듈 경로, 이벤트 출력 디렉토리, 그룹 매핑, 패키지 매니저 명령어 등을 저장합니다.

---

## obsidian-nexus 용어

### obs-nexus CLI

Obsidian 볼트 문서를 검색/관리하는 외부 CLI 도구. `brew tap gorilla-kim/tap && brew install obs-nexus`로 설치합니다.

### 볼트 (Vault)

Obsidian의 문서 저장소 단위. obs-nexus는 볼트 단위로 문서를 인덱싱하고 검색합니다.

### docsmith

obsidian-nexus 플러그인 내 문서 자동 생성 파이프라인의 이름. `docsmith-analyzer`(분석)와 `docsmith-writer`(작성) 두 에이전트로 구성됩니다.

### 위키링크 (Wikilink)

Obsidian의 문서 간 링크 형식. `[[문서 제목]]` 형태로 작성합니다.

### frontmatter

마크다운 문서 상단의 YAML 메타데이터 블록. `title`, `aliases`, `tags`, `created`, `updated` 등을 포함합니다. obsidian-nexus는 이를 기반으로 문서를 검색하고 태그를 관리합니다.

---

## 관련 문서

- [[프로젝트 개요]]
- [[플러그인 시스템 구조]]
