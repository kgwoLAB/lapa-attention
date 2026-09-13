> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# v18: Source·Width·Endian·Base 직접 attention 계획

## 목적과 범위

사용자 요청은 속성을 새로운 Q/K 벡터로 바꾸는 것이 아니라, **네 학습 요인 자체로 attention 확률을 만드는 것**이다. v18은 모든 encoder layer와 최종 목적지 readout에 이를 적용한다. 기존 LAPA·v17 코드와 결과는 보존한다. 두 수식의 우열은 가설이며, 평가 결과를 보고 수식·seed·학습량을 변경하지 않는다.

- 학습 요인: source 위치, width, endian, base의 네 확률 분포.
- 제거: Q/K projection과 dot-product similarity, 기존 backbone, learned program classifier, sign/mask head.
- 유지: encoder의 learned value projection V, output projection, residual·FFN·LayerNorm.
- 따라서 **Q/K-free이지 완전 QKV-free는 아니다.** RoPE/CoPE/TAPE/SDPA를 붙인 모델로 재명명하지 않는다.
- source scorer는 receiver/origin 및 상대 위치의 **비선형 가산 점수**다. 내부 선형 변환은 있지만 Q/K 내적이나 속성→Q/K 경로는 없다.

## 구현과 정확한 수식

`model18.py`의 기본값은 dim32, heads4, encoder2층, FFN64, 최대길이1024, ordinal slot64다. raw byte·관측 mask·공개 ordinal slot만 forward에 들어간다. 프로토콜명·정답 source/width/endian/base/endpoint는 forward 입력이 아니다.

head별 source 분포를 \(S_{is}\), source 조건부 세 축 분포를 \(W_{sw},E_{se},B_{sb}\), 결정론적 실행과 유효성을 \(T,V\)라 둔다. head 표기는 생략한다.

\[
D_{sj}=\sum_{w,e,b}W_{sw}E_{se}B_{sb}V_{sweb}\mathbf1[T(s,w,e,b;x)=j],\qquad
R_{ij}=\sum_sS_{is}D_{sj},\qquad m_i=\sum_jR_{ij}.
\]

이는 확률의 전달·집계이며 hidden vector similarity가 아니다. \(U_i\)는 관측 byte+END+NULL의 균등 분포, \(\epsilon=0.02\)다.

| 사전 고정 mode | 최종 attention 분포 |
|---|---|
| `direct` | \(A_i=(1-\epsilon)R_i/m_i+\epsilon U_i\); \(m_i=0\)이면 \(U_i\) |
| `sink` | \(A_i=(1-\epsilon)R_i+[1-(1-\epsilon)m_i]U_i\) |

`direct`는 **source까지 합산한 뒤 receiver별 유효 질량**을 정규화한다. `sink`는 invalid 실행의 확률을 중립 분포로 되돌린다. NULL은 실제 연산의 정답 endpoint이며 invalid/중립 sink와 다르다.

Encoder에서는 byte 목적지의 값 \(H W_V\)를 attention으로 집계한다. END/NULL에는 가상의 byte V를 만들지 않고 그 질량을 해당 receiver의 self-loop로 보낸다. 최종 readout에서는 END와 NULL을 서로 다른 목적으로 유지하며, 네 head의 목적지 확률을 평균한다.

## 고정 연산 사전 지식

`executor18.py`는 width={1,2,3,4}, endian={big,little}, 아래 base/address-reference operator7개를 사용한다. 전체4×2×7=56칸 중42칸이 합법적이다. executor의 내부 flat42 목록은 수치 실행용이며 학습할42/68-way program classifier가 아니다.

| Base operator | 결정론적 의미 |
|---|---|
| `field_end_forward` | source+width+decoded length |
| `packet_absolute` | decoded packet-absolute address |
| `field_start_forward` | source+decoded unsigned value |
| `field_start_backward` | source−decoded unsigned value |
| `previous_offset_plus_length` | 직전 offset+현재 length; 현재 length0의 NULL 의미 포함 |
| `offset_with_next_length` | 현재 offset; 다음 length0이면 NULL |
| `packet_absolute_masked14` | width2, 고정 marker guard와14-bit mask를 적용한 absolute pointer |

마지막 세 연산에는 SMB2 인접 필드 및 DNS pointer에 대한 **고정 구조 지식**이 있다. 이는 순수 좌표 base보다 넓은 의미다. 학습되지 않은 프로토콜을 평가하더라도 연산 사전까지 미지인 조건은 아니다. sign/mask를 학습하지 않으며 signed displacement는 이번 범위가 아니다. width1에서는 두 endian이 수치적으로 같다.

## 데이터·학습·평가 계약

- 합성 데이터 없이 기존 실제 DNS/Modbus/TLS/SMB2 capture를 사용한다. v17의 데이터 계약·분할을 그대로 참조한다. v17의 development24개/protocol manifest도 보존하지만 v18에는 개발셋 기반 선택 단계가 없으며 이를 학습·선택에 사용하지 않는다.
- Outer4개: 한 프로토콜을 train/dev 선택에서 제외하고 나머지3개로 학습한다. 최종 평가 전체는74개 메시지/347개 필드다.
- **4 targets ×2 modes ×3 seeds=24개 모델**, seed170301/170302/170303, 각600updates, 총14,400updates를 처음부터 학습한다.
- 기존 sampler 그대로 protocol균등→message균등, batch16=positive8+negative8, AdamW lr0.002·weight decay0.01, gradient clip1, 마지막600step checkpoint 고정.
- 두 mode는 동일 초기화·sample stream을 검증한다. v17과는 source/seed/data/step/sample stream을 맞추지만 서로 다른 구조의 전체 초기 가중치가 같다는 주장은 하지 않는다.
- Loss4그룹은 \(L=L_{presence}+L_{source}+L_{attributes}+L_{endpoint}\), 가중치 모두1이다. attributes는 true source에서 width/endian/base NLL의 **합**을 평균한다. width1 endian 항은 두 동치 endian을 주변화하여0으로 둔다. 별도 program loss/head는 없다.
- 정답 축·source는 학습 감독 및 예측 후 진단에서만 사용한다. 실제 추론을 먼저 봉인하고 gold로 채점한다. 목표 프로토콜에서 threshold·checkpoint·수식을 선택하지 않는다.
- 기존 v17 Off/Hybrid의4 backbone 대조군은 같은 source3개·600updates·seed·입력·출력 seal·hash를 검증한 경우에만 재사용한다. **새 v18을 backbone4개로 복제하거나24개 실행을96개로 세지 않는다.**

## 실행 순서와 산출물

구현 확인 → 실제 TRAIN packet CPU/GPU smoke → 수식·mask·실행 동등성 테스트 → 코드/데이터/계획 hash 동결 →24개 학습 → raw-only 예측·채점 → 독립 검증 → 그래프·표·보고서 순서로 진행한다. 완료·진행·실패는 체크리스트와 단계 로그에 남기며 실패를0점 결과로 대신하지 않는다.

Primary 결과는 정답 목적지 p(target), NLL, Hit@1이다. DNS label/root/RDLENGTH/TXT/pointer, Modbus length, TLS length, SMB2 length/offset을 구분하고 표본 수를 표시한다. Source·세 축·유효 질량과 INTERIOR/END/NULL도 구분한다. F1을 추가 보고하면 source-dev에서만 threshold를 정하고 endpoint 확률과 혼동하지 않는다.

Matplotlib 수치 그래프와 표는 `direct`, `sink`, 검증된 기존 대조군을 같은 평가 필드에서 비교한다. 서로 다른 seed의 평균 및 paired 차이를 기록하되3seed CI는 학습 변동만 반영함을 명시한다. 두 mode 모두 공개하고 유리한 관계만으로 승자를 선정하지 않는다.

## 해석 한계

이미 반복 확인한 historical test이므로 fresh confirmatory 결과가 아니다. Modbus/TLS END shortcut, DNS ordinal slot 노출 이동, held-out DNS mask/SMB2 연산의 positive 감독 부재, 작은 capture/표본 수를 분리해 설명한다. 업데이트 수만 같고 파라미터/FLOPs까지 같지 않다. 본 비교는 전체 구조·사전·감독이 함께 달라져 **Q/K 제거만의 단독 인과효과**로 해석할 수 없다.
