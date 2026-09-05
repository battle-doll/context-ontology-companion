# 03. 공통 계약과 데이터 모델

## 계약 원칙

계약은 저장소나 특정 언어 구현보다 먼저 고정합니다. 이 패키지의 JSON Schema는 `0.1.0-draft.1` **검토용 초안**입니다. 정식 공통 계약 저장소/패키지가 발행된 것은 아닙니다. 예약된 `schemas.example.invalid` URI는 식별자이며 네트워크에서 내려받을 대상이 아닙니다.

공통 개념은 Entity, Relation, Evidence, SourceReference, Validity, Revision, Supersession입니다. `co:` 코드 vocabulary를 새로운 문맥 vocabulary로 바꾸거나 동일 이름의 관계를 같은 의미로 가정하지 않습니다.

## 서로 독립적인 네 가지 축

| 축 | 예 | 의미 |
| --- | --- | --- |
| origin | `user_asserted`, `document_observed`, `model_inferred` | 누가/무엇을 근거로 주장했는가 |
| extraction_method | `direct_user_input`, `quoted_excerpt`, `rule_based`, `model_generated` | 어떻게 구조화했는가 |
| review.status | `pending`, `user_approved`, `rejected` | 사용자가 저장 내용을 검토했는가 |
| verification | `unverified`, `source_checked` | 원본과의 일치가 확인됐는가 |

사용자 승인은 사실성을 보장하지 않습니다. `source_checked`는 출처와 일치한다는 뜻이지 외부 사실의 진실 판정이 아닙니다. 모델 제안을 승인해도 origin을 자동으로 직접 진술로 바꾸지 않습니다. 사용자가 별도로 사실을 진술하면 새 출처/새 revision으로 기록합니다.

수치 confidence를 진실 확률처럼 사용하지 않습니다. MVP는 정성적 provenance와 검토 상태를 사용합니다. 이후 점수를 추가하면 무엇에 대한 점수인지, 산출 방법·버전·보정 시험을 함께 기록해야 합니다.

## ContextRecord

`contracts/draft-0.1/context-record.schema.json`의 주요 필드:

| 필드 | 역할 |
| --- | --- |
| `id`, `revision`, `schema_version` | 불투명 식별자, revision, 계약 버전 |
| `project_id` | 서버가 권한을 확인한 프로젝트 식별자 |
| `kind` | Decision / Goal / Requirement / Constraint |
| `statement` | 승인된 최소 자연어 문장 |
| `subject`, `predicate`, `object` | 해당 문맥의 구조화된 의미 |
| `origin`, `extraction_method`, `verification` | 위 세 축 |
| `review` | 검토 상태·시각·승인 방법. 서버가 기록 |
| `sources` | 최소 source reference와 선택된 짧은 excerpt |
| `valid_from`, `valid_until` | 실제 적용 시간의 반개구간 `[from, until)` |
| `recorded_at` | 시스템이 기록한 시각 |
| `status` | proposed / active / disputed / superseded / retracted |
| `supersedes` | 이전 revision 식별자. 자기참조·cycle 금지 |

삭제된 본문은 정상 ContextRecord로 보존하지 않습니다. payload를 지운 별도 최소 erasure receipt를 사용합니다. `status=erased`만 붙이고 statement를 남기는 방식은 “삭제”가 아닙니다.

## 시간 의미

모든 wire timestamp는 UTC ISO 8601이며, UI는 사용자의 시간대로 보여줍니다. 시간대가 없는 사용자 입력은 프로젝트 시간대 확인 없이 추정하지 않습니다. 유효 시점과 기록 시점은 별개입니다. 예를 들어 9월 5일에 “9월 1일부터 적용”한다고 저장할 수 있습니다.

`valid_until`은 null 또는 `valid_from`보다 커야 합니다. 같은 시간의 변경 순서는 DB revision/transaction으로 정하며 wall-clock 정렬만으로 승자를 만들지 않습니다. 과거 시점의 상태 조회와 현재 DB가 알고 있는 과거 사실은 다른 질의입니다. MVP는 적용 시점 as-of를 지원하고, 완전한 양시점 조회는 P0에서 범위를 확정합니다.

## SourceReference

출처는 실제로 전달받은 범위만 표현합니다. 호스트가 메시지 ID를 제공하지 않았다면 가짜 대화 ID를 만들지 않습니다. 서버 생성 source ID는 내부 관리용이지 플랫폼 원문 확인 증명이 아닙니다.

짧은 excerpt를 저장하지 않은 source reference도 허용합니다. 접근 불가능한 출처는 `unavailable`로 표시하고 확인했다고 주장하지 않습니다. 상대 경로와 symbol 이름도 기밀일 수 있으므로 코드 연결 시 별도 공유 범위를 확인합니다.

## 서버 불변 조건 — JSON Schema만으로 검사할 수 없음

1. 인증된 주체가 프로젝트와 모든 참조 대상에 접근할 수 있어야 합니다.
2. 활성 기록은 유효한 사용자 승인을 거쳐야 합니다. payload에 포함된 승인 필드는 신뢰하지 않습니다.
3. `valid_until > valid_from`, UTC 규칙, revision 증가를 검증합니다.
4. source reference는 실제 존재하고 같은 프로젝트/허용 범위여야 합니다.
5. supersedes 대상이 같고, 기대 revision이 일치하며, 자기참조/순환이 없어야 합니다.
6. 추론 origin은 사용자 승인만으로 바뀌지 않습니다.
7. 같은 idempotency key와 payload는 중복 기록을 만들지 않습니다.
8. 철회·삭제·만료된 기록은 현재 검색에서 나타나지 않습니다.
9. 삭제된 source에 의존하는 파생 주장·요약·인덱스를 추적할 수 있어야 합니다.
10. `contradicts` 관계는 발견 후보일 수 있으며 자동 폐기 명령이 아닙니다.

## 계약 진화

정식 계약은 semantic version을 사용합니다. 필드 삭제·의미 변경·새 required 필드는 호환성 파괴입니다. 새로운 선택 필드도 `additionalProperties=false`인 이전 validator에서 실패할 수 있으므로 버전 협상 없이 “항상 호환”이라고 하지 않습니다.

소비자는 지원하는 schema version을 명시하고 알 수 없는 버전을 안전하게 거절합니다. upcaster는 원본 계약을 보존하고 변환 버전/손실/출처를 기록합니다. 두 제품이 모두 사용하는 core 추출은 실제 동일 동작 테스트가 생긴 후 진행합니다.

[계약 안내](../contracts/README.md) · [코드 연결](11_COMMON_CORE_AND_CODE_BRIDGE.md)

## v2: Context 교환 형식과 공통 계약 구분

현재 draft-0.1의 knowledge-envelope는 ContextRecord와 ctx_ ID에 고정되어 있어 **Context 전용**입니다. schema-valid라는 사실만으로 Code 호환성을 주장하지 않습니다. 별도 Contracts 프로젝트에서 최소 envelope metadata와 code/context profile을 정의한 뒤 실제 두 소비자의 fixtures로 검증합니다. 원본 draft 스키마는 변경하지 않았으며, 새 DESIGN_VERSION은 schema_version을 자동으로 올리지 않습니다.

검증 결과에는 schema/profile semantic/reference/compatibility의 수행 여부와 `not_checked`를 구분합니다. 문법 통과는 사실·사용자 권한·현재 승인 검증이 아닙니다. 역사 known-at 질의는 완전한 기록 시점 재구성과 삭제 처리를 구현한 후에만 지원합니다.
