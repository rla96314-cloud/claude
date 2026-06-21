---
name: hello-demo
description: 사용자가 "hello demo"라고 하면 인사하고 현재 시간을 보고하는 데모 스킬.
triggers:
  - hello demo
  - 데모 스킬 테스트
---

## When to invoke this skill

사용자가 "hello demo" 또는 "데모 스킬 테스트"라고 말할 때.

## What to do

1. 한국어로 친근하게 인사한다.
2. 현재 UTC 시각을 `date -u` 로 확인해 보여준다.
3. 이게 사용자 정의 스킬임을 알린다.
