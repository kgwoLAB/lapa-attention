> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# v18 결과 보고서: Q/K 대신 Source·Width·Endian·Base 직접 attention

## 1. 결론

사용자 요청에 맞춰 **Q/K similarity를 모든 encoder layer와 최종 readout에서 제거하고 source·width·endian·base 네 학습 분포로 attention을 직접 만드는 모델을 구현·학습했다.** 속성을 다시 Q/K로 투영하는 v17 방식이 아니다. 별도 program/sign/mask 학습 head도 없다. Value projection V와 residual/FFN은 유지한다.

실제 DNS·Modbus·TLS·SMB2를 사용한3→1 평가에서 신규24개 모델을 전부 완료했다. 기존4개 backbone의 Off/On96개 대조군과 같은347개 필드를 비교했다. 신규 모델의 학습·평가 큐는450.23초(약7.5분), 각600updates, 총14,400updates였다. 이는 검증·그림·문서 작성 시간을 제외한 큐 시간이다.

**현재600step 조건에서는 네 요인 모델의 전체 p(target)가 기존 LAPA On보다 낮다. DNS pointer의 목적지 확률 상승도 올바른 source 경로의 성공으로 해석하면 안 된다.** 따라서 기본 배포 모델을 새 구조로 교체하지 않았다. 반대로 이 결과가 Q/K 자체의 필요성을 입증하는 것도 아니다. 연산 후보·보조 목적함수·파라미터화가 함께 달라진 비교다.

## 2. 무엇을 구현했는가

| 요소 | 학습하는 것 | 목적지 계산에서의 역할 |
| --- | --- | --- |
| Source | receiver별 원본 byte 위치 분포 | 어디에서 주소값을 읽는가 |
| Width | source별1/2/3/4-byte 분포 | 몇 byte를 정수로 읽는가 |
| Endian | source별big/little 분포 | byte 순서를 어떻게 해석하는가 |
| Base | source별7개 주소 참조 연산 분포 | 정수를 어느 기준 위치에 적용하는가 |

Head 표기를 생략하면 다음을 각 encoder층과 readout에서 계산한다. \(v\)는 고정 실행 유효성이다.

\[
R_{ij}=\sum_{s,w,e,b}S_{is}W_{sw}E_{se}B_{sb}\,v_{sweb}
\mathbf1[j=T(x,s,w,e,b)],\qquad m_i=\sum_jR_{ij}.
\]

- Direct: \(A_i=0.98R_i/m_i+0.02U_i\). 유효 질량0이면 균등 분포.
- Sink: \(A_i=0.98R_i+(1-0.98m_i)U_i\).
- \(U\)는 관측 byte+END+NULL에 대한 균등 분포다. Padding 확률은0이다.
- Encoder에서는 \(A\)로 learned V를 집계한다. END/NULL의 value 질량은 receiver self-loop로 보낸다. 최종 readout에서는 END와 NULL을 서로 다른 class로 유지한다.
- Source 점수는 receiver/origin/상대 위치를 더한 비선형 MLP다. 학습 선형변환은 있지만 QK 내적은 없다. 확률 전달의 행렬곱 및 AV 행렬곱은 사용한다.
- Dim32, heads4, encoder2층, FFN64, ordinal slot64, 학습 파라미터31,041개다. Direct/Sink는 동일 초기화와 sample stream을 사용한다.

Width4 × endian2 × base7의56개 조합 중42개가 합법적이다. **Base는 순수 좌표 원점만이 아니라 주소 참조 연산이다.** DNS의14-bit pointer mask/marker guard와 SMB2의 인접 offset+length/NULL 규칙은 고정 사전 지식이다. 데이터에서 새로운 연산 의미까지 무감독 발명한 실험이 아니다. 정확한 수식·코드 대응은 [FORMULAS.md](FORMULAS.md)에 있다.

## 3. 실험 조건과 loss

각 target을 학습에서 완전히 제외하고 나머지3개 프로토콜만 학습한다. 합성 프로토콜은 사용하지 않았다. Frozen v17 실제 capture의 train/evaluation split과 sampler를 그대로 재사용했으며, v18에는 development 선택 과정이 없다.

| Held-out 평가 | 학습 프로토콜 | 평가 메시지 | 평가 필드 |
| --- | --- | ---: | ---: |
| DNS | Modbus, TLS, SMB2 | 38 | 266 |
| Modbus | DNS, TLS, SMB2 | 6 | 6 |
| TLS | DNS, Modbus, SMB2 | 15 | 15 |
| SMB2 | DNS, Modbus, TLS | 15 | 60 |
| 합계 | target별 별도 모델 | 74 | 347 |

2수식 ×4targets ×3seeds(170301/170302/170303)=24개 신규 모델이다. 각600step, batch16(positive8/negative8), AdamW lr0.002·weight decay0.01·gradient clip1. 마지막600step 모델을 평가한다. 실패·seed 추가·예산 변경·target 결과에 따른 수식 선택은 없었다.

| 모델 | 실제 최적화 목적함수 |
| --- | --- |
| 기존 Off | 목적지 NLL만. LAPA 보조 head에 직접 loss를 주지 않음 |
| 기존 LAPA On/Hybrid | Presence + Source + Program + Endpoint |
| 신규 네 요인 | Presence + Source + Attributes + Endpoint |

신규 Attributes는 true training source에서 Width/Endian/Base NLL의 **합**이다. 네 그룹의 가중치는 모두1이다. Width1에서는 두 endian이 동치이므로 endian loss를0으로 둔다. Negative slot은 presence BCE만 받으며, 존재하지 않는 필드를 NULL endpoint로 학습시키지 않는다. NULL은 실제 존재하는 필드의 의미론적 정답이다.

추론 입력은 raw byte·관측 mask·공개 ordinal slot뿐이다. **프로토콜명, 정답 source/width/endian/base, 정답 필드 수는 forward에 제공하지 않는다.** 모든 메시지의64slot 확률을 먼저 저장·봉인한 후 gold로 정답 slot/source/목적지를 찾아 채점한다. 여기서 endpoint 성능은 실제 필드 slot에 대한 성능이며, 전체 필드 발견 F1과 다르다. 이번 결과를 F1으로 표기하지 않는다.

기존 대조군은 RoPE/CoPE/TAPE/SDPA × Off/Hybrid ×4targets ×3seeds=96개이며 재학습하지 않았다. 전체 artifact hash, 같은 source/seed/600step/sample stream, 동일 평가 입력·정답 식별자를 검증한 후 재사용했다. 새 구조에는 이4개 backbone이 없으므로 v18에 RoPE/CoPE/TAPE/SDPA 라벨을 붙이지 않는다.

## 4. 전체 결과

Protocol-macro: seed별로 각 protocol 안의 필드 평균을 구한 뒤4개 protocol을 동등 평균하고,3개 seed를 평균한다. 기존 Off까지 포함한10개 방법의 전체 수치는 [TABLES.md](TABLES.md), 원정밀도·표준편차·CI·seed별 값은 `SUMMARY.json`에 있다.

| 모델 | p(target) ↑ | NLL (nat) ↓ | Hit@1 ↑ |
| --- | ---: | ---: | ---: |
| RoPE + LAPA | 0.420837 | 3.063246 | 0.534492 |
| CoPE + LAPA | 0.456255 | 3.525861 | 0.509848 |
| TAPE + LAPA | 0.436009 | 3.035284 | 0.487448 |
| SDPA + LAPA | 0.414544 | 3.509370 | 0.432749 |
| Four-factor Direct | 0.295720 | 3.847661 | 0.373162 |
| Four-factor Sink | 0.311763 | 3.419171 | 0.430911 |

두 새 수식 모두 전체 p 평균이 기존 네 Hybrid보다 낮다. Sink의 NLL은 CoPE/SDPA Hybrid보다 작지만 RoPE/TAPE Hybrid보다 크다. Direct는 네 Hybrid보다 NLL도 크다. Sink−Direct의 protocol-macro NLL 차이는−0.428490 nat이며 paired3seed CI는[−0.738110,−0.118870]다. 이 비교는 Sink를 다음 배포 승자로 선정하는 과정이 아니라 두 고정 수식의 관측 차이를 보고하는 것이다.

Field-micro(347개 필드 동등 가중)는 Direct p=0.041878/NLL=6.914277, Sink p=0.052515/NLL=5.855405다. DNS가266/347개를 차지하므로 protocol-macro와 질문이 다르다. 유리한 평균만 골라서 보고하지 않았다.

## 5. 프로토콜 × length/pointer/offset

다음은 각 실제 평가 필드에서 정답 목적지에 준 최종 확률의3seed 평균이다. 기존 비교는 대표 TAPE만 본문에 넣었으며, 그림과 상세표에는10개 방법을 모두 유지했다. TAPE만 기준으로 우월성을 판정하지 않는다.

| Cohort | 필드 수 | TAPE + LAPA | Four-factor Direct | Four-factor Sink |
| --- | ---: | ---: | ---: | ---: |
| DNS length | 230 | 0.017513 | 0.002189 | 0.004742 |
| DNS pointer | 36 | 0.005098 | 0.066398 | 0.076874 |
| Modbus length | 6 | 0.816296 | 0.672724 | 0.476061 |
| TLS length | 15 | 0.850640 | 0.496778 | 0.752908 |
| SMB2 length | 30 | 0.119859 | 0.003003 | 0.003802 |
| SMB2 offset | 30 | 0.002677 | 0.001995 | 0.003353 |

추가로 요청했던 DNS RDLENGTH25개에서 Direct p=0.000209, Sink p=0.001489이며 **두 수식 모두 Hit@1=0**이다. DNS label/root/TXT/pointer를 별도 표·그림으로 분리했다. SMB2 NameLength/ContextLength/NameOffset/ContextOffset도 각각15개씩 분리했으며 신규 두 수식은 **SMB2 네 관계 모두 Hit@1=0**이다. 실행 실패를0으로 바꾼 것이 아니라, 정상적으로 생성한 확률에서 argmax가 정답이 아니었던 실제 결과다.

Modbus와 TLS의 평가 정답은 모두 END다. Always-END만으로 이 두 cohort는1점이므로, 높은 확률만으로 길이 정수를 해석했다는 증거가 되지 않는다. 신규 Sink의 TLS source p=0.702712, width p=0.984432처럼 source·축 진단을 함께 봐야 하지만, 그것도 다양한 목적지에 대한 독립 연산 검증을 대체하지는 않는다.

## 6. DNS pointer 확률 상승을 성공이라고 부를 수 없는 이유

DNS pointer에서 Direct Hit@1=0.027778, Sink Hit@1=0.083333이다. 그러나 true source 확률은 각각0.000216,0.000243에 불과하다. 서로 다른 source/연산이 같은 byte 목적지로 도달하면 endpoint 확률은 높아질 수 있다. Head 평균의 source·축 확률을 단순 곱해서 실제 경로 기여를 재구성하면 안 된다.

Sink의 구조에서 source별 목적지 분포 질량은 최대1이므로, **정답으로 표기된 source에서 정답 목적지로 오는 기여**에는 다음 상한이 있다.

\[
p_{\mathrm{true\ source}\to y}\le0.98\,\overline{S_{s^*}},\qquad
p_{\mathrm{neutral}\to y}=\frac{1-0.98\bar m}{n+2}.
\]

따라서 다른 source의 기여 하한은

\[
p_{\mathrm{other\ sources}\to y}\ge
\max\{0,p_{\mathrm{final}}(y)-p_{\mathrm{neutral}\to y}-0.98\overline{S_{s^*}}\}.
\]

저장된 예측에서 이를 사후 계산했다. 학습·평가 순위·수식을 바꾸는 추가 최적화가 아니며, Direct에는 이 상한을 잘못 적용하지 않았다.

| DNS pointer, Sink | 평균 확률질량 |
| --- | ---: |
| 최종 정답 목적지 p | 0.07687442 |
| 균등/중립 혼합의 정확한 기여 | 0.00130147 |
| 정답 source 기여의 상한 | 0.00023836 |
| 그 외 source 기여의 하한 | 0.07538077 |

36개 필드 ×3seed=108개 예측의 **정답 목적지 총 확률질량 중 최소98.057%가 annotated source 이외에서 왔다.** 98%의 패킷이 틀렸다는 의미도,108개 독립 패킷이라는 의미도 아니다. 어떤 대체 source/base 조합이 원인인지는 이 하한만으로 식별하지 않는다. 계산과 독립 검증은 `diagnose18.py`, `MECHANISM_DIAGNOSIS.json`, `INDEPENDENT_AUDIT.json`에 있다.

이 결과에서 타당한 설명은 “DNS pointer endpoint 확률이 상승했지만 의미론적 source-localization 경로는 거의 성공하지 못했다”이다. “새 구조가 pointer를 제대로 해석한다”는 headline은 지원되지 않는다.

## 7. 해석 한계와 다음 판단

- 현재는 고정600update의 historical real-data 실험이다. 보편적 최적 수식이나 충분히 수렴한 최고 성능을 찾았다는 주장은 하지 않는다.
- 95% CI는3개 학습 seed에 대한 Student t(df2) 구간이다. Capture/protocol 모집단의 불확실성이 아니며 작은 표본에서 넓다. 물리 범위로 자르지 않았다.17개 paired 대비에는 다중비교 보정을 하지 않았으므로 탐색적 근거로 사용한다.
- 신규 네 요인은42개 합법 조합, 기존 Hybrid는68개 프로그램 후보이며 보조 loss 형태·입력 위치 파라미터화·파라미터 수가 다르다. 같은 source/seed/sample/step이 Q/K 제거 단독 인과효과를 보장하지 않는다.
- DNS held-out의241/266필드는 해당 native program의 source-positive 정답 예시가 없고119/266필드는 slot4이상 positive 예시가 없다. **RDLENGTH25개는 source 학습에서 같은 연산이 관측되므로 그 실패를 미학습 연산 탓으로만 설명할 수 없다.**
- SMB2 target의 little endian, width4, 인접필드 base들은 source-positive 감독에 없다. 해당 fixed executor 후보는 존재하지만 선택을 잘 학습한 것은 아니다.
- 최종 source→target evaluation은 capture-disjoint이나 평가 protocol당 capture는1개다. TLS/SMB2는 group도 각각1개다. 원래 train/dev capture 중복과 기타 한계는 변경하지 않았다. v18은 dev 선택을 수행하지 않는다.

다음 변경을 판단하려면 먼저 네 요인 구조 안에서 source localization과 축 선택을 분리하는 **같은 operator support·같은 loss의 통제 실험**이 필요하다. 정답 source/axis를 조건으로 주는 진단을 하더라도 배포 입력이 아닌 oracle 진단으로 분명히 분리해야 한다. 현재 test에서 수식을 계속 고른 뒤 같은 test를 최종 증거로 재사용하지 않는 새 lineage도 필요하다. 이 후속 제안은 이번에 실행한 결과로 세지 않는다.

## 8. 검증과 산출물

- CPU/CUDA smoke PASS: 실제 TRAIN8메시지34필드, 각 layer4요인 gradient, QK 표준 호출 차단, padding·정규화·END/NULL·checkpoint 검증.
- 독립 감사 PASS: 신규24개+기존96개, 유한 loss14,400행, 재생 sample stream12개, 같은 Direct/Sink 초기화12쌍, NPZ2,220개, 정답 field-seed prediction10,410건 재계산.
- Source 기여 하한의17개 그룹도 독립 재계산 일치.
- 그림 숫자 감사 PASS:9개 그림, 숫자390칸, paired 효과16개,9페이지 PDF, 파일 hash248개. 작은 양의 확률은0으로 보이지 않도록 scientific notation으로 표시한다.
- Matplotlib 숫자 그림9개: PNG 및 vector SVG `figures/`; vector PDF9페이지 `output/pdf/LAPA_four_factor_attention_v18.pdf`.
- 수치표: [TABLES.md](TABLES.md), LaTeX 원본24개 `tables/`. LaTeX는 구조/숫자 검증까지이며 TeX compiler로 최종 논문 조판한 것은 아니다. `booktabs`가 필요하고, 두 overall 표의 한글 caption은 한글/Unicode를 지원하는 TeX 환경이 필요하다.
- 설계·실행: [PLAN.md](PLAN.md), [FORMULAS.md](FORMULAS.md), [REPRODUCTION.md](REPRODUCTION.md), [MASTER_CHECKLIST.md](MASTER_CHECKLIST.md), [WORK_LOG.md](WORK_LOG.md).
- `FINAL_ARTIFACTS.json`은 최종 해시를, `VISUAL_REVIEW.json`은 PDF 렌더링 검수 근거를 보존한다. 기존 배포 패키지와 v17 결과는 변경하지 않는다.
