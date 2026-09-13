> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# LAPA v17 재현 안내

이 문서는 실제 v17 코드의 실행 순서, 고정 설정, 저장물, 해석 경계를 설명한다. 학습 완료 여부나 후보의 우월성은 이 문서에서 주장하지 않는다. 진행 상태는 `GRID_PROGRESS.json`, 완료 여부는 `GRID_COMPLETE.json`과 개별 `COMPLETE.json`, 수치 해석은 별도의 보고서와 표에서 확인한다.

## 1. 먼저 구별할 것

- 실험에는 **실제 DNS, Modbus, TLS, SMB2 데이터만** 사용한다. 합성 프로토콜 생성이나 외부 대상에 대한 패킷 전송은 없다.
- 30개 모든 후보는 screening을 한다. 그러나 모든 후보를 네 backbone × 최종 test에 전부 학습하는 설계는 아니다. 내부 검증으로 승격·선택된 후보만 최종 단계에 들어간다.
- 탐색은 TAPE 기준이다. CNN/GRU encoder 후보에는 Transformer backbone이 없으므로 `none`으로 표시한다.
- 최종 RoPE/CoPE/TAPE/SDPA 실험은 **TAPE 기준으로 source-only 선택한 수식의 다른 backbone 적용**을 평가한다. 각 backbone에서 독립적으로 최적 수식을 탐색한 결과라고 부르지 않는다.
- Off는 endpoint NLL만 사용한다. 모든 On은 presence/source/program/endpoint 네 항을 양의 가중치로 사용한다. 일부 후보의 가중치·program 감독 변경은 아래와 `FORMULAS.md`에 명시한다.
- 기존 `lapa-attention` 패키지 및 v16 checkpoint를 덮어쓰지 않는다. v17은 별도의 `SearchModel` 연구 클래스다.

## 2. 경로와 환경

현재 작업 공간의 실행 경로는 다음과 같다.

```bash
v17_taskdir=WORKSPACE/openAI/packet_attention_v3m/paper/more_experiement/source_destination_decomposition/prior_method_field_study_v2/formula_search_v17
v17_python=WORKSPACE/experiments/.venv/bin/python
cd "$v17_taskdir"
```

`common17.py`가 인접한 `formula_search_v16`과 workspace의 `lapa-attention/src`를 import path에 추가한다. 따라서 이 실험 폴더 하나만 외부로 복사하면 독립 실행되는 패키지가 아니다.

문서 작성 시 해당 Python 환경에서 직접 확인한 버전은 다음과 같다. 논문의 모든 과거 실험이 이 버전에서 수행되었다는 뜻은 아니다.

| 구성 | 확인된 버전/경로 |
|---|---|
| Python | 3.12.3 |
| PyTorch | 2.13.0+cu130 |
| PyTorch CUDA runtime | 13.0 |
| NumPy | 2.5.1 |
| Matplotlib | 3.11.1 |
| pypdf | 6.14.2 |
| Python 실행 파일 | `WORKSPACE/experiments/.venv/bin/python` |

학습 CLI는 CUDA를 요구한다. GPU가 보이지 않을 때 CPU로 조용히 바꾸거나 step 수를 줄이지 않는다. 제한된 실행 sandbox에서 `torch.cuda.is_available()`이 false라면, 권한이 있는 GPU 실행 환경에서 확인해야 한다. CPU는 smoke test 용도로만 지원한다.

```bash
"$v17_python" -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())"
```

학습 초기화에서는 CPU thread 수 2, CUDA process memory fraction 0.20, TF32 off, cuDNN benchmark off를 설정한다. `torch._native.registry.deregister_op_overrides(disable_dsl_names='triton')`도 사용한다. 이 private API는 현재 환경에 종속적이므로, 패키지의 일반 최소 의존성 `torch>=2.2`만 충족한다고 본 실험 코드가 동일하게 실행된다고 가정하면 안 된다. 다른 PyTorch로 이관할 때는 별도 환경 검증·새 코드 계약이 필요하다.

Queue는 기본 4 worker, 최대 4 worker를 지원한다. 각 worker의 memory fraction 설정은 전체 실행이 어떤 GPU에서나 안전하다는 보장이 아니다. 실제 가용 메모리와 동시 실행 작업을 확인해야 한다.

## 3. 데이터와 봉인 계약

### 3.1 원본과 작업 복사본

`prepare17.py`는 v16의 `DATA_CONTRACT.json`을 읽고, 해당 계약의 각 파일 hash를 검증한 뒤 v17 `data/`에 동일 JSONL 내용을 복사한다. 원본은 기존 real-protocol corpus다.

```text
data/
├── clean/
│   ├── train.jsonl
│   ├── development.jsonl
│   └── evaluation.jsonl
└── gold/
    ├── train.jsonl
    ├── development.jsonl
    └── evaluation.jsonl
```

Clean row의 key는 `message_id`, `data_hex`, `byte_length`, `raw_sha256` 네 개뿐이다. 모델에 들어가는 `ModelInputs`는 raw byte, observed mask, 공개 ordinal slot만 포함한다. Gold의 protocol/field annotation은 학습 loss, source-only 검증, 예측 봉인 이후 평가에 사용한다.

데이터 계약의 메시지 수는 다음과 같다.

| 프로토콜 | Train | Development 전체 | Development 사용 상한 | Evaluation |
|---|---:|---:|---:|---:|
| DNS | 1,000 | 262 | 24 | 38 |
| Modbus | 1,000 | 139 | 24 | 6 |
| TLS | 1,000 | 80 | 24 | 15 |
| SMB2 | 89 | 41 | 24 | 15 |

Development 24개는 `(raw_sha256, message_id)` 정렬 순서의 앞부분으로 고정한다. 정답으로 “좋은 예제”를 선별하지 않는다. 사용 ID는 `DATA_CONTRACT.json`의 `development_ids`에 명시한다. Evaluation 전체는 74개 메시지, 347개 annotation field다.

Evaluation은 과거에 분석한 **historical test**다. 새로운 blind confirmatory test라고 표현하지 않는다. 다만 v17 수식 선택 단계에서는 해당 outer target의 development/test 점수를 선택 근거로 사용하지 않는다.

### 3.2 계약 파일

| 파일 | 역할 |
|---|---|
| `PLAN.md` | 실행 전 후보·예산·선택 규칙 |
| `CODE_CONTRACT.json` | v17 학습 코드, 의존하는 v16 코드, 기존 패키지 `.py` hash와 seed/step |
| `DATA_CONTRACT.json` | 입력 파일 hash, split/protocol ID, development subset |
| `PROMOTION.json` | Screen에서 refine으로 올린 후보와 source-only 근거 |
| `SELECTION.json` | Refine 이후 확률/NLL 기준 각각의 선택 후보와 근거 |
| 각 run의 `COMPLETE.json` | 학습·예측·평가 산출물 hash |

현재 계약을 읽기 전용으로 검증하는 명령은 다음과 같다.

```bash
"$v17_python" -c "from common17 import verify_contract; verify_contract(); print('code/data contracts verified')"
```

실행 중 frozen 코드나 입력 파일을 수정하면 검증이 실패한다. 결과를 살리기 위해 hash만 새로 덮어쓰면 안 된다. 새로운 구조·학습 예산·데이터 변경은 별도 실험 lineage로 분리한다.

### 3.3 `prepare17.py`는 빈 재현 작업 디렉토리에서 한 번만

```bash
"$v17_python" prepare17.py
```

이 명령은 **아직 `data/`, 코드/데이터 계약이 생성되지 않은 새 작업 사본**을 초기화할 때만 사용한다. 현재 봉인된 v17 폴더에서 재실행하면 기존 파일을 덮어쓰지 않고 실패하도록 되어 있다. 현재 폴더에는 위의 `verify_contract`를 사용한다.

독립 재현을 위해서는 먼저 별도 결과 root에 필요한 코드와 `PLAN.md`를 준비하고, v16 의존 파일 및 동일 package source 접근을 유지해야 한다. 계약의 코드 경로는 절대 경로이므로, 다른 시스템으로 폴더를 옮긴 뒤 기존 계약을 그대로 재사용할 수 없다. 원 계약을 보존한 채 새 경로의 provenance와 새 계약을 만들어야 한다. 단순한 파일 이동을 원래 봉인과 동일한 run으로 표시하지 않는다.

## 4. Smoke test

```bash
"$v17_python" test17.py --device cpu
"$v17_python" test17.py --device cuda
```

검사는 각 프로토콜의 canonical TRAIN 파일 앞 두 메시지, 총 8개 메시지만 사용한다. Development/evaluation은 읽지 않는다. Known-field executor oracle fixture는 34개 field다.

새 smoke 기록을 저장하려면 **존재하지 않는 출력 파일명**을 지정한다.

```bash
"$v17_python" test17.py --device cpu --output SMOKE_CPU_recheck.json
"$v17_python" test17.py --device cuda --output SMOKE_CUDA_recheck.json
```

주요 검사 항목은 다음과 같다.

- Off + 30개 On 후보의 forward와 2 optimizer update.
- 네 backbone의 기존 Off/Hybrid 초기 tensor parity.
- On 네 loss의 실제 weighted sum과 Off auxiliary gradient 부재.
- Attribute Q/K의 endpoint gradient가 source 및 다섯 축 head로 전달되는지.
- CNN/GRU encoder에 native QKV가 없는지. `*_attr`의 최종 새 QK는 의도적으로 존재한다.
- 값 255의 비관측 padding을 추가해도 final/source/program 예측이 보존되는지.
- END/NULL index remap, 확률 합 1, padding 확률 0, checkpoint variant/backbone roundtrip.

CUDA scatter의 합산 순서 때문에 허용오차는 absolute/relative 각각 `1e-5`다. CPU는 `3e-6`다. 모든 tensor의 bitwise 학습 재현성을 보장하는 검사가 아니다.

## 5. 단계와 예산

| 단계 | 학습 조건 | 후보/seed | 고정 update |
|---|---|---|---:|
| Screen | 6개 고유 2-protocol source 쌍 | 30개 후보 × seed `170101` | 120 |
| Promotion | 해당 outer target을 제외한 source-only 내부 검증 | Target별 서로 다른 4개 후보 승격 | 학습 없음 |
| Refine | 승격 후보의 2→1 내부 검증 | Seeds `170201`, `170202` | 400 |
| Selection | Refine의 source-only 점수 | 확률 champion / NLL champion을 별도 고정 | 학습 없음 |
| Final | 3개 프로토콜 학습 → 나머지 1개 평가 | Seeds `170301`, `170302`, `170303` | 600 |

Screen은 180개 모델이다. Refine은 동일 `(source pair, variant, backbone, seed)`를 여러 outer fold에서 재사용하므로 최대 96개다. Final은 최대 192개이며, 같은 champion/Hybrid 중복 및 CNN/GRU의 `none` backbone 중복을 제거한다. 최대 합계는 468개이고, 실제 예정 job 수는 선택 파일을 반영한 `phase_jobs()`로 결정한다. 최대치를 실제 완료 개수처럼 보고하면 안 된다.

각 단계는 이전 checkpoint를 이어 학습하지 않고, 해당 단계 seed로 **처음부터** 학습한다. Screen 120 + Refine 400 + Final 600을 한 모델의 1,120 update처럼 합치지 않는다.

### 5.1 Outer target을 제외한 선택

예를 들어 DNS가 outer target이면, Modbus/TLS/SMB2 안에서만 다음 세 내부 조건을 사용한다.

| 내부 학습 | 내부 검증 |
|---|---|
| Modbus + TLS | SMB2 development |
| Modbus + SMB2 | TLS development |
| TLS + SMB2 | Modbus development |

Screen/Refine 모델은 자신이 학습하지 않은 두 프로토콜의 development를 계산해 다른 outer fold에서도 재사용할 수 있다. 그러나 **DNS 선택 점수에는 DNS development를 넣지 않는다.** Hash 감사가 다른 파일을 읽는 것과 그 점수를 선택에 사용하는 것은 별개다. `select17.py`는 모든 evidence의 source/validation에서 해당 outer target을 제외하는 assertion을 수행한다.

Promotion은 Hybrid, balanced probability 승자, balanced log-gain 승자, attribute 계열 rank-sum 승자를 우선 포함한다. 중복은 제거하고 고정 rank-sum/후보 순서로 채워 정확히 네 개를 선택한다. 따라서 최소 한 개 attribute 후보가 refine까지 진행된다.

Selection은 승격 네 후보만 대상으로 확률 champion과 NLL champion을 따로 정한다. 최종 target test를 보고 둘 중 더 잘 나온 후보로 승자 이름을 바꾸지 않는다.

### 5.2 선택 점수와 보고 점수

한 protocol 내의 비어 있지 않은 `relation × target-kind(INTERIOR/END/NULL)` 층을 동등 평균한다.

- `balanced_p`: 층별 정답 목적지 확률 평균을 다시 동등 평균.
- `balanced_log_gain`: 층별 `log(byte_length + 2) − NLL` 평균을 다시 동등 평균.

이후 세 내부 검증 protocol과 seed를 동등 평균한다. Uniform log 기준은 후보와 무관하므로, balanced log-gain 최대화는 같은 층 가중치의 NLL 최소화와 같다.

최종 표의 일반 field-mean `p(target)`, NLL, Hit@1은 이 balanced selection score와 다르다. 두 값을 섞어 승패를 설명하지 않는다.

## 6. 전체 queue 실행과 모니터링

준비·smoke·계약 검증 이후 다음 명령 하나가 screen → promotion → refine → selection → final을 순서대로 처리한다.

```bash
"$v17_python" run17.py --workers 4
```

Queue를 중복 실행하지 않는다. 이미 실행 중인지 확인하려면 진행 파일과 PID를 확인한다.

```bash
"$v17_python" -c "from common17 import ROOT, read, json; print(json.dumps(read(ROOT/'GRID_PROGRESS.json'), indent=2))"
```

| 파일 | 확인 내용 |
|---|---|
| `GRID_PROGRESS.json` | 현재 phase, done/total, active PID, pending, failure |
| `EVENTS.jsonl` | 시작·완료·실패·검증 재사용·선택 봉인 이벤트 |
| `logs/<phase>/*.log` | 개별 worker의 stdout/stderr |
| `<phase>/<group>/<model>/PROGRESS.json` | Step 또는 validation/threshold/inference 상태 |
| `MASTER_CHECKLIST.md`, `WORK_LOG.md` | 사람이 읽는 단계 체크와 해석 로그 |

Queue는 complete run이 있으면 **모든 artifact hash를 검증하고 재사용**한다. 그러나 partial run 폴더 또는 완료 seal 없는 기존 log가 있으면 자동으로 지우거나 재시도하지 않는다. 새 실행을 멈추고 원인을 조사하도록 fail-closed 처리한다. 이미 돌아가는 해당 queue의 worker는 마무리하고 봉인할 수 있게 기다린다.

부분 실패를 해결할 때는 해당 폴더와 log를 먼저 보존하고, 실패 원인과 변경 여부를 기록한다. 임의 seed 추가, 실패 run 삭제, threshold 완화, 예산 변경을 원래 실험처럼 섞지 않는다. 실행 중인 queue를 확인하지 않고 `run17.py`를 다시 실행하는 것은 재개가 아니라 중복 실행이 될 수 있다.

### 6.1 개별 scheduled job 명령

다음은 **해당 run 폴더가 아직 없고 다른 queue가 실행하지 않을 때** 사용할 수 있는 실제 CLI 예다.

```bash
"$v17_python" train17.py --phase screen --variant attr_only --backbone tape --seed 170101 --sources dns modbus
```

Final의 Hybrid 대조군 예시는 다음과 같다. 먼저 선택 파일이 봉인되어 있어야 한다.

```bash
"$v17_python" train17.py --phase final --variant hybrid --backbone tape --seed 170301 --sources dns modbus tls --target smb2
```

Source 순서는 고정 protocol 순서 `dns, modbus, tls, smb2`의 부분순서를 따른다. `train17.py`는 frozen schedule에 없는 seed/variant/phase 조합을 거부한다. Refine의 후보는 `PROMOTION.json`, Final의 champion은 `SELECTION.json`에 있어야 한다.

CNN/GRU 후보는 `--backbone none`을 사용한다. 이것은 다섯 번째 attention 방식이 아니라, Transformer backbone이 없다는 저장상의 구분이다.

Promotion과 Selection은 일반적으로 queue가 호출한다. 수동 실행이 필요하면 이전 단계가 모두 검증되어 있고 해당 출력 파일이 아직 없는지 확인한 뒤 사용한다.

```bash
"$v17_python" select17.py promote
"$v17_python" select17.py select
```

## 7. 고정 학습·모델 설정

| 항목 | 설정 |
|---|---|
| Optimizer | AdamW |
| Learning rate / weight decay | 0.002 / 0.01 |
| Gradient norm clip | 1.0 |
| Batch | 16 query: positive 8 + negative 8 |
| Sampling | Source protocol 균등 → 해당 protocol의 message 균등 |
| Hidden / heads / layers / FF | 32 / 4 / 2 / 64 |
| Maximum input length / legal slots | 1,024 / 64 |
| 기본 route epsilon / prior strength | 0.02 / 1.0 |
| Program bank | `native_v4`, 68개 기존 후보 |
| Checkpoint | 해당 단계의 고정 마지막 step |
| Pretrained checkpoint | 사용하지 않음 |
| Encoding | Bidirectional, `causal=False` |
| 기본 구현 profile | `native_v4_compact`, `injection='retrieval'` |

Negative query slot을 고를 때 training annotation의 field count를 사용하는 것은 supervised training sampler의 동작이다. 모델 입력으로 field count를 제공하는 것은 아니다. 예측 단계에서는 모든 메시지에 공개 slot 64개를 동일하게 평가한다.

일반 On은 presence/source/program/endpoint loss 가중치가 모두 1이다. `aux_small`은 앞 세 항 0.25, `aux_large`는 앞 세 항 4이며 endpoint는 항상 1이다. `axis_direct`는 program 항을 다섯 축 CE 평균×4로, `equivalent_program`은 정답 source에서 정답 목적지를 만드는 유효 program 집합의 확률합 NLL로 바꾼다. 모든 weighted component는 `curve.json`에 기록되며 합계가 실제 differentiated total과 같아야 한다.

Off는 endpoint NLL만 사용한다. Native endpoint path에 해당하는 allow-list 밖의 parameter에는 gradient가 없어야 하고, auxiliary state hash가 학습 전후 같아야 한다.

## 8. 예측·확률·F1과 저장물

### 8.1 예측 봉인

`evaluate16.py`의 재사용 evaluator는 clean input만 받아 메시지마다 slot 64개를 16개씩 예측한다. Raw byte hash와 input key 집합을 검증한 뒤, annotation을 읽기 전에 `.npz`와 `PREDICTION_SEAL.json`을 만든다. 이후 gold로 점수를 계산한다.

저장되는 probability array는 `base`, `final`, `source`, 예측 source에서의 program 분포, presence, 사용 가능한 route다. 전체 `slot × byte × program` tensor를 파일에 저장하는 구조는 아니다. **정답 source 조건부 program 확률**은 예측 seal 이후의 별도 `STAGES.jsonl` 진단에서 얻는다.

END/NULL은 서로 다르며, abstain 실패 상태와 혼합하지 않는다. 정답 endpoint가 존재하는 field query의 probability score에 presence probability를 곱하지 않는다.

### 8.2 F1 threshold

On의 presence threshold는 source protocol들의 limited development에서만 고른다. 탐색 범위는 0.05부터 0.95까지 0.05 간격이며, source-protocol macro exact typed-field F1로 선택한다. 동률이면 더 큰 threshold다.

F1은 `(start, end, semantic)` exact multiset matching이며, source/program argmax를 이용한 기존 field decoder를 사용한다. Endpoint 확률·Hit@1·NLL과는 다른 task다. Off의 field head는 훈련하지 않았으므로 field F1은 N/A다. 이를 측정된 0으로 대체하지 않는다.

### 8.3 Run 폴더

```text
screen/<source_pair>/<backbone>__<variant>__<seed>/
refine/<source_pair>/<backbone>__<variant>__<seed>/
final/<target>/<backbone>__<variant>__<seed>/
```

| 저장물 | 내용 |
|---|---|
| `model.pt` | Variant/backbone, config, bank fingerprint, weights, metadata |
| `TRAINING.json` | 초기/최종 hash, sample-stream hash, loss 가중치, parameter 수, 환경, optimizer |
| `curve.json` | 매 step의 실제 weighted loss component, total, gradient norm |
| `validation/<protocol>/` | Screen/Refine의 sealed development 예측·점수 |
| `development/`, `THRESHOLD.json` | Final On의 source-only threshold 선택 |
| `evaluation/` | Final의 sealed target 예측·점수 |
| `STAGES.jsonl` | Source/program/route/final의 사후 분해 |
| `FIELDS.jsonl`, `FIELD_METRICS.json` | On field 예측 및 별도 F1 |
| `COMPLETE.json` | 해당 run 산출물 전체 hash seal |

`TRAINING.json`의 `gradient_active_parameters`는 해당 run에서 `.grad is not None`이었던 parameter tensor의 크기를 합한 값이다. 전체 `parameters`와 구분한다. 일부 row만 사용한 embedding도 tensor 전체가 집계될 수 있으므로, FLOPs나 실제 활성 scalar 수로 읽지 않는다. Smoke의 같은 개념은 `parameters_with_gradient`라는 이름으로 저장된다.

## 9. 집계·그림·검증

이 단계는 `GRID_COMPLETE.json`이 있고 모든 최종 run 검증이 끝난 뒤 수행한다.

```bash
"$v17_python" aggregate17.py
"$v17_python" plot17.py
"$v17_python" verify_figures17.py
```

집계는 sealed prediction과 source-only 선택 파일을 검증하고, 일반 endpoint metric, semantic/relation 분해, stage, F1, paired gain, sanity reference를 정리한다. 예상 저장물은 `SUMMARY.json`, `AUDIT.json`, `TABLES.md`, `tables/*.tex`다.

`plot17.py`는 Matplotlib의 noninteractive `Agg` backend를 사용한다. 수치 그림은 `figures/`의 PNG/PDF/SVG로, 통합 PDF는 다음 경로로 출력한다.

```text
output/pdf/LAPA_formula_search_v17.pdf
```

그림 구성에는 전체 30개 후보의 screen 점수, source-only 선택표, 최종 p/Hit@1/NLL, DNS/SMB2 세부 relation, source/program 진단, 별도 field F1, paired gain이 포함된다. Screen 수치를 최종 target test 수치처럼 표시하지 않는다. 최종에는 Off/Hybrid/확률 선택/NLL 선택 역할을 표시하고, 같은 실제 후보가 두 역할을 맡으면 별도 학습 모델로 중복 집계하지 않는다.

`verify_figures17.py`는 plotting 함수를 import해서 같은 계산을 반복하는 방식이 아니라, summary와 paired seed 자료에서 표시할 수치·라벨을 독립 재구성한다. PDF text와 파일 hash도 확인하지만, **글자 겹침·잘림·여백 같은 시각 품질을 보장하지 않는다.** 통합 PDF의 모든 페이지를 render해서 별도로 확인해야 한다.

원본 PDF/그림을 재생성하면 파일 hash와 manifest가 바뀔 수 있다. 완성된 논문 산출물을 무심코 덮어쓰지 말고 기존 것을 먼저 보존한 후 재생성 이력을 남긴다. `FIGURE_AUDIT.json` 같은 create-once 출력이 이미 있으면 같은 이름으로 재실행하는 것도 거부될 수 있다.

확률·NLL·Hit@1의 seed CI는 3개 final seed를 사용한다. Student-t df=2에 따른 넓은 구간은 표본 수의 한계를 반영한다. 이는 training-seed 변동성이지, protocol 모집단·capture 모집단에 대한 불확실성 추정은 아니다. 작은 seed 수와 historical test라는 경계는 보고서에도 남겨야 한다.

## 10. 기존 논문 코드·공동작업 패키지로 이관할 때

### 10.1 Checkpoint는 variant와 backbone을 함께 복원

`model.pt`의 schema는 `lapa-formula-search-v17`이다. 일반 `LapaModel` 또는 v16 `FormulaModel`로 구조를 추측해 불러오지 않는다.

```python
import torch
from models17 import SearchModel

checkpoint = torch.load("<검증한 run의 model.pt>", map_location="cpu", weights_only=True)
assert checkpoint["schema"] == "lapa-formula-search-v17"
model = SearchModel(checkpoint["variant"], checkpoint["backbone"])
assert model.bank.fingerprint == checkpoint["bank_fingerprint"]
assert model.config.to_dict() == checkpoint["config"]
model.load_state_dict(checkpoint["state_dict"], strict=True)
model.eval()
```

CNN/GRU 후보의 schedule backbone은 `none`이다. Config 내부의 attention 값만 보고 TAPE Transformer checkpoint로 복원하면 안 된다. `variant`와 `backbone`을 함께 사용한다.

### 10.2 공개 package default를 조용히 바꾸지 않기

- `lapa-attention`의 기본 API/기존 model forward는 유지한다.
- 선택된 연구 후보를 package에 넣으려면 opt-in config, checkpoint schema, bank ID, forward-output 의미를 별도 version으로 문서화한다.
- Native final QK가 없는 후보의 `base`는 uniform reference일 수 있다. 이것을 기존 QK 성능이라고 잘못 해석하지 않도록 API metadata를 유지한다.
- `attr_only`와 CNN/GRU의 `*_attr`가 모두 “전체 QKV-free”라는 이름으로 합쳐지지 않도록 한다.
- CoPE/TAPE는 현재 package의 `native_v4_compact` 구현이다. 원 논문 전체 architecture를 그대로 재현했다고 범위를 넓혀 표현하지 않는다.
- Bank의 mask/guard/adjacent 연산 prior와 positive program exposure를 구분한다. 새 protocol 또는 새 연산을 추가하면 별도의 데이터·코드 계약이 필요하다.
- Third-party notice, 코드 출처, 데이터 사용 권한은 기존 package 문서와 원본 manifest를 함께 유지한다. 연구 실험 폴더를 공유한다고 원본 capture의 재배포 권한이 새로 생기지는 않는다.

### 10.3 과거 비교 모델 수치를 새 결과에 섞지 않기

이 v17은 LAPA 수식·encoder·loss 탐색이다. 과거 BinaryInferno/FieldHunter/BinPRE/SAGENET 등에서 나온 값을 이번 split/학습 조건으로 새로 계산한 것처럼 삽입하지 않는다. 같은 평가 조건으로 다시 측정하지 않은 모델은 과거 결과임을 구분한다. Always END/NULL/Uniform은 기존 논문 모델이 아니라 sanity reference다.

최종 후보가 source-only 선택 기준에서 우수하더라도 모든 task/backbone에서 보편적 최적이라는 뜻은 아니다. 예상과 다른 결과도 그대로 보존하는 것이 재현 계약의 일부다.
