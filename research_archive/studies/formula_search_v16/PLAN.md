> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# LAPA 수식 탐색 v16 — 사전 고정 계획

## 목적과 범위

QKV가 LAPA를 방해한다는 것은 가설이다. 기존 패키지/체크포인트를 변경하지 않고 실험 전용 모듈에서 대안을 비교한다. 기준 encoder는 native-v4 compact **TAPE**다. 이번 제한된 구조 탐색은 RoPE/CoPE/SDPA 전체 재실험이 아니다. 원본 실측 DNS, Modbus, TLS, SMB2만 사용하며 합성 패킷을 만들지 않는다.

현재 program head는 이미 width/endian/sign/base/mask 축의 가산 점수다. base/endian/width만으로 DNS mask/guard나 SMB2 인접 필드 연산을 설명할 수 없다. 68개 기존 program bank와 실행기를 모든 후보에서 동일하게 고정한다. 이 bank는 사전 구조 지식이며 unseen protocol이 완전히 unknown operation이라는 뜻은 아니다.

## 후보: 결과를 보기 전에 고정

1. `hybrid`: 현행 TAPE+LAPA, head별 QK logits + log(route/uniform) 결합.
2. `route_sink`: 같은 TAPE encoder와 기존 gate/sink를 유지하되 final=route prior. 목적지 retrieval QK 제거, encoder QKV는 유지.
3. `route_direct`: source×conditional program×valid의 전체 질량을 정규화 후 실행 목적지로 합산. top/width gate, retrieval QK 제거.
4. `route_axis`: 3과 같은 최종 수식. program loss를 valid-bank CE 대신 5개 축 CE의 평균으로 변경하여 축 감독 효과만 비교.
5. `route_joint`: source logit+5개 축 점수 합을 유효한 모든 (source,program) 위에서 공동 softmax. 4와 같은 축 감독. per-source program 분모 제거 효과 비교.
6. `cnn_joint`: 5와 같은 수식/감독, TAPE encoder 대신 slot-conditioned dilated CNN. encoder와 final 모두 QKV 없음. encoder 유형/파라미터 수가 함께 바뀌므로 QKV만의 인과 효과로 해석하지 않는다.

추가 최종 대조군 `off`: TAPE, 목적지 NLL만. 위 6개 On 후보는 presence/source/program/endpoint 네 loss를 모두 가중치1로 사용한다. 축 CE 평균도 하나의 program loss 항이다. 정답 source/program은 학습 감독 및 사후 진단에서만 사용하며 forward에는 raw bytes, observed mask, ordinal slot만 전달한다.

## 탐색 → 고정 → 최종 평가

- 데이터와 코드 해시를 고정한 뒤 GPU smoke test와 본 실험을 구분한다.
- 6개 서로 다른 2-protocol 학습 조합 × 6개 후보 × 2개 seed(160101,160102) = **72개 탐색 모델**, 각250 update.
- 각 모델은 학습하지 않은 두 프로토콜의 development만 예측한다. 이를 재사용하여 outer target별로 나머지3개 프로토콜 내의 inner 2→1 검증3개를 얻는다. 해당 outer target의 development 점수는 그 target의 수식 선택에 절대 사용하지 않는다.
- Development는 protocol별 raw_sha256/message_id 순서 앞32개 메시지로 사전 고정한다. labels로 샘플을 선택하지 않는다. 모든 메시지에서64개 ordinal query를 예측한 뒤 gold를 읽어 점수화한다.
- 선택 지표: 각 validation protocol에서 nonempty **relation×{INTERIOR,END,NULL}** strata를 동등 평균한 `log(n+2)−NLL`, 이후3개 protocol×2개 seed 동등 평균. 높은 것이 좋음. 동점은 위 후보 순서. END shortcut을 숨기지 않도록 interior/END/NULL과 Always-END/NULL/uniform을 별도 보고한다.
- target별 후보1개를 선택해 `SELECTION.json`을 고정한 후에만 evaluation 추론을 시작한다.
- 최종:3-source train→1-target test, target4개 × freshseed3개(160201–160203) × {TAPE off, 현행 hybrid, 선택된 수식} = 최대 **36개 모델**, 각600 update. 선택된 수식이 hybrid면 같은 실행을 재사용하고 중복 계산하지 않는다.
- Optimizer AdamW lr.002/wd.01, gradient clip1; batch16=양성8+음성8, protocol균등→message균등. 동일 seed의 샘플 스트림 일치. final은600번째 checkpoint 고정, target tuning/early stopping 없음.
- Field threshold는 source-development의 protocol-macro typed F1로만 선택(.05:.05:.95, 동률시 큰 값). Off는 field auxiliary loss가 없으므로 discovery F1을 미지원으로 표기하고 endpoint만 비교한다. 기존 decoder 유지; 공동 route posterior와 pre-validity locator는 진단에서 구분한다.

## 산출물과 해석 한계

체크리스트/단계 로그, 실행 가능한 모델과 테스트, 해시 계약,72개 탐색 결과, 최종 checkpoint 및 raw-only prediction seal, 수식별 dev 비교와 target별 최종 p(target)/NLL/Hit@1/field F1, source/program stage 및 seen/unseen ordinal 분해, Matplotlib 숫자 그래프/표, 보고서를 남긴다.

최종 test는 이전 실험에서 이미 본 historical test이므로 **탐색적 결과**다. 최상의 수식은 이6개 후보/예산/선택 규칙 안에서만 정의한다. 3 seed CI는 seed 변동만 반영하며 작은 packet/capture 수와 데이터 모집단 불확실성을 해결하지 않는다. 최종에서 부진해도 결과를 보고 다른 수식으로 교체하지 않는다. 후속 개선은 새 탐색으로 분리해야 한다.

기존 fixed ordinal query 체계 및 알려진 program bank를 유지한다. DNS source-training positive slot 지원 부족, SMB2 소량 학습, Modbus/TLS END shortcut, train/dev 일부 capture 공유 등의 한계는 별도 감사한다. 본 실험에서 QKV 제거만으로 unseen parsing이 해결된다고 미리 주장하지 않는다.
