---
name: onboard
description: 프로젝트 코드베이스를 분석하여 필요한 문서를 카테고리별로 자동 생성하는 온보딩 스킬 (문서 온보딩, doc-onboard, 문서 생성, 문서 초기화, docs 생성, 프로젝트 문서, 문서 셋업)
---

# 문서 온보딩 (Doc Onboard)

프로젝트 코드베이스를 분석하여 부족한 문서를 파악하고, 인터뷰를 거쳐 카테고리별 docs/ 폴더에 문서를 자동 생성합니다.

## 입력

```
/doxus:onboard
/doxus:onboard ~/projects/my-app
/doxus:onboard --cleanup
```

## 생성되는 docs/ 구조

```
docs/
├── overview/          # project-summary.md [필수], tech-stack.md [필수], glossary.md [필수]
├── architecture/      # module-map.md [필수], decisions/
├── guides/            # getting-started.md [필수]
├── integrations/
├── devlog/
├── context/
specs/             # {LogicName}/{LogicName}.spec.md  ← docs/ 외부, 프로젝트 루트 기준
```

## 실행 절차

### Step 0: MCP / CLI 감지

→ `$CLAUDE_PLUGIN_ROOT/cli-reference.md` — "공통 패턴 > MCP / CLI / 설치 안내 3단계 감지" 절차를 따릅니다.

### Step 0.5: on-config.json 초기화

`docs/on-config.json`이 없으면 프로젝트명(basename)으로 자동 생성:
```json
{"name": "{project_name}"}
```
> 이 파일은 docsmith-analyzer/writer가 문서 생성 시 프로젝트명 참조용으로 읽습니다.

### Step 1: 기존 문서 정리 (--cleanup 플래그 시)

```
Agent(
  subagent_type: "doxus:docsmith-analyzer",
  model: "sonnet",
  prompt: "프로젝트 경로: {cwd}. doxus 프로젝트 ID: {id}. Phase 0만 실행하세요.",
  description: "docsmith 기존 문서 정리"
)
```

정리 완료 후 종료.

### Step 2: 프로젝트 분석 (docsmith-analyzer 스폰)

```
Agent(
  subagent_type: "doxus:docsmith-analyzer",
  model: "sonnet",
  prompt: "프로젝트 경로: {cwd}. doxus 설치 여부: {yes/no}. doxus 프로젝트 ID: {id}. Phase 1~3을 실행하세요.",
  description: "docsmith 프로젝트 분석"
)
```

### Step 3: 문서 생성 (docsmith-writer 병렬 스폰)

독립적인 카테고리는 병렬 실행:
```
Agent(
  subagent_type: "doxus:docsmith-writer",
  model: "sonnet",
  prompt: "프로젝트 경로: {cwd}. doxus 프로젝트 ID: {id}.
생성할 문서: {analyzer 결과}
기존 태그 목록: [...]
템플릿 경로: $CLAUDE_PLUGIN_ROOT/templates/overview.md",
  description: "docsmith 문서 작성"
)
```

### Step 4: 후처리

재인덱싱 후 결과 보고: `MODE=mcp` → `doxus_index_project(name=<PROJECT>)` / `MODE=cli` → `doxus index`

## 규칙

- 필수 문서 5개는 반드시 생성 권장 (사용자가 제외하지 않는 한)
- 기존 docs/ 가 있으면 중복 생성하지 않음
- frontmatter tags, aliases, created/updated 반드시 완전하게 채움
- on-config.json이 이미 존재하면 덮어쓰지 않음
