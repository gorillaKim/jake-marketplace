---
name: session-devlog
description: 현재 세션 대화 내용을 분석하여 devlog 및 적합한 문서 타입으로 분류·생성하는 스킬. 디폴트는 devlog 기록 (세션 기록, devlog, 오늘 작업, 세션 정리, 개발 일지, session-devlog)
---

# 세션 Devlog (Session Devlog)

현재 세션 대화 내용을 분석하여 오늘 한 작업을 문서로 기록합니다.
디폴트는 `devlog`이며, 내용에 따라 더 적합한 문서 타입을 감지하면 사용자에게 제안합니다.

## 입력

```
/obs-nexus:session-devlog
/obs-nexus:session-devlog --type troubleshooting
/obs-nexus:session-devlog --update docs/devlog/2026-03-20-xxx.md
```

| 인자 | 설명 |
|------|------|
| (없음) | 세션 분석 후 타입 자동 제안, 디폴트 devlog |
| `--type <type>` | 타입 강제 지정 |
| `--update <path>` | 기존 문서에 append 모드로 업데이트 |

## 문서 타입 분류 기준

| 타입 | 감지 신호 | 저장 위치 |
|------|----------|----------|
| `devlog` | 일반 개발 작업, 기능 추가, 리팩토링 | `docs/devlog/YYYY-MM-DD-{slug}.md` |
| `troubleshooting` | 에러 해결, 버그 수정, "안 됐는데 해결" 패턴 | `docs/devlog/YYYY-MM-DD-{slug}.md` (tag: troubleshooting) |
| `decision` | 설계 선택, "A 대신 B로", 트레이드오프 논의 | `docs/architecture/decisions/NNN-{slug}.md` |
| `guide` | 설치/설정 방법, 반복 사용 절차 정리 | `docs/guides/{slug}.md` |
| `integration` | 외부 서비스 연동, API 사용법 | `docs/integrations/{slug}.md` |
| `context` | 비즈니스 배경, 프로덕트 방향 논의 | `docs/context/{slug}.md` |

## 실행 절차

### Step 1: obs-nexus 감지

→ `$CLAUDE_PLUGIN_ROOT/cli-reference.md` — "공통 패턴 > nexus 감지" 절차를 따릅니다.

### Step 2: 세션 내용 분석

현재 대화 컨텍스트에서 다음을 추출합니다:

**추출 항목:**
- 오늘 수행한 작업 목록 (기능 추가, 수정, 설정 등)
- 발생한 문제와 해결 방법
- 내린 설계 결정과 이유
- 새로 학습한 사항, 참고한 외부 자료

**분류 로직:**
1. 주 내용이 무엇인지 판단 (작업 vs 문제해결 vs 설계결정 vs 절차)
2. 하나의 세션에 여러 타입이 섞여 있으면 **분리 저장** 제안
3. 애매하면 `devlog`로 처리 (디폴트)

### Step 3: 분류 결과를 사용자에게 제안

다음 형식으로 보고합니다:

```
📋 세션 내용 분석 결과

[devlog로 기록] — 기본 저장 항목
  파일: docs/devlog/2026-03-20-obs-nexus-개선.md
  내용: docsmith-analyzer Phase 0 추가, .gitignore 설정, CCG 평가 진행
  tags: [devlog, feature]

[별도 문서 제안]
  ⚡ decision: "사서 에이전트 Phase 0 onboard에서 --cleanup으로 분리"
     → docs/architecture/decisions/NNN-cleanup-flag-separation.md
     이유: 설계 결정 사항이며 향후 참고 가치가 높습니다

모두 생성할까요? 특정 항목을 제외하거나 타입을 바꾸고 싶으면 말씀해 주세요.
[1] 전체 생성  [2] devlog만  [3] 개별 선택
```

사용자가 명시적으로 응답하지 않으면 **[1] 전체 생성**으로 진행합니다.

### Step 4: 문서 생성 (docsmith-writer 스폰)

승인된 항목별로 writer 에이전트를 스폰합니다:

```
Agent(
  subagent_type: "obs-nexus:docsmith-writer",
  model: "sonnet",
  prompt: "프로젝트 경로: {cwd}. nexus 프로젝트 ID: {id}.
세션에서 추출한 내용:
{extracted_content}

문서 타입: {type}
파일 경로: {file_path}
현재 날짜: {YYYY-MM-DD}
기존 태그 목록: [...]
템플릿 경로: $CLAUDE_PLUGIN_ROOT/templates/devlog.md

세션 대화 내용을 바탕으로 작업 내용을 구체적으로 작성하세요.
코드 변경이 있으면 핵심 변경사항을 포함하세요.
기존 파일이 있으면 update 모드(append)로 병합하세요.",
  description: "session devlog 작성"
)
```

### Step 5: 후처리

1. obs-nexus 연동 시: `obs-nexus index <PROJECT>` 재인덱싱
2. 결과 보고:
```
✅ 세션 devlog 저장 완료!

  docs/devlog/2026-03-20-obs-nexus-개선.md
    tags: [devlog, feature]
    aliases: [obs-nexus-개선, 옵시디언 넥서스 개선]

  docs/architecture/decisions/005-cleanup-flag-separation.md
    tags: [decision, architecture]
```

## --update 모드

기존 devlog 파일에 오늘 내용을 추가할 때:

1. 기존 파일 Read
2. 오늘 날짜 섹션(`## YYYY-MM-DD`) 존재 여부 확인
   - 없으면 새 날짜 섹션 append
   - 있으면 해당 섹션에 내용 merge
3. `updated` frontmatter 갱신

## 규칙

- 디폴트 타입은 `devlog` — 판단이 애매하면 devlog로 처리
- decision 타입은 반드시 사용자 확인 후 생성 (설계 결정은 돌이키기 어려움)
- 세션 내용을 과장하거나 없는 내용을 추가하지 않음 (대화에서 확인된 사실만)
- 한 세션에 작업이 적으면 기존 당일 devlog에 append 제안
