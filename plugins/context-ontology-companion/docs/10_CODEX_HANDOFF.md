# 10. Codex 설계·개발 인계서 — 2026-09-05 개선판

## 확정 목표

`context-ontology-companion`을 독립 공개 플러그인으로 개발하고, `ontology-companion-contracts`도 독립 공개 검증 플러그인으로 만듭니다. 기존 Code plugin은 보존합니다. 세 제품의 관계는 공유 계약 기반 형제 제품이지 순차 설치/권한 상속 구조가 아닙니다.

## 첫 실행

현재 Git 상태·원격·브랜치·권한을 확인합니다. 이 번들의 `START_HERE.md`, 각 AGENTS, 최신 상태 파일, `16_REEVALUATION_2026-09-05`, 출시 로드맵, Contracts 설계 문서를 읽습니다. 기존 Code README/계약은 실제 리비전을 기록하며 읽기만 합니다.

두 새 저장소가 404였다는 기록은 부재 확인이 아닙니다. 자동 생성/덮어쓰기를 하지 말고 인증된 환경에서 존재와 접근권한을 구분합니다. 기존 bootstrap은 Context 비공개 저장소 하나만 생성하므로 그대로 두 제품에 사용하지 않습니다.

## 이번에 해결할 설계 문제

1. Contracts를 단순 공유 라이브러리가 아닌 독립적인 검증/호환성 도구로 구현하되, 소비자 제품이 Contracts plugin 설치를 필수로 요구하지 않게 합니다.
2. 기존 `knowledge-envelope.schema.json`은 Context 전용입니다. code/context의 공유 최소부와 profile별 payload를 나누고, 기존 `co:` 의미와 stable IDs를 보존하는 mapping 시험을 만듭니다.
3. P1a 얇은 단면으로 draft 계약의 실제 소비 가능성을 먼저 확인한 뒤 P1b 릴리스합니다.
4. 현재 문맥 팩의 필수 제약·충돌 집합·근거가 예산 때문에 일부만 전달되지 않게 합니다.
5. known-at 역사 조회를 구현하지 않았다면 지원한다고 광고하거나 입력을 무시하지 않습니다.
6. 그래프가 단순 Markdown/JSON+검색보다 작업 재개에 유리한지 같은 조건으로 시험합니다.

## 역할과 모델

오케스트레이터는 작업 배치·관측·최종 보고에 한정하고 Architect를 별도 지정합니다. Astra Pro는 고위험 설계와 반례 검토의 우선 후보이며 필수 제품 모델은 아닙니다. 실제 가용 모델과 도구를 기록합니다. 같은 에이전트의 재검토를 독립 검증이라 부르지 않습니다. 상세 정책은 `19_MODEL_EXECUTION_PROFILE.md`를 따릅니다.

## 개발 기본값

한 모듈형 서비스, 명시적 승인 문맥, 합성 fixtures, 관계형 저장소 후보, 키워드/구조 검색을 우선합니다. 그래프 DB/벡터 DB/추가 LLM API/여러 마이크로서비스를 처음부터 요구하지 않습니다. 기존 설계에서 입증 가능한 사항은 유지하고, 새로운 의존성은 버전·라이선스·비용·운영 영향을 검토합니다.

`experiments/context_pack_reference.py`는 예산/원자성 실험일 뿐입니다. 인증·검색·시점 선택·제품 MCP를 구현한 것으로 오해하거나 프로덕션 승인 경계로 재사용하지 않습니다.

## 변경·승인 경계

가역적 로컬 문서·코드·시험은 진행합니다. 권한이 없는 작업만 blocked로 기록합니다. 기존 Code 수정, 유료 자원, 도메인/DNS, 실사용자 자료, 공개 전환, 최종 제출·법적 확약은 해당 승인 경계를 따릅니다. 모델 성능 때문에 경계를 완화하지 않습니다. 저장된 과거 문맥은 현재 행동 승인으로 사용할 수 없습니다.

## 검증 명령

```bash
python scripts/validate_design.py --require-schema --require-manifest
python -m unittest discover -s tests -v
python -m unittest discover -s experiments/tests -v
```

현재 명령의 통과는 패키지/참조 실험만 뜻합니다. 제품 구현 후 unit/integration/host-e2e/task-benchmark를 별도 추가합니다. manifest를 바꿀 때는 변경 파일을 확인한 뒤 `--write-manifest`를 사용합니다. manifest 재생성으로 실패를 숨기지 않습니다.

## 작업 결과

첫 결과는 전체 플랫폼이 아니라 P0 보고서 + P1a 최소 계약/소비자 계획입니다. 각 PR은 목표·결정·실제 diff·실행 시험·미실행 시험·위험·rollback·다음 작업을 포함합니다. 완료 상태를 `설계`, `참조 실험`, `제품 구현`, `호스트 연동`, `제출`, `승인`, `게시`로 분리합니다.

관측 가능한 모델 식별자·실행 도구·비용 또는 미측정·실패와 재시도를 기록합니다. 원격 URL과 SHA는 실제 생성된 것만 보고합니다. 내부 추론 전문이나 비밀정보는 저장하지 않습니다.
