---
title: "{LogicName} 요구사항 명세"
aliases:
  - "{english-alias}"
  - "{한글 별칭}"
tags:
  - spec
  - "{domain-tag}"
created: "{YYYY-MM-DD}"
updated: "{YYYY-MM-DD}"
---

<!-- docsmith: auto-generated {YYYY-MM-DD} -->

# {LogicName} 요구사항 명세

## 개요

[로직/컴포넌트의 목적과 역할을 명확하게 설명합니다]
[사용되는 컨텍스트, 해결하는 문제를 포함합니다]

---

## 기능 요구사항

체크리스트 형식으로 구현해야 할 기능을 상세하게 나열합니다.

- [ ] [기능 1]
- [ ] [기능 2]
- [ ] [기능 3]

---

## 제약사항

구현 시 지켜야 할 제약사항과 주의사항을 명시합니다.

- [제약사항 1]
- [제약사항 2]
- 사용 가능한 라이브러리/도구: [예: react-spring, zod, express]
- 기존 코드와의 호환성: [변경하면 안 되는 것들]

---

## 성공 기준

구현 완료 시 확인해야 할 구체적인 기준들입니다.

- [기준 1]
- [기준 2]
- 시각적/기능적 검증: [정량적 기준]

---

## 인터페이스 정의

해당하는 형식으로 작성합니다. (Props / REST API / CLI args / 함수 시그니처)

### Props (React 컴포넌트인 경우)

```typescript
interface {LogicName}Props {
  /** prop 설명 */
  prop1: type

  /** 선택적 prop — 기본값 명시 */
  prop2?: type // default: [기본값]

  /** 자식 요소 */
  children?: React.ReactNode
}
```

| Props | 타입 | 기본값 | 필수 | 설명 |
| ----- | ---- | ------ | ---- | ---- |
| `prop1` | `type` | — | ✓ | [설명] |
| `prop2` | `type` | `defaultValue` | — | [설명] |

### API 엔드포인트 (REST API인 경우)

```
METHOD /path

Request:
  - header: ...
  - body: { field: type }

Response:
  - 200: { field: type }
  - 4xx: { error: string }
```

### CLI args / 함수 시그니처 (해당하는 경우)

```
명령어 또는 함수 시그니처
```

---

## 부가 스펙 (선택)

**애니메이션, 스타일, 데이터 스키마 등 추가 명세가 필요한 경우 작성**

### 스타일 명세

| 항목 | 속성 | 값 | 비고 |
| ---- | ---- | --- | ---- |
| — | — | — | — |

### 애니메이션 상세

| 구분 | Property | 값 | Duration | 비고 |
| ---- | -------- | --- | -------- | ---- |
| — | — | — | — | — |

---

## 사용 예시 (선택)

```tsx
// 실제 사용 방식을 보여주는 예제
```

---

## 관련 문서

- [[관련 문서 1]]
- [[관련 문서 2]]
