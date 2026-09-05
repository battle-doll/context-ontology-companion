# 문서 목차

| 순서 | 문서 | 용도 |
| --- | --- | --- |
| 00 | [결정 요약](00_DECISION_BRIEF.md) | 지금까지의 대화, 승인된 방향, 과장·가정 보정 |
| 01 | [제품 요구사항](01_PRODUCT_REQUIREMENTS.md) | MVP 범위, 기능과 완료 기준 |
| 02 | [아키텍처](02_ARCHITECTURE.md) | 제품·데이터·배포 경계와 모듈 |
| 03 | [공통 계약과 모델](03_CONTRACTS_AND_DATA_MODEL.md) | 출처·시간·판정·관계의 규칙 |
| 04 | [문맥 생명주기·검색](04_MEMORY_LIFECYCLE_RETRIEVAL.md) | 승인 저장, 대체, 검색, 복구 |
| 05 | [MCP·승인 설계](05_MCP_AND_APPROVAL.md) | 도구 초안과 서버가 확인하는 승인 |
| 06 | [개인정보·보안](06_PRIVACY_SECURITY.md) | 위협, 격리, 삭제, 최소 수집 |
| 07 | [출시 로드맵](07_RELEASE_ROADMAP.md) | P0–P6, 의존성과 통과 조건 |
| 08 | [시험·평가](08_TEST_AND_EVALUATION.md) | 기능·안전·검색·연동 검증 |
| 09 | [공개 등록 런북](09_PUBLIC_PLUGIN_SUBMISSION.md) | 공식 포털, 심사·게시, 소유자 절차 |
| 10 | [Codex 인계서](10_CODEX_HANDOFF.md) | 실제 작업 지시와 재개 규칙 |
| 11 | [공통 코어·코드 연결](11_COMMON_CORE_AND_CODE_BRIDGE.md) | 계약 분리와 기존 제품 무변경 통합 |
| 12 | [미결정·위험](12_OPEN_QUESTIONS_AND_RISKS.md) | 소유자 결정과 기술 검토 분리 |
| 13 | [출처·검증](13_SOURCES_AND_VERIFICATION.md) | 실제 확인한 근거와 불확실성 |
| 14 | [운영·비용](14_OPERATIONS_AND_COSTS.md) | 운영 준비와 지출 승인 |
| 15 | [작업 백로그](15_TASK_BACKLOG.md) | Codex가 작은 PR로 옮길 작업 단위 |

## 설계 결정 기록

- [ADR-0001 제품 분리](adr/0001-product-separation.md)
- [ADR-0002 계약 우선](adr/0002-contract-first.md)
- [ADR-0003 명시적 문맥과 승인](adr/0003-explicit-context.md)
- [ADR-0004 이력과 삭제](adr/0004-history-and-erasure.md)
- [ADR-0005 순수 코어](adr/0005-pure-core.md)

## 작업 상태와 기계 판독 산출물

[현재 상태](agent/CURRENT_STATE.md) · [다음 작업](agent/NEXT_ACTIONS.md) · [P0 계획](agent/plans/P0_DESIGN_REVIEW.md) · [관측성 보고서 양식](agent/WORK_REPORT_TEMPLATE.md) · [초기 작업 보고서](agent/reports/2026-08-29-design-bootstrap.md)

[공통 계약 초안](../contracts/README.md) · [시험 시나리오](../evals/README.md) · [제출 준비 상태](../submission/README.md)

## 2026-09-05 재평가와 개선

- [16. 재평가 보고서](16_REEVALUATION_2026-09-05.md)
- [17. 문맥 재구성기](17_CONTEXT_COMPILER.md)
- [18. 작업 재개 평가](18_EVAL_PROTOCOL.md)
- [19. 모델 실행 프로필](19_MODEL_EXECUTION_PROFILE.md)
- [ADR 0006](adr/0006-contracts-public-plugin.md), [ADR 0007](adr/0007-consumer-driven-contract.md), [ADR 0008](adr/0008-atomic-context-budget.md)
