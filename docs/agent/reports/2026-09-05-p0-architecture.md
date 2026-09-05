# P0 독립 아키텍처 검토 — 2026-09-05

## 판정과 근거 범위

**새 draft envelope + 분리된 profile + 로컬 소비자 한 경로로 P1a를 진행할 수 있다.** 기존 Context 전용 draft를 범용 계약으로 재정의하지 않는다. 안정 버전, 공개 서비스 보안, 호스트 연동, 그래프의 효과는 아직 승인하거나 입증하지 않는다.

이번 검토는 명시적으로 지정된 별도 Architect 에이전트 `/root/architect_p0`가 수행했다. 오케스트레이터와 다른 에이전트의 검토이며, 다른 모델 간 비교 평가가 아니다. 관측 가능한 정확한 실행 모델 ID·비용·토큰 수는 unavailable이다. 사용 도구는 로컬 파일 읽기, `rg`, `apply_patch`이며 외부 서비스 변경과 기존 Code 저장소 변경은 수행하지 않았다.

검토한 현재 자료: `START_HERE.md`, 현재 Context/Contracts AGENTS, Context `02_ARCHITECTURE`, `03_CONTRACTS_AND_DATA_MODEL`, `05_MCP_AND_APPROVAL`, `06_PRIVACY_SECURITY`, `07_RELEASE_ROADMAP`, `10_CODEX_HANDOFF`, `16_REEVALUATION`, `17_CONTEXT_COMPILER`, 현재 상태/다음 작업/계획, Contracts `ARCHITECTURE`, `CONFORMANCE`, `PLATFORM_MATRIX`, 예산 참조 실험의 구현. 현재 사용자 첨부 요청의 독립 설치·공개 품질·gate와 추가 macOS/Windows/Linux 요구도 반영했다. 삭제되거나 보관된 AETHER 에이전트 설정은 사용하지 않았다.

이 보고서는 로컬 아키텍처 검토다. 공식 플랫폼 문서와 현재 Code upstream 리비전 확인은 오케스트레이터가 별도 취합해야 하며, 이 보고서가 그 확인을 대신하지 않는다. `git status --short --branch`는 Context 폴더에서 `not a git repository`로 종료했다. 이 결과로 원격의 존재 여부를 판단하지 않는다. 보고서 외의 파일은 이 검토에서 수정하지 않았다.

## 먼저 수정할 설계 결정

| 항목 | P0 결정 | P1a에서 필요한 증거 |
| --- | --- | --- |
| 공통 계약 | 기존 draft-0.1 보존. 새 초안 envelope와 code/context profile 분리 | 각 profile의 정상 fixture와 서로의 필수 필드를 강요하지 않는 시험 |
| 계약 소비 | Context가 만든 실제 export를 같은 버전의 Contracts validator가 검사 | 소비자 integration 시험; 수작업 fixture만으로 완료하지 않음 |
| Code 호환 | 현재 Code artifact의 읽기 전용 mapping을 명시 | 원본 ID·`co:` 관계·static/runtime-unknown 의미 보존, 손실 목록 |
| 승인 | 모델 입력은 저장 후보만 생성. 신뢰된 별도 승인 adapter만 활성화 | 위조 승인·payload 변경·만료·다른 프로젝트·재사용 거절 |
| 시간 | UTC 적용 시점만 명시적으로 지원. known-at는 미구현이면 거절 | `known_at` 입력이 현재 결과로 조용히 대체되지 않음 |
| 저장소 | 단일 로컬 트랜잭션 저장소부터 시작 | reopen 후 정확한 기록과 근거, 중복 요청·revision 충돌 시험 |
| 검색 | 구조/키워드 기준선을 우선 구현 | 제약 별도 조회와 그래프 없는 재개 시나리오 |
| OS | macOS·Windows·Linux를 목표 지원 OS로 명시 | OS별 CI와 실제 수행 여부를 구분한 지원표 |

## 최소 공통 계약

공통 envelope는 교환 형식과 생산자를 설명하는 메타데이터로 좁힌다. 초안에서 다음 의미를 분리한다.

- `schema_version`: envelope 문법 버전.
- `profile`와 `profile_version`: payload의 의미와 지원 버전.
- `artifact_id`, `producer`: 교환물과 생산 도구 식별. 사실 인증이나 사용자 권한이 아님.
- `payload`: profile별 스키마. Context 레코드를 공통 엔티티 타입으로 강요하지 않음.
- 선택적 무결성 metadata: 알고리즘과 계산 대상·직렬화 규칙을 명시. digest 일치는 작성자의 신원이나 내용의 진실성을 증명하지 않음.

모든 profile에 Context의 `project_id`, `review`, `ctx_` ID, 유효기간을 필수로 요구하지 않는다. Code는 원본 node ID·관계 URI·저장소 리비전·정적 출처를 보존한다. Context는 결정/요구사항/제약, 출처·승인 상태·적용 기간을 별도 규칙으로 갖는다. Code 정적 관측과 Context 사용자 진술을 같은 provenance enum으로 억지 변환하지 않는다.

출처 reference의 공유 모양은 두 소비자에서 같은 의미를 확인한 부분만 공유한다. 출처 접근 가능 여부, 외부 사실 확인, 실행 증거를 개별 필드/결과로 남긴다. Context import의 `review=user_approved`는 원본 생산자의 **선언된 데이터**다. 현재 저장소의 활성 기록을 만드는 승인 권한이 아니다.

검증기는 parse/schema/profile semantics/reference/compatibility 결과를 각각 반환한다. 수행하지 않은 권한·외부 사실·runtime 확인은 `not_checked`다. 지원하지 않는 버전은 `unsupported`; 알려지지 않은 필드를 조용히 버리거나 자동으로 낮은 버전으로 해석하지 않는다. 부분 export의 외부 reference는 명시 상태가 있을 때만 허용한다.

입력은 byte/depth/배열 크기가 제한된 JSON으로 시작한다. 중복 key, NaN/Infinity, 미등록 profile, remote `$ref`를 거절하고 고정된 로컬 schema registry만 사용한다. 오류는 JSON Pointer와 rule ID를 반환하며 실제 본문을 되풀이하지 않는다. stable ID에 Unicode 정규화·대소문자 변경·플랫폼 경로 정규화를 몰래 적용하지 않는다. digest를 추가하면 canonicalization 규칙과 버전을 고정하고 숫자·Unicode 경계 시험을 붙인다.

## 호스트와 분리된 승인 경로

`approved=true`, `--approved`, 모델에게 전달된 서명 키, proposal URL 자체, 과거 승인된 context는 현재 사용자 승인 근거가 될 수 없다. 이 점은 모델이 shell 또는 브라우저 도구를 사용할 수 있다는 상황에도 적용된다.

실제 로컬 승인 spike를 구현한다면 다음 경계를 함께 구현한다.

1. 모델/CLI/MCP의 prepare adapter는 bounded pending proposal을 만들고 opaque proposal ID만 반환한다.
2. 별도 검토 adapter는 loopback에서만 수신한다. 로컬 운영자가 직접 마련한 credential로 인증한 세션만 받는다. 개발용 credential을 fixture나 모델 출력에 넣지 않는다.
3. 검토 화면은 정확한 project/action/payload/evidence/target revision/validity/삭제 범위를 escape해 표시한다. URL에는 인증 비밀을 넣지 않는다.
4. 변경은 인증된 세션의 POST, 엄격한 Host/Origin 검사, CSRF 검증, 세션 만료를 거친다. loopback 주소라는 사실만으로 인증이나 CSRF 방지가 완성되지 않는다. 원격 프로필은 TLS와 정식 계정 인증을 별도로 요구한다.
5. 승인 principal이 proposal principal/project와 일치하는지 확인한다. 현재 권한도 재확인한다.
6. 고정 payload digest·action·project·target revision·nonce·expiry를 검증한 뒤, nonce 소비/record 쓰기/idempotency 결과를 한 트랜잭션에서 처리한다.
7. 모델에 노출되는 표면은 prepare와 status다. approval/apply를 일반 MCP 도구로 추가하지 않는다. tool hint 자체도 접근 제어를 대신하지 않는다.

로컬 OS 관리자 또는 동일 OS 사용자로 임의 파일/프로세스를 조작하는 공격자까지 이 경계로 막았다고 주장하지 않는다. 원격 OAuth 계정 인증, 실제 호스트가 보여준 사용자 승인, 다중 사용자 서비스 보안도 로컬 spike와 별도 증거가 필요하다.

위 인증 UI까지 이번 slice에서 구현하지 않는 경우에는 **test-only 승인 authority를 주입한 합성 경로**로 소비자 계약을 검증할 수 있다. 모의 경로에는 네트워크 인증 완료나 실제 인간 승인 검증이라는 명칭을 사용하지 않고, 실제 auth/host E2E는 `not_run`으로 유지한다. 인증 UI 구현의 부재가 순수 계약·소비자 시험을 막을 이유는 없다.

## 최소 소비자 단면

P1a 구현 범위를 다음 하나의 작업으로 제한한다.

```text
합성 결정 + 합성 source
→ project 범위가 정해진 pending proposal
→ 신뢰된 승인 adapter 또는 명시적 test-only authority
→ 하나의 transaction으로 승인 적용
→ 프로세스/세션을 다시 열어 project+ID로 조회
→ 원문 statement·revision·origin·근거·적용 시점이 보존된 Context export
→ Contracts validator가 같은 draft profile로 검사
```

Python 표준 라이브러리 기반 모듈형 구조를 우선한다. durable local slice에는 SQLite 후보가 단순 JSON 덮어쓰기보다 revision/idempotency/동시 승인 원자성을 직접 시험하기 쉽다. in-memory adapter는 단위 시험에 한정한다. 단일 JSON 파일을 택한다면 lock, crash recovery, atomic replace, 동시 쓰기 증거를 추가해야 하므로 “의존성 없음”만으로 더 단순하다고 판단하지 않는다. 운영 다중 사용자 DB 보장은 어느 로컬 선택으로도 자동 충족되지 않는다.

저장소별 권장 경계는 Contracts `schemas/`, `src/`, `tests/fixtures/`, `examples/`, `docs/`, 향후 구현이 있는 `skills/`; Context `src/.../domain`, `application`, `adapters`, `tests/`, `examples/`, `docs/`다. 파일 수를 먼저 늘리기보다 pure validator와 consumer의 import/API 경계를 먼저 둔다.

Context에는 필요한 계약 artifact를 버전과 digest로 pin하여 포함하거나 일반 패키지 의존으로 제공한다. 사용자가 Contracts **플러그인**을 별도로 설치해야 import가 성공하는 구조를 만들지 않는다. 개발 중 형제 폴더 `sys.path` 주입으로만 성공한 시험은 독립 설치 시험으로 인정하지 않는다. 각 배포물을 형제 디렉터리가 없는 격리된 임시 환경에 설치해 각각의 CLI/소비자 시험을 실행한다.

## Scope·시점·삭제·예산 위험

| 위험 | 필요한 구현 경계 | 실패 시 동작 |
| --- | --- | --- |
| ID를 알면 타 프로젝트 내용을 읽음 | 인증 scope를 query에 전달하고 fetch/source/relation에도 재검사 | `NOT_FOUND_OR_FORBIDDEN`, 본문·다른 scope의 ID 미노출 |
| 과거 적용 시점과 당시 알려진 사실 혼동 | `valid_at`과 `known_at`를 분리, 미지원 축 거절 | `UNSUPPORTED_TEMPORAL_QUERY` 등 명시 오류 |
| superseded 상태 때문에 유효한 과거 결정이 사라짐 | 현재 알고 있는 자료의 유효 구간과 대체 관계로 선택 | 구현 전 historical 조회는 지원하지 않는다고 표시 |
| 승인 화면 이후 payload/target 변경 | digest와 expected revision을 transaction에서 재검사 | 재검토 요구, 부분 쓰기 없음 |
| 삭제한 본문이 history/proposal/export에서 재등장 | 모든 소유 payload와 파생물의 삭제 범위 추적 | 접근 차단 우선, 완료 범위/미완료 범위 구분 |
| 그래프에서 삭제/권한 경계를 넘어감 | 각 이웃과 evidence를 같은 scope/time/deletion 필터로 검사 | 확장 중단 또는 명시적 누락 |
| Top-K 때문에 필수 제약이 빠짐 | 현재 적용 제약을 별도의 authoritative 조회로 구성 | 필수 집합을 모르면 완전한 팩으로 반환하지 않음 |
| 작은 예산에서 충돌의 한쪽만 나감 | conflict 연결 성분을 정규화해 원자 그룹으로 처리 | 그룹 전체 포함 또는 전체 누락/미해결 |
| 근거 없이 주장만 남음 | claim+evidence+provenance를 같은 예산 그룹으로 구성 | 불완전한 claim을 성공 팩으로 반환하지 않음 |
| metadata를 더해 최종 예산 초과 | 최종 JSON 전체를 UTF-8 bytes로 측정 | 필수 그룹 미수용 시 bounded 실패 코드 |

P1a에서 구현하지 않은 supersede/retract/erase/history/graph 연산은 인터페이스에서 노출하지 않거나 명시적으로 unsupported를 반환한다. stub 성공 응답을 만들지 않는다. 삭제를 구현했다면 현재 row의 status만 바꾸는 시험으로 완료하지 않는다. revision 본문, pending proposal, export staging, relation label, cache/index가 실제로 제거되고 재시작 후도 조회되지 않는지 검사한다. 외부 다운로드 사본이나 OS 백업까지 지웠다고 약속하지 않는다.

참조 예산 실험은 이미 필터링된 합성 그룹만 받는다. 그 함수를 재사용하더라도 권한·시점·출처·충돌 탐지를 구현한 것은 아니다. product 경로는 그 선행 조건을 실제 store query와 authoritative 확인으로 보장해야 한다.

## P1a 수용 시험

| ID | 시험 | 통과 기준 |
| --- | --- | --- |
| ARCH-P1A-01 | Context export → validator | 소비자가 생성한 artifact가 지원 draft로 통과 |
| ARCH-P1A-02 | Code mapping | 원본 ID·관계·정적 근거 의미 보존; Context review 필수 없음 |
| ARCH-P1A-03 | unknown version/profile, wrong profile payload | 명시 unsupported/invalid; 조용한 필드 삭제 없음 |
| ARCH-P1A-04 | 중복 key, duplicate ID, dangling source, 역전 시간, remote ref | bounded 오류; 네트워크 호출 없음; 본문 echo 없음 |
| ARCH-P1A-05 | 모조 `approved=true`와 import review 선언 | durable active record 생성 없음 |
| ARCH-P1A-06 | proposal 후 payload/revision 변경, 만료, 다른 project/principal | 승인 실패, 부분 쓰기 없음 |
| ARCH-P1A-07 | 동일 key+동일 payload / 동일 key+다른 payload | 같은 결과 / conflict; 중복 row 없음 |
| ARCH-P1A-08 | 새 store 연결 또는 새 process에서 조회 | 동일 결정·근거·origin·revision 복원 |
| ARCH-P1A-09 | fetch/search/source/관계의 scope 경계 | 같은 ID를 알아도 다른 범위의 내용 없음 |
| ARCH-P1A-10 | `known_at` 입력 | 미구현이면 거절; 입력을 무시하지 않음 |
| ARCH-P1A-11 | 필수 그룹, 충돌 그룹, 한글·emoji와 경계 byte 예산 | 필수/근거/양측 원자성, JSON 전체 한도 준수 |
| ARCH-P1A-12 | 삭제 후 재시작·history·proposal·새 export 조회 | 구현한 삭제 범위의 본문 부활 없음; 미구현이면 unsupported |
| ARCH-P1A-13 | 독립 배포물 설치 | 형제 제품/플러그인 없이 각 workflow 실행 |
| ARCH-P1A-14 | OS matrix | macOS/Windows/Linux 실제 CI 결과를 구분; 미실행은 not_run |

실제 로컬 승인 adapter를 구현하면 로그인 실패, 만료 세션, 잘못된 Origin/Host, CSRF 누락, 다른 사용자 proposal, GET 부작용, nonce replay를 추가한다. 모의 승인 adapter의 통과를 이 시험의 대체 증거로 쓰지 않는다.

## 그래프 도입 gate와 OS·문서

P1a에서는 그래프 DB, 벡터 DB, 외부 LLM enrichment가 필요하지 않다. 구조화 record와 source relation만 저장하고 키워드/ID 조회를 기준선으로 삼는다. 같은 합성 corpus·질문·허용 정보·byte/token 예산에서 raw context, summary+source, Markdown/JSON, bounded relation expansion을 비교한다. task resume 성공, 필수 제약 보존, provenance 정확도, conflict 오판, stale 선택, 지연, 실제 tokenizer를 썼을 때만 token cost, 구현 복잡성을 각각 측정한다. 현재 그 비교는 `not_run`이다.

macOS·Windows·Linux 지원은 경로/설치와 인증 adapter에도 적용한다. `pathlib`, UTF-8, platform별 user-data 경로, `python -m` 진입점, shell-free subprocess 인자를 사용하고 POSIX 권한값만으로 Windows의 파일 보호를 입증하지 않는다. loopback 서버와 Python webbrowser 같은 portable adapter를 우선하며 특정 macOS keychain이나 Unix socket을 공통 필수조건으로 두지 않는다. 운영 secret store의 OS별 구현은 별도 검증한다.

GitHub 문서는 영어 canonical README와 한국어/일본어/중국어 등 **현재 Code 저장소에서 실제 확인한 언어 집합**에 대응한 번역 링크 구조를 권장한다. 확인 전 언어 집합을 Code의 현행 구조라고 단정하지 않는다. 각 언어에서 설치 독립성, OS matrix의 tested/planned 구분, 보안·개인정보·지원하지 않는 행동, 버전/이관 정책이 같은 의미를 유지해야 한다. 실제 문서와 명령이 준비되지 않은 locale 링크는 만들지 않는다.

## 검증 상태와 다음 단계

이 보고서의 결과는 `design-reviewed`의 아키텍처 하위 항목이다. 파일·현재 설계·참조 실험의 정적 검토를 수행했고 제품 실행 시험은 수행하지 않았다. 보고서 작성 때문에 package manifest를 자동 재생성하거나 기존 실패를 덮지 않았다.

오케스트레이터는 공식 플랫폼/기존 Code 증거와 별도 security review를 합쳐 P0를 판정한다. gate가 통과하면 위 범위로 P1a를 구현하고 실제 consumer/validator/independent-install 시험 결과를 기록한다. P1b 안정 버전, remote auth, ChatGPT/Codex host E2E, 공개 저장소 전환, 제출은 각각 별도 미완료 상태로 유지한다.
