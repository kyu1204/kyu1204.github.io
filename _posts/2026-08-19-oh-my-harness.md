---
title: oh-my-harness - 자연어로 AI 코딩 에이전트 가드레일 만들기
description: 자연어 한 줄로 AI 코딩 에이전트용 강제 가드레일(훅)을 생성하는 npm CLI, oh-my-harness를 소개합니다.
categories: [ai, oh-my-harness]
tags: [ai-agents, claude-code, codex, hooks, cli, guardrails, tdd]
image: /assets/img/oh-my-harness.png
date: 2026-08-19 00:00:00 +09:00
---

## 개요

AI 코딩 에이전트(Claude Code, Codex 등)를 쓰다 보면 누구나 한 번쯤 겪는 사고가 있습니다. 분명 CLAUDE.md에 "테스트 통과 전에는 커밋하지 마"라고 적어놨는데, 에이전트가 신나게 테스트도 안 돌리고 커밋을 해버리는 상황이죠. 지시문(instruction)은 어디까지나 *부탁*이지 *강제*가 아니기 때문입니다.

여기에 문제가 하나 더 있습니다. 에이전트마다 설정 파일이 전부 다르다는 것. Claude Code는 `CLAUDE.md` + hooks, Codex는 `AGENTS.md`, Cursor는 `.cursorrules`... 프로젝트마다 이걸 복붙하다 보면 어느 순간 TDD 훅 하나가 빠져있고, 그날 사고가 납니다 🥲

그래서 만들었습니다. 바로 [oh-my-harness](https://github.com/kyu1204/oh-my-harness)!

> "Tame your AI coding agents with natural language."

자연어 한 줄로 AI 코딩 에이전트용 **강제(enforced) 가드레일**을 생성하는 npm CLI 입니다. "지켜줬으면 좋겠는 규칙"을 적는 게 아니라, **실제로 차단하는 훅**을 만들어줍니다.

## 무엇이 다른가

핵심 차이는 "지시문"과 "강제"의 차이입니다.

> - 테스트가 통과하지 않으면 커밋 자체가 **차단**됩니다
> - 테스트를 먼저 수정하지 않으면 소스 편집이 **차단**됩니다 (TDD Guard)
> - `node_modules/` 쓰기, 위험한 명령 실행이 **차단**됩니다

에이전트가 규칙을 "까먹어도" 훅이 물리적으로 막아주기 때문에, 지시문처럼 무시될 수가 없습니다.

## 핵심 아키텍처

동작 흐름은 다음과 같습니다.

```
자연어 설명 → NL Processing (멀티 프로바이더 LLM)
            → Project Detector (14개 언어 결정론적 감지)
            → harness.yaml (source of truth)
            → 에미터: CLAUDE.md / AGENTS.md / .omh/hooks/*.sh
              / .claude/settings.json / .codex/{config.toml,hooks.json}
```

### harness.yaml 이 유일한 source of truth

"테스트 없이 커밋 금지, main 브랜치 직접 작업 금지"라고 자연어로 설명하면, 그 결과가 `harness.yaml` 하나에 담깁니다. Claude Code용 설정, Codex용 설정은 전부 이 파일에서 **생성**되는 산출물일 뿐이에요. git으로 추적할 수 있고, 생성 파일이 수동 수정으로 드리프트하면 `omh sync --check`(CI 게이트), `omh diff`(프리뷰)로 잡아냅니다.

### 훅 스크립트는 런타임 간 공유

`.omh/hooks/*.sh` 훅 스크립트를 Claude Code와 Codex가 **공유**합니다. 런타임별로 스크립트를 복제하지 않고, 같은 스크립트가 자신을 호출한 런타임을 감지해 응답 형식만 바꿉니다. 덕분에 "Claude에서는 막히는데 Codex에서는 뚫리는" 상황이 구조적으로 생기지 않습니다.

### 빌딩 블록 카탈로그

모든 가드레일은 재사용 가능한 파라미터화된 블록입니다. 17개 카탈로그 중 몇 개만 소개하면:

> - **tdd-guard**: 테스트 먼저 수정하지 않으면 소스 편집 차단
> - **commit-test-gate / commit-typecheck-gate**: 테스트·타입체크 미통과 커밋 차단
> - **branch-guard**: 보호 브랜치 직접 작업 차단
> - **path-guard / command-guard**: 특정 경로 쓰기·위험 명령 차단
> - **secret-file-guard**: 시크릿 파일 접근 차단
> - **lint/format/test-on-save**: 저장 시 자동 실행

### block 모드와 ask 모드

무조건 차단(`block`)만 있는 게 아니라, 사용자 승인을 요청하는 `ask` 모드도 있습니다. Claude Code에서는 네이티브 permission prompt로 자연스럽게 뜹니다. 재밌는 지점은 ask를 지원하지 않는 런타임(Codex)에서는 **하드 블록으로 폴백**한다는 것 - 가드레일이 조용히 "allow"로 다운그레이드되는 일은 절대 없어야 한다는 안전 원칙입니다.

### 관측성

모든 훅 호출은 `.omh/state/events.jsonl`에 기록됩니다. `omh stats`를 실행하면 TUI 대시보드로 어떤 가드레일이 실제로 얼마나 발동했는지 볼 수 있어요. "설정은 했는데 한 번도 안 쓰인 규칙"을 찾아내는 데 유용합니다.

## 시작하기

설치 없이 npx로 바로 실행할 수 있습니다.

```bash
# Zero-install
npx oh-my-harness init "TypeScript Next.js frontend with Python FastAPI backend"

# 또는 전역 설치 (짧은 alias omh 제공)
npm install -g oh-my-harness
omh init "React app with TDD"
```

이렇게 자연어로 프로젝트를 설명하면 언어·프레임워크·패키지 매니저를 자동 감지해서 `harness.yaml`과 런타임별 설정을 생성합니다. NL 처리는 Claude CLI(기본), Claude API, OpenAI API, Gemini API, Codex OAuth 등 멀티 프로바이더를 지원하고, 첫 실행 시 인터랙티브 UI로 선택할 수 있습니다.

생성 후에 쓰게 되는 커맨드들도 같이 소개하면:

```bash
omh catalog list  # 블록 카탈로그 목록
omh test          # 드라이런으로 harness 검증
omh stats         # TUI 분석 대시보드
omh diff          # sync가 바꿀 내용 프리뷰
omh sync --check  # 생성 파일이 stale하면 exit 1 - CI 게이트
```

## 마치며

재밌는 사실 하나 - 이 프로젝트 자체가 자기 자신의 harness로 개발되고 있습니다(dogfooding). TDD Guard, branch-guard, commit-test-gate 등 12개 훅이 활성화된 상태로, "테스트 먼저 수정 → 실패 확인 → 최소 구현" 워크플로우가 강제된 채 900개 이상의 테스트와 함께 개발 중입니다. AI 에이전트에게 코딩을 시키면서도 품질이 무너지지 않는 경험을 직접 하고 있으니, 에이전트가 자꾸 말을 안 듣는다면 ~~혼내지 마시고~~ 한번 채워보세요, 가드레일 ⚡️

## Reference

- https://github.com/kyu1204/oh-my-harness
- https://www.npmjs.com/package/oh-my-harness
