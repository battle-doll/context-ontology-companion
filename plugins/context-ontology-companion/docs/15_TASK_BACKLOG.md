# 15. 작업 백로그

이 항목들은 GitHub issue로 변환할 수 있는 작업 명세입니다. 이 패키지에서는 실제 issue를 생성하지 않았습니다. 각 작업은 작은 feature branch/draft PR로 처리하며 선행 gate를 지킵니다.

| ID | 단계 | 작업 | 완료 조건 |
| --- | --- | --- | --- |
| TASK-001 | P0 | baseline/공식 문서 재검증 | immutable refs와 차이 기록 |
| TASK-002 | P0 | 독립 아키텍처·위협 리뷰 | 리뷰 결과와 ADR 수정 |
| TASK-003 | P0 | 승인 UX/호스트 spike | transaction-bound 승인 경로 입증 |
| TASK-004 | P0 | 스택·운영 경계 결정 | 비용 없는 로컬 default와 미결정 분리 |
| TASK-005 | P1 | 공통 vocabulary와 schema | 정상·금지 fixture 검증 |
| TASK-006 | P1 | 계약 version/migration 규칙 | 호환성 matrix와 부정 시험 |
| TASK-007 | P1 | contracts 분리 패키지 | 독립 빌드, 기존 코드 변화 없음 |
| TASK-008 | P2 | 순수 context domain | 시간·origin·대체·cycle 시험 |
| TASK-009 | P2 | storage/transaction | DB 동시성·idempotency 시험 |
| TASK-010 | P2 | 프로젝트 onboarding/ACL | 다른 계정 데이터 접근 0건 |
| TASK-011 | P2 | proposal/review/apply | 승인 조작·만료·변경 거절 |
| TASK-012 | P2 | 검색/pack | baseline 비교·한국어 질의·크기 제한 |
| TASK-013 | P2 | retract/erase/export | 지식 생명주기와 파생물 처리 |
| TASK-014 | P2 | 최소 관리 UI | 접근성·CSRF·XSS·동일 사용자 확인 |
| TASK-015 | P3 | remote MCP/OAuth | 표면별 인증·도구 E2E |
| TASK-016 | P3 | 최종 Skill/metadata | 실제 동작과 hint/schema 일치 |
| TASK-017 | P3 | 운영/보존/rollback | 실제 환경 증거, 비용 승인 |
| TASK-018 | P3 | listing/정책/제출 자료 | 최종 구현에서 생성, 5+3 재현 |
| TASK-019 | P3 | 소유자 제출·게시 절차 | 실제 상태/URL 기록, 승인 gate |
| TASK-020 | P4 | portable code bridge | 근거 있는 연결, 무승인 업로드 없음 |
| TASK-021 | P5 | pure shared core 추출 | 두 소비자 동일 동작·회귀/rollback |
| TASK-022 | P6 | Suite 유효성 검토 | 실제 사용 근거, 자동 통합하지 않음 |

우선순위는 TASK-001~004입니다. 사용자 승인 없이 기존 플러그인 수정이나 공개 배포부터 시작하지 않습니다.

## v2 추가 작업 (기존 22개 작업과 병행 추적)

| ID | 작업 | 완료 근거 |
| --- | --- | --- |
| V2-01 | 명시 이름/Contracts 공개 요구 반영 | D-06/D-07 및 두 repo 계획 |
| V2-02 | Context 전용 envelope와 공통 profile 분리 | 두 소비자 정상/금지 fixtures |
| V2-03 | thin slice로 계약 검증 | 결정 1개 저장/복구 실행 로그 |
| V2-04 | Contracts 검증 workflow 구현 | JSON pointer별 오류, unsupported version 시험 |
| V2-05 | 문맥 팩 필수/충돌/근거 원자성 | budget 경계 및 직렬화 시험 |
| V2-06 | 시점 질의 지원 범위 | current/valid_at/known_at 지원·거절 시험 |
| V2-07 | 단순 기준선과 비교 | 보류 평가 결과 및 비용 |
| V2-08 | 호스트/모델 실제 기능 표 | 환경별 실측 결과 |
| V2-09 | 제품별 공개 readiness | 구현 기반 descriptor/지원 정책/승인 상태 |
