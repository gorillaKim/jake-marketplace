---
name: sprint-retro
description: |
  스프린트 회고 문서를 자동 생성하는 트리거 스킬. engram-retro 에이전트를 spawn 하여
  전체 이슈 분석 → 회고 마크다운 생성 → 파일 저장을 일괄 처리한다.
  트리거 키워드: "회고", "retro", "retrospective", "스프린트 리뷰", "sprint-retro",
               "회고 문서", "retro 생성", "이번 스프린트 정리".
---

# sprint-retro

## 목적

지정된 스프린트 (또는 가장 최근 스프린트) 의 모든 이슈를 분석하여 회고 문서를 생성한다.

- 완료/미완료/취소 이슈 분류
- decision / discovery / blocker / caveat 노트 수집
- 액션 아이템 자동 도출
- Markdown 문서 저장

## 트리거

다음 발화 시 자동 실행:

- `"회고해줘"` / `"회고 문서 만들어줘"` / `"retro"`
- `"스프린트 리뷰"` / `"이번 스프린트 정리해줘"`
- `"retrospective"` / `"sprint-retro"`
- `"retro 생성"` / `"회고 돌려줘"`
- `"/engram-orchestrator:sprint-retro"`

## 실행 방법

### 현재(최근) 스프린트 회고

```
/engram-orchestrator:sprint-retro
```

또는 자연어:
```
"회고해줘"
"이번 스프린트 회고 문서 만들어줘"
"retro 돌려줘"
```

### 특정 스프린트 회고

```
/engram-orchestrator:sprint-retro sprint_id=<N>
```

또는 자연어:
```
"스프린트 3 회고해줘"
"지난 스프린트 retro"
```

### 저장 경로 지정

```
/engram-orchestrator:sprint-retro output_path=docs/retro/sprint-2-retro.md
```

## 동작 흐름

```
[사용자 트리거]
      │
      ▼
[sprint-retro 스킬]
      │  project_key 결정 + sprint_id 결정
      ▼
[engram-retro 에이전트 spawn]
      │
      ├── Step A: 스프린트 확정
      │     sprint_current / sprint_list → finished 또는 active 스프린트 선택
      │
      ├── Step B: 이슈 전체 수집 (병렬)
      │     issue_list(sprint_id) → 각 이슈별 issue_get + history_for + note_list
      │
      ├── Step C: 노트 분석
      │     decision / discovery / blocker_detail / caveat 추출
      │     블로킹 빈도 순위 · 반복 caveat 패턴 · 액션 아이템 도출
      │
      ├── Step D: 문서 생성 + 저장
      │     AskUserQuestion(저장 경로, output_path 미명시 시)
      │     Write(path, markdown)
      │
      └── Step E: 요약 보고
            완료 N / 미완료 M / 액션 J개 요약
```

## project_key 결정 절차

```
Bash("git config --get remote.origin.url") → repo 이름 추출
session_restore()                           → 활성 프로젝트 매칭
```

매칭 실패 시:
```
AskUserQuestion("어느 프로젝트의 회고를 생성할까요?")
```

## 생성 문서 구조

회고 문서는 다음 9개 섹션으로 구성된다:

1. **스프린트 요약** — 전체/완료/미완료/취소 이슈 수치 + 완료율
2. **완료된 것 (Done)** — finished 이슈 목록
3. **미완료 (Not Done)** — working/ready 이슈 목록
4. **주요 결정 (Decisions)** — decision note 전체
5. **발견·배운 것 (Discoveries)** — discovery note 전체
6. **블로커 분석 (Blockers)** — blocker_detail + 빈도 순위
7. **반복 주의사항** — 2+ 회 등장 caveat 패턴
8. **재발 방지 항목** — 패턴 → 개선 제안
9. **다음 스프린트 액션 아이템** — 이월/선행해결/프로세스개선

## 출력 예시

### 보고 요약

```
[retro] 스프린트 'engram 만들기' 회고 완료

완료: 8건 / 미완료: 2건 / 취소: 1건 (완료율 72%)
주요 결정: 5건
발견·배운 것: 7건
블로커: 3건 (해소 2건 / 미해소 1건)
액션 아이템: 4건

저장 위치: docs/retro/sprint-2-retro.md
```

### 생성 문서 샘플 (섹션 1~2)

```markdown
# Sprint Retro — engram 만들기

> 기간: 2026-05-10 ~ 2026-05-24
> 스프린트 목표: engram 완성하기
> 생성일: 2026-05-19
> 생성: engram-retro@afb591c8

---

## 1. 스프린트 요약

| 항목 | 수치 |
|------|------|
| 전체 이슈 | 11 |
| 완료 (finished) | 8 |
| 사용자 검토 대기 (demo) | 0 |
| 미완료 (working/ready) | 2 |
| 취소 (cancelled) | 1 |
| 완료율 | 72% |

---

## 2. 완료된 것 (Done)

| # | 제목 | 에픽 | 우선순위 |
|---|------|------|---------|
| #20 | engram-analyzer 에이전트 작성 | engram-orchestrator 확장 | high |
| #21 | engram-leader v0.4.0 Hybrid 패턴 적용 | engram-orchestrator 확장 | high |
...
```

## 주의사항

- 이슈 상태 전이 금지 — retro 에이전트는 **읽기 전용**.
- 파일 Write 전 반드시 저장 경로 확인 (`output_path` 미명시 시 `AskUserQuestion`).
- MCP 연결 실패 시 서버 재시작 안내 → CLI fallback 제안 (note #93 참조).
- 활성 스프린트 회고 시: "스프린트가 아직 진행 중입니다. 중간 회고로 진행할까요?" 확인.
