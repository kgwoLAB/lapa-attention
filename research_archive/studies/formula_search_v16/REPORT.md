> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# LAPA 구조·수식 탐색 v16 결과 보고서

## 1. 결론

**QKV를 제거하면 좋아진다는 가설은 이번 실험에서 지지되지 않았다. 기존 LAPA를 대체할 만큼 우수한 새 수식도 확인하지 못했다.** 수식6개를 구현하고72개 내부 검증 모델,27개 최종 모델을 실행했다. 기존 패키지는 변경하지 않았으며 새 수식들은 실험 전용 코드로 남겼다.

내부 검증에서 DNS/TLS/SMB2 평가 fold는 기존 hybrid를, Modbus 평가 fold는 `route_sink`를 선택했다. 그러나 최종 Modbus에서 `route_sink`는 기존 hybrid보다 평균 정답 목적지 확률과 NLL이 모두 나빠졌다. 최종 결과를 보고 선택을 바꾸거나 유리한 seed만 고르지 않았다. 따라서 지금의 권고는 **기존 hybrid를 유지하면서 locator/program 전이 문제를 다음 개선 대상으로 삼는 것**이다. 이것이 기존 hybrid가 모든 구조·데이터·예산에서 최적이라는 뜻은 아니다.

이번 탐색의 Transformer 기준은 **TAPE native-v4 compact**다. RoPE/CoPE/SDPA까지 새 구조를 재학습한 실험으로 해석하면 안 된다. CNN 후보는 encoder부터 QKV를 제거했다. 데이터는 기존 실제 DNS/Modbus/TLS/SMB2 capture이고, 합성 프로토콜은 사용하지 않았다.

## 2. 무엇을 구현했나

현재 LAPA에는 encoder QKV와 최종 목적지 retrieval QK가 따로 있다. 최종 목적지 경로 자체는 확률을 반환하며 별도 V를 곱하지 않는다. 또한 기존 program head도 이미 width/endian/sign/base/mask의5축 점수를 합한다. 그러므로 base/endian/width head를 다시 만드는 것 자체는 새로운 구조가 아니다.

| 후보 | 바꾼 부분 | Encoder QKV | 목적지 QK | 파라미터 |
|---|---|---|---|---:|
| `hybrid` | 기존 head별 QK+log-route 결합 | 유지 | 유지 | 56,649 |
| `route_sink` | 기존 gate/sink route prior를 최종 분포로 사용 | 유지 | 제거 | 54,337 |
| `route_direct` | gate 없이 유효 source×program 질량을 전체 정규화 | 유지 | 제거 | 51,962 |
| `route_axis` | direct와 같은 forward, program을5축 CE 평균으로 감독 | 유지 | 제거 | 51,962 |
| `route_joint` | source+program logits를 유효한 모든 쌍 위에서 공동 softmax | 유지 | 제거 | 51,962 |
| `cnn_joint` | joint 수식에 slot-conditioned dilated CNN encoder 사용 | 제거 | 제거 | 45,298 |

별도 Off 대조군은 TAPE endpoint NLL만 학습했다. 모든 On 후보에는 presence/source/program/endpoint 네 항을 가중치1로 적용했다. Axis 후보의 program 항은5축 CE 평균이라 기존 bank CE와 수치 scale이 다르다. 따라서 해당 대비는 단순히 head 유무만 바꾼 실험이 아니다. 동일 step 수를 사용했으나 파라미터 수/FLOPs까지 같게 맞춘 것은 아니다.

공통적으로68개 기존 프로그램 bank와 결정론적 실행기를 유지했다. mask/guard, signed 여부, SMB2 인접 필드 연산 같은 사전 구조 지식도 그대로다. 모델 입력에는 raw bytes, padding mask, 공개 ordinal slot만 들어가며 프로토콜명·정답 source·정답 program·정답 destination은 들어가지 않는다.

전체 수식과 모듈 설명: [FORMULAS.md](FORMULAS.md). 구현: [models16.py](models16.py), [losses16.py](losses16.py).

## 3. 핵심 수식

Source 확률을 \(\alpha_s\), source 조건부 program 확률을 \(\beta_{sp}\), 실행 유효성을 \(V_{sp}\), 실행 목적지를 \(T(s,p;x)\), 관측 위치+END+NULL의 균등 분포를 \(U_d\)라 두었다.

Gate-free direct 후보는 다음과 같다.

\[
J_{sp}=\frac{\alpha_s\beta_{sp}V_{sp}}{\sum_{u,r}\alpha_u\beta_{ur}V_{ur}},\qquad
P(d)=(1-\epsilon)\sum_{s,p}J_{sp}\mathbf1[T(s,p;x)=d]+\epsilon U_d.
\]

Joint 후보는 \(a_s\)가 source logit, \(b_{sp}\)가5축 program logit의 합일 때 다음처럼 바꾼다.

\[
J_{sp}=\operatorname{softmax}_{(s,p):V_{sp}=1}(a_s+b_{sp}).
\]

두 수식의 차이는 per-source program 분모다. Joint에서는 program evidence가 source posterior에도 영향을 주며, 단순히 source와 program을 독립적으로 잘 맞추면 된다는 구조가 아니다. 두 후보 모두 \(\epsilon=0.02\)다. 유효한 쌍이 없으면 uniform으로 돌아가며 NULL로 처리하지 않는다.

기존 hybrid는 route prior를 \(R_d\), head별 목적지 logit을 \(z_{hd}\)라고 하면 다음과 같다.

\[
P(d)=\frac1H\sum_h\operatorname{softmax}_d\left(z_{hd}+\log\frac{R_d}{U_d}\right).
\]

즉 head마다 정규화한 후 평균한다. 평균 base 확률과 route 확률을 한 번 곱하고 정규화한 식으로 일반화하면 정확하지 않다. `route_sink`는 이 최종 결합을 제거하고 \(P(d)=R_d\)만 사용한다.

## 4. 평가 절차와 실행 규모

| 단계 | 조건 | 모델 수 | 모델당 update |
|---|---|---:|---:|
| Smoke | 실제 TRAIN8개 메시지, CPU/GPU11종 검증 | 7종 각각 검증 | 3 |
| 내부 탐색 | 2-protocol train, 제외된 protocol development | 72 | 250 |
| 최종 | 3-protocol train, 남은1개 protocol test | 27 | 600 |

본 학습은 총99개 모델/34,200 update다. 탐색 seed2개와 최종 fresh seed3개를 분리했다.6개 고유 source pair를 재사용해 각 outer target 안에서3개 inner2→1 검증을 수행했다. Development는 프로토콜별 raw hash 순서32개 메시지를 사전 고정했다.

수식 선택 지표는 각 validation protocol의 relation×{INTERIOR,END,NULL}를 동등하게 평균한 \(\log(n+2)-\mathrm{NLL}\), 이후 protocol/seed 동등 평균이다. 해당 outer target의 dev/test는 그 target의 선택에 쓰지 않았다. 선택을 봉인한 뒤에만 test 추론을 시작했다.

최종 평가는74개 메시지/347개 필드다. DNS266필드, Modbus6, TLS15, SMB2 60이다. 메시지마다64개 slot 전체를 먼저 예측·봉인하고 이후 정답과 비교했다. Threshold는 source development의 typed field F1로만 선택했다. 샘플링은 protocol균등→message균등, batch16=양성8+음성8, AdamW lr.002/wd.01, gradient clip1이다.

독립 감사는99개 모델,7,668개 파일 해시,6,510개 확률 파일,186개 예측 봉인,24개 재생성한 학습 스트림을 검증했다. Off/Hybrid12쌍의 초기 가중치와 학습 스트림이 동일했고, 기존 LAPA 소스48개 파일도 바뀌지 않았다. [INDEPENDENT_AUDIT.json](INDEPENDENT_AUDIT.json)에 근거가 있다.

## 5. 내부 검증에서 선택된 수식

| 최종 held-out target | 해당 target을 제외한 내부 검증의 선택 | 선택 점수(nat) |
|---|---|---:|
| DNS | 기존 `hybrid` | 1.4687 |
| Modbus | `route_sink` | 0.0965 |
| TLS | 기존 `hybrid` | 0.5175 |
| SMB2 | 기존 `hybrid` | 1.7633 |

이 점수는 해당 target의 test 결과가 아니다. 예를 들어 DNS 행은 Modbus/TLS/SMB2 내부에서 얻은 점수다. 따라서 “DNS에서 hybrid가1.4687을 얻었다”고 서술하면 틀린다.

Direct의 일부 장점도 있었다. **탐색 단계의2→DNS development**에서 pointer 정답 확률은 hybrid0.00777 대 direct0.12652였다. 그러나 DNS label은0.01434 대0.00322, RDLENGTH-END는0.01052 대0.00038로 반대 방향이었다. 일부 pointer 개선을 모든 관계의 개선으로 확대할 수 없다. 이 숫자는3→DNS 최종 test의 direct 성능이 아니다.

CNN은 학습 loss가 낮아졌는데도 전이 점수가 낮았다. Direct/CNN은 틀린 목적지에 확률을 과도하게 몰아 정답 확률을 smoothing floor 근처로 보내는 사례도 관측됐다. 수식만으로 강제 정규화하면 신뢰할 수 없는 source/program 선택을 오히려 증폭할 수 있다는 해석과 일치한다. 이는 관측에 대한 해석이지 분리된 인과 증명은 아니다. 자세한 탐색 수치는 [SEARCH_INTERPRETATION.md](SEARCH_INTERPRETATION.md)에 있다.

## 6. 최종 정답 목적지 확률

각 값은3개 seed 평균이다. Selected는 target별 내부 검증이 선택한 모델이며, DNS/TLS/SMB2에서는 기존 hybrid와 동일한 실행을 재사용한다.

| 관계 | 필드 수 | TAPE Off | 기존 TAPE+LAPA | 사전 선택된 수식 |
|---|---:|---:|---:|---:|
| DNS length | 230 | 0.037698 | 0.012922 | 0.012922 |
| DNS pointer | 36 | 0.000022 | 0.009231 | 0.009231 |
| Modbus length | 6 | 0.701712 | 0.524533 | **0.252033** |
| TLS length | 15 | 0.872451 | 0.459035 | 0.459035 |
| SMB2 length | 30 | 0.071690 | 0.039924 | 0.039924 |
| SMB2 offset | 30 | 0.000133 | 0.003396 | 0.003396 |

Modbus에서 route-only의 평균 변화는 \(\Delta p=-0.272500\), NLL 개선량(기존−새 모델)은−1.531219nat였다.3-seed paired95% t-CI는 각각[−1.438719,0.893720], [−5.683393,2.620955]다. 매우 넓고0을 포함하므로 모집단 차이나 확정적인 우열로 해석하지 않는다. t-CI를 물리적 확률 범위에 강제로 잘라 표시하지 않았다.

4개 프로토콜을 동등 평균한 전체 필드 p(target)는 Off0.410668, 기존hybrid0.254413, Selected0.186288이다. 반면 NLL은 Off8.885539, hybrid3.632921, Selected4.015726이다. **평균 정답 확률과 NLL의 순위가 다르다.** 일부 잘 맞춘 사례의 높은 확률은 p 평균을 올리지만, 많은 정답에 거의0의 확률을 주면 NLL은 크게 나빠진다. 따라서 p만으로 가장 좋은 수식을 정하지 않았다.

## 7. QKV보다 먼저 확인해야 할 병목

### Source·program 선택 자체가 약하다

기존 hybrid의 모든 관계를 합친 protocol별 stage 평균은 다음과 같다.

| Held-out protocol | Source p | Program p given true source | Route p(target) | Final p(target) |
|---|---:|---:|---:|---:|
| DNS | 0.01350 | 0.00112 | 0.01350 | 0.01242 |
| Modbus | 0.05841 | 0.07919 | 0.09479 | 0.52453 |
| TLS | 0.08626 | 0.58030 | 0.09204 | 0.45903 |
| SMB2 | 0.00370 | 0.00252 | 0.00519 | 0.02166 |

True-source Program은 정답 source를 입력했다는 뜻이 아니다. raw-only forward를 끝낸 뒤 그 위치의 program 확률을 인덱싱한 진단이다. DNS/SMB2는 이 조건에서도 낮다. 최종 QK가 이미 정확한 route를 망치는 문제만으로 현재 실패를 설명하기 어렵다.

위 표에서 Modbus/TLS의 Final이 Route보다 높은 것은 같은 hybrid checkpoint의 결합 전후 진단이다. 새 route-only를 다시 학습한 인과 실험과 동일하지 않다. 또한 두 프로토콜은 현재 test length가 전부END여서 높은 Final이 주소 계산 성공의 증거가 되지 않는다.

### Ordinal query 및 프로그램 노출 이동

- DNS를 제외한 source는 positive slot0–3만 제공한다. DNS test266개 중119개는 slot4이상이다. 그 slot들은 source 학습에서 양성이 아니라 음성 presence supervision만 받는다.
- 다만 DNS에서 slot0–3과 slot4이상의 hybrid p가 모두약0.0124로 낮았다. 따라서 slot 문제가 유일한 원인이라고도 할 수 없다.
- DNS pointer mask와 SMB2 compound operation은 해당 protocol held-out에서 positive program 감독이 없다. Bank에 존재한다는 것과 선택법이 학습됐다는 것은 다르다.
- source/program이 불확실한데 valid 후보 안에서 확률을 모두 재분배하면 정답이 아닌 유효한 프로그램으로 확신이 이동할 수 있다.

### Field discovery는 별도 과제

최종 typed exact multiset field F1은 DNS/Modbus/SMB2에서 On 모두0, TLS의 기존/Selected 전체 semantic F1은0.0934였다. TLS LENGTH만 분리한 F1은0.0957이다. Off는 auxiliary discovery head를 학습하지 않아 F1을N/A로 표기했다. 높은 endpoint p와 필드 발견 성공을 같은 수치처럼 주장하면 안 된다.

## 8. 지금 유지할 구조와 다음 개선 순서

**기존 hybrid를 기본값으로 유지한다.** 이번 테스트를 본 뒤 Selected 행을 hybrid로 바꾸지는 않았다. 배포 기본값을 변경하지 않는다는 판단과 사전 선택 절차의 실패 기록을 구분했다.

다음 연구는 다음 순서가 타당하다. 아래는 아직 구현·검증된 개선 결과가 아니다.

1. **Ordinal slot 의존성 완화:** 공유 byte-wise source locator 또는 set prediction으로 바꿔, source에서 음성만 학습한 query가 target 양성이 되는 문제를 별도 대조한다.
2. **프로그램 조합 전이:** known operator prior와 학습된 selector를 분리하고, width/endian/base 조합 holdout 및 mask/compound operation 노출을 구분한다. 단순 축 head 추가는 기존에도 있던 기능이다.
3. **불확실성 기반 결합:** source/program entropy·유효 질량을 이용해 route를 과도하게 확신하지 않는 결합을 검토한다. 예컨대 convex mixture도 후보가 될 수 있지만, 이번 결과로 그 수식의 우수성을 주장할 수 없다.

새 수식은 새 source-only 선택 계약에서 평가하고, 충분히 좋은 후보만4개 backbone 및 추가 독립 capture로 확장한다. 최종 test 결과를 다시 탐색 지표로 사용하지 않는다.

## 9. 한계와 사용 가능한 주장

- 실제 packet corpus이지만 최종 메시지 수74개로 작으며 Modbus6필드, DNS TXT1필드다.
- 같은 test를 이전 연구에서 이미 확인했으므로 fresh confirmatory test가 아니다.
- 최종3개 seed의 CI는 seed 변동만 나타낸다. capture/protocol 모집단 불확실성을 반영하지 않는다.
- train/dev는 raw·group이 분리되지만 capture2개를 공유한다. 최종 test는 train/dev와 raw·group·capture 모두 분리된다.
- 고정68개 program bank, compact TAPE,32개 dev message 제한,250/600 update, fixed ordinal query에 대한 탐색 결과다. QKV-free 일반 구조 전체의 가능성을 부정하지 않는다.
- 후보별 parameter/연산량과 program loss scale이 다르다. “QKV 유무만의 효과”라고 전체6후보 대비를 부르면 안 된다.

사용 가능한 결론: **“기존 LAPA에서 최종 QK 제거, gate-free 정규화, 공동 source-program 정규화, CNN 기반 완전 QKV 제거를 비교했으나, 제한된 real-protocol3→1 평가에서 대체 구조의 일관된 우위를 확인하지 못했다. 일부 pointer development 개선은 length 성능 저하와 동반됐으며, source/program 선택과 query-distribution shift가 중요한 후속 진단 대상이다.”**

## 10. 산출물

- [TABLES.md](TABLES.md):p/NLL/Hit@1/CI/F1 및 모든 세부 표.
- [figures/02_main_p_true.png](figures/02_main_p_true.png):대표 숫자 비교 그래프.
- [figures/03_relation_p_true.png](figures/03_relation_p_true.png):DNS label/RDLENGTH/pointer 및 SMB2 필드별 그래프.
- `output/pdf/lapa_formula_search_results.pdf`:8페이지 Matplotlib 그래프 묶음. PNG/SVG 원본도 보관.
- [FORMULAS.md](FORMULAS.md), [REPRODUCTION.md](REPRODUCTION.md):수식·코드·checkpoint 사용법.
- [MASTER_CHECKLIST.md](MASTER_CHECKLIST.md), [WORK_LOG.md](WORK_LOG.md), `EVENTS.jsonl`:단계별 완료 기록.
- `SUMMARY.json`, `SELECTION.json`, `INDEPENDENT_AUDIT.json`:수치·선택·검증 근거.

표형 그래프240칸(수치234개와 Off field-head 미학습 N/A6개) 및 paired effect plot을 원 수치에서 생성했다. PDF는 전체8페이지를 렌더링해 시각 검증하며, 최종 검증 상태는 `COMPLETION.json`에 기록한다.
