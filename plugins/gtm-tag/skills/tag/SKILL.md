---
name: tag
description: 기획자의 GA4 이벤트 CSV를 파싱하여 gtm-tracker 기반으로 이벤트 정의 파일 생성 + 컴포넌트에 trackEvent 호출을 자동 삽입하는 스킬. 서브에이전트 파이프라인으로 자동화합니다. (gtm 태깅, gtm 이벤트 태깅, ga4 이벤트, gtm-tag)
---

# GTM Tag 자동화

기획자의 GA4 이벤트 목록(CSV 또는 직접 입력)을 기반으로 `gtm-tracker` 모듈을 사용하여 이벤트 정의 파일을 생성하고, React 컴포넌트에 `trackEvent` 호출을 자동 삽입합니다.

## Input

- `$ARGUMENTS`: 이벤트 CSV 파일 경로 또는 빈 값 (대화형 수집)

## Workflow

### Phase 0: Init (최초 1회)

프로젝트에 gtm-tracker 관련 설정이 존재하는지 확인하고, 없으면 `/gtm-tag:init` 스킬에 위임합니다.

1. `gtm-tag/project-config.md` 읽기
   - **없으면** → AskUserQuestion으로 사용자에게 선택지 제시:
     ```yaml
     questions:
       - question: 'project-config.md가 없습니다. 어떻게 할까요?'
         header: '설정 필요'
         options:
           - label: '/gtm-tag:init 실행'
             description: '초기화 스킬로 전체 설정을 진행합니다 (권장)'
           - label: '여기서 바로 설정'
             description: '최소 설정만 질문하고 바로 태깅을 시작합니다'
         multiSelect: false
     ```
     - "init 실행" 선택 → `/gtm-tag:init` 안내 후 종료
     - "바로 설정" 선택 → `mkdir -p gtm-tag` 후 AskUserQuestion으로 필수 설정만 수집하여 `gtm-tag/project-config.md` 생성
   - **있으면** → project-config.md 읽고 다음 단계로
2. gtm-tracker 모듈 존재 확인 (project-config.md의 경로로 검색, 또는 `defineEvents`/`createTracker` 프로젝트 전체 검색)
   - 있으면 → 경로 확인, project-config.md 업데이트
   - 없으면 → AskUserQuestion으로 설치 위치 질문 → `${CLAUDE_PLUGIN_ROOT}/module/` 내용을 지정 위치에 복사 (**`__tests__/` 디렉토리는 제외**)
3. `GTMTrackerProvider`가 앱 루트에 설정되었는지 확인 → 없으면 설정:
   - `createTracker({ debug: process.env.NODE_ENV === 'development' })`로 인스턴스 생성
   - 앱 루트 컴포넌트를 `<GTMTrackerProvider>` 로 감싸기
4. **기존 raw dataLayer.push 감지**: 프로젝트 내 `window.dataLayer.push(` 또는 `dataLayer.push(` 직접 호출을 검색 (gtm-tracker 모듈 내부 제외)
   - 발견 시 → 사용자에게 경고 + 건수 보고:
     ```
     ⚠️ gtm-tracker를 사용하지 않는 직접 dataLayer.push 호출이 {N}건 발견되었습니다.
     이벤트 중복 방지를 위해 기존 호출을 gtm-tracker로 마이그레이션하는 것을 권장합니다.
     ```
   - AskUserQuestion으로 처리 방법 확인:
     ```yaml
     questions:
       - question: '기존 dataLayer.push 호출을 어떻게 처리할까요?'
         header: '기존 dataLayer.push 감지'
         options:
           - label: '무시하고 진행'
             description: '기존 호출은 그대로 두고 새 이벤트만 gtm-tracker로 추가합니다'
           - label: '파일 목록 확인'
             description: '기존 dataLayer.push 호출 위치를 먼저 확인합니다'
         multiSelect: false
     ```
   - 미발견 시 → 다음 단계로
5. project-config.md의 이벤트 파일 출력 경로 디렉토리 생성 (없으면)
6. project-config.md의 문서 출력 경로 디렉토리 확인

### Phase 1: 요구사항 수집

`$ARGUMENTS`에 CSV 경로가 있으면 해당 파일을 읽습니다.
없으면 AskUserQuestion으로 수집합니다.

```yaml
questions:
  - question: '이벤트 목록을 어떻게 제공하시겠습니까?'
    header: '입력 방식'
    options:
      - label: 'CSV 파일 경로 입력'
        description: '기획자에게 전달받은 CSV 문서 경로'
      - label: '기존 요구사항 문서(md) 경로 입력'
        description: '이전에 생성된 requirement.md 재사용'
      - label: '직접 입력'
        description: '대화형으로 이벤트 목록 입력'
    multiSelect: false
```

**중요**: 기존에 존재하는 과거 폴더의 요구사항 문서를 전달받으면, 해당 폴더에서 작업합니다.

### Phase 2: 파싱 + 사용자 승인

1. CSV 파싱 → 이벤트 추출 (페이지, 카테고리, 이벤트명, 설명, 파라미터)
2. project-config.md의 스킵 규칙 적용 → 스킵 대상 이벤트 필터링
3. 센터별 그룹핑 + 이벤트 파일 구성안 생성
4. Host App 공통 파라미터(project-config.md의 Host App 공통 변수) 식별 → 이벤트 params에서 제외
5. **유효 이벤트 0건 체크**: 스킵 후 남은 이벤트가 0건이면 → '모든 이벤트가 스킵 규칙에 해당합니다' 안내 + 스킵 사유 요약만 생성하고 Phase 3을 건너뛰어 Phase 4로 이동
6. 작업 범위를 사용자에게 제시하고 승인 요청

```yaml
questions:
  - question: '위 작업 범위로 진행할까요?'
    header: '작업 승인'
    options:
      - label: '승인, 진행'
        description: '위 범위대로 작업 시작'
      - label: '범위 수정'
        description: '일부 항목 제외/추가'
      - label: '취소'
        description: '작업 취소'
    multiSelect: false
```

7. 승인 후 → `${CLAUDE_PLUGIN_ROOT}/templates/requirement-template.md` 기반으로 requirement.md 생성

**산출물 저장 경로 결정** (이후 모든 산출물에 적용):
   - CSV 파일로 시작한 경우 → CSV가 있는 폴더를 작업 폴더로 사용
   - 기존 requirement.md 재사용 → 해당 requirement.md가 있는 폴더
   - 직접 입력 → project-config.md의 `문서 출력 경로`에 날짜 폴더 생성 (예: `{docs_output_path}/{YYYYMMDD}/`)

### Phase 3: 에이전트 순차 실행

**배칭**: 30개 초과 이벤트 → 센터별 배치로 분할. 30개 이하 → 단일 배치. 단일 센터가 30개 초과인 경우에도 분할하지 않는다. 배치는 반드시 순차 실행 (batch N 완료 → batch N+1). 각 배치마다 analyzer → implementer를 실행하고, 모든 배치 완료 후 verifier를 1회 실행.

**배치 파티셔닝 방법**: requirement.md의 이벤트를 센터(그룹) 단위로 분할한다. 예: da-center 이벤트 → batch 1, bm-center 이벤트 → batch 2. 각 배치의 analyzer 프롬프트에는 해당 센터의 이벤트만 포함하고, 다른 센터의 이벤트는 제외한다.

#### Step 3-1: Analyzer — Team 에이전트 (gtm-analyzer)

`${CLAUDE_PLUGIN_ROOT}/agents/gtm-analyzer.md`를 Team 에이전트 정의로 사용합니다.
사용자와 직접 소통이 가능한 **Team 에이전트**로 실행. 컴포넌트 매핑 모호성 등 모든 판단을 이 단계에서 사용자와 해결합니다.

모델 동적 선택 (TeamCreate의 model 파라미터로 frontmatter 기본값 오버라이드):

- 20개 이하 또는 단순 매핑 → `model: sonnet`
- 20개 초과 또는 복잡한 컴포넌트 구조 → `model: opus`

**프롬프트에 반드시 포함할 컨텍스트** (project-config.md에서 추출):
- requirement.md 경로
- analysis.json 저장 경로 (배치 모드: `analysis-batch-{N}.json`)
- gtm-tracker 모듈 경로 및 import alias
- React import 경로 (`{alias}/react`)
- Host App 공통 변수 목록
- 이벤트 파일 출력 경로 패턴
- 그룹 매핑 (센터, prefix, 라우트)
- 스킵 규칙

```
TeamCreate(
  name="gtm-analyzer",
  agentDef="${CLAUDE_PLUGIN_ROOT}/agents/gtm-analyzer.md",
  prompt="[위 컨텍스트 전체를 포함한 프롬프트]"
)
→ Team 에이전트가 사용자와 AskUserQuestion으로 질의응답
→ 결과: 모든 결정이 완료된 수정 계획 JSON (analysis.json)
```

Output: 이벤트별 컴포넌트 매핑 + 수정 계획 (구조화된 JSON 맵)

- 모든 `needsUserDecision` 항목이 사용자와 해결된 상태
- 결과를 작업 폴더에 저장 (단일 배치: `analysis.json`, 다중 배치: `analysis-batch-{N}.json`)

#### Step 3-2: Implementer — 서브에이전트 (gtm-implementer)

`${CLAUDE_PLUGIN_ROOT}/agents/gtm-implementer.md`를 서브에이전트 정의로 사용합니다.
사용자 상호작용 없이 **순수 실행기**로 동작하는 서브에이전트.

> 플러그인 에이전트는 name 기반으로 호출. subagent_type이 아닌 name 필드 사용.

```
Agent(name="gtm-implementer", model="sonnet", prompt="analysis.json 경로 + project-config.md의 import alias 경로")
```

Output: 변경된 파일 목록 + 요약

#### Step 3-3: Verifier — 서브에이전트 (gtm-verifier)

`${CLAUDE_PLUGIN_ROOT}/agents/gtm-verifier.md`를 서브에이전트 정의로 사용합니다.

```
Agent(name="gtm-verifier", model="opus", prompt="implementer 요약 + requirement.md 경로 + 작업 폴더 경로")
```

Output: pass 또는 gap_report

- gap_report인 경우 → implementer 재실행 (1회) → verifier 재실행
  - **2차 verifier도 gap_report면** → 남은 누락 항목을 사용자에게 보고하고 Phase 4로 진행
- 에러인 경우 → 사용자에게 보고

생성 문서 (작업 폴더):

- `event-coverage.md`: 이벤트 커버리지 검증 문서
- `integration-guide.md`: 개발자용 통합 가이드

### Phase 4: 결과 취합 + 문서 생성

project-config.md의 패키지 매니저 명령어로 타입 체크 + 테스트를 실행합니다.

타입 에러 시:
- import 경로 수정 후 재실행 (최대 2회)

테스트 실패 시:
- snapshot 불일치 → project-config.md의 스냅샷 업데이트 명령어로 업데이트
- 기타 에러 → 수정 후 재실행 (최대 2회)

#### result.md 생성

테스트 통과 후, `${CLAUDE_PLUGIN_ROOT}/templates/result-template.md` 기반으로 **구현 결과 문서**를 생성합니다.
작업 폴더에 `result.md`로 저장합니다.

- **담당자**: `git config user.name`으로 자동 채움
- **브랜치**: `git branch --show-current`로 자동 채움

이 문서는 기획자에게 전달하는 **최종 산출물**입니다. 다음을 포함해야 합니다:

1. **센터별 구현 현황**: 각 이벤트의 구현 상태 (완료 / 스킵), 이벤트명, 파일 위치
2. **스킵 항목**: 사유와 대안
3. **기획자 참고 사항**:
   - dataLayer에 push되는 실제 이벤트명 (prefix 포함)과 GTM 트리거 설정 가이드
   - Host App이 제공하는 공통 변수 목록
   - 이벤트별 파라미터 상세
4. **GTM 컨테이너 설정 가이드** (기획자가 직접 수행):
   - 데이터 영역 변수 생성 방법 (파라미터별)
   - 트리거 생성 방법 (개별 이벤트 또는 센터 단위 정규식)
   - GA4 이벤트 태그 생성 + prefix 자동 제거 (맞춤 자바스크립트 변수)
   - 이벤트 매개변수 연결 방법
   - GTM 미리보기로 검증하는 방법
5. **dataLayer 테스트 방법**: 브라우저 콘솔에서 확인하는 방법

사용자 확인 후 커밋 (`commit-with-format` 스킬 연계).

## 페이지 → 센터 매핑

`gtm-tag/project-config.md`의 '그룹 매핑' 섹션 참조

## CSV 포맷

`gtm-tag/project-config.md`의 CSV 헤더 포맷 참조. 포맷이 다르면 Phase 2에서 사용자에게 컬럼 매핑 확인.

`경로` 컬럼은 실제 라우트 경로를 포함하며, analyzer가 컴포넌트를 찾을 때 활용합니다.

### 파라미터 컬럼 포맷 (2가지)

CSV의 파라미터 컬럼은 두 가지 포맷이 혼용됨:

1. **콜론 형태**: `key: 설명, key2: 설명` — 광고운영/실행내역/규칙관리에서 사용
2. **파이프/bare 형태**: `key1|key2` 또는 `keyName` — 예산 모니터링에서 사용

두 포맷 모두 파싱 가능해야 함. `없음`이면 params 없는 이벤트.

## 이벤트 정의 규칙

1. **`defineEvents(prefix, schema)` 사용**: prefix는 센터별 팀 식별자 (da, bm 등)
2. **이벤트명 구조**: `{prefix}_{domain}_{action}` → GTM에서 prefix 제거하여 GA4 이벤트명으로 사용
3. **Host App 공통 파라미터 제외**: project-config.md의 Host App 공통 변수는 Host가 dataLayer에 push
4. **센터별 1파일**: project-config.md의 이벤트 파일 경로 패턴에 따라 생성
5. **타입 안전성**: params의 type과 required 정확히 정의
6. **기존 이벤트 파일 merge**: 기존 파일이 있으면 Read → 기존 defineEvents schema 파싱 → 새 이벤트 추가 (동일 key는 덮어쓰지 않음) → 전체 Write

## Rules

1. **기존 trackEvent 호출 절대 변경/삭제 금지**
2. **defineEvents prefix 필수**: 팀 간 네임스페이스 분리
3. **Host App 공통 변수는 이벤트 params에서 제외**
4. **모호하면 물어보기**: 추측하지 말고 AskUserQuestion 사용
5. **한 커밋 = 한 논리적 변경**: 관련 없는 변경은 분리 제안
6. **스킵 규칙**: project-config.md의 스킵 규칙 참조
7. **모듈 복사 시 `__tests__/` 제외**: 테스트 파일은 플러그인에만 존재

## 시그널 기록

이벤트(redo/tool_error/cancelled/clarify/correct/manual_fix/blocked) 발생 시 type+cause_type+cause_detail을 메모리에 누적한다.
스킬 종료 시 누적된 시그널을 아래 JSON 형식으로 Write(~/.claude/skill-doctor/tmp/sd-session-{timestamp}.json)로 저장한다:

```json
{
  "skill": "gtm-tag:tag",
  "skill_path": "${CLAUDE_PLUGIN_ROOT}/skills/tag/SKILL.md",
  "signals": [
    {"type": "correct", "context": "상황 설명", "action_taken": "조치", "cause_type": "ambiguous_instruction", "cause_detail": "구체적 원인"}
  ]
}
```

시그널이 없었으면 `"signals": []`(빈 배열)로 기록한다 — 정상 실행의 긍정적 데이터.

**원인 귀속**: 시그널의 원인이 스킬 결함인지 사용자 측 요인인지 판단하여 cause_type을 기록한다.
- **스킬 측** (CD 가산): ambiguous_instruction, missing_precondition, scope_exceeded, error_handling, output_mismatch
- **사용자 측** (CD 가산 안 함): insufficient_context, user_preference, external_issue
- **clarify**(질문)는 정상 동작이므로 CD +0.

### skill-doctor 연동

저장 후 skill-doctor CLI로 기록한다. **skill-doctor 미설치 시 안내 + init까지 진행**:

1. skill-doctor CLI 경로 탐색:
```bash
SD_CLI=$(ls -d ${CLAUDE_PLUGIN_ROOT}/../../skill-doctor/*/scripts/cli.py 2>/dev/null | tail -1)
```
> `CLAUDE_PLUGIN_ROOT`는 `~/.claude/plugins/cache/jake-plugins/gtm-tag/{version}/`으로 해석됨.
> glob `*/`로 skill-doctor 버전을 동적 탐색하여 버전 업그레이드에도 대응.

2. CLI 존재 확인:
```bash
python3 "$SD_CLI" list 2>/dev/null
```

3. **성공 시** (exit code 0): 정상 기록 + 진단
```bash
python3 "$SD_CLI" record --file <path>
```
cd_score ≥ 50이면:
```bash
python3 "$SD_CLI" diagnose --skill gtm-tag:tag
```
→ skill-doctor 서브에이전트를 호출하여 진단한다.

4. **실패 시** (command not found / exit code != 0): skill-doctor가 미설치
   - 사용자에게 안내:
   ```
   ⚠️ skill-doctor 플러그인이 설치되어 있지 않아 시그널 기록을 건너뜁니다.
   스킬 품질 추적을 위해 skill-doctor 설치를 권장합니다.
   ```
   - AskUserQuestion으로 설치 여부 질문:
   ```yaml
   questions:
     - question: 'skill-doctor를 설치하고 초기화할까요?'
       header: 'skill-doctor 미설치'
       options:
         - label: '설치 + 초기화'
           description: 'skill-doctor를 설치하고 /skill-doctor:init을 실행합니다'
         - label: '나중에'
           description: '시그널 기록 없이 계속합니다'
       multiSelect: false
   ```
   - "설치 + 초기화" 선택 시:
     - `/plugin install skill-doctor@jake-plugins` 안내
     - 설치 완료 후 `/skill-doctor:init` 실행
     - init 완료 후 시그널 기록 재시도
