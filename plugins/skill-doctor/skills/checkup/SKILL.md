---
name: checkup
description: skill-doctor 자체의 환경 문제를 진단하고 자동 수정 (checkup, 환경 점검, 설정 문제, skill-doctor 안돼, 오류, 에러, setup check, 환경 진단)
---

# skill-doctor 환경 점검 (checkup)

skill-doctor의 설치 상태, 설정, DB 무결성을 점검하고 발견된 문제를 자동으로 수정한다.

CLI 경로: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py`

## 실행 절차

### 1. 환경 점검 항목 수집

아래 항목을 순서대로 점검한다. 각 항목의 결과를 `pass` / `warn` / `fail`로 기록한다.

#### 1.1 Python 실행 가능 여부
```bash
python3 --version
```
- pass: 버전 출력됨 (3.6+)
- fail: command not found 또는 3.6 미만

#### 1.2 데이터 디렉토리 존재
```bash
ls -d ~/.claude/skill-doctor ~/.claude/skill-doctor/tmp ~/.claude/skill-doctor/reports 2>&1
```
- pass: 3개 디렉토리 모두 존재
- fail: 누락된 디렉토리 있음 → **자동 수정**: `mkdir -p ~/.claude/skill-doctor/{tmp,reports}`

#### 1.3 DB 연결 및 스키마 확인
```bash
python3 -c "
import sqlite3, json
db = sqlite3.connect(str(__import__('pathlib').Path.home() / '.claude/skill-doctor/skill-doctor.db'))
db.row_factory = sqlite3.Row
tables = [r[0] for r in db.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()]
required = {'sessions', 'signals', 'skill_profiles'}
missing = required - set(tables)
if missing:
    print(json.dumps({'status': 'fail', 'missing_tables': list(missing)}))
else:
    # 컬럼 점검
    cols = [r[1] for r in db.execute('PRAGMA table_info(skill_profiles)').fetchall()]
    required_cols = {'skill','project','skill_path','health_score','heal_tracking','source','plugin_name'}
    missing_cols = required_cols - set(cols)
    if missing_cols:
        print(json.dumps({'status': 'warn', 'missing_columns': list(missing_cols)}))
    else:
        print(json.dumps({'status': 'pass', 'tables': tables, 'columns': cols}))
db.close()
"
```
- pass: 테이블 3개 + 필수 컬럼 모두 존재
- warn: 컬럼 누락 → **자동 수정**: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py list` 실행 (마이그레이션 트리거)
- fail: 테이블 누락 → **자동 수정**: 위와 동일 (get_db()가 CREATE TABLE IF NOT EXISTS 실행)

#### 1.4 DB 데이터 무결성
```bash
python3 -c "
import sqlite3, json, pathlib
db = sqlite3.connect(str(pathlib.Path.home() / '.claude/skill-doctor/skill-doctor.db'))
issues = []
# 고아 시그널 확인
orphans = db.execute('SELECT COUNT(*) FROM signals WHERE session_id NOT IN (SELECT id FROM sessions)').fetchone()[0]
if orphans > 0:
    issues.append({'type': 'orphan_signals', 'count': orphans})
# 깨진 JSON 필드 확인
for row in db.execute('SELECT skill, project, resolved_issues, dismissed_issues, heal_tracking FROM skill_profiles').fetchall():
    for i, col in enumerate(['resolved_issues', 'dismissed_issues', 'heal_tracking']):
        try:
            json.loads(row[i+2] or '[]')
        except:
            issues.append({'type': 'malformed_json', 'skill': row[0], 'project': row[1], 'column': col})
if issues:
    print(json.dumps({'status': 'warn', 'issues': issues}))
else:
    print(json.dumps({'status': 'pass'}))
db.close()
"
```
- pass: 무결성 OK
- warn: 고아 시그널 → **자동 수정**: 고아 레코드 삭제
- warn: 깨진 JSON → **자동 수정**: 해당 필드를 `'[]'`로 리셋

#### 1.5 CLAUDE_PLUGIN_ROOT 환경 변수
```bash
echo "${CLAUDE_PLUGIN_ROOT:-__NOT_SET__}"
```
- pass: 경로가 출력되고 해당 경로에 `scripts/cli.py`가 존재
- fail: `__NOT_SET__` 출력 → 플러그인 환경 밖에서 실행 중. 수동 수정 필요 안내.

#### 1.6 Hook 시그널 수집 상태
```bash
ls "${CLAUDE_PLUGIN_ROOT}/hooks/hooks.json" 2>/dev/null && echo "HOOKS_OK" || echo "HOOKS_MISSING"
```
- pass: `hooks/hooks.json` 존재
- fail: 파일 없음 → 플러그인 재설치 필요 안내

```bash
ls ~/.claude/skill-doctor/active/ 2>/dev/null | head -5
```
- pass: active 세션 파일 존재 (hook이 동작 중)
- warn: 파일 없음 (아직 시그널이 수집되지 않았거나 hook이 동작하지 않음)

#### 1.7 CLAUDE.md 보조 시그널 설정 (선택)
프로젝트 루트의 `.claude/CLAUDE.md` 파일을 Read 도구로 확인:
- `<!-- skill-doctor -->` 마커 존재 여부 확인
- pass: 마커 존재 (보조 수집 활성)
- info: 마커 없음 — hook 기반 자동 수집은 동작 중. 보조 수집은 `/skill-doctor:init`에서 선택 가능

#### 1.8 마켓플레이스 발견 상태
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py discover-marketplace 2>&1
```
- pass: discovered > 0
- warn: discovered = 0 (설치된 플러그인에 스킬이 없음)
- fail: installed_plugins.json 미존재 → 마켓플레이스 플러그인 미설치 안내

### 2. 자동 수정 실행

점검 결과에 `fail` 또는 `warn`이 있으면 자동 수정을 실행한다:

| 문제 | 수정 방법 |
|------|----------|
| 디렉토리 누락 | `mkdir -p ~/.claude/skill-doctor/{tmp,reports}` |
| 테이블/컬럼 누락 | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py list` (DB 자동 마이그레이션) |
| 고아 시그널 | `python3 -c "import sqlite3, pathlib; db=sqlite3.connect(str(pathlib.Path.home()/'.claude/skill-doctor/skill-doctor.db')); db.execute('DELETE FROM signals WHERE session_id NOT IN (SELECT id FROM sessions)'); db.commit(); db.close()"` |
| 깨진 JSON 필드 | `python3 -c "..."` 로 해당 필드 '[]'로 리셋 |
| Hook 파일 없음 | 플러그인 재설치 안내 |
| CLAUDE.md 보조 미설정 | 선택사항 — `/skill-doctor:init`에서 추가 가능 안내 |

자동 수정 후 해당 항목을 다시 점검하여 `fixed` 상태로 업데이트한다.

### 3. 점검 리포트 표시

```
## 🩺 skill-doctor 환경 점검 결과

| 항목 | 상태 | 비고 |
|------|------|------|
| Python3 | ✅ pass | 3.x.x |
| 데이터 디렉토리 | ✅ pass | |
| DB 스키마 | 🔧 fixed | source, plugin_name 컬럼 추가됨 |
| DB 무결성 | ✅ pass | |
| CLAUDE_PLUGIN_ROOT | ✅ pass | /path/to/plugin |
| Hook 시그널 수집 | ✅ pass | hooks.json 존재 |
| CLAUDE.md 보조 | ℹ️ info | 선택사항 |
| 마켓플레이스 발견 | ✅ pass | 16개 스킬 발견 |

상태: ✅ pass | 🔧 fixed (자동 수정됨) | ⚠️ warn (수동 조치 필요) | ❌ fail (치명적)
```

### 4. 다음 단계 추천

점검 결과에 따라 AskUserQuestion 도구로 다음 단계를 제안:

**수동 조치가 필요한 경우:**
```yaml
questions:
  - question: '일부 항목에 수동 조치가 필요합니다. 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: 'init — 초기 설정 실행'
        description: 'DB 초기화, 마켓플레이스 발견, 보조 시그널 설정을 수행합니다'
      - label: 'dashboard — 현황 확인'
        description: '수정 후 스킬 상태를 확인합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

**모두 정상인 경우:**
```yaml
questions:
  - question: '모든 환경이 정상입니다! 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: 'dashboard — 스킬 현황'
        description: '추적 중인 스킬 건강도를 확인합니다'
      - label: 'diagnose — 스킬 진단'
        description: '특정 스킬을 진단합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

사용자 선택에 따라 해당 스킬을 실행한다.

## 시그널 기록

> **자동 수집 (Hook+Agent)**: 도구 실패, 사용자 메시지 등 raw 이벤트를 Hook이 수집하고, Stop 시 Claude가 유의미한 시그널만 판별하여 DB에 기록합니다.
> **수동 보조**: redo, manual_fix, clarify, blocked는 hook으로 감지하기 어려우므로, 발생 시 `/skill-doctor:record`로 수동 기록하면 데이터 품질이 향상됩니다.
