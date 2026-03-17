#!/usr/bin/env python3
"""skill-doctor CLI — record, diagnose, update-profile for skill health tracking."""

import argparse
import json
import os
import random
import sqlite3
import string
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path.home() / ".claude" / "skill-doctor"
DB_PATH = DATA_DIR / "skill-doctor.db"
REPORTS_DIR = DATA_DIR / "reports"

SCORE_MAP = {
    "clarify": 0, "correct": 25, "redo": 40,
    "tool_error": 15, "cancelled": 50, "manual_fix": 30, "blocked": 0,
}

# 사용자 측 cause_type — CD 점수에 가산하지 않음
USER_SIDE_CAUSE_TYPES = {"insufficient_context", "user_preference", "external_issue"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    cd_score INTEGER NOT NULL,
    signal_count INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    type TEXT NOT NULL,
    score INTEGER NOT NULL,
    context TEXT,
    action_taken TEXT,
    cause_type TEXT,
    cause_detail TEXT,
    timestamp TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS skill_profiles (
    skill TEXT NOT NULL,
    project TEXT NOT NULL,
    skill_path TEXT,
    last_diagnosed TEXT,
    health_score INTEGER DEFAULT 100,
    resolved_issues TEXT DEFAULT '[]',
    dismissed_issues TEXT DEFAULT '[]',
    heal_tracking TEXT DEFAULT '[]',
    source TEXT DEFAULT 'local',
    plugin_name TEXT,
    PRIMARY KEY (skill, project)
);
"""


TMP_DIR = DATA_DIR / "tmp"


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    # migrate: add skill_path if missing
    try:
        db.execute("SELECT skill_path FROM skill_profiles LIMIT 1")
    except sqlite3.OperationalError:
        db.execute("ALTER TABLE skill_profiles ADD COLUMN skill_path TEXT")
        db.commit()
    # migrate: add heal_tracking if missing
    try:
        db.execute("SELECT heal_tracking FROM skill_profiles LIMIT 1")
    except sqlite3.OperationalError:
        db.execute("ALTER TABLE skill_profiles ADD COLUMN heal_tracking TEXT DEFAULT '[]'")
        db.commit()
    # migrate: add source and plugin_name for marketplace discovery
    try:
        db.execute("SELECT source FROM skill_profiles LIMIT 1")
    except sqlite3.OperationalError:
        db.execute("ALTER TABLE skill_profiles ADD COLUMN source TEXT DEFAULT 'local'")
        db.execute("ALTER TABLE skill_profiles ADD COLUMN plugin_name TEXT")
        db.commit()
    return db


def detect_project():
    try:
        url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"], stderr=subprocess.DEVNULL
        ).decode().strip()
        name = url.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return name
    except Exception:
        pass
    return os.path.basename(os.getcwd())


def gen_session_id():
    now = datetime.now().strftime("%Y%m%d-%H%M%S")
    rand = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{now}-{rand}"


def _parse_heal_tracking(profile_row):
    """Safely parse heal_tracking from profile row."""
    if not profile_row or not profile_row["heal_tracking"]:
        return []
    try:
        return json.loads(profile_row["heal_tracking"])
    except (json.JSONDecodeError, TypeError):
        return []


def cleanup(db):
    cutoff = (datetime.now() - timedelta(days=90)).isoformat()
    old_sessions = [
        r[0] for r in db.execute(
            "SELECT id FROM sessions WHERE timestamp < ?", (cutoff,)
        ).fetchall()
    ]
    if old_sessions:
        placeholders = ",".join("?" * len(old_sessions))
        db.execute(f"DELETE FROM signals WHERE session_id IN ({placeholders})", old_sessions)
        db.execute(f"DELETE FROM sessions WHERE id IN ({placeholders})", old_sessions)
    # cleanup old reports
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    for f in REPORTS_DIR.iterdir():
        if f.is_file() and f.stat().st_mtime < (datetime.now() - timedelta(days=90)).timestamp():
            f.unlink()


# ── record ──────────────────────────────────────────────────────────────────

def cmd_record(args):
    filepath = Path(args.file)
    if not filepath.exists():
        print(json.dumps({"error": f"File not found: {args.file}"}))
        sys.exit(1)

    with open(filepath) as f:
        data = json.load(f)

    skill = data["skill"]
    skill_path = data.get("skill_path")
    signals = data.get("signals", [])
    project = detect_project()
    session_id = gen_session_id()
    now = datetime.now().isoformat()

    cd_score = 0
    rows = []
    for sig in signals:
        sig_type = sig.get("type", "")
        cause_type = sig.get("cause_type", "")
        score = SCORE_MAP.get(sig_type, 0)
        # 사용자 측 cause_type이면 CD에 가산하지 않음
        if cause_type in USER_SIDE_CAUSE_TYPES:
            score = 0
        cd_score += score
        rows.append((
            session_id, sig_type, score,
            sig.get("context"), sig.get("action_taken"),
            sig.get("cause_type"), sig.get("cause_detail"), now,
        ))

    db = get_db()
    try:
        db.execute(
            "INSERT INTO sessions (id, project, skill_name, timestamp, cd_score, signal_count) VALUES (?,?,?,?,?,?)",
            (session_id, project, skill, now, cd_score, len(signals)),
        )
        if rows:
            db.executemany(
                "INSERT INTO signals (session_id, type, score, context, action_taken, cause_type, cause_detail, timestamp) VALUES (?,?,?,?,?,?,?,?)",
                rows,
            )
        if skill_path:
            db.execute(
                """INSERT INTO skill_profiles (skill, project, skill_path) VALUES (?, ?, ?)
                   ON CONFLICT(skill, project) DO UPDATE SET skill_path=excluded.skill_path""",
                (skill, project, skill_path),
            )
        else:
            db.execute(
                """INSERT INTO skill_profiles (skill, project) VALUES (?, ?)
                   ON CONFLICT(skill, project) DO NOTHING""",
                (skill, project),
            )
        cleanup(db)
        db.commit()
    finally:
        db.close()

    try:
        filepath.unlink()
    except Exception:
        pass

    print(json.dumps({"session_id": session_id, "cd_score": cd_score}))


# ── diagnose ────────────────────────────────────────────────────────────────

def cmd_diagnose(args):
    db = get_db()
    project = detect_project() if not args.all_projects else None
    skill = args.skill
    session_id = args.session

    # auto-select latest session if not specified
    if not session_id:
        if project:
            row = db.execute(
                "SELECT id FROM sessions WHERE skill_name=? AND project=? ORDER BY timestamp DESC LIMIT 1",
                (skill, project),
            ).fetchone()
        else:
            row = db.execute(
                "SELECT id FROM sessions WHERE skill_name=? ORDER BY timestamp DESC LIMIT 1",
                (skill,),
            ).fetchone()
        if not row:
            print(json.dumps({"error": f"No sessions found for skill '{skill}'"}))
            sys.exit(1)
        session_id = row["id"]

    _expire_dismissed(db, skill, project)

    if project:
        profile_row = db.execute(
            "SELECT * FROM skill_profiles WHERE skill=? AND project=?", (skill, project)
        ).fetchone()
    else:
        profile_row = db.execute(
            "SELECT * FROM skill_profiles WHERE skill=? LIMIT 1", (skill,)
        ).fetchone()

    resolved = json.loads(profile_row["resolved_issues"]) if profile_row else []
    dismissed_raw = json.loads(profile_row["dismissed_issues"]) if profile_row else []
    dismissed = [d["cause_type"] for d in dismissed_raw]
    # heal_tracking에서 observing 중인 cause_type은 resolved여도 제외하지 않음 (재발 감지용)
    heal_tracking_raw = _parse_heal_tracking(profile_row)
    observing_causes = set()
    for h in heal_tracking_raw:
        if h.get("status") == "observing":
            for ct in h.get("cause_types", []):
                observing_causes.add(ct)
    exclude = (set(resolved) | set(dismissed)) - observing_causes

    if project:
        total = db.execute(
            "SELECT COUNT(*) FROM sessions WHERE skill_name=? AND project=?", (skill, project)
        ).fetchone()[0]
    else:
        total = db.execute(
            "SELECT COUNT(*) FROM sessions WHERE skill_name=?", (skill,)
        ).fetchone()[0]

    cur = db.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    cur_signals = db.execute(
        "SELECT type, COUNT(*) as cnt FROM signals WHERE session_id=? GROUP BY type", (session_id,)
    ).fetchall()
    signal_summary = {r["type"]: r["cnt"] for r in cur_signals}

    if project:
        all_signals = db.execute(
            """SELECT sig.cause_type, sig.cause_detail, sig.session_id
               FROM signals sig JOIN sessions s ON sig.session_id = s.id
               WHERE s.skill_name=? AND s.project=? AND sig.cause_type IS NOT NULL""",
            (skill, project),
        ).fetchall()
    else:
        all_signals = db.execute(
            """SELECT sig.cause_type, sig.cause_detail, sig.session_id
               FROM signals sig JOIN sessions s ON sig.session_id = s.id
               WHERE s.skill_name=? AND sig.cause_type IS NOT NULL""",
            (skill,),
        ).fetchall()

    cause_counts = {}
    cause_details = {}
    for r in all_signals:
        ct = r["cause_type"]
        if ct in exclude:
            continue
        detail = r["cause_detail"] or ""
        if ct not in cause_counts:
            cause_counts[ct] = set()
            cause_details[ct] = []
        cause_counts[ct].add(r["session_id"])
        if detail and detail not in cause_details[ct]:
            cause_details[ct].append(detail)

    cause_type_counts = {k: len(v) for k, v in cause_counts.items()}

    if project:
        recent = db.execute(
            "SELECT cd_score FROM sessions WHERE skill_name=? AND project=? ORDER BY timestamp DESC LIMIT 3",
            (skill, project),
        ).fetchall()
    else:
        recent = db.execute(
            "SELECT cd_score FROM sessions WHERE skill_name=? ORDER BY timestamp DESC LIMIT 3",
            (skill,),
        ).fetchall()
    avg_cd = round(sum(r["cd_score"] for r in recent) / max(len(recent), 1))

    heal_tracking_raw = _parse_heal_tracking(profile_row)
    active_heals = [h for h in heal_tracking_raw if h.get("status") == "observing"]
    previous_heals = [h for h in heal_tracking_raw if h.get("status") == "failed"]

    source = "local"
    plugin_name = None
    if profile_row:
        try:
            source = profile_row["source"] or "local"
            plugin_name = profile_row["plugin_name"]
        except (IndexError, KeyError):
            pass

    result = {
        "skill": skill,
        "project": project or "all",
        "source": source,
        "plugin_name": plugin_name,
        "profile": {
            "health_score": profile_row["health_score"] if profile_row else 100,
            "last_diagnosed": profile_row["last_diagnosed"] if profile_row else None,
            "skill_path": profile_row["skill_path"] if profile_row else None,
            "total_sessions": total,
            "resolved_issues": resolved,
            "dismissed_issues": [d["cause_type"] for d in dismissed_raw],
        },
        "heal_tracking": {
            "active": active_heals,
            "previous_heals": previous_heals,
        },
        "current_session": {
            "id": session_id,
            "cd_score": cur["cd_score"] if cur else 0,
            "signal_summary": signal_summary,
        },
        "cross_session": {
            "cause_type_counts": cause_type_counts,
            "cause_type_details": cause_details,
            "avg_cd_last_3": avg_cd,
        },
    }

    if args.full:
        if project:
            recent_sessions = db.execute(
                "SELECT * FROM sessions WHERE skill_name=? AND project=? ORDER BY timestamp DESC LIMIT 5",
                (skill, project),
            ).fetchall()
        else:
            recent_sessions = db.execute(
                "SELECT * FROM sessions WHERE skill_name=? ORDER BY timestamp DESC LIMIT 5",
                (skill,),
            ).fetchall()
        full_data = []
        for s in recent_sessions:
            sigs = db.execute(
                "SELECT * FROM signals WHERE session_id=?", (s["id"],)
            ).fetchall()
            full_data.append({
                "session": dict(s),
                "signals": [dict(sig) for sig in sigs],
            })
        result["recent_sessions_full"] = full_data

    db.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _expire_dismissed(db, skill, project):
    if project:
        row = db.execute(
            "SELECT dismissed_issues FROM skill_profiles WHERE skill=? AND project=?", (skill, project)
        ).fetchone()
    else:
        row = db.execute(
            "SELECT dismissed_issues FROM skill_profiles WHERE skill=? LIMIT 1", (skill,)
        ).fetchone()
    if not row:
        return
    dismissed = json.loads(row["dismissed_issues"])
    now = datetime.now().isoformat()
    updated = [d for d in dismissed if d.get("until", "") > now]
    if len(updated) != len(dismissed):
        if project:
            db.execute(
                "UPDATE skill_profiles SET dismissed_issues=? WHERE skill=? AND project=?",
                (json.dumps(updated), skill, project),
            )
        else:
            # --all-projects: update only the specific row found by LIMIT 1
            row_skill = row["skill"] if hasattr(row, "keys") else skill
            db.execute(
                "UPDATE skill_profiles SET dismissed_issues=? WHERE skill=? AND rowid=(SELECT rowid FROM skill_profiles WHERE skill=? LIMIT 1)",
                (json.dumps(updated), skill, skill),
            )
        db.commit()


# ── update-profile ──────────────────────────────────────────────────────────

def cmd_update_profile(args):
    db = get_db()
    project = detect_project()
    skill = args.skill
    now = datetime.now().isoformat()

    db.execute(
        """INSERT INTO skill_profiles (skill, project) VALUES (?, ?)
           ON CONFLICT(skill, project) DO NOTHING""",
        (skill, project),
    )

    db.execute(
        "UPDATE skill_profiles SET health_score=?, last_diagnosed=? WHERE skill=? AND project=?",
        (args.health_score, now, skill, project),
    )

    if args.resolve:
        row = db.execute(
            "SELECT resolved_issues FROM skill_profiles WHERE skill=? AND project=?", (skill, project)
        ).fetchone()
        resolved = json.loads(row["resolved_issues"])
        if args.resolve not in resolved:
            resolved.append(args.resolve)
            db.execute(
                "UPDATE skill_profiles SET resolved_issues=? WHERE skill=? AND project=?",
                (json.dumps(resolved), skill, project),
            )

    if args.dismiss:
        row = db.execute(
            "SELECT dismissed_issues FROM skill_profiles WHERE skill=? AND project=?", (skill, project)
        ).fetchone()
        dismissed = json.loads(row["dismissed_issues"])
        until = (datetime.now() + timedelta(days=30)).isoformat()
        dismissed = [d for d in dismissed if d.get("cause_type") != args.dismiss]
        dismissed.append({"cause_type": args.dismiss, "until": until})
        db.execute(
            "UPDATE skill_profiles SET dismissed_issues=? WHERE skill=? AND project=?",
            (json.dumps(dismissed), skill, project),
        )

    if args.heal_tracking:
        row = db.execute(
            "SELECT heal_tracking FROM skill_profiles WHERE skill=? AND project=?", (skill, project)
        ).fetchone()
        tracking = _parse_heal_tracking(row)
        try:
            entry = json.loads(args.heal_tracking)
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON for --heal-tracking"}))
            db.close()
            sys.exit(1)
        entry["applied_at"] = now
        if "status" not in entry:
            entry["status"] = "observing"
        tracking.append(entry)
        db.execute(
            "UPDATE skill_profiles SET heal_tracking=? WHERE skill=? AND project=?",
            (json.dumps(tracking), skill, project),
        )

    if args.fail_heal:
        row = db.execute(
            "SELECT heal_tracking, resolved_issues FROM skill_profiles WHERE skill=? AND project=?", (skill, project)
        ).fetchone()
        tracking = _parse_heal_tracking(row)
        found = False
        failed_causes = []
        for t in tracking:
            if t.get("heal_id") == args.fail_heal:
                t["status"] = "failed"
                failed_causes = t.get("cause_types", [])
                found = True
        if not found:
            db.commit()
            db.close()
            print(json.dumps({"error": f"heal_id '{args.fail_heal}' not found"}))
            sys.exit(1)
        # resolved_issues에서 실패한 cause_type 제거 (재발 감지 가능하게)
        resolved = json.loads(row["resolved_issues"]) if row and row["resolved_issues"] else []
        resolved = [r for r in resolved if r not in failed_causes]
        db.execute(
            "UPDATE skill_profiles SET heal_tracking=?, resolved_issues=? WHERE skill=? AND project=?",
            (json.dumps(tracking), json.dumps(resolved), skill, project),
        )

    if args.confirm_heal:
        row = db.execute(
            "SELECT heal_tracking FROM skill_profiles WHERE skill=? AND project=?", (skill, project)
        ).fetchone()
        tracking = _parse_heal_tracking(row)
        found = False
        for t in tracking:
            if t.get("heal_id") == args.confirm_heal:
                t["status"] = "confirmed"
                found = True
        if not found:
            db.commit()
            db.close()
            print(json.dumps({"error": f"heal_id '{args.confirm_heal}' not found"}))
            sys.exit(1)
        db.execute(
            "UPDATE skill_profiles SET heal_tracking=? WHERE skill=? AND project=?",
            (json.dumps(tracking), skill, project),
        )

    db.commit()
    db.close()
    print(json.dumps({"status": "ok", "skill": skill, "project": project, "health_score": args.health_score}))


# ── list ────────────────────────────────────────────────────────────────────

def cmd_list(args):
    db = get_db()
    project = detect_project() if not args.all_projects else None

    if project:
        rows = db.execute(
            """SELECT sp.skill, sp.project, sp.health_score, sp.last_diagnosed,
                      sp.source, sp.plugin_name,
                      COUNT(s.id) as total_sessions,
                      MAX(s.timestamp) as last_session
               FROM skill_profiles sp
               LEFT JOIN sessions s ON sp.skill = s.skill_name AND sp.project = s.project
               WHERE sp.project = ?
               GROUP BY sp.skill, sp.project
               ORDER BY sp.health_score ASC""",
            (project,),
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT sp.skill, sp.project, sp.health_score, sp.last_diagnosed,
                      sp.source, sp.plugin_name,
                      COUNT(s.id) as total_sessions,
                      MAX(s.timestamp) as last_session
               FROM skill_profiles sp
               LEFT JOIN sessions s ON sp.skill = s.skill_name AND sp.project = s.project
               GROUP BY sp.skill, sp.project
               ORDER BY sp.health_score ASC""",
        ).fetchall()

    result = [
        {
            "skill": r["skill"],
            "project": r["project"],
            "health_score": r["health_score"],
            "total_sessions": r["total_sessions"],
            "last_diagnosed": r["last_diagnosed"],
            "last_session": r["last_session"],
            "source": r["source"] or "local",
            "plugin_name": r["plugin_name"],
        }
        for r in rows
    ]
    db.close()
    print(json.dumps(result, ensure_ascii=False, indent=2))


# ── discover-marketplace ───────────────────────────────────────────────────

INSTALLED_PLUGINS_PATH = Path.home() / ".claude" / "plugins" / "installed_plugins.json"


def cmd_discover_marketplace(args):
    if not INSTALLED_PLUGINS_PATH.exists():
        print(json.dumps({"error": "installed_plugins.json not found", "discovered": 0}))
        sys.exit(1)

    with open(INSTALLED_PLUGINS_PATH) as f:
        data = json.load(f)

    db = get_db()
    project = detect_project()
    discovered = []

    for plugin_key, installations in data.get("plugins", {}).items():
        for inst in installations:
            install_path = Path(inst.get("installPath", ""))
            skills_dir = install_path / "skills"
            if not skills_dir.is_dir():
                continue
            for skill_dir in skills_dir.iterdir():
                if not skill_dir.is_dir():
                    continue
                skill_md = skill_dir / "SKILL.md"
                if not skill_md.exists():
                    continue
                skill_name = skill_dir.name
                skill_path = str(skill_md)
                # project-scoped plugins → use plugin's project, else current project
                target_project = project
                proj_path = inst.get("projectPath")
                if proj_path:
                    target_project = os.path.basename(proj_path)

                db.execute(
                    """INSERT INTO skill_profiles (skill, project, skill_path, source, plugin_name)
                       VALUES (?, ?, ?, 'marketplace', ?)
                       ON CONFLICT(skill, project) DO UPDATE SET
                         skill_path=excluded.skill_path,
                         source='marketplace',
                         plugin_name=excluded.plugin_name""",
                    (skill_name, target_project, skill_path, plugin_key),
                )
                discovered.append({
                    "skill": skill_name,
                    "plugin": plugin_key,
                    "project": target_project,
                    "path": skill_path,
                })

    if args.prune:
        # Remove marketplace skills whose plugin is no longer installed
        installed_keys = set(data.get("plugins", {}).keys())
        rows = db.execute(
            "SELECT skill, project, plugin_name FROM skill_profiles WHERE source='marketplace'"
        ).fetchall()
        pruned = 0
        for r in rows:
            if r["plugin_name"] not in installed_keys:
                db.execute(
                    "DELETE FROM skill_profiles WHERE skill=? AND project=? AND source='marketplace'",
                    (r["skill"], r["project"]),
                )
                pruned += 1
        db.commit()
        db.close()
        print(json.dumps({"discovered": len(discovered), "pruned": pruned, "skills": discovered}, ensure_ascii=False, indent=2))
    else:
        db.commit()
        db.close()
        print(json.dumps({"discovered": len(discovered), "skills": discovered}, ensure_ascii=False, indent=2))


# ── main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="skill-doctor CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_rec = sub.add_parser("record", help="Record session signals")
    p_rec.add_argument("--file", required=True, help="Path to session JSON file")

    p_diag = sub.add_parser("diagnose", help="Diagnose skill health")
    p_diag.add_argument("--skill", required=True)
    p_diag.add_argument("--session", default=None, help="Session ID (omit for latest)")
    p_diag.add_argument("--all-projects", action="store_true", default=False)
    p_diag.add_argument("--full", action="store_true", default=False)

    p_list = sub.add_parser("list", help="List tracked skills")
    p_list.add_argument("--all-projects", action="store_true", default=False)

    p_disc = sub.add_parser("discover-marketplace", help="Discover skills from installed marketplace plugins")
    p_disc.add_argument("--prune", action="store_true", default=False, help="Remove skills from uninstalled plugins")

    p_up = sub.add_parser("update-profile", help="Update skill profile")
    p_up.add_argument("--skill", required=True)
    p_up.add_argument("--health-score", type=int, required=True)
    p_up.add_argument("--resolve", help="cause_type to mark as resolved")
    p_up.add_argument("--dismiss", help="cause_type to dismiss for 30 days")
    p_up.add_argument("--heal-tracking", dest="heal_tracking", help="JSON heal tracking entry to append")
    p_up.add_argument("--fail-heal", dest="fail_heal", help="heal_id to mark as failed")
    p_up.add_argument("--confirm-heal", dest="confirm_heal", help="heal_id to mark as confirmed (verified successful)")

    args = parser.parse_args()
    if args.command == "record":
        cmd_record(args)
    elif args.command == "diagnose":
        cmd_diagnose(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "discover-marketplace":
        cmd_discover_marketplace(args)
    elif args.command == "update-profile":
        cmd_update_profile(args)


if __name__ == "__main__":
    main()
