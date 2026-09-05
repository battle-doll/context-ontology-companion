# Context Ontology Companion — 문서

[English](../README.md) | [한국어](README.md) | [日本語](../ja/README.md) | [简体中文](../zh-CN/README.md) | [Русский](../ru/README.md)

로컬 프리뷰와 제한사항부터 확인하세요. Context의 번호가 있는 설계 문서는 장기 로드맵이며 현재 런타임 지원 범위를 넓히지 않습니다.

- [로컬 프리뷰 실행](../../README.ko.md)
- [macOS / Windows / Linux 안내](PLATFORMS.md)
- [구조와 로드맵](ARCHITECTURE_AND_ROADMAP.md)
- [버전 정책](VERSION_POLICY.md)
- [출시와 롤백](RELEASE_POLICY.md)
- [보안](SECURITY.md)
- [개인정보](PRIVACY.md)
- [지원](SUPPORT.md)
- [기여](CONTRIBUTING.md)
- [변경 기록](../../CHANGELOG.md)
- [Apache-2.0](../../LICENSE)

`demo`는 합성 예제·임시 저장소·모의 승인을 사용합니다. 별도의 로컬 프로토타입에는 영구 로컬 저장소, 인증된 루프백 사람 검토 화면, 수동 설정하는 stdio를 구현했습니다. 로컬 합성 시험을 통과했으며 실제 데이터 사용·운영 인증·실제 ChatGPT/Codex 호스트 연동은 아직 지원하지 않습니다.

Code·Context·Contracts는 독립 제품입니다. 소비자는 Contracts 플러그인을 설치하지 않고 계약 산출물을 버전 고정하거나 포함할 수 있습니다. 사용자 DB·권한의 공유, 자동 플러그인 호출, 기존 Code 제품 변경을 뜻하지 않습니다.

로컬 인증 검토 화면과 수동 설정 stdio는 구현된 프리뷰이며 실제 호스트 연동과 별개입니다. 합성 데이터만 사용합니다. Windows ACL 보호는 미검증입니다.

[로컬 런타임과 인증 검토 안내(영어)](../LOCAL_RUNTIME.md)
