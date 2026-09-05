# 05. MCP 도구와 검증 가능한 승인

> 모든 이름·스키마·annotation은 **계획**입니다. 구현체를 읽기 전 실제 제출 JSON을 생성하지 않습니다. 호스트의 최신 standard search/fetch 계약과 충돌하면 P0에서 정합성을 검토합니다.

## 도구 표면 — 8개 제안

| 도구 | 단일 역할 | 입력 핵심 | annotation 제안 (readOnly / destructive / openWorld) |
| --- | --- | --- | --- |
| `list_projects` | 접근 가능한 개인 프로젝트 조회 | limit, cursor | true / false / false |
| `search` | 승인된 문맥 검색 | project_id, query, as_of, limit, cursor | true / false / false |
| `fetch` | 선택 문맥과 근거 조회 | id, revision 선택 | true / false / false |
| `get_context_history` | 승인·대체·철회 이력 조회 | id, limit, cursor | true / false / false |
| `build_context_pack` | 현재 질의용 최소 문맥 구성 | project_id, query, as_of, max_chars | true / false / false |
| `prepare_context_change` | create/supersede/retract/erase **승인 후보만 생성** | action, project_id, candidate 또는 target+expected_revision, idempotency_key | false / false / false |
| `get_change_status` | 승인/거절/만료/적용 상태 조회 | proposal_id | true / false / false |
| `export_context` | 선택 프로젝트를 bounded page로 반환 | project_id, format, cursor, limit | true / false / false |

`prepare_context_change`는 본문 저장, 기존 지식 대체/삭제를 수행하지 않고 짧은 수명의 draft만 저장하므로 destructive=false라는 **계획**입니다. 구현이 삭제까지 수행하면 annotation과 이름을 변경해야 합니다. export가 파일 생성/작업 enqueue를 한다면 readOnly=true를 그대로 유지할 수 없습니다.

닫힌 개인 서비스 안의 조작으로 한정하므로 openWorld=false를 제안합니다. 공개 게시·다른 시스템 변경·임의 외부 URL 접근을 추가하면 다시 검토해야 합니다. 메타데이터는 실제 부작용을 읽고 확정하며 권한 검사 자체를 대신하지 않습니다. [S-04](13_SOURCES_AND_VERIFICATION.md)

## 요청·응답 규칙

입력은 작고 목적이 분명해야 합니다. `full_conversation`, `raw_chat_log`, 광범위한 사용자 프로파일, `tenant_id`, 모델이 꾸민 `approved=true`는 받지 않습니다. 프로젝트 선택이 없으면 list_projects 결과 또는 온보딩 화면으로 사용자가 선택하게 합니다.

조회는 불투명 ID, 읽기 쉬운 제목/statement, 유효 상태, 제한된 provenance와 상세 링크를 반환합니다. 내부 로그, 토큰, 연결 문자열, 접근 불가능한 다른 프로젝트 ID를 노출하지 않습니다. public-facing resource URL은 본인 서비스의 인증 경로만 사용하며 민감한 query string은 넣지 않습니다.

모든 도구에 실제 `inputSchema`·`outputSchema`·에러 구조를 정의합니다. 페이지 cursor는 서명하고 principal/project/filter/snapshot에 바인딩하며 변경된 조건에 재사용할 수 없게 합니다. 삭제된 내용은 오래된 cursor로도 반환하지 않습니다.

## 승인 모델 — 중요

**OAuth 연결 승인 ≠ 특정 내용을 저장/삭제하는 승인.** 또한 모델이 `approved=true`라고 보낸 것은 사용자가 승인했다는 증거가 아닙니다.

MVP 제안은 별도의 인증된 검토 페이지입니다. 호스트 내 위젯은 나중에 추가할 수 있습니다.

1. 명시적 사용자 요청 후 최소 draft를 생성하고 고정 서비스 도메인의 review URL을 반환합니다.
2. 사용자가 본인 계정으로 review 페이지를 엽니다. URL 자체는 승인 권한이 아닙니다.
3. 페이지에서 정확한 statement/출처/프로젝트/시점/삭제 범위를 표시합니다.
4. 사용자 클릭과 CSRF 보호된 요청을 서버가 검증합니다.
5. 서버는 principal, project, action, target revision, canonical payload digest, nonce, expiry에 묶인 승인 기록을 만듭니다.
6. 같은 트랜잭션에서 승인된 내용을 적용합니다. 서버 내부 apply를 임의 MCP 쓰기 도구로 공개하지 않습니다.
7. 호스트는 get_change_status로 완료 결과를 확인합니다. approval secret은 모델 텍스트로 전달하지 않습니다.

플랫폼이 내용·사용자·시점에 바인딩된 검증 가능한 승인을 제공하면 그 메커니즘으로 바꿀 수 있습니다. 단순 UI 확인 문구만으로 서버가 승인을 검증할 수 있다고 가정하지 않습니다. P0에서 사용성·호스트 지원을 실제 확인해야 합니다.

## 재시도·동시성

idempotency 범위는 principal + project + operation + key입니다. 같은 key+같은 canonical payload는 동일 proposal/result를 반환하고, 같은 key+다른 payload는 `IDEMPOTENCY_CONFLICT`입니다.

expected_revision이 달라지거나 pending payload가 바뀌면 기존 승인을 무효화하고 다시 검토합니다. 적용 후 재시도는 중복 기록이나 중복 삭제를 만들지 않습니다.

## 오류 계약

| 코드 | 의미 | 다음 동작 |
| --- | --- | --- |
| `AUTH_REQUIRED` | 인증/재인증 필요 | 공식 OAuth 흐름 |
| `NOT_FOUND_OR_FORBIDDEN` | 존재 여부를 공개할 수 없음 | 허용 프로젝트 확인 |
| `INVALID_INPUT` | 계약·크기·시간 오류 | 해당 필드만 수정 |
| `SENSITIVE_INPUT_REJECTED` | 금지 정보 감지 | 내용을 응답/로그에 되풀이하지 않음 |
| `REVISION_CONFLICT` | 화면 표시 후 대상 변경 | 최신 revision 확인 후 새 승인 |
| `IDEMPOTENCY_CONFLICT` | 같은 키에 다른 내용 | 키 재사용 중단 |
| `APPROVAL_EXPIRED` | 승인이 만료/변경됨 | 새 proposal 검토 |
| `RATE_LIMITED` | 한도 도달 | 서버 retry hint 범위에서 재시도 |
| `SOURCE_UNAVAILABLE` | 근거 확인 불가 | 확인되지 않았음을 표시 |

## Skill 지침 초안

Skill은 사용자가 저장/검색/정정/삭제를 명시적으로 요청하거나 해당 프로젝트의 문맥을 이어 쓰려는 경우에만 적용합니다. 일반 대화마다 이 서비스를 호출하거나 다른 플러그인 선택을 방해하지 않습니다.

구체적인 tool 이름과 호출 순서는 구현 후 검증한 descriptor에 맞춰 작성합니다. 이 설계 패키지에는 실행 가능한 plugin manifest나 배포 가능한 Skill을 넣지 않았습니다.
