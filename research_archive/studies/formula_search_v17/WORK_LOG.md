> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# v17 작업 로그

## P00 구현·설계

- 사용자의추가요청에따라v16의6수식에서30개후보로확대했다.
- 속성으로실제로Q/K를만드는readout,공유slot CNN/GRU,실행특징programscorer를독립구현했다.
- gate·normalization·lapa보조loss비중·실행동치supervision도별도후보로구현했다.
- p와NLL의최적후보를독립적으로선택한다. 속성QK후보는최소1개이상refine에승격한다.
- 모든후보실행은순차체크리스트/기계판독로그로관리하며최종test기반재선택은하지않는다.

## P01–P02

- Off+30개후보전체CPU/GPU 2-step검증통과. 원본Off/Hybrid4개backbone동일초기화forward검증통과.
- 실제8개TRAIN메시지/34필드만smoke에사용했다. 전체정답연산이실행동치집합에도포함됨을확인했다.
- 속성attention의endpointgradient가source와5축head까지실제로전달됨을확인했다.
- 62개코드파일과원본데이터계약을봉인했고,180개screen을4-worker GPU큐로시작했다.

## P02 완료 → P03 시작 (2026-09-13 13:20 KST)

- 180개 screen 모델을 모두 학습·봉인했다. 실패 없이 완료했다.
- 각 outer target의 dev/test를 제외한 inner source-only 점수로 승격했다.
- DNS 제외: hybrid, aux_small, attr_content, shared_slot_hybrid.
- Modbus 제외: hybrid, attr_content, shared_slot_hybrid, mix_entropy.
- TLS 제외: hybrid, gru_shared_attr, shared_slot_hybrid, attr_content.
- SMB2 제외: hybrid, attr_content, aux_small, weak_product.
- 중복 pair / formula / seed를 제거한 64개 refine 모델을 새 seed 2개, 400 update로 실행하기 시작했다.
- 집계·독립 감사 코드를 병행 준비했다. 12개 Matplotlib 그림의 수치 매핑과 레이아웃을 코드 검토했다. 아직 최종 test 결과를 집계하거나 그림으로 표시하지 않았다.

## P03–P04 완료 → P05 시작 (2026-09-13 13:30 KST)

- 64/64 refine 모델을 오류 없이 완료했다.
- Source-only 선택 결과를 SELECTION.json에 봉인한 뒤에만 최종 모델 큐를 시작했다.

| 최종 평가에서 제외할 target | P champion | NLL champion |
|---|---|---|
| DNS | aux_small | aux_small |
| Modbus | mix_entropy | hybrid |
| TLS | attr_content | shared_slot_hybrid |
| SMB2 | attr_content | attr_content |

- 네 backbone / 세 final seed / Off·Hybrid·선택 후보를 중복 제거하면 최종 156개, 전체 400개 고유 모델이다.
- Screen 21,600 + refine 25,600 + final 93,600 = 총 140,800 update다.
- 이 표는 inner validation에서 선택된 수식이며, 최종 target 성능이 우수하다는 결론은 아니다. 최종 결과를 보고 수식을 바꾸지 않는다.
- FORMULAS.md에 실제 30개 수식과 입력·loss·QKV 제거 범위를 상세히 기록했다.

## P05 완료 → P06–P07 시작 (2026-09-13 14:00 KST)

- GRID_COMPLETE.json: screen 180 + refine 64 + final 156 = 총 400개 모델 완료.
- 모든 실행이 실패·재시도 없이 완료됐다. 최종 모델 큐는 약 30.6분 걸렸다.
- 325개 완료 시점의 중간 독립 감사는 PASS_COMPLETED_SUBSET이었다. 이를 최종 감사로 오인하지 않았고, 400개 완료 후 감사와 집계를 다시 시작했다.
- 최종 선택·loss·seed·데이터·동결 코드 계약은 실행 중 바꾸지 않았다.

## P06–P08 완료 (2026-09-13 14:01–14:12 KST)

- 전체 독립 감사 PASS: 400개 모델, 140,800 update, 파일 해시 26,920개, 샘플 스트림 재생 30개, 선택 근거 456개, prediction seal 752개, 최종 NPZ 2,844개, endpoint 진단 12,672개를 확인했다.
- SUMMARY.json과 상세 TABLES.md / LaTeX 표 14개를 생성했다. 원본 확률을 다시 읽어 p/NLL/Hit@1을 검증했고, source-dev threshold와 정확한 typed-field F1도 재계산했다.
- Matplotlib 그림 12개를 PNG/PDF/SVG로 생성하고 12페이지 통합 PDF를 만들었다. 독립 그림 감사에서 924개 숫자 셀 / 24개 N/A와 모든 PDF 페이지·파일 해시를 확인했다.
- 처음 렌더링한 PDF 12페이지를 직접 확인했다. 마지막 paired-CI 페이지의 footer가 축 라벨과 겹쳐 plot17.py의 레이아웃만 수정했다. 재생성 후 그림 숫자 감사를 다시 통과했다. 첫 11페이지는 렌더링 해시가 이전 검수본과 동일했고, 변경된 12페이지는 다시 직접 확인해 겹침이 없음을 확인했다.
- 논문용 압축 표 3개(16×6)의 288개 숫자와 alias·정답 cohort 수·LaTeX 구조를 독립 검증했다. TeX compiler가 없어서 컴파일/지면 배치 검증까지 했다고 주장하지 않는다.
- FORMULAS.md, REPRODUCTION.md, DATA_LIMITATIONS.md, REPORT.md에 실제 구현·결과·제약을 정리했다. 선택 결과가 Hybrid의 NLL을 개선하지 못한 점과 SMB2 offset Hit@1=0을 그대로 보고했다.
- 최종 기본 모델은 교체하지 않았다. 기존 lapa-attention의 tracked 파일은 git status 기준 변경이 없고, v16을 포함한 동결 코드·데이터 계약도 유지됐다.
- FINAL_ARTIFACTS.json과 VISUAL_REVIEW.json에 최종 해시·검수 근거를 남긴다. 검수용 임시 렌더 PNG만 이후 정리하며, 원본 모델·수치·최종 그림은 보존한다.
