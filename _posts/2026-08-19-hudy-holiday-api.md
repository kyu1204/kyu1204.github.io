---
title: HuDy - 대한민국 공휴일 API 서비스
description: 대한민국 공휴일 조회부터 영업일 계산, 캘린더 동기화, MCP 서버까지 제공하는 공휴일 API 서비스 HuDy(휴디)를 소개합니다.
categories: [hudy, api]
tags: [holiday, api, rest-api, saas, rust, nextjs, mcp]
image: /assets/img/hudy-og.png
date: 2026-08-19 00:00:01 +09:00
---

## 개요

서비스를 만들다 보면 꼭 한 번은 마주치는 요구사항이 있습니다. 바로 **"공휴일 처리"**.

> - 정산 배치를 영업일에만 돌려야 하는데, 다음 영업일이 언제지?
> - 예약 시스템에서 공휴일은 선택 못 하게 막아야 하는데?
> - 대체공휴일은... 이게 올해는 언제더라?

공공데이터포털 API를 써보신 분들은 아시겠지만, 인증키 발급받고, XML 파싱하고, 응답이 느리거나 가끔 죽어있는 걸 겪다 보면 "공휴일 하나 가져오는 게 왜 이렇게 힘들지"라는 생각이 듭니다 🥲

그래서 만들었습니다. 바로 [HuDy(휴디)](https://hudy.co.kr)!

대한민국 공휴일 데이터를 깔끔한 REST API로 제공하는 서비스입니다. 공공데이터포털의 한국천문연구원 공식 데이터를 기반으로 법정공휴일·대체공휴일·임시공휴일까지 정확하게 제공하며, 회원가입 후 API 키만 발급받으면 바로 사용할 수 있습니다.

## 주요 기능

### 공휴일 조회 API

연도별 공휴일을 JSON으로 조회할 수 있습니다. 설날·추석 연휴는 물론 대체공휴일, 임시공휴일까지 모두 포함되어 있어서 직접 계산할 필요가 없습니다.

```bash
curl "https://api.hudy.co.kr/v2/holidays?year=2026" \
  -H "x-api-key: YOUR_API_KEY"
```

```json
{
  "result": true,
  "data": [
    {
      "id": "1",
      "name": "신정",
      "date": "2026-01-01",
      "type": "public"
    }
  ]
}
```

### 영업일 계산

"이 날이 영업일인가?"를 넘어 실무에서 진짜 필요한 계산들을 API 한 번으로 해결합니다. 주말과 공휴일은 자동으로 제외됩니다.

```bash
# 특정 날짜의 영업일 여부 확인
GET /v2/business-days/check?day=2026-02-17

# 기간 내 영업일 수 계산
GET /v2/business-days/count?from=2026-01-01&to=2026-01-31

# N영업일 후 날짜 계산
GET /v2/business-days/add?from=2026-02-15&days=10
```

정산 배치, 알림 발송, 예약 시스템처럼 영업일 기준으로 동작해야 하는 로직에 그대로 붙일 수 있습니다.

### 커스텀 공휴일

회사 창립기념일이나 사내 행사일처럼 서비스마다 다른 휴일이 있죠. 커스텀 공휴일을 등록하면 법정 공휴일과 합쳐서 조회·영업일 계산에 반영됩니다.

### 캘린더 동기화

iCal 형식 구독을 지원해서 구글 캘린더, 애플 캘린더에 공휴일을 자동 동기화할 수 있습니다. 개발자가 아니어도 쓸 수 있는 기능이에요.

### 공식 SDK

Node.js/TypeScript와 Python 공식 SDK를 제공합니다.

```javascript
// npm install @hudy-sdk/sdk
import { HudyClient } from '@hudy-sdk/sdk'

const client = new HudyClient({ apiKey: 'hd_live_xxxx' })
const holidays = await client.getHolidays(2026)
```

```python
# pip install hudy-sdk
from hudy import HudyClient

client = HudyClient(api_key="hd_live_xxxx")
holidays = client.get_holidays(2026)
```

### MCP 서버

요즘 대세인 MCP도 지원합니다. Claude Desktop, Claude Code, Cursor 같은 AI 도구에 HuDy를 연결하면 AI가 직접 공휴일 조회·영업일 계산을 수행합니다.

```bash
claude mcp add --transport http -H "x-api-key: YOUR_API_KEY" hudy https://www.hudy.co.kr/api/mcp
```

"다음 달 영업일이 며칠이야?"라고 AI에게 물어보면 알아서 HuDy를 호출해 답해줍니다 ⚡️

## 요금제

| 플랜 | 가격 | 월 API 호출 | 주요 기능 |
|------|------|------------|---------|
| **Free** | 무료 | 100회 | 기본 공휴일 조회 |
| **Pro** | $3/월 | 5,000회 | 커스텀 공휴일, 영업일 계산, iCal 동기화, 우선 지원 |

Pro 플랜은 30일 무료 체험을 제공하니 부담 없이 써볼 수 있습니다. 사이드 프로젝트라면 Free로도 충분히 시작할 수 있어요.

## 기술 이야기 조금

코어 API 서버는 Rust(actix-web)로 작성했고 캐시 기반으로 응답하기 때문에 매우 빠릅니다 (100ms 이내 응답, 99.9% Uptime). 프론트는 Next.js + React, 데이터베이스는 Supabase(PostgreSQL) 구성입니다.

보안에도 신경을 많이 썼는데, API 키는 평문 저장 없이 **sha256 해시로만 저장·검증**되며 전체 키는 발급 시점에 딱 한 번만 노출됩니다. GitHub 토큰처럼요.

## 마치며

"공휴일 API"라고 하면 작아 보이지만, 막상 직접 구현해보면 대체공휴일 규칙이나 설·추석 연휴 계산, 시간대 처리 같은 함정이 곳곳에 숨어있습니다. 이런 반복 작업을 서비스 하나로 끝내고 싶어서 시작한 프로젝트인데, 감사하게도 검색을 통해 찾아와 주시는 분들이 조금씩 늘고 있습니다.

공휴일 처리 때문에 골치 아프셨던 분들은 [hudy.co.kr](https://hudy.co.kr)에서 한번 사용해보세요. 피드백은 언제나 환영입니다 🙌

## Reference

- [HuDy](https://hudy.co.kr)
