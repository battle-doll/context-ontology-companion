# 11. 공통 계약·코어 및 코드 그래프 연결

## 목표 저장소 구성

```text
battle-doll/code-ontology-companion       기존 제품, 변경 없이 유지
battle-doll/context-ontology-companion    새 제품과 설계·개발
battle-doll/ontology-companion-contracts  P1에서 정식 교환 계약 분리
battle-doll/ontology-companion-core       P5에서 실제 공통 코드만 분리
```

후자의 세 이름은 계획입니다. 이 패키지 작성 시 새 원격 저장소를 생성하지 않았습니다. 초기부터 4개 저장소를 무조건 동시에 운영하지 않습니다.

## 계약 패키지의 내용

언어 중립 JSON Schema, namespace/term 정의, Evidence와 SourceReference, 시간과 supersession 의미, 예제/금지 fixture, migration/compatibility matrix를 제공합니다. 코드와 문맥 분야별 의미는 별도 profile로 둡니다.

현재 Code Plugin의 `observed / declared / inferred / validated / approved` 계보는 문맥 record의 origin/review와 일대일 같은 enum이 아닙니다. 둘을 원문 의미와 함께 보존하는 mapping envelope를 사용합니다.

| 코드 쪽 의미 | Context에서의 처리 |
| --- | --- |
| direct_syntax / resolved_static | 코드 정적 추출 근거로 보존, 실행 사실로 승격하지 않음 |
| framework_semantic / name_heuristic | 제한사항을 함께 보존 |
| runtime_unknown | 실행/운영 사실 미확인임을 유지 |
| inferred sidecar | 별도 추론 근거로 연결, observed graph에 병합하지 않음 |
| validated / approved lineage event | 무엇을 검증/승인했는지 범위를 명시, 사용자 사실 승인과 혼동 금지 |

## 최소 코드 참조

bridge는 repository identity, immutable revision, snapshot identity, symbol identity, 허용된 source span, evidence classification을 사용합니다. 절대 로컬 경로·파일 본문·전체 hash manifest·credential은 기본 payload에 넣지 않습니다.

같은 symbol 이름이 있다는 이유로 동일 엔티티로 합치지 않습니다. repo/revision/snapshot을 포함해 식별하고, rename 또는 코드 이동은 mapping 근거가 없으면 unresolved로 남깁니다.

```text
가상 결정 "배포 전에 회귀 테스트 수행"
  -> relates_to -> 승인된 demo repository의 ReleasePipeline symbol
  -> supported_by -> 사용자가 선택한 결정 발췌
  -> effective_from -> 적용 시각
```

`relates_to`와 `caused_by`, `implemented_by`는 다릅니다. 코드가 바뀐 시점과 결정 시점이 가깝다는 이유로 인과 관계를 만들지 않습니다.

## egress 경계

사용자는 어떤 metadata가 로컬에서 원격 Context 서비스로 나가는지 확인해야 합니다. 코드 플러그인 자체가 조용히 업로드하도록 변경하지 않습니다. standalone portable export를 사용자가 명시적으로 제공하는 방식이 우선입니다.

읽기 전용 MCP를 가진 코드 플러그인을 새 서비스에서 쓰기 가능하게 바꾸지 않습니다. 관련 수정이 필요하면 기존 정책에 따라 별도 설계/승인/PR/회귀 검증을 수행합니다. [R-03](13_SOURCES_AND_VERIFICATION.md)

## 순수 코어 추출 기준

두 소비자에서 같은 입력에 같은 결과가 필요한 validation/canonicalization/temporal/relation 함수가 실제로 중복될 때 추출합니다. 공통 DB, cloud service, user profile, 임베딩, LLM provider를 core에 넣지 않습니다.

기존 코드 플러그인의 표준 라이브러리 중심 실행과 결정론적 배포 경계를 유지할 수 없다면 별도 library 의존 대신 versioned exchange contract만 사용합니다. 공유 그 자체가 목적은 아닙니다.

## 호환성 gate

기존 source/target/type triples, stable IDs, co vocabulary, evidence metadata, portable privacy와 동일 입력의 정규화 결과를 기존 golden fixture로 검증합니다. 기존 source를 다시 실행하거나 새 버전을 배포한 척하지 않습니다. 저장소 문서만 읽은 것은 runtime 검증이 아닙니다.

## v2: 의존 방향과 공통화 범위

Contracts 공통 데이터 배포물을 Code/Context가 각각 pin하거나 필요한 부분만 출처·라이선스와 함께 vendor합니다. Contracts plugin을 설치하지 않아도 소비자 기능은 작동해야 합니다. 런타임에 부모 플러그인을 호출하는 구조는 요구하지 않습니다. Code graph의 기존 stable IDs/co: namespace를 바꾸지 않고 profile mapping으로 연결합니다. 같은 순수 실행 코드의 실제 재사용이 확인되기 전에는 새 core 저장소/네 번째 plugin을 만들지 않습니다.
