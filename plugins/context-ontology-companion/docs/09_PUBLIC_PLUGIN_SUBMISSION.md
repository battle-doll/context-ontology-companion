# 09. 공개 플러그인 등록 런북

확인일: 2026-08-29. 공식 문서의 canonical 경로는 현재 `/plugins/`이며 과거 `/apps-sdk/` 링크는 일부 리다이렉트됩니다. 메뉴·계정·심사 조건은 제출 시 다시 확인하세요. [출처 S-01~S-06](13_SOURCES_AND_VERIFICATION.md)

## 목표 형태

Context 제품은 **With MCP + 필요한 Skill**을 우선 대상으로 합니다. 사용자 간 세션을 넘어 지속 상태를 보관하는 원격 서비스와 인증을 제공해야 하므로, 스킬만 포장해 지속 기억 기능이 완성됐다고 하지 않습니다.

UI가 없는 MCP도 제출할 수 있습니다. 다만 이 설계의 사용자 승인/삭제 관리 화면은 운영 사이트로 필요하며, ChatGPT 내 위젯을 사용하는지는 별도 결정입니다. 로컬 stdio나 imported `.mcp.json`은 공개 ChatGPT 웹 동작을 보장하지 않습니다.

## 준비 순서

1. 실제 MCP 구현과 도구 schema, hint, side effect를 검토합니다.
2. 운영 HTTPS 주소·인증·최소 권한·도메인 검증·rollback을 준비합니다.
3. 소유자 신원/조직과 제출 권한을 확인합니다.
4. 실제 데이터 처리와 일치하는 privacy/terms/support와 배포 국가를 결정합니다.
5. 실제 지원 표면에서 최종 Skill과 MCP 버전을 시험합니다.
6. 구현을 읽어 `chatgpt-app-submission.json` 등 현재 포털이 받는 자료를 만듭니다.
7. 포털에서 Create plugin → With MCP를 선택하고 server/tools/skills/listing/tests를 검토합니다.
8. 소유자의 최종 확인 후 Submit for Review를 수행합니다.
9. 리뷰 결과를 확인하고 필요한 수정은 별도 버전으로 제출합니다.
10. 승인 후 소유자가 게시를 선택하고 실제 listing을 확인합니다.

공식 문서는 제출, 승인, 게시를 별도 단계로 설명합니다. GitHub 공개와도 별개입니다. [S-05](13_SOURCES_AND_VERIFICATION.md)

## 준비 자료

| 자료 | 완료 증거 |
| --- | --- |
| 제품 이름/설명/카테고리 | 실제 기능과 일치하며 무제한 기억·공식 보증 문구가 없음 |
| 개발자 신원/제출 권한 | 실제 계정에서 확인. 민감 증빙을 repo에 보관하지 않음 |
| HTTPS MCP와 인증 | 공개 운영 endpoint에서 성공·거절·재인증 시험 |
| 도메인 검증 | 포털이 요구하는 실제 challenge로 확인 |
| tool metadata | 모든 hint와 input/output schema를 최종 구현과 대조 |
| Skill bundle | 최종 파일 트리로 시험, 좁은 trigger, 미승인 행동 금지 |
| privacy/terms/support | 실제 주소·운영·보존·삭제·수탁자와 일치 |
| 데모 계정 | 가상 데이터만 사용, reviewer가 접근 가능한 격리 환경 |
| 긍정/부정 사례 | 최소 공식 요구량, 이 패키지는 5+3의 초안 제공 |
| 국가·언어 | 지원과 법적 준비가 된 범위만 선택 |
| 배포 증거 | commit·tag·artifact digest·test·rollback |

데모 계정 비밀번호는 저장소에 넣지 않고 공식 제출 경로에만 전달합니다. reviewer 접근을 편하게 만들기 위해 실제 사용자 계정의 MFA나 운영 보안을 끄지 않습니다. 별도 synthetic demo tenant를 사용합니다.

## Skill와 metadata 업데이트

공개 metadata/Skill은 심사된 snapshot으로 다뤄질 수 있습니다. 서버 파일을 바꿨다는 이유만으로 공개 배포된 Skill이 자동 갱신됐다고 하지 않습니다. 현재 포털의 Scan Tools, 검토, 버전 제출, 게시 절차를 재확인하세요. [S-05](13_SOURCES_AND_VERIFICATION.md)

## Codex가 자동 확약하면 안 되는 것

유료 인프라 구매, DNS 변경, 개인/사업자 신원 확인, 개인정보/약관 법적 확약, 배포 지역의 법적 준비, 운영 데이터 이관, 최종 공개 전환·제출·게시입니다. 필요한 자료와 실행 가능한 다음 단계를 준비하고 소유자 결정을 받습니다.

등록 도구나 계정 권한이 없다면 제출 준비 자료까지만 완료하고 `submission-ready`와 `submitted`를 구분합니다. 예상 심사 시간이나 승인 가능성을 보장하지 않습니다.

## 현재 상태

이 패키지에는 서버 구현이나 운영 endpoint가 없으므로 실제 제출용 manifest를 만들지 않았습니다. 제출 초안은 `submission/`에만 있으며 상태는 `DESIGN_ONLY_NOT_SUBMITTABLE`입니다.

## v2: Contracts 공개 플러그인

Contracts 역시 사용자가 요청한 독립 공개 제품입니다. 첫 형태는 지원 환경에서 검증 스크립트를 실행하는 skills 패키지를 우선 검토합니다. 실제 실행 기능이 없는 호스트에서 deterministic validation을 완료했다고 표시하지 않습니다. 원격 MCP는 별도 배포·정보 전송·동의·운영 결정을 요구합니다. 제품별 등록 상태를 따로 추적하며 계약 릴리스와 디렉터리 승인을 혼동하지 않습니다. 공개 심사 문서는 최종 구현을 확인한 뒤 생성합니다.
