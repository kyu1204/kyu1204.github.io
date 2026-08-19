---
title: GitHub Actions self-hosted runner를 Mac mini에 세팅하며 겪은 함정들
description: launchd 환경의 keychain 오류, svc.sh 하드코딩, arm64 이미지 매니페스트 문제까지 - Mac mini에 self-hosted runner를 올리며 실제로 밟은 함정 4가지를 정리했습니다.
categories: [devops, ci-cd]
tags: [github-actions, self-hosted-runner, macos, launchd, docker, arm64, ci/cd]
image: /assets/img/gh-actions-runner.png
date: 2026-08-19 00:00:02 +09:00
---

## 개요

집에서 놀고 있는 Mac mini, 다들 한 대쯤 있으시죠? ~~없으면 지금이 살 기회~~ 사이드 프로젝트가 늘어나다 보면 GitHub Actions의 무료 러너로는 아쉬운 순간이 옵니다. 빌드는 느리고, 배포 대상 서버에 SSH로 들어가는 시크릿 관리도 번거롭고요.

그래서 Mac mini를 배포 서버 겸 **self-hosted runner** 호스트로 쓰기 시작했는데, 결론부터 말하면 아주 만족스럽습니다. CI가 완료되면 러너가 같은 머신에서 `docker compose pull && up -d`까지 알아서 해주니까요. 다만 여기까지 오는 길에 함정을 여러 개 밟았습니다 🥲

이 포스트에서는 실제로 겪은 함정 4가지를 에러 메시지와 함께 정리합니다.

> 1. launchd 러너에서 docker login이 안 되는 문제 (keychain)
> 2. 러너 디렉터리 복사 셋업 시 `svc.sh` 하드코딩 함정
> 3. `no matching manifest for linux/arm64/v8`
> 4. 러너 여러 개 공존 시 이름 충돌

## 기본 셋업

셋업 자체는 공식 문서대로 하면 어렵지 않습니다. 레포의 **Settings → Actions → Runners → New self-hosted runner** 에서 안내하는 대로 진행하면 됩니다.

```bash
mkdir ~/actions-runner && cd ~/actions-runner
curl -o actions-runner-osx-arm64.tar.gz -L https://github.com/actions/runner/releases/download/v2.319.1/actions-runner-osx-arm64-2.319.1.tar.gz
tar xzf ./actions-runner-osx-arm64.tar.gz

./config.sh --url https://github.com/OWNER/REPO --token XXXX
```

그리고 macOS에서는 러너를 launchd 서비스로 등록해 상시 구동시킵니다.

```bash
./svc.sh install
./svc.sh start
```

여기까지는 순조롭습니다. 문제는 이제부터 시작입니다.

## 함정 1: launchd 러너에서 docker pull이 실패한다

워크플로우에서 ghcr.io 프라이빗 이미지를 pull하는 단계가 이런 에러로 죽었습니다.

```
Error saving credentials: error storing credentials - err: exit status 1,
out: `error storing credentials - err: exit status 1,
out: `The user name or passphrase you entered is not correct. (-25308)`
```

`-25308`은 macOS의 `errSecInteractionNotAllowed` 에러입니다. 터미널에서 직접 `docker login` 하면 멀쩡히 되는데 러너에서만 실패하니 처음엔 꽤 혼란스럽습니다.

원인은 이렇습니다. macOS의 docker는 기본적으로 자격증명을 **keychain**(osxkeychain credential helper)에 저장하는데, launchd로 뜬 러너는 **GUI 세션이 없는 컨텍스트**라 keychain에 접근할 수 없습니다. 사람이 로그인한 터미널에서는 되고, launchd에서는 안 되는 이유죠.

해결은 러너 전용으로 **격리된 `DOCKER_CONFIG`**를 만들어 keychain을 우회하는 것입니다.

```bash
# 러너 전용 docker config 디렉터리 생성
mkdir -p ~/actions-runner/.docker

# credsStore 없이 auth를 직접 기입
cat > ~/actions-runner/.docker/config.json <<EOF
{
  "auths": {
    "ghcr.io": {
      "auth": "$(echo -n 'USERNAME:GHCR_TOKEN' | base64)"
    }
  }
}
EOF
```

그리고 워크플로우에서 이 config를 쓰도록 지정합니다.

```yaml
jobs:
  deploy:
    runs-on: self-hosted
    env:
      DOCKER_CONFIG: /Users/me/actions-runner/.docker
```

한 가지 함정이 더 있는데, `DOCKER_CONFIG`를 바꾸면 docker CLI가 **compose 플러그인도 그 경로에서 찾습니다.** OrbStack이나 Docker Desktop이 설치해둔 플러그인 경로를 심볼릭 링크로 연결해줘야 `docker compose`가 계속 동작합니다.

```bash
ln -s ~/.docker/cli-plugins ~/actions-runner/.docker/cli-plugins
```

## 함정 2: svc.sh의 서비스명 하드코딩

두 번째 프로젝트의 러너를 올릴 때였습니다. 셋업이 귀찮아서 기존 러너 디렉터리를 복사한 뒤 `config.sh`만 새로 돌렸는데, `./svc.sh install`을 하니 **기존 러너와 같은 launchd 서비스명**으로 등록되어 버렸습니다.

`svc.sh`를 열어보면 원인이 바로 보입니다.

```bash
#!/bin/bash
SVC_NAME="actions.runner.OWNER-REPO.runner-name"  # ← 최초 config 시점의 레포명이 하드코딩
```

`config.sh`를 다시 돌려도 이 파일은 갱신되지 않습니다. 복사 셋업을 했다면 **반드시 `SVC_NAME`을 새 레포·러너명으로 치환**하고 install 해야 합니다. 안 그러면 멀쩡히 돌던 기존 러너의 launchd 서비스를 덮어쓰는 대참사가 납니다 🥲

애초에 복사 셋업 대신 디렉터리를 새로 받아 구성하는 게 안전합니다.

## 함정 3: no matching manifest for linux/arm64/v8

CI에서 빌드한 이미지를 러너가 pull하는 순간 이런 에러가 났습니다.

```
no matching manifest for linux/arm64/v8 in the manifest list entries
```

원인은 단순합니다. CI의 빌드 잡이 `ubuntu-latest`(amd64)에서 `platforms` 지정 없이 이미지를 빌드하고 있었고, 배포 대상인 Mac mini는 **arm64(Apple Silicon)**였던 거죠. 예전에 x86 클라우드 인스턴스로 배포할 때는 문제가 없다가, 배포 대상을 Mac mini로 옮기는 순간 터졌습니다.

해결 방법은 두 가지입니다.

**방법 1: QEMU 멀티 플랫폼 빌드** - `docker/build-push-action`에 `platforms: linux/amd64,linux/arm64`를 추가합니다. 간단하지만 크로스 빌드라 느립니다. 특히 Rust처럼 컴파일이 무거운 프로젝트는 빌드 시간이 몇 배로 늘어납니다.

**방법 2: self-hosted 러너에서 네이티브 빌드** - 어차피 러너가 arm64 머신이니, 빌드 잡 자체를 `runs-on: self-hosted`로 돌려 네이티브 arm64 이미지를 만드는 방법입니다.

```yaml
jobs:
  build-and-push:
    runs-on: self-hosted  # arm64 네이티브 빌드
    steps:
      - uses: actions/checkout@v4
      - name: Build and push
        env:
          DOCKER_CONFIG: /Users/me/actions-runner/.docker
        run: |
          docker build -t ghcr.io/owner/repo:latest .
          docker push ghcr.io/owner/repo:latest
```

저는 Rust 프로젝트라 방법 2를 선택했고, 빌드 시간도 GitHub 호스티드 러너보다 오히려 빨라졌습니다.

교훈은 하나입니다. **배포 대상의 아키텍처와 이미지의 아키텍처를 항상 일치시킬 것.** 지금 문제가 없더라도 배포 대상이 바뀌는 순간 터지는 시한폭탄입니다.

## 함정 4: 러너 여러 개 공존시키기

프로젝트가 늘어나면 한 머신에 러너가 여러 개 공존하게 됩니다. 이때 각 러너는 다음이 전부 **머신 안에서 유일**해야 합니다.

> - 러너 디렉터리: `~/actions-runner-projectA`, `~/actions-runner-projectB` 처럼 분리
> - 러너 이름: `config.sh --name` 으로 프로젝트별 고유값 지정 (예: `macmini-projectA`)
> - launchd 서비스명: 함정 2의 `SVC_NAME` - 레포가 다르면 자동으로 달라지지만, 복사 셋업 시엔 직접 확인

"이 머신에 나 혼자 산다"는 암묵적인 가정이 모든 충돌의 원인입니다. 러너뿐 아니라 포트, 컨테이너 이름까지 - 새 프로젝트를 올리기 전에 네임스페이스부터 예약하는 습관을 들이면 사고가 확 줄어듭니다.

## 보너스: 배포 디렉터리는 git pull 대신 rsync

러너가 배포까지 담당한다면, 서버의 배포 디렉터리를 git pull로 갱신하고 싶어집니다. 그런데 배포 디렉터리의 git remote가 옛 조직/레포를 바라보고 있거나 인증이 꼬여있으면 pull이 조용히 실패합니다. checkout 받은 워크스페이스에서 **rsync로 필요한 파일만 동기화**하는 방식이 더 견고했습니다.

```yaml
- name: Sync deploy directory
  run: |
    rsync -av --exclude='.env' --exclude='.git' \
      ./ /Users/me/services/my-app/
```

단, `--delete` 옵션은 조심해야 합니다. 배포 디렉터리에 레포 밖에서 관리되는 파일(기동 스크립트, 설정 등)이 있다면 그대로 날아갑니다. `.env` 같은 파일은 반드시 exclude에 명시하세요.

## 마치며

Mac mini self-hosted runner 셋업의 함정들을 정리해봤습니다. 요약하면:

> 1. launchd 러너는 GUI 세션이 없다 → keychain 대신 격리 `DOCKER_CONFIG` (+ cli-plugins 심볼릭 링크)
> 2. `svc.sh`의 `SVC_NAME`은 하드코딩이다 → 복사 셋업 시 반드시 치환
> 3. 이미지 아키텍처는 배포 대상과 일치시킨다 → arm64는 네이티브 빌드가 빠르다
> 4. 러너명·서비스명·디렉터리는 머신 안에서 유일해야 한다

함정만 잘 피하면 push 한 번으로 빌드부터 배포·헬스체크까지 끝나는 파이프라인을 전기료만 내고 가질 수 있습니다. 놀고 있는 Mac mini가 있다면 한번 시도해보세요 ⚡️

## Reference

- [Adding self-hosted runners - GitHub Docs](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/adding-self-hosted-runners)
- [Configuring the self-hosted runner application as a service](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/configuring-the-self-hosted-runner-application-as-a-service)
- [actions/runner](https://github.com/actions/runner)
- [Docker credential helpers](https://github.com/docker/docker-credential-helpers)
