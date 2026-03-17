# Jake's Claude Code 플러그인 마켓플레이스

개인용 Claude Code 플러그인을 관리하는 마켓플레이스입니다.

## 마켓플레이스 설치

```bash
/plugin marketplace add gorillaProject/jake-marketplace
```

## 등록된 플러그인

| 플러그인 | 설명 | 명령어 | 버전 |
|---------|------|--------|------|
| `skill-doctor` | 스킬 건강 상태를 크로스 세션으로 진단하고 점진적으로 개선 | `/skill-doctor:diagnose` | 0.1.0 |

## 플러그인 설치 / 업데이트 / 제거

```bash
# 설치
/plugin install skill-doctor@jake-plugins

# 업데이트
/plugin marketplace update
/plugin uninstall skill-doctor
/plugin install skill-doctor@jake-plugins

# 제거
/plugin uninstall skill-doctor
```
