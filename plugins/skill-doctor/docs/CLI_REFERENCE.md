# skill-doctor CLI Reference

CLI 경로: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py`

모든 커맨드는 auto-init 내장 (DB 없으면 자동 생성).

데이터 저장 경로: `~/.claude/skill-doctor/` (플러그인 재설치해도 데이터 유지)

---

## `record --file <path>`

세션 시그널을 DB에 기록합니다.

```bash
python3 .../cli.py record --file /tmp/sd-session-20260317.json
```

**입력**: JSON 파일 (필수: `skill`, `signals` 배열. 선택: `skill_path` — 스킬 파일 경로. 빈 배열 허용)
**출력**: `{"session_id": "20260317-143022-a1b2", "cd_score": 65}`
**부수효과**: project 자동 감지, 90일 cleanup, 입력 파일 삭제

**CD 점수 계산 참고**:
- `clarify` = +0 (질문은 정상 동작)
- 사용자 측 cause_type(`insufficient_context`, `user_preference`, `external_issue`)의 시그널은 CD에 가산되지 않음
- 스킬 측 cause_type만 CD에 가산됨

---

## `list [--all-projects]`

기록된 스킬 목록을 조회합니다.

```bash
python3 .../cli.py list                # 현재 프로젝트만
python3 .../cli.py list --all-projects # 전체 프로젝트
```

**출력**: JSON 배열 (skill, project, health_score, total_sessions, last_session, source, plugin_name)

---

## `diagnose --skill <name> [--session <id>] [--all-projects] [--full]`

스킬의 진단 데이터를 JSON으로 출력합니다.

```bash
python3 .../cli.py diagnose --skill e2e-testid                          # 최근 세션 자동 선택
python3 .../cli.py diagnose --skill e2e-testid --session 20260317-a1b2  # 특정 세션
python3 .../cli.py diagnose --skill e2e-testid --full                   # 전체 signals 포함
python3 .../cli.py diagnose --skill e2e-testid --all-projects           # 전체 프로젝트 통합
```

**출력**: skill, project, source, plugin_name + profile + current_session + cross_session (cause_type_counts, cause_type_details, avg_cd_last_3) + heal_tracking (active, previous_heals)
**--session 생략**: 해당 스킬의 가장 최근 세션 자동 선택
**--full**: 최근 5세션의 전체 signals 추가 포함

---

## `update-profile --skill <name> --health-score <N> [--resolve <cause_type>] [--dismiss <cause_type>] [--heal-tracking <json>] [--fail-heal <heal_id>] [--confirm-heal <heal_id>]`

스킬 프로파일을 업데이트합니다.

```bash
python3 .../cli.py update-profile --skill e2e-testid --health-score 72
python3 .../cli.py update-profile --skill e2e-testid --health-score 85 --resolve ambiguous_instruction
python3 .../cli.py update-profile --skill e2e-testid --health-score 72 --dismiss scope_exceeded
python3 .../cli.py update-profile --skill e2e-testid --health-score 85 --resolve ambiguous_instruction --heal-tracking '{"heal_id":"20260317-a1b2","cause_types":["ambiguous_instruction"],"verify_after_sessions":3,"diff_summary":"복합 변경 분류 규칙 추가"}'
python3 .../cli.py update-profile --skill e2e-testid --health-score 60 --fail-heal "20260317-a1b2"
python3 .../cli.py update-profile --skill e2e-testid --health-score 90 --confirm-heal "20260317-a1b2"
```

**--resolve**: 해결된 cause_type을 resolved 목록에 추가 (diagnose에서 제외됨)
**--dismiss**: 30일간 해당 cause_type 에스컬레이션 억제
**--heal-tracking**: skill-healer가 생성한 heal 추적 메타데이터 JSON을 저장 (status: "observing")
**--fail-heal**: 지정된 heal_id의 상태를 "failed"로 변경 + resolved_issues에서 해당 cause_type 제거 (재발 감지 가능)
**--confirm-heal**: 지정된 heal_id의 상태를 "confirmed"로 변경 (3세션 이상 재발 없음 확인 시)

> 사용자 측 cause_type(`insufficient_context`, `user_preference`, `external_issue`)은 resolve/dismiss 대상이 아닙니다. 이들은 에스컬레이션에 포함되지 않으므로 별도 처리가 불필요합니다.

---

## `discover-marketplace [--prune]`

설치된 마켓플레이스 플러그인에서 스킬을 자동 발견하여 DB에 등록합니다.

```bash
python3 .../cli.py discover-marketplace           # 스킬 발견 및 등록
python3 .../cli.py discover-marketplace --prune    # + 삭제된 플러그인의 스킬 정리
```

**동작**:
1. `~/.claude/plugins/installed_plugins.json` 읽기
2. 각 플러그인의 `{installPath}/skills/*/SKILL.md` 스캔
3. `skill_profiles`에 `source='marketplace'`, `plugin_name`, `skill_path` upsert

**출력**: `{"discovered": N, "skills": [{"skill": "name", "plugin": "key", "project": "...", "path": "..."}]}`
**--prune**: `installed_plugins.json`에 없는 플러그인의 marketplace 스킬을 DB에서 삭제. 추가 출력: `"pruned": N`

> 마켓플레이스 스킬은 진단(diagnose)은 가능하지만, 수정(heal)은 불가합니다. 외부 플러그인은 읽기 전용이므로 리포트만 축적됩니다.
