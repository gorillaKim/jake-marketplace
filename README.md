# Jake's Claude Code 플러그인 마켓플레이스

개인용 Claude Code 플러그인을 관리하는 마켓플레이스입니다.

## 마켓플레이스 설치

```bash
/plugin marketplace add gorillaProject/jake-marketplace
```

## 등록된 플러그인

| 플러그인 | 설명 | 주요 명령어 | 버전 |
|---------|------|------------|------|
| `skill-doctor` | 스킬 건강 상태를 크로스 세션으로 진단하고 Hook+Agent 하이브리드로 자동 개선 | `/skill-doctor:dashboard` `/skill-doctor:diagnose` `/skill-doctor:heal` | 0.1.0 |
| `gtm-tag` | GA4 이벤트 CSV → gtm-tracker 이벤트 정의 + trackEvent 자동 삽입 | `/gtm-tag:init` `/gtm-tag:tag` | 0.1.0 |

### skill-doctor

스킬 실행 중 발생하는 문제를 **여러 세션에 걸쳐 자동 감지**하고 **점진적으로 개선**하는 플러그인.

- **Hook+Agent 하이브리드 시그널 수집**: Hook이 raw 이벤트(도구 실패, 사용자 메시지)를 시스템 레벨로 수집 → Claude가 유의미한 시그널만 판별하여 DB 기록
- **마켓플레이스 스킬 지원**: 설치된 외부 플러그인 스킬 자동 발견 및 진단 (heal은 로컬 스킬만)
- **점진적 에스컬레이션**: 같은 문제 1회→프로파일 업데이트, 2회→리포트, 3회→수정 제안, 4회+→자동 적용 추천
- **환경 자가 점검**: `/skill-doctor:checkup`으로 DB, Hook, 설정 상태 진단 및 자동 수정

### gtm-tag

GA4 이벤트 정의 CSV를 분석하여 gtm-tracker 기반 이벤트 정의 코드와 trackEvent 호출을 자동 생성하는 플러그인.

## 플러그인 설치 / 업데이트 / 제거

```bash
# 설치
/plugin install skill-doctor@jake-plugins
/plugin install gtm-tag@jake-plugins

# 업데이트
/plugin marketplace update
/plugin uninstall <플러그인명>
/plugin install <플러그인명>@jake-plugins

# 제거
/plugin uninstall <플러그인명>
```
