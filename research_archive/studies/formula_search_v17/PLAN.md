> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# v17: 광범위 LAPA 구조 탐색 — 실행 전 고정 계약

## 목적

앞선6수식에 제한하지 않고 사용자가 요청한 구조 변화를 실제로 넓게 비교한다. 수학적으로 무한한 모든 수식을 시험했다는 뜻이 아니라, 아래30개 구체적인 후보와 명시한2단계 탐색/최종 예산을 끝까지 실행한다. 실제 DNS/Modbus/TLS/SMB2만 사용하며 합성 프로토콜이나 외부 트래픽 생성은 하지 않는다. 기존 패키지와v16결과를 보존한다.

## 30개 후보

| 범주 | 후보 |
|---|---|
| 현행/route 대조 | hybrid, route_sink, route_direct, route_joint |
| 속성 기반 새 Q/K | attr_only, attr_content, attr_distance, attr_product, attr_mix |
| 결합/gate | mix_half, mix_learned, mix_entropy, power_learned, weak_product, stopgrad_product |
| 정규화/불확실성 | smooth_route, soft_joint, valid_mass_route |
| encoder·slot | cnn_shared_route, cnn_shared_attr, gru_shared_route, gru_shared_attr, shared_slot_hybrid, shared_slot_route |
| 감독·program | axis_direct, aux_small, aux_large, bilinear_program, execute_score, equivalent_program |

- attr_only는 **예측된 source·program·width/endian/sign/base/mask embedding으로 Q와K를 실제로 만든다.** 기존 hidden-content retrieval QK를 사용하지 않는다. attr_content는 여기에 hidden content도 합친다.
- attr_distance는 관측 bytes에서 모든 후보를 실행한 목적지와 거리 kernel을 사용한다. 정답 목적지에 맞춘 kernel이 아니다.
- attr_product/attr_mix는 속성 QK와 결정론적 실행 route를 각각 곱셈/학습된 convex mixture로 결합한다.
- mix_half는기존 QK와direct의.5혼합, mix_learned는내용/entropy/validmass gate, mix_entropy는예측불확실성 기반고정gate, power_learned는학습된route exponent, weak_product는기존productstrength.1, stopgrad_product는endpoint→route gradient만차단한다.
- smooth_route는epsilon.2, soft_joint는jointtemperature2, valid_mass_route는invalid질량을재정규화로버리지않고uniform sink로남긴다.
- cnn/gru_shared_route는전체QKV가없다. cnn/gru_shared_attr는encoder QKV가없지만 **최종에는새속성QK가있다**. 이를전체QK-free라고부르지않는다. GRU는양방향/packedsequence다.
- 공유slot은64개독립query embedding대신slot수치의공유MLP다. 정답fieldcount는입력하지않는다.
- axis_direct는5축CE평균×4로스케일을사전고정한다. aux_small/large는presence/source/program 가중치.25/4,endpoint1이다. 그외On은네loss가중치1이다.
- execute_score는source표현·연산속성·실제decoded값·validity·실행목적지특징을이용해programlogit을보정한다. 모든후보를실행하며정답연산을받지않는다.
- equivalent_program은학습정답source에서같은정답목적지를만드는모든유효program확률의합을감독한다. exactprogram-ID CE와명확히구분한다. 평가forward에는정답을주지않는다.

## 선택 기준과 단계

현재74개메시지/347필드evaluation은과거에여러번본historicaltest다. 새모델선택은그test또는동일outertarget의dev를쓰지않는다. 표본수/seed가작으므로탐색적결과다.

1. **Screen:**30후보×6고유2-source쌍×1seed(170101),각120update=180모델. TAPE기준이며encoder없는CNN/GRU는별도backbone없음. 각모델은학습하지않은두protocol의development만예측한다.
2. **Promotion:**outertarget별나머지3protocol안의inner2→1점수만사용한다. hybrid,balancedp승자,balancedlog-gain승자,속성계열best를우선확보해정확히4개후보를올린다. 중복시두지표의rank합/고정후보순으로충원한다. 속성계열best도rank합으로고른다. 속성QK를짧은screen만하고끝내지않는장치다.
3. **Refine:**승격후보×해당outer의3쌍×새seed2개(170201/170202),각400update. 동일pair/candidate/seed는재사용하므로최대96모델. 처음부터재학습하며screencheckpoint를선별이어학습하지않는다.
4. **Selection:**outer별refine에서balancedp champion과balancedlog-gain(NLL)champion을별도로고정한다. 두지표순위가충돌하면두결과를모두보고한다. targettest를보고승자를바꾸지않는다.
5. **Final:**3protocoltrain→1protocoltest,600update,새seed3개(170301–170303). **RoPE/CoPE/TAPE/SDPA**별Off,hybrid,pchampion,nllchampion을평가한다. 중복후보/CNN·GRU의backbone중복은재사용한다. 최종최대192모델이다.

최대실행규모468모델,screen21,600step+refine38,400+final115,200step. 실제수는승격/선택중복에따라감소한다. Runtime은실행로그에측정한다. 최종4backbone은TAPE기준source-only로선택한수식의전이검증이지각backbone별로최적화를새로했다는주장이아니다.

지표는각protocol의nonempty relation×INTERIOR/END/NULL층을동등평균한다. balancedp는그층별p(target)평균,balancedlog-gain은log(n+2)−NLL평균이다. 이후innerprotocol/seed를동등평균한다. 실제표에는일반fieldmean p/NLL/Hit@1과referenceEND/NULL/uniform도제공한다. balancedselection과원래확률평균을혼동하지않는다.

## 고정 학습·평가 규칙

- 동일원본train/dev/test,dev는각protocol raw_sha256/message_id순앞24개. labels로대표샘플을선별하지않는다.
- protocol균등→message균등,16querybatch=positive8+negative8;동일seed/sources의샘플stream일치.
- AdamWlr.002/wd.01,gradientclip1,고정마지막checkpoint. Source-devthreshold만사용(.05:.05:.95,동률큰값).
- Off에는endpointNLL만,On에는네가지positiveweightedloss를모두적용. 실제lossweights와weightedcomponents를로그에남긴다.
- rawbyte+observedmask+publicordinalslot만forward입력. 정답source/program은훈련loss또는봉인후진단인덱싱에만사용.
- 기존68개programbank와mask/guard/compound연산prior유지. operator가bank에있다는것과selector가그operator양성학습을받았다는것은별도다.
- attr실행집계는CUDA scatter_add를사용하므로수치적재현허용오차1e-5;bitwise동일을주장하지않는다. 샘플stream/초기가중치는별도검증한다.
- 출처별원래NLL·probability지표와fieldF1은분리한다. Off미학습fieldheadF1은N/A이며0으로치환하지않는다.

## 완료 조건

전후비교가능한모델/학습/평가코드,30후보모든screen상태와승격·탈락근거,refine/최종결과,source/program/route진단,동일seed대비/CI,matplotlib숫자그래프와표,모든단계체크리스트/로그,원본보존검증을남긴다. 우월한수식을찾지못한경우도그대로완료보고하며성공으로바꾸어쓰지않는다.
