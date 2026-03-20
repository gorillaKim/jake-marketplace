---
title: "{title}"
aliases:
  - "{english-alias}"
  - "{한글 별칭}"
tags:
  - architecture
  - "{domain-tag}"
  - "{tech-tag}"
created: "{YYYY-MM-DD}"
updated: "{YYYY-MM-DD}"
---

<!-- docsmith: auto-generated {YYYY-MM-DD} -->

# {title}

이 문서의 목적과 범위를 1-2문장으로 설명합니다.

## 구조 개요

```mermaid
graph TD
    A[모듈 A] --> B[모듈 B]
    A --> C[모듈 C]
    B --> D[모듈 D]
```

## 모듈 설명

### 모듈 A

- **역할**:
- **의존**:
- **핵심 파일**:

### 모듈 B

- **역할**:
- **의존**:
- **핵심 파일**:

## 데이터 흐름

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Core
    participant DB
    User->>API: 요청
    API->>Core: 처리
    Core->>DB: 저장/조회
    DB-->>Core: 결과
    Core-->>API: 응답
    API-->>User: 결과
```

## 설계 결정

주요 설계 결정과 그 근거를 기술합니다.

## 관련 문서

- [[관련 문서 1]]
- [[관련 문서 2]]
