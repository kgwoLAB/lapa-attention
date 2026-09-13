# LAPA Attention / X-Route — Research Archive

바이트로 표현된 length·offset·pointer 관계를 다루는 attention 연구 코드입니다.
**현재 신규 개발은 보류하고, 구현과 긍정·부정 결과를 보존합니다.** 이것은 연구 상태의
표시이며 GitHub 저장소를 서버에서 read-only archive 처리했다는 뜻은 아닙니다.

현재 설계는 **학습하지 않은 프로토콜에서 올바른 source와 주소 연산을 선택한다는
핵심 주장을 충분히 입증하지 못했습니다.** LAPA의 가능성 전체가 반증되었다는 뜻은
아닙니다. [아카이브 상태와 결론](docs/archive_status.md)

## 어디부터 보면 되나요?

| 목적 | 위치 |
| --- | --- |
| 실행 가능한 SDPA/RoPE/CoPE/TAPE × LAPA Off/On | [패키지](src/lapa/), [예제](examples/) |
| 최종 four-factor 실험 결과 | [v18 보고서](research_archive/studies/four_factor_attention_v18/REPORT.md), [수치표](research_archive/studies/four_factor_attention_v18/TABLES.md) |
| Source·Width·Endian·Base 수식과 loss | [v18 수식](research_archive/studies/four_factor_attention_v18/FORMULAS.md) |
| v16 → v17 → v18 연구 이력 | [연구 아카이브](research_archive/README.md) |
| 공개 전 확인 사항 | [릴리스 체크리스트](docs/release_checklist.md) |

![같은 평가 필드에서의 정답 목적지 확률 비교](research_archive/studies/four_factor_attention_v18/figures/01_all_methods_numeric_probability.png)

실제 DNS·Modbus·TLS·SMB2의 **3개 학습 → 나머지1개 평가**, 3seed, 600updates
조건입니다. F1이 아니라 **정답 목적지 확률**입니다. DNS pointer의 확률 상승을 정답
source를 통한 연산 성공으로 해석하면 안 됩니다. 표본 수·NLL·Hit@1·source 기여
분석과 실패 결과는 보고서에 함께 보존했습니다.

## 구현과 재현 범위

| 구성 | 의미 |
| --- | --- |
| `src/lapa` | 초기 native-v4 compact bidirectional port. LAPA는 최종 retrieval에 결합하며 모든 encoder층에 삽입되지 않음 |
| v16 아카이브 | 초기 수식 비교의 역사적 코드·설계·결과 |
| v17 아카이브 | 확대 수식 탐색의 역사적 코드·설계·결과 |
| v18 아카이브 | 모든 encoder층/readout에서 QK 대신 source/width/endian/base를 직접 결합. 별도 program head 없음, V 유지 |

연구 아카이브는 **원래 workspace와 비공개 데이터·계약·체크포인트에 의존하는 기록용
snapshot**입니다. 아래 설치만으로 과거 전체 학습이 재현된다고 주장하지 않습니다.
초기 패키지의 joint-loss 기본값과 후기 비교의 **Off=endpoint NLL only** 조건도
다릅니다. 패키지 기본 CLI 결과를 v16–v18 결과로 대체하지 마세요.

## 설치와 데이터 없는 작동 확인

Python 3.10 이상이 필요합니다. 의존성 하한은 `pyproject.toml`을 따르며 모든 버전
조합에서의 호환성을 보장하는 뜻은 아닙니다. 아래 확인에는 CUDA가 필요하지 않습니다.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[plots]"
python -m unittest discover -s tests -t . -v
python examples/minimal_forward.py
python examples/compare_on_off.py
python examples/inspect_routing.py
```

기본 예제는 작은 고정 수치 텐서로 **미학습 API의 작동만** 확인합니다. 합성 프로토콜
벤치마크나 정확도 실험이 아닙니다. 승인된 로컬 데이터가 있다면 명시할 수 있습니다.

```bash
python examples/compare_on_off.py --data data/native_v4/evaluation.jsonl --index 0
```

```python
import torch
from lapa import LapaConfig, LapaModel, ModelInputs

model = LapaModel(LapaConfig(attention="tape", lapa_enabled=True)).eval()
data = torch.arange(16, dtype=torch.long)[None, :]
inputs = ModelInputs(data, torch.ones_like(data, dtype=torch.bool), torch.tensor([0]))
with torch.no_grad():
    probabilities = model(inputs)["final"]
# 작동 확인용 입력이며 성능 지표를 계산하지 않습니다.
```

## 데이터·가중치와 업로드 대상

- GitHub용: 소스, 설정, 테스트, 문서, 경로를 정리한 집계 결과, Matplotlib 그림·표.
- 로컬 보존/추적 제외: 실제 packet byte JSONL, DNS/x86 텐서, PCAP, 가중치, 실행별
  예측, 원본 자산 manifest·검증·reference 묶음, 생성 출력과 환경 파일.
- 원래 실제 데이터는 train 3,089 / development 522 / evaluation 74메시지이며 평가
  필드는347개입니다. **GitHub clone에 데이터와 가중치는 포함되지 않습니다.**
- 데이터 확보와 사용 권한은 [데이터 안내](data/README.md), [출처 고지](THIRD_PARTY_NOTICES.md)를 확인하세요.

추적 제외한 원본 파일과 이전 Git 이력은 로컬 전용 백업에 보존합니다. 새 공개
저장소에는 정리한 현재 파일만 포함하며 **이전 비공개 커밋 이력은 올리지 않습니다.**
커밋에는 개인 이메일 대신 GitHub noreply 주소를 사용합니다.

## 공개 전 확인

```bash
python scripts/prepare_research_archive.py --verify
python scripts/check_release.py --report
git diff --check
git status --short
```

현재 추적 파일과 ignore되지 않은 새 파일에서 원시 자산, 5MiB 초과 파일, 개인 홈 경로,
일부 credential 형식을 검사합니다. 완전한 보안·개인정보·권리 검토나 Git 이력 검사를
대신하지 않습니다. 큰 집계 JSON은 숫자를 생략하지 않고 분할해 보존합니다.

## 라이선스와 출처

프로젝트가 권리를 가진 코드·문서에는 [Apache-2.0](LICENSE)을 적용합니다.
제3자 고지는 [NOTICE](NOTICE)와 [라이선스 묶음](LICENSES/README.md)에 보존합니다.
이는 원시 데이터·가중치 또는 타인 소유 자료의 재배포 허가가 아닙니다.
CoPE의 공식 소프트웨어 라이선스는 확인되지 않았으며, 로컬 수식 구현을
공식 Meta 코드의 배포나 별도 권리 확보로 표현하지 않습니다.

공개 저장소는 [kgwoLAB/lapa-attention](https://github.com/kgwoLAB/lapa-attention)입니다.
연구 아카이브 상태를 유지하되 GitHub 서버의 읽기 전용 archive 전환은 하지 않습니다.
논문 작성자·출판 정보는 별도 확인 대상이며 인용 메타데이터는 초안입니다.

[아키텍처](docs/architecture.md) · [API](docs/api.md) ·
[원 구현과의 차이](docs/baseline_fidelity.md) · [재현 범위](docs/reproduction.md) ·
[작업 로그](WORK_LOG.md)
