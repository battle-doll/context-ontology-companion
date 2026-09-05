# 로컬 검증 기준점과 현재 출시 상태

아래 구현·시험 기록은 **2026-09-05 로컬 검증 시점의 과거 스냅샷**이다. 현재 GitHub 원격·commit·공개 배포·플랫폼 CI·제출 상태는 [release-state.json](../../release-state.json)에서 확인한다. 과거의 미실행·미공개 기록을 현재 상태로 해석하지 않는다.

현재 최초 배포 경로는 **skills-only ZIP**이다. 실행 가능한 Skill과 필요한 Python 코드·계약·예제를 함께 배포하며, 호스팅된 MCP 서버나 운영 사용자 인증의 배포를 뜻하지 않는다. 사용자 공개 승인을 받은 이후의 실제 게시·설치·심사 결과는 출시 상태 파일에 증거와 함께 별도로 기록한다.

현재 프로젝트 적용 시험에서 source-backed simulation 160개 점검과 도구 응답 46개 스키마 검증을 통과했다. macOS Codex 0.153.3 app-server의 프로젝트 전용 stdio 연결에서 Context 7개 읽기 도구와 Contracts 3개 도구를 발견하고 실제 호출했다. 모델 turn은 0개이고 승인 표본은 simulated_not_human_evidence이다. 실제 hosted ChatGPT/packaged plugin 설치와 사람 운영 승인은 이 결과에 포함되지 않는다.

이 호스트 시험에서 발견한 tools/list metadata·빈/null cursor 호환성 오류를 수정하고 3개 회귀시험을 추가했다. 루트 PROJECT_TRIAL.md 및 verification/codex-trial-host-fixed.json에 재현·설정 근거가 있다.

2026-09-05 스냅샷에서 P0 검토 및 P1a 로컬 합성 소비자 경로를 구현했다. 그 시점에는 안정 계약/P1b 릴리스, 실제 사용자 운영, hosted E2E, 공개 GitHub 및 Directory 제출을 완료하지 않았다.

- Context: SQLite 트랜잭션, 신뢰한 adapter 주체, proposal과 승인 분리, 현재 시점 검색/복구, 정정·명시적 충돌·철회·삭제, 원자적 문맥 팩, bounded export, stdio 8도구, 사람이 로그인하는 loopback 검토 prototype.
- Contracts: draft 0.1.0-draft.1, offline 두 profile 검증·정확한 버전 쌍·identity migration plan, CLI/stdio 3도구와 Skill. 실제 Code 저장소는 변경하지 않았고 Code consumer는 합성 mapping fixture 범위이다.
- 독립 설치: Context는 필요한 validator/schema를 digest로 vendor한다. 다른 plugin 설치나 형제 디렉터리 import가 필요하지 않다.
- 공개 문서: 영어·한국어·일본어·중국어 간체·러시아어 README 및 문서, macOS/Windows/Linux 가이드, 정책·기여·이슈·버전·롤백, 3 OS × 3 Python CI.
- 과거 MCP 제출 초안 JSON: Context 8도구, Contracts 3도구, 각각 positive 5 / negative 3의 로컬 구현 기준 자료이다. 당시 공개 MCP/hosted ChatGPT 실행 근거가 없어 해당 MCP 경로는 submission-ready=false였다. 최초 skills-only ZIP 제출의 현재 메타데이터나 준비 상태로 사용하지 않는다.

2026-09-05 실행 증거는 [로컬 시험 로그](reports/2026-09-05-product-tests.txt), [P0 종합](reports/2026-09-05-P0_REVIEW.md), [독립 보안 검토](reports/2026-09-05-security-review.md)를 확인한다. 당시 macOS Python 3.12.14 시험만 실행했고 Windows/Linux CI는 not_run이었다. Windows ACL은 그 시험에서 검증하지 않았다. 후속 결과는 [출시 상태](../../release-state.json)를 확인한다.

승인은 합성 HTTP 테스트까지 검증했다. unrestricted 같은 OS 프로세스를 막는 보안 경계가 아니며 운영 OAuth/host 로그인으로 승격하지 않는다. 15분은 승인 유효 시간이다. 만료 payload는 실행 중인 review 서버 maintenance 또는 purge-expired 명령으로 정리되며 프로세스가 꺼진 동안 디스크에 남을 수 있다.

2026-09-05 로컬 스냅샷 당시에는 GitHub 원격 생성·push가 없었고 각 제품의 로컬 feat/p0-p1a 저장소에 remote/commit이 없었다. 기존 Code 공개 main을 읽은 기준 commit은 be1699f784e48433a692bbfaa1c6c1d6f2b489b0이었다. 그 단계에서 새 계정·키·OAuth·도메인·호스팅·외부 전송은 없었다. 이 문단은 이후 공개 배포의 현재 상태를 설명하지 않는다.
