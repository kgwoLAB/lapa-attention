> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# v18 작업 로그

모든 시간은 UTC. 기존 v17 및 배포 패키지는 수정하지 않는다. 평가 결과를 보고 seed, 수식, 학습량을 변경하지 않는다.

## 2026-09-13 — P01–P04 구현

- 사용자 정정 반영: attributes→Q/K가 아니라 source/width/endian/base 네 분포를 직접 실행·집계한다.
- 모든 encoder 2층 및 final readout을 새 네 요인 구조로 교체. Q/K 내적·별도 program/sign/mask 학습 head 없음. V/output·FFN·residual은 유지.
- direct/sink 두 고정 수식. width4 × endian2 × base7의56칸 중42개 합법 후보. DNS/SMB2 고정 실행 사전 지식 공개.
- Presence/source/attributes/endpoint 네 loss 그룹. Attribute는3축 NLL 합이며 width1 endian은 동치 주변화.
- 실제 기존 capture/data sampler와600step/3seed/3-source 계약을 참조하는 독립 실행기 작성.

## 2026-09-13 05:39–05:42 — P05–P07 검증

- CPU 및 CUDA smoke 모두 PASS. 각 mode31,041 parameters.
- 실제 TRAIN8메시지34필드의 정답 실행과 기존 native executor 일치. Synthetic observed packet 사용 없음.
- 모든 encoder/readout 네 factor와 V에 endpoint gradient 도달. QK 표준 호출 차단 상태에서 forward/backward 성공.
- 확률 정규화, nonzero padding 불변성, END/NULL와 invalid 분리, 음성 slot loss 처리, checkpoint roundtrip 통과.
- Evaluator는64slot raw-only 예측을 먼저 봉인한 다음 gold로 채점. 정답 source/axis는 forward 입력이 아님.
- 별도 TRAIN-only evaluator smoke에서 direct/sink valid_mass 저장·집계·범위 검사 통과.

## 2026-09-13 — P08 동결 및 P09–P12 실행 시작

- `freeze18.py`로 코드10개(계획 포함), upstream code/data 계약 및 기존96개 Off/Hybrid 대조군 TRAINING/COMPLETE hash를 고정.
- 기존 대조군의 COMPLETE 전체 산출물 hash를 실제 검증한 후 동결. v18에서는 target threshold/checkpoint/formula 선택 없음.
- `run18.py` CUDA 2worker로24개 작업을 시작. 각600updates, 총14,400updates. 각 작업 stdout·단계·곡선·학습 메타데이터·봉인된 예측을 보존.
- 완료 작업 재실행은 검증 전용이며, 부분 실패 발생 시 새 작업을 멈추고 진행 중 작업을 완료한 뒤 원본을 보존하도록 처리.

## 2026-09-13 05:57 — P09–P10 완료, 전체16/24

- DNS6개 및 Modbus6개 완료. TLS4개 추가 완료,2개 진행 중, SMB2는 후속6개 예정.
- 각600update와 sealed target inference/score 완료. 실패0; 완료 시점까지 계약 변경 없음.
- 기존 lapa-attention `git status --short` 출력 없음. 새 실험은 독립v18에만 기록.
- 후처리 수치·LaTeX 표·독립 감사·Matplotlib9개 그림의 생성 코드를 병행 준비했다. 최종 수치는 전체24개 완료 후 집계한다.

## 2026-09-13 05:59 — P09–P14 전체24/24 완료

- DNS/Modbus/TLS/SMB2 각6개, 총24개 신규 모델/14,400updates 완료. 실패·중간 재시도·예산 변경 없음.
- 모든 모델의600step 학습과64slot raw-only inference seal, gold 사후 채점 완료.
- 각 target/seed마다 기존8개 Off/Hybrid와 source 목록·stream hash 일치 및 기존 COMPLETE artifact hash 확인.
- 최종 target 결과를 보고 수식/seed/학습량을 바꾸지 않고 집계 및 독립 감사를 시작했다.

## 2026-09-13 — P15–P17 완료

- 독립 감사 PASS: 신규24개/기존96개,14,400유한 loss행,12개 sample stream재생,12쌍초기화,NPZ2,220개 및 endpoint10,410건 재계산 일치.
- Source-bound의17개 그룹도 독립 재계산. DNS pointer Sink의 endpoint 확률 상승을 true-source 해석 성공으로 부르지 않도록 기여 하한을 보고서에 명시.
- Macro/micro/core6개/relation11개/INTERIOR·END·NULL과17개 paired 대비, LaTeX24개 표 생성. 새 수식의 전체 성능 하락도 그대로 보존.
- Matplotlib9개 PNG/SVG와9페이지 vector PDF 생성.9페이지 모두 실제 렌더링을 직접 열어 글자·범례·표·CI 간격을 확인.
- 작은 양의 확률이0.0000으로 보이는 표기만 scientific notation으로 변경. Summary/예측/모델 수치는 변경하지 않았고, 최종9페이지를 다시 렌더링·시각 확인.
- 독립 그림 감사 재실행 PASS: 숫자390칸, paired16효과 및 실제 SVG errorbar 좌표,9페이지,248hash검증.
- FORMULAS/REPRODUCTION/REPORT에 정확한4요인·V유지·고정prior·loss·결과·비인과적 비교 한계를 기록.

## 2026-09-13 — P18 최종 인계

- 보고서 및 실제 LaTeX24개 독립 감사 PASS:246data rows,822숫자,표구조·환경·중괄호·열 수·hash 검증. TeX compiler를 실행했다고 주장하지 않으며 한글 caption2개의Unicode 요구를 명시.
- 보고서의 핵심 수치, 98.057% 확률질량 하한, source/operator 노출 및 capture 제약을 원본에서 다시 확인.
- 모든 체크리스트를 갱신하고 `finalize18.py --visual-review-confirmed`로 최종 산출물·24run seal·실제9페이지 시각 검수 근거를 봉인한다.
- 최종 모델·수치·PNG/SVG/PDF·로그는 보존한다. 시각 검수용 `tmp/pdfs/review-1.png`부터 `review-9.png`까지9개 임시 렌더만 최종 해시 기록 후 정리한다. 원본 PDF에서 다시 생성할 수 있다.
- 기존 v17 및 lapa-attention tracked 파일은 변경하지 않았다. 후속 제안은 이번 완료 실험에 포함하거나 기본 모델에 자동 적용하지 않는다.
