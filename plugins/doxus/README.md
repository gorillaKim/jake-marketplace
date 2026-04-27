# doxus 플러그인

프로젝트 코드베이스를 분석하여 필요한 문서를 자동 생성하고 관리하는 플러그인.
doxus 검색 엔진과 연동하여 하이브리드 검색, 세션 기반 devlog 자동 생성을 지원합니다.

## 스킬

| 스킬 | 호출 | 역할 |
|------|------|------|
| **onboard** | `/doxus:onboard` | 프로젝트 분석 → 인터뷰 → 문서 세트 생성 |
| **add** | `/doxus:add <type> "제목"` | 개별 문서 추가 (devlog, decision 등) |
| **doctor** | `/doxus:doctor` | 문서 상태 진단 (누락, 오래됨, 불일치) |
| **librarian** | `/doxus:librarian <질의>` | 문서 검색/관리/발견성 개선 |
| **retro** | `/doxus:retro` | 주간 회고 자동 생성 |
| **session-devlog** | `/doxus:session-devlog` | 세션 대화 → 5카테고리 devlog + 하네스 개선 제안 |

## 에이전트

| 에이전트 | 역할 | 모델 |
|----------|------|------|
| docsmith-analyzer | 프로젝트 분석 + 사용자 인터뷰 | sonnet |
| docsmith-writer | 실제 문서 작성 | sonnet |
| librarian | 문서 검색/관리 사서 | haiku |
| session-analyzer | 세션 분석 → 5카테고리 + 하네스 제안 | sonnet |
| retro-coordinator | 주간 회고 파이프라인 조율 | sonnet |
| retro-gatherer | 기간별 문서 수집 → JSON | sonnet |
| retro-writer | JSON → 회고 문서 | sonnet |

## obsidian-nexus에서 마이그레이션하는 경우

> 이 섹션은 obsidian-nexus 사용자를 위한 마이그레이션 가이드입니다. 신규 사용자는 건너뛰세요.

1. MCP prefix 변경: `nexus_*` → `doxus_*`
2. session-devlog 5카테고리 확장: 주요작업 / 이슈 / 배운점 / 개선할점 / 하네스 개선 제안
3. 작성 에이전트 모델명 + 작업별 난이도 자동 기록
4. session-analyzer 에이전트 신설 (하네스 분석 전담)
5. doxus 전용 도구 활용: `doxus_agent_summary`, `doxus_create_document`, `doxus_get_freshness_report`
