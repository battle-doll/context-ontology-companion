# Current checkpoint — 2026-09-05

P0 and local P1a implementation have progressed beyond the input design baseline. Read [current state](CURRENT_STATE.md) and [next actions](NEXT_ACTIONS.md) first. The original design introduction below is retained as input history, not current release status.

# 시작 안내 — 2026-09-05 개선판

이 폴더는 Context 제품의 수정 설계와 제한된 참조 실험입니다. 제품 서버, 두 새 GitHub 저장소, 공개 등록은 이번 작업에서 실행하지 않았습니다.

먼저 [재평가](docs/16_REEVALUATION_2026-09-05.md), [출시 순서](docs/07_RELEASE_ROADMAP.md), [Codex 인계서](docs/10_CODEX_HANDOFF.md), [상태](docs/agent/CURRENT_STATE.md)를 읽으세요. 별도 폴더 `ontology-companion-contracts`에는 독립 Contracts 플러그인의 설계가 있습니다.

## 재현

```bash
python scripts/validate_design.py --require-schema --require-manifest
python -m unittest discover -s tests -v
python -m unittest discover -s experiments/tests -v
```

## 원격 작업

기존 bootstrap은 과거 Context 전용 비공개 생성 도구로 보존합니다. 현재 원격 상태와 변경 범위를 확인하지 않고 `--apply`를 실행하지 않습니다. Contracts 공개 플러그인 요구는 별도 처리해야 합니다. public GitHub 소스와 공개 플러그인 게시도 서로 다른 상태입니다.

두 새 저장소에 대한 404는 존재하지 않음/접근 불가를 구별하지 못합니다. 인증된 Codex에서 확인하고 알려지지 않은 기존 자료를 덮어쓰지 않습니다. 필요한 승인이나 도구가 없으면 해당 외부 작업만 보류하고 로컬 검토를 계속합니다.
