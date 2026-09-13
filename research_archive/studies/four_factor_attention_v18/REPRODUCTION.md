> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# v18 Four-factor attention 재현 안내

이 문서는 실제 frozen v18의 실행·검증·복원 절차를 설명한다. 현재 완료 여부나 성능은 주장하지 않는다. 진행 상태는 `GRID_PROGRESS.json`, 최종 완료는 `GRID_COMPLETE.json`과 개별 run seal에서 확인한다.

## 1. 실험 범위

- Source/width/endian/base 네 factor로 **모든 encoder layer와 최종 readout**의 attention을 만든다.
- Dot-product QK, 기존 attention backbone, program classifier, learned sign/mask head는 없다. Learned V는 유지한다.
- `direct`와 `sink` 두 mode를 모두 처음부터 학습한다. Target 결과를 이용한 mode 선택이나 development 기반 조정은 없다.
- **합성 프로토콜 없이** 실제 DNS/Modbus/TLS/SMB2를 사용한다.
- 3개 protocol train → 나머지 1개 protocol evaluation을 네 번 수행한다.
- `4 targets × 2 modes × 3 seeds = 24개` 새 모델, 모델당 600 update, 합계 14,400 update다.

V17과 달리 30개 후보 screening/refinement 단계는 없다. V18 두 모델을 RoPE/CoPE/TAPE/SDPA에 각각 붙였다고 이름을 바꾸거나, 24개를 96개 신규 실행으로 세지 않는다.

## 2. 작업 경로와 Python

```bash
v18_taskdir=WORKSPACE/openAI/packet_attention_v3m/paper/more_experiement/source_destination_decomposition/prior_method_field_study_v2/four_factor_attention_v18
v18_python=WORKSPACE/experiments/.venv/bin/python
cd "$v18_taskdir"
```

`common18.py`는 인접한 `formula_search_v17`, 그곳에서 참조하는 v16, workspace의 `lapa-attention/src`에 의존한다. 이 폴더 하나만 복사한 독립 package가 아니다.

현재 사용 환경은 Python 3.12.3 및 PyTorch 2.13.0+cu130 환경이다. 실제 실행 기록의 `TRAINING.json`에 PyTorch 버전과 device를 남긴다. GPU 노출 상태는 다음으로 확인한다.

```bash
"$v18_python" -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available())"
```

학습은 CUDA가 없으면 실패하도록 되어 있다. CPU로 조용히 전환하거나 step을 줄이지 않는다. 제한된 sandbox가 GPU device를 노출하지 않는다면 GPU 권한이 있는 실행 환경에서 확인해야 한다.

코드는 `torch._native.registry.deregister_op_overrides(disable_dsl_names='triton')`를 사용한다. 이 private API를 포함한 환경 의존성을 다른 PyTorch 버전에서도 당연히 지원한다고 가정하면 안 된다. 다른 환경으로 이관하면 별도 smoke와 새 provenance를 남긴다.

학습 worker의 설정은 CPU threads 2, CUDA memory fraction 0.35, TF32 off다. Queue는 **2 worker 고정**이며 `--workers` 옵션이 없다. Smoke CUDA memory fraction은 0.20으로 학습과 다르다. 메모리 비율은 실제 GPU의 가용 공간·다른 프로세스와 함께 확인해야 한다.

## 3. 고정 데이터와 대조군

데이터를 새로 생성하거나 v18에 다시 복사하지 않고, v17의 frozen `DATA_CONTRACT.json`과 `data/clean`, `data/gold`를 참조한다. 다음 세 split을 그대로 유지한다.

| Protocol | Train 메시지 | Development 전체 | Evaluation 메시지 / field |
|---|---:|---:|---:|
| DNS | 1,000 | 262 | 38 / 266 |
| Modbus | 1,000 | 139 | 6 / 6 |
| TLS | 1,000 | 80 | 15 / 15 |
| SMB2 | 89 | 41 | 15 / 60 |

Evaluation 전체는 74개 메시지, 347개 field다. V17의 development subset manifest는 보존하지만 v18 학습/선택에는 사용하지 않는다. 이 평가 자료는 과거에 분석한 historical test이므로 새로운 blind confirmatory test라고 표현하지 않는다.

새 모델과 비교하는 v17 Off/Hybrid 대조군은 `4 targets × 4 backbones × 2 modes(Off/Hybrid) × 3 seeds = 96개` 기존 run이다. Source 목록, seed, 600 update, 실제 sample-stream hash, 학습/예측/완료 artifact hash를 검증한 경우에만 재사용한다.

이 대조군은 이번에 새로 학습한 것이 아니다. V18 24개와 재사용 96개를 합친 비교 대상은 120개 distinct run이다. 같은 seed라도 구조가 다른 전체 초기 weight가 동일하다는 뜻은 아니다.

## 4. Frozen 계약: 현재 작업에서는 검증부터

`CONTRACT.json`에는 다음이 들어 있다.

- Frozen v18 코드와 `PLAN.md` hash.
- V17 코드/데이터 계약 hash와 기존 Off/Hybrid control의 학습/완료 hash.
- 24개 scheduled job, seed, update 수, 두 mode.
- Executor의 seven-base manifest와 fingerprint.
- Freeze 시 확인한 CPU/CUDA smoke 기록의 hash.

현재 frozen 폴더에서 실행 가능한 읽기 전용 검증 명령은 다음과 같다.

```bash
"$v18_python" -c "from common18 import verify_contract; verify_contract(); print('Frozen code/data/control contracts verified')"
```

Grid가 완료된 후에는 개별 run과 전체 예정 job을 읽기 전용으로 검증할 수 있다.

```bash
"$v18_python" -c "from common18 import verify_contract; from run18 import verify_completed_grid; verify_contract(); verify_completed_grid(); print('Completed grid verified without training')"
```

두 번째 명령은 `GRID_COMPLETE.json`이 있어야 한다. 완료 전에는 실패한다. 현재 진행 파일을 읽는 명령은 다음과 같다.

```bash
"$v18_python" -c "from common18 import ROOT, read, json; print(json.dumps(read(ROOT/'GRID_PROGRESS.json'), indent=2))"
```

**현재 폴더에서 freeze를 다시 하거나 run/기존 log를 덮어쓰지 않는다.** 코드·loss·mask·seed·예산 변경을 원래 실험처럼 섞지 않는다.

## 5. 처음 실행할 때의 순서

아래는 별도의 아직 봉인되지 않은 재현 작업 사본에서의 절차다. 현재 frozen 작업을 초기화하는 명령이 아니다.

### 5.1 TRAIN-only smoke

```bash
"$v18_python" test18.py --device cpu --output SMOKE_CPU.json
"$v18_python" test18.py --device cuda --output SMOKE_CUDA.json
```

기존 출력이 있으면 덮어쓰지 않고 실패한다. 현재 계약에 묶인 smoke 파일을 바꾸지 않고 다시 점검하려면 `--output`을 생략한다.

```bash
"$v18_python" test18.py --device cpu
"$v18_python" test18.py --device cuda
```

Smoke는 실제 TRAIN의 protocol별 앞 두 메시지, 총 8개/34개 field만 사용한다. Development/evaluation을 읽지 않는다. 표준 attention API를 호출하면 실패하도록 patch한 상태에서 모든 forward를 검사하고, 구조상 program/sign/mask/QK head가 없는지 확인한다.

검사에는 모든 layer의 four-factor 분포, V의 endpoint gradient, 2 optimizer update, negative-label 무관성, END/NULL self-loop, padding, checkpoint roundtrip, width-1 endian 동치가 포함된다. CUDA absolute/relative 허용오차는 `1e-5`, CPU는 `3e-6`다.

### 5.2 한 번만 freeze

```bash
"$v18_python" freeze18.py
```

두 smoke가 PASS이고, `CONTRACT.json`과 `runs/`가 아직 없을 때만 가능하다. 기존 v17 대조군도 검증한 뒤 계약을 만든다. 계약 경로는 절대 경로이므로 다른 시스템으로 이동한 사본에서는 원 계약을 보존하고 별도 경로 provenance/계약을 만들어야 한다. Hash만 새 값으로 덮어써 원 run인 것처럼 보이게 하면 안 된다.

### 5.3 고정 queue 실행

```bash
"$v18_python" run18.py
```

Queue는 두 worker로 24개 job을 실행한다. 이미 돌아가는 queue가 있는데 같은 명령을 다시 실행하지 않는다. 개별 scheduled job의 예시는 다음과 같다.

```bash
"$v18_python" train18.py --target dns --mode direct --seed 170301
```

Source 목록은 `target`을 제외한 나머지 protocol로 코드에서 결정한다. 개별 명령은 해당 output folder가 아직 없고 다른 queue가 같은 job을 처리하지 않는 경우에만 사용한다.

`run18.py`를 **완료된** grid에 다시 실행하면 전체 artifact를 검증하고 모델을 재학습하지 않는다. 다만 `GRID_PROGRESS.json` 상태 파일은 갱신하므로 순수 읽기 전용 검증이 필요하면 4절의 `verify_completed_grid` 명령을 사용한다.

부분 run 폴더나 완료 seal 없는 log가 있으면 queue는 이를 보존하고 실패를 보고한다. 자동 삭제, silent retry, seed 추가, budget 축소를 하지 않는다. 이미 실행 중인 worker는 마무리·봉인할 수 있게 기다린다. 실패 원인을 조사하고 변경 여부를 기록한 후 재개 정책을 결정해야 한다.

## 6. 실제 학습 상수와 loss 의미

| 항목 | 고정값 |
|---|---|
| Seeds | 170301, 170302, 170303 |
| Mode | `direct`, `sink` |
| Update | 각 모델 600 |
| Batch | 16 query: positive 8 + negative 8 |
| Sampling | Source protocol 균등 → source message 균등 |
| Optimizer | AdamW, learning rate 0.002, weight decay 0.01 |
| Gradient clip | Norm 1.0 |
| Hidden / heads / layers / FFN | 32 / 4 / 2 / 64 |
| Max length / slot | 1,024 / 64 |
| Source scorer rank / receiver chunk | 12 / 16 |
| Route epsilon | 0.02 |
| Checkpoint | 마지막 600번째 update 고정 |
| Pretrained / target tuning / development selection | 모두 없음 |

Loss는 `presence + source + attributes + endpoint` 네 그룹이며 가중치 모두 1이다. Attributes는 정답 training source에서 width/endian/base NLL을 **합산한 뒤** positive example 평균한다. Width 1에서는 endian 두 값이 같은 연산이므로 해당 항을 0으로 주변화한다. 별도 program classifier나 program-ID CE는 없다.

Presence만 positive/negative query 둘 다 학습한다. Negative query의 source/attribute/endpoint label은 무시한다. Negative query를 NULL 정답으로 학습시키지 않는다. Sampler가 supervised field count로 positive/negative slot을 선택하지만, 그 field count를 모델 input으로 전달하는 것은 아니다.

Layer마다 직접 별도의 정답 factor loss를 주는 설계가 아니라, 최종 네 objective가 encoder로 역전파되는 설계다. `curve.json`에는 실제 total과 각 그룹의 loss, gradient norm을 기록한다.

## 7. 저장물과 봉인 후 평가

```text
runs/<target>/<direct 또는 sink>__<seed>/
├── model.pt
├── TRAINING.json
├── curve.json
├── PROGRESS.json
├── evaluation/
│   ├── <message_id>.npz
│   ├── PREDICTION_SEAL.json
│   ├── diagnostics.jsonl
│   └── METRICS.json
└── COMPLETE.json
```

`evaluate18.infer`는 clean row의 key가 `message_id`, `data_hex`, `byte_length`, `raw_sha256` 네 개뿐인지 검사한다. 모든 메시지에 공개 slot 64개를 8개씩 적용하며 `diagnostics=False`로 실행한다. 정답·protocol ID를 forward에 넣지 않는다.

NPZ는 다음 일곱 array를 저장한다.

| Array | Shape | 의미 |
|---|---|---|
| `final` | `[64,n+2]` | 최종 목적지 확률 |
| `source` | `[64,n]` | Head-mean source 분포 |
| `width` | `[64,n,4]` | Source별 head-mean width factor |
| `endian` | `[64,n,2]` | Source별 head-mean endian factor |
| `base` | `[64,n,7]` | Source별 head-mean base factor |
| `presence` | `[64]` | 해당 ordinal field 존재 확률 |
| `valid_mass` | `[64]` | 정규화/smoothing 이전 readout 유효 질량의 head 평균 |

모든 예측 파일을 raw hash/config/executor fingerprint와 함께 봉인한 후 `score`가 gold를 읽어 점수를 계산한다. Complete 64-slot 배열 전체의 shape·범위·정규화를 검사하며, `presence`와 `valid_mass`는 slot별 scalar이므로 slot 전체 합 1을 요구하지 않는다.

Endpoint probability에 presence probability를 곱하지 않는다. Source 및 세 축 진단은 봉인 이후 정답 source를 인덱싱한 값이다. 이 head 평균 factor들을 곱해 final 확률을 재구성해서는 안 된다. 실제 모델은 head별 곱·실행·정규화 후 평균하기 때문이다.

지표는 overall, protocol, semantic, relation, INTERIOR/END/NULL로 분해한다. NLL의 probability floor는 `1e-30`이다. 현재 evaluator는 field F1과 threshold 선택을 구현하지 않는다.

집계에서는 `base_axis_p`가 v18 base 축 확률이고, v17 `base_p`는 목적지 QK 확률이라는 이름 차이를 보존한다. Width 1은 raw canonical `endian_p`와 두 동치 endian을 합한 `endian_equivalence_p`를 구별한다.

## 8. Checkpoint를 CPU에서 정확히 복원

원하는 run의 `COMPLETE.json` hash를 먼저 검증한 후 다음과 같이 읽는다. Placeholder는 실제 검증한 파일 경로로 바꾼다.

```python
import torch
from model18 import FourFactorModel

checkpoint = torch.load("<검증한 run의 model.pt>", map_location="cpu", weights_only=True)
assert checkpoint["schema"] == "four-factor-attention-v18"
model = FourFactorModel(**checkpoint["config"])
assert model.executor.fingerprint == checkpoint["metadata"]["executor_fingerprint"]
model.load_state_dict(checkpoint["state_dict"], strict=True)
model.eval()
# 실제 원시 입력은 ModelInputs(data, observed, slots)로 별도 구성한다.
# with torch.no_grad():
#     output = model(inputs, diagnostics=False)
```

CUDA에서 저장한 state도 `map_location='cpu'`로 옮긴다. 기존 `LapaModel`, v16 `FormulaModel`, v17 `SearchModel`로 읽으면 안 된다. Mode는 config에 포함되어 있으므로 `direct/sink`를 임의로 추측해 바꾸지 않는다.

이 checkpoint는 현재 workspace 의존 연구 클래스용이며, 배포 package의 기본 모델로 자동 등록되지 않는다. 공개 API로 이관하려면 별도 config/schema/manifest 및 테스트를 마련하고, 기존 기본값을 조용히 덮어쓰지 않는다.

## 9. 집계와 그림 생성

학습 완료 후 먼저 전체 grid를 검증한다. 집계는 새 모델 24개와 검증한 과거 control 96개의 동일 field를 비교한다.

```bash
"$v18_python" aggregate18.py
```

이 명령은 `SUMMARY.json`, `TABLES.md`, LaTeX tables를 생성하며 기존 표를 조용히 덮어쓰지 않는다. 독립 검증으로 `INDEPENDENT_AUDIT.json`이 PASS인 것을 확인한 뒤에만 plotting을 수행한다.

```bash
"$v18_python" diagnose18.py
"$v18_python" audit18.py
"$v18_python" plot18.py
"$v18_python" verify_figures18.py
```

`diagnose18.py`는 Sink의 true-source 기여 상한과 다른 source 기여 하한을 사후 계산한다. 학습이나 수식 선택이 아니며 기존 출력이 있으면 덮어쓰지 않는다. `audit18.py`는 run/예측/지표/진단을 독립 검증한다. 이미 완료된 결과에서는 생성 명령을 다시 실행하지 말고 기존 seal을 확인한다. LaTeX에는 `booktabs`가 필요하며 두 overall caption의 한글을 조판하려면 한글/Unicode 지원 환경이 필요하다. 이번 작업에서는 TeX compiler를 사용하지 않았다.

Plot은 Matplotlib PNG/SVG와 다음 통합 vector PDF를 생성한다.

```text
output/pdf/LAPA_four_factor_attention_v18.pdf
```

완성된 그림/PDF를 재생성하면 hash가 바뀔 수 있고 기존 파일을 덮어쓸 수 있으므로, 이전 산출물을 보존하고 재생성 이력을 남긴다. 이 문서를 작성하면서 PDF를 생성한 것은 아니다. 실제 그림의 값·라벨·페이지 layout 검증은 별도 완료 절차다.

전체 macro는 seed별로 각 protocol의 field 평균을 먼저 구한 뒤 네 protocol을 동등 평균하고, 마지막에 세 seed를 평균한다. Micro와 다르다. CI는 세 training seed의 Student-t 95% 구간(df=2)이며 범위를 자르지 않는다. Capture 또는 unseen-protocol 모집단의 불확실성을 추정하는 CI가 아니다.

## 10. 비교 해석과 배포 시 경계

- QK dot-product를 제거했다는 구조적 사실과 성능 개선 여부는 별개다.
- 같은 sample stream·step을 맞췄어도 architecture, seven-base prior, loss, parameter 수, FLOPs가 다르다. 결과를 QK 제거 하나의 인과효과라고 해석할 수 없다.
- Masked14와 SMB2 companion/NULL 연산은 고정 사전 지식이다. Unseen protocol이 곧 unseen operator 사전이라는 뜻은 아니다.
- Actual NULL은 invalid/sink/negative query와 다르다. Encoder에서는 END/NULL 질량을 self-loop로 보내지만 최종 출력에서는 구분한다.
- Modbus/TLS의 END shortcut, DNS slot 노출 이동, held-out 연산의 양성 감독 부재, 작은 test 표본을 함께 해석한다.
- 기존 BinaryInferno/FieldHunter/BinPRE/SAGENET 수치를 v18 조건에서 재학습한 것처럼 넣지 않는다. 이번 재사용 대상은 검증된 v17 Off/Hybrid 96개다.
- Historical captures와 외부 코드의 사용·재배포 권한은 원 manifest와 package의 third-party notice를 따른다. 폴더 복사가 새 데이터 재배포 권한을 부여하지 않는다.
- 다른 데이터·새 base operator·signed displacement·추가 head·학습 예산 변경은 새 계약과 실험 lineage로 분리한다. 두 mode의 불리한 결과도 보존한다.
