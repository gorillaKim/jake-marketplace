---
title: "{LogicName} Techspec 생성 프롬프트"
aliases:
  - "{LogicName} spec prompt"
  - "{한글명} 스펙 프롬프트"
tags:
  - template
  - prompt
  - spec
created: "{YYYY-MM-DD}"
updated: "{YYYY-MM-DD}"
---

<!-- docsmith: auto-generated {YYYY-MM-DD} -->

# {LogicName} Techspec 생성 프롬프트

이 파일은 `{LogicName}.spec.md`를 생성할 때 Claude에 전달한 프롬프트를 기록합니다.
스펙 수정·재생성 시 이 프롬프트를 참고하거나 수정하여 재사용하세요.

---

## Claude에게 전달한 프롬프트

```
다음 정보를 바탕으로 요구사항 명세 문서를 Markdown으로 작성해줘.

## 기본 정보

**로직명:** [PascalCase 영문명]
**한글명:** [설명]
**목적:** [한두 문장으로 목적과 역할 설명]
**타입:** component / api / service / cli / hook / util (해당하는 것)

---

## 기능 요구사항

다음 기능들을 구현해야 합니다:

1. [기능 1]
2. [기능 2]
3. [기능 3]

---

## 인터페이스 정의

### Props / API / CLI args

[해당하는 인터페이스를 작성합니다]

예시 (Props):
interface [ComponentName]Props {
  prop1: type
  prop2?: type // default: 값
  children?: React.ReactNode
}

예시 (REST API):
POST /api/path
Request: { field: type }
Response: { result: type }

---

## 제약사항

- [제약 1]
- [제약 2]
- 사용 라이브러리: [예: react-spring, zod, express]
- 호환성: [변경 불가 사항들]

---

## 성공 기준

구현 완료 시 다음을 확인할 수 있어야 합니다:

1. [기준 1]
2. [기준 2]

---

## 참고 자료

- 참고 코드: [[기존 관련 파일명]]
- 유사 로직: [프로젝트 내 유사 구현]

---

## 출력 형식

techspec.md 템플릿 구조를 따라 작성해줘:

Frontmatter:
- title: "[LogicName] 요구사항 명세"
- aliases: 영문명, 한글명 등
- tags: spec, [domain-tag 1-3개]

필수 섹션: 개요, 기능 요구사항, 제약사항, 성공 기준, 인터페이스 정의
선택 섹션: 부가 스펙, 사용 예시
```

---

## 생성된 문서

- 스펙: [[{LogicName} 요구사항 명세]]

---

## 관련 문서

- [[관련 문서 1]]
