---
name: onboard
description: |
  engram CLI, Desktop 앱, MCP 서버 등록까지 한 번에 안내하는 온보딩 스킬.
  플러그인 설치 후 처음 실행하거나 새 환경에서 설정할 때 사용한다.
  트리거 키워드: "온보딩", "onboard", "engram 설치", "설치 안내", "설정해줘",
               "처음 시작", "engram 시작", "setup engram".
---

# onboard

## 목적

새 환경에서 `engram-orchestrator` 플러그인을 사용하기 위한 전체 설정을 일괄 안내한다.

1. **환경 체크** — CLI 설치 여부, MCP 연결 상태, PATH 확인
2. **CLI 설치** — GitHub Releases 에서 플랫폼별 바이너리 설치 (curl 직접)
3. **Desktop 앱 설치** — DMG 다운로드 + Gatekeeper 해제
4. **MCP 등록** — Claude Code / Claude Desktop / 프로젝트 settings.json
5. **연결 검증** — probe + 실패 시 3단계 처리 + 스킬 소개

## 트리거

다음 발화 시 자동 실행:

- `"온보딩"` / `"onboard"` / `"setup engram"`
- `"engram 설치"` / `"설치 안내"` / `"설정해줘"`
- `"처음 시작"` / `"engram 시작"`
- `"/engram-orchestrator:onboard"`

## 실행 방법

```
/engram-orchestrator:onboard
```

또는 자연어:
```
"engram 온보딩 해줘"
"engram 설치하고 싶어"
"처음 설정 도와줘"
"setup engram"
```

---

## Step 1. 환경 체크

```bash
# CLI 설치 여부
which engram

# PATH 에 ~/.local/bin 포함 여부
echo $PATH | grep -q '.local/bin' && echo "PATH OK" || echo "PATH MISSING"

# MCP 연결 probe (engram MCP 도구 사용 가능 환경)
# session_restore 를 read-only 프로브로 사용
```

| 확인 항목 | 결과 | 다음 단계 |
|----------|------|---------|
| `which engram` 성공 | CLI 이미 설치됨 | Step 2 skip → Step 3 |
| `which engram` 실패 | CLI 없음 | Step 2 진행 |
| MCP probe 성공 | MCP 연결 OK | Step 4 skip → Step 5 |
| MCP probe 실패 | MCP 미연결 | Step 4 진행 |
| PATH 에 `.local/bin` 없음 | 설치 후 export 안내 필요 | Step 2 완료 후 안내 |

---

## Step 2. CLI 설치

> `which engram` 이 성공하면 이 단계를 skip 한다.

### 방법 A — curl 직접 설치 (권장, gh 불필요)

```bash
# 최신 버전 조회
VER=$(curl -s https://api.github.com/repos/gorillaKim/engram/releases/latest \
  | grep tag_name | cut -d'"' -f4 | sed 's/v//')

echo "설치할 버전: v${VER}"

# 플랫폼/아키텍처 감지
OS=$(uname -s)    # Darwin / Linux
ARCH=$(uname -m)  # arm64 / x86_64

# 대상 트리플 결정
if [ "$OS" = "Darwin" ]; then
  [ "$ARCH" = "arm64" ] && TARGET="aarch64-apple-darwin" || TARGET="x86_64-apple-darwin"
else
  TARGET="x86_64-unknown-linux-gnu"
fi

# ~/.local/bin 디렉토리 생성 (없으면)
mkdir -p ~/.local/bin

# 다운로드 + 압축 해제 + 설치
curl -L "https://github.com/gorillaKim/engram/releases/download/v${VER}/engram-${VER}-${TARGET}.tar.gz" \
  | tar xz && mv engram ~/.local/bin/

# macOS: Gatekeeper 해제 (curl 설치 시 필수)
if [ "$OS" = "Darwin" ]; then
  xattr -cr ~/.local/bin/engram
fi

# 검증
engram --version
```

### 방법 B — Homebrew (macOS, brew 있는 경우)

```bash
brew tap gorillaKim/engram
brew install engram
# Homebrew 설치 시 xattr -cr 불필요 (자동 처리)
```

### PATH 설정 (~/.local/bin 이 PATH 에 없는 경우)

```bash
# bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# zsh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

> 안내 문구: "새 터미널을 열거나 `source ~/.zshrc` 를 실행하면 `engram` 명령을 바로 사용할 수 있습니다."

---

## Step 3. Desktop 앱 설치

> macOS 전용. Linux 또는 Desktop 앱이 필요 없으면 skip.

Desktop 앱 설치는 `/Applications` 에 파일을 복사하므로 **반드시 사용자 동의 후 진행**:

```
AskUserQuestion(
  "engram Desktop 앱을 /Applications 에 설치할까요?",
  options=["설치", "나중에", "skip"]
)
```

동의 시:

```bash
# 최신 버전 조회 (Step 2 에서 이미 조회했으면 재사용)
VER=$(curl -s https://api.github.com/repos/gorillaKim/engram/releases/latest \
  | grep tag_name | cut -d'"' -f4 | sed 's/v//')

ARCH=$(uname -m)
[ "$ARCH" = "arm64" ] && DMG_ARCH="aarch64" || DMG_ARCH="x64"

# gh CLI 로 DMG 다운로드
gh release download "v${VER}" \
  --repo gorillaKim/engram \
  --pattern "Engram_${VER}_${DMG_ARCH}.dmg"

# 마운트 + 복사 + Gatekeeper 해제
hdiutil attach "Engram_${VER}_${DMG_ARCH}.dmg" -nobrowse
cp -r /Volumes/Engram/Engram.app /Applications/
xattr -cr /Applications/Engram.app     # 미서명 앱 — 필수 (note #95)
hdiutil detach /Volumes/Engram
rm "Engram_${VER}_${DMG_ARCH}.dmg"

# 실행 확인
open /Applications/Engram.app
```

> `gh` CLI 가 없는 경우:
> ```bash
> curl -L "https://github.com/gorillaKim/engram/releases/download/v${VER}/Engram_${VER}_${DMG_ARCH}.dmg" \
>   -o "Engram_${VER}_${DMG_ARCH}.dmg"
> ```

---

## Step 4. MCP 등록

> MCP probe 성공이면 이 단계를 skip 한다.

### 4-A. Claude Code CLI

> 참고: 이 플러그인은 `.mcp.json` 으로 `engram`(같은 endpoint)을 **번들**한다 → 플러그인 활성 상태면 아래 수동 등록은 **선택사항**이다(같은 URL 이라 endpoint dedup 으로 흡수, `mcp__engram__*` 그대로 유지). 다만 **다른 프로젝트에서 플러그인 없이도** engram 을 쓰려면 user scope 등록이 유용하다.

```bash
claude mcp add --scope user --transport http engram http://127.0.0.1:3456/mcp
```

또는 `~/.claude.json` 직접 편집:

```json
{
  "mcpServers": {
    "engram": {
      "type": "http",
      "url": "http://127.0.0.1:3456/mcp"
    }
  }
}
```

> ⚠️ Claude Code CLI 인식 위치는 `~/.claude.json` 의 `mcpServers`.
> `~/.claude/settings.json` 의 `mcpServers` 는 무시됨.

### 4-B. Claude Desktop (macOS)

```bash
# 설정 파일 경로
CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# 현재 설정 확인
cat "$CONFIG"
```

`mcpServers` 에 추가:

```json
{
  "mcpServers": {
    "engram": {
      "type": "http",
      "url": "http://127.0.0.1:3456/mcp"
    }
  }
}
```

### 4-C. 프로젝트 `.claude/settings.json` (선택)

```json
{
  "mcpServers": {
    "engram": {
      "type": "http",
      "url": "http://127.0.0.1:3456/mcp"
    }
  }
}
```

설정 후 **Claude Code 재시작** 필요.

---

## Step 5. 연결 검증 + 실패 처리

### 5-1. MCP probe

```
session_restore(project_key, mode="agent")   # 또는 임의의 read-only MCP 호출 (프로브 → mode='agent' 로 최소 페이로드)
```

**성공** → Step 5-2 (완료 안내).

**실패** → Step 5-3 (서버 시작 안내).

### 5-1b. Playwright MCP 전제 점검 (UI 테스트용)

이 플러그인은 UI 테스트용 `playwright` MCP 서버를 **번들**한다(`.mcp.json`). 플러그인 활성화 시 자동 시작되므로 별도 `claude mcp add` 는 **불필요**하다. 다만 `npx` 로 구동되므로 node/npx 전제만 점검한다:

```bash
node -v && npx -v    # 둘 다 출력되면 OK
```

- **OK** → `/mcp` 에 `playwright` 서버가 연결로 표시되는지 확인(자동 시작). 안 보이면 `/reload-plugins`.
- **node/npx 없음** → 사용자에게 Node.js(LTS) 설치 안내. UI 테스트(`ui-test` 스킬 / UI 이슈 리뷰)는 설치 후 사용 가능. engram 핵심 기능(이슈/리뷰)은 이와 무관하게 동작.

### 5-2. 완료 안내 (MCP 연결 성공)

```
[onboard] 설정 완료!

사용 가능한 트리거 키워드:
  - "회고해줘" / "retro"        → /engram-orchestrator:sprint-retro
  - "리뷰해줘" / "코드 리뷰"    → /engram-orchestrator:review-issue
  - "이슈로 처리해줘"            → /engram-orchestrator:intake-as-issue
  - "트래킹하면서 처리해줘"      → /engram-orchestrator:solo-track
  - "ready 큐 비워줘"           → engram-leader (dispatch 모드)

다음 단계:
  - engram Desktop 앱에서 프로젝트/스프린트 생성
  - "이슈로 처리해줘" 로 첫 작업 시작
```

### 5-3. 서버 시작 안내 (MCP 연결 실패)

```
AskUserQuestion(
  "engram MCP 서버에 연결할 수 없습니다. 서버를 시작해주세요:\n"
  "  engram serve --port 3456\n"
  "  (또는 engram Desktop 앱 실행 후 서버 탭 확인)\n"
  "준비가 되면 '계속'을 입력해주세요.",
  options=["계속 (재시도)", "CLI 모드로 진행", "중단"]
)
```

**"계속"** → MCP probe 1회 재시도.
- 성공 → Step 5-2.
- 실패 → Step 5-4.

**"CLI 모드"** → Step 5-4.

**"중단"** → 온보딩 중단. 서버 문제 해결 후 재실행 안내.

### 5-4. CLI fallback 확인

```bash
which engram
```

**있음** → CLI 모드로 계속:
```
[onboard] CLI 모드로 진행합니다.
MCP 서버 없이 engram CLI 로 동일 기능을 사용할 수 있습니다.
이 세션에서는 MCP 재시도 없이 CLI 명령어만 사용합니다.

CLI 주요 명령어:
  engram session restore --project <key> --mode agent --json
  engram issue list --status ready --project <key>
  engram issue claim <id> --agent-id "main@<sess>-issue<id>"
  engram note add --issue <id> --type discovery --summary "..."
```

**없음** → CLI 설치 먼저:
```
[onboard] engram CLI 가 설치되지 않았습니다.
Step 2 의 curl 설치 방법을 먼저 완료해주세요.
설치 후 다시 onboard 를 실행하세요.
```

---

## 보고 형식

```
[onboard] 완료 요약

환경: macOS arm64 (Apple Silicon)
CLI: v0.1.1 (~/.local/bin/engram) ✓
Desktop 앱: /Applications/Engram.app ✓ (또는 skip)
MCP 등록:
  - Claude Code: ~/.claude.json ✓
  - Claude Desktop: ~/Library/.../claude_desktop_config.json ✓
MCP 연결: ✓ (http://127.0.0.1:3456/mcp)

다음 단계:
  - Desktop 앱에서 프로젝트 생성
  - "이슈로 처리해줘" 로 첫 작업 시작
```

---

## 설계 결정 참조

| note | 내용 |
|------|------|
| #93 | MCP 연결 실패 3단계 처리 (서버 안내 → 재시도 → CLI fallback) |
| #95 | xattr -cr: Desktop DMG = 필수, Homebrew CLI = 불필요 |
| #96 | 에셋 패턴: `Engram_{ver}_{arch}.dmg` / `engram-{ver}-{target}.tar.gz` |
| #97 | Homebrew 부가 옵션 (brew tap gorillaKim/engram) |
| #98 | 확정: ~/.local/bin + curl 직접 사용 (gh 불필요) |

---

## 주의사항

- Desktop 앱 설치(`cp to /Applications`) 는 반드시 사용자 동의 후 진행.
- CLI fallback 선택 시 해당 세션은 MCP 재시도 없이 CLI 전용으로 동작.
- `which engram` 없는 상태에서 CLI fallback 선택 시 → Step 2 설치 먼저 안내.
- `~/.local/bin` PATH 미설정 시 설치 성공해도 `engram` 명령이 안 먹힘 — PATH export 필수.
- Homebrew 로 설치한 경우 `xattr -cr` 불필요 (Homebrew 가 자동 처리).
