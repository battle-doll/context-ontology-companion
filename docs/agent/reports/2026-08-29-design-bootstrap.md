# AI 작업 관측성 보고서 — 설계 패키지 초기 작성

## 요청과 결과

- 날짜: 2026-08-29, Asia/Seoul.
- 요청: 별도 Context 플러그인과 공통 계약·코어 방향으로 설계·개발 저장소를 준비하고 Codex에 인계한다.
- 실제 수행: 기존 저장소와 공식 문서 조회, 설계 문서·계약 초안·합성 예제·안전한 저장소 생성 스크립트·패키지 검증기 작성.
- 결과: 설계 패키지 작성 완료, 원격 생성·업로드는 blocked.
- 원격 상태: 이 대화의 GitHub connector에 생성/수정/푸시 도구가 없다. 추가 쓰기 플러그인 검색 결과도 없었다. 기존 저장소를 변경하지 않았다.
- baseline: `battle-doll/code-ontology-companion` / `356808216896a2024eee5329e026836b9f8e14bf` / 문서 버전 0.5.2.
- 원격 commit / branch / PR: not created. `docs/initial-design`은 생성 예정 브랜치다.

## 실제 역할과 실행

| 역할 | 실제 실행 | 실제 모델 식별자 | 사용 권한 / 도구 |
| --- | --- | --- | --- |
| 작성·조정 | 이 대화의 단일 assistant | 실행 API 식별자 unavailable | GitHub 읽기, 공식 웹 문서 조회, 로컬 파일 생성·검사 |
| 설계 초안 | 같은 assistant | unavailable | 설계 및 계약 초안 작성 |
| 독립 설계/보안 검토 | not run | not run | P0에서 별도로 실행 |
| 독립 subagent | not run | not run | 사용하지 않음 |
| 원격 게시/개발/심사 | not run | not run | 사용하지 않음 |

## 검증과 변경

- `python -m unittest discover -s tests -v`: 단위 시험 32건 PASS. 원격 작업은 mock이며 실제 GitHub 요청이 아니다.
- `python scripts/validate_design.py --require-schema --require-manifest`: 최종 패키지에서 PASS. JSON Schema 3개, fixture 8개(정상 4개 허용·금지 4개 거절), 로컬 문서 링크 58개를 검사했다.
- `python scripts/bootstrap_github.py --plan`: 실제 실행 PASS. 네트워크·저장소 변경 없이 계획 JSON만 반환했다. 별도 subprocess 시험으로 bytecode 파일을 포함한 로컬 파일 무변경도 확인했다.
- `python -m py_compile scripts/bootstrap_github.py scripts/validate_design.py tests/test_bootstrap.py tests/test_design.py`: 구문 검사 PASS.
- `FILE_MANIFEST.json`: 전달 파일 56개의 SHA-256/크기를 기록한다. manifest 자체를 포함한 ZIP은 57개 파일이다. 무결성 비교용이며 게시자 전자서명이 아니다.
- 수정 반복: 계약 초안 external `$ref`의 fragment 표현을 첫 시험 전에 보정했다. 기본 계획 실행의 무쓰기 경계를 위해 bytecode 캐시 생성을 차단하고 회귀 시험을 추가했다. 최종 시험 실패·skip은 없다.
- 검증 환경: Python 3.13.5, 이미 설치된 jsonschema/referencing. 이 작업을 위해 패키지 설치나 유료 인프라 생성은 하지 않았다.
- 계약 JSON Schema는 입력 구조만 검사한다. OAuth·권한·실제 동의·DB 삭제·MCP 호환성을 검증하지 않는다.
- 제품 시나리오 37건과 제출 검토 예제 5+3건은 명세이며 실행되지 않았다.
- 비용·토큰·모델 내부 실행 시간: unavailable. 수치를 추정해 실측처럼 기입하지 않는다.

## 잔여 위험과 다음 작업

- `scripts/bootstrap_github.py`의 실제 원격 실행은 인증된 Codex 환경에서 필요하다.
- `START_HERE.md`를 따라 저장소와 draft PR을 생성하고 실제 URL/SHA를 확인한 다음 CURRENT_STATE를 갱신한다.
- P0에서 독립 설계 검토, 플랫폼 최신 요건 확인, 호스팅·비용·보존 기간 등 미결정을 검토한다.
- 제품 구현, 배포, 제출, 승인, 공개 게시를 각각 구분한다. 이 보고서는 그 어느 단계도 완료했다고 주장하지 않는다.
