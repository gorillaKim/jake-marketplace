---
name: ui-test
description: |
  번들된 Playwright MCP 로 대상 URL/화면의 UI 를 실제 브라우저에서 검증하는 스킬.
  ui-qa-reviewer 서브에이전트를 spawn 해 스크린샷·접근성 스냅샷·인터랙션을 spec 대비 검증한다.
  Engram 트래킹과 함께 쓰면 결과를 이슈 note 로 남긴다. 트리거 — "ui 테스트", "UI 검증",
  "화면 검증", "ui 리뷰", "ui-test".
tools:
  - Agent
  - AskUserQuestion
  - mcp__engram__issue_get
  - mcp__engram__note_add
  - Read
  - Bash
---

# UI Test

번들 Playwright MCP 를 이용해 화면을 실제 브라우저로 검증한다.

## 전제

- 이 플러그인은 `playwright` MCP 서버를 **번들**한다(`.mcp.json`). 플러그인 활성화 시 자동 시작되므로 별도 `claude mcp add` 불필요.
- 전제 조건: 사용자 머신에 **node/npx**. 연결이 안 되면 `onboard` 스킬의 "Playwright MCP 전제 점검" 안내 참조.
- `/mcp` 에 `playwright` 서버가 보이지 않으면: `node -v` / `npx -v` 확인 후 `/reload-plugins`.

## 입력 정리

1. **대상**: 검증할 URL 또는 라우트 (예: `http://localhost:3000/...`). 없으면 사용자에게 질의.
2. **spec**: 무엇을 확인할지(레이아웃/모달/반응형/인터랙션 등). 연관 Engram 이슈가 있으면 `issue_get` 으로 goal·description·context note 에서 도출.
3. **연관 이슈**(선택): `issue_id`.

## 실행

```
Agent(subagent_type='engram-orchestrator:ui-qa-reviewer',
      prompt="target_url=<URL>, spec=<검증 항목 배열>, issue_id=<N|생략>, project_key=<P>, viewport=...")
```

- 반환 `status`:
  - `REVIEWED` → `verdict`(PASS/FAIL)와 passed/failed 를 사용자에게 보고. `issue_id` 있으면 결과를 note 로 기록:
    - PASS → `note_add(type="context", summary="[UI REVIEW] PASS ...")`
    - FAIL → `note_add(type="caveat", summary="[UI REVIEW] FAIL ...")`
  - `LOGIN_REQUIRED` / `SKIPPED_LOGIN_REQUIRED` → 사용자에게 "대상 페이지 로그인 필요" 안내. 사용자가 로그인 가능하면 로그인 완료 후 ui-qa-reviewer 재spawn, 불가하면 UI 검증 보류로 마무리.
  - `ERRORED` → 사유 보고(연결/URL 문제 등).

## 보고 형식

```
[ui-test] <target_url> — verdict: PASS | FAIL
  passed: <N>건
  failed:
    - <U-2> 360px footer 버튼 모달 밖 (screenshot: <path>)
  (issue #<N> 에 결과 note 기록함 / 또는 트래킹 없음)
```

## 금지

- 자격 증명 직접 입력/요구 금지 — 로그인은 사용자가 직접(ui-qa-reviewer 가 요청).
- demo→finished 등 상태 전이 금지(사용자 전용).
