# 공통 계약 초안

문서 버전: `0.1.0-draft.1`. 이 디렉터리는 **P0 검토용 schema/fixture**이며 정식 공통 패키지나 제품 구현이 아닙니다.

- [ContextRecord](draft-0.1/context-record.schema.json): 서버가 관리하는 지식 기록의 출력 모델.
- [ContextChange](draft-0.1/context-change.schema.json): 승인 후보를 준비하는 최소 입력. 승인·사용자 권한 필드는 없음.
- [KnowledgeEnvelope](draft-0.1/knowledge-envelope.schema.json): 명시적 내보내기용 교환 구조.
- [fixture index](fixture-index.json): 정상 4개와 의도적인 금지 입력 4개.

모든 예제는 가상입니다. `examples/`의 정상 자료를 실제 사용자 기록이라고 말하지 마세요. `fixtures/invalid_*`는 실패가 정답입니다.

Schema ID의 `example.invalid`는 예약된 예시 URI이며 네트워크로 접근하지 않습니다. 검증기는 로컬 registry로만 `$ref`를 해석합니다.

JSON Schema는 권한, 실제 사용자 승인, 시점 순서, 참조의 존재, 동일 프로젝트, cycle, idempotency, 삭제 전파를 검증하지 못합니다. 이 불변 조건은 [데이터 모델](../docs/03_CONTRACTS_AND_DATA_MODEL.md)과 제품 시험에 별도로 구현해야 합니다.

P1에서 의미를 확정하고 별도 contracts 저장소로 옮길 때 파일 경로·ID·version 정책·consumer compatibility를 함께 갱신합니다. 원본 Code Plugin vocabulary를 바꾸지 않습니다.
