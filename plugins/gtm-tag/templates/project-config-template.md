# GTM Tag — 프로젝트 설정

> 이 파일은 `gtm-tag:init` 스킬이 자동 생성합니다.
> 프로젝트별 설정이며, `gtm-tag/project-config.md`에 저장됩니다.

## gtm-tracker 모듈
- 경로: `{gtm_tracker_path}`
- import: `import { defineEvents } from '{import_alias}'`
- React import: `import { useTrackEvent } from '{import_alias}/react'`
- Provider import: `import { GTMTrackerProvider } from '{import_alias}/react'`
- Tracker import: `import { createTracker } from '{import_alias}'`

## 이벤트 파일 출력 경로
- 디렉토리: `{events_dir}`
- 파일 패턴: `{group}.events.ts`

## 앱 루트
- 파일: `{app_root_file}`

## Host App 공통 변수 (이벤트 params에서 제외)
- {host_app_common_vars}

## 패키지 매니저
- 타입 체크: `{type_check_cmd}`
- 테스트: `{test_cmd}`
- 스냅샷 업데이트: `{snapshot_update_cmd}`

## 문서 출력 경로
- 기본: `{docs_output_path}`
- CSV 입력 시: CSV 파일이 있는 폴더를 작업 폴더로 사용
- 직접 입력 시: `{docs_output_path}/{YYYYMMDD}/` 하위에 날짜 폴더 생성
- 기존 requirement.md 재사용 시: 해당 파일이 있는 폴더

### 작업 폴더에 생성되는 산출물
- `requirement.md` — 요구사항 문서 (Phase 2)
- `analysis.json` — 컴포넌트 매핑 결과 (Phase 3-1)
- `event-coverage.md` — 이벤트 커버리지 검증 (Phase 3-3)
- `integration-guide.md` — 개발자용 통합 가이드 (Phase 3-3)
- `result.md` — 기획자 전달용 최종 산출물 (Phase 4)

## 그룹 매핑

| 그룹명 | prefix | 페이지 | 라우트 | 비고 |
|--------|--------|--------|--------|------|
| {group_name} | {prefix} | {page} | {route} | |

## 스킵 규칙
- {skip_rules}

## CSV 헤더 포맷
```
{csv_header_format}
```
