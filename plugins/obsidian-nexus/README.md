# obs-nexus 플러그인

프로젝트 코드베이스를 분석하여 필요한 문서를 자동 생성하고 관리하는 플러그인.

## 스킬

| 스킬 | 호출 | 역할 |
|------|------|------|
| **onboard** | `/obs-nexus:onboard` | 프로젝트 분석 → 인터뷰 → 문서 세트 생성 |
| **add** | `/obs-nexus:add <type> "제목"` | 개별 문서 추가 (devlog, decision 등) |
| **doctor** | `/obs-nexus:doctor` | 문서 상태 진단 (누락, 오래됨, 불일치) |
| **librarian** | `/obs-nexus:librarian <질의>` | 문서 검색/관리/발견성 개선 |
| **session-devlog** | `/obs-nexus:session-devlog` | 세션 대화 → devlog 및 문서 자동 생성 |

## 생성되는 docs/ 구조

```
docs/
├── overview/          # 프로젝트 전체 그림
├── architecture/      # 코드 설계, ADR
├── integrations/      # 외부 서비스 연동
├── guides/            # 실용 가이드
├── devlog/            # 개발 일지 (상시 축적)
└── context/           # 비즈니스 컨텍스트
```

## obs-nexus CLI 연동

obs-nexus가 설치되어 있으면 자동으로 활용합니다:
- `obs-nexus search` — 기존 문서 검색, 중복 방지
- `obs-nexus doc list` — 태그 분포 파악, 태그 재사용
- `obs-nexus doc meta` — frontmatter 점검
- `obs-nexus index` — 문서 생성 후 즉시 재인덱싱

설치: `brew tap gorilla-kim/tap && brew install obs-nexus`

## 에이전트

| 에이전트 | 역할 | 모델 |
|----------|------|------|
| docsmith-analyzer | 프로젝트 분석 + 사용자 인터뷰 | sonnet |
| docsmith-writer | 실제 문서 작성 | sonnet |
| librarian | 문서 검색/관리 사서 | haiku |
