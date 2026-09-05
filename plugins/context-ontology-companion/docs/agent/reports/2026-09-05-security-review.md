# 독립 보안·품질 검토 — 2026-09-05

## 요청과 결과

- 기록 시각: 2026-09-05 13:47 UTC / 22:47 KST 이후의 검증 결과.
- 요청: 실제 Context 저장소·MCP·도구 코드와 Contracts 검증기의 권한, 삭제, 읽기 전용 효과, 입력 타입, 계약 일치, 자원 제한, 동시 조회를 독립 검토.
- 실제 범위: 합성 데이터만 사용하는 임시 DB와 로컬 런타임. 실제 사용자 자료·운영 DB·원격 서비스는 열지 않았다.
- 결과: **지정한 코어 범위의 반례 검토와 수정 후 재검증을 수행했다. 전체 보안 감사, Windows/Linux 실행, 실제 ChatGPT/Codex 호스트 E2E 또는 공개 출시 승인은 아니다.**
- 작업 트리: `feat/p0-p1a`, 아직 HEAD commit 없음. 변경 중인 로컬 소스를 검사했으며 실행 전후 SHA-256을 별도 증거에 보존했다.
- 증거: [실행 결과와 소스 해시](2026-09-05-security-review-results.json).

## 역할과 실행

| 역할 | 실제 agent | 관측 가능한 모델 | 사용 범위 |
| --- | --- | --- | --- |
| Orchestrator / Context 코어 수정 | `/root` | unavailable | 검토 결과 수신, 구현 수정 및 회귀 시험 |
| Architect / 로컬 승인 어댑터 | `/root/architect_p0` | unavailable | 별도 설계·승인 어댑터 작업; 이 검토의 작성자가 아님 |
| Contracts 구현 | `/root/contracts_impl` | unavailable | 별도 검증기 구현 |
| 독립 Reviewer | `/root/multilingual_oss_docs` | unavailable | 런타임 소스 읽기, 합성 반례 실행, 이 보고서 작성 |

Reviewer는 앞서 공개 문서를 작성했으며 검토 대상 런타임 코드는 작성·수정하지 않았다. 독립성은 별도 에이전트와 구현 역할 분리를 뜻하며 서로 다른 모델 계열을 사용했다는 뜻은 아니다. 사용 도구는 로컬 shell/Python, 파일 읽기, 팀 메시지, 보고서 작성이다. 비용·토큰·총 경과 시간은 unavailable. 비공개 추론 전문은 기록하지 않는다.

## 확인하여 수정된 문제

| ID | 최초 실행 결과 | 영향 | 수정 후 독립 재검증 |
| --- | --- | --- | --- |
| R-01 | `pack`의 두 `search`가 서로 다른 시각을 사용하여 유효 시작 시점을 통과한 레코드가 `matched`에만 포함되고 `KeyError` 발생 | 해당 오류는 당시 MCP 예외 경계에서 잡히지 않아 stdio 처리가 중단될 수 있음 | 한 검색 결과·한 effective-time을 사용하도록 수정. 시계가 연속 두 시각을 반환해도 실제 읽기는 1회이며 미래 레코드는 제외됨 |
| R-02 | `Research Project`를 프로젝트 ID로 저장한 뒤 export가 성공했지만 실제 Contracts 검증에서 scope pattern 오류 | 소비자가 자신이 받아들인 프로젝트를 유효한 교환물로 내보내지 못함 | 프로젝트 ID의 공백·제어 문자 등을 생성 전 거절. `INVALID_PROJECT_ID` 확인 |
| R-03 | 126개 레코드 × 근거 8개 = 1,008개 근거, 또는 130개 × 4,000자 본문 = 571,589 UTF-8 bytes의 export를 반환 | 허용된 개별 레코드가 집계될 때 실제 계약의 collection/byte 한도를 초과 | 전체 export를 검증한 뒤 부적합 시 `EXPORT_CONTRACT_LIMIT_OR_MISMATCH`로 중단. 두 반례 모두 부분 교환물을 반환하지 않음 |
| R-04 | Context JSON parser가 `1e999`를 무한대 float로 해석 | 당시 도구 입력 타입에서는 거절됐으며 저장·권한 우회는 재현되지 않았으나 비정상 숫자 차단 정책이 불완전 | 유한 숫자 검사 수정 후 overflow·NaN·중복 키·과도한 깊이·잘못된 UTF-8의 5개 반례 모두 parser에서 거절 |

R-01의 최소 조건은 `valid_from=2026-09-05T00:00:01Z`인 합성 decision을 저장하고, pack 동안 시계가 `00:00:00Z`와 `00:00:01Z`를 순서대로 반환하게 하는 것이다. 최초 코드에서 `KeyError`를 직접 관측했다. 단순 예외 처리 추가가 아니라 같은 조회 자료와 시각을 쓰는 수정으로 재검증했다.

R-03은 자료를 자르거나 오래된 항목을 조용히 버려 해결하지 않았다. 사용자에게 필요한 완전한 교환물을 만들 수 없을 때 명시적으로 실패하는 동작을 확인했다.

## 실제 실행한 검증

환경은 번들 Python **3.12.14**, macOS이다. 운영 파일 대신 `tempfile.TemporaryDirectory`로 만든 합성 DB를 사용하고 종료 시 정리했다.

| 검증 | 실제 결과 |
| --- | --- |
| 다른 principal의 fetch/history/proposal-status, 권한 주장 인자 및 `known_at` 입력 | 6개 거절 확인, 타 사용자 본문 반환 없음; 다른 principal의 export/pack은 비어 있음 |
| 선언된 읽기 전용 도구 7개, 만료된 proposal이 있는 상태 | DB SHA-256·SQLite `total_changes`·proposal 행이 실행 전후 동일 |
| Context 도구의 잘못된 타입 변형 | **106건**, 제어된 오류, 처리되지 않은 예외 없음 |
| 삭제 후 관련 pending proposal·history·export·pack·재시작 | 삭제 레코드 반환 없음, 관련 승인의 재실행 거절, 관련 payload와 nonce 제거 확인 |
| 유효 시각 경계와 프로젝트 ID 회귀 | 위 R-01/R-02 수정 확인 |
| 동시 writer와 pack | 조회 트랜잭션의 이전 snapshot이 일관되게 반환되고 이후 search는 writer commit을 관측 |
| export 집계 근거 수·byte 한도 회귀 | 두 반례 모두 `EXPORT_CONTRACT_LIMIT_OR_MISMATCH`, 부분 artifact 없음 |
| 두 Contracts profile의 JSON 필드·배열·객체 타입 변형 | **600건**, 593건 invalid/unsupported, 처리되지 않은 예외 없음, 오류 최대 32개 유지, external verification은 `not_checked` |
| Context transport 비정상 입력 | 5건 모두 거절 |
| 기존 Context `test_store.py` | **16 tests passed** |
| 기존 Contracts `test_contracts.py` | **41 tests 중 40 passed, 1 skipped** |

일부 Contracts 변형 7건이 valid인 것은 nullable 또는 선택적/비어 있을 수 있는 자료에 허용 값을 넣었기 때문이다. 모든 변형이 invalid여야 한다고 가정하지 않았다. 이 변형 시험은 예외·출력 경계 검사이며 임의 자료의 의미적 정확성을 증명하지 않는다.

실행 명령은 다음과 같다. `PYTHON`은 실제 번들 Python 3.12.14 실행 파일을 뜻하며 가상의 결과가 아니다.

```text
PYTHON <temporary-review-directory>/ontology-security-probes.py

# Context 저장소에서
PYTHON -m unittest discover -s tests_product -p test_store.py -v

# Contracts 저장소에서
PYTHON -m unittest discover -s tests -p test_contracts.py -v
```

독립 반례 harness는 `<temporary-review-directory>/ontology-security-probes.py`이며 runtime이나 정식 시험 코드는 수정하지 않았다. 핵심 반례는 이 보고서에 기록했고, 최종 결과·해시는 같은 폴더의 JSON에 보존했다. 최종 harness 실행 전후의 다섯 runtime source 해시는 동일했다.

검증 중 한 harness 기대값은 일반 `INVALID_INPUT`을 요구했으나 실제 수정은 더 구체적인 `INVALID_PROJECT_ID`를 반환했다. 이는 제품 오류가 아니므로 정확한 제어 오류로 기대값을 수정했다. overflow 숫자는 실제 발견 사항으로 보고한 뒤 수정본에서 다시 검사했다. 같은 실패를 통과로 재명명하지 않았다.

## 남은 한계와 다음 확인

- **승인 만료와 자료 삭제 시각은 다르다.** 만료 직후 모델용 status는 `expired`, review는 거절되지만 DB payload는 maintenance 전까지 남는다. 이후 확인한 `review.py`는 운영자가 실행한 reviewer 서비스에서 30초 간격 `purge_expired`를 호출한다. 서비스가 멈춘 상태에서는 그 주기가 보장되지 않는다. 읽기 전용 도구에 숨은 정리 쓰기를 추가하지 않고, 보존 정책에 실제 maintenance 조건을 명시해야 한다.
- 삭제 검사는 요청한 레코드와 연결된 proposal/history/relations에 한정했다. 독립적으로 만들어진 동일 내용의 다른 proposal까지 자동 삭제하는 동작은 요구하거나 주장하지 않았다. OS 백업·호스트 대화 기록·기존 export·안전 삭제를 입증하지 않았다.
- `Store`는 adapter가 제공하는 principal을 신뢰한다. 동일 OS 사용자/관리자 또는 DB 파일에 직접 접근할 수 있는 프로세스로부터의 격리는 이 코어가 제공하는 보장이 아니다.
- 생성 후의 `review.py`도 별도로 읽었다. Host/Origin·CSRF·세션·escape·권한 제한과 maintenance 코드를 확인했지만 **이 Reviewer는 HTTP 승인 흐름을 독립 실행하지 않았다.** 해당 어댑터의 시험 결과는 별도 담당자의 보고서로 판단한다. Windows ACL 보호는 그 코드에서도 미확인으로 명시되어 있다.
- Contracts의 독립 `jsonschema` 비교 시험은 선택적 개발 의존성이 없어 1건 skip되었다. 이 검토에서 그 비교를 통과로 계산하지 않았다.
- Windows/Linux 실행, 실제 ChatGPT/Codex 호스트, 공개 MCP, 외부 스키마/서비스, 실사용자 승인, 운영 부하·장기 저장 한도·백업/삭제 복구 공격·전체 위협 모델은 이 실행 범위 밖이다.

이 범위에서 최초 발견한 런타임 반례는 수정 후 재검증했다. 제품의 공개·호스트·실데이터 사용 판정은 남은 시험과 별도 출시 근거에 따라 유지한다.
