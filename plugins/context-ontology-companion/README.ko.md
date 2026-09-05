# Context Ontology Companion

[English](README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Русский](README.ru.md)

프로젝트에서 선택한 결정, 요구사항, 제약을 로컬에 저장하고 출처와 변경 이력과 함께 다시 찾습니다. 프로젝트가 바뀌면 기록을 수정·철회·삭제하고, 필요한 문맥을 다른 도구에서 사용할 수 있도록 내보낼 수 있습니다.

macOS, Windows, Linux에서 Python 3.11 이상으로 실행합니다. API 키나 원격 서비스는 필요하지 않습니다.

## 설치

```text
codex plugin marketplace add battle-doll/context-ontology-companion
codex plugin add context-ontology-companion@context-ontology-preview
```

스킬, 서버, 스키마가 함께 제공되는 전체 플러그인을 설치하세요.

## 프로젝트 연결

Codex에서 사용할 프로젝트를 열고 다음과 같이 요청하세요.

```text
$manage-approved-context
현재 프로젝트에 이 플러그인의 로컬 MCP 연결을 설정해줘.
```

설정 후 같은 프로젝트에서 새 작업을 열면 MCP 도구를 사용할 수 있습니다. 직접 실행할 명령, 설치된 플러그인 경로, 운영체제별 안내는 [로컬 MCP 설정](docs/LOCAL_MCP.md)과 [Windows 빠른 시작](docs/WINDOWS_QUICKSTART.md)을 참고하세요.

## 사용

저장할 결정을 구체적으로 요청하세요.

```text
$manage-approved-context
이 프로젝트의 요구사항으로 macOS, Windows, Linux를 지원한다고 저장해줘.
이 메시지를 출처로 사용해줘.
```

나중에 다른 작업에서 다시 찾을 수 있습니다.

```text
$manage-approved-context
이 프로젝트가 지원하는 운영체제를 찾아 출처와 함께 보여줘.
```

선택한 기록의 수정·삭제, 변경 이력 조회, 문맥 내보내기도 요청할 수 있습니다. MCP 연결 없이 사용할 수 있는 CLI 명령은 [로컬 사용 가이드](docs/LOCAL_USE.md)에 있습니다.

데이터는 저장소 밖에 로컬 OS 계정 기준으로 보관되며 프로젝트 경로별로 구분됩니다. 선택한 내용만 저장하고 대화 전체를 자동 수집하지 않습니다. 저장된 결정은 문맥이며 이후 작업의 실행 권한을 부여하지 않습니다. 인증정보나 민감한 개인정보는 저장하지 마세요. 클라우드에서만 실행되는 호스트는 로컬 런타임에 별도로 연결해야 합니다.

## 업데이트

```text
codex plugin marketplace upgrade context-ontology-preview
codex plugin add context-ontology-companion@context-ontology-preview
```

업데이트 후 위의 프로젝트 연결 요청을 다시 실행하고 새 작업을 열면 새로 설치된 버전을 사용합니다.

## 도움말

[문서](docs/ko/README.md) · [지원](SUPPORT.md) · [개인정보](PRIVACY.md) · [보안](SECURITY.md) · [변경 이력](CHANGELOG.md)

[Apache-2.0](LICENSE) 라이선스로 배포합니다.
