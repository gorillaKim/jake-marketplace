---
name: session-devlog
description: 현재 세션 대화 내용을 분석하여 5카테고리 devlog 및 하네스 개선 제안을 생성하는 스킬. 작성 에이전트 모델명과 작업별 난이도도 기록합니다 (세션 기록, devlog, 오늘 작업, 세션 정리, 개발 일지, session-devlog)
---

# 세션 Devlog (Session Devlog)

현재 세션 대화 내용을 분석하여 5카테고리로 구조화된 devlog를 생성합니다.
작성에 사용된 에이전트 모델명과 각 작업의 난이도를 함께 기록합니다.

## 입력

```
/doxus:session-devlog
/doxus:session-devlog --type troubleshooting
/doxus:session-devlog --update docs/devlog/2026-03-20-xxx.md
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
| `troubleshooting` | 에러 해결, 버그 수정 패턴 | `docs/devlog/YYYY-MM-DD-{slug}.md` (tag: troubleshooting) |
| `decision` | 설계 선택, "A 대신 B로", 트레이드오프 논의 | `docs/architecture/decisions/NNN-{slug}.md` |
| `guide` | 설치/설정 방법, 반복 사용 절차 정리 | `docs/guides/{slug}.md` |
| `integration` | 외부 서비스 연동, API 사용법 | `docs/integrations/{slug}.md` |
| `context` | 비즈니스 배경, 프로덕트 방향 논의 | `docs/context/{slug}.md` |
| `techspec` | 컴포넌트/로직 명세, Props/API 인터페이스 설계 | `specs/{LogicName}/{LogicName}.spec.md` |

## 실행 절차

### Step 1: MCP / CLI 감지

→ `$CLAUDE_PLUGIN_ROOT/cli-reference.md` — "공통 패턴 > MCP / CLI / 설치 안내 3단계 감지" 절차를 따릅니다.

### Step 2: session-analyzer 스폰 (세션 분석 전담)

```
Agent(
  subagent_type: "doxus:session-analyzer",
  model: "sonnet",
  prompt: "현재 세션 대화를 분석하여 5카테고리 JSON을 반환하세요.
cwd: {현재 작업 디렉토리}
today: {YYYY-MM-DD}
plans_dir: .omc/plans/",
  description: "세션 분석"
)
```

session-analyzer가 반환하는 JSON:
```json
{
  "title": "세션 제목",
  "doc_type": "devlog",
  "main_tasks": [
    {"task": "작업 설명", "files_changed": ["path/to/file"], "difficulty": "medium", "outcome": "결과"}
  ],
  "issues": [
    {"description": "이슈 설명", "severity": "high", "resolved": true, "solution": "해결 방법"}
  ],
  "learnings": ["배운 사항 1", "배운 사항 2"],
  "improvements": ["개선할 점 1", "개선할 점 2"],
  "harness_suggestions": [
    {"type": "skill_candidate", "observation": "관찰 내용", "suggestion": "제안 내용", "evidence": "근거"}
  ],
  "plan_context": "관련 플랜 파일 요약 (있을 경우)",
  "search_failures": ["검색 실패한 쿼리 목록"]
}
```

**harness_suggestions 타입:**
- `skill_candidate`: 같은 작업이 3회 이상 반복 → 스킬/hook 자동화 제안
- `rule_candidate`: 자주 참조하는 문서/경로 → CLAUDE.md alias 또는 고정 참조 제안
- `unnecessary_call`: 단순 작업에 과도한 스킬/에이전트 호출 → 더 가벼운 대안 제안
- `optimization`: 직렬로 실행된 독립 작업 → 병렬 MCP 호출로 개선 제안

**plan → 문서 전환 기준:**

| 세션에서 이런 일이 있었다면 | → 문서 타입 |
|---|---|
| Props/API/인터페이스가 **확정**됐다 | `techspec` |
| A 대신 B 방식으로 가기로 **결정**됐다 | `decision` |
| 계획을 세우고 **구현**까지 완료됐다 | `devlog` |
| 계획만 세우고 구현은 **아직**이다 | 저장하지 않음 |

### Step 3: 분류 결과를 사용자에게 제안

```
AskUserQuestion(
  question: "📋 세션 분석 결과입니다.\n\n{분석 결과 요약}\n\n어떻게 진행할까요?",
  options: ["전체 생성", "devlog만", "개별 선택"]
)
```

검색 실패 흔적이 감지됐으면 별도로:
```
AskUserQuestion(
  question: "검색이 잘 안됐던 문서들이 있습니다. alias를 추가할까요?\n\n{문서별 alias 제안}",
  options: ["전체 추가", "개별 선택", "건너뜀"]
)
```

### Step 4: 문서 생성 (docsmith-writer 스폰)

```
Agent(
  subagent_type: "doxus:docsmith-writer",
  model: "sonnet",
  prompt: "프로젝트 경로: {cwd}. doxus 프로젝트 ID: {id}.
세션 분석 결과: {session-analyzer JSON}
문서 타입: {type}
파일 경로: {file_path}
현재 날짜: {YYYY-MM-DD}
작성 에이전트 모델: {session-analyzer JSON의 agent_model 값 — 하드코딩 금지, 실행 시점 모델 ID 사용}
템플릿 경로: $CLAUDE_PLUGIN_ROOT/templates/session-devlog.md

5카테고리(주요작업/이슈/배운점/개선할점/하네스 개선 제안)를 모두 채우세요.
각 주요작업에는 난이도(difficulty)를 함께 기록하세요.
기존 파일이 있으면 append 모드로 병합하세요.",
  description: "session devlog 작성"
)
```

### Step 5: 후처리

1. 재인덱싱: `MODE=mcp` → `doxus_index_project(name=<PROJECT>)` / `MODE=cli` → `doxus index`
2. 결과 보고 (저장 경로 + tags + aliases)

## --update 모드

1. 기존 파일 Read
2. 오늘 날짜 섹션(`## YYYY-MM-DD`) 존재 여부 확인
   - 없으면 새 날짜 섹션 append
   - 있으면 해당 섹션에 내용 merge
3. `updated` frontmatter 갱신

## 규칙

- 디폴트 타입은 `devlog`
- decision 타입은 반드시 사용자 확인 후 생성
- 세션 내용을 과장하거나 없는 내용 추가 금지 (대화에서 확인된 사실만)
- 한 세션에 작업이 적으면 기존 당일 devlog에 append 제안
