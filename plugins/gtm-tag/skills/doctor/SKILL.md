---
name: doctor
description: gtm-tag 설정 및 모듈 상태를 진단하고 문제를 자동 수정합니다. project-config 누락, 모듈 불완전, Provider 미설정, import 경로 불일치 등을 검출합니다. (gtm-tag 진단, gtm 문제, gtm doctor, gtm 체크, gtm 상태, config 확인)
---

# gtm-tag Doctor

gtm-tag 플러그인의 설정, 모듈, Provider, import 경로 등을 진단하고 문제를 자동 수정합니다.

## Input

- `$ARGUMENTS`: 빈 값이면 전체 진단, `--fix`면 자동 수정 모드

## 실행 절차

### 1. project-config.md 진단

`gtm-tag/project-config.md` 파일을 확인한다.

**Check 1.1 — 파일 존재**
```
Read gtm-tag/project-config.md
```
- 없으면: ❌ `CONFIG_MISSING` — init 스킬 실행 필요
- 있으면: 다음 체크로

**Check 1.2 — 플레이스홀더 잔존**
파일 내용에서 `{`와 `}`로 감싼 플레이스홀더 패턴을 검색:
```
Grep pattern="\{[a-z_]+\}" path=gtm-tag/project-config.md
```
- 발견되면: ⚠️ `CONFIG_PLACEHOLDER` — init이 불완전하게 실행됨
- 없으면: ✅

**Check 1.3 — 필수 섹션 존재**
다음 섹션 헤더가 모두 존재하는지 확인:
- `## gtm-tracker 모듈`
- `## 이벤트 파일 출력 경로`
- `## 앱 루트`
- `## Host App 공통 변수` (부분 일치 허용: 괄호 부연설명이 있어도 통과)
- `## 패키지 매니저`
- `## 문서 출력 경로`
- `## 그룹 매핑`
- `## CSV 헤더 포맷`

누락된 섹션이 있으면: ⚠️ `CONFIG_INCOMPLETE` — 해당 섹션 보충 필요

### 2. gtm-tracker 모듈 진단

project-config.md에서 모듈 경로를 추출한다.

**Check 2.1 — 모듈 디렉토리 존재**
```
Glob pattern="{모듈경로}/index.ts"
```
- 없으면: ❌ `MODULE_MISSING` — 모듈 미설치

**Check 2.2 — 필수 파일 완전성**
다음 파일들이 모두 존재하는지 확인:
```
필수 파일:
  - index.ts
  - tracker.ts
  - registry.ts
  - types.ts
  - validation.ts
  - global.d.ts
  - react/index.ts
  - react/provider.tsx
  - react/hooks.ts
```
```
Glob pattern="{모듈경로}/**/*.{ts,tsx}"
```
- 누락 파일 있으면: ⚠️ `MODULE_INCOMPLETE` — 누락 파일 목록 제시

**Check 2.3 — 핵심 export 확인**
```
Grep pattern="export.*createTracker" path={모듈경로}/tracker.ts
Grep pattern="export.*defineEvents" path={모듈경로}/registry.ts
Grep pattern="export.*useTrackEvent" path={모듈경로}/react/hooks.ts
Grep pattern="export.*GTMTrackerProvider" path={모듈경로}/react/provider.tsx
```
- 누락되면: ❌ `MODULE_CORRUPTED` — 해당 파일이 변형됨

### 3. import 경로 진단

**Check 3.1 — tsconfig/jsconfig paths 매칭**
project-config.md의 import alias를 tsconfig.json (또는 jsconfig.json)의 `paths` 또는 `baseUrl`과 대조.
tsconfig.json이 없으면 jsconfig.json을 확인한다. `extends` 필드가 있으면 부모 config도 확인한다.
```
Read tsconfig.json → compilerOptions.paths, compilerOptions.baseUrl 확인
```
- import alias가 tsconfig paths에 없으면: ❌ `IMPORT_PATH_MISMATCH` — tsconfig 또는 config 수정 필요

**Check 3.2 — 실제 import 사용 확인**
프로젝트 내 기존 `defineEvents`, `useTrackEvent` import가 config의 alias와 일치하는지:
```
Grep pattern="from ['\"].*gtm-tracker" glob="*.{ts,tsx}"
```
- 불일치 있으면: ⚠️ `IMPORT_INCONSISTENT` — 실제 사용 경로와 config 불일치

### 4. Provider 진단

**Check 4.1 — GTMTrackerProvider 존재**
project-config.md의 앱 루트 파일에서:
```
Grep pattern="GTMTrackerProvider" path={앱루트파일}
```
- 없으면: ❌ `PROVIDER_MISSING` — Provider 미설정

**Check 4.2 — createTracker 인스턴스 존재**
```
Grep pattern="createTracker" path={앱루트파일}
```
- 없으면: ❌ `TRACKER_MISSING` — tracker 인스턴스 미생성

**Check 4.3 — 중복 Provider 검사**
```
Grep pattern="GTMTrackerProvider" glob="src/**/*.tsx"
```
- 2개 이상이면: ⚠️ `PROVIDER_DUPLICATE` — 중복 Provider 발견

### 5. 이벤트 파일 진단

**Check 5.1 — 이벤트 디렉토리 존재**
```
Glob pattern="{이벤트경로}/*.events.ts"
```
- 디렉토리 없으면: ⚠️ `EVENTS_DIR_MISSING` — 아직 이벤트 생성 전이면 정상

**Check 5.2 — 이벤트 파일 TypeScript 유효성** (이벤트 파일이 있는 경우)
```bash
{타입체크명령어} 2>&1 | grep -i "events"
```
- 타입 에러 있으면: ❌ `EVENTS_TYPE_ERROR` — 이벤트 정의 파일 타입 에러

### 6. 그룹 매핑 일관성 진단

**Check 6.1 — prefix 중복 검사**
project-config.md의 그룹 매핑 테이블에서 같은 prefix가 다른 그룹에 사용되는지:
- 중복 있으면: ⚠️ `PREFIX_COLLISION` — prefix 네임스페이스 충돌

**Check 6.2 — 라우트 경로 유효성**
그룹 매핑의 라우트 경로가 실제 프로젝트 라우트 파일에 존재하는지:
```
Grep pattern="{각 라우트 경로}" glob="src/**/*.{ts,tsx}"
```
- 없으면: ⚠️ `ROUTE_NOT_FOUND` — 라우트 경로가 변경되었을 수 있음

### 7. raw dataLayer.push 감지

**Check 7.1 — gtm-tracker 미사용 직접 호출**
gtm-tracker 모듈 내부를 제외하고, 프로젝트 소스에서 `dataLayer.push(` 직접 호출을 검색:
```
Grep pattern="dataLayer\.push\(" glob="src/**/*.{ts,tsx}"
```
gtm-tracker 모듈 경로의 파일은 결과에서 제외한다.
- 발견되면: ⚠️ `RAW_DATALAYER_PUSH` — gtm-tracker를 거치지 않는 직접 dataLayer.push 호출 {N}건. 이벤트 중복/추적 누락 위험. 마이그레이션 권장.
- 없으면: ✅

---

## 진단 결과 출력

모든 체크 완료 후, 결과를 테이블로 출력:

```
## gtm-tag 진단 결과

| # | 항목 | 상태 | 코드 | 설명 |
|---|------|------|------|------|
| 1.1 | project-config.md 존재 | ✅/❌ | CONFIG_MISSING | ... |
| 1.2 | 플레이스홀더 잔존 | ✅/⚠️ | CONFIG_PLACEHOLDER | ... |
| 1.3 | 필수 섹션 완전성 | ✅/⚠️ | CONFIG_INCOMPLETE | ... |
| 2.1 | 모듈 디렉토리 | ✅/❌ | MODULE_MISSING | ... |
| 2.2 | 모듈 파일 완전성 | ✅/⚠️ | MODULE_INCOMPLETE | ... |
| 2.3 | 핵심 export | ✅/❌ | MODULE_CORRUPTED | ... |
| 3.1 | tsconfig paths | ✅/❌ | IMPORT_PATH_MISMATCH | ... |
| 3.2 | import 일관성 | ✅/⚠️ | IMPORT_INCONSISTENT | ... |
| 4.1 | Provider 존재 | ✅/❌ | PROVIDER_MISSING | ... |
| 4.2 | Tracker 인스턴스 | ✅/❌ | TRACKER_MISSING | ... |
| 4.3 | Provider 중복 | ✅/⚠️ | PROVIDER_DUPLICATE | ... |
| 5.1 | 이벤트 디렉토리 | ✅/⚠️ | EVENTS_DIR_MISSING | ... |
| 5.2 | 이벤트 타입 체크 | ✅/❌ | EVENTS_TYPE_ERROR | ... |
| 6.1 | prefix 중복 | ✅/⚠️ | PREFIX_COLLISION | ... |
| 6.2 | 라우트 유효성 | ✅/⚠️ | ROUTE_NOT_FOUND | ... |
| 7.1 | raw dataLayer.push | ✅/⚠️ | RAW_DATALAYER_PUSH | ... |

총 {N}개 항목 | ✅ {통과} | ⚠️ {경고} | ❌ {에러}
```

---

## 자동 수정 (`--fix` 모드 또는 사용자 승인)

진단 결과에 ❌ 또는 ⚠️가 있으면, 자동 수정 가능 여부를 판단하고 AskUserQuestion으로 수정 승인을 요청한다.

### 자동 수정 가능 항목

| 코드 | 수정 방법 | 신뢰도 |
|------|----------|--------|
| `CONFIG_MISSING` | `/gtm-tag:init` 실행 안내 | — (init 위임) |
| `CONFIG_PLACEHOLDER` | AskUserQuestion으로 빈 값 수집 → config 업데이트 | HIGH |
| `CONFIG_INCOMPLETE` | 누락 섹션을 template에서 복사 + AskUserQuestion으로 값 수집 | HIGH |
| `MODULE_MISSING` | `${CLAUDE_PLUGIN_ROOT}/module/` → config 경로에 복사 | HIGH |
| `MODULE_INCOMPLETE` | 누락 파일만 `${CLAUDE_PLUGIN_ROOT}/module/`에서 복사 | HIGH |
| `MODULE_CORRUPTED` | 해당 파일을 `${CLAUDE_PLUGIN_ROOT}/module/`에서 덮어쓰기 (사용자 확인 필요) | MEDIUM |
| `IMPORT_PATH_MISMATCH` | tsconfig.json에 paths 추가 또는 config의 alias 수정 | MEDIUM |
| `IMPORT_INCONSISTENT` | 기존 import 경로를 config 기준으로 통일 | MEDIUM |
| `PROVIDER_MISSING` | 앱 루트에 Provider + tracker 인스턴스 삽입 | HIGH |
| `TRACKER_MISSING` | 앱 루트에 createTracker 호출 추가 | HIGH |
| `PROVIDER_DUPLICATE` | 중복 Provider 위치를 보여주고 사용자에게 제거 요청 | LOW (수동) |
| `EVENTS_DIR_MISSING` | 디렉토리 생성 (`mkdir -p`) | HIGH |
| `EVENTS_TYPE_ERROR` | tsc 에러 메시지를 분석하여 수정 시도 | MEDIUM |
| `PREFIX_COLLISION` | 사용자에게 수정 요청 (자동 수정 불가) | LOW (수동) |
| `ROUTE_NOT_FOUND` | 사용자에게 경고만 (라우트 변경 확인 필요) | LOW (정보) |
| `RAW_DATALAYER_PUSH` | 발견 위치 목록 제시 + 마이그레이션 안내 | LOW (정보) |

### 수정 승인 플로우

```yaml
questions:
  - question: '위 {N}개 항목을 자동 수정할까요?'
    header: '자동 수정'
    options:
      - label: '전체 수정'
        description: '모든 자동 수정 가능 항목을 수정합니다'
      - label: '항목별 선택'
        description: '각 항목을 하나씩 확인하고 선택적으로 수정합니다'
      - label: '수정 안 함'
        description: '진단 결과만 확인합니다'
    multiSelect: false
```

### 수정 실행

승인된 항목을 순서대로 수정:
1. CONFIG 관련 수정 (1.x)
2. MODULE 관련 수정 (2.x)
3. IMPORT 관련 수정 (3.x)
4. PROVIDER 관련 수정 (4.x)
5. EVENTS 관련 수정 (5.x)

각 수정 후 해당 체크를 재실행하여 수정 성공 확인.

---

## 수정 후 재진단

모든 수정 완료 후, 전체 진단을 재실행하여 최종 상태를 확인:

```
## gtm-tag 재진단 결과

| 항목 | 이전 | 현재 |
|------|------|------|
| ... | ❌ | ✅ |
| ... | ⚠️ | ✅ |

{수정 건수}개 항목 수정 완료.
```

---

## 다음 단계 추천

```yaml
questions:
  - question: '진단이 완료되었습니다. 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: 'tag — 이벤트 태깅 시작'
        description: '모든 설정이 정상이면 태깅을 시작합니다'
      - label: 'init — 설정 재초기화'
        description: '설정을 처음부터 다시 합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

## 시그널 기록

이벤트(redo/tool_error/cancelled/clarify/correct/manual_fix/blocked) 발생 시 type+cause_type+cause_detail을 메모리에 누적한다.
스킬 종료 시 누적된 시그널을 아래 JSON 형식으로 Write(~/.claude/skill-doctor/tmp/sd-session-{timestamp}.json)로 저장한다:

```json
{
  "skill": "gtm-tag:doctor",
  "skill_path": "${CLAUDE_PLUGIN_ROOT}/skills/doctor/SKILL.md",
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
python3 "$SD_CLI" diagnose --skill gtm-tag:doctor
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
