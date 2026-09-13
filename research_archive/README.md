# LAPA 연구 보관 묶음

실험의 성공·실패와 구현을 읽을 수 있도록 만든 **GitHub 공개용 사본**입니다.
프로젝트 소유 부분의 라이선스는 Apache-2.0이며 새 실험은 아닙니다. 개발 보류의 이유와 연구 해석은
[프로젝트 상태](../docs/archive_status.md)에 있습니다.

## 보관 구조

```text
research_archive/
├── README.md
├── MANIFEST.json
└── studies/
    ├── formula_search_v16/
    ├── formula_search_v17/
    └── four_factor_attention_v18/
```

| 연구 | 읽을 문서 | 범위 |
| --- | --- | --- |
| v16 | [보고서](studies/formula_search_v16/REPORT.md), [수치표](studies/formula_search_v16/TABLES.md) | 초기 수식 비교 |
| v17 | [보고서](studies/formula_search_v17/REPORT.md), [수치표](studies/formula_search_v17/TABLES.md) | 확대 수식 탐색과 고정된 선택 과정 |
| v18 | [보고서](studies/four_factor_attention_v18/REPORT.md), [수치표](studies/four_factor_attention_v18/TABLES.md), [수식](studies/four_factor_attention_v18/FORMULAS.md) | Source/Width/Endian/Base 직접 attention, QK-free·V-retained |

각 폴더에 역사적 Python 소스, 설계·작업 로그·보고서, 집계 JSON, 기존 LaTeX 표와
Matplotlib 그림을 보존했습니다. 기존 파일 중 무엇을 포함했는지는
[MANIFEST.json](MANIFEST.json)에 전부 나열되어 있습니다.

v18은24개 신규 모델, 각600update의3→1 평가이며 같은 조건의 과거96개 대조군을
재사용했습니다. 이들을120개 신규 학습으로 세지 않습니다. 이전 연구와 중복되는
모델을 버전별 개수만 합쳐 독립 실험처럼 세면 안 됩니다.

## 원본과 배포 사본의 차이

- 원래 연구 폴더, 원시 데이터, 체크포인트, 예측 및 실패 기록은 변경하지 않았습니다.
- 원시 payload/JSONL/PCAP, tensor/weight, packet별 NPZ, 실행별 폴더, 전체 계약과
  원래 감사 JSON은 이 보관 묶음에 넣지 않았습니다.
- 연구 코드·문서·JSON의 개인 절대 경로는 `WORKSPACE` 또는 `USER_HOME` 형태로
  치환했습니다. 문서에는 배포 사본임을 알리는 안내를 추가했습니다.
- 숫자는 반올림·삭제하지 않았습니다. 큰 JSON은 파일당4MiB 이하의 부분 파일로
  나누며, `$archive_ref`는 생략 표시가 아니라 보존된 다른 JSON에 대한 참조입니다.
- 그림·표 등 그대로 복사 가능한 파일은 byte 단위 원본과 동일합니다. PDF는 새로
  그리거나 편집하지 않고 기존 산출물을 복사했습니다.
- Manifest는 원본의 workspace-relative 위치와 SHA-256, 배포 사본 SHA-256,
  변환 종류를 함께 기록합니다. 생성된 안내에는 대응 원본이 없음을 명시합니다.

`MANIFEST.json`은 exporter가 생성한209개 파일을 봉인합니다. 이 안내 README는
후속 작성한 문서이므로 그 목록 밖에 있습니다. 원본 계약의 hash가 남은 역사적
문서나 소스는 **현재 배포 사본이 그 원본 계약을 통과한다는 주장**이 아닙니다.

## 검증과 집계 읽기

저장소 루트에서, 원시 데이터나 PyTorch 없이 표준 Python으로 검사할 수 있습니다.

```bash
python scripts/prepare_research_archive.py --verify
```

분할 여부와 관계없이 JSON을 읽으려면 다음 helper를 사용합니다.

```python
from scripts.read_archive_summary import read_summary

summary = read_summary(
    "research_archive/studies/four_factor_attention_v18/SUMMARY.json"
)
score = summary["methods"]["four_factor_sink"]["overall_protocol_macro"]["metrics"]["p_true"]
print(score["mean"], score["ci95"])
```

v17도 같은 helper에 `research_archive/studies/formula_search_v17/SUMMARY.json` 경로를 주면 전체
구조를 복원합니다. Export 시에는 세 연구 각각의 복원 결과와 경로만 치환한 원본
SUMMARY가 완전히 같은지 확인했습니다. 공개 사본만으로 가능한 해시 검증과,
원래 비공개 예측/정답을 사용한 실험 재채점은 서로 다른 검증입니다.

## 실행 가능 범위와 공개 전 남은 사항

**역사적 학습 스크립트는 공개 clone만으로 재현되는 portable runner가 아닙니다.**
원래 workspace, 고정 contract, 비공개 split, 이전 모델들이 필요합니다. 치환된
경로를 임의로 복원하거나 hash 검사를 끄고 원래 실행을 재현했다고 주장하지 마세요.
기본 패키지의 작동 확인은 [루트 README](../README.md)의 예제를 사용하세요.

프로젝트 소유 코드·문서는 [Apache-2.0](../LICENSE)을 따르며 제3자 조건은
[출처 고지](../THIRD_PARTY_NOTICES.md)에 보존합니다. 데이터·가중치 재배포 승인은
별도입니다. 필요한 비공개 자료는 권한을 확인한 공동연구 채널에서 확보해야 합니다.
[공개 체크리스트](../docs/release_checklist.md)

새 결과를 만들려면 원본을 덮어쓰지 말고 별도의 실험 lineage에 기록하세요. 현재
exporter는 기존 출력이 있으면 재생성을 거부하며 `--verify`는 파일을 수정하지 않습니다.
