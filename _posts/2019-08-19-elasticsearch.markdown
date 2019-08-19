---
published: true
title: Elasticsearch DSL 쿼리 정리
series:
categories: Blog
tags: [Elasticsearch]
layout: post
excerpt:
comments: yes
toc: true
---
## Elasticsearch DSL 쿼리
### 1. 검색 쿼리
must: AND
shuold: OR
must_not: NOT
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
          ],
          "must_not": [],
          "should": []
        }
      }
    }
  },"size":1
}

terms 쿼리
{
  "query":{
    "bool":{
      "filter":{
        "bool":{
          "must":[
            {
              "terms":{
                "field_name": ["field_value1", "field_value2"]
              }
            }
          ],
          "must_not": [],
          "should": []
        }
      }
    }
  },"size":1
}

random 쿼리
{
 "query": {
   "function_score": {
     "query": {
       "bool": {
         "must": [
           {
             "match": {
               "field": "field_value"
             }
           }
         ],
         "must_not": [],
         "should": []
       }
     },
     "random_score": {}
   }
 },"size": 1
}
```
