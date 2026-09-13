> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# 수식 탐색 단계 해석: search-only

이 문서는 완료된 **72개 search 모델**, 해당 모델의 **source-only 내부 development 예측**, 학습 곡선, 봉인된 `SELECTION.json`만 분석했다. `final/`의 평가 결과는 읽지 않았다. 아래 수치로 선택된 수식을 변경하지 않으며, 이 문서는 최종 평가 결론이 아니다.

## 1. 먼저 얻은 답

**이번 250-step 탐색에서는 QKV를 제거하면 일반화가 일관되게 좋아진다는 가설을 지지하지 않는다.** 네 outer fold 중 DNS·TLS·SMB2를 제외하는 fold에서는 기존 Hybrid가 선택되었다. Modbus 제외 fold에서는 최종 목적지 QK만 제거하고 기존 route gate/sink를 남긴 `route_sink`가 선택되었다. 모든 encoder QKV를 제거한 `cnn_joint`는 어느 fold에서도 선택되지 않았다.

이는 “QKV는 반드시 필요하다”의 증명도 아니다. 탐색은 여섯 후보·두 seed·250 step의 제한된 예산이고, 후보별 정규화·loss·encoder 변경이 섞여 있다. 특히 CNN은 학습 loss 자체는 잘 내려갔지만, 보지 못한 프로토콜의 목적지 분포로 전이되지 않았다.

## 2. 선택 점수와 실제 순위

선택 점수는 각 필드의 `log(byte_length+2) − NLL`을 먼저 계산하고, 프로토콜 내부의 비어 있지 않은 `relation × {INTERIOR, END, NULL}` 그룹을 동일 가중 평균한 값이다. 그 후 세 내부 검증 프로토콜과 두 seed를 동일 가중 평균한다. **0은 uniform 목적지 분포와 같은 로그 성능, 양수는 uniform보다 좋음을 뜻한다.** 이것은 raw `p(target)` 평균이 아니다.

| 후보 | DNS outer 제외 | Modbus outer 제외 | TLS outer 제외 | SMB2 outer 제외 |
|---|---:|---:|---:|---:|
| Hybrid | **1.46874** | −0.78943 | **0.51752** | **1.76333** |
| Route-sink | −0.41454 | **0.09651** | 0.30781 | −0.20036 |
| Route-direct | −0.29226 | −0.37987 | −0.45545 | −1.00610 |
| Route-axis | −0.83246 | −0.54839 | −0.30851 | −0.87734 |
| Route-joint | −1.45729 | −1.00609 | −0.42107 | −0.91437 |
| CNN-joint | −1.54864 | −1.30121 | −0.97097 | −0.57110 |

각 열의 target development/evaluation은 **그 열의 선택에 사용하지 않았다.** 예를 들어 DNS 제외 열의 점수는 Modbus·TLS·SMB2에서만 얻은 내부 검증 결과다. 따라서 DNS 제외 열에서 Hybrid를 선택했다고 DNS에서 Hybrid가 좋다고 이미 판정한 것은 아니다.

### Modbus 제외 fold에서 Sink가 이긴 이유

| 내부 검증 프로토콜 | Hybrid 점수 | Route-sink 점수 | Route-direct 점수 |
|---|---:|---:|---:|
| DNS — TLS+SMB2로 학습 | −0.5154 | −0.1362 | −1.5931 |
| TLS — DNS+SMB2로 학습 | −1.7603 | 0.3312 | 0.4971 |
| SMB2 — DNS+TLS로 학습 | −0.0926 | 0.0945 | −0.0436 |
| 세 프로토콜 평균 | −0.7894 | **0.0965** | −0.3799 |

Route-sink가 여기서 선택된 이유는 세 프로토콜 모두에서 큰 확률 손실을 피한 결과다. 반대로 Route-direct는 TLS에서 좋았지만 DNS에서 잃은 로그 성능을 회복하지 못했다. **이는 최종 Modbus 결과가 아니라 Modbus 정답을 전혀 쓰지 않는 선택 근거**다.

## 3. 목적지 QK를 제거하면 무엇을 잃었는가

아래 표는 특정 outer fold의 선택표가 아니라, 각 validation 프로토콜에 대해 가능한 세 source-pair × 두 seed, 즉 여섯 search 결과의 평균이다. 모든 source-pair는 해당 validation 프로토콜을 학습에서 제외한다. 고정된 development 표본은 DNS 302개 필드, Modbus 32개, TLS 32개, SMB2 128개다. 각 프로토콜에서 32개 메시지를 사용했다.

| Validation | Hybrid p(target) | Sink p(target) | Direct p(target) | Axis p(target) | Joint p(target) | CNN p(target) |
|---|---:|---:|---:|---:|---:|---:|
| DNS | .01425 | .01368 | .00802 | .00675 | .00655 | .00655 |
| Modbus | .51651 | .13825 | .33051 | .20499 | .22174 | .25497 |
| TLS | .31649 | .01851 | .07747 | .06659 | .07683 | .07173 |
| SMB2 | .03411 | .00491 | .00544 | .00542 | .00391 | .01626 |

Modbus/TLS의 length 정답은 이 데이터에서 모두 END다. Hybrid의 이득에는 특수 END endpoint를 직접 예측하는 경로가 기여할 수 있다. Always-END는 여기서 완벽하므로, 위 이득을 올바른 length 산술을 학습했다는 증거로 해석하면 안 된다.

같은 Hybrid forward 안에서 평균 `base_p → final_p`는 Modbus `.49317 → .51651`, TLS `.27005 → .31649`였다. 같은 모델의 `route_p`는 각각 `.16477`, `.03415`였다. 즉 이 내부 검증들에서는 최종 QK 쪽 분포가 route 분포보다 정답 목적지에 많은 질량을 주고 있었다. 별도 학습된 Route-sink와의 차이를 이것 하나의 인과효과로 단정할 수는 없지만, “QK는 무조건 방해한다”와는 맞지 않는 관측이다.

## 4. Pointer 개선이 전체 선택으로 이어지지 않은 이유

DNS의 relation×target-kind별 목적지 확률은 다음과 같다. 각 값은 동일한 여섯 search 결과의 평균이다. N은 한 validation 세트의 고유 필드 수다.

| DNS relation × target kind | N | Hybrid | Sink | Direct | Axis | Joint | CNN |
|---|---:|---:|---:|---:|---:|---:|---:|
| Label × INTERIOR | 238 | .01434 | .01361 | .00322 | .00400 | .00511 | .00526 |
| Pointer × INTERIOR | 12 | .00777 | .01097 | **.12652** | .07468 | .04197 | .04395 |
| RDLENGTH × END | 10 | .01052 | .00966 | .00038 | .00130 | .00054 | .00021 |
| Root terminator × END | 8 | .00939 | .00955 | .00038 | .00153 | .00054 | .00036 |
| Root terminator × INTERIOR | 34 | .01816 | .01728 | .00386 | .00486 | .00735 | .00573 |

Direct는 pointer에서 분명한 확률 증가를 보였지만 length 계열 네 그룹에서 크게 감소했다. 이 선택 기준은 필드가 많은 label만 가중하는 것도 아니고 pointer만 가중하는 것도 아니다. **다섯 relation×kind 그룹을 동일 가중**하므로, pointer 한 그룹의 개선만으로 다른 그룹의 감소를 상쇄하지 못했다.

실제로 DNS의 balanced log gain은 Hybrid `−.51492`, Sink `−.10221`, Direct `−2.18450`, Axis `−1.80924`, Joint `−2.04417`, CNN `−2.71217`이었다. Direct의 pointer 그룹은 `+.95479`였지만, RDLENGTH-END는 `−3.46899`, root-END는 `−3.49565`였다.

한 가지 중요한 구분도 남는다. Modbus+SMB2 학습 → DNS pointer 검증에서 Direct의 목적지 확률은 `.25978`, Hit@1은 `.33333`이지만, 정답 source의 **pre-validity head 확률**은 `.00050`이었다. 따라서 endpoint 개선을 곧바로 정확한 필드 위치 발견으로 해석하면 안 된다. 유효 source-program 쌍 정규화가 source posterior를 바꿀 수 있으므로, 이 낮은 head 확률만으로 잘못된 source를 사용했다고 확정할 수도 없다. 해당 결론에는 실제 route posterior와 필드 F1을 별도로 확인해야 한다.

## 5. 강한 정규화가 분포를 집중시켰지만 정답을 보호하지 못함

DNS validation에서 각 양성 슬롯의 전체 목적지 분포를 확인했다. KL은 `KL(final || uniform)`이며, 최고 확률은 그 슬롯에서 가장 큰 목적지 확률이다. 모두 여섯 search 결과를 동일 가중 평균했다.

| 후보 | KL(final∥uniform), nat | 평균 최고 목적지 확률 | 정답 p가 smoothing floor의 1.05배 이하인 비율 |
|---|---:|---:|---:|
| Hybrid | .74703 | .18726 | 비교 대상 아님: log-product라 같은 floor 보장 없음 |
| Route-sink | .37794 | .11594 | 3.48% |
| Route-direct | 2.01554 | .38265 | 30.96% |
| Route-axis | 1.75045 | .33474 | 20.42% |
| Route-joint | 1.77561 | .36572 | 22.90% |
| CNN-joint | 2.38621 | .51328 | 39.18% |

여기서 smoothing floor는 `.02/(byte_length+2)`다. Direct/Joint/CNN은 uniform보다 훨씬 집중된 분포를 만들었지만, 상당수 정답은 거의 최소 확률만 받았다. 따라서 raw 평균 확률에서 일부 성공 사례가 좋아 보여도 NLL은 나빠질 수 있다. Sink의 분포가 정확히 uniform인 것은 아니지만, 이 DNS 검증에서는 상대적으로 덜 집중되어 정답 확률의 극단적 하락이 적었다.

SMB2에서도 비슷한 주의가 필요하다. CNN의 NameOffset-INTERIOR 평균 p는 `.05004`로 Hybrid `.00063`보다 높지만, 해당 그룹의 uniform-relative log gain은 여전히 `−1.69180`이었다. 일부 높은 확률과 많은 낮은 확률이 공존할 수 있으므로, 평균 p 하나만으로 견고한 일반화를 주장할 수 없다. 이 그룹의 N은 30이다.

## 6. CNN은 아예 학습이 안 된 것인가

그렇게 보기는 어렵다. 각 모델의 마지막 25개 update를 평균한 뒤, 후보당 12개 학습 run을 동일 가중 평균했다.

| 후보 | Presence loss | Source loss | Program loss | Endpoint loss |
|---|---:|---:|---:|---:|
| Hybrid | .05904 | .88105 | .12198 | .37742 |
| Route-sink | .04176 | .75759 | .10279 | .74898 |
| Route-direct | .04139 | .73007 | .10431 | .66037 |
| Route-axis | .04184 | .79723 | .06790 | .74660 |
| Route-joint | .04359 | .79552 | .07929 | .71807 |
| CNN-joint | .09906 | **.32691** | .04510 | **.31685** |

CNN의 source·endpoint training loss는 충분히 감소했다. 그런데 DNS validation NLL은 CNN `6.96622`, Hybrid `4.88251`, Sink `4.56861`이었다. 이 관측은 최적화 실패보다는 학습한 source/program 선택 방식의 프로토콜 전이가 어렵다는 해석과 양립한다. 다만 train loss와 validation loss 차이가 크다고 곧바로 특정 원인을 확정할 수는 없다.

### Program loss의 척도 차이를 반드시 구분

Hybrid/Sink/Direct는 bank program CE를, Axis/Joint/CNN은 다섯 축의 CE 평균을 쓴다. 첫 update의 평균 program loss는 다음과 같다.

- Hybrid/Sink/Direct: **4.21796**
- Axis/Joint: **1.05062**
- CNN: **1.05090**

최상위 네 loss의 계수는 모두 1이지만, program 항의 의미와 초기 수치 척도는 같지 않다. Direct와 Axis는 초기 forward가 같고 첫 endpoint loss도 `5.31061`로 같지만, program 항을 바꾸므로 gradient와 학습 균형이 바뀐다. 따라서 Axis/Joint의 결과를 순수한 “규칙 인자화의 효과”나 “QK 제거 효과”로 설명하면 안 된다. 원래 구현의 program 점수도 이미 width/endian/sign/base/mask 축 점수의 합이었다.

## 7. 현재 증거가 허용하는 결론과 허용하지 않는 결론

현재 search 결과가 허용하는 결론은 다음 정도다.

1. 이 후보·예산·선택 지표에서는 **일괄적인 QKV 제거가 우세하지 않았다.** 기존 Hybrid가 네 fold 중 세 fold의 source-only 검증에서 선택되었다.
2. Direct의 DNS pointer 확률 개선은 별도 연구 가치가 있지만, 같은 조건에서 length 계열 목적지 확률이 감소했다. 전체 선택과 pointer-specific 목표를 혼동하면 안 된다.
3. Sink가 이긴 fold는 강제적인 유효 쌍 정규화보다 덜 공격적인 확률 배분이 유리했던 사례다. 이는 완성된 주소 추론 능력의 증명은 아니다.
4. CNN은 training source/endpoint loss를 낮췄지만 unseen-protocol validation으로 전이하지 못했다. 학습 budget 증가, 다른 encoder, 다른 질의 방식의 결과까지 배제하지 않는다.
5. Program loss 척도와 정규화의 동시 변경이 있으므로, 후속 인과적 ablation에는 동일 forward의 Direct/Axis 비교뿐 아니라 program gradient 규모를 맞춘 대조군도 필요하다. 이 조정은 현재 봉인된 선택/최종 실험 중간에는 하지 않는다.

아직 허용하지 않는 결론은 “QKV가 일반화 실패의 원인이다”, “CNN은 주소 관계에 부적합하다”, “pointer만 좋아졌으므로 새 LAPA가 전체적으로 더 좋다”이다. DNS/SMB2 고유 프로그램의 양성 미노출, DNS 양성 슬롯의 미노출, END shortcut, 역사적으로 이미 관찰한 평가 자료라는 제한을 함께 보고해야 한다. true-source Program 확률은 이 search export에 없으므로 그 단계가 실패 원인이라고 수치로 단정하지 않는다.

## 근거 파일과 재현 집계 규칙

- 선택: `SELECTION.json`의 `choices[target].ranked`와 각 `evidence.path`.
- Search endpoint 수치: `search/{source_pair}/{variant}_{seed}/validation/{protocol}/METRICS.json` 및 `diagnostics.jsonl`.
- 전체 분포 집중도: 같은 validation 폴더의 메시지별 `.npz` 중 `final`; 양성 슬롯만 gold로 후처리 인덱싱했다.
- 학습 loss: 각 search run의 `curve.json`; 마지막 25개 update 또는 첫 update만 사용했다.
- 설계 제약: `DESIGN_LIMITATIONS.md`, `DESIGN_AUDIT.json`, `models16.py`, `losses16.py`.

표의 확률·NLL·집중도는 search 후보 2-seed 평균의 기술통계다. 여기서 confidence interval이나 최종 성능 유의성은 주장하지 않는다. **이 문서 작성 과정에서 `final/` 평가 결과를 읽거나 수식·선택 기준·학습 코드를 수정하지 않았다.**
