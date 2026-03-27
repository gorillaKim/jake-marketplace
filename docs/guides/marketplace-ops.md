---
title: 마켓플레이스 운영 가이드
aliases:
  - marketplace-ops
  - marketplace-operations
  - 마켓플레이스 운영 가이드
  - 마켓플레이스 관리
tags:
  - guide
  - marketplace
  - claude-code
created: 2026-03-27
updated: 2026-03-27
---

<!-- docsmith: auto-generated 2026-03-27 -->

# 마켓플레이스 운영 가이드

jake-marketplace를 관리하는 방법을 설명합니다. 독자는 마켓플레이스 관리자입니다.

## 마켓플레이스 구조

```
jake-marketplace/
├── .claude-plugin/
│   └── marketplace.json     # 마켓플레이스 레지스트리
├── plugins/
│   ├── skill-doctor/        # 플러그인 디렉토리
│   ├── gtm-tag/
│   └── obsidian-nexus/
├── docs/                    # 마켓플레이스 문서
└── README.md
```

## marketplace.json 레지스트리

`.claude-plugin/marketplace.json`에 모든 플러그인이 등록됩니다.

```json
{
  "name": "jake-plugins",
  "owner": {
    "name": "jake",
    "email": "yhkim@madup.com"
  },
  "metadata": {
    "description": "Jake의 Claude Code 플러그인 마켓플레이스",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "skill-doctor",
      "source": "./plugins/skill-doctor",
      "description": "스킬의 건강 상태를 크로스 세션으로 진단하고 점진적으로 개선하는 플러그인",
      "version": "0.1.0",
      "category": "developer-tools"
    }
  ]
}
```

### plugins 배열 필드

| 필드 | 필수 | 설명 |
|------|------|------|
| `name` | 예 | 플러그인 이름 (plugin.json의 name과 일치해야 함) |
| `source` | 예 | 플러그인 디렉토리 경로 (상대경로) |
| `description` | 권장 | 플러그인 설명 |
| `version` | 권장 | 버전 |
| `category` | 선택 | 카테고리 (예: `developer-tools`) |

## 현재 등록 플러그인

| 플러그인 | 버전 | 설명 | 주요 스킬 |
|---------|------|------|----------|
| `skill-doctor` | 0.1.0 | 스킬 건강 상태 크로스 세션 진단 및 자동 개선 | `/skill-doctor:dashboard` `/skill-doctor:diagnose` `/skill-doctor:heal` |
| `gtm-tag` | 0.1.0 | GA4 이벤트 CSV → gtm-tracker 이벤트 정의 + trackEvent 자동 삽입 | `/gtm-tag:init` `/gtm-tag:tag` |
| `obsidian-nexus` | 0.1.0 | 프로젝트 분석 기반 문서 자동 생성 및 관리 | `/obs-nexus:onboard` `/obs-nexus:librarian` `/obs-nexus:doctor` |

## 사용자 관점: 마켓플레이스 설치

```bash
# 마켓플레이스 등록 (최초 1회)
/plugin marketplace add gorillaProject/jake-marketplace

# 플러그인 설치
/plugin install skill-doctor@jake-plugins
/plugin install gtm-tag@jake-plugins
/plugin install obsidian-nexus@jake-plugins
```

## 관리자 작업

### 새 플러그인 추가

1. `plugins/<plugin-name>/` 디렉토리 생성
2. `plugins/<plugin-name>/.claude-plugin/plugin.json` 작성
3. `.claude-plugin/marketplace.json`의 `plugins` 배열에 항목 추가
4. README.md에 플러그인 설명 추가
5. git commit 및 push

### 플러그인 버전 업데이트

1. 플러그인 코드 수정
2. `plugins/<plugin-name>/.claude-plugin/plugin.json`의 `version` 갱신
3. `.claude-plugin/marketplace.json`의 해당 플러그인 `version` 갱신
4. git commit 및 push

사용자는 다음 명령으로 업데이트를 받습니다.

```bash
/plugin marketplace update
/plugin uninstall <plugin-name>
/plugin install <plugin-name>@jake-plugins
```

### 플러그인 제거

1. `plugins/<plugin-name>/` 디렉토리 삭제
2. `.claude-plugin/marketplace.json`에서 해당 항목 제거
3. README.md에서 해당 플러그인 설명 제거
4. git commit 및 push

## 의존성 관리

플러그인이 외부 도구에 의존하는 경우 README.md에 명시합니다.

현재 의존성:

| 플러그인 | 의존성 | 설치 방법 |
|---------|--------|----------|
| `obsidian-nexus` | `obs-nexus` CLI | `brew tap gorilla-kim/tap && brew install obs-nexus` |
| `skill-doctor` | Python 3 | 시스템 설치 확인 |

## 캐시 위치

사용자가 설치한 플러그인은 다음 경로에 캐시됩니다.

```
~/.claude/plugins/cache/<marketplace-name>/<plugin-name>/<version>/
```

예시: `~/.claude/plugins/cache/jake-plugins/skill-doctor/0.1.0/`

## 관련 문서

- [[플러그인 제작 가이드]]
- [[스킬 작성 가이드]]
- [[에이전트 작성 가이드]]
- [[설계 결정 기록]]
