> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# v16 master checklist

- [x] P00 원 구현/수식 및 기존 한계 조사. 패키지 보존, TAPE 기준6후보 고정.
- [x] P01 데이터/코드 계약, 누출·operator·ordinal 지원 감사.
- [x] P02 6개 수식+Off 구현, 정규화/gradient/마스크/동일 초기화/체크포인트 테스트.
- [x] P03 별도 CPU/CUDA smoke test와 시간 측정.
- [x] P04 72개 inner 2→1 development 탐색 실행.
- [x] P05 outer-target별 source-only 수식 선택 및 seal.
- [x] P06 최대36개 최종3→1 학습 및 raw-only 평가. 실제27개, 합계99개 모델 완료.
- [x] P07 전체 수치/paired 차이/shortcut/stage/ordinal 진단 집계.
- [x] P08 Matplotlib 숫자 그래프·테이블 생성 및 시각 검증.
- [x] P09 수식 설명/결론/한계/재현법 보고서, 산출물 해시 확인.

전체 완료:99개 모델,8페이지 그래프/PNG·SVG,6개 LaTeX 표,보고서·수식·재현법,독립 감사 및 시각 검증 완료. 기존 패키지 유지. 최종 해시 봉인은 COMPLETION.json 참조.

진행 중 정보: EVENTS.jsonl, GRID_PROGRESS.json, 각 run/PROGRESS.json.
