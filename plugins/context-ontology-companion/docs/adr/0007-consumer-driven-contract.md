# ADR 0007 — 소비자 검증을 거친 계약 확정

상태: 권장 실행 순서.

Context 전용 envelope를 공통 형식이라 부르는 문제를 고칩니다. P1a에서 작은 공통 metadata와 두 profile의 샘플을 작성하고, 소비자와 검증기가 같은 draft를 실제 처리하도록 합니다. P1b에서 지원 버전/프로필만 릴리스합니다. 초기에 모든 자연어·코드 관계를 통합한 거대한 universal ontology를 확정하지 않습니다.

기존 code stable IDs 및 co: 의미는 유지하며 별도 mapping으로 연결합니다. 과거 context draft는 보존합니다. 새 필드를 추가해도 기존 strict reader가 깨질 수 있으므로 버전 compatibility를 fixtures로 입증합니다.
