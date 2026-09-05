# 02. 아키텍처

## 논리 구조

```text
ChatGPT / Codex
  ├─ Skill: 의도 확인, 최소 후보 작성, 출처 설명
  └─ 인증된 remote MCP 호출
          |
      MCP Adapter (입출력 계약·오류·호스트 호환)
          |
      Application Services
       ├─ Authorization / project boundary
       ├─ Context proposal and approval
       ├─ Knowledge ledger / supersession
       ├─ Retrieval and bounded context pack
       └─ Export / erasure lifecycle
          |
      Pure Domain Core + Versioned Contracts
          |
      Storage Ports
       ├─ Relational records / relations / revision history
       ├─ Bounded approved evidence
       ├─ Derived search index (rebuildable)
       └─ Content-free operational audit

Authenticated review page -> approve/reject -> same application services
Code portable artifact -> optional P4 bridge -> context-side references only
```

이 그림은 설계이며 실제 배포를 뜻하지 않습니다. 하나의 서비스 내부에 경계를 분리하는 **모듈형 단일 애플리케이션**으로 시작합니다. 마이크로서비스·분산 그래프·벡터 DB·작업 큐를 먼저 도입하지 않습니다.

## 제품·저장소 경계

| 구성 | 소유 책임 | 포함하지 않는 것 |
| --- | --- | --- |
| 기존 Code Plugin | 코드 구조·정적 증거·로컬 스냅샷 | 사용자 대화 DB·원격 쓰기·개인 문맥 |
| Context Plugin | 승인 문맥·검색·정정·삭제·공개 호스트 연동 | 코드 실행·원본 저장소 수집 |
| 공통 contracts | 엔티티·관계·출처·버전 교환 규격 | OAuth·LLM·DB·사용자 계정 |
| 공통 core | 검증·정규화·순수 관계/시점 함수 | 네트워크·파일 IO·배포·공유 사용자 저장소 |

## 제안 기술 기본값 — P0에서 재검토

- 서버: Python과 공식 MCP Python SDK를 우선 비교 대상으로 합니다. 기존 코드 도구와 같은 언어를 사용할 수 있지만 그 자체로 선택이 확정되는 것은 아닙니다.
- 데이터: 운영은 관계형 DB의 record/edge 테이블로 시작합니다. PostgreSQL을 후보로 두며 계정/프로젝트 격리를 서비스와 DB 양쪽에서 시험합니다.
- 개발: 메모리/SQLite 어댑터는 순수 코어 검증용으로만 사용합니다. 운영 DB의 동시성·권한 검증을 대신하지 않습니다.
- 검색: 구조화 조건 + 전문/부분 문자열 + alias + 제한된 관계 확장을 먼저 검증합니다. 한국어 검색은 별도 평가가 필요합니다. 임베딩은 지표로 효과가 확인될 때만 opt-in 추가합니다.
- 모델: 기본 서버 경로는 외부 LLM 호출을 요구하지 않습니다. 호스트가 만든 후보를 서버가 계약과 권한으로 검증합니다. 호스트의 언어 추출 품질은 별도 평가 대상입니다.
- UI: 호스트 내 커스텀 위젯은 선택 사항입니다. 사용자 승인·정정·삭제를 위한 최소 인증 웹 화면은 제공하는 안을 우선 검토합니다.
- 버전: 런타임·SDK 지원 버전은 구현 시 공식 문서와 lockfile로 확정합니다. 이 문서는 존재하지 않는 최신 버전을 가정하지 않습니다.

## 인증과 격리

공개 서버는 사용자별 인증을 요구합니다. 인증 주체, 프로젝트 소유자, 저장 공간은 토큰·서버 상태에서 결정합니다. LLM이 보낸 `user_id`, `tenant_id`, `approved=true`는 권한 근거로 쓰지 않습니다.

조회 ID가 정당한 형식이어도 소유권을 매번 확인합니다. 검색 후보, 그래프 이웃, 변경 이력, 내보내기, 캐시, 페이지 cursor에도 같은 경계를 적용합니다. 사용자에게는 임의 내부 DB 키 대신 승인된 불투명 resource ID만 반환합니다.

OAuth 연결 동의와 개별 지식 payload 저장 동의는 다릅니다. 상세는 [승인 설계](05_MCP_AND_APPROVAL.md)를 참조합니다. 플랫폼 인증 규격은 [S-03](13_SOURCES_AND_VERIFICATION.md)을 구현 직전에 재확인합니다.

## 데이터 일관성

지식 기록, revision 변경, 관계, idempotency 결과는 한 트랜잭션에서 처리합니다. 검색 인덱스가 비동기라면 outbox와 tombstone을 사용하고, 지연·삭제 직후에도 조회 시 authoritative store의 상태/권한으로 다시 필터링합니다.

승인 화면이 보여준 payload digest, 대상 revision, 유효 시점, 프로젝트를 승인 거래에 묶습니다. 표시 후 수정된 payload나 만료된 승인은 거절합니다. 동시 대체는 낙관적 잠금으로 한 작업만 성공시킵니다.

## 배포 프로필

| 프로필 | 목적 | 공개 지원 상태 |
| --- | --- | --- |
| local-core | 계약·순수 코어의 로컬 검사 | 개발용 |
| local-mcp | Codex 로컬 연결 및 개발 시험 | P2 선택, 별도 명시 |
| remote-private | 인증된 실제 호스트 연동 | P3 시험 환경 |
| remote-public | 소유자가 운영하는 HTTPS MCP | 심사와 게시 후에만 공개 제품 |

로컬 `.mcp.json`을 배포했다고 ChatGPT 웹에서 동작하는 공개 플러그인이 되는 것은 아닙니다. 현재 공식 도움말은 일부 MCP 선언형 imported plugin의 Desktop-only 경계를 설명합니다. 실제 표면별 지원을 검증하고 문서화해야 합니다. [S-01](13_SOURCES_AND_VERIFICATION.md)

## 실패 처리

저장 실패에 성공을 반환하지 않습니다. 부분 성공을 허용하지 않는 작은 배치를 기본으로 하고, timeout 재시도는 같은 키로 상태를 확인합니다. 검색 무결과와 접근 거절은 정보 유출을 막는 형태로 구분·표현합니다. 인덱스 장애 시 제한된 정형 조회로 fallback하거나 명확한 오류를 반환합니다.

## v2 refinement

공통 계약은 Code와 Context의 형제 관계를 위한 교환 약속입니다. Contracts public plugin은 독립적인 검증 도구이며, 사용자 문맥 DB/권한을 보유하는 상위 서비스가 아닙니다. 기존 모듈형 단일 서비스와 추가 LLM API 없는 기본 경로를 유지합니다. `17_CONTEXT_COMPILER.md`는 retrieval 뒤 예산·필수 제약·충돌 원자성의 구체적인 계약입니다.
