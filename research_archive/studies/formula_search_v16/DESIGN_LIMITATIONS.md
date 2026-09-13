> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# 독립 설계 감사: 해석 범위와 주의점

이 문서는 모델 결과를 읽지 않고 기존 원본 데이터, 라벨 구성, 분할, 질의 슬롯과 프로그램 후보를 확인한 기록이다. `audit_design16.py`가 입력 해시와 구조적 수치를 검증하고 `DESIGN_AUDIT.json`을 생성한다. 기존 실험과 기본 LAPA 패키지는 수정하지 않는다.

## 1. QKV 가설과 분리해야 할 기존 문제

QKV가 LAPA의 일반화를 방해한다는 것은 검증할 가설이지 출발 시 확정된 결론이 아니다. 최종 목적지 QK 결합을 제거하는 실험과 모든 encoder self-attention QKV를 제거하는 실험은 서로 다르다. 동일 encoder에서 최종 결합만 바꾸는 대조군과 attention-free encoder를 분리해 해석해야 한다.

기존 프로그램 점수도 이미 `width`, `endian`, `sign`, `base`, `mask` 축별 점수의 합으로 구성된다. 따라서 base/endian/width라는 이름을 다시 붙이는 것만으로 새 구조가 되는 것은 아니다. source 조건화, 점수 정규화, 유효 프로그램 지지집합, 게이트와 목적지 집계 중 무엇이 달라졌는지 명시해야 한다. SMB2 인접 offset/length 결합 규칙과 DNS pointer의 마스크·가드는 단순한 세 속성보다 많은 사전 지식을 포함한다.

## 2. 프로토콜 및 수집 파일 분할

원본 train/development/evaluation은 raw hash와 communication group이 서로 겹치지 않는다. 그러나 train/development에는 공통 capture hash가 **2개** 있다. 하나에는 DNS와 TLS가 포함되고, 다른 하나에는 SMB2가 포함된다. 따라서 내부 DNS↔TLS 교차 프로토콜 검증은 같은 수집 파일을 공유할 수 있다. 내부 검증을 capture-held-out이라고 표현하면 안 된다.

최종 evaluation은 train 및 development와 raw/group/capture가 모두 분리된다. 다만 이 evaluation은 여러 이전 실험에서 이미 확인한 역사적 평가 세트다. 이번 결과는 탐색적 비교이며 신규 blind confirmatory 결과가 아니다. 실제 프로토콜의 원본 바이트만 사용하며 합성 프로토콜은 생성하지 않는다.

## 3. 목표 프로토콜 정답을 이용하지 않는 수식 선택

각 outer held-out protocol마다 나머지 세 프로토콜만 사용한다. 그중 둘로 학습하고 셋째의 development로 평가하는 내부 2→1 검증을 세 번 구성한다. 후보 선택에는 이 세 점수와 search seed만 사용하고, outer target의 development 및 evaluation 점수를 사용하지 않는다.

전체 네 프로토콜에서 가능한 두 프로토콜 학습 조합은 여섯 개다. 동일 학습 조합의 모델을 재사용하되, 각 outer fold는 자신의 target을 제외한 내부 검증 점수만 읽는다. 각 development의 표본은 라벨이나 성능을 보지 않고 `(raw_sha256, message_id)` 순서의 처음 32개 메시지로 고정한다. 예측 시에는 항상 64개 ordinal slot을 모두 질의한다.

선택 점수는 필드마다 `log(byte_length + 2) - NLL`을 계산하고, 프로토콜 내부의 비어 있지 않은 `relation × {INTERIOR, END, NULL}` 그룹 평균을 동일 가중으로 평균한 뒤 세 내부 검증 프로토콜과 seed를 평균한다. 동일 표본과 가중치에서는 negative NLL과 후보 순위가 같으며, uniform 대비 정보 이득이라는 해석이 추가된다. 이 점수의 선택과 raw p(target), NLL, Hit@1의 보고를 구분한다. 외부 fold마다 선택된 수식이 다를 수 있으므로 하나의 공통 수식이 모든 unseen protocol에서 최적이라고 주장할 수 없다.

## 4. END 지름길과 관측 수

Modbus MBAP length와 TLS record length의 정답은 현재 train/development/evaluation에서 모두 END다. 최종 Modbus는 6개, TLS는 15개 length 필드뿐이다. Always-END의 Hit@1=1은 주소 산술을 학습했다는 증거가 아니다. END/NULL과 실제 내부 바이트 위치 INTERIOR를 분리하고, 기존 참조 예측기와 함께 해석해야 한다.

전체 최종 평가는 74개 메시지의 347개 필드다. DNS 266개, Modbus 6개, TLS 15개, SMB2 60개다. DNS TXT length는 최종 평가에 1개뿐이며 train/development에는 없다. 이 한 건의 수치에 일반적 결론을 부여하지 않는다. SMB2 train은 89개 메시지이며 다른 프로토콜의 train은 각각 1,000개다. 프로토콜 균등 샘플링을 동일하게 유지해 후보 간 데이터 노출 차이를 최소화한다.

## 5. Ordinal slot의 노출 차이

DNS 전체를 제외하면 source 프로토콜의 양성 필드는 slot 0–3에만 존재한다. 그런데 DNS 최종 266개 필드 중 **119개가 slot 4–38**에 있다. 이 slot들은 source/program/endpoint의 양성 loss를 받은 적이 없고, presence의 음성 학습 후보가 될 수 있다. 따라서 DNS 일반화 실패를 QKV 탓으로만 돌릴 수 없다. 가능한 경우 slot 0–3과 4 이상을 보조 진단으로 구분하되, 이 평가 라벨 정보를 예측 입력이나 수식 선택에 넣지 않는다.

다른 세 outer fold에는 이 의미의 미노출 양성 slot이 없다. endpoint 평가는 기존 ordinal query를 기준으로 한 정답 목적지 평가이며, 새로운 프로토콜에서 필드의 존재·위치·의미를 스스로 발견했다는 주장과는 다르다.

## 6. 프로그램 노출과 평가 확실성

공유 프로그램 bank에는 DNS masked pointer와 SMB2 little-endian compound offset/length 연산이 들어 있다. 해당 프로토콜을 전체 제외하면 그 프로그램의 양성 학습 라벨은 0개다. 알려진 실행기 규칙과 실행기 선택을 새 프로토콜에서 학습 없이 알아내는 능력은 별개다. 각 outer fold의 정확한 program 및 속성별 양성 라벨 수는 감사 JSON에 기록한다. 라벨 생성의 `select_program`은 지도학습용으로만 쓰며 모델 forward에 프로토콜 ID나 정답 구조를 전달하면 안 된다.

250-step search와 600-step final 학습은 제한된 계산 예산의 탐색이다. 최종 세 seed는 학습 초기화 변동의 작은 표본이며 독립 capture 수가 아니다. 좁은 seed 분산이 새로운 트래픽 모집단에 대한 높은 확실성을 의미하지 않는다. 기존 패키지는 최종 성능을 본 뒤 자동 교체하지 않는다.
