> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# v17 master checklist

- [x] P00 30개 구조와 평가 계약 고정, 기존 결과 보존.
- [x] P01 속성 QK / encoder / 실행 scorer / 결합 / loss 구현 및 CPU·CUDA 검증.
- [x] P02 코드·데이터 계약 봉인, 180개 screen 실행.
- [x] P03 target별 4개 후보 승격, 64개 refine 실행.
- [x] P04 p / NLL champion 독립 선택·봉인.
- [x] P05 4개 backbone × Off / On / 선택 수식의 3→1 최종 평가: 156개 모델.
- [x] P06 전체 산출물 / 초기화 / stream / loss / 예측 봉인 독립 감사.
- [x] P07 확률·NLL·Hit@1·F1·stage 세부 집계 / 그래프 / 표.
- [x] P08 수식·실행 결과·한계 보고서, PDF 시각 검수, 최종 해시 생성·확인.

실시간 상태: GRID_PROGRESS.json / EVENTS.jsonl / 각 run의 PROGRESS.json.

완료: 180/180 screen + 64/64 refine + 156/156 final, 전체 400개 고유 모델 / 140,800 training update. 최종 독립 감사 PASS. 그림 12개(PNG/PDF/SVG)와 12페이지 PDF, 상세 표 14개, 압축 논문 표 3개, 수식·재현·한계·결과 보고서를 생성했다.

검증: FIGURE_AUDIT.json의 924개 숫자 셀 / 24개 N/A, PAPER_TABLES_AUDIT.json의 288개 셀, VISUAL_REVIEW.json의 전체 12페이지 확인. TeX compiler가 없어 LaTeX 지면 컴파일은 미실시이며 문법·수치 검증만 완료했다.

핵심 결과: 일부 확률 개선은 있지만, 선택 정책의 최종 macro NLL은 모든 backbone에서 기존 Hybrid보다 나빴다. 기존 패키지 기본 모델을 교체하지 않았다. 세부 근거는 REPORT.md, 완료 해시는 FINAL_ARTIFACTS.json.
