---
published: true
title:
series:
categories:
tags:
layout: post
excerpt:
comments: yes
toc: true
---
## Elasticsearch
### 1. 설치

### 2. 쿼리
```sh
match 쿼리
{
  "query":{
    "bool":{
      "filter":{
        "bool":{
          "must":[
            {
              "match":{
                "field_name": "field_value"
              }
            }
          ]
        }
      }
    }
  },"size":1
}
```
