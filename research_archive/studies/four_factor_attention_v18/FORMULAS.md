> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# v18: Source·Width·Endian·Base로 직접 만드는 attention

이 문서는 frozen `model18.py`, `executor18.py`, `losses18.py`, `evaluate18.py`, `train18.py`의 실제 수식을 설명한다. 성능 결과나 특정 mode의 우월성을 미리 주장하지 않는다.

## 1. v17과 달라진 핵심

v17의 `attr_only`는 속성을 embedding한 뒤 새 Q/K 내적을 계산했다. v18은 그 방식이 아니다. **모든 encoder layer와 최종 readout에서 source·width·endian·base 네 확률 요인의 곱을 실행 목적지로 전달해 attention 분포를 직접 만든다.**

| 구성 요소 | v18 구현 |
|---|---|
| 표준 \(QK^\top/\sqrt d\), RoPE/CoPE/TAPE/SDPA 점수 | 없음 |
| 속성 embedding → 새 Q/K 내적 | 없음 |
| Source 위치 선택 | Receiver·origin·상대 위치의 비선형 가산 scorer |
| Width/endian/base | 각각 독립된 categorical head |
| Program classifier, learned sign/mask head | 없음 |
| 값의 변환 \(V=HW_V\) | **유지** |
| Output projection, residual, LayerNorm, FFN | 유지 |

따라서 표현은 **“dot-product Q/K similarity를 제거한 four-factor attention”** 또는 **“Q/K-free, V-retained”**가 정확하다. 완전한 QKV-free 모델은 아니다. 가산 source scorer에도 receiver와 origin을 각각 변환하는 학습 linear가 있다. 모든 두 입력 변환 자체를 없앴다는 뜻이 아니라, 이들을 내적하지 않고 비선형 가산 energy로 결합한다는 뜻이다.

## 2. 기호와 입력

한 메시지의 실제 관측 byte 수를 \(n\), 배치 저장 길이를 \(L\), head를 \(h\), receiver를 \(i\), byte source를 \(s\)라 한다. Head 표기는 필요한 곳에서만 생략한다.

- Encoder hidden sequence에는 task token 하나와 \(L\)개의 byte 저장 위치가 있다.
- Task receiver의 수치 좌표는 −1, byte receiver/source의 좌표는 0부터 \(n-1\)이다.
- **Source 후보에는 task token이 들어가지 않는다.** 관측 byte 위치만 source가 된다.
- 목적지는 관측 byte 위치와 END/NULL이다.

\[
\mathcal D=\{0,\ldots,n-1,\mathrm{END},\mathrm{NULL}\},\qquad
U(d)=\frac1{n+2}\quad(d\in\mathcal D).
\]

텐서에서 END/NULL은 열 \(L,L+1\)이다. 실제 메시지 하나의 저장 파일에서는 padding이 없어 열 \(n,n+1\)이다. NULL은 유효한 연산의 특별한 목적지이며, invalid execution, absent field, abstain, uniform sink와 같지 않다.

Forward 입력은 raw `data`, 연속 관측 prefix를 표시하는 `observed`, 공개 ordinal `slots`뿐이다. Protocol ID, 정답 source/width/endian/base/endpoint, 정답 field count는 모델에 입력하지 않는다. Slot은 0–63의 독립 embedding이므로 ordinal-query 의존성은 유지된다.

## 3. 입력 embedding

기본 설정은 hidden dimension 32, head 4개, encoder 2층, FFN dimension 64, 최대 길이 \(M=1024\), slot 64개다.

Byte \(x_s\)의 초기 표현은 byte embedding과 아래 네 위치 특징의 linear projection을 더한 값이다.

\[
f_s=\left[\frac{s}{M},\frac{s}{n},\frac{n-s}{n},
\frac{\log(1+n)}{\log(1+M)}\right],\qquad
H_s^{(0)}=\operatorname{EmbedByte}(x_s)+W_{\mathrm{pos}}f_s.
\]

Task 표현은 학습 task vector와 공개 slot embedding의 합이다. Task와 byte를 concatenate한 뒤 input LayerNorm을 적용하고 padding을 0으로 만든다. 모델은 bidirectional 관측 메시지를 사용하며, causal 또는 streaming 전용 구현이 아니다.

## 4. 첫 번째 요인: source의 비선형 가산 선택

Receiver 표현을 \(r_i\), origin byte 표현을 \(o_s\), receiver 좌표를 \(p_i\)라 한다. Source scorer의 내부 rank는 12다.

\[
g_{is}=\left[\frac{p_i}{M},\frac{s}{M},
\frac{s-p_i}{n},\frac{|s-p_i|}{n}\right].
\]

\[
u_{is}=\tanh\left(W_r r_i+W_o o_s+W_g g_{is}+b_g\right),\qquad
a^h_{is}=v_h^\top u_{is}.
\]

\[
S^h_{is}=\operatorname{softmax}_{s\text{ observed}}a^h_{is}.
\]

`receiver`와 `origin` linear는 bias가 없고, 상대 특징 `relative` linear에는 bias가 있다. 마지막 `energy` linear는 rank 12를 head 4개의 score로 바꾸며 bias가 없다. 식의 \(v_h^\top u\)는 비선형 결합 표현을 scalar로 바꾸는 projection이지, 독립된 query/key 표현 사이의 pairwise dot product가 아니다.

Receiver 축은 16개씩 나눠 계산한다. 이는 메모리 사용을 줄이는 chunking이며 source 후보를 16개로 제한하지 않는다.

## 5. 나머지 세 요인: width·endian·base

각 layer의 origin 표현에서 세 head가 각각 예측한다.

\[
W^h_{sw}=\operatorname{softmax}_{w}\operatorname{WidthHead}(o_s),\qquad
E^h_{se}=\operatorname{softmax}_{e}\operatorname{EndianHead}(o_s),\qquad
B^h_{sb}=\operatorname{softmax}_{b}\operatorname{BaseHead}(o_s).
\]

출력 linear dimension은 각각 \(4H,2H,7H\)다. 이 세 분포는 **head와 origin source가 주어졌을 때** 곱으로 factorize된다. 각 receiver마다 별도의 세 head를 다시 계산하지 않는다. Receiver별 선택은 \(S^h_{is}\)가 담당한다. 각 encoder layer와 최종 readout은 서로 다른 parameter의 four-factor 모듈을 가진다.

\[
W\in\{1,2,3,4\},\qquad E\in\{\mathrm{big},\mathrm{little}\},\qquad B\in\{0,\ldots,6\}.
\]

관측하지 않은 source의 세 분포는 0이다. 관측 source에서는 각 분포 합이 1이다. 별도의 42-way 또는 68-way program logit/softmax는 생성하지 않는다.

## 6. 일곱 base/address-reference operator와 고정 prior

여기서 `base`는 단순한 좌표 기준점보다 넓은 **주소 참조 연산 계열**이다. 읽은 unsigned 정수를 \(z\)라 할 때 안정적인 ID와 의미는 다음과 같다.

| ID | Base operator | 목적지 / 추가 조건 |
|---:|---|---|
| 0 | `field_end_forward` | \(s+w+z\); END 허용 |
| 1 | `packet_absolute` | \(z\) |
| 2 | `field_start_forward` | \(s+z\) |
| 3 | `field_start_backward` | \(s-z\); decoded 값은 unsigned |
| 4 | `previous_offset_plus_length` | 직전 같은 width의 offset + 현재 length; 현재 length가 0이면 NULL |
| 5 | `offset_with_next_length` | 현재 offset; 바로 다음 같은 width의 length가 0이면 NULL |
| 6 | `packet_absolute_masked14` | Width 2, raw value의 `0xc000` marker 검사 후 `0x3fff` mask를 적용한 absolute pointer |

앞의 네 연산은 모든 width에서 가능하다. 두 adjacent-field 연산은 width 2/4에서만 가능하고, masked14는 width 2에서만 가능하다. 따라서 \(4\times2\times7=56\)개 Cartesian cell 중 합법적인 cell은 42개다. Illegal cell은 학습 class를 제거하는 대신 실행 유효성을 0으로 둔다.

| Width | 두 endian을 포함한 합법 cell 수 |
|---:|---:|
| 1 | 8 |
| 2 | 14 |
| 3 | 8 |
| 4 | 12 |

Executor가 내부적으로 사용하는 42개 `Program` 객체는 기존 numerical execution을 재사용하기 위한 고정 목록이다. 그 목록에 categorical score를 학습하는 것이 아니다. Source/width/endian/base의 독립 factor 분포가 56개 조합에 질량을 준다.

DNS mask/guard와 SMB2 companion/NULL 의미는 **사전 제공된 구조 지식**이다. Unseen protocol 평가라고 해서 operator 사전도 전혀 모르는 조건은 아니다. Learned sign/mask 축은 없으며, signed displacement 및 masked-relative 연산은 지원하지 않고 label conversion에서 오류로 처리한다.

Byte 읽기, endian 변환, 범위·marker·companion 검사 결과를 \(T(s,w,e,b;x)\), 유효성을 \(V_{sweb}\in\{0,1\}\)로 쓴다. Invalid target은 저장상 0으로 둘 수 있으나 반드시 validity 0과 함께 사용하므로 byte 0으로 질량을 보내지 않는다. 불완전한 width의 provisional decoded 값은 진단에서 0으로 지워 padding의 영향이 들어오지 않게 한다.

### Width 1의 endian 동치

한 byte에서는 big/little endian의 decoded 값과 실행 결과가 같다. Native label은 보통 big endian을 사용하지만, v18은 이를 식별 가능한 정답 차이로 학습시키지 않는다. Width가 1인 학습 예제에서는 endian 두 후보를 주변화해 그 축의 NLL을 0으로 둔다.

Raw `endian_p`는 canonical native label에 대한 확률로 저장된다. 집계의 `endian_equivalence_p`는 width 1이면 두 endian 확률의 합인 1, 그 외에는 canonical endian 확률이다. 이 두 지표를 혼동하면 안 된다.

## 7. 네 요인의 확률 전달로 attention 만들기

먼저 각 source에서 가능한 width/endian/base 조합의 실행 결과를 모은다.

\[
D^h_{sd}=\sum_{w,e,b}W^h_{sw}E^h_{se}B^h_{sb}V_{sweb}
\mathbf1[T(s,w,e,b;x)=d].
\]

그다음 receiver가 선택한 source 확률을 곱해 전달한다.

\[
R^h_{id}=\sum_sS^h_{is}D^h_{sd},\qquad
m^h_i=\sum_{d\in\mathcal D}R^h_{id}.
\]

코드의 `torch.matmul(source, source_destination)`은 이 **확률 전달**을 계산한다. Hidden-vector similarity를 계산하는 행렬 곱이 아니다. 목적지별 집계에는 `scatter_add`를 사용한다. Executor 인덱스는 이산적이지만, 학습 요인이 부여한 질량에는 gradient가 흐른다.

중요하게도 source별 \(D_s\)를 먼저 각각 합계 1로 만드는 것이 아니다. Source까지 합친 뒤 **receiver/head별 유효 질량 \(m_i^h\)**를 계산한다. 두 mode는 이 질량을 처리하는 방식만 다르다.

### `direct`: 유효 질량을 조건부 정규화

\[
A^h_i=
\begin{cases}
(1-\epsilon)R^h_i/m^h_i+\epsilon U,&m^h_i>0,\\
U,&m^h_i=0,
\end{cases}
\qquad\epsilon=0.02.
\]

유효 질량이 작더라도 양수이면 조건부로 정규화한다. 분모 계산에는 \(10^{-30}\) floor를 사용한다.

### `sink`: invalid 질량을 중립 분포에 남김

\[
A^h_i=(1-\epsilon)R^h_i+left[1-(1-\epsilon)m^h_i\right]U.
\]

이는 \((1-\epsilon)[R^h_i+(1-m^h_i)U]+\epsilon U\)와 같다. 유효 질량이 작으면 uniform 비중이 커진다. Invalid 질량을 NULL에 몰아주지 않는다. 두 mode 모두 관측된 목적지와 END/NULL에서 합계 1이며, padding 목적지에는 0을 준다.

## 8. Encoder: END/NULL self-loop와 V의 유지

Encoder에는 END/NULL에 해당하는 실제 byte value가 없다. 따라서 byte 목적지는 해당 byte의 value를 읽고, END와 NULL의 질량 합은 현재 receiver 자신에게 돌린다.

Task token의 hidden 인덱스를 0, byte \(d\)의 hidden 인덱스를 \(d+1\)이라 하면:

\[
\widetilde A^h_{ik}=
\sum_{d=0}^{n-1}A^h_{id}\mathbf1[k=d+1]
+\left[A^h_i(\mathrm{END})+A^h_i(\mathrm{NULL})\right]\mathbf1[k=i].
\]

Padding receiver의 행은 전부 0이다. Task column을 일반 byte source로 읽는 항은 없고, task receiver의 special mass만 자기 task value에 남는다.

\[
V^h=\operatorname{SplitHeads}(HW_V)^h,\qquad
C=\operatorname{ConcatHeads}(\widetilde A^hV^h).
\]

\[
H'=\operatorname{LN}(H+W_OC),\qquad
H''=\operatorname{LN}(H'+\operatorname{FFN}(H')).
\]

두 residual 단계 이후에도 observed mask를 적용한다. FFN은 linear → GELU → linear다. Learned V와 output projection을 유지한다.

Uniform sink가 encoder에서 완전한 identity/no-op이 되는 것은 아니다. Uniform의 byte 질량은 byte value들을 섞고, END/NULL 질량만 self-loop로 간다. 이런 처리는 학습 가능한 특수 END/NULL value embedding을 사용하는 방식과도 다르다.

최종 readout에서는 encoder task token 하나를 receiver로 사용한다. 더 이상 V를 모으지 않고, END/NULL이 분리된 목적지 분포를 그대로 출력한다.

\[
P_{\mathrm{final}}(d)=\frac1H\sum_h A^h_{\mathrm{task},d}.
\]

## 9. Head별 분포와 저장되는 평균의 차이

실제 attention은 각 head 안에서 네 factor를 곱하고 실행·정규화한 뒤, 마지막에 head를 평균한다. 반면 진단용 출력은 다음과 같은 head 평균이다.

\[
\bar S_s=\frac1H\sum_hS^h_{\mathrm{task},s},\quad
\bar W_{sw}=\frac1H\sum_hW^h_{sw},\quad
\bar E_{se}=\frac1H\sum_hE^h_{se},\quad
\bar B_{sb}=\frac1H\sum_hB^h_{sb}.
\]

일반적으로 \(\overline{SWEB}\ne\bar S\bar W\bar E\bar B\)이고, mode의 정규화도 head별이므로 **진단표의 네 확률을 곱해 final 확률을 재구성할 수 없다.**

Width/endian/base는 각 source 위치에서의 head별 factor를 평균한 값이다. 이를 head mixture에서 source 사건으로 조건화해 head posterior를 다시 계산한 엄밀한 조건부 분포와 동일시해서는 안 된다. 문서·표의 “true source에서의 factor 확률”은 **forward 이후 정답 source 위치를 인덱싱한 head-mean 진단값**이라는 의미다.

`valid_mass`는 \(\bar m=H^{-1}\sum_hm^h_{\mathrm{task}}\)이며, normalization/smoothing 이전 값이다. Slot별 scalar이므로 각각 0–1 범위를 검사하지만 64개 slot 전체 합계가 1일 필요는 없다. `base_p`/집계의 `base_axis_p`는 base operator 축 확률이며, 기존 v17의 목적지 QK 분포인 `base_p`와 다르다.

## 10. 네 loss 그룹: program head 없이 감독하기

학습 objective는 다음 네 그룹의 합이며 가중치는 모두 1이다.

\[
\mathcal L=\mathcal L_{\mathrm{presence}}+\mathcal L_{\mathrm{source}}
+\mathcal L_{\mathrm{attributes}}+\mathcal L_{\mathrm{endpoint}}.
\]

Presence는 positive query의 \(\operatorname{softplus}(-z)\) 평균과 negative query의 \(\operatorname{softplus}(z)\) 평균을 다시 평균한 class-balanced BCE다.

나머지 세 그룹은 **positive field query만** 사용한다.

\[
\mathcal L_{\mathrm{source}}=\operatorname{mean}[-\log\bar S_{s^*}],\qquad
\mathcal L_{\mathrm{endpoint}}=\operatorname{mean}[-\log P_{\mathrm{final}}(d^*)].
\]

\[
\mathcal L_{\mathrm{attributes}}=\operatorname{mean}\left[
-\log\bar W_{s^*,w^*}
-\mathbf1[w^*>1]\log\bar E_{s^*,e^*}
-\log\bar B_{s^*,b^*}
\right].
\]

세 축 NLL을 **합한 뒤 예제 평균**한다. 세 축 평균이나 기존 v17의 program-ID CE가 아니다. Head 평균 확률의 로그를 사용하며, head별 NLL을 평균하는 식과도 다르다. 모든 로그에는 \(10^{-30}\) probability floor를 사용한다.

Width 1의 endian 항을 0으로 하는 것은 동일 실행인 두 endian을 주변화한 \(-\log(\bar E_{\mathrm{big}}+\bar E_{\mathrm{little}})=0\)에 해당한다. Evaluator는 raw canonical endian 확률도 보존한다.

Native program label은 `collate`에서 source와 세 축 label로 바꾸는 호환용 수단일 뿐, 모델의 program class input/output이 아니다. 정답 source는 source/attribute 감독에서만 인덱싱한다. Negative query에는 source/attribute/endpoint 정답을 학습시키지 않으며, negative query를 NULL endpoint로 취급하지 않는다.

각 encoder layer의 factor head에 직접 별도 label loss를 부여하는 것은 아니다. 최종 source/attribute/presence/endpoint objective가 encoder를 통해 역전파된다. Structural test는 endpoint loss만으로도 모든 encoder의 네 factor와 V가 gradient를 받는지 확인한다.

## 11. 추론과 평가 경계

`evaluate18.py`는 메시지마다 모든 공개 slot 64개를 8개씩 계산하고, `diagnostics=False`로 layer의 큰 진단 tensor를 저장하지 않는다. `final`, `source`, `width`, `endian`, `base`, `presence`, `valid_mass`를 NPZ로 저장한 뒤 파일 hash·raw hash·config·executor fingerprint를 봉인한다.

그다음에만 gold field 순서로 slot을 인덱싱해 p(target), NLL, Hit@1과 source/세 축/유효 질량을 계산한다. Presence 확률을 endpoint 확률에 곱하지 않는다. 현재 구현은 field F1이나 threshold 선택을 수행하지 않는다.

CUDA scatter의 floating-point atomic 합산 때문에 수치 검사는 absolute/relative \(10^{-5}\), CPU는 \(3\times10^{-6}\) 허용오차를 사용한다. 동일 seed가 학습 전체의 bitwise 동일성을 뜻하지 않는다. 같은 데이터·sample stream·mode 초기화는 별도로 확인한다.

## 12. 비교로 말할 수 있는 것과 없는 것

네 real protocol의 3→1 holdout, mode 두 개, seed 세 개, 600 update씩 총 24개 새 모델을 실행한다. 두 mode를 모두 보고하며 target 결과를 보고 수식을 재선택하지 않는다.

V17 Off/Hybrid 대조군과 source protocol, raw split, seed, 600 update, sample stream을 맞추지만, 다음은 같지 않다.

- 모든 layer의 attention architecture와 source conditioning.
- Program/sign/mask 축의 제거 및 seven-base operator prior.
- Program-ID CE 대신 세 attribute NLL 합을 사용하는 objective.
- Special endpoint의 encoder 처리, slot/position 표현, parameter 수와 FLOPs.

따라서 성능 차이를 **“QK 제거 하나의 단독 인과효과”**라고 주장할 수 없다. 전체 four-factor 설계의 비교다. Historical test, 작은 seed/capture 수, Modbus/TLS END shortcut, source와 operator exposure 이동도 함께 해석해야 한다. QK를 쓰지 않는 구조를 구현했다는 사실과 그 구조가 더 좋은지에 대한 결론은 구별한다.
