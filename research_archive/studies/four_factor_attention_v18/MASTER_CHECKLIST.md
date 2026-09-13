> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# v18 마스터 체크리스트

`[x]`는 실제 확인한 완료만 의미한다. 진행·실패·재개는 단계 로그에 기록하며 기존 결과를 덮어쓰지 않는다.

- [x] P01. 사용자 범위를 반영한 PLAN 작성: source/width/endian/base 직접 attention, 두 mode, 실제4프로토콜.
- [x] P02. `model18.py` 확인: 모든 encoder layer와 readout에4요인 적용, Q/K·program·sign/mask head 없음, learned V 유지.
- [x] P03. `executor18.py` 확인:7개 고정 base operator,56칸/42합법 조합, DNS mask·SMB2 prior 공개.
- [x] P04. `losses18.py` 확인: presence/source/attributes/endpoint4그룹;3축 NLL 합, width1 endian 동치 처리.
- [x] P05. 실제 TRAIN packet에서 CPU/GPU forward·backward·네 loss gradient 검증.
- [x] P06. 확률 정규화, nonzero padding 불변성, invalid/END/NULL 구분, encoder special-mass self-loop 검증.
- [x] P07. 실제 TRAIN smoke 표본의 정답 연산과 기존 실행기의 수치 동등성 및 Q/K 우회 경로 부재 검증.
- [x] P08. 코드·데이터·계획 hash 계약 동결;24개 작업과600updates·seed·source3개 계약 확인. `CONTRACT.json` 및 기존96대조군 artifact hash 확인.
- [x] P09. DNS held-out: direct/sink ×3seed 완료, 각600updates 및 sample stream 봉인.
- [x] P10. Modbus held-out: direct/sink ×3seed 완료, 각600updates 및 sample stream 봉인.
- [x] P11. TLS held-out: direct/sink ×3seed 완료, 각600updates 및 sample stream 봉인.
- [x] P12. SMB2 held-out: direct/sink ×3seed 완료, 각600updates 및 sample stream 봉인.
- [x] P13.24개 모델 raw-only64slot 추론 봉인 후 endpoint p/NLL/Hit@1과 source·축·유효 질량 채점.
- [x] P14. v17 Off/Hybrid4backbone 대조군의 같은600step·source·seed·stream·test 입력·hash 확인 후 재사용.
- [x] P15. 독립 감사:24개 완결성, 두 mode 초기화/stream 일치, train/dev target 배제, 확률·지표·seal 검증. `INDEPENDENT_AUDIT.json` PASS.
- [x] P16. protocol/relation 및 INTERIOR/END/NULL별 표·평균·paired 효과·표본 수 작성. `SUMMARY.json`, `TABLES.md`, LaTeX24개.
- [x] P17. Matplotlib 숫자 그래프·표 및 PDF/PNG 생성; 수치와 렌더링 시각 검증.9페이지 최신 렌더 전부 확인. `FIGURE_AUDIT.json` PASS.
- [x] P18. 결과 보고서·한계·재현 명령·단계 로그·최종 산출물 manifest 완료. `REPORT_AUDIT.json` PASS; `FINAL_ARTIFACTS.json`에 최종 해시 및24개 run seal 보존.

주의: 새 모델은 RoPE/CoPE/TAPE/SDPA의 네 변형이 아니다. 서로 다른 수식 두 개의24개 실행이며,3seed와 작은 historical test만으로 보편적 우월성이나 Q/K 제거 단독효과를 주장하지 않는다.
