> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# LAPA 수식 탐색 v16: 정확한 수식과 비교 의미

이 문서는 [models16.py](models16.py), [losses16.py](losses16.py), 기존 `lapa-attention/src/lapa/` 구현을 설명한다. 기존 패키지를 교체하지 않는 실험용 분기다. 아래 내용은 구현·실험 설계 설명이며 어느 후보가 우수하다는 결과 주장이 아니다.

## 1. 무엇을 없애고 무엇을 유지하는가

현재 구현에는 서로 다른 두 attention 경로가 있다.

1. **Encoder 내부 QKV**: byte 표현과 ordinal query 표현을 문맥화한다. 여기의 V는 다른 위치의 표현을 혼합하는 value tensor다.
2. **최종 목적지 retrieval QK**: 문맥화된 task query와 각 byte의 key로 목적지 점수를 만든다. 이 최종 경로는 목적지 분포를 반환하며 별도의 V를 곱하지 않는다. END/NULL도 가짜 byte/value가 아니라 별도 task-head logits를 가진 출력 클래스다.

따라서 `route_sink`, `route_direct`, `route_axis`, `route_joint`는 **최종 목적지 QK를 제거**하지만 TAPE encoder의 QKV는 유지한다. `cnn_joint`만 encoder까지 CNN으로 바꾸어 **전체 모델에서 QKV를 제거**한다. 이 둘을 모두 “QKV 제거”라고 부르면 실험의 의미가 달라진다.

새 경로는 다음 순서로 목적지를 정한다.

`관측 bytes + ordinal slot → 문맥 표현 → source/program 점수 → 원본 bytes에서 프로그램 실행 → 같은 목적지의 확률 질량 합산`

목적지 QK가 없어도 source와 program의 결합으로 목적지 분포를 만들 수 있다. 단, 올바른 source/program에 충분한 확률을 주지 못하면 실행기가 정확해도 최종 예측은 틀린다.

## 2. 공통 기호와 출력 좌표

아래는 메시지 하나와 ordinal query 하나에 대한 식이다. 배치·query 첨자는 생략한다.

| 기호 | 의미 |
|---|---|
| \(x=(x_0,\ldots,x_{n-1})\) | 관측된 원본 byte 메시지 |
| \(q\) | 공개 ordinal slot ID; 필드 위치나 정답 program ID가 아님 |
| \(h_s\), \(t\) | source 후보 위치 \(s\)의 문맥 표현, task 표현 |
| \(\mathcal P\) | 모든 후보가 공유하는 68개 고정 native-v4 프로그램 |
| \(a_s\) | 학습된 source logit |
| \(b_{sp}\) | 위치 \(s\)에서 프로그램 \(p\)의 학습된 logit |
| \(\alpha_s\) | 관측 위치들에 대한 source softmax |
| \(\beta_{sp}\) | 위치 \(s\)에서 68개 프로그램에 대한 conditional softmax |
| \(V_{sp}\in\{0,1\}\) | 프로그램의 byte 완전성·guard·주소 범위 검사를 통과했는지 |
| \(T(s,p;x)\) | 관측 bytes에서 결정론적으로 계산한 목적지 |
| \(\mathcal D\) | 관측 byte 위치들에 END와 NULL을 더한 출력 support |
| \(U_d\) | \(d\in\mathcal D\)이면 \(1/(n+2)\), padding이면 0인 균등 분포 |
| \(\epsilon\) | 고정 smoothing 비율 0.02 |

배치 저장 길이가 \(L\), 메시지 실제 길이가 \(n\le L\)이면 실제 출력 배열에서 END는 인덱스 \(L\), NULL은 \(L+1\)이다. 관측 byte는 \(0,\ldots,n-1\), padding 좌표 \(n,\ldots,L-1\)의 확률은 0이다. 이 재배치는 배치화 규칙일 뿐 원본 패킷의 주소값을 변경하지 않는다.

**NULL, END, neutral sink는 서로 다르다.** NULL은 프로그램이 명시적으로 산출하는 특수 목적지이고, END는 유효한 exclusive field end다. Sink는 아직 어떤 목적지에도 보내지 않은 질량이며 기존 수식에서 균등 분포로 재분배된다.

## 3. 기존부터 존재하던 source·program 인수분해

Source는 다음과 같다.

\[
a_s=w_{\mathrm{src}}^\top h_s+c_{\mathrm{src}},\qquad
\alpha_s=\frac{\exp(a_s)}{\sum_{u\text{ observed}}\exp(a_u)}.
\]

Program은 이미 다음 **다섯 축**의 점수를 합하도록 구현되어 있었다.

\[
\mathcal A=\{\mathrm{width,endian,sign,base,mask}\},\qquad
b_{sp}=\sum_{A\in\mathcal A}\ell^A_{s,A(p)},
\]

\[
Z_s=\sum_{r\in\mathcal P}\exp(b_{sr}),\qquad
\beta_{sp}=\frac{\exp(b_{sp})}{Z_s}.
\]

\(\ell^A_s\)는 해당 축의 linear-head logits, \(A(p)\)는 프로그램의 속성이다. 이 \(\beta\)는 아직 실행 유효성 \(V\)로 제한하지 않은 분포다.

따라서 “base/endian/width head를 새로 만들었다”는 것은 이번 실험의 새로운 기여가 아니다. 이번 후보는 **최종 결합·정규화 방식, 축 감독 방식, encoder**를 변경한다. 프로그램 bank가 모든 축 조합의 완전한 Cartesian product는 아니므로, 이 구현을 다섯 개 독립 softmax를 그대로 곱한 분포와 무조건 동일시해서도 안 된다. 최종 분모는 실제 bank의 68개 후보에 대해 계산된다.

## 4. 기준 모델 `hybrid`: head별 QK와 route의 결합

### 4.1 기존 gate와 sink

\(\gamma\)는 top head의 세 번째 softmax 성분, \(\omega_{s,w(p)}\)는 width-conditioned sigmoid gate다. Top head에는 task 표현, source 가중 평균 표현, source logit의 maximum 및 log-mean-exp가 들어간다.

\[
\bar h=\sum_s\alpha_s h_s,
\qquad
\gamma=\operatorname{softmax}\!\left(g(t,\bar h,\max_s a_s,
\log\sum_s e^{a_s}-\log n)\right)_2.
\]

기존 목적지별 committed mass는 다음과 같다.

\[
R_d=\gamma\sum_{s,p}\alpha_s\beta_{sp}\,
\omega_{s,w(p)}\,V_{sp}\,\mathbf1[T(s,p;x)=d].
\]

\[
\eta=\max\left(0,1-\sum_dR_d\right),\qquad
P^{\mathrm{sink}}_d=(1-\epsilon)(R_d+\eta U_d)+\epsilon U_d.
\]

Gate로 보류되거나 invalid 실행에 해당하는 질량은 sink에 남는다. 초기 top softmax는 \((0.70,0.15,0.15)\), width gate는 약 0.5이므로 초기 committed mass는 최대 약 0.075 수준이다. 이는 초기화 특성이지 학습 후 측정 결과가 아니다. Top의 앞 두 성분은 이 구현의 목적지 계산에서 별도 경로를 만들지 않고 남는 sink 질량에 포함된다.

### 4.2 최종 head별 결합: 평균한 base에 단순 곱하는 식이 아님

Head \(h\)의 최종 retrieval logits를 \(z_{hd}\)라 하자. Byte 좌표에서는 각 attention 방식의 QK 점수이며 END/NULL에서는 별도 learned logits다.

\[
B_{hd}=\operatorname{softmax}_{d\in\mathcal D}(z_{hd}),\qquad
B_d=\frac1H\sum_{h=1}^{H}B_{hd}.
\]

기존 hybrid의 정확한 최종 분포는 다음과 같다. 현재 \(H=4\), prior strength \(\lambda=1\)이다.

\[
P^{\mathrm{hybrid}}_d
=\frac1H\sum_h
\operatorname{softmax}_{d\in\mathcal D}
\left(z_{hd}+\lambda\log\frac{P^{\mathrm{sink}}_d}{U_d}\right).
\]

동치인 곱셈 형태도 **head마다 분모가 따로** 있다.

\[
P^{\mathrm{hybrid}}_d
=\frac1H\sum_h
\frac{B_{hd}(P^{\mathrm{sink}}_d/U_d)^\lambda}
{\sum_{j\in\mathcal D}B_{hj}(P^{\mathrm{sink}}_j/U_j)^\lambda}.
\]

이를 \(B_dP^{\mathrm{sink}}_d\)를 한 번 정규화한 것으로 일반화하면 부정확하다. Route가 정답을 지지해도 해당 head의 base가 다른 곳에 강하게 집중하면 최종 정답 확률이 낮을 수 있다. 반대로 base가 route의 모호함을 보완할 수도 있다. 어느 효과가 실제로 우세한지는 비교 결과로 판단해야 한다.

## 5. 대안 다섯 개: 무엇이 달라지는가

### 5.1 `route_sink`: 최종 QK만 제거

\[
P^{\mathrm{route\_sink}}_d=P^{\mathrm{sink}}_d.
\]

Source, conditional program, top/width gate, neutral sink와 smoothing을 그대로 유지한다. Retrieval Q/K와 special-endpoint logit 모듈은 물리적으로 제거한다. Encoder 내부 QKV는 그대로다. 동일 초기화·학습 예산에서 `hybrid`와 비교하는 것이 최종 QK 결합 경로 제거에 가장 직접적인 대조다. 단, 최종 수식 변경은 학습 중 encoder에 전달되는 endpoint gradient도 변경한다.

### 5.2 `route_direct`: gate 없이 유효한 source×program을 정규화

\[
M_{sp}=\alpha_s\beta_{sp}V_{sp},\qquad
C=\sum_{s,p}M_{sp},\qquad
J^{\mathrm{direct}}_{sp}=M_{sp}/C.
\]

\[
P^{\mathrm{route\_direct}}_d
=(1-\epsilon)\sum_{s,p}J^{\mathrm{direct}}_{sp}
\mathbf1[T(s,p;x)=d]+\epsilon U_d.
\]

코드는 underflow를 줄이기 위해 \(\log\alpha_s+\log\beta_{sp}\)를 유효한 모든 \((s,p)\) 위에서 masked softmax한다. 유효한 후보가 하나도 없으면 균등 분포를 반환한다.

기존 top/width gate와 committed-mass sink를 제거하고, 유효 후보 안에서는 질량 전체를 다시 분배한다. 따라서 `route_sink` 대비 성능 변화는 QK 때문만이 아니라 **gate 제거·invalid mass 처리·정규화 변경**이 합쳐진 효과다. Padding mask, guard, 범위 검사는 유지한다.

### 5.3 `route_axis`: forward는 direct와 동일, program 감독만 변경

\[
P^{\mathrm{route\_axis}}=P^{\mathrm{route\_direct}}.
\]

동일 초기 파라미터에서 forward는 정확히 같다. 달라지는 것은 다음 절의 program loss다. 따라서 이 비교는 새로운 실행 연산을 추가하는 실험이 아니라 **같은 다섯 축 head를 어떻게 감독할지**에 대한 실험이다.

### 5.4 `route_joint`: source와 program의 공동 energy 정규화

\[
E_{sp}=a_s+b_{sp},\qquad
J^{\mathrm{joint}}_{sp}
=\frac{V_{sp}\exp(E_{sp})}
{\sum_{u,r}V_{ur}\exp(E_{ur})}.
\]

\[
P^{\mathrm{route\_joint}}_d
=(1-\epsilon)\sum_{s,p}J^{\mathrm{joint}}_{sp}
\mathbf1[T(s,p;x)=d]+\epsilon U_d.
\]

`route_axis`와 같은 축 감독을 사용하고, per-source program 정규화 \(Z_s\)를 joint 계산에서 제거한다. 별도의 learned destination logits는 없다.

**Direct와 joint의 차이**를 명시하면 다음과 같다.

\[
J^{\mathrm{direct}}_{sp}\ \propto\ V_{sp}\frac{e^{a_s+b_{sp}}}{Z_s},
\qquad
J^{\mathrm{joint}}_{sp}\ \propto\ V_{sp}e^{a_s+b_{sp}}.
\]

유효한 conditional program 질량을 \(v_s=\sum_pV_{sp}\beta_{sp}\)라 하면, 정규화 전 source marginal은 다음과 같다.

\[
\sum_pJ^{\mathrm{direct}}_{sp}\ \propto\ e^{a_s}v_s,
\qquad
\sum_pJ^{\mathrm{joint}}_{sp}\ \propto\ e^{a_s}Z_sv_s.
\]

Joint에서는 source가 program logit의 총 energy \(Z_s\)에도 영향을 받는다. 이를 추가 source evidence로 활용할 수 있지만, \(Z_s\)가 자동으로 보정된 확신도라는 뜻은 아니다. 한 위치의 모든 program logits에 같은 상수를 더하면 \(\beta\)는 변하지 않지만 \(Z_s\)와 joint posterior는 변한다. 초기에는 유효한 프로그램 수 차이도 source marginal을 바꿀 수 있다. 이 때문에 원래 source head 확률과 실제 joint source marginal을 구분해 기록한다.

### 5.5 `cnn_joint`: 같은 공동 수식, QKV 없는 encoder

Final 수식과 loss는 `route_joint`와 같다. 대신 \(h_s,t\)를 다음 CNN으로 계산한다.

- 기존 byte embedding, slot embedding, task parameter와 router의 초기값을 재사용한다.
- 위치 입력은 \(s/1024\), \(s/n\), \((n-s)/n\), \(\log(1+n)/\log(1025)\), 주기 16·64의 sin/cos 네 성분이다.
- Slot 표현의 선형 변환을 각 byte 표현에 더하고 LayerNorm/GELU로 조건화한다.
- Dilation 1, 2, 4의 depthwise 3-tap convolution, channel mixing, feed-forward residual block으로 처리한다.
- 관측 byte의 masked mean pooling과 slot query를 합친 MLP로 task 표현을 만든다.
- 모든 층에서 padding을 다시 0으로 만들며 위치 특징은 batch padding 길이가 아니라 실제 관측 길이 또는 고정 상수를 사용한다.

Q/K/V projection이나 attention weight matrix가 없다. 다만 encoder 유형, receptive field, 위치 특징, 길이 특징, 파라미터 수가 함께 바뀐다. 따라서 성능 차이를 **QKV 유무 하나의 인과 효과**로 해석하면 안 된다. 실제 메시지 길이 \(n\)는 관측 가능한 입력 정보지만 길이 shortcut을 돕는 inductive bias가 될 수 있다.

## 6. Off 대조군과 네 가지 loss

`off`는 기존 TAPE 모델의 \(P^{\mathrm{off}}_d=B_d\)를 사용한다. 양성 query의 endpoint NLL만 학습한다. Presence/source/program 파라미터에는 gradient가 없으며 auxiliary 파라미터가 변하지 않는지 검사한다. 이 모델의 미학습 field head로 field F1을 평가하지 않는다.

여섯 On 후보는 모두 다음 네 항을 가중치 1로 합한다.

\[
\mathcal L_{\mathrm{On}}
=\mathcal L_{\mathrm{presence}}
+\mathcal L_{\mathrm{source}}
+\mathcal L_{\mathrm{program}}
+\mathcal L_{\mathrm{endpoint}}.
\]

Presence는 양성·음성 그룹의 BCE 평균을 다시 평균한 class-balanced loss다. 나머지 세 항은 양성 query에만 적용한다. 정답을 \((s^*,p^*,d^*)\)로 쓰면:

\[
\mathcal L_{\mathrm{source}}=-\log\alpha_{s^*},\qquad
\mathcal L_{\mathrm{endpoint}}=-\log P_{d^*}.
\]

`hybrid`, `route_sink`, `route_direct`는 기존 bank CE를 사용한다.

\[
\mathcal L^{\mathrm{bank}}_{\mathrm{program}}
=-\log\beta_{s^*,p^*}.
\]

`route_axis`, `route_joint`, `cnn_joint`는 다섯 축 CE의 평균으로 이 한 항을 대체한다.

\[
\mathcal L^{\mathrm{axis}}_{\mathrm{program}}
=\frac15\sum_{A\in\mathcal A}
\operatorname{CE}\bigl(\ell^A_{s^*},A(p^*)\bigr).
\]

Bank CE는 실행 유효성으로 제한하기 **전** 68개 bank logits에 대한 CE다. 축 CE 역시 실행 후 joint posterior가 아니라 각 축의 logits를 감독한다. 프로그램 축을 다섯 개 감독한다고 전체 loss가 여덟 개가 되는 것은 아니다. 다섯 축 평균이 program loss 한 항을 이룬다.

계수는 모두 1이지만 bank CE와 축 평균 CE의 수치 규모·gradient는 같지 않다. 따라서 축 감독 후보의 효과에는 감독 방식과 유효한 최적화 균형의 변화가 함께 포함된다.

**정답 source를 program loss 계산에서 선택하는 것은 학습 감독이다.** 모델 forward 입력은 `ModelInputs(data, observed, slots)`뿐이다. 정답 source/program, 필드 목록, protocol ID는 forward에 전달하지 않는다. 평가에서 true-source program 확률을 읽는 작업도 raw-only 예측을 생성한 뒤 실시하는 사후 진단이며 실제 추론 경로에 oracle source를 주는 조건이 아니다.

## 7. Width/endian/base 세 가지로 충분하지 않은 이유

이번 실험은 기존 68개 bank와 원본 실행기를 그대로 공유한다. Source 위치만 알고 width/endian/base만 고른다고 모든 연산이 완전히 지정되는 것은 아니다.

| 속성·규칙 | 필요한 이유 |
|---|---|
| Width | 1/2/3/4-byte 정수의 읽기 범위와 완전성 판단 |
| Endian | 다중 byte의 big-/little-endian 해석; 1-byte는 big으로 canonicalize |
| Sign | signed displacement와 unsigned length/offset을 구분 |
| Base | packet absolute, field-end forward, field-start forward/backward 및 인접 필드 결합 |
| Mask | DNS 압축 pointer의 하위 14-bit 주소 추출 등 |
| Guard | DNS pointer 상위 bit 패턴 검사; mask와는 별도의 실행 제약 |
| Adjacent operation | SMB2 length는 앞 offset과 더하거나, offset은 뒤 length를 검사하여 NULL 의미를 해석 |
| Bounds/END/NULL | 같은 수치라도 byte 주소·exclusive end·null pointer의 유효성 및 의미를 구분 |

Program schema에는 shift/scale/bias도 있지만 이번 native bank에서는 고정 기본값을 사용한다. Guard 역시 이번 bank에서 후보 정의에 고정되어 있고 별도 여섯 번째 learned head는 아니다. 이를 학습으로 새 프로토콜 규칙 전체를 자동 발견했다고 표현해서는 안 된다.

특히 SMB2 `previous_offset_plus_length`는 단순히 field-end에 length를 더하는 규칙과 다르다. `offset_with_next_length`는 뒤 length가 0일 때 NULL로 해석한다. DNS pointer 역시 mask/guard를 제거하면 일반 absolute offset과 같아져 원래 문제의 의미를 보존하지 못한다.

## 8. 비교의 공정성과 출력 해석

| 후보 | 파라미터 수 | 최종 QK | Encoder QKV | Program loss |
|---|---:|---|---|---|
| Off | 56,649 | 유지 | 유지 | 없음 |
| Hybrid | 56,649 | 유지 | 유지 | Bank CE |
| Route-sink | 54,337 | 제거 | 유지 | Bank CE |
| Route-direct | 51,962 | 제거 | 유지 | Bank CE |
| Route-axis | 51,962 | 제거 | 유지 | 5-axis 평균 CE |
| Route-joint | 51,962 | 제거 | 유지 | 5-axis 평균 CE |
| CNN-joint | 45,298 | 제거 | 제거 | 5-axis 평균 CE |

파라미터 수는 할당된 전체 파라미터 수다. 모든 파라미터가 모든 후보에서 loss를 받는다는 뜻은 아니다. 초기화는 native 모델을 동일 순서로 생성한 뒤 필요한 모듈을 제거하여 공유되는 tensor의 초기값을 맞춘다. CNN의 새 convolution/position 모듈은 별도다. Training step 수와 sample stream은 비교 규칙에 따라 맞추지만 파라미터 수까지 동일한 실험은 아니다.

필드 decoder는 비교 일관성을 위해 기존 규칙을 유지한다: presence threshold → pre-validity \(\alpha\)의 argmax source → 해당 source의 \(\beta\) argmax program → 최종 목적지 argmax. Joint posterior의 source marginal로 decoder를 조용히 바꾸지 않는다. 따라서 field F1은 동일 readout하에서 측정한 성능이고, joint posterior 기반 최적 decoder의 성능이라는 주장은 하지 않는다.

출력 `source`/`program`은 이 pre-validity head다. 정규화된 후보에는 실제 `route.joint`, `source_marginal`, `program_conditional`, `valid_mass`를 별도로 기록한다. Retrieval을 제거한 후보의 호환용 `base` 배열은 균등 참조이며 `base_available=False`다. 이것을 “QK 경로의 성능”으로 표나 그래프에 넣지 않는다.

## 9. 어떤 의미에서 최상의 수식을 고르는가

이 실험은 TAPE를 기준 encoder로 고정한 여섯 후보의 제한된 탐색이다. RoPE/CoPE/SDPA 전체 조합에 대한 최적화가 아니다.

Outer target이 DNS라면 Modbus/TLS/SMB2 세 프로토콜 안에서만 2개 학습→나머지 1개 development 검증을 세 번 구성한다. 다른 target도 같은 방식이다. 해당 target의 development나 evaluation 점수는 그 target의 후보 선택에 쓰지 않는다.

후보 점수는 각 validation protocol의 relation×{INTERIOR,END,NULL} 비어 있지 않은 strata를 동등 평균한 \(\log(n+2)-\mathrm{NLL}\), 이후 inner protocol 세 개와 search seed 두 개를 동등 평균한 값이다. 이는 uniform 대비 log-score 이득이며 확률 자체를 protocol 간 단순 합산한 값이 아니다. 동점은 사전 후보 순서로 처리한다.

Target별 후보를 고정한 뒤 fresh seed로 세 source 전체를 학습하고 남은 target을 평가한다. Target별 선택 결과가 서로 다를 수 있다. “최상”은 **이 후보 집합·데이터·학습 예산·선택 지표 안에서 source-side validation이 선택한 수식**이라는 뜻이지, 수학적으로 보편적 최적이거나 모든 프로토콜에서 가장 우수하다는 뜻이 아니다. 최종 target 성능이 낮아도 그 수치를 보고 다른 후보로 교체하지 않는다.

기존 historical evaluation은 이전 연구 과정에서 이미 관찰한 데이터다. 따라서 새 seed와 nested 선택 규칙을 사용해도 완전히 새 blind confirmatory benchmark가 되지는 않는다. 고정 ordinal query의 학습 범위, DNS의 많은 필드 수, SMB2의 작은 데이터, Modbus/TLS의 END shortcut, 알려진 program bank도 함께 보고한다. 특히 “QKV가 방해한다”는 가설은 결과를 보기 전에 결론으로 두지 않는다.

## 10. 구현 위치

- [models16.py](models16.py): 후보 모듈 제거, encoder, route 정규화, 공통 출력 인터페이스.
- [losses16.py](losses16.py): Off endpoint-only, On 네 loss 및 축 감독 대체.
- [test16.py](test16.py): native parity, 실제 train 필드 실행 정답, padding/END/NULL, gradient, checkpoint 검사.
- [PLAN.md](PLAN.md), [select16.py](select16.py): 탐색 예산과 target별 source-only 선택 규칙.
- 기존 패키지의 `routing/program.py`, `routing/router.py`, `routing/fusion.py`, `models/lapa_attention.py`, `programs/executor.py`: faithful hybrid와 고정 프로그램 실행 의미의 기준.
