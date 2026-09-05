# 다음 작업

1. 이 상태와 release-state.json, 테스트 증거, 최신 독립 리뷰를 읽고 source/digest/branch/remote를 다시 확인한다.
2. 최종 공개 플러그인 소스는 public 저장소를 목표로 한다. 로컬 공개 전 검증과 소유자 생성·업로드 승인 후 battle-doll/ontology-companion-contracts 및 battle-doll/context-ontology-companion을 생성하고 명시한 검토 파일만 push한다. Private staging은 필수 단계가 아니다. 현재 인증 계정, 동명 저장소, visibility, remote, branch, credential 접근을 직전에 재조회한다. 기존 bootstrap --apply는 실행하지 않는다.
3. 실제 GitHub Actions macOS/Windows/Linux matrix를 실행하고 Windows ACL·경로/권한 보완을 완료한다. CI YAML 존재는 시험 통과 증거가 아니다.
4. P1b stable contract는 draft 소비자 회귀·버전/손실 검토 후 별도 결정한다. Code mapping fixture를 실제 Code 제품 사용 증거로 승격하지 않는다.
5. P2/P3 remote profile은 검증된 OAuth provider 선택, 승인 UX, principal 격리, 삭제/보존 운영을 구현한다. OAuth client/도메인/유료 hosting/실데이터는 별도 승인 경계를 따른다. 로컬 profile은 실제 데이터용으로 공개하지 않는다.
6. 실제 ChatGPT 연결·호출·권한·삭제·실패 E2E 및 5/3 사례를 실행한 뒤 live descriptor와 submission JSON을 다시 대조한다. 검증된 publisher identity·공개 지원/정책 URL·브랜드 자료를 준비한다.
7. security/privacy/license/secret scan/test gate와 소유자 공개 승인 후에만 public 전환/최종 제출. submitted, approved, published 각각 실제 증거를 남긴다.
8. 동일 정보·예산의 raw/current, summary+source, Markdown/JSON, relation expansion 비교를 수행한다. 작업 재개 성공·필수 제약·provenance·stale·오판·latency/token cost는 아직 model benchmark not_run. 이득 없이 graph/core 추출을 추가하지 않는다.
