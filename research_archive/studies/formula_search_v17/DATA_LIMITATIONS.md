> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# Frozen real-protocol corpus: descriptive limitations

이 문서는 v17의 고정된 corpus와 DATA_CONTRACT만 감사한 결과다. 수식 선택 점수나 최종 모델 결과를 읽지 않았으며, 학습·평가·선택 설정을 변경하지 않았다. 합성 프로토콜을 사용하지 않았다. 모든 세부 집계, capture 해시, sample-stream 해시는 DATA_LIMITATIONS.json에 있다.

## 1. 메시지 수와 정답 필드 수

각 셀은 `messages / annotated fields`다. Field 수는 독립 capture 수가 아니다.

| Protocol | Train | Full development | Selected development | Evaluation |
|---|---:|---:|---:|---:|
| DNS | 1000 / 10544 | 262 / 2817 | 24 / 230 | 38 / 266 |
| Modbus | 1000 / 1000 | 139 / 139 | 24 / 24 | 6 / 6 |
| TLS | 1000 / 1000 | 80 / 80 | 24 / 24 | 15 / 15 |
| SMB2 | 89 / 356 | 41 / 164 | 24 / 96 | 15 / 60 |
| Total | 3,089 / 12,900 | 522 / 3,200 | 96 / 374 | 74 / 347 |

개발 집합은 프로토콜별 사전에 고정한 24개 메시지만 선택/threshold 계산에 사용한다. 따라서 DNS의 선택용 개발 정답은 LENGTH 221개, POINTER 9개뿐이다. 전체 개발 집합의 DNS pointer 233개를 모두 검증한 것은 아니다.

학습 메시지는 DNS·Modbus·TLS 각 1,000개지만 SMB2는 89개다. 프로토콜 균등 샘플링은 protocol별 배치 비중을 맞출 뿐, SMB2의 원본 메시지 다양성을 늘리지 않는다.

## 2. Capture/group 독립성: 보장되는 범위와 보장되지 않는 범위

| Global split comparison | Duplicate message IDs | Shared raw hashes | Shared group IDs | Shared capture hashes |
|---|---:|---:|---:|---:|
| development_vs_evaluation | 0 | 0 | 0 | 0 |
| train_vs_development | 0 | 0 | 0 | 2 |
| train_vs_evaluation | 0 | 0 | 0 | 0 |

중요: **train과 development가 모두 capture-disjoint인 것은 아니다.** DNS와 TLS는 train/development뿐 아니라 두 protocol 사이에서도 동일한 원본 capture를 공유한다. SMB2도 train/development의 원본 capture가 같다. 이들은 메시지/raw/group은 분리되어 있지만 capture 전체를 분리한 검증은 아니다. Modbus의 train/development는 서로 다른 capture다.

따라서 내부 protocol transfer 검증 12개 source-pair→validation 조합 중 다음 4개는 capture를 공유한다. 나머지 8개는 capture 교집합 0이며, 12개 모두 raw/group 교집합은 0이다.

| Inner training protocols | Validation protocol | Shared captures |
|---|---|---:|
| DNS + Modbus | TLS | 1 |
| DNS + SMB2 | TLS | 1 |
| Modbus + TLS | DNS | 1 |
| TLS + SMB2 | DNS | 1 |

반면 최종 3→1의 네 outer fold 모두에서 source train→target evaluation, source selected development→target evaluation의 message/raw/group/capture 교집합은 모두 0이다. 정확한 표현은 **최종 target evaluation은 source와 capture-disjoint**이지, 모든 단계에서 capture를 분리했다는 표현이 아니다.

| Evaluation protocol | Messages | Unique groups | Unique captures | Byte-length range |
|---|---:|---:|---:|---:|
| DNS | 38 | 8 | 1 | 25-256 |
| Modbus | 6 | 4 | 1 | 9-18 |
| TLS | 15 | 1 | 1 | 6-252 |
| SMB2 | 15 | 1 | 1 | 132-256 |

TLS와 SMB2의 평가 메시지는 각각 group 1개, capture 1개에서 나왔다. 세 seed의 신뢰구간은 학습 난수에 대한 변동만 반영한다. 다양한 capture나 protocol 모집단에 대한 일반화 불확실성으로 해석하면 안 된다. 평가 corpus는 과거 실험에서 이미 검토된 자료이므로 새로운 blind confirmatory test가 아니다.

## 3. Evaluation relation × destination kind

INTERIOR는 메시지 내부 byte 위치, END는 메시지 길이 n, NULL은 n+1의 별도 정답 class다. 아래의 NULL은 실제 존재하는 annotated field의 정답이며, 없는 필드나 예측 실패를 NULL로 바꾼 것이 아니다.

| Protocol | Relation | Fields | Messages containing relation | INTERIOR | END | NULL |
|---|---|---:|---:|---:|---:|---:|
| DNS | DNS RDLENGTH | 25 | 10 | 15 | 10 | 0 |
| DNS | DNS TXT length | 1 | 1 | 0 | 1 | 0 |
| DNS | DNS label | 164 | 38 | 164 | 0 | 0 |
| DNS | DNS pointer | 36 | 10 | 36 | 0 | 0 |
| DNS | DNS root terminator | 40 | 38 | 38 | 2 | 0 |
| Modbus | Modbus MBAP length | 6 | 6 | 0 | 6 | 0 |
| TLS | TLS record length | 15 | 15 | 0 | 15 | 0 |
| SMB2 | SMB2 ContextLength | 15 | 15 | 0 | 13 | 2 |
| SMB2 | SMB2 ContextOffset | 15 | 15 | 13 | 0 | 2 |
| SMB2 | SMB2 NameLength | 15 | 15 | 6 | 2 | 7 |
| SMB2 | SMB2 NameOffset | 15 | 15 | 8 | 0 | 7 |

Modbus length 6개와 TLS length 15개는 전부 END다. 따라서 Always END만으로 두 cohort의 p(target)=1 및 Hit@1=1이다. 이 두 결과만으로 length 값을 읽고 연산했다고 입증할 수 없다. DNS TXT length도 평가 필드가 1개이고 정답이 END이므로 독립적인 강한 증거로 사용할 수 없다.

DNS LENGTH 전체는 230개 중 END 13개(5.65%), INTERIOR 217개다. SMB2 LENGTH는 30개 중 END 15개, INTERIOR 6개, NULL 9개이며, SMB2 OFFSET은 INTERIOR 21개, NULL 9개다. 이 비율 때문에 최종 protocol macro와 field micro 평균은 서로 다른 질문을 답한다.

## 4. Public ordinal slot의 positive 노출

`slot`은 public query ordinal이지 정답 byte source 위치가 아니다. 추론은 메시지마다 항상 64개 slot을 처리하며 정답 field count를 입력하지 않는다.

| Held-out target | Positive source slot range | Target slots without source-positive supervision | Affected target fields |
|---|---|---|---:|
| DNS | 0-3 | 4-38 | 119 / 266 |
| Modbus | 0-32 | None | 0 / 6 |
| TLS | 0-32 | None | 0 / 15 |
| SMB2 | 0-32 | None | 0 / 60 |

DNS를 제외한 학습 자료의 positive slot은 0-3뿐이다. DNS 평가 정답 266개 중 119개(44.74%)는 slot 4-38에 있다. 이 slot들이 완전히 학습되지 않았다는 뜻은 아니다. 고정된 세 최종 seed 각각에서 slot 4-38은 **negative presence 예시**를 받았지만 positive source/program/endpoint 예시는 0개였다. 해당 35개 slot의 개별 negative 횟수는 JSON에 보존했다.

나머지 세 fold의 target slot은 모두 source positive slot 범위 안이다. CNN/GRU 및 shared-slot variant는 독립 slot embedding을 shared 함수로 바꾸지만 positive-label 노출 자체를 새로 만드는 것은 아니다.

## 5. Program bank prior와 실제 positive supervision 구분

모든 routed 수식은 학습 전에 고정된 **68개 native_v4 program**을 안다. Bank fingerprint: `4fb4761b507db01a0fc4fd9bbf6cbfd9cf658cb61532e3fcbdbcdbb39d40e81d`. 축은 width, endian, sign, base, mask다. DNS pointer guard와 SMB2 인접 offset/length 연산도 executor에 미리 존재한다. 새로운 protocol의 training label이 없다는 사실은 주소 연산 bank까지 전혀 모른다는 뜻이 아니다.

아래 `source corpus fields`는 선택 가능한 source 정답의 수이며 실제 gradient에 사용된 draw 횟수와 다르다. `sampled positives`는 모델 결과를 읽지 않고 고정 sampler를 600 step 재생하여 계산한 counts이며, 반복 추출을 포함한다. ID는 고정 bank의 0-based index다.

| Target | Relation(s) | Program ID | Width/endian/base | Source corpus fields | Target fields | Positive draws: seed 170301 / 170302 / 170303 |
|---|---|---:|---|---:|---:|---:|
| DNS | DNS TXT length; DNS label; DNS root terminator | 1 | 1 / big / field_end_forward | 0 | 205 | 0 / 0 / 0 |
| DNS | DNS RDLENGTH | 9 | 2 / big / field_end_forward | 2000 | 25 | 3152 / 3213 / 3262 |
| DNS | DNS pointer | 56 | 2 / big / packet_absolute / mask=0x3fff | 0 | 36 | 0 / 0 / 0 |
| Modbus | Modbus MBAP length | 9 | 2 / big / field_end_forward | 1585 | 6 | 1699 / 1650 / 1696 |
| TLS | TLS record length | 9 | 2 / big / field_end_forward | 1585 | 15 | 1699 / 1650 / 1696 |
| SMB2 | SMB2 NameLength | 62 | 2 / little / previous_offset_plus_length | 0 | 15 | 0 / 0 / 0 |
| SMB2 | SMB2 NameOffset | 63 | 2 / little / offset_with_next_length | 0 | 15 | 0 / 0 / 0 |
| SMB2 | SMB2 ContextLength | 66 | 4 / little / previous_offset_plus_length | 0 | 15 | 0 / 0 / 0 |
| SMB2 | SMB2 ContextOffset | 67 | 4 / little / offset_with_next_length | 0 | 15 | 0 / 0 / 0 |

| Held-out target | Target program IDs without source-positive labels | Affected target fields | Axis values absent from source-positive labels |
|---|---|---:|---|
| DNS | 1, 56 | 241 / 266 | base: packet_absolute; mask: 3fff; width: 1 |
| Modbus | None | 0 / 6 | None |
| TLS | None | 0 / 15 | None |
| SMB2 | 62, 63, 66, 67 | 60 / 60 | base: offset_with_next_length, previous_offset_plus_length; endian: little; width: 4 |

DNS holdout에서 241/266개(90.60%)의 target field는 해당 program이 source-positive 정답으로 등장하지 않는다. RDLENGTH의 program 9는 source corpus 2,000개와 실제 positive draw 3,152-3,262개에 등장하므로, RDLENGTH 실패를 단순히 ‘그 연산을 학습한 적이 없다’고 설명하면 안 된다.

SMB2 holdout에서는 target의 네 program 모두 source-positive 정답이 0개이며, little endian, width 4, 두 인접 offset/length base도 source-positive label에 없다. 다른 protocol에서 학습한 source locator와 selector가 고정 bank의 미감독 후보를 선택해야 하는 조건이다. 반대로 Modbus/TLS의 program 9는 source corpus와 모든 최종 seed에서 positive로 등장한다.

Program CE의 positive label이 없더라도 그 후보의 확률·파라미터가 완전히 고정되어 있다는 뜻은 아니다. 전체 softmax 경쟁, 공유 axis 파라미터, source/endpoint loss 등으로 영향을 받을 수 있다. 일부 동치 프로그램은 같은 목적지를 만들 수 있으므로 labeled-program 정확도와 endpoint 정확도도 구분한다.

## 6. Loss가 실제 적용되는 예시

| Model / query | Presence | Source | Program | Endpoint |
|---|---|---|---|---|
| LAPA On, positive field slot (8 per step) | Yes | Yes | Yes | Yes |
| LAPA On, absent field slot (8 per step) | Yes | No | No | No |
| X-Route Off, positive field slot (8 per step) | No | No | No | Yes |
| X-Route Off, absent field slot (8 per step) | No | No | No | No |

최종 600 step의 모델별 배치는 positive draw 4,800개와 negative draw 4,800개다. On의 negative 예시는 presence BCE에만 직접 기여한다. 공유 encoder는 이 BCE를 통해 업데이트될 수 있지만 negative 예시에 source/program/endpoint 정답 loss를 부여한 것은 아니다. Off는 negative 예시에서 loss를 받지 않는다.

**Negative query를 NULL endpoint로 학습시키지 않는다.** NULL endpoint 정답이 있는 SMB2 field는 present=True인 positive field이며 위 첫째/셋째 행에 해당한다.

## 7. 해석 경계

- corpus 다양성, capture 수, selected-development 수, positive slot 범위, program-label 범위는 서로 다른 제한이다. 이를 하나의 ‘unseen’이라고 합쳐 설명하지 않는다.
- final target label을 학습하거나 수식 선택에 사용하지 않았다는 조건과, 고정 operator bank가 사전 지식을 제공한다는 조건을 동시에 적는다.
- 학습 draw는 protocol 균등 → 해당 protocol 안에서 message 균등 → positive/negative slot 균등이다. 따라서 데이터의 raw field 수 비율과 gradient 기여 비율은 일치하지 않는다.
- 위 audit은 실험 결과의 강점이나 약점을 숨기기 위한 후속 필터가 아니다. 현재의 frozen 선택이나 평가 표를 변경하지 않고 해석상 주의점을 공개하는 용도다.

