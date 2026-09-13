# LAPA 연구 보관 상태

상태: **개발 중단·연구 기록 보관 (development paused / research archive)**.
현재 연구 방향의 추가 개발을 멈추고 구현, 실험 경과와 부정적 결과를 보존한다.
이는 LAPA의 모든 가능성이 불가능하다는 판정이나, GitHub에서 저장소를 실제로
`Archived` 상태로 전환했다는 뜻이 아니다. 저장소 생성·공개·push·서버 측 archive는
별도 승인과 작업이 필요한 절차다.

## 중단 판단의 근거

최종 근거는 [v18 보고서](../research_archive/studies/four_factor_attention_v18/REPORT.md)와
[원정밀도 집계](../research_archive/studies/four_factor_attention_v18/SUMMARY.json)다.
Source·Width·Endian·Base 분포로 모든 encoder 층과 최종 readout의 attention을
직접 만드는 두 수식을 시험했다. Q/K similarity는 제거했지만 learned V,
residual, FFN과 고정 주소 연산 규칙은 유지했다.

실제 DNS·Modbus·TLS·SMB2에서 세 프로토콜로 학습하고 남은 하나로 평가하는
3→1 조건으로, 두 수식 × 네 target × 세 seed의 **신규 24개 모델**을 각각
600 update 학습했다. 기존 RoPE/CoPE/TAPE/SDPA × Off/Hybrid의 **96개 대조군은
재학습하지 않고 재사용**했다. 비교 대상은 동일한 74개 메시지·347개 필드다.

다음은 protocol 안의 필드를 평균한 뒤 네 protocol을 동등 평균하고,
마지막으로 세 seed를 평균한 protocol-macro 결과다. `p(target)`은 정답 목적지에
준 확률이며, 필드 발견 F1이나 패킷 정확도가 아니다.

| 방법 | 평균 p(target) ↑ | 평균 NLL (nat) ↓ | Hit@1 ↑ |
| --- | ---: | ---: | ---: |
| RoPE + LAPA Hybrid | 0.420837 | 3.063246 | 0.534492 |
| CoPE + LAPA Hybrid | 0.456255 | 3.525861 | 0.509848 |
| TAPE + LAPA Hybrid | 0.436009 | 3.035284 | 0.487448 |
| SDPA + LAPA Hybrid | 0.414544 | 3.509370 | 0.432749 |
| Four-factor Direct | 0.295720 | 3.847661 | 0.373162 |
| Four-factor Sink | 0.311763 | 3.419171 | 0.430911 |

새 두 수식의 평균 정답 확률은 기존 네 Hybrid보다 낮았다. Sink의 NLL은
CoPE/SDPA Hybrid보다 낮지만 RoPE/TAPE Hybrid보다 높으므로, 모든 지표에서
일괄적으로 열등했다고 쓰지도 않는다. 필드 347개를 동등 가중한 field-micro
정답 확률은 Direct 0.041878, Sink 0.052515다. DNS가 266개 필드를 차지하므로
macro와 micro는 서로 다른 질문에 답한다.

DNS pointer의 endpoint 확률 상승은 올바른 의미론적 경로의 성공을 뜻하지
않았다. Annotated true-source 확률은 Direct 0.000216, Sink 0.000243이었다.
Sink의 36개 pointer 필드 × 세 seed = 108개 예측에서, **정답 목적지에 쌓인
총 확률질량의 최소 98.057%가 annotated source 이외에서 왔다**는 하한이
계산되었다. 이는 98.057%의 패킷이 틀렸다는 뜻이 아니며, 108개 독립 패킷을
관측했다는 뜻도 아니다. 이 Sink 전용 경계로 특정 대체 source/base를
식별하거나 Direct의 원인을 단정할 수 없다.

DNS RDLENGTH 25개에서 두 새 수식 모두 Hit@1=0이었고, SMB2의 네 세부 관계도
모두 Hit@1=0이었다. 이는 학습·평가 실행이 중단되어 채워 넣은 0이 아니라,
완료된 모델의 예측 실패다. 이런 부정적 결과와 원래 해석 한계를 보존한다.

앞선 [v17 보고서](../research_archive/studies/formula_search_v17/REPORT.md)에서도
400개 모델의 탐색이 범용 기본 수식을 교체할 근거를 확보하지 못했다.
일부 확률 상승과 전체 NLL 악화가 공존했고 source/program 선택의 어려움이
남았다. 최종 v18도 기본 패키지를 새 구조로 교체할 근거가 되지 않았다.

## 이 결과가 주장하지 않는 것

- 고정 600-update, 세 training seed와 작은 historical 평가 자료에서 얻은
  결과다. 충분히 수렴한 최적 성능이나 새로운 capture/protocol로의 일반화를
  입증하지 않는다. Seed CI는 capture 모집단의 불확실성이 아니다.
- 새 모델은 42개 합법 조합, 기존 Hybrid는 68개 프로그램을 사용한다.
  보조 loss·파라미터화·파라미터 수도 달라 Q/K 제거만의 인과효과를 분리하지
  못한다. Q/K의 보편적 필요성이나 LAPA 전체의 불가능성을 증명하지 않는다.
- DNS pointer mask/guard와 SMB2 인접 필드 규칙은 고정 사전 지식이다.
  연산 의미 자체를 무감독으로 발견했다는 주장이 아니다.
- Modbus/TLS 평가 목적지는 모두 END다. 높은 endpoint 확률만으로 길이
  연산을 이해했다고 볼 수 없다. v18은 필드 발견 F1을 계산하지 않았다.
- Operator/slot의 positive 학습 범위와 capture 수가 제한된다. 다만 DNS
  RDLENGTH의 실패까지 모두 미학습 연산 때문이라고 설명할 수는 없다.

## 보존 범위와 공개 범위

공개 묶음은 아래 경량 자료로 한정한다. 사용자의 게시·라이선스 지정 요청에
따라 프로젝트 소유 코드·문서는 Apache-2.0으로 제공하고 제3자 고지는 보존한다.
원시 데이터와 가중치는 공개 범위에 포함하지 않는다.

| 구분 | 보관·배포 원칙 |
| --- | --- |
| `src/`, `configs/`, `scripts/`, `examples/`, `tests/` | 기존 compact 패키지 구현과 인터페이스·검증 코드를 유지한다. v18 전체 연구를 이식한 패키지로 표현하지 않는다. |
| `research_archive/studies/formula_search_v16/` | 과거 수식 탐색의 선택된 보고서·집계·그림·코드 스냅샷을 보존한다. |
| `research_archive/studies/formula_search_v17/` | 구조 탐색의 선택된 보고서·집계·그림·코드 스냅샷을 보존한다. |
| `research_archive/studies/four_factor_attention_v18/` | 최종 네 요인 연구의 선택된 보고서·집계·그림·코드 스냅샷을 보존한다. |
| 원시 데이터·payload·PCAP·tensor 자료 | 로컬 보존 대상이다. 이 공개 후보 묶음에는 업로드하지 않는다. |
| 체크포인트·가중치·학습 run·패킷별 예측/진단 | 로컬 보존 대상이다. 경량 집계와 혼동하여 업로드하지 않는다. |
| 원 작업공간의 전체 경로 계약·원시 manifest | 절대 경로와 비공개 자산 참조를 포함할 수 있어 로컬에 둔다. 공개용 목록은 상대 경로와 검토된 메타데이터로 제한한다. |

연구 코드 스냅샷은 **당시 작업공간에 의존하는 역사적 기록**이다. 원 데이터,
형제 연구 모듈, 계약 파일과 실행 환경이 빠진 공개 clone에서 그대로 전체 학습을
재현할 수 있다는 보장은 없다. 선택된 파일의 해시 일치도 전체 재현성이나
비공개 원자료의 공개 허가를 대신하지 않는다. 스냅샷과 문서가 참조하는 일부
원시 산출물이 공개 후보 묶음에 없는 것은 이 범위 제한 때문이다.

`src/`의 compact 패키지 사용 범위는 [구현 충실도](baseline_fidelity.md)와
[재현 안내](reproduction.md)를 따른다. 단위 테스트의 기능 확인, 승인된 로컬
데이터를 쓰는 smoke 학습, 과거 연구 전체의 재현은 서로 다른 수준의 검증이다.
과거 보고서와 체크리스트의 PASS는 당시 실행 기록이며, 이번 공개 후보 묶음의
새 검증이나 공개 승인으로 옮겨 읽지 않는다.

## 접근·라이선스·재개 조건

[LICENSE](../LICENSE)는 Apache-2.0이다. 프로젝트가 소유하는 부분에 적용되며,
원 데이터나 가중치의 재배포 권한을 만들거나 제3자 조건을 대체하지 않는다.
[제3자 고지](../THIRD_PARTY_NOTICES.md)와 [데이터 안내](../data/README.md)를 따른다.
공개판의 세 위치 모듈에는 출처 주석만 추가했다. 실행 코드는 같지만 과거
동결 계약의 파일 해시와는 달라졌으므로 원본 계약 PASS를 새 패키지에 주장하지 않는다.

비공개 원자료가 필요한 재현자는 소유자에게 자료 범위와 목적을 설명하고,
권리·개인정보 검토가 끝난 묶음을 승인된 채널로 받아야 한다. 접근 제공이나
응답을 보장하지 않으며, 누락 자산을 공개 push 또는 git의 강제 추가로
해결해서는 안 된다. [공개 전 체크리스트](release_checklist.md)는 별도의
게시 승인을 받기 위한 점검표다.

향후 재개한다면 기존 실패 결과를 덮어쓰지 않고 별도 lineage를 만든다.
동일 operator support·loss 아래 source localization과 축 선택을 분리하고,
새 capture/protocol 평가와 test 재사용 정책을 사전에 고정하는 것이 필요한
후속 조건이다. 이 제안은 완료된 실험이나 계속되는 개발 약속이 아니다.
