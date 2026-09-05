# P0 — 설계 보완 및 검토 실행 계획

상태: NOT STARTED / 선행: 원격 등록은 선택적 실행 환경 전제, 로컬 검토는 가능.

## 목표

승인된 제품 방향을 유지하면서 실제 구현 가능한 최소 안전 아키텍처와 계약을 확정합니다.

## 작업

- [ ] 저장소/Git/권한/기존 코드 baseline 확인
- [ ] 현재 OpenAI 공개 plugin/MCP/인증/제출 경로 재검증
- [ ] 제품 범위와 FR/NFR→테스트 매핑 확인
- [ ] source/origin/review/verification 의미 검토
- [ ] 승인 payload 바인딩과 실제 사용자 확인 경로 검증
- [ ] 시점·대체·충돌·삭제·backup restore 위협 검토
- [ ] Python/TypeScript·DB·검색·UI 기본값 비교 후 ADR 기록
- [ ] 계약 schema/fixture와 미구현 불변 조건 구분
- [ ] 별도 Architect/Reviewer의 실제 수행 여부 기록
- [ ] DESIGN_REVIEW 보고서와 P1 계획 작성

## 완료 기준

중요 모순을 해결하거나 owner gate로 분류하고, 구현이 가능한 계약 경계와 테스트 계획을 확정합니다. 미결정 비용/도메인 때문에 불필요하게 로컬 작업 전체를 멈추지 않습니다.

완료 보고 위치: `docs/agent/reports/`에 새 날짜/작업 ID 문서를 생성합니다. 초기 생성 보고서를 덮어쓰지 않습니다.

## v2 우선 항목

재평가 F-01~F-08을 검토합니다. 이름과 공개 Contracts 목표를 다시 사용자에게 묻지 않습니다. 기존 패키지에 이미 있는 보안/삭제/역할 원칙은 유지합니다. 공통 envelope가 실제로 code/context 두 profile을 표현하는지 확인하고, 형식 확정 전 P1a 소비자 단면을 계획합니다. 원격404는 부재 판정으로 사용하지 않습니다.
