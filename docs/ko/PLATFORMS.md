# macOS / Windows / Linux 안내

지원 대상은 macOS·Windows·Linux이며 Python 3.11 이상을 사용합니다. OS별 실행 증거는 코드 검토나 CI 행렬 설정 여부와 구분해 기록합니다.

| OS | 실행 근거 |
| --- | --- |
| macOS | 로컬 Python 3.12.14 합성 시험 통과 |
| Windows | `not_run` — CI 구성 완료, 실행 대기 |
| Linux | `not_run` — CI 구성 완료, 실행 대기 |
| 플러그인 호스트 연동 | 대기 — 호스트 E2E·디렉터리 출시 확인 전 |

가상 환경을 만들기 전에 Python 버전을 확인합니다. 3.11 미만이면 설치된 3.11 이상 인터프리터를 선택하세요. 활성화 스크립트 대신 가상 환경의 Python을 직접 실행합니다.

## macOS와 Linux

```sh
python3 --version
python3 -m venv .venv
.venv/bin/python scripts/run.py demo
.venv/bin/python scripts/run.py tools
.venv/bin/python scripts/check.py
```

## Windows PowerShell

```powershell
py -3 --version
py -3 -m venv .venv
.venv\Scripts\python.exe scripts/run.py demo
.venv\Scripts\python.exe scripts/run.py tools
.venv\Scripts\python.exe scripts/check.py
```

핵심 예제에는 별도 셸 설치기·Docker·Node.js·관리자 권한·API 키·네트워크 서비스가 필요하지 않습니다. Python 준비와 플러그인 호스트 지원은 별도 전제입니다. Linux에서 CLI가 실행된다는 사실은 Linux 데스크톱 호스트 지원의 증거가 아닙니다.

아래 명령은 로컬 개발 코드를 실행합니다. 플러그인을 설치하거나 호스팅 서비스를 만들지 않습니다. 예제 자료는 합성 데이터입니다.

[문서 목차](README.md)

로컬 인증 검토 화면과 수동 설정 stdio는 구현된 프리뷰이며 실제 호스트 연동과 별개입니다. 합성 데이터만 사용합니다. Windows ACL 보호는 미검증입니다.

[로컬 런타임과 인증 검토 안내(영어)](../LOCAL_RUNTIME.md)
