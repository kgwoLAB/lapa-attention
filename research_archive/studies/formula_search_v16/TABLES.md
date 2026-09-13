> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# Formula search v16: sealed numerical tables

These are exploratory, historically inspected real-capture evaluations, not a fresh confirmatory test.

Values are means [95% Student-t CI] across three fixed training seeds (df=2). Intervals are not clipped and quantify seed variation only, not packet/capture/protocol uncertainty. Selected is independently chosen inside each outer fold using source protocols only; it is not one global best formula.

## Source-only selection

| Held-out target | Source protocols | Selected formula | Inner balanced log gain |
|---|---|---|---:|
| DNS | modbus, tls, smb2 | hybrid | 1.468737 |
| MODBUS | dns, tls, smb2 | route_sink | 0.096509 |
| TLS | dns, modbus, smb2 | hybrid | 0.517524 |
| SMB2 | dns, modbus, tls | hybrid | 1.763326 |

### All candidate search scores (not final test scores)

| Outer target excluded | Candidate | Source-only inner balanced log gain | Selected |
|---|---|---:|---|
| DNS | hybrid | 1.468737 | yes |
| DNS | route_direct | -0.292262 | no |
| DNS | route_sink | -0.414543 | no |
| DNS | route_axis | -0.832458 | no |
| DNS | route_joint | -1.457294 | no |
| DNS | cnn_joint | -1.548638 | no |
| MODBUS | route_sink | 0.096509 | yes |
| MODBUS | route_direct | -0.379875 | no |
| MODBUS | route_axis | -0.548389 | no |
| MODBUS | hybrid | -0.789427 | no |
| MODBUS | route_joint | -1.006086 | no |
| MODBUS | cnn_joint | -1.301211 | no |
| TLS | hybrid | 0.517524 | yes |
| TLS | route_sink | 0.307808 | no |
| TLS | route_axis | -0.308515 | no |
| TLS | route_joint | -0.421070 | no |
| TLS | route_direct | -0.455452 | no |
| TLS | cnn_joint | -0.970973 | no |
| SMB2 | hybrid | 1.763326 | yes |
| SMB2 | route_sink | -0.200363 | no |
| SMB2 | cnn_joint | -0.571103 | no |
| SMB2 | route_axis | -0.877343 | no |
| SMB2 | route_joint | -0.914367 | no |
| SMB2 | route_direct | -1.006096 | no |

## Final endpoint probabilities by protocol and semantic

N is the number of unique annotated fields per seed, not three times that number. The Off field head is untrained; its field F1 must not be interpreted as zero.

| Protocol | Semantic | N | Role (formula) | p(target) [95% CI] | Hit@1 [95% CI] | NLL [95% CI] |
|---|---|---:|---|---:|---:|---:|
| DNS | LENGTH | 230 | off (off) | 0.0377 [0.0084, 0.0670] | 0.0377 [0.0047, 0.0707] | 25.6010 [-17.2839, 68.4859] |
| DNS | LENGTH | 230 | hybrid (hybrid) | 0.0129 [0.0021, 0.0237] | 0.0159 [-0.0220, 0.0539] | 5.6563 [4.8938, 6.4189] |
| DNS | LENGTH | 230 | selected (hybrid) | 0.0129 [0.0021, 0.0237] | 0.0159 [-0.0220, 0.0539] | 5.6563 [4.8938, 6.4189] |
| DNS | POINTER | 36 | off (off) | 0.0000 [-0.0000, 0.0001] | 0.0000 [0.0000, 0.0000] | 22.1339 [-4.2491, 48.5169] |
| DNS | POINTER | 36 | hybrid (hybrid) | 0.0092 [0.0016, 0.0169] | 0.0185 [-0.0213, 0.0584] | 5.1621 [4.5021, 5.8221] |
| DNS | POINTER | 36 | selected (hybrid) | 0.0092 [0.0016, 0.0169] | 0.0185 [-0.0213, 0.0584] | 5.1621 [4.5021, 5.8221] |
| MODBUS | LENGTH | 6 | off (off) | 0.7017 [-0.2249, 1.6283] | 0.7778 [-0.1784, 1.7339] | 0.6061 [-1.5725, 2.7848] |
| MODBUS | LENGTH | 6 | hybrid (hybrid) | 0.5245 [0.1129, 0.9361] | 0.7222 [-0.4730, 1.9174] | 0.7126 [-0.1953, 1.6205] |
| MODBUS | LENGTH | 6 | selected (route_sink) | 0.2520 [-0.5089, 1.0129] | 0.4444 [-0.4174, 1.3063] | 2.2439 [-1.0833, 5.5710] |
| TLS | LENGTH | 15 | off (off) | 0.8725 [0.6669, 1.0780] | 0.9333 [0.9333, 0.9333] | 0.2217 [0.0350, 0.4084] |
| TLS | LENGTH | 15 | hybrid (hybrid) | 0.4590 [0.3618, 0.5562] | 0.7333 [0.2952, 1.1715] | 1.0244 [0.6398, 1.4090] |
| TLS | LENGTH | 15 | selected (hybrid) | 0.4590 [0.3618, 0.5562] | 0.7333 [0.2952, 1.1715] | 1.0244 [0.6398, 1.4090] |
| SMB2 | LENGTH | 30 | off (off) | 0.0717 [-0.2169, 0.3602] | 0.1778 [-0.5167, 0.8722] | 7.4025 [0.1635, 14.6415] |
| SMB2 | LENGTH | 30 | hybrid (hybrid) | 0.0399 [-0.1081, 0.1879] | 0.1556 [-0.5137, 0.8249] | 6.6677 [1.1493, 12.1861] |
| SMB2 | LENGTH | 30 | selected (hybrid) | 0.0399 [-0.1081, 0.1879] | 0.1556 [-0.5137, 0.8249] | 6.6677 [1.1493, 12.1861] |
| SMB2 | OFFSET | 30 | off (off) | 0.0001 [-0.0000, 0.0003] | 0.0000 [0.0000, 0.0000] | 11.7626 [6.8582, 16.6670] |
| SMB2 | OFFSET | 30 | hybrid (hybrid) | 0.0034 [-0.0088, 0.0156] | 0.0000 [0.0000, 0.0000] | 7.7426 [4.2445, 11.2408] |
| SMB2 | OFFSET | 30 | selected (hybrid) | 0.0034 [-0.0088, 0.0156] | 0.0000 [0.0000, 0.0000] | 7.7426 [4.2445, 11.2408] |

## Paired final gains by protocol and semantic

Positive gains favor Selected. NLL gain is reference minus Selected; probability gain is Selected minus reference.

| Protocol | Semantic | Reference | Δp(target) [95% CI] | NLL gain [95% CI] |
|---|---|---|---:|---:|
| DNS | LENGTH | hybrid | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| DNS | POINTER | hybrid | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| DNS | LENGTH | off | -0.0248 [-0.0647, 0.0151] | 19.9447 [-22.5484, 62.4378] |
| DNS | POINTER | off | 0.0092 [0.0015, 0.0169] | 16.9718 [-9.8811, 43.8247] |
| MODBUS | LENGTH | hybrid | -0.2725 [-1.4387, 0.8937] | -1.5312 [-5.6834, 2.6210] |
| MODBUS | LENGTH | off | -0.4497 [-2.1331, 1.2338] | -1.6377 [-7.0304, 3.7549] |
| TLS | LENGTH | hybrid | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| TLS | LENGTH | off | -0.4134 [-0.6906, -0.1362] | -0.8028 [-1.3214, -0.2841] |
| SMB2 | LENGTH | hybrid | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| SMB2 | OFFSET | hybrid | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| SMB2 | LENGTH | off | -0.0318 [-0.1742, 0.1107] | 0.7348 [-8.7486, 10.2183] |
| SMB2 | OFFSET | off | 0.0033 [-0.0090, 0.0155] | 4.0200 [-3.1588, 11.1987] |

## Equal-protocol macro

| Cohort | Role | p(target) [95% CI] | Hit@1 [95% CI] | NLL [95% CI] | Balanced log gain [95% CI] |
|---|---|---:|---:|---:|---:|
| all_fields | off | 0.4107 [0.1779, 0.6435] | 0.4581 [0.1682, 0.7481] | 8.8855 [-0.6129, 18.3840] | -2.2554 [-7.7118, 3.2010] |
| all_fields | hybrid | 0.2544 [0.1220, 0.3868] | 0.3874 [-0.0333, 0.8081] | 3.6329 [3.2147, 4.0511] | 0.4963 [0.2885, 0.7041] |
| all_fields | selected | 0.1863 [0.0259, 0.3466] | 0.3180 [0.0604, 0.5756] | 4.0157 [2.6995, 5.3319] | 0.1135 [-1.1322, 1.3591] |
| length | off | 0.4209 [0.1736, 0.6682] | 0.4816 [0.1230, 0.8403] | 8.4578 [-0.8391, 17.7547] | -1.5773 [-6.4534, 3.2988] |
| length | hybrid | 0.2591 [0.1151, 0.4031] | 0.4068 [-0.0851, 0.8986] | 3.5153 [2.4134, 4.6172] | 0.5624 [0.0214, 1.1035] |
| length | selected | 0.1910 [0.0373, 0.3447] | 0.3373 [0.0303, 0.6443] | 3.8981 [2.4104, 5.3857] | 0.1796 [-0.9208, 1.2800] |

## Relation detail

| Protocol | Relation | N | Role | p(target) [95% CI] | Hit@1 [95% CI] | NLL [95% CI] |
|---|---|---:|---|---:|---:|---:|
| DNS | DNS RDLENGTH | 25 | off | 0.2526 [0.0058, 0.4994] | 0.2533 [0.0033, 0.5034] | 15.6542 [-9.9911, 41.2995] |
| DNS | DNS RDLENGTH | 25 | hybrid | 0.0117 [-0.0192, 0.0425] | 0.0533 [-0.1761, 0.2828] | 5.2955 [3.5673, 7.0237] |
| DNS | DNS RDLENGTH | 25 | selected | 0.0117 [-0.0192, 0.0425] | 0.0533 [-0.1761, 0.2828] | 5.2955 [3.5673, 7.0237] |
| DNS | DNS TXT length | 1 | off | 0.2357 [-0.4448, 0.9163] | 0.3333 [-1.1009, 1.7676] | 2.2935 [-2.4860, 7.0730] |
| DNS | DNS TXT length | 1 | hybrid | 0.0129 [-0.0137, 0.0394] | 0.0000 [0.0000, 0.0000] | 4.6154 [2.3358, 6.8951] |
| DNS | DNS TXT length | 1 | selected | 0.0129 [-0.0137, 0.0394] | 0.0000 [0.0000, 0.0000] | 4.6154 [2.3358, 6.8951] |
| DNS | DNS label | 164 | off | 0.0009 [-0.0022, 0.0040] | 0.0000 [0.0000, 0.0000] | 26.9386 [-16.7288, 70.6059] |
| DNS | DNS label | 164 | hybrid | 0.0129 [0.0017, 0.0241] | 0.0122 [-0.0181, 0.0425] | 5.8643 [5.2004, 6.5283] |
| DNS | DNS label | 164 | selected | 0.0129 [0.0017, 0.0241] | 0.0122 [-0.0181, 0.0425] | 5.8643 [5.2004, 6.5283] |
| DNS | DNS pointer | 36 | off | 0.0000 [-0.0000, 0.0001] | 0.0000 [0.0000, 0.0000] | 22.1339 [-4.2491, 48.5169] |
| DNS | DNS pointer | 36 | hybrid | 0.0092 [0.0016, 0.0169] | 0.0185 [-0.0213, 0.0584] | 5.1621 [4.5021, 5.8221] |
| DNS | DNS pointer | 36 | selected | 0.0092 [0.0016, 0.0169] | 0.0185 [-0.0213, 0.0584] | 5.1621 [4.5021, 5.8221] |
| DNS | DNS root terminator | 40 | off | 0.0492 [0.0460, 0.0523] | 0.0500 [0.0500, 0.0500] | 26.9166 [-24.9171, 78.7503] |
| DNS | DNS root terminator | 40 | hybrid | 0.0139 [0.0075, 0.0202] | 0.0083 [-0.0275, 0.0442] | 5.0552 [4.4987, 5.6118] |
| DNS | DNS root terminator | 40 | selected | 0.0139 [0.0075, 0.0202] | 0.0083 [-0.0275, 0.0442] | 5.0552 [4.4987, 5.6118] |
| MODBUS | Modbus MBAP length | 6 | off | 0.7017 [-0.2249, 1.6283] | 0.7778 [-0.1784, 1.7339] | 0.6061 [-1.5725, 2.7848] |
| MODBUS | Modbus MBAP length | 6 | hybrid | 0.5245 [0.1129, 0.9361] | 0.7222 [-0.4730, 1.9174] | 0.7126 [-0.1953, 1.6205] |
| MODBUS | Modbus MBAP length | 6 | selected | 0.2520 [-0.5089, 1.0129] | 0.4444 [-0.4174, 1.3063] | 2.2439 [-1.0833, 5.5710] |
| TLS | TLS record length | 15 | off | 0.8725 [0.6669, 1.0780] | 0.9333 [0.9333, 0.9333] | 0.2217 [0.0350, 0.4084] |
| TLS | TLS record length | 15 | hybrid | 0.4590 [0.3618, 0.5562] | 0.7333 [0.2952, 1.1715] | 1.0244 [0.6398, 1.4090] |
| TLS | TLS record length | 15 | selected | 0.4590 [0.3618, 0.5562] | 0.7333 [0.2952, 1.1715] | 1.0244 [0.6398, 1.4090] |
| SMB2 | SMB2 ContextLength | 15 | off | 0.1131 [-0.3670, 0.5932] | 0.2889 [-0.9541, 1.5319] | 6.7654 [-6.7250, 20.2557] |
| SMB2 | SMB2 ContextLength | 15 | hybrid | 0.0701 [-0.2026, 0.3429] | 0.2889 [-0.9541, 1.5319] | 5.7659 [-3.1754, 14.7073] |
| SMB2 | SMB2 ContextLength | 15 | selected | 0.0701 [-0.2026, 0.3429] | 0.2889 [-0.9541, 1.5319] | 5.7659 [-3.1754, 14.7073] |
| SMB2 | SMB2 ContextOffset | 15 | off | 0.0001 [-0.0001, 0.0004] | 0.0000 [0.0000, 0.0000] | 10.7434 [8.2046, 13.2822] |
| SMB2 | SMB2 ContextOffset | 15 | hybrid | 0.0019 [-0.0048, 0.0086] | 0.0000 [0.0000, 0.0000] | 7.8810 [5.7547, 10.0073] |
| SMB2 | SMB2 ContextOffset | 15 | selected | 0.0019 [-0.0048, 0.0086] | 0.0000 [0.0000, 0.0000] | 7.8810 [5.7547, 10.0073] |
| SMB2 | SMB2 NameLength | 15 | off | 0.0303 [-0.0679, 0.1285] | 0.0667 [-0.0989, 0.2323] | 8.0397 [7.0498, 9.0295] |
| SMB2 | SMB2 NameLength | 15 | hybrid | 0.0097 [-0.0139, 0.0333] | 0.0222 [-0.0734, 0.1178] | 7.5695 [3.4907, 11.6482] |
| SMB2 | SMB2 NameLength | 15 | selected | 0.0097 [-0.0139, 0.0333] | 0.0222 [-0.0734, 0.1178] | 7.5695 [3.4907, 11.6482] |
| SMB2 | SMB2 NameOffset | 15 | off | 0.0001 [0.0000, 0.0003] | 0.0000 [0.0000, 0.0000] | 12.7818 [5.5049, 20.0587] |
| SMB2 | SMB2 NameOffset | 15 | hybrid | 0.0049 [-0.0128, 0.0226] | 0.0000 [0.0000, 0.0000] | 7.6043 [2.7251, 12.4835] |
| SMB2 | SMB2 NameOffset | 15 | selected | 0.0049 [-0.0128, 0.0226] | 0.0000 [0.0000, 0.0000] | 7.6043 [2.7251, 12.4835] |

## Target-kind detail

END and NULL are distinct valid output classes. INTERIOR is a byte destination. Absent fields are not relabeled NULL, and no abstention is folded into NULL.

| Protocol | Target kind | N | Role | p(target) [95% CI] | Hit@1 [95% CI] | NLL [95% CI] |
|---|---|---:|---|---:|---:|---:|
| DNS | END | 13 | off | 0.6543 [0.1173, 1.1913] | 0.6667 [0.0829, 1.2504] | 1.1339 [-0.9847, 3.2525] |
| DNS | END | 13 | hybrid | 0.0243 [-0.0561, 0.1048] | 0.1282 [-0.4234, 0.6798] | 4.7407 [1.5804, 7.9011] |
| DNS | END | 13 | selected | 0.0243 [-0.0561, 0.1048] | 0.1282 [-0.4234, 0.6798] | 4.7407 [1.5804, 7.9011] |
| DNS | INTERIOR | 253 | off | 0.0007 [-0.0013, 0.0026] | 0.0000 [0.0000, 0.0000] | 26.3649 [-16.3312, 69.0610] |
| DNS | INTERIOR | 253 | hybrid | 0.0118 [0.0035, 0.0201] | 0.0105 [-0.0099, 0.0310] | 5.6331 [5.1946, 6.0715] |
| DNS | INTERIOR | 253 | selected | 0.0118 [0.0035, 0.0201] | 0.0105 [-0.0099, 0.0310] | 5.6331 [5.1946, 6.0715] |
| MODBUS | END | 6 | off | 0.7017 [-0.2249, 1.6283] | 0.7778 [-0.1784, 1.7339] | 0.6061 [-1.5725, 2.7848] |
| MODBUS | END | 6 | hybrid | 0.5245 [0.1129, 0.9361] | 0.7222 [-0.4730, 1.9174] | 0.7126 [-0.1953, 1.6205] |
| MODBUS | END | 6 | selected | 0.2520 [-0.5089, 1.0129] | 0.4444 [-0.4174, 1.3063] | 2.2439 [-1.0833, 5.5710] |
| TLS | END | 15 | off | 0.8725 [0.6669, 1.0780] | 0.9333 [0.9333, 0.9333] | 0.2217 [0.0350, 0.4084] |
| TLS | END | 15 | hybrid | 0.4590 [0.3618, 0.5562] | 0.7333 [0.2952, 1.1715] | 1.0244 [0.6398, 1.4090] |
| TLS | END | 15 | selected | 0.4590 [0.3618, 0.5562] | 0.7333 [0.2952, 1.1715] | 1.0244 [0.6398, 1.4090] |
| SMB2 | END | 15 | off | 0.1419 [-0.4338, 0.7177] | 0.3556 [-1.0333, 1.7444] | 5.8210 [-7.0750, 18.7170] |
| SMB2 | END | 15 | hybrid | 0.0786 [-0.2185, 0.3758] | 0.3111 [-1.0275, 1.6497] | 4.8560 [-3.8036, 13.5155] |
| SMB2 | END | 15 | selected | 0.0786 [-0.2185, 0.3758] | 0.3111 [-1.0275, 1.6497] | 4.8560 [-3.8036, 13.5155] |
| SMB2 | INTERIOR | 27 | off | 0.0003 [-0.0007, 0.0012] | 0.0000 [0.0000, 0.0000] | 12.8452 [8.1189, 17.5715] |
| SMB2 | INTERIOR | 27 | hybrid | 0.0014 [-0.0032, 0.0060] | 0.0000 [0.0000, 0.0000] | 8.4355 [5.4250, 11.4460] |
| SMB2 | INTERIOR | 27 | selected | 0.0014 [-0.0032, 0.0060] | 0.0000 [0.0000, 0.0000] | 8.4355 [5.4250, 11.4460] |
| SMB2 | NULL | 18 | off | 0.0010 [-0.0008, 0.0028] | 0.0000 [0.0000, 0.0000] | 7.8232 [4.9687, 10.6777] |
| SMB2 | NULL | 18 | hybrid | 0.0045 [-0.0121, 0.0211] | 0.0000 [0.0000, 0.0000] | 7.3173 [2.9205, 11.7142] |
| SMB2 | NULL | 18 | selected | 0.0045 [-0.0121, 0.0211] | 0.0000 [0.0000, 0.0000] | 7.3173 [2.9205, 11.7142] |

## Stage diagnostics (all annotated fields per protocol)

Source and Program are pre-validity heads. Program is conditioned on the true source only by post-forward indexing. Route is the destination prior after execution and smoothing. The separately stored route_source_p / route_program_p are validity-normalized posterior quantities.

| Protocol | Role | Source p | Program p given true source | Route p | Final p |
|---|---|---:|---:|---:|---:|
| DNS | off | 0.0175 [0.0175, 0.0176] | 0.0148 [0.0143, 0.0154] | N/A | 0.0326 [0.0072, 0.0580] |
| DNS | hybrid | 0.0135 [-0.0111, 0.0381] | 0.0011 [-0.0028, 0.0050] | 0.0135 [0.0133, 0.0137] | 0.0124 [0.0033, 0.0216] |
| DNS | selected | 0.0135 [-0.0111, 0.0381] | 0.0011 [-0.0028, 0.0050] | 0.0135 [0.0133, 0.0137] | 0.0124 [0.0033, 0.0216] |
| MODBUS | off | 0.0950 [0.0948, 0.0951] | 0.0148 [0.0147, 0.0149] | N/A | 0.7017 [-0.2249, 1.6283] |
| MODBUS | hybrid | 0.0584 [0.0167, 0.1001] | 0.0792 [-0.0419, 0.2003] | 0.0948 [0.0739, 0.1157] | 0.5245 [0.1129, 0.9361] |
| MODBUS | selected | 0.0270 [-0.0712, 0.1253] | 0.0962 [-0.0203, 0.2127] | 0.2520 [-0.5089, 1.0129] | 0.2520 [-0.5089, 1.0129] |
| TLS | off | 0.0345 [0.0343, 0.0346] | 0.0147 [0.0144, 0.0151] | N/A | 0.8725 [0.6669, 1.0780] |
| TLS | hybrid | 0.0863 [0.0056, 0.1669] | 0.5803 [-0.3112, 1.4718] | 0.0920 [0.0713, 0.1128] | 0.4590 [0.3618, 0.5562] |
| TLS | selected | 0.0863 [0.0056, 0.1669] | 0.5803 [-0.3112, 1.4718] | 0.0920 [0.0713, 0.1128] | 0.4590 [0.3618, 0.5562] |
| SMB2 | off | 0.0050 [0.0049, 0.0050] | 0.0147 [0.0146, 0.0149] | N/A | 0.0359 [-0.1083, 0.1802] |
| SMB2 | hybrid | 0.0037 [0.0006, 0.0068] | 0.0025 [-0.0079, 0.0130] | 0.0052 [-0.0031, 0.0135] | 0.0217 [-0.0496, 0.0930] |
| SMB2 | selected | 0.0037 [0.0006, 0.0068] | 0.0025 [-0.0079, 0.0130] | 0.0052 [-0.0031, 0.0135] | 0.0217 [-0.0496, 0.0930] |

## DNS positive-slot exposure

For DNS held out, non-DNS source training has positive fields only in slots 0–3. Slots ≥4 still receive negative-presence examples; this is unseen positive-supervision position, not an entirely untrained slot embedding.

| Slot group | N | Role | p(target) [95% CI] | NLL [95% CI] |
|---|---:|---|---:|---:|
| slot_lt4 | 147 | off | 0.0003 [-0.0006, 0.0012] | 28.5089 [-20.1971, 77.2149] |
| slot_ge4 | 119 | off | 0.0725 [0.0152, 0.1297] | 20.9600 [-9.8655, 51.7856] |
| slot_lt4 | 147 | hybrid | 0.0124 [-0.0006, 0.0254] | 6.1355 [5.1668, 7.1041] |
| slot_ge4 | 119 | hybrid | 0.0124 [0.0050, 0.0198] | 4.9150 [4.6610, 5.1689] |
| slot_lt4 | 147 | selected | 0.0124 [-0.0006, 0.0254] | 6.1355 [5.1668, 7.1041] |
| slot_ge4 | 119 | selected | 0.0124 [0.0050, 0.0198] | 4.9150 [4.6610, 5.1689] |

## Field F1 (separate task)

| Protocol | Role | Typed field F1 [95% CI] |
|---|---|---:|
| DNS | off | Not trained |
| DNS | hybrid | 0.0000 [0.0000, 0.0000] |
| DNS | selected | 0.0000 [0.0000, 0.0000] |
| MODBUS | off | Not trained |
| MODBUS | hybrid | 0.0000 [0.0000, 0.0000] |
| MODBUS | selected | 0.0000 [0.0000, 0.0000] |
| TLS | off | Not trained |
| TLS | hybrid | 0.0934 [-0.0461, 0.2329] |
| TLS | selected | 0.0934 [-0.0461, 0.2329] |
| SMB2 | off | Not trained |
| SMB2 | hybrid | 0.0000 [0.0000, 0.0000] |
| SMB2 | selected | 0.0000 [0.0000, 0.0000] |

## Deterministic sanity references

These are not prior-paper models. Uniform Hit@1 uses deterministic argmax tie-breaking at byte index 0; its expected sampled Hit@1 equals p(target). Zero-probability NLL uses the same 1e-30 reporting floor.

| Protocol | Semantic | N | Reference | p(target) | Hit@1 | NLL |
|---|---|---:|---|---:|---:|---:|
| DNS | LENGTH | 230 | always_end | 0.056522 | 0.056522 | 65.173169 |
| DNS | LENGTH | 230 | always_null | 0.000000 | 0.000000 | 69.077553 |
| DNS | LENGTH | 230 | uniform | 0.018129 | 0.000000 | 4.165816 |
| DNS | POINTER | 36 | always_end | 0.000000 | 0.000000 | 69.077553 |
| DNS | POINTER | 36 | always_null | 0.000000 | 0.000000 | 69.077553 |
| DNS | POINTER | 36 | uniform | 0.008141 | 0.000000 | 5.004062 |
| MODBUS | LENGTH | 6 | always_end | 1.000000 | 1.000000 | 0.000000 |
| MODBUS | LENGTH | 6 | always_null | 0.000000 | 0.000000 | 69.077553 |
| MODBUS | LENGTH | 6 | uniform | 0.079429 | 0.000000 | 2.553219 |
| TLS | LENGTH | 15 | always_end | 1.000000 | 1.000000 | 0.000000 |
| TLS | LENGTH | 15 | always_null | 0.000000 | 0.000000 | 69.077553 |
| TLS | LENGTH | 15 | uniform | 0.029738 | 0.000000 | 3.937628 |
| SMB2 | LENGTH | 30 | always_end | 0.500000 | 0.500000 | 34.538776 |
| SMB2 | LENGTH | 30 | always_null | 0.300000 | 0.300000 | 48.354287 |
| SMB2 | LENGTH | 30 | uniform | 0.004899 | 0.000000 | 5.339500 |
| SMB2 | OFFSET | 30 | always_end | 0.000000 | 0.000000 | 69.077553 |
| SMB2 | OFFSET | 30 | always_null | 0.300000 | 0.300000 | 48.354287 |
| SMB2 | OFFSET | 30 | uniform | 0.004899 | 0.000000 | 5.339500 |

## Audit and interpretation boundaries

- Verified 72 search models and 27 unique final models.
- All final runs use 600 steps and the same protocol-balanced sample stream for paired seeds.
- Off uses endpoint NLL only; On variants use four unit-weight losses. Axis variants replace bank CE with mean axis CE.
- Original Off/Hybrid share complete initial states; all selected variants preserve shared tensor initialization (smoke-test evidence).
- Route-only base_p is a uniform reference, never a learned QK result. CNN-joint has no encoder QKV; other route variants still use a Transformer encoder.
- Formula choices are source-only and outer-fold-specific. Final target outcomes never re-rank those choices.
- Selected versus Hybrid can change normalization and program loss as well as final QK removal; this contrast alone is not an isolated causal proof that QKV is harmful.
- Full seed values, target-kind slices, paired intervals, raw F1 counts, and seal hashes are preserved in SUMMARY.json.
- No untrained, stale, or unsupported prior-paper baseline is silently assigned a zero or inserted into this comparison.
