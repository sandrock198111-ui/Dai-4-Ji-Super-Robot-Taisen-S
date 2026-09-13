# Dai-4-Ji-Super-Robot-Taisen-S 한글화 프로젝트 작업 규칙

## 프로젝트 목표

이 프로젝트는 일본판 Dai-4-Ji Super Robot Taisen S(PS1)을 기준으로 한글 패치를 제작한다.

항상 다음 원칙을 우선한다.

* 원본 데이터를 최대한 보존한다.
* 성공한 결과보다 후퇴하지 않는다.
* 모든 작업은 재현 가능해야 한다.
* 중요한 변경은 반드시 문서화한다.
* 프로젝트의 안정성이 작업 속도보다 우선이다.
* 확실하지 않으면 수정보다 분석을 우선한다.

\---

# 작업 시작 전 (필수)

어떤 작업이든 시작하기 전에 반드시 아래 순서대로 진행한다.

1. 05\_docs/bible\_current.txt 읽기
2. 05\_docs/changelog.txt 읽기
3. 05\_docs/test\_log.txt 읽기
4. 05\_docs/codex\_notes.txt 읽기

현재 프로젝트 상태를 충분히 이해한 후 작업를 시작한다.

\---

# 작업 원칙

수정보다 분석을 먼저 한다.

파일을 수정하기 전에 반드시 아래 내용을 먼저 설명한다.

* 수정 대상 파일
* 수정 이유
* 예상 위험
* 기대 결과

사용자의 확인 없이 바로 수정하지 않는다.

\---

# 폴더 규칙

* 00\_original : 원본 보관. 절대 직접 수정 금지.
* 01\_work : 작업 파일.
* 02\_scripts : Python 및 도구.
* 03\_output : 테스트 결과물.
* 04\_screenshots : 결과 이미지.
* 05\_docs : 프로젝트 문서.

\---

# 문서 관리 규칙

## bible\_current.txt

현재 가장 성공한 상태만 기록한다.

## changelog.txt

실제로 적용된 변경 사항만 기록한다.

## test\_log.txt

모든 테스트를 기록한다.

* 날짜
* 수정 파일
* 테스트 방법
* 결과
* 실패 원인

## codex\_notes.txt

프로젝트를 진행하며 확인된 사실만 기록한다.

기록 대상

* 포인터 구조
* 압축 방식
* 폰트 구조
* 파일 포맷
* 성공한 분석
* 실패 원인
* 다시 시도하면 안 되는 방법

추측은 기록하지 않는다.

\---

# 백업 규칙

ROM, ISO, 바이너리 수정 전에는 반드시 백업 또는 복사본을 만든다.

\---

# 절대 금지

* 영어판 구조로 회귀
* 8x8 한글 방식으로 회귀
* 성공한 UI 덮어쓰기
* 원본 일본판 ROM 직접 수정
* 추측으로 포인터 수정
* 추측으로 압축 수정
* 확인되지 않은 영역 수정

\---

# Git 규칙

Codex는 사용자가 별도로 승인하지 않아도 필요하다고 판단하는 시점에 commit/push 할 수 있다.

자동 commit/push 가능한 경우:

* 작업 규칙, 인수인계 문서, changelog, test\_log, codex\_notes 업데이트
* 스크립트, 매니페스트, 분석 CSV/MD 변경
* 회귀 방지용 기준점 저장
* 새 세션 또는 재설치 대비 복구 지점 저장
* 사용자가 명시적으로 "진행", "해줘", "관리해줘"라고 한 작업의 완료 저장

자동 commit/push 전에는 반드시 확인한다.

* git status 확인
* git diff 또는 staged diff 확인
* 원본/대용량/저작권 위험 파일 포함 여부 확인
* 필요한 경우 .gitignore 보강

절대 commit/push 하지 않는 것:

* 00\_original/
* 03\_output/
* 99\_backup/
* ex/
* 06\_tools/
* 원본 ROM/ISO/BIN/CUE/CHD
* DAT/IMG/XA/STR/EXE/SND 같은 게임 추출 파일
* patch-only ZIP, FULL\_ARC ZIP, 패키징 산출물
* .gitignore에서 제외한 파일

브랜치 삭제와 히스토리 변경은 사용자가 명시적으로 요청하지 않으면 하지 않는다.

commit/push 후에는 커밋 해시, 변경 파일, 남은 문제를 사용자에게 보고한다.

\---

# Codex 작업 규칙

* 모르면 추측하지 않는다.
* 확신이 없으면 먼저 질문한다.
* 기존 성공 사례를 우선 활용한다.
* codex\_notes.txt를 적극 참고한다.
* 같은 실패를 반복하지 않는다.

\---

# 응답 순서

1. 현재 상태 분석
2. 수정 계획
3. 실제 수정
4. 변경 내용 요약
5. 테스트 방법
6. 위험 요소 및 남은 문제

\---

# 우선순위

1. 원본 보호
2. 성공 결과 보호
3. 문서 업데이트
4. 재현 가능한 작업 유지
5. 코드 품질 개선

\---

# 작업 종료 규칙

작업이 끝나면 반드시 다음을 수행한다.

1. bible\_current.txt 업데이트 여부 확인
2. changelog.txt 업데이트 여부 확인
3. test\_log.txt 기록
4. codex\_notes.txt에 새롭게 확인된 사실 기록
5. 변경 파일 목록 보고
6. 다음 작업 후보 제안

이 과정을 생략한 채 작업을 종료하지 않는다.

\---

# Claude 협업 규칙

Codex는 필요할 때 Claude를 호출할 수 있다. 2026-08-29 설정 완료.

## 호출 방법 두 가지

### 1\. 작업 위임 (권장)

셸에서 직접 실행한다. Claude가 스스로 판단하고 도구를 써서 결과를 돌려준다.

&#x20;   claude -p "지시 내용"


설정 변경이나 재시작이 필요 없다. 검증 완료.

### 2\. MCP 도구로 사용

`\~/.codex/config.toml` 의 `\[mcp\_servers.claude]` 에 등록되어 있다.
Codex 재시작 후 Read/Edit/Bash/Glob/Grep/Skill/Agent 등 28개 도구를 쓸 수 있다.

이 경로는 도구만 빌려오는 것이라 판단은 Codex가 한다.
Claude에게 생각을 시키려면 1번을 쓴다.

## 확인된 실패 원인 (다시 시도하지 말 것)

* **Paseo의 MCP 주입은 Codex에서 동작하지 않는다.**
`\~/.paseo/config.json` 의 `injectIntoAgents` 가 켜져 있어도 소용없다.
Codex가 요구하는 MCP 프로토콜 `2026-07-28` 을 Paseo 0.6.1의 번들 SDK가
  모른다(최대 `2025-11-25`). `\~/.paseo/daemon.log` 에
`Unsupported protocol version` 으로 누적된다.
Claude Code는 구버전으로 협상해 정상 동작하므로, 한쪽만 되는 비대칭이 생긴다.
0.6.1이 최신 릴리스라 업데이트로 해결할 수 없다. Paseo 신버전을 기다린다.
* **claude-cowork 플러그인 / external\_agent import는 호출 수단이 아니다.**
끝난 Claude 세션 로그를 복사해 오는 기능이며, 전제가 되는
`AppData\\Roaming\\Claude\\`(데스크톱 앱)가 설치되어 있지 않다.
* **Windows에서 `claude` 또는 `claude.cmd` 를 MCP command로 주면 실패한다.**
전자는 sh 스크립트, 후자는 배치 파일이라 spawn이 깨진다.
반드시 `claude.exe` 전체 경로를 준다.



# SRW-specific rules (2026-09-13)

Inherited from E:/korean/AGENTS.md at the user's request. Arc-specific findings are not SRW findings.
Previously authorized testing, setup and documentation do not require repeated confirmation.
Do not shorten translations or paraphrase to accommodate glyph limits. Prefer precomposed 16x16 1bpp fonts; do not switch to compositional fonts without discussing the choice.
Verify RAM storage, VRAM behavior and long-text expansion independently. Distinguish static evidence, sampled runtime tests and full-game verification.
Working repository: https://github.com/sandrock198111-ui/Dai-4-Ji-Super-Robot-Taisen-S
Reference upstream: https://github.com/Einbroch/srw4s-kr-patch

User clarification 2026-09-13: SFC Korean patch is a TRANSLATION reference, not a request to replace the PS1 font. Preserve the existing 1bpp precomposed font appearance. Do not substitute Bold or another typeface for a user-facing test build. Test glyph supply/capacity independently of typeface choice. The Bold diagnostic build was a scope mistake and is withdrawn from use.
