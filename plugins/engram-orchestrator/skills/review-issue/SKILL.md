---
name: review-issue
description: |
  demo 상태 이슈를 코드 레벨에서 검토하는 트리거 스킬. engram-reviewer 에이전트를
  spawn 하여 LGTM 또는 CHANGES_REQUESTED 를 판정한다.
  트리거 키워드: "리뷰", "review", "코드 리뷰", "검토", "demo 검토", "review-issue",
               "lgtm", "승인", "변경요청".
---

# review-issue

## 목적

`demo` 상태 이슈를 코드 레벨에서 검토하고 승인/변경요청을 판정한다.

- **승인 (LGTM)**: `context` note 기록 후 사용자에게 `finished` 안내.
- **변경요청 (CHANGES_REQUESTED)**: `caveat` note 기록 + 이슈 `working` 환원.

> **UI 이슈 자동 검증**: 검토 대상이 UI 성격(레이아웃/모달/반응형 등) + 검증 URL 이 확보되면 engram-reviewer 가 번들된 Playwright MCP 로 `ui-qa-reviewer` 를 spawn 해 실제 브라우저 검증을 수행하고, 그 PASS/FAIL 을 판정에 종합한다. 로그인이 필요한 페이지는 사용자에게 로그인을 요청한다.

## 트리거

다음 발화 시 자동 실행:

- `"리뷰해줘"` / `"코드 리뷰"` / `"review"` / `"review-issue"`
- `"demo 검토"` / `"demo 이슈 확인"`
- `"LGTM 확인"` / `"승인해줘"` / `"변경요청"`
- `"/engram-orchestrator:review-issue"`

## 실행 방법

### 단일 이슈 검토

```
/engram-orchestrator:review-issue issue_id=<N>
```

또는 자연어:
```
"이슈 #128 리뷰해줘"
"#128 코드 검토"
```

### 전체 demo 이슈 일괄 검토 (batch)

```
/engram-orchestrator:review-issue
```

또는 자연어:
```
"demo 이슈 전부 리뷰해줘"
"코드 리뷰 돌려줘"
"검토 한 번 해줘"
```

## 동작 흐름

```
[사용자 트리거]
      │
      ▼
[review-issue 스킬]
      │  project_key 결정 (git remote 또는 session_restore)
      │  issue_id 파싱 (명시 / 생략)
      │
      ▼
[폴링 여부 질문]  ← AskUserQuestion
      │
      ├── 일회성 검토
      │     ▼
      │   [engram-reviewer 에이전트 spawn]
      │     ├── Step A: 컨텍스트 수집
      │     │     session_restore + issue_get (또는 epic별 issue_list)
      │     ├── Step B: 코드 검토
      │     │     context note 읽기 → 변경 파일 Read → git diff 확인
      │     ├── Step C: 판정 체크리스트
      │     │     task 완료 / test 통과 / 코드 실재 / 패턴 일관성 / 사이드이펙트
      │     └── Step D: 결과 기록
      │           LGTM → note_add(context, "LGTM") + 사용자 안내
      │           CHANGES_REQUESTED → note_add(caveat) + issue_release(ready|working)
      │
      └── 폴링 모드
            ▼
          /loop 10m /engram-orchestrator:review-issue project_key=<key>
          (10분마다 batch 검토 자동 반복)
```

## 폴링 모드

`project_key` 결정 직후, **반드시** 실행 방식을 먼저 질문한다:

```
AskUserQuestion(
  "리뷰 실행 방식을 선택하세요",
  options=[
    "일회성 검토 (지금 한 번만 실행)",
    "폴링 모드 (10분마다 demo 이슈 자동 검토)"
  ]
)
```

**일회성**: 기존처럼 engram-reviewer 에이전트를 즉시 spawn.

**폴링 모드**:
- 다음 명령을 실행한다:
  ```
  /loop 10m /engram-orchestrator:review-issue project_key=<key>
  ```
- 루프는 10분마다 batch 검토를 반복하며, demo 이슈가 없으면 "검토할 항목 없음" 로그만 남긴다.
- 중단하려면 `/oh-my-claudecode:cancel` 을 입력한다.

> ⚠️ 폴링 모드는 단일 이슈 지정(`issue_id=N`)과 함께 사용 불가 — batch 전용.

## project_key 결정 절차

스킬 진입 시 `project_key` 가 명시되지 않은 경우:

```
Bash("git config --get remote.origin.url") → repo 이름 추출
session_restore(mode="agent")               → 활성 프로젝트 목록에서 매칭 (오리엔테이션 → mode='agent')
```

매칭 실패 시:
```
AskUserQuestion("어느 프로젝트의 demo 이슈를 검토할까요?")
```

## 출력 예시

### 단일 이슈 LGTM

```
[reviewer] #128 'JWT 갱신 로직 추가' — LGTM

체크리스트:
  task 완료: ✓ (required 0개)
  test 통과: ✓ (5/5 checked)
  코드 실재: ✓ (src/auth/jwt.ts)
  패턴 일관성: ✓
  사이드이펙트: ✓

검토 의견: 이슈 설명 대로 구현됨. 토큰 만료 처리 엣지케이스 테스트 포함 확인.

다음 단계: 데스크톱 칸반에서 #128 을 demo → finished 로 이동하여 종결하세요.
```

### 단일 이슈 CHANGES_REQUESTED

```
[reviewer] #129 '결제 콜백 처리' — CHANGES_REQUESTED

실패 항목:
  - test 통과: ✗ (2개 unchecked)
  - 코드 실재: ✗ (src/payment/callback.ts 파일 없음)

요청 사항:
  - callback.ts 구현 완료 후 task_test_check 처리
  - 오류 응답(400) 케이스 테스트 추가

이슈 → working 환원 완료. 워커 재처리 후 demo 재진입 필요.
```

### batch 완료

```
[reviewer] batch 검토 완료 (jake-marketplace)

승인 (LGTM): 2건
  - #128 'JWT 갱신 로직 추가'
  - #131 '사용자 프로필 캐싱'

변경요청 (CHANGES_REQUESTED): 1건
  - #129 '결제 콜백 처리' — test 미완료, 파일 누락

demo 상태 이슈 없음: 0건
```

## 주의사항

- `demo → finished` 전이는 **사용자 전용**. reviewer 는 절대 시도하지 않음.
- reviewer 는 이슈를 `claim` 하지 않음 — `issue_release` 권한 오류 시 `force=true` 사용.
- CHANGES_REQUESTED 복귀 상태는 blocker/심각도 기준으로 `ready` 또는 `working` 자동 결정.
- 폴링 모드 중단: `/oh-my-claudecode:cancel` 또는 루프 종료 커맨드 사용.
- 폴링 모드는 단일 이슈 지정(`issue_id=N`)과 함께 사용 불가 — batch 전용.
- MCP 연결 실패 시 서버 재시작 안내 → CLI fallback 제안 (note #93 참조).
