# 요구사항 문서 템플릿

Phase 2에서 CSV/입력을 파싱 후 requirement.md 생성 시 사용하는 포맷.

## 포맷

```
# GTM 이벤트 태깅 요구사항: {제목}

> 생성일: {YYYY-MM-DD}
> 원본: {CSV 경로 또는 "직접 입력"}
> 대상 센터: {da-center, bm-center 등}

## 1. 개요
- 목적: {목적}
- 대상 범위: {센터명} — {페이지 목록}
- prefix: {da, bm 등}

## 2. 이벤트 네이밍 규칙
- dataLayer 이벤트명: `{prefix}_{domain}_{action}`
- GTM에서 prefix 제거 → GA4 이벤트명: `{domain}_{action}`
- Host App 공통 변수 (이벤트 params에서 제외): (project-config.md의 Host App 공통 변수)

## 3. 이벤트 목록

### 3.x {페이지명} — {도메인}

| 이벤트 ID | GA4 이벤트명 | dataLayer 이벤트명 | 설명 | 파라미터 |
|-----------|-------------|-------------------|------|---------|
| {ID} | {CSV 이벤트명} | {prefix}_{domain}_{action} | {설명} | {파라미터 목록} |

## 4. 이벤트 파일 구성

| 파일 | const 이름 | prefix | 도메인 | 이벤트 수 |
|------|-----------|--------|--------|-----------|
| (project-config.md의 이벤트 파일 경로 패턴) | {CONST_NAME} | {prefix} | {domains} | {N} |

## 5. 컴포넌트 매핑 (Analyzer에서 확정)

(Phase 3 Analyzer 실행 전에는 비어있음. Analyzer가 분석 후 analysis.json에 기록)
```
