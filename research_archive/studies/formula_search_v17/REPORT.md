> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# LAPA 구조 탐색 v17 — 400개 모델 실행 결과

## 1. 결론부터

요청한 **예측 source·program·base·endian·width 등을 실제 새 Q/K로 만드는 모델을 구현하고 학습했다.** 이것만이 아니라 최종 QK 제거, encoder QKV 제거, CNN/GRU, source–program 상호작용, 실행 특징, 공유 ordinal query, gate·결합·normalization, 보조 loss 비중 및 program 동치 감독까지 30개 후보를 비교했다.

Screen 180개 + refine 64개 + final 156개 = **400개 고유 모델, 140,800 update를 실패·재시도 없이 완료**했다. GPU 큐 전체 실행 시간은 55.305분이었다. 구현·smoke·감사·문서·시각 검수 시간은 이 시간에 포함되지 않는다.

그러나 **“QK를 제거하거나 속성으로 바꾸면 전반적으로 더 좋다”는 결론은 얻지 못했다.**

- 속성+content Q/K는 SMB2 length 등 일부 정답 확률을 높였다.
- SMB2 offset은 해결하지 못했다. 선택된 attribute 모델의 offset Hit@1은 네 backbone 모두 0이다.
- SDPA의 확률 기준 선택 정책은 기존 Hybrid보다 macro 확률이 0.0634 높았지만 NLL은 나빠졌다.
- 네 backbone 모두에서 두 선택 정책의 최종 macro NLL은 기존 Hybrid보다 높았다.
- DNS와 SMB2는 source 및 program 선택 확률 자체가 매우 낮다. 이 조건에서 readout QK만의 문제라고 단정할 근거는 없다.

따라서 기존 패키지의 기본 모델을 새 수식으로 교체하지 않았다. **v17은 분리된 연구 구현**으로 보존한다. 수학적으로 가능한 모든 수식을 시험했다거나, 30개 모두를 모든 backbone의 최종 평가까지 실행했다는 뜻은 아니다.

## 2. 무엇을 구현했나

| 비교 범주 | 실제 후보 |
|---|---|
| 기존 및 목적지 QK 제거 | hybrid, route_sink, route_direct, route_joint |
| 예측 속성 기반 새 Q/K | attr_only, attr_content, attr_distance, attr_product, attr_mix |
| QK/route 결합·gate | mix_half, mix_learned, mix_entropy, power_learned, weak_product, stopgrad_product |
| 유효 질량·확신도 처리 | smooth_route, soft_joint, valid_mass_route |
| Encoder·ordinal query | cnn_shared_route, cnn_shared_attr, gru_shared_route, gru_shared_attr, shared_slot_hybrid, shared_slot_route |
| 연산 selector·감독 | axis_direct, aux_small, aux_large, bilinear_program, execute_score, equivalent_program |

별도로 기존 목적지 attention만 쓰는 `off`를 최종 대조군에 포함했다.

### 사용자가 제안한 속성 Q/K는 어떻게 들어갔나

기본 예측은 source 확률 \(\alpha_s\), source별 program 확률 \(\beta_{sp}\), 그리고 **width/endian/sign/base/mask의 다섯 축**이다. 정답 source나 정답 속성을 forward 입력으로 주지 않는다.

- Query: 예측 확률로 가중한 source 위치·program·다섯 속성 embedding, entropy, 유효 실행 질량을 결합한다.
- Key: 각 목적지로 실제 실행되어 들어오는 source/program의 예측 질량과 embedding, 목적지 위치·END/NULL 특징을 결합한다.
- `attr_only`: 이 속성 표현으로 새로운 Q/K projection을 만든다.
- `attr_content`: 위 속성 표현에 encoder의 task/byte hidden content를 추가한 별도 Q/K projection이다.

\[
Q^{AC}=W_Q\operatorname{LN}([x_Q;t]),\quad
K^{AC}_d=W_K\operatorname{LN}([x_K(d);h_d]),\quad
p(d)=\frac1H\sum_h\operatorname{softmax}_d\!\left(\frac{Q_h^{AC}\cdot K_{hd}^{AC}}{\sqrt{d_h}}\right).
\]

이때 기존 native retrieval Q/K와 special-endpoint logit head를 제거한다. 다만 Transformer encoder의 QKV는 남는다. **모델 전체가 QKV-free인 후보는 `cnn_shared_route`, `gru_shared_route`**이고, CNN/GRU의 `_attr` 후보는 encoder만 QKV-free이며 마지막에는 새 attribute Q/K가 있다.

정확한 30개 수식과 코드 대응, kernel·gate·program 감독의 정의는 [FORMULAS.md](FORMULAS.md)에 정리했다.

## 3. 선택과 최종 평가를 어떻게 분리했나

실제 DNS·Modbus·TLS·SMB2만 사용했다. 합성 프로토콜은 사용하지 않았다.

| 단계 | 학습·평가 방식 | Seed / update | 고유 모델 수 |
|---|---|---|---:|
| Screen | 30개 후보 × 6개 2-source 쌍; 나머지 protocol의 development 예측 | 170101 / 120 | 180 |
| Refine | Outer target별 4개 승격 후보; 그 target을 제외한 내부 2→1 검증 | 170201, 170202 / 400 | 64 |
| Final | 3개 protocol train → 나머지 1개 protocol evaluation; 4개 backbone | 170301–170303 / 600 | 156 |

Screen/refine은 TAPE 기준이며, CNN/GRU에는 별도 Transformer backbone이 없다. 최종 평가는 TAPE 기준 source-only로 선택한 수식이 RoPE·CoPE·TAPE·SDPA에서 어떻게 작동하는지 보는 실험이다. **각 backbone에 최적인 수식을 별도로 탐색한 것은 아니다.**

각 outer target의 선택에 그 target의 development/evaluation은 쓰지 않았다. 다만 여러 outer fold가 같은 screen 실행을 재사용하므로, 저장된 validation 결과 전부가 한 target의 선택 근거인 것은 아니다. 선택 코드는 해당 target이 들어간 근거를 제외하며 감사도 이를 검증했다.

선택 지표는 protocol 내 nonempty relation×INTERIOR/END/NULL 층을 동등 평균한 `balanced_p`와 `balanced_log_gain`이다. 후자는 \(\log(n+2)-\mathrm{NLL}\)이므로 같은 검증 자료에서 stratified NLL 최소화와 같다. 최종 그림에는 원래 요청한 **필드별 정답 목적지 확률의 평균**을 사용한다. 선택 점수와 최종 단순 평균은 다르다.

| Held-out target | 확률 기준 선택 | NLL 기준 선택 |
|---|---|---|
| DNS | aux_small | aux_small |
| Modbus | mix_entropy | hybrid |
| TLS | attr_content | shared_slot_hybrid |
| SMB2 | attr_content | attr_content |

`P-selected`와 `NLL-selected`는 위의 **target별 선택 정책**이다. 각각 하나의 고정 architecture를 뜻하지 않고, 최종 결과를 본 oracle 선택도 아니다. “NLL-selected”라고 적혀 있어도 최종 NLL이 가장 좋다는 뜻은 아니다.

### Loss와 초기화

- Off: 실제 존재하는 field slot의 목적지 NLL만 사용한다. Presence/source/program head는 학습되지 않으며 변경되지 않았음을 검증했다.
- 일반 On: presence/source/program/endpoint 네 loss의 가중치는 모두 1이다.
- `aux_small`: 앞의 세 보조 loss는 각각 0.25, endpoint는 1이다. `aux_large`는 각각 4와 1이다. 네 loss를 없앤 것이 아니다.
- `axis_direct`, `equivalent_program`은 program 감독의 정의를 명시적으로 바꾼 별도 후보다.
- 매 update는 positive 8개 + negative 8개다. Negative는 On의 presence loss에만 기여한다. **없는 field를 NULL 목적지로 학습시키지 않는다.**
- 동일 source/seed의 샘플 순서와 공유 native 초기 tensor를 맞췄다. Off/Hybrid 48개 초기화 쌍을 확인했다. 모든 모델의 parameter 수가 동일하다는 의미는 아니다.

## 4. 전체 결과: 확률과 NLL의 결론이 다르다

아래 값은 `평균 p(target) / 평균 NLL(nat)`이다. Protocol 안에서는 field 평균, protocol 사이에서는 네 protocol 동등 평균이다. 세 final seed의 평균이다.

| Backbone | Off | 기존 Hybrid | P-selected | NLL-selected |
|---|---:|---:|---:|---:|
| RoPE | 0.3951 / 5.5322 | 0.4208 / 3.0632 | 0.4352 / 3.8754 | 0.4266 / 3.8756 |
| CoPE | 0.3470 / 4.4288 | 0.4563 / 3.5259 | 0.4486 / 4.1736 | 0.4637 / 4.1465 |
| TAPE | 0.3928 / 7.6970 | 0.4360 / 3.0353 | 0.4245 / 4.0738 | 0.4127 / 4.0436 |
| SDPA | 0.3811 / 4.6658 | 0.4145 / 3.5094 | 0.4779 / 4.2583 | 0.4339 / 4.3521 |

SDPA의 P-selected는 Hybrid 대비 확률 **+0.0634 [0.0494, 0.0774]**, 즉 +6.34 percentage point다. 하지만 NLL은 3.5094→4.2583으로 악화했다. 일부 정답에 큰 확률을 주더라도 다른 정답에 지나치게 작은 확률을 주면 평균 확률과 평균 NLL이 반대 방향으로 움직일 수 있다.

RoPE의 P-selected NLL gain은 **−0.8121 [−1.0119, −0.6123] nat**다. 여기서 gain은 `Hybrid NLL − selected NLL`이므로 음수는 악화다. 다른 backbone도 평균 NLL은 악화 방향이지만, 모든 paired CI가 0을 제외하는 것은 아니다.

기존 Hybrid 자체는 Off보다 네 backbone 모두 평균 확률이 높고 NLL이 낮다. 이는 routing과 보조 감독을 포함한 전체 구성의 효과다. 두 모델 모두 QK를 사용하고 loss도 다르므로, **이 비교만으로 QK 경로 자체의 인과 기여를 분리할 수는 없다.** QK 제거·교체의 근거는 해당 후보의 별도 비교에서 판단해야 하며, 이번 탐색으로 QK의 보편적 우월성이나 유해성을 증명하지는 못했다.

**CI 주의:** 표의 대괄호는 세 training seed에 대한 Student-t 95% 구간(df=2)이다. Capture·packet·새 protocol의 모집단 불확실성, 다중 비교 보정, 사후 선택 불확실성을 포함하지 않는다. 구간을 0–1로 잘라 보이지 않았다.

## 5. Protocol·연산별로 무엇이 좋아졌나

### TAPE의 상세 비교

| 평가 cohort | N | Off p | Hybrid p | P-selected p | 선택 수식 |
|---|---:|---:|---:|---:|---|
| DNS length | 230 | 0.039682 | 0.017513 | 0.017897 | aux_small |
| DNS pointer | 36 | 0.000134 | 0.005098 | 0.007041 | aux_small |
| Modbus length | 6 | 0.522511 | 0.816296 | 0.725708 | mix_entropy |
| TLS length | 15 | 0.984566 | 0.850640 | 0.881048 | attr_content |
| SMB2 length | 30 | 0.058955 | 0.119859 | 0.149438 | attr_content |
| SMB2 offset | 30 | 0.000494 | 0.002677 | 0.000438 | attr_content |

### 새 attribute Q/K의 효과와 실패

SMB2에서 `attr_content`는 네 backbone 모두 전체 평균 확률을 높였다. 하지만 증가가 주로 length에 집중됐다. TAPE에서:

- NameLength: 0.0209→0.0739.
- ContextLength: 0.2188→0.2249.
- NameOffset: 0.004081→약 0.000010.
- ContextOffset: 0.001273→0.000866.

SMB2 전체 NLL은 TAPE에서 **5.7042→9.0201**, SDPA에서 **7.7875→10.5232**로 나빠졌다. 선택 attribute의 offset Hit@1과 SMB2 field F1은 네 backbone 모두 0이다. 따라서 “SMB2 address 해석에 성공했다”는 결론은 불가능하다.

TLS의 attribute 확률은 높지만 평가 15개가 모두 END다. Modbus 6개도 모두 END여서 **Always END만으로 p=1, Hit@1=1**이다. 이 수치만으로 바이트에 인코딩된 length 연산을 이해했다고 입증할 수 없다. SDPA Modbus의 `mix_entropy`는 p 0.6448→0.8246으로 좋아졌지만 이 제한을 동일하게 받는다.

### DNS RDLENGTH도 별도 확인했다

DNS length를 하나로만 묶지 않고 label 164개, root terminator 40개, RDLENGTH 25개, TXT length 1개로 분해했다. Pointer는 별도 36개다.

TAPE의 RDLENGTH p는 Hybrid 0.0534→aux_small 0.0664, RoPE는 0.0493→0.1191이다. 하지만 Off는 각각 0.2725, 0.3967로 더 높다. DNS label의 선택 모델 확률은 여전히 낮다. TXT length는 표본 1개이므로 강한 독립 증거가 아니다.

## 6. Source와 program의 문제가 남아 있다

TAPE의 진단 값이다. `Program p`는 정답 source를 **봉인 이후 인덱싱**해 읽은 labeled-program 확률이다. 정답 source를 모델 입력으로 제공한 실험이 아니다.

| Target | 모델 | Source p | Program p | Final p |
|---|---|---:|---:|---:|
| DNS | Hybrid | 0.009212 | 0.000168 | 0.015833 |
| DNS | aux_small | 0.005759 | 0.000734 | 0.016427 |
| SMB2 | Hybrid | 0.002683 | 0.006154 | 0.061268 |
| SMB2 | attr_content | 0.001861 | 0.006022 | 0.074938 |
| TLS | Hybrid | 0.577863 | 0.931058 | 0.850640 |
| TLS | attr_content | 0.443241 | 0.808475 | 0.881048 |

Final p가 높아져도 정확한 source/program 선택이 함께 좋아지는 것은 아니다. 특히 attribute+content readout은 낮은 source/program 정확도에도 일부 END 목적지에 높은 확률을 줄 수 있다. 이 증가를 executor 개선과 같은 뜻으로 쓰면 안 된다. 반대로 동치 program이 같은 목적지를 만들 수 있으므로 labeled-program 정확도만으로 모든 실행 능력을 평가해서도 안 된다.

Field F1은 목적지 확률과 별개의 과제다. 이번 최종 평가에서 DNS·Modbus·SMB2의 학습된 On 모델은 정확한 typed-span F1이 모두 0이고, TLS만 비영점이다. Off의 field head는 의도적으로 학습하지 않았으므로 F1은 **N/A이지 0이 아니다**.

## 7. 결과를 해석할 때 반드시 공개할 제한

1. 최종 평가는 **74개 메시지 / 347개 field**뿐이다. TLS·SMB2는 각각 group 1개, capture 1개다. 과거 실험에서 이미 본 historical test이므로 blind confirmatory 결과가 아니다.
2. Final target은 source train/development와 raw/group/capture가 분리된다. 그러나 train/development 사이에는 capture 2개가 겹치며, DNS↔TLS의 일부 내부 검증도 같은 capture를 공유한다.
3. DNS holdout에서는 평가 266개 중 **119개가 positive 학습이 없는 slot 4–38**에 있다. 그 slot들은 On의 negative presence 예시를 받았지만 positive source/program/endpoint 감독은 받지 않았다.
4. DNS 241/266개는 정답 program ID의 source-positive 예제가 없다. SMB2는 60/60개가 그렇고 little endian, width 4, 두 compound base의 양성 label도 없다. 다만 **DNS RDLENGTH의 program은 실제 source-positive 학습을 받았다**. 모든 실패를 “연산을 본 적 없음”으로 설명할 수는 없다.
5. 모든 routed 모델은 동일한 68개 program bank와 DNS pointer mask/guard·SMB2 인접 offset/length 실행 규칙을 사전에 안다. 알려지지 않은 연산 규칙 자체를 무에서 추론한 실험이 아니다.
6. 30개 후보는 모두 short screen을 받았고, 승격 후보만 refine, 최종 선택 후보만 final을 받았다. QKV-free 후보의 보편적 실패나 전역 최적 수식을 주장하지 않는다.
7. 작은 학습 예산, 1-seed screen, 2-seed refine, 3-seed final 및 제한된 operator/slot 노출이 동시에 작용한다. 현재 결과만으로 각 원인의 인과 기여를 완전히 분리하지는 못한다.

세부 데이터 수·split 교집합·실제 positive/negative draw와 program 노출은 [DATA_LIMITATIONS.md](DATA_LIMITATIONS.md)에 있다.

## 8. 현재 결정과 남는 연구 방향

**이번 실험에서 새로운 범용 기본 수식으로 교체할 근거는 확보하지 못했다.** 기존 Hybrid를 유지하고, attribute+content와 entropy mixture를 목적별 후속 후보로 남기는 것이 현재 근거에 맞다.

다음 단계가 필요하다면, 이번 test에 맞춰 수식을 추가 선택하기보다 별도의 고정 실험으로 다음을 분리해야 한다.

- Protocol shift와 operator/slot-positive coverage shift를 분리한다.
- END만 맞히는 shortcut을 피할 수 있도록 내부 목적지가 충분한 별도 real-capture 평가를 마련한다.
- 정확한 source 선택, program 선택, 목적지 분포의 확신도 문제를 각각 비교한다.
- 최종적으로 한 수식을 고른다면 새로운 capture·protocol lineage에서 재확인한다.

이는 향후 권고이지, 현재 완료된 400개 실험에 추가 실행한 것처럼 계산하지 않았다.

## 9. 산출물과 검증

- [전체 숫자 그래프](figures/04_final_numeric_p.png): 네 backbone × Off/Hybrid/두 선택 정책, 여섯 protocol-semantic 열.
- [NLL 그래프](figures/06_final_numeric_nll.png), [DNS 세부 관계](figures/07_dns_relations_p.png), [SMB2 세부 관계](figures/08_smb2_relations_p.png), [paired CI](figures/09_paired_macro_gains.png).
- `output/pdf/LAPA_formula_search_v17.pdf`: 12페이지 전체 그림집. 각 그림은 PNG/PDF/SVG로도 보존했다.
- [TABLES.md](TABLES.md): 전체 screen/refine/final 수치와 CI, stage, F1, sanity references.
- [논문용 압축 표 안내](tables/README.md): 16×6 p/Hit@1/NLL LaTeX 표 3개 및 상세 보충 표 14개. 압축 표 288개 셀과 문법 구조를 검증했다. TeX compiler가 없어 LaTeX 컴파일·지면 배치까지 검증한 것은 아니다.
- [FORMULAS.md](FORMULAS.md), [REPRODUCTION.md](REPRODUCTION.md), [MASTER_CHECKLIST.md](MASTER_CHECKLIST.md), [WORK_LOG.md](WORK_LOG.md).

최종 독립 감사는 **400개 모델 / 26,920개 파일 해시 / 30개 샘플 스트림 재생 / 456개 선택 근거 / 752개 prediction seal / 2,844개 최종 NPZ / 12,672개 endpoint 진단**을 확인하고 PASS했다. 별도 그림 감사는 12개 그림·36개 파일과 모든 숫자·PDF 페이지를 검증했다. PDF는 전체 페이지를 직접 렌더링해 확인했고, 마지막 CI 그림의 설명문 겹침을 수정했다.

재현용 checkpoint, 실제 weighted loss curve, source-only 선택 근거 및 원시 확률을 보존했다. 기존 v16/공개 패키지의 동결 파일은 그대로이며, 이전 BinaryInferno·FieldHunter·Wireshark 등의 수치를 이번 신규 학습 결과인 것처럼 섞지 않았다. 전체 산출물 해시는 FINAL_ARTIFACTS.json에 기록한다.
