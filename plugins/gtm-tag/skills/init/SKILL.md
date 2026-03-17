---
name: init
description: 프로젝트에 gtm-tag를 설정하고 project-config.md를 생성할 때 사용 (gtm-tag 설정, init, 초기화, gtm-tag 시작, 셋업, gtm-tag 설치)
---

# gtm-tag 초기화

프로젝트에 gtm-tracker 모듈과 project-config.md를 설정합니다.

## 실행 절차

### 1. project-config.md 확인

프로젝트 루트의 `gtm-tag/project-config.md`가 있는지 확인한다.

- **있으면**: "이미 설정되어 있습니다" 안내 후, 내용을 보여주고 수정 여부를 질문
- **없으면**: Step 2로 진행

### 2. 프로젝트 설정 수집

AskUserQuestion으로 프로젝트 설정값을 수집한다.

```yaml
questions:
  - question: '프로젝트 설정을 순서대로 입력해주세요'
    header: 'gtm-tag 프로젝트 설정'
    options:
      - label: '대화형으로 하나씩 입력'
        description: '각 항목을 질문/응답 형식으로 수집합니다'
      - label: '한번에 입력'
        description: '설정 항목 전체를 한번에 제공합니다'
    multiSelect: false
```

수집할 항목:

1. **gtm-tracker 모듈 설치 경로**: 프로젝트 내 gtm-tracker 모듈이 위치할 경로 (예: `src/utils/gtm-tracker/`)
2. **import alias**: tsconfig.json baseUrl/paths 기반 import 경로 (예: `utils/gtm-tracker`)
3. **이벤트 파일 출력 디렉토리**: 이벤트 정의 파일이 생성될 경로 (예: `src/events/`)
4. **앱 루트 파일**: GTMTrackerProvider를 감쌀 루트 컴포넌트 파일 (예: `src/Main.tsx`)
5. **Host App 공통 변수**: Host가 dataLayer에 push하는 공통 변수 목록 (이벤트 params에서 제외)
6. **패키지 매니저 명령어** (3개 각각 수집):
   - 타입 체크 명령어 (예: `pnpm tsc --noEmit`)
   - 테스트 명령어 (예: `pnpm test`)
   - 스냅샷 업데이트 명령어 (예: `pnpm test -- -u`)
7. **문서 출력 경로**: 산출물(requirement.md, analysis.json, result.md 등) 저장 기본 경로 (예: `__docs__/tag/task/`). CSV 입력 시에는 CSV 폴더가 우선, 직접 입력 시 이 경로에 날짜 폴더 생성
8. **그룹 매핑**: 센터별 그룹명, prefix, 페이지, 라우트 매핑
9. **스킵 규칙**: 특정 그룹/prefix를 스킵하는 규칙
10. **CSV 헤더 포맷**: 기획자가 제공하는 CSV의 헤더 포맷

### 3. project-config.md 생성

수집한 값으로 `${CLAUDE_PLUGIN_ROOT}/templates/project-config-template.md`를 참고하여 `gtm-tag/project-config.md`를 생성한다.

```bash
mkdir -p gtm-tag
```

프로젝트 루트의 `gtm-tag/project-config.md`에 Write.

### 4. gtm-tracker 모듈 설치

프로젝트에 gtm-tracker 모듈이 존재하는지 확인한다:
- `defineEvents` 또는 `createTracker`를 프로젝트 전체에서 검색
- 모듈 경로(project-config.md에 설정된 경로)에 파일이 있는지 확인

**없으면**: `${CLAUDE_PLUGIN_ROOT}/module/` 내용을 project-config.md에 설정된 경로에 복사 (**`__tests__/` 디렉토리는 제외**)

**있으면**: 경로 확인 후 project-config.md와 일치하는지 검증

### 5. Provider 설정 확인

`GTMTrackerProvider`가 앱 루트에 설정되었는지 확인:
- 없으면 → `createTracker({ debug: process.env.NODE_ENV === 'development' })`로 인스턴스 생성 + 앱 루트를 `<GTMTrackerProvider>` 로 감싸기
- 있으면 → 스킵

### 6. 디렉토리 확인

- 이벤트 파일 출력 디렉토리 생성 (없으면)
- 문서 출력 경로 디렉토리 생성 (없으면)

### 7. 설치 확인 리포트

```
## gtm-tag 초기화 완료

| 항목 | 상태 |
|------|------|
| project-config.md | ✅ gtm-tag/project-config.md |
| gtm-tracker 모듈 | ✅ {모듈 경로} |
| GTMTrackerProvider | ✅ {앱 루트 파일} |
| 이벤트 디렉토리 | ✅ {이벤트 경로} |
| 문서 디렉토리 | ✅ {문서 경로} |
| 플러그인 | ✅ gtm-tag@jake-plugins |

사용 가능한 명령어:
- `/gtm-tag:tag` — GA4 이벤트 태깅 자동화 실행
- `/gtm-tag:tag <CSV 경로>` — CSV 파일로 바로 시작
```

### 8. 다음 단계 추천

```yaml
questions:
  - question: '초기화가 완료되었습니다. 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: 'tag — 이벤트 태깅 시작'
        description: 'CSV를 기반으로 이벤트 태깅을 시작합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

사용자가 tag를 선택하면 `/gtm-tag:tag` 스킬 실행을 안내한다.

