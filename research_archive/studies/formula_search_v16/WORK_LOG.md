> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# 작업 로그

## P00 — 설계

- 기존 `routing/program.py`는 이미5축 가산 logits인 것을 확인했다.
- 최종 retrieval QK 제거와 encoder QKV 제거를 다른 실험으로 구분했다.
- 기존 패키지/실험을 덮어쓰지 않고 이 디렉터리에 구현한다.
- 같은2개 source 학습은 재사용하되 outer target의 development를 선택 지표에서 제외하는 nested 설계를 고정했다.
- 음성 결과를 숨기거나 target 결과로 수식을 교체하지 않는다.
- 이후 단계의 기계 판독 가능한 시간 로그는 EVENTS.jsonl에도 기록한다.

## P01–P03 — 구현·감사·실행 준비

- 원본 데이터 해시와 byte 값 일치를 확인하고 clean/gold를 별도로 보관했다. clean loader는 gold를 읽지 않고 고정 cohort ID만 사용한다.
- 독립 감사에서 dev 32개 ID,72개 고유 탐색 job,outer target 제외, 기존 패키지48개 파일 해시 보존을 확인했다.
- Off/Hybrid 원 구현 bitwise 동일, 공통 tensor 초기화 동일,11종 CPU/CUDA 검증을 통과했다.
- Off는 endpoint만, On은 네 loss 모두 계산·역전파됨을 확인했다. Route-only retrieval QK 모듈은 실제 제거했다.
- 탐색/최종 학습 코드를 봉인했으며4-worker GPU 큐를 시작했다. smoke는 실측 TRAIN8개 메시지/34필드만 사용했다.

## P04–P05 — 탐색 종료·선택 봉인

- 72개 탐색(각250 step) 및 각 모델의 두 excluded-protocol development 예측을 모두 완료했다. 실행 오류0.
- target별 선택에 쓰인 inner score는 DNS:hybrid1.4687, Modbus:route_sink0.0965, TLS:hybrid0.5175, SMB2:hybrid1.7633 nat다. 이 값들은 해당 target의 test 점수가 아니다.
- CNN 전체 QKV 제거 또는 joint normalization이 자동으로 유리하다는 관측은 없었다. 후보/threshold/seed를 결과에 맞춰 수정하지 않았다.
- `SELECTION.json` 봉인 후 최종3→1로 전환했다. 선택이 hybrid인3개 target은 동일 모델을 재사용하여 총27개 final job이다.

## P06–P07 — 최종 실험·집계

- 27개 final/각600 step을 끝냈다. 총99개 모델/34,200 step, 실행 오류0.
- 독립 감사가7668개 파일해시,6510개 확률 파일,186개 prediction seal과24개 재생성 sampling stream을 검증했다.
- Modbus 선택된route_sink p=0.252033, 기존hybrid p=0.524533로 평균하락했다. 최종 결과를 이용해 선택을 바꾸지 않았다.
- 부정 결과, p평균/NLL 순위 차이, 별도 field F1 및 END shortcut을 보고서에 모두 포함했다.
- 숫자 그래프8장/PNG·SVG 및8페이지 PDF,LaTeX 표6개를 생성했다.8페이지 전체를 시각 검토한 뒤 F1 colorbar 이름을 정확하게 수정했다.

## P08–P09 — 산출물 검증·종료

- Matplotlib 표형 그래프240칸은 실수값234개와Off field-head 미학습 N/A6개다. 작은 양수는 지수 표기로 남겨0으로 둔갑하지 않도록 했다.
- PDF8페이지 전체를 렌더링·검토했고,마지막 F1 colorbar 수정 후 다시 렌더링해 확인했다. 잘림/겹침 없음.
- REPORT.md, FORMULAS.md, TABLES.md, REPRODUCTION.md와독립감사/시각검증을 남겼다. COMPLETION.json이 최종 파일 해시와완료상태를 기록한다.
- 임시 PDF 검수PNG8개는 해시를 기록한 뒤 정리한다. 원본 PDF와PNG/SVG 그래프는 보존되며검수이미지는다시렌더링할수있다.
- 확인된 새 우월 수식이 없으므로공개LAPA기본구조를교체하지 않았다. 모든 후보코드와checkpoint는재사용가능하다.
