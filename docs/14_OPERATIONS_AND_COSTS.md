# 14. 운영 및 비용 설계

## 비용 경계

공개 MCP 서비스를 운영하려면 서버·데이터 저장·백업·도메인·관측성·지원 비용이 발생할 수 있습니다. 이 패키지는 특정 업체의 최신 가격이나 무료 운영을 보장하지 않습니다. 예산이 정해지기 전 유료 리소스를 만들지 않습니다.

기본 서버 경로는 별도 LLM API를 호출하지 않도록 설계합니다. 호스트의 ChatGPT/Codex 사용량과 서비스 인프라 비용은 별개입니다. 추후 embedding/LLM enrichment를 추가하면 데이터 수신자·비용·삭제 영향에 대해 별도 opt-in과 예산 검토가 필요합니다.

## 운영 준비

운영 endpoint, TLS, OAuth metadata, DB migration, backup/restore, deletion replay, rate limits, rollback, release ownership, 지원 채널을 준비합니다. 개발 터널과 demo를 생산 서비스인 것처럼 제출하지 않습니다.

로그는 요청 클래스·응답 시간·오류 코드·한도·권한 실패·삭제 처리 상태 중심으로 합니다. 문장/근거/토큰 원문은 로그에 넣지 않습니다. 공개 metrics에도 사용자별 내부 식별자를 노출하지 않습니다.

## 제안 한도

| 항목 | 초기 제안 | 확인 |
| --- | --- | --- |
| 단일 statement | 2,000자 | UI/schema/server가 같은 한도 사용 |
| 단일 source excerpt | 1,000자 | 과도한 대화 전달 방지 |
| 단일 context pack | 최대 12,000자, 20개 기록 기본 | 정확한 token 한도와 혼동 금지 |
| graph expansion | 2-hop 기본 | node/edge/time 예산 추가 |
| pending proposal | 15분 TTL | 만료 후 payload 삭제 검증 |
| account quota | P2 load test 후 확정 | 무제한 저장 홍보 금지 |

수치는 검토 가능한 기본값입니다. 코드가 구현되기 전 SLO나 서비스 약속이 아닙니다.

## 장애 및 rollback

읽기 장애, 쓰기 장애, 인증 장애, 인덱스 지연, 데이터 누출 의심, 삭제 지연을 분리합니다. 사고가 의심되면 쓰기·외부 공개를 중단할 수 있어야 합니다. 인덱스를 초기화해도 권한·삭제 상태를 재구성할 수 있어야 합니다.

migration은 reversible/irreversible 여부를 문서화합니다. rollback으로 지식 내용이 부활하지 않도록 삭제 원장을 다시 적용합니다. 사용 중인 schema와 서버가 호환되지 않으면 임의로 변환하지 말고 안전한 오류를 반환합니다.

## 공개 전 운영 증거

실제 배포 commit/digest, 인프라 지역, 적용된 보존 설정, restore 시험, deletion 시험, 비용 한도, 오류 알림, 비상 중단 방법, 운영 책임자를 기록합니다. 증거에 비밀이나 실제 사용자의 본문을 포함하지 않습니다.
