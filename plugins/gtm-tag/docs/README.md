# GTM Tag — 워크플로우 & 아키텍처

## 파일 구조

```
plugins/gtm-tag/
├── .claude-plugin/
│   └── plugin.json                ← 플러그인 메타데이터
├── skills/
│   ├── init/SKILL.md              ← /gtm-tag:init (프로젝트 초기화)
│   ├── tag/SKILL.md               ← /gtm-tag:tag (오케스트레이터 Phase 0~4)
│   └── doctor/SKILL.md            ← /gtm-tag:doctor (설정 진단 + 자동 수정)
├── agents/
│   ├── gtm-analyzer.md            ← Team 에이전트 (sonnet/opus, 사용자 소통)
│   ├── gtm-implementer.md         ← Sub 에이전트 (sonnet, 코드 수정)
│   └── gtm-verifier.md            ← Sub 에이전트 (opus, 검증)
├── templates/
│   ├── project-config-template.md ← project-config 기본 템플릿
│   ├── requirement-template.md    ← 요구사항 문서 포맷
│   └── result-template.md         ← 결과 문서 포맷 (기획자 전달용)
├── module/                        ← gtm-tracker 모듈 번들
│   ├── index.ts, tracker.ts, registry.ts, types.ts, validation.ts, global.d.ts
│   ├── react/ (provider.tsx, hooks.ts, index.ts)
│   └── __tests__/ (프로젝트 복사 시 제외)
├── docs/
│   └── README.md                  ← 이 파일
└── README.md                      ← 플러그인 개요 + 사용법
```

## 프로젝트 설정 경로

```
{프로젝트 루트}/gtm-tag/project-config.md
```

> `.claude/` 하위가 아닌 프로젝트 루트의 `gtm-tag/` 폴더에 저장됩니다.

## 전체 워크플로우

```mermaid
flowchart TD
    A[Phase 0: Init] --> B[Phase 1: 입력 수집]
    B --> C[Phase 2: 파싱 + 승인]
    C -->|승인| D[Phase 3: 에이전트 파이프라인]
    C -->|이벤트 0건| S[스킵 요약만 생성]
    C -->|취소| Z[종료]

    subgraph Phase3 [Phase 3: 에이전트 파이프라인]
        D --> E{30개 초과?}
        E -->|Yes| F[센터별 배치 분할]
        E -->|No| G[단일 배치]
        F --> H
        G --> H

        subgraph Batch [배치 N]
            H[gtm-analyzer<br/>Team 에이전트] -->|analysis.json| I[gtm-implementer<br/>Sub 에이전트]
        end

        I --> J{다음 배치?}
        J -->|Yes| H
        J -->|No| K[gtm-verifier<br/>Sub 에이전트]
        K --> L{결과}
        L -->|pass| M[Phase 4]
        L -->|gap_report| I2[implementer 재실행 1회]
        I2 --> K2[verifier 재실행]
        K2 -->|pass| M
        K2 -->|gap_report| RPT[사용자에게 보고 → Phase 4]
        L -->|error| ERR[사용자에게 보고]
    end

    S --> M2[Phase 4]
    M[Phase 4] --> N[타입 체크 + 테스트]
    N --> O[result.md 생성]
    O --> P[커밋]
```

## 에이전트 역할

```mermaid
flowchart LR
    subgraph Analyzer [gtm-analyzer — Team]
        A1[CSV 파싱]
        A2[컴포넌트 탐색]
        A3[사용자 질의]
        A4[analysis.json]
        A1 --> A2 --> A3 --> A4
    end

    subgraph Implementer [gtm-implementer — Sub]
        I1[이벤트 파일 생성]
        I2[Provider 설정]
        I3[trackEvent 삽입]
        I1 --> I2 --> I3
    end

    subgraph Verifier [gtm-verifier — Sub]
        V1[커버리지 검증]
        V2[import/참조 검증]
        V3[문서 생성]
        V1 --> V2 --> V3
    end

    Analyzer -->|analysis.json| Implementer
    Implementer -->|변경 요약| Verifier
```

### Analyzer 프롬프트 필수 컨텍스트 (8개)

오케스트레이터가 project-config.md에서 추출하여 전달:

1. requirement.md 경로
2. analysis.json 저장 경로 (배치 모드: `analysis-batch-{N}.json`)
3. gtm-tracker 모듈 경로 및 import alias
4. React import 경로 (`{alias}/react`)
5. Host App 공통 변수 목록
6. 이벤트 파일 출력 경로 패턴
7. 그룹 매핑 (센터, prefix, 라우트)
8. 스킵 규칙

### 에이전트 호출 패턴

```
# Team 에이전트 (사용자 소통 가능)
TeamCreate(name="gtm-analyzer", agentDef="${CLAUDE_PLUGIN_ROOT}/agents/gtm-analyzer.md", ...)

# Sub 에이전트 (순수 실행)
Agent(name="gtm-implementer", model="sonnet", ...)
Agent(name="gtm-verifier", model="opus", ...)
```

> 플러그인 에이전트는 `name` 기반으로 호출. `subagent_type`이 아닌 `name` 필드 사용.

## 배칭 로직

- 30개 이하 → 단일 배치
- 30개 초과 → 센터(그룹) 단위로 분할
- 단일 센터가 30개 초과여도 분할하지 않음
- 배치는 순차 실행 (batch N 완료 → batch N+1)
- 각 배치: analyzer → implementer
- 전체 완료 후: verifier 1회

## 데이터 흐름

```
CSV (기획자 제공)
  → requirement.md          (Phase 2: 파싱 + 승인)
  → analysis.json           (Analyzer: 컴포넌트 매핑)
  → {group}.events.ts       (Implementer: 이벤트 정의 파일)
  → 컴포넌트 수정            (Implementer: trackEvent 삽입)
  → event-coverage.md       (Verifier: 커버리지 검증)
  → integration-guide.md    (Verifier: 통합 가이드)
  → result.md               (Phase 4: 기획자 전달용 최종 산출물)
```

## Doctor 진단 체크리스트

| # | 카테고리 | 항목 | 에러 코드 |
|---|---------|------|----------|
| 1.1 | Config | 파일 존재 | CONFIG_MISSING |
| 1.2 | Config | 플레이스홀더 잔존 | CONFIG_PLACEHOLDER |
| 1.3 | Config | 필수 섹션 (8개) | CONFIG_INCOMPLETE |
| 2.1 | Module | 디렉토리 존재 | MODULE_MISSING |
| 2.2 | Module | 필수 파일 (9개) | MODULE_INCOMPLETE |
| 2.3 | Module | 핵심 export | MODULE_CORRUPTED |
| 3.1 | Import | tsconfig/jsconfig paths | IMPORT_PATH_MISMATCH |
| 3.2 | Import | import 일관성 | IMPORT_INCONSISTENT |
| 4.1 | Provider | GTMTrackerProvider 존재 | PROVIDER_MISSING |
| 4.2 | Provider | createTracker 인스턴스 | TRACKER_MISSING |
| 4.3 | Provider | 중복 검사 | PROVIDER_DUPLICATE |
| 5.1 | Events | 디렉토리 존재 | EVENTS_DIR_MISSING |
| 5.2 | Events | TypeScript 유효성 | EVENTS_TYPE_ERROR |
| 6.1 | Group | prefix 중복 | PREFIX_COLLISION |
| 6.2 | Group | 라우트 유효성 | ROUTE_NOT_FOUND |

