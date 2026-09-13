> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# v16 재현 및 코드 사용

## 실험 모델 사용

기존 `lapa-attention` 기본값과 공개 checkpoint 형식은 바꾸지 않았다. 실험용 모듈을 opt-in으로 사용한다. 설치된 PyTorch 환경에서 두 경로를 Python import path에 추가한다.

```python
import sys
from pathlib import Path

workspace = Path('WORKSPACE')
study = workspace / 'openAI/packet_attention_v3m/paper/more_experiement/source_destination_decomposition/prior_method_field_study_v2/formula_search_v16'
sys.path.insert(0, str(workspace / 'lapa-attention/src'))
sys.path.insert(0, str(study))

from models16 import FormulaModel
from losses16 import formula_loss

model = FormulaModel('route_joint', backbone='tape')
output = model(batch.inputs)  # raw bytes / observed mask / public ordinal slot only
loss, components = formula_loss(model, output, batch.labels)
```

`route_sink`, `route_direct`, `route_axis`, `route_joint`는 최종 QK가 없지만 encoder QKV는 유지한다. `cnn_joint`는 전체 QKV가 없다. `hybrid`/`off`는 기존 forward와 정확히 같다. 다른 attention 이름을 지정할 수 있는 코드 인터페이스와 실제 실행한 TAPE 기준 실험을 혼동하지 않는다: RoPE/CoPE/SDPA 결과는 이번 실행으로 검증하지 않았다.

## 체크포인트 읽기

새 실험 checkpoint는 `lapa-formula-search-v16` schema와 variant를 저장한다. 기존 패키지의 `load_checkpoint`에 넣지 않는다.

```python
import torch

payload = torch.load(checkpoint_path, map_location='cpu', weights_only=True)
assert payload['schema'] == 'lapa-formula-search-v16'
model = FormulaModel(payload['variant'], payload['backbone'])
assert model.bank.fingerprint == payload['bank_fingerprint']
model.load_state_dict(payload['state_dict'], strict=True)
model.eval()
```

## 실험 진입점

Python은 `WORKSPACE/experiments/.venv/bin/python`을 사용했다. 현재 디렉터리에서 실행한다.

```bash
python test16.py --device cpu
python test16.py --device cuda
python run16.py --workers 4
python aggregate16.py
python plot16.py
```

- `run16.py`는 완료된 실행의 해시를 확인해 건너뛰고 이어 간다. 이미 있는 partial run을 덮어쓰지 않는다. 원인을 확인하고 별도 보존/재시작 결정을 해야 한다.
- `prepare16.py`는 최초 계약 생성용이며 기존 계약/데이터를 덮어쓰지 않는다. 완전히 새 재현은 별도 연구 폴더에서 계획과 코드/데이터 계약을 새로 고정해야 한다.
- CPU/GPU smoke는8개 실제 TRAIN 메시지/34개 필드만 사용한다. 본 학습은 GPU 전용이며 임의로 CPU로 바꾸거나 step을 줄이지 않는다.
- optional Triton op override는 기존 실험과 동일하게 끄고 ATen CUDA를 사용한다. TF32는 끈다. 환경/실행 seed/step/active parameter/학습 stream hash는 각 TRAINING.json에 저장한다.
- Matplotlib 원본 그래프는 PNG200dpi/SVG, 묶음은 `output/pdf/`에 저장한다. PDF를 다시 만들었으면 반드시 다시 렌더링해 시각 검증한다.

## 해석 시 필수 구분

- `SELECTION.json`: target의 dev/test를 제외한 내부2→1 검증으로 선택한 수식. target마다 달라질 수 있다.
- `search/`:250 update 탐색 결과. `final/`:600 update,새seed3개,3→1 결과. 두 표의 수치를 직접 같은 학습 예산으로 비교하지 않는다.
- `evaluation/*.npz`:64개 query 전체의 raw-only 예측. 그 뒤 `diagnostics.jsonl`에서 정답 query 위치에 해당하는 목적지 확률을 점수화한다.
- `STAGES.jsonl`:봉인 후 true source를 인덱싱한 program 진단. true source/program을 모델에 입력하지 않는다.
- route-only의 `base` 배열은 legacy API용 uniform reference이며 learned QK 성능이 아니다. `base_kind`를 반드시 확인한다.
- `FIELD_METRICS.json`:확률과 별개의 typed exact span **multiset** F1. 중복 예측도 FP로 센다. Off는 discovery head 미학습으로 N/A다.
- confidence interval은3개 seed 평균에 대한 df2 t-구간이다. packet/capture 모집단 또는 모든 unseen protocol에 대한 신뢰구간이 아니다.
