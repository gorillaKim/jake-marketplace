---
title: 프로젝트 개요
aliases:
  - project-summary
  - jake-marketplace
  - 프로젝트 개요
  - 마켓플레이스 개요
tags:
  - overview
  - marketplace
  - claude-code
  - plugin
created: 2026-03-27
updated: 2026-03-27
audience: 개발자/전체
---

<!-- docsmith: auto-generated 2026-03-27 -->

# Jake's Claude Code 플러그인 마켓플레이스

개인용 Claude Code 플러그인을 관리하는 마켓플레이스 저장소입니다.
Claude Code의 `/plugin` 명령어로 설치하면 플러그인이 `~/.claude/`에 복사되어 즉시 사용 가능합니다.

## 마켓플레이스 등록

```bash
/plugin marketplace add gorillaProject/jake-marketplace
```

## 등록된 플러그인

| 플러그인 | 버전 | 설명 |
|---------|------|------|
| `skill-doctor` | 0.1.0 | 스킬 건강 상태를 크로스 세션으로 진단하고 Hook+Agent 하이브리드로 자동 개선 |
| `gtm-tag` | 0.1.0 | GA4 이벤트 CSV → gtm-tracker 이벤트 정의 + trackEvent 자동 삽입 |
| `obsidian-nexus` | 0.1.0 | 프로젝트 분석 기반 문서 자동 생성 및 관리, obs-nexus CLI 연동 |

## 저장소 구조

```
jake-marketplace/
├── plugins/
│   ├── skill-doctor/          ← 스킬 자가 진단/치유 플러그인
│   │   ├── agents/            ← skill-doctor.md, skill-healer.md
│   │   ├── skills/            ← init, dashboard, diagnose, heal, record, report, suggest, create, checkup
│   │   ├── hooks/             ← hooks.json (시그널 자동 수집)
│   │   ├── scripts/           ← cli.py, signal-collector.py
│   │   └── docs/
│   ├── gtm-tag/               ← GTM 이벤트 자동화 플러그인
│   │   ├── agents/            ← gtm-analyzer.md, gtm-implementer.md, gtm-verifier.md
│   │   ├── skills/            ← init, tag, doctor
│   │   ├── module/            ← gtm-tracker TypeScript 모듈 번들
│   │   └── templates/
│   └── obsidian-nexus/        ← 문서 관리 사서 플러그인
│       ├── agents/            ← docsmith-analyzer.md, docsmith-writer.md, librarian.md
│       ├── skills/            ← onboard, add, doctor, librarian, session-devlog
│       └── templates/
└── docs/
    └── overview/              ← 이 문서 위치
```

## 플러그인 설치 / 업데이트 / 제거

```bash
# 설치
/plugin install skill-doctor@jake-plugins
/plugin install gtm-tag@jake-plugins
/plugin install obsidian-nexus@jake-plugins

# 업데이트
/plugin marketplace update
/plugin uninstall <플러그인명>
/plugin install <플러그인명>@jake-plugins

# 제거
/plugin uninstall <플러그인명>
```

## 기술 스택

| 영역 | 기술 |
|------|------|
| 에이전트/스킬 정의 | Markdown (SKILL.md, agents/*.md) |
| CLI 도구 | Python 3 (외부 패키지 불필요) |
| GTM 트래커 모듈 | TypeScript |
| 문서 관리 연동 | obs-nexus CLI |
| 플랫폼 | Claude Code `/plugin` 시스템 |

## 외부 의존성

| 플러그인 | 의존성 | 설치 방법 |
|---------|--------|-----------|
| skill-doctor | python3 (macOS 기본 포함) | 별도 설치 불필요 |
| gtm-tag | React SPA + TypeScript 프로젝트 | 프로젝트별 |
| obsidian-nexus | obs-nexus CLI | `brew tap gorilla-kim/tap && brew install obs-nexus` |

## 관련 문서

- [[플러그인 시스템 구조]]
- [[용어 사전]]
