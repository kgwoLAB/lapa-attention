> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# LAPA v17: 30개 후보 수식과 실제 구현 대응

이 문서는 `common17.py`, `models17.py`, `attribute17.py`, `locator17.py`, `execution_features17.py`, `losses17.py` 및 기존 LAPA 모듈의 **실제 구현을 설명하는 설계 명세**다. 어떤 후보가 우수한지, QKV가 성능을 저해하는지에 대한 결과를 미리 주장하지 않는다. 기존 패키지의 기본 모델은 교체하지 않는다.

## 1. 무엇을 제거하거나 바꾸는가

현재 모델에는 서로 다른 두 종류의 경로가 있다.

1. **Encoder의 Q/K/V self-attention:** 원시 바이트와 공개 ordinal query를 문맥 표현으로 바꾼다.
2. **최종 목적지 readout의 Q/K:** query 표현과 목적지 후보 표현의 점수를 계산해 목적지 확률을 만든다. 이 readout은 확률을 출력하며, END/NULL에 가상의 V 벡터를 부여해 값을 복원하는 attention layer가 아니다.

`route_*`의 다수 후보는 두 번째 경로만 제거한다. `attr_*`는 두 번째 경로를 **예측된 source·program·연산 속성에서 만드는 새로운 Q/K**로 교체한다. 따라서 `attr_only`를 “모델 전체가 QKV-free”라고 부르면 안 된다.

| 구성 | Encoder QKV | 최종 native content QK | 최종 새 attribute QK |
|---|---|---|---|
| 기존 Transformer + `hybrid` | 있음 | 있음 | 없음 |
| Transformer + `route_direct` 등 | 있음 | 없음 | 없음 |
| Transformer + `attr_only` 등 | 있음 | 없음 | 있음 |
| `cnn_shared_route`, `gru_shared_route` | 없음 | 없음 | 없음 |
| `cnn_shared_attr`, `gru_shared_attr` | 없음 | 없음 | **있음** |

CNN/GRU의 `*_route`는 encoder와 목적지 readout에서 QKV/QK가 모두 없지만, `*_attr`는 encoder만 attention-free다. `attr_content`는 속성 표현에 hidden content를 다시 추가하는 별도 대조군이다.

## 2. 공통 기호와 입력 경계

배치·query 인덱스는 생략한다. 한 메시지의 실제 관측 바이트 수를 \(n\), 배치 저장 길이를 \(L\), head 수를 \(H\), 프로그램 수를 \(P=68\)이라 한다. 기본 hidden dimension은 32, head 수는 4다.

\[
\mathcal D=\{0,\ldots,n-1,\mathrm{END},\mathrm{NULL}\},\qquad
U(d)=\frac{1}{n+2}\quad(d\in\mathcal D).
\]

텐서에서 END는 열 \(L\), NULL은 열 \(L+1\)에 저장한다. 그러나 END의 **수치적 위치**를 사용하는 특징에서는 반드시 실제 길이 \(n\)으로 되돌린다. NULL은 별개의 범주이지 위치 \(n+1\), uniform sink, 탐지 실패와 같은 의미가 아니다. Padding 열은 모든 최종 확률에서 0이다.

Forward 입력은 다음 세 가지뿐이다.

- 원시 `data` 바이트.
- 관측된 연속 prefix를 표시하는 `observed` mask.
- 공개 ordinal `slots` 값: 0부터 63까지.

프로토콜 ID, 정답 field count, 정답 source, 정답 width/endian/base/program, 정답 목적지는 forward에 제공하지 않는다. 정답은 학습 loss 및 평가·진단을 위한 별도 인덱싱에만 사용한다. Ordinal slot은 여전히 사용하므로, 이번 탐색을 “query 조건도 없는 완전한 비지도 파서”라고 해석해서는 안 된다.

Encoder가 출력하는 task 표현을 \(t\), 위치별 바이트 표현을 \(h_s\)라 쓰면 source와 program의 기본 예측은 다음과 같다.

\[
a_s=\operatorname{SourceHead}(h_s),\qquad
\alpha_s=\operatorname{softmax}_{s\text{ observed}}(a_s).
\]

속성 축은 세 개가 아니라 아래 **다섯 개**다.

\[
\mathcal A=\{\mathrm{width},\mathrm{endian},\mathrm{sign},\mathrm{base},\mathrm{mask}\}.
\]

각 축의 head logit을 \(z_s^A(c)\), 프로그램 \(p\)의 해당 속성 ID를 \(c_A(p)\)라 하면:

\[
\ell_{sp}=\sum_{A\in\mathcal A}z_s^A(c_A(p)),\qquad
\beta_{sp}=\operatorname{softmax}_{p}(\ell_{sp}).
\]

즉 기본 program 확률은 기존 bank에 있는 **유효한 속성 조합 68개를 대상으로 softmax**한 값이다. 다섯 독립 축 softmax를 단순히 곱한 완전한 Cartesian-product 분포와 같지 않다. 관측하지 않은 padding source의 program 확률은 0으로 만든다.

### 2.1 기존 program bank라는 구조적 prior

모든 후보는 같은 native bank와 executor를 사용한다. Bank에는 다음이 이미 들어 있다.

- 1/2/3/4-byte width, big/little endian, unsigned/signed.
- Packet absolute, field-end forward, field-start backward/forward.
- 이전 offset와 현재 length의 합, offset와 다음 length의 관계를 처리하는 adjacent-field 연산.
- `0x3fff` mask와 `0xc000` guard를 사용하는 masked pointer 후보.

따라서 “unseen protocol”은 알려지지 않은 연산을 무에서 발명한다는 뜻이 아니다. **연산 후보는 사전 정의되어 있고, 바이트만 보고 source·program을 선택하는 능력**을 평가한다. 특정 연산이 bank에 있는 것과 해당 연산의 양성 학습 예제를 실제로 본 것은 별개다.

Executor는 모든 \((s,p)\)를 실행해 목적지 \(E_{sp}\)와 유효성 \(v_{sp}\in\{0,1\}\)를 반환한다. 읽기 범위, sign/mask/guard, companion field, END/NULL 조건을 적용한다. 이 계산은 정답 source나 정답 program을 선택해서 실행하는 oracle이 아니다. 정수 decode와 목적지 인덱스 자체는 미분하지 않으며, 각 실행 결과에 부여하는 학습 확률에는 gradient가 흐른다.

## 3. 공통 route와 결합 연산

### 3.1 Source–program 결합과 유효 질량

\[
J^0_{sp}=\alpha_s\beta_{sp},\qquad
J^v_{sp}=J^0_{sp}v_{sp},\qquad
m=\sum_{s,p}J^v_{sp}.
\]

`route_direct`는 유효한 쌍의 확률을 재정규화한다.

\[
J^{\mathrm{direct}}_{sp}=
\frac{\alpha_s\beta_{sp}v_{sp}}{\sum_{u,q}\alpha_u\beta_{uq}v_{uq}}.
\]

실제 구현은 \(\log\alpha_s+\log\beta_{sp}\)에 유효성 mask를 적용한 global softmax다. 유효한 쌍이 하나도 없으면 joint를 0으로 반환한다. Zero denominator를 NULL로 바꾸지 않는다.

`route_joint`는 program의 source별 partition function을 제거한 별도 energy 모델이다.

\[
J^{\mathrm{joint}}_{sp}=
\frac{e^{a_s+\ell_{sp}}v_{sp}}{\sum_{u,q}e^{a_u+\ell_{uq}}v_{uq}}.
\]

두 식은 일반적으로 다르다. 첫 식은 각 source에서 program을 먼저 조건부 정규화한다. 두 번째는 source와 program logit을 합쳐 한 번에 정규화하므로, program logit의 source별 전체 크기도 source 선택에 영향을 준다.

임의의 기여 질량 \(J\)를 목적지로 모으는 pushforward는 다음과 같다.

\[
R_J(d)=\sum_{s,p}J_{sp}\mathbf1[E_{sp}=d].
\]

### 3.2 Uniform sink와 smoothing

\[
\operatorname{Prior}_\epsilon(R)(d)
=(1-\epsilon)\left[R(d)+\left(1-\sum_eR(e)\right)_+U(d)\right]
+\epsilon U(d).
\]

남은 질량은 **uniform sink**로 분배한다. 이것은 NULL endpoint 확률로 몰아주는 동작이 아니다. 기본 \(\epsilon=0.02\)이고, `smooth_route`만 0.20이다. 유효한 실행이 전혀 없으면 최종 prior는 \(U\)가 된다.

이 문서에서 다음 약자를 사용한다.

\[
D=\operatorname{Prior}_{0.02}(R_{J^{\mathrm{direct}}}),\qquad
J=\operatorname{Prior}_{0.02}(R_{J^{\mathrm{joint}}}).
\]

### 3.3 Native gated route

기존 router는 source와 program 외에 width별 well-formedness와 세 갈래 top gate를 사용한다. \(w_{sp}\)는 해당 width의 sigmoid score에 candidate mask를 곱한 값이고, \(g_{\mathrm{exec}}\)는 세 갈래 softmax의 세 번째 성분이다.

\[
R_{\mathrm{native}}(d)=
\sum_{s,p}g_{\mathrm{exec}}\alpha_s\beta_{sp}w_{sp}v_{sp}\mathbf1[E_{sp}=d],
\qquad N=\operatorname{Prior}_{0.02}(R_{\mathrm{native}}).
\]

Top gate는 \([t;\sum_s\alpha_sh_s;\max_s a_s;\operatorname{logmeanexp}_s(a_s)]\)를 입력으로 받는다. 첫 두 top-gate 성분과 나머지 미집계 질량은 별도 endpoint로 출력하지 않고, 위 uniform-sink 규칙을 통해 처리된다.

### 3.4 Head별 정규화와 product

Native readout의 head별 logit을 \(u_{hd}\)라 쓰자. 관측 바이트의 점수에는 backbone의 SDPA/RoPE/CoPE/TAPE 구현이 적용되고, END/NULL 점수는 기존 task 기반 special head가 제공한다.

\[
\mathcal S(u)(d)=\frac1H\sum_h\operatorname{softmax}_{e\in\mathcal D}(u_{he})_d,
\qquad B=\mathcal S(u).
\]

\[
\mathcal P(u,R,\lambda)
=\mathcal S\left(u+\lambda\log\frac{R}{U}\right).
\]

**각 head에서 softmax한 뒤 평균**한다. Head logit을 먼저 평균해서 softmax하는 식이 아니다. \(U\)는 메시지 내 supported destination에 대해 상수이므로, 위 식은 head별 base 확률과 \(R^\lambda\)를 곱해 다시 정규화하는 것과 같다.

## 4. 실제로 source·program·속성으로 새 Q/K를 만드는 식

구현: `attribute17.py:AttributeDestination`. Native `retrieval_query`, `retrieval_key`, `special_endpoints`를 제거하고, 이 모듈의 별도 projection을 사용한다.

### 4.1 Source 위치 embedding과 속성 예측

위치 \(s\)에 대해 다음 8개 특징을 만든다. \(M=1024\)는 고정 최대 길이이며, 분모의 \(n\)은 배치 padding 길이가 아니다.

\[
\phi(s,n)=\left[
\frac{s}{M},\frac{s}{n},\frac{n-s}{n},
\frac{\log(1+n)}{\log(1+M)},
\sin\frac{2\pi s}{16},\cos\frac{2\pi s}{16},
\sin\frac{2\pi s}{64},\cos\frac{2\pi s}{64}
\right].
\]

\[
e_s^{\mathrm{src}}=\tanh(W_{\mathrm{src}}\phi(s,n)).
\]

Program ID와 각 축의 가능한 값에는 학습 embedding \(e_p^{\mathrm{prog}}\), \(e^A_c\)가 있다. 이것은 **정답 program ID나 정답 속성을 입력하는 것**이 아니다. 모든 후보에 embedding을 마련하고, 예측 확률로 기대값을 계산한다.

\[
\bar e^{\mathrm{src}}=\sum_s\alpha_se_s^{\mathrm{src}},\qquad
\bar e^{\mathrm{prog}}=\sum_{s,p}\alpha_s\beta_{sp}e_p^{\mathrm{prog}}.
\]

\[
\gamma_s^A(c)=\operatorname{softmax}_c z_s^A(c),\qquad
\bar e^A=\sum_s\alpha_s\sum_c\gamma_s^A(c)e_c^A.
\]

Query의 축 기대값은 각 축 head의 **독립 softmax 예측**으로 계산한다. Program 기대값은 bank 위의 \(\beta\)로 계산하므로, 두 표현은 동일한 값을 이름만 바꾼 것이 아니다.

Source entropy와 source-조건부 program entropy는 다음과 같이 정규화한다.

\[
\widehat H_S=\frac{-\sum_s\alpha_s\log\alpha_s}{\log\max(n,2)},\qquad
\widehat H_P=\frac{-\sum_s\alpha_s\sum_p\beta_{sp}\log\beta_{sp}}{\log68}.
\]

Query attribute vector는 다음 순서의 concatenation이다.

\[
x_Q=[\bar e^{\mathrm{src}};\bar e^{\mathrm{prog}};
\bar e^{\mathrm{width}};\bar e^{\mathrm{endian}};\bar e^{\mathrm{sign}};
\bar e^{\mathrm{base}};\bar e^{\mathrm{mask}};
\max_s\alpha_s;\widehat H_S;\widehat H_P;m].
\]

### 4.2 목적지로 들어오는 source–program 속성으로 K 만들기

먼저 프로그램별로 목적지에 들어오는 질량을 계산한다.

\[
M_{dp}=\sum_s\alpha_s\beta_{sp}v_{sp}\mathbf1[E_{sp}=d],\qquad
m_d=\sum_pM_{dp}.
\]

여기서 source와 program을 각각 argmax로 고른 뒤 조합하지 않는다. **결합 확률과 실제 실행 목적지의 관계**를 보존한다.

프로그램의 descriptor는 다음과 같다.

\[
b_p=[e_p^{\mathrm{prog}};
e^{\mathrm{width}}_{c_{\mathrm{width}}(p)};
e^{\mathrm{endian}}_{c_{\mathrm{endian}}(p)};
e^{\mathrm{sign}}_{c_{\mathrm{sign}}(p)};
e^{\mathrm{base}}_{c_{\mathrm{base}}(p)};
e^{\mathrm{mask}}_{c_{\mathrm{mask}}(p)}].
\]

\[
\widetilde b_d=\frac{\sum_pM_{dp}b_p}{m_d},\qquad
\widetilde e_d^{\mathrm{src}}=
\frac{\sum_{s,p}\alpha_s\beta_{sp}v_{sp}\mathbf1[E_{sp}=d]e_s^{\mathrm{src}}}{m_d}.
\]

실제 코드는 분모를 \(10^{-12}\) 이상으로 clamp한다. 들어오는 질량이 0인 목적지는 분자도 0이므로 incoming embedding이 0이다.

목적지 위치 특징 \(\psi_d\)는 \(\phi(d,n)\)와 END/NULL 구분 bit 두 개다. END는 \(\phi(n,n)\), NULL의 8개 숫자 특징은 전부 0으로 두고 NULL bit만 켠다. \(\alpha_d^{\mathrm{here}}\)는 실제 byte destination에서 \(\alpha_d\), END/NULL에서는 0이다.

\[
x_K(d)=[\widetilde e_d^{\mathrm{src}};\widetilde b_d;\psi_d;
m_d;\log(1+n m_d);\alpha_d^{\mathrm{here}};m].
\]

Native content projection을 재사용하지 않고 다음의 새 Q/K를 학습한다.

\[
Q^A=W_Q\operatorname{LN}(x_Q),\qquad
K^A_d=W_K\operatorname{LN}(x_K(d)),\qquad
u^A_{hd}=\frac{\langle Q^A_h,K^A_{hd}\rangle}{\sqrt{d_h}}.
\]

\[
A=\mathcal S(u^A).
\]

`attr_only`의 최종 Q/K projection에는 \(t,h_d\)를 직접 넣지 않는다. 그러나 upstream source·program·axis 예측은 encoder hidden states에서 계산되므로, 모델이 바이트 내용을 전혀 사용하지 않는다는 뜻은 아니다.

### 4.3 Content를 다시 넣는 대조군

`attr_content`는 별도의 projection을 사용한다.

\[
Q^{AC}=W_{QC}\operatorname{LN}([x_Q;t]),\qquad
K^{AC}_d=W_{KC}\operatorname{LN}([x_K(d);h_d]).
\]

END/NULL에는 기존 special-endpoint logit head가 아니라 이 모듈의 학습 가능한 두 content embedding을 사용한다. 이 후보의 최종 분포를 \(A_C\)라 한다.

### 4.4 실행 거리 kernel

`attr_distance`는 먼저 \(r(d)=m_d/m\)을 계산한다. \(m=0\)이면 \(r=U\)다. Byte와 END의 수치 좌표를 \(\xi_d\)라 하면, Gaussian kernel은 다음과 같다.

\[
\tau=\operatorname{clip}(\operatorname{softplus}(\theta_\tau),0.25,32),
\quad \tau_{\mathrm{init}}=2.
\]

\[
G_{dj}\propto\exp\left[-\frac{(\xi_d-\xi_j)^2}{2\tau^2}\right],\qquad
\sum_dG_{dj}=1.
\]

열마다 정규화한다. Padding은 제외한다. NULL과 byte/END 사이의 kernel weight는 0, NULL→NULL weight는 1이다. **NULL을 숫자 거리로 다른 위치에 퍼뜨리지 않는다.**

\[
r_{\mathrm{kernel}}=0.75r+0.25Gr,\qquad
\widetilde r=0.98r_{\mathrm{kernel}}+0.02U.
\]

\[
\eta=\operatorname{softplus}(\theta_\eta),\quad\eta_{\mathrm{init}}=1,\qquad
A_D=\mathcal S(u^A+\eta\log\widetilde r).
\]

75% exact/25% Gaussian 비율과 2% uniform smoothing은 고정하고, bandwidth와 log-bias 강도는 학습한다. 정답 목적지 근처에 Gaussian을 놓는 것이 아니라, **모든 후보를 실행해 얻은 예측 질량**에서 kernel을 만든다. 실행 인덱스 자체는 이산적이지만, 그 질량·embedding·Q/K·bandwidth·강도에는 gradient가 흐른다.

## 5. 30개 후보의 정확한 식과 구현 분기

아래 30개가 screen 대상이며, `off`는 별도의 기준 모델이다. `off`의 최종 분포는 \(B\), loss는 endpoint NLL 하나다.

| 번호 | `variant` | 최종 분포 또는 핵심 변경 | Encoder/감독 변경 |
|---:|---|---|---|
| 1 | `hybrid` | \(\mathcal P(u,N,1)\) | 기존 모델의 정확한 forward |
| 2 | `route_sink` | \(N\) | 최종 native QK 제거, 기존 gate 유지 |
| 3 | `route_direct` | \(D\) | 유효 \(\alpha\beta\) 쌍 재정규화 |
| 4 | `route_joint` | \(J\) | \(a_s+\ell_{sp}\) global softmax |
| 5 | `axis_direct` | \(D\) | program loss를 다섯 축 CE 평균×4로 변경 |
| 6 | `attr_only` | \(A\) | 예측 source/program/다섯 축으로 새 Q/K |
| 7 | `attr_content` | \(A_C\) | attribute Q/K에 hidden content 추가 |
| 8 | `attr_distance` | \(A_D\) | 실행 거리 kernel 추가 |
| 9 | `attr_product` | \(\mathcal P(u^A,D,1)\) | attribute QK와 direct route의 product |
| 10 | `attr_mix` | \((1-g)A+gD\) | 학습 gate 사용 |
| 11 | `mix_half` | \(0.5B+0.5D\) | 고정 convex mixture |
| 12 | `mix_learned` | \((1-g)B+gD\) | 학습 gate 사용 |
| 13 | `mix_entropy` | \((1-g_E)B+g_ED\) | entropy/valid-mass 기반 고정식 gate |
| 14 | `power_learned` | \(\mathcal P(u,D,g)\) | route exponent를 학습 |
| 15 | `weak_product` | \(\mathcal P(u,N,0.1)\) | native route 강도만 0.1 |
| 16 | `stopgrad_product` | \(\mathcal S(u+\operatorname{sg}[\log(N/U)])\) | endpoint→route-bias gradient 차단 |
| 17 | `smooth_route` | \(\operatorname{Prior}_{0.20}(R_{J^{\mathrm{direct}}})\) | uniform smoothing 20% |
| 18 | `soft_joint` | joint energy \((a_s+\ell_{sp})/2\)로 만든 prior | joint temperature 2 |
| 19 | `valid_mass_route` | \(\operatorname{Prior}_{0.02}(R_{J^v})\) | 유효 질량 재정규화하지 않음 |
| 20 | `cnn_shared_route` | CNN 표현으로 계산한 \(D\) | QKV-free CNN encoder, 공유 slot |
| 21 | `cnn_shared_attr` | CNN 표현으로 계산한 \(A\) | Encoder QKV 없음, 최종 attribute QK 있음 |
| 22 | `gru_shared_route` | GRU 표현으로 계산한 \(D\) | 양방향 GRU encoder, 공유 slot |
| 23 | `gru_shared_attr` | GRU 표현으로 계산한 \(A\) | Encoder QKV 없음, 최종 attribute QK 있음 |
| 24 | `shared_slot_hybrid` | 공유 slot 표현으로 계산한 \(\mathcal P(u,N,1)\) | Transformer 유지, ordinal table 교체 |
| 25 | `aux_small` | \(\mathcal P(u,N,1)\) | presence/source/program 가중치 0.25 |
| 26 | `aux_large` | \(\mathcal P(u,N,1)\) | presence/source/program 가중치 4 |
| 27 | `bilinear_program` | 보정 program logit으로 계산한 \(D\) | source–task–program 상호작용 추가 |
| 28 | `shared_slot_route` | 공유 slot 표현으로 계산한 \(D\) | Transformer 유지, 최종 native QK 제거 |
| 29 | `execute_score` | 실행 특징으로 보정한 program logit의 \(D\) | 모든 후보의 decoded/validity/목적지 특징 사용 |
| 30 | `equivalent_program` | \(D\) | 같은 정답 목적지를 만드는 program 집합 감독 |

`attr_mix`의 gate는 hidden content를 읽는다. 따라서 “attribute Q/K 자체에 hidden content를 직접 넣지 않았다”와 “해당 모델의 모든 최종 계산에서 hidden content를 쓰지 않았다”를 구별해야 한다.

### 5.1 학습 mixture gate와 entropy gate

\[
\bar h=\sum_s\alpha_sh_s,\qquad
g=\sigma\left(\operatorname{MLP}([t;\bar h;\widehat H_S;\widehat H_P;m])\right).
\]

MLP는 hidden dimension 32, GELU, scalar output이다. 마지막 linear의 weight/bias를 0으로 초기화하므로 \(g\)는 처음에 0.5다. `mix_learned`, `power_learned`, `attr_mix`가 같은 gate 형태를 사용한다. Convex mixture의 gate와 product의 exponent는 역할이 다르다.

\[
g_E=\operatorname{clip}((1-\widehat H_S)(1-\widehat H_P)m,0,1).
\]

`mix_entropy`는 entropy가 높거나 유효 실행 질량이 작으면 direct route의 비중을 줄인다. 이 식 자체에는 학습 parameter가 없지만, entropy와 mass의 입력 확률은 학습된다. Gate의 옳고 그름을 미리 보장하지 않는다.

### 5.2 `valid_mass_route`가 direct와 다른 점

Direct는 \(m\)이 작더라도 0이 아니면 유효 쌍을 합계 1로 만든다. `valid_mass_route`는 \(J^v\)를 그대로 사용하므로, 유효 실행 질량이 \(m\)이면 나머지 \(1-m\)는 uniform sink로 남는다.

\[
R_{J^v}=m\,R_{J^{\mathrm{direct}}}\quad(m>0).
\]

따라서 극소수 유효 후보에 과도한 확신을 주는 현상을 완화할 수 있는지를 시험하는 후보이며, 항상 더 좋다고 가정하지 않는다.

### 5.3 `stopgrad_product`의 차단 범위

`route['bias'].detach()`를 적용한다. Endpoint loss가 route-bias 계산 경로로 역전파되는 것만 차단한다. Presence/source/program의 보조 loss는 그대로 학습하며, endpoint loss는 native content QK와 encoder 경로로 계속 전달된다. Encoder가 공유되므로 “source/program 관련 모든 parameter가 endpoint 학습과 완전히 독립된다”는 뜻은 아니다.

## 6. Source locator와 ordinal 표현 변경

### 6.1 공유 ordinal query

기존 구현은 `nn.Embedding(256, dim)`을 할당하지만, 입력 계약상 사용하는 slot은 0–63이다. 공유-slot 후보는 독립 lookup table 대신 하나의 MLP를 사용한다. \(r\)을 slot 값이라 하면:

\[
f(r)=\left[
\frac r{63},\frac{\log(1+r)}{\log64},
\left\{\sin\frac{2\pi kr}{64}\right\}_{k\in\{1,2,4,8\}},
\left\{\cos\frac{2\pi kr}{64}\right\}_{k\in\{1,2,4,8\}}
\right],\qquad q_r=\operatorname{MLP}(f(r)).
\]

분모는 고정 config의 slot 수로 결정한다. 정답 field count나 학습 중 관측한 마지막 slot으로 정규화하지 않는다. 평가 때 slot을 학습 범위에 맞춰 임의 remapping하지 않는다. 다만 이 변경도 ordinal 순서에 대한 의존성을 완전히 없애지는 않는다.

Transformer의 `shared_slot_*`는 query-ID embedding만 이 MLP로 바꾸며, 기존 task vector와 고정 version-index embedding은 유지한다. CNN/GRU encoder는 task vector와 공유 slot MLP를 사용하고, 독립 query-ID table이나 version table을 복사하지 않는다.

### 6.2 CNN encoder

Byte embedding, 실제 길이 기반 위치 특징, 공유 slot projection을 더해 초기 byte 표현을 만든다. 3개의 depthwise convolution block을 사용하며 dilation은 1, 2, 4다. 각 block은 depthwise convolution, channel mixing, residual LayerNorm, feed-forward로 구성한다. 관측 mask를 각 단계에 다시 곱해 padding을 지운다.

마지막 task 표현은 공개 query와 관측 byte 표현의 mean pooling을 concatenate한 MLP 출력이다. Q/K/V projection과 token attention matrix가 없다. 모든 byte 위치를 자유롭게 직접 연결하는 self-attention과 같은 구조는 아니며, convolution의 제한된 receptive field 및 mean pooling이라는 다른 inductive bias를 갖는다.

### 6.3 GRU encoder

동일한 byte/position/shared-slot 입력에 양방향 GRU를 적용한다. Layer 수는 config의 2이며 dropout은 0이다. 실제 관측 길이로 `pack_padded_sequence`를 사용하고, 출력도 관측 길이에 맞춰 복구한다. Padding을 recurrent input으로 읽지 않는다.

GRU 뒤에 residual normalization과 feed-forward가 있고, task pooling은 CNN과 같다. 양방향이므로 전체 메시지를 보는 offline 설정이다. Streaming/causal decoder와 동일한 조건이라고 주장하지 않는다.

## 7. Program 상호작용과 실행 특징

### 7.1 `bilinear_program`

\[
c_s=\tanh(W_Sh_s+W_Tt),\qquad c_s\in\mathbb R^{16},
\]

\[
\ell'_{sp}=\ell_{sp}+\frac{\langle c_s,e_p\rangle}{4},\qquad
\beta'_{sp}=\operatorname{softmax}_p\ell'_{sp}.
\]

Program embedding \(e_p\)도 학습하며 초기 표준편차는 0.02다. 분모 4는 \(\sqrt{16}\)이다. 보정한 program logit을 program CE와 direct route 양쪽에 사용한다. Source posterior는 기존 source head가 출력한다. 이 후보는 최종 native QK를 제거한다.

### 7.2 `execute_score`

Source hidden state, task hidden state, program의 다섯 속성 embedding, 실제 후보 실행의 수치 특징을 합쳐 program logit을 보정한다.

\[
b_p^{\mathrm{exec}}=\frac1{\sqrt5}\sum_{A\in\mathcal A}e^A_{c_A(p)},
\]

\[
y_{sp}=W_Sh_s+W_Tt+b_p^{\mathrm{exec}}+\sum_{j=1}^{13}f_j(s,p)w_j,
\]

\[
\delta_{sp}=\operatorname{MLP}(\operatorname{LN}(y_{sp})),\qquad
\ell'_{sp}=\ell_{sp}+\delta_{sp}.
\]

숨은 크기는 16이다. 독립 program-ID embedding을 새로 더하는 대신 factorized attribute embedding을 합산한다. 13개 수치 특징은 다음과 같다.

| 특징 | 의미 |
|---|---|
| `source_over_length` | source / 실제 길이 |
| `remaining_over_length` | 남은 길이 / 실제 길이 |
| `field_end_over_length` | (source + width) / 실제 길이 |
| `width_over_length` | width / 실제 길이 |
| `width_over_four` | width / 4 |
| `signed_log_decoded_over_log_length` | decoded 값의 sign × log 크기 / log 길이 |
| `clipped_decoded_over_length` | decoded 값 / 실제 길이, 범위 제한 |
| `valid_nonnull_target_over_length` | 유효한 비-NULL 목적지 / 실제 길이 |
| `valid_nonnull_displacement_over_length` | 유효한 비-NULL 목적지와 source의 차이 / 길이 |
| `valid` | 후보 실행의 유효 여부 |
| `null` | 유효 NULL 연산 여부 |
| `end` | 유효 END 연산 여부 |
| `candidate_mask` | 기존 executor의 후보 mask |

큰 정수 특징은 bounded range로 clamp한다. 완전히 관측되지 않은 width의 provisional decoded 값은 0으로 처리한다. Invalid target을 byte 0으로 해석하지 않고 수치 특징에서 제거하며, END는 실제 길이로 변환하고 NULL은 별도 bit로 표현한다.

마지막 scalar linear를 0으로 초기화하므로 처음에는 \(\delta=0\), 기본 program logits와 같다. Scalar head가 움직인 뒤 그 앞의 실행-feature 계층에 gradient가 전달된다. 모든 후보를 실행하는 공통 bank prior를 활용하는 것이지, 프로토콜 정답 구조를 제공하는 새 parser가 아니다.

## 8. 네 가지 loss와 감독 변경의 정확한 의미

모든 On 후보는 네 가지 loss를 **양의 가중치로** 사용한다.

\[
\mathcal L=\lambda_{\mathrm{presence}}\mathcal L_{\mathrm{presence}}
+\lambda_{\mathrm{source}}\mathcal L_{\mathrm{source}}
+\lambda_{\mathrm{program}}\mathcal L_{\mathrm{program}}
+\lambda_{\mathrm{endpoint}}\mathcal L_{\mathrm{endpoint}}.
\]

\(\mathcal L_{\mathrm{presence}}\)는 positive/negative query 각각의 BCE 평균을 다시 평균한 class-balanced BCE다. Source/program/endpoint는 정답 field가 존재하는 positive query에서 계산한다.

\[
\mathcal L_{\mathrm{source}}=-\log\alpha_{s^*},\qquad
\mathcal L_{\mathrm{program}}=-\log\beta_{s^*,p^*},\qquad
\mathcal L_{\mathrm{endpoint}}=-\log P_{\mathrm{final}}(d^*).
\]

Program loss에서 정답 source \(s^*\)를 인덱싱하는 것은 **학습 감독**이다. 평가 forward에서 정답 source를 input으로 제공한다는 뜻이 아니다. Endpoint loss는 예측 source와 program을 거친 최종 확률에 적용한다. Presence prediction이 낮다고 endpoint 정답 확률에 곱해 줄이는 방식도 아니다.

| 후보 | Presence | Source | Program | Endpoint |
|---|---:|---:|---:|---:|
| `off` | 사용 안 함 | 사용 안 함 | 사용 안 함 | 1 |
| 일반 On | 1 | 1 | 1 | 1 |
| `aux_small` | 0.25 | 0.25 | 0.25 | 1 |
| `aux_large` | 4 | 4 | 4 | 1 |

`axis_direct`와 `equivalent_program`도 위 일반 On 가중치를 사용하지만, program 항의 **내용**을 바꾼다.

### 8.1 `axis_direct`: 다섯 축에 직접 CE

\[
\mathcal L_{\mathrm{program}}^{\mathrm{axis}}
=\frac4{5}\sum_{A\in\mathcal A}
\operatorname{CE}(z_{s^*}^A,c_A(p^*)).
\]

구현은 “5개 CE의 평균 × 4”다. **4개 축만 학습한다는 뜻이 아니다.** 스케일 4는 실행 전 고정값이다. 다른 loss는 그대로이며, forward에서는 기존 68개 program logit 합산 및 direct route를 사용한다.

### 8.2 `equivalent_program`: 실행 결과가 같은 program 집합

\[
\mathcal E(s^*,d^*)=\{p:v_{s^*,p}=1,\ E_{s^*,p}=d^*\},
\]

\[
\mathcal L_{\mathrm{program}}^{\mathrm{equiv}}
=-\log\sum_{p\in\mathcal E(s^*,d^*)}\beta_{s^*,p}.
\]

이는 exact program-ID CE와 다르다. 같은 source에서 같은 endpoint를 만드는 유효 프로그램들에 총확률을 주면 손실이 작아진다. 유효성 mask는 유지한다. 정답 native program이 이 집합 안에 포함되는지 별도 oracle unit test로 검사한다.

단일 메시지에서 결과가 같다고 다른 메시지에서도 의미가 같은 연산이라는 보장은 없다. 따라서 이 항은 “semantic-equivalence proof”가 아니라 **해당 학습 예제의 execution-equivalence supervision**이다. 정답 목적지로 집합을 만드는 과정은 loss에만 있으며, 평가 forward에서는 사용하지 않는다.

### 8.3 Off에 보조 loss를 주지 않는다는 검증

Off도 인터페이스 호환 때문에 presence/router tensor를 할당하고 예측할 수 있지만, 학습 total에는 endpoint NLL만 들어간다. 해당 보조 parameter의 `.grad`가 `None`이고 optimizer update 전후 값이 같은지 검사한다. “모듈이 메모리에 있다”와 “그 loss로 학습했다”를 혼동하지 않는다.

## 9. Parameter 수, 계산량, 초기화, 수치 재현성

### 9.1 할당 parameter와 학습에 참여하는 parameter

초기화 순서를 맞추고 기존 모델과 공통 tensor를 비교하기 위해 일부 사용하지 않는 모듈도 할당 상태로 유지한다.

- Native router의 top/width gate는 direct route에서 사용하지 않을 수 있다.
- Attribute 모듈은 attribute-only projection과 content-concatenation projection을 둘 다 할당하지만, 한 후보에서 두 쌍을 동시에 사용하지 않는다.
- Attribute의 END/NULL content embedding은 `attr_content`에서, 거리 kernel parameter는 `attr_distance`에서 사용한다.
- Native host의 위치 관련 tensor 중 일부는 현재 선택한 backbone에서 사용하지 않을 수 있다.

`parameters`는 할당된 전체 scalar 수다. Smoke 기록의 `parameters_with_gradient`는 두 optimizer update 중 `.grad is not None`이었던 **parameter tensor 전체의 scalar 수**를 합한 값이다. Embedding의 일부 row만 gradient를 받아도 그 embedding tensor 전체를 센다. 따라서 정확한 “활성 scalar 개수”, nonzero-gradient 개수, FLOPs, peak memory와 같지 않다. Gradient가 존재하는 tensor의 일부 row는 AdamW weight decay의 영향도 받을 수 있다.

기존 Off/Hybrid는 네 backbone 모두 초기 state-dict parity를 검사한다. 새 후보는 같은 이름·shape의 공통 tensor가 같은 초기값인지 검사하고, 추가 모듈은 해당 후보의 고정 seed에서 초기화한다. 서로 다른 모델을 parameter 수까지 완전히 동일하게 만든 탐색이라고 주장하지 않는다.

### 9.2 Padding·END/NULL·checkpoint

입력의 실제 bytes를 바꾸지 않고 값 255의 비관측 right padding만 늘려 다음을 검사한다.

- 최종 확률의 byte 열과 재매핑한 END/NULL 열이 같은가.
- 관측 위치의 source/program 예측이 같은가.
- Padding 목적지와 padding source의 확률이 0인가.
- 모델/variant/backbone/bank를 저장 후 재구성했을 때 최종 확률이 같은가.

이 검사는 단순히 padding 값 0에 우연히 맞는 모델을 통과시키려는 것이 아니다. Nonzero padding도 읽지 않아야 한다.

### 9.3 CUDA scatter의 atomic 합산

Pushforward 및 attribute incoming aggregation은 `scatter_add`를 사용한다. CUDA의 atomic floating-point 덧셈 순서는 실행마다 달라질 수 있으므로, seed를 고정했다고 모든 출력의 bitwise 동일성을 주장하지 않는다.

CUDA 확률·padding·checkpoint 검사의 허용오차는 absolute/relative 각각 \(10^{-5}\)다. CPU 검사는 \(3\times10^{-6}\)를 사용한다. 이는 학습 sample stream이나 초기 parameter를 바꿔도 된다는 뜻이 아니다. 샘플 stream·초기 tensor 동등성은 별도 계약으로 검사한다.

## 10. 해석할 때 지켜야 하는 경계

- 이 실험은 무한히 가능한 모든 수식을 망라한 것이 아니라 **코드에 명시한 30개 후보**를 고정 예산 안에서 비교한다.
- 새로운 Q/K 후보가 기존 hidden-content Q/K를 제거했는지와 encoder QKV까지 제거했는지를 따로 보고한다.
- 구조적 program bank는 공통 prior로 유지한다. 속성 예측 입력에 정답을 주었다고도, 아무 연산 prior가 없다고도 표현하지 않는다.
- 수식 선택은 source-only 내부 검증으로 하고, 해당 outer target의 정답을 보고 후보를 선택하지 않는다. Historical evaluation은 과거에 본 데이터이므로 새로운 blind confirmatory test라고 부르지 않는다.
- Balanced selection score, 일반 field-mean 정답 목적지 확률/NLL/Hit@1, field-discovery F1은 서로 다른 지표다. Off의 미학습 field head를 F1=0으로 강제해 비교하지 않는다.
- `base` 출력이 uniform reference인 attribute/route-only 후보에서 이를 “기존 QK의 성능”으로 해석하지 않는다. Attribute QK 자체의 확률과 native base QK는 별개다.
- 정확한 source·program을 학습 loss에 사용하는 것과 inference에 제공하는 것을 구별한다. Equivalent-program 집합도 loss 전용이다.
- 구현 후보 중 어떤 것이 우수한지, 제거 또는 결합이 실제 이득인지에 대한 판단은 결과·불확실성·대조군을 본 뒤에만 내린다.
