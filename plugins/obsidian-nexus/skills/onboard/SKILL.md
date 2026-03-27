---
name: onboard
description: 프로젝트 코드베이스를 분석하여 필요한 문서를 카테고리별로 자동 생성하는 온보딩 스킬 (문서 온보딩, doc-onboard, 문서 생성, 문서 초기화, docs 생성, 프로젝트 문서, 문서 셋업)
---

# 문서 온보딩 (Doc Onboard)

프로젝트 코드베이스를 분석하여 부족한 문서를 파악하고, 인터뷰를 거쳐 카테고리별 docs/ 폴더에 문서를 자동 생성합니다.

## 입력

- `args`: 없으면 현재 프로젝트, 경로를 지정하면 해당 프로젝트 분석
- `--cleanup`: 기존 문서 태그/aliases/폴더 정리만 실행 (신규 문서 생성 없음)

예시:
```
/obs-nexus:onboard
/obs-nexus:onboard ~/projects/my-app
/obs-nexus:onboard --cleanup
```

## 생성되는 docs/ 구조

```
docs/
├── overview/          # 프로젝트 전체 그림
│   ├── project-summary.md    [필수]
│   ├── tech-stack.md         [필수]
│   └── glossary.md           [필수]
├── architecture/      # 코드 설계
│   ├── module-map.md         [필수]
│   ├── data-flow.md
│   └── decisions/
├── integrations/      # 외부 연동
├── guides/            # 실용 가이드
│   ├── getting-started.md    [필수]
│   ├── common-tasks.md
│   └── release.md
├── devlog/            # 개발 일지 (상시 축적)
└── context/           # 비즈니스 컨텍스트
```

## 실행 절차

### Step 0: MCP / CLI 감지

→ `$CLAUDE_PLUGIN_ROOT/cli-reference.md` — "공통 패턴 > MCP / CLI / 설치 안내 3단계 감지" 절차를 따릅니다.

### Step 0.5: on-config.json 초기화

`docs/on-config.json`이 없으면 자동 생성합니다:

1. `docs/` 폴더가 없으면 먼저 생성
2. `docs/on-config.json` 존재 여부 확인
3. 없으면 프로젝트 디렉토리명(basename)으로 생성:
   ```json
   {"name": "{project_name}"}
   ```
4. 생성 시 알림: `on-config.json 생성됨 → docs/on-config.json`
5. 이미 존재하면 덮어쓰지 않고 진행

### Step 1: 기존 문서 정리 (--cleanup 플래그 시)

`--cleanup` 인자가 있으면 신규 문서 생성 없이 기존 문서 정리만 실행합니다:

```
Agent(
  subagent_type: "obs-nexus:docsmith-analyzer",
  model: "sonnet",
  prompt: "프로젝트 경로: {cwd}. obs-nexus 설치 여부: {yes/no}. nexus 프로젝트 ID: {id}. Phase 0만 실행하세요. 기존 문서의 태그/aliases 보완 및 폴더 이동을 진행하세요.",
  description: "docsmith 기존 문서 정리"
)
```

정리 완료 후 종료합니다 (Step 2~3 건너뜀).

### Step 2: 프로젝트 분석 (docsmith-analyzer 스폰)

```
Agent(
  subagent_type: "obs-nexus:docsmith-analyzer",
  model: "sonnet",
  prompt: "프로젝트 경로: {cwd}. obs-nexus 설치 여부: {yes/no}. nexus 프로젝트 ID: {id}. Phase 1~3을 실행하세요. 프로젝트를 분석하고, 갭 리포트를 작성하고, 사용자 인터뷰를 진행하세요.",
  description: "docsmith 프로젝트 분석"
)
```

analyzer가 반환하는 정보:
- 생성할 문서 목록 (카테고리/파일명/제목)
- 각 문서의 대상 독자와 상세도
- 기존 태그 목록

### Step 3: 문서 생성 (docsmith-writer 스폰)

analyzer 결과를 바탕으로 카테고리별 writer를 스폰합니다.
독립적인 카테고리는 **병렬 실행** 가능합니다:

```
# 병렬 가능: overview, architecture, guides 등
Agent(
  subagent_type: "obs-nexus:docsmith-writer",
  model: "sonnet",
  prompt: "프로젝트 경로: {cwd}. nexus 프로젝트 ID: {id}.
생성할 문서:
- docs/overview/project-summary.md (제목: 프로젝트 개요, 독자: 개발자)
- docs/overview/tech-stack.md (제목: 기술 스택, 독자: 개발자)
- docs/overview/glossary.md (제목: 용어 사전, 독자: 전체)
기존 태그 목록: [...]
템플릿 경로: $CLAUDE_PLUGIN_ROOT/templates/overview.md",
  description: "docsmith overview 문서 작성"
)
```

### Step 4: 후처리

1. obs-nexus 연동 시: `obs-nexus index <PROJECT>`로 재인덱싱
2. 생성 결과 요약 보고:
```
문서 온보딩 완료!

생성된 문서:
  docs/on-config.json ✅ (신규 생성 시)
  docs/overview/project-summary.md ✅
  docs/overview/tech-stack.md ✅
  docs/overview/glossary.md ✅
  docs/architecture/module-map.md ✅
  docs/guides/getting-started.md ✅

다음 단계:
  - /obs-nexus:add devlog "제목" 으로 개발 일지를 추가하세요
  - /obs-nexus:doctor 로 문서 상태를 점검하세요
```

## 규칙

- 필수 문서 5개는 반드시 생성 권장 (사용자가 제외하지 않는 한)
- 기존 docs/ 가 있으면 기존 문서를 존중하고 중복 생성하지 않음
- frontmatter의 tags, aliases, created/updated 는 반드시 완전하게 채움
- 아키텍처 문서에는 Mermaid 다이어그램 적극 활용
- 문서 말미에 `## 관련 문서` 섹션에 위키링크 포함
- `on-config.json`이 이미 존재하면 덮어쓰지 않음
