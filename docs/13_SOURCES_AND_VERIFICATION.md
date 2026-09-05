# 13. 출처와 검증 기록

확인 기준일: **2026-08-29 (Asia/Seoul)**. 아래 링크는 사실 근거입니다. 제품 구조·수치 목표·도구 목록은 설계 제안이며 외부 문서가 이 제품의 품질을 보증하는 것이 아닙니다.

## 기존 저장소 — 실제 연결된 GitHub로 읽음

기준 commit: `356808216896a2024eee5329e026836b9f8e14bf`, default branch: `main`.

| ID | 자료 | 확인한 범위 |
| --- | --- | --- |
| R-01 | [기존 아키텍처 문서](https://github.com/battle-doll/code-ontology-companion/blob/356808216896a2024eee5329e026836b9f8e14bf/docs/ko/ARCHITECTURE_AND_ROADMAP.md) | 문서상 0.5.2, 로컬 정적 분석, evidence, immutable snapshot, read-only MCP |
| R-02 | [기존 제출 문서](https://github.com/battle-doll/code-ontology-companion/blob/356808216896a2024eee5329e026836b9f8e14bf/SUBMISSION.md) | Skills-only 계획과 로컬 MCP 경계. 실제 등록 상태는 미검증 |
| R-03 | [기존 기여 정책](https://github.com/battle-doll/code-ontology-companion/blob/356808216896a2024eee5329e026836b9f8e14bf/CONTRIBUTING.md) | 버전/릴리스·다국어·보안 경계 변경 시 별도 검토 요구 |
| R-04 | [기준 커밋](https://github.com/battle-doll/code-ontology-companion/commit/356808216896a2024eee5329e026836b9f8e14bf) | 조회한 main의 immutable revision |

이번 작업은 문서와 메타데이터 조회입니다. 기존 분석기 실행, 전체 코드 감사, golden test 실행, CI 통과, 공개 디렉터리 등록을 확인했다고 주장하지 않습니다. 기존 저장소를 수정하지 않았습니다.

## 공식 OpenAI 문서 — 현재 웹 확인

| ID | 자료 | 이 설계에 적용한 사실 |
| --- | --- | --- |
| S-01 | [Plugins in ChatGPT and Codex](https://help.openai.com/en/articles/20001256-plugins-in-codex/) | plugin/app/skill 구분, 계정·표면별 이용 조건, 일부 imported MCP plugin의 Desktop-only 경계 |
| S-02 | [Plugin guidelines](https://developers.openai.com/plugins/app-guidelines) | 목적별 최소 입력, 전체 채팅 수집/복원 금지, 민감정보 경계, 정직한 기능 설명 |
| S-03 | [Authentication](https://developers.openai.com/plugins/build/auth) | MCP resource 보호, OAuth/PKCE, issuer/audience/expiry/scopes 검증 |
| S-04 | [Define tools](https://developers.openai.com/plugins/plan/tools) | 도구를 사용자 목적에 맞춰 설계, 실제 부작용에 맞는 annotation |
| S-05 | [Submit plugins](https://developers.openai.com/plugins/deploy/submission) | Skills-only/With MCP 선택, 제출 자료·신원·도메인·시험, 제출→승인→게시의 구분 |
| S-06 | [Build an MCP server](https://developers.openai.com/plugins/build/mcp-server) | Python/TypeScript 공식 SDK, streamable HTTP, custom UI는 선택 |

이전 `/apps-sdk/` 주소를 조회했을 때 `/plugins/`로 리다이렉트된 문서가 있었습니다. 새 구현은 canonical 경로와 실제 현재 API를 확인해야 합니다. 위 사실만으로 특정 계정에 모든 기능이 제공된다고 판단하지 않습니다.

## GitHub 등록 helper의 공식 참고

| ID | 자료 | 사용 범위 |
| --- | --- | --- |
| G-01 | [gh repo create](https://cli.github.com/manual/gh_repo_create) | private 신규 저장소와 초기 README 생성 |
| G-02 | [gh pr create](https://cli.github.com/manual/gh_pr_create) | base/head 지정, draft PR 생성 |
| G-03 | [gh auth setup-git](https://cli.github.com/manual/gh_auth_setup-git) | 인증 helper 개념 참고. 제공 스크립트는 전역 설정을 변경하지 않음 |

## 대화에서 가져온 사용자 결정

근거는 현재 대화의 “별도 Plugin + 공통 계약·코어” 채택과 새 설계·개발 저장소 요청입니다. 대화 원문 전체, 사용자 프로필, 무관한 개인·직장·건강·투자 정보는 포함하지 않았습니다. 문서 속 프로젝트/결정 예시는 모두 synthetic입니다.

## 이 세션에서 확인한 실행 제약

연결된 GitHub tool 목록은 읽기/조회 액션만 제공했습니다. 추가 write-capable plugin 검색에서도 대안을 얻지 못했고, 로컬 실행 환경에는 인증된 GitHub CLI가 없었습니다. 따라서 원격 저장소 생성·commit·push·PR은 실행하지 않았습니다.

이 패키지의 bootstrap은 사용자 측 인증된 Codex 환경에서 실행할 도구입니다. 원격 작업은 모의 시험과 실제 실행을 구분해 보고해야 합니다.

## 다음 검증 규칙

Codex가 P0/P3을 수행할 때 재조회 날짜, 문서 URL, 실제 tool/schema version, 현재 구현과의 차이, 수정 ADR을 기록합니다. 공식 문서가 달라지면 이 설계를 근거로 구 API를 강행하지 않습니다.

# 출처와 검증 범위 — 2026-09-05

## 원본 자료

원본 파일은 Files Library에서 회수한 `context-ontology-companion-design-pack.zip`입니다. 생성일은 Library 메타데이터상 2026-08-29입니다. 57개 파일, 원본 schema 3개와 fixtures 8개를 확인했습니다.

현재 GitHub Code README blob SHA: `5e5b50d1b4798967cdc3724940b6204322dd8c90`. README는 0.5.3과 기존 읽기 전용 정적 분석 경계를 설명합니다. README blob 식별자와 저장소 commit 식별자를 혼동하지 않습니다. 두 새 저장소 조회는 404이며, 접근 불가/부재는 구분되지 않았습니다. 원격 변경은 없습니다.

## 공식 문서

- S-01: [GPT-5.6 and GPT-6 Pro in ChatGPT](https://help.openai.com/en/articles/20001354-gpt-56-and-gpt-6-pro-in-chatgpt) — Astra/GPT-6 Pro 명칭과 제품별 제공 차이; 이 프로젝트의 성능 향상은 별도 측정해야 한다.
- S-02: [GPT-6 Astra introduction](https://openai.com/index/gpt-6-astra/) — 공식 제품 발표. 발표 벤치마크를 이 프로젝트 결과로 사용하지 않는다.
- S-03: [Plugin architecture](https://developers.openai.com/plugins/concepts/plugins) — Skills/MCP/선택 UI를 조합할 수 있고 기능은 표면별로 다를 수 있다.
- S-04: [Package your plugin](https://developers.openai.com/plugins/build/plugins) — 패키징 지침. 임의 plugin 부모/자식 설치 및 권한 상속 기능을 추정하지 않는다.
- S-05: [Submit plugins](https://developers.openai.com/plugins/deploy/submission) — 실제 패키지/계정/검증/제출 절차는 개발 시 재확인; 소스 공개와 등록은 별개.
- S-06: [Plugin guidelines](https://developers.openai.com/plugins/app-guidelines) — 독립적인 목적, 실제 side effect와 맞는 도구, 최소 데이터 수집. 전체 채팅 자동 수집을 제품 목표로 두지 않는다.
- S-07: [Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices) — 작업별 평가·반복 비교를 참고한다. 특정 외부 Evals 서비스에 제품 평가를 종속하지 않는다.
- S-08: [ChatGPT Work and Codex](https://help.openai.com/en/articles/20001275) — 제품별 사용량 체계와 Astra 사용량 차이를 설명한다. 구독/API 비용을 혼동하지 않는다.

공식 문서의 변경 가능성이 있으므로 실제 구현/제출 시 다시 확인합니다. 이 문서의 설계 제안은 OpenAI 보증이 아닙니다. 이 검토에서는 Sol/Astra 양 모델의 통제 실험, 실제 호스트 E2E 또는 공개 디렉터리 승인 확인을 수행하지 않았습니다.
