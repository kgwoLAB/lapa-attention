> Public archive copy — path-sanitized historical workspace snapshot.
> Original checks and referenced seals below are historical, not proof of
> the current export. See ARCHIVE_NOTICE.md and ../../MANIFEST.json.
> Project-owned contributions: Apache-2.0; see root LICENSE/NOTICE.

# Formula search v17: audited numerical tables

Exploratory, historically inspected real captures; not a fresh confirmatory test. No synthetic protocols.

Final values are means [un-clipped 95% Student-t CI, df=2] across three fixed training seeds. Intervals quantify seed variation, not uncertainty over packets, captures, or unseen protocols. Champions are selected independently within each outer fold using source protocols only; selection is anchored to TAPE, not retuned per backbone.

CNN/GRU rows labeled `none` reuse the same sealed runs in each backbone panel. Identical role aliases are not additional experiments. N/A denotes an absent or untrained quantity; measured zero remains zero. Off auxiliary heads and field F1 are not trained.

## Frozen source-only choices

| Target excluded | Sources | p champion | NLL champion | Promoted formulas |
| --- | --- | --- | --- | --- |
| DNS | modbus, tls, smb2 | aux_small | aux_small | hybrid, aux_small, attr_content, shared_slot_hybrid |
| MODBUS | dns, tls, smb2 | mix_entropy | hybrid | hybrid, attr_content, shared_slot_hybrid, mix_entropy |
| TLS | dns, modbus, smb2 | attr_content | shared_slot_hybrid | hybrid, gru_shared_attr, shared_slot_hybrid, attr_content |
| SMB2 | dns, modbus, tls | attr_content | attr_content | hybrid, attr_content, aux_small, weak_product |

## Screen candidate scores — not final test results

| Outer target excluded | Formula | Balanced p | Balanced log gain | Evidence cells |
| --- | --- | --- | --- | --- |
| DNS | hybrid | 0.486939 | 1.854593 | 3 |
| DNS | route_sink | 0.066993 | 0.049020 | 3 |
| DNS | route_direct | 0.180876 | -0.044719 | 3 |
| DNS | route_joint | 0.147873 | -0.604204 | 3 |
| DNS | axis_direct | 0.189094 | -0.122858 | 3 |
| DNS | attr_only | 0.309180 | -1.233258 | 3 |
| DNS | attr_content | 0.536852 | 1.963494 | 3 |
| DNS | attr_distance | 0.271081 | -0.828970 | 3 |
| DNS | attr_product | 0.219177 | -5.666673 | 3 |
| DNS | attr_mix | 0.300738 | -0.513370 | 3 |
| DNS | mix_half | 0.376761 | 1.775556 | 3 |
| DNS | mix_learned | 0.525594 | 1.876870 | 3 |
| DNS | mix_entropy | 0.455583 | 1.266872 | 3 |
| DNS | power_learned | 0.261644 | 1.006957 | 3 |
| DNS | weak_product | 0.588105 | 1.371154 | 3 |
| DNS | stopgrad_product | 0.541351 | 1.274877 | 3 |
| DNS | smooth_route | 0.159627 | 0.228574 | 3 |
| DNS | soft_joint | 0.192432 | 0.419882 | 3 |
| DNS | valid_mass_route | 0.172899 | 0.566028 | 3 |
| DNS | cnn_shared_route | 0.022288 | -0.543621 | 3 |
| DNS | cnn_shared_attr | 0.228046 | 1.128929 | 3 |
| DNS | gru_shared_route | 0.010986 | -1.065231 | 3 |
| DNS | gru_shared_attr | 0.407016 | -0.525419 | 3 |
| DNS | shared_slot_hybrid | 0.492488 | 2.521522 | 3 |
| DNS | aux_small | 0.627215 | 2.822922 | 3 |
| DNS | aux_large | 0.386330 | 1.504303 | 3 |
| DNS | bilinear_program | 0.146289 | -0.177815 | 3 |
| DNS | shared_slot_route | 0.160401 | -0.507728 | 3 |
| DNS | execute_score | 0.194504 | 0.928744 | 3 |
| DNS | equivalent_program | 0.153275 | -0.335839 | 3 |
| MODBUS | hybrid | 0.041238 | 0.263079 | 3 |
| MODBUS | route_sink | 0.011356 | 0.029563 | 3 |
| MODBUS | route_direct | 0.029590 | -0.600788 | 3 |
| MODBUS | route_joint | 0.033390 | -0.945120 | 3 |
| MODBUS | axis_direct | 0.028303 | -0.705588 | 3 |
| MODBUS | attr_only | 0.042768 | -2.712532 | 3 |
| MODBUS | attr_content | 0.106042 | 0.645058 | 3 |
| MODBUS | attr_distance | 0.032516 | -2.926414 | 3 |
| MODBUS | attr_product | 0.043903 | -2.720063 | 3 |
| MODBUS | attr_mix | 0.030898 | -0.649563 | 3 |
| MODBUS | mix_half | 0.033273 | -0.072867 | 3 |
| MODBUS | mix_learned | 0.029938 | -0.259042 | 3 |
| MODBUS | mix_entropy | 0.070200 | -0.249124 | 3 |
| MODBUS | power_learned | 0.035973 | 0.051992 | 3 |
| MODBUS | weak_product | 0.044603 | -0.290860 | 3 |
| MODBUS | stopgrad_product | 0.036763 | -0.309945 | 3 |
| MODBUS | smooth_route | 0.012558 | -0.422099 | 3 |
| MODBUS | soft_joint | 0.017925 | -0.241506 | 3 |
| MODBUS | valid_mass_route | 0.011331 | 0.065040 | 3 |
| MODBUS | cnn_shared_route | 0.018181 | -1.059729 | 3 |
| MODBUS | cnn_shared_attr | 0.079148 | -0.476571 | 3 |
| MODBUS | gru_shared_route | 0.013707 | -0.602421 | 3 |
| MODBUS | gru_shared_attr | 0.099957 | -1.373689 | 3 |
| MODBUS | shared_slot_hybrid | 0.067577 | 1.005429 | 3 |
| MODBUS | aux_small | 0.088106 | -0.500098 | 3 |
| MODBUS | aux_large | 0.019310 | 0.142545 | 3 |
| MODBUS | bilinear_program | 0.021494 | -0.725935 | 3 |
| MODBUS | shared_slot_route | 0.016137 | -0.644113 | 3 |
| MODBUS | execute_score | 0.028204 | 0.444994 | 3 |
| MODBUS | equivalent_program | 0.016143 | -0.650530 | 3 |
| SMB2 | hybrid | 0.524464 | 2.153754 | 3 |
| SMB2 | route_sink | 0.065838 | 0.251446 | 3 |
| SMB2 | route_direct | 0.135603 | -0.623231 | 3 |
| SMB2 | route_joint | 0.145413 | -0.447814 | 3 |
| SMB2 | axis_direct | 0.122356 | -0.786807 | 3 |
| SMB2 | attr_only | 0.490426 | -2.783654 | 3 |
| SMB2 | attr_content | 0.750977 | 1.948652 | 3 |
| SMB2 | attr_distance | 0.440854 | -1.837799 | 3 |
| SMB2 | attr_product | 0.468873 | -4.077723 | 3 |
| SMB2 | attr_mix | 0.479936 | 2.055818 | 3 |
| SMB2 | mix_half | 0.340806 | 1.650172 | 3 |
| SMB2 | mix_learned | 0.557617 | 1.914926 | 3 |
| SMB2 | mix_entropy | 0.560098 | 2.096471 | 3 |
| SMB2 | power_learned | 0.538426 | 2.032198 | 3 |
| SMB2 | weak_product | 0.599232 | 2.135531 | 3 |
| SMB2 | stopgrad_product | 0.575340 | 2.039962 | 3 |
| SMB2 | smooth_route | 0.082523 | -0.215278 | 3 |
| SMB2 | soft_joint | 0.061503 | -0.393313 | 3 |
| SMB2 | valid_mass_route | 0.089083 | 0.397961 | 3 |
| SMB2 | cnn_shared_route | 0.094042 | -0.548220 | 3 |
| SMB2 | cnn_shared_attr | 0.551585 | -0.353717 | 3 |
| SMB2 | gru_shared_route | 0.114621 | -0.951508 | 3 |
| SMB2 | gru_shared_attr | 0.466787 | -2.433086 | 3 |
| SMB2 | shared_slot_hybrid | 0.507656 | 2.392247 | 3 |
| SMB2 | aux_small | 0.615693 | 2.455833 | 3 |
| SMB2 | aux_large | 0.439570 | 1.712815 | 3 |
| SMB2 | bilinear_program | 0.149612 | -0.567903 | 3 |
| SMB2 | shared_slot_route | 0.137899 | -0.150030 | 3 |
| SMB2 | execute_score | 0.250124 | 1.130348 | 3 |
| SMB2 | equivalent_program | 0.117160 | -0.819364 | 3 |
| TLS | hybrid | 0.082770 | 0.493773 | 3 |
| TLS | route_sink | 0.043885 | -0.022435 | 3 |
| TLS | route_direct | 0.185437 | -0.527688 | 3 |
| TLS | route_joint | 0.182600 | -1.019273 | 3 |
| TLS | axis_direct | 0.189024 | -0.844638 | 3 |
| TLS | attr_only | 0.236902 | -3.116442 | 3 |
| TLS | attr_content | 0.207204 | 0.194391 | 3 |
| TLS | attr_distance | 0.210132 | -3.070242 | 3 |
| TLS | attr_product | 0.208326 | -2.936434 | 3 |
| TLS | attr_mix | 0.174411 | -0.717730 | 3 |
| TLS | mix_half | 0.138824 | 0.625525 | 3 |
| TLS | mix_learned | 0.120464 | 0.460114 | 3 |
| TLS | mix_entropy | 0.122885 | 0.012107 | 3 |
| TLS | power_learned | 0.128684 | 0.385135 | 3 |
| TLS | weak_product | 0.112472 | 0.245735 | 3 |
| TLS | stopgrad_product | 0.090200 | 0.283821 | 3 |
| TLS | smooth_route | 0.147473 | 0.060403 | 3 |
| TLS | soft_joint | 0.171686 | -0.103382 | 3 |
| TLS | valid_mass_route | 0.039224 | -0.109498 | 3 |
| TLS | cnn_shared_route | 0.124326 | -0.219612 | 3 |
| TLS | cnn_shared_attr | 0.273360 | -0.940765 | 3 |
| TLS | gru_shared_route | 0.126178 | -0.099354 | 3 |
| TLS | gru_shared_attr | 0.332508 | -2.091574 | 3 |
| TLS | shared_slot_hybrid | 0.233856 | 0.991659 | 3 |
| TLS | aux_small | 0.082310 | 0.022132 | 3 |
| TLS | aux_large | 0.139319 | 0.553381 | 3 |
| TLS | bilinear_program | 0.178328 | -0.568982 | 3 |
| TLS | shared_slot_route | 0.186395 | -0.253830 | 3 |
| TLS | execute_score | 0.201594 | 0.152638 | 3 |
| TLS | equivalent_program | 0.195161 | -0.614992 | 3 |

## Screen complete validation matrix

Both excluded protocols are retained for transparency; only outer-target-free evidence enters each choice.

| Sources | Validation | Backbone | Formula | Seed | p(target) | Balanced p | NLL | Balanced log gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dns,modbus | tls | tape | hybrid | 170101 | 0.734891 | 0.734891 | 0.321844 | 4.393485 |
| dns,modbus | smb2 | tape | hybrid | 170101 | 0.007941 | 0.017268 | 5.587409 | 0.548614 |
| dns,modbus | tls | tape | route_sink | 170101 | 0.018782 | 0.018782 | 4.477910 | 0.237420 |
| dns,modbus | smb2 | tape | route_sink | 170101 | 0.003589 | 0.003400 | 5.689145 | -0.361818 |
| dns,modbus | tls | tape | route_direct | 170101 | 0.011033 | 0.011033 | 5.598958 | -0.883629 |
| dns,modbus | smb2 | tape | route_direct | 170101 | 0.004091 | 0.004612 | 5.992527 | -0.586335 |
| dns,modbus | tls | tape | route_joint | 170101 | 0.025392 | 0.025392 | 5.485956 | -0.770627 |
| dns,modbus | smb2 | tape | route_joint | 170101 | 0.001873 | 0.001441 | 6.967690 | -1.699744 |
| dns,modbus | tls | tape | axis_direct | 170101 | 0.007312 | 0.007312 | 5.788035 | -1.072706 |
| dns,modbus | smb2 | tape | axis_direct | 170101 | 0.001674 | 0.001711 | 7.063800 | -1.603972 |
| dns,modbus | tls | tape | attr_only | 170101 | 0.619162 | 0.619162 | 1.067937 | 3.647392 |
| dns,modbus | smb2 | tape | attr_only | 170101 | 0.010839 | 0.008437 | 6.175127 | -2.079850 |
| dns,modbus | tls | tape | attr_content | 170101 | 0.863550 | 0.863550 | 0.286296 | 4.429034 |
| dns,modbus | smb2 | tape | attr_content | 170101 | 0.056582 | 0.083179 | 5.720614 | -0.322847 |
| dns,modbus | tls | tape | attr_distance | 170101 | 0.498595 | 0.498595 | 0.916696 | 3.798634 |
| dns,modbus | smb2 | tape | attr_distance | 170101 | 0.006772 | 0.006027 | 7.003533 | -2.416210 |
| dns,modbus | tls | tape | attr_product | 170101 | 0.525504 | 0.525504 | 0.959794 | 3.755535 |
| dns,modbus | smb2 | tape | attr_product | 170101 | 0.012821 | 0.012729 | 6.395152 | -1.859131 |
| dns,modbus | tls | tape | attr_mix | 170101 | 0.497207 | 0.497207 | 1.136660 | 3.578669 |
| dns,modbus | smb2 | tape | attr_mix | 170101 | 0.006430 | 0.004976 | 5.833803 | -1.118118 |
| dns,modbus | tls | tape | mix_half | 170101 | 0.497468 | 0.497468 | 0.702684 | 4.012645 |
| dns,modbus | smb2 | tape | mix_half | 170101 | 0.006715 | 0.014068 | 5.645846 | 0.446942 |
| dns,modbus | tls | tape | mix_learned | 170101 | 0.887514 | 0.887514 | 0.121133 | 4.594197 |
| dns,modbus | smb2 | tape | mix_learned | 170101 | 0.007251 | 0.013600 | 5.834807 | 0.313989 |
| dns,modbus | tls | tape | mix_entropy | 170101 | 0.882565 | 0.882565 | 0.140939 | 4.574390 |
| dns,modbus | smb2 | tape | mix_entropy | 170101 | 0.004152 | 0.008225 | 7.652531 | -1.328878 |
| dns,modbus | tls | tape | power_learned | 170101 | 0.694100 | 0.694100 | 0.418192 | 4.297137 |
| dns,modbus | smb2 | tape | power_learned | 170101 | 0.017230 | 0.029743 | 5.320275 | 0.744232 |
| dns,modbus | tls | tape | weak_product | 170101 | 0.913877 | 0.913877 | 0.103473 | 4.611856 |
| dns,modbus | smb2 | tape | weak_product | 170101 | 0.019555 | 0.031636 | 6.883809 | -0.372023 |
| dns,modbus | tls | tape | stopgrad_product | 170101 | 0.874381 | 0.874381 | 0.162049 | 4.553281 |
| dns,modbus | smb2 | tape | stopgrad_product | 170101 | 0.021003 | 0.034828 | 6.411060 | 0.069983 |
| dns,modbus | tls | tape | smooth_route | 170101 | 0.022605 | 0.022605 | 5.095391 | -0.380061 |
| dns,modbus | smb2 | tape | smooth_route | 170101 | 0.008039 | 0.005230 | 5.640399 | -0.486838 |
| dns,modbus | tls | tape | soft_joint | 170101 | 0.015150 | 0.015150 | 5.242315 | -0.526986 |
| dns,modbus | smb2 | tape | soft_joint | 170101 | 0.012165 | 0.009030 | 5.130302 | 0.251549 |
| dns,modbus | tls | tape | valid_mass_route | 170101 | 0.019326 | 0.019326 | 4.350118 | 0.365211 |
| dns,modbus | smb2 | tape | valid_mass_route | 170101 | 0.003885 | 0.003298 | 5.758626 | -0.474079 |
| dns,modbus | tls | none | cnn_shared_route | 170101 | 0.076440 | 0.076440 | 3.510835 | 1.204494 |
| dns,modbus | smb2 | none | cnn_shared_route | 170101 | 0.007027 | 0.018961 | 5.665213 | 0.565506 |
| dns,modbus | tls | none | cnn_shared_attr | 170101 | 0.553655 | 0.553655 | 1.056494 | 3.658836 |
| dns,modbus | smb2 | none | cnn_shared_attr | 170101 | 0.047352 | 0.062464 | 7.150081 | -1.082033 |
| dns,modbus | tls | none | gru_shared_route | 170101 | 0.017452 | 0.017452 | 5.079327 | -0.363997 |
| dns,modbus | smb2 | none | gru_shared_route | 170101 | 0.010777 | 0.029717 | 5.725199 | 0.597150 |
| dns,modbus | tls | none | gru_shared_attr | 170101 | 0.414901 | 0.414901 | 1.006314 | 3.709015 |
| dns,modbus | smb2 | none | gru_shared_attr | 170101 | 0.066744 | 0.088707 | 6.520787 | 0.003652 |
| dns,modbus | tls | tape | shared_slot_hybrid | 170101 | 0.660545 | 0.660545 | 0.445178 | 4.270152 |
| dns,modbus | smb2 | tape | shared_slot_hybrid | 170101 | 0.064827 | 0.081777 | 5.477935 | 0.179444 |
| dns,modbus | tls | tape | aux_small | 170101 | 0.892571 | 0.892571 | 0.127239 | 4.588091 |
| dns,modbus | smb2 | tape | aux_small | 170101 | 0.036933 | 0.065909 | 5.477081 | 1.252032 |
| dns,modbus | tls | tape | aux_large | 170101 | 0.463561 | 0.463561 | 0.910605 | 3.804724 |
| dns,modbus | smb2 | tape | aux_large | 170101 | 0.013947 | 0.017178 | 5.289147 | 0.327351 |
| dns,modbus | tls | tape | bilinear_program | 170101 | 0.013898 | 0.013898 | 5.821920 | -1.106591 |
| dns,modbus | smb2 | tape | bilinear_program | 170101 | 0.003703 | 0.002819 | 6.163787 | -0.980780 |
| dns,modbus | tls | tape | shared_slot_route | 170101 | 0.014202 | 0.014202 | 4.944369 | -0.229039 |
| dns,modbus | smb2 | tape | shared_slot_route | 170101 | 0.005713 | 0.004656 | 5.531662 | -0.212021 |
| dns,modbus | tls | tape | execute_score | 170101 | 0.147677 | 0.147677 | 2.939417 | 1.775912 |
| dns,modbus | smb2 | tape | execute_score | 170101 | 0.004647 | 0.003174 | 6.099703 | -0.872778 |
| dns,modbus | tls | tape | equivalent_program | 170101 | 0.006923 | 0.006923 | 6.036757 | -1.321427 |
| dns,modbus | smb2 | tape | equivalent_program | 170101 | 0.001700 | 0.001581 | 6.804753 | -1.421344 |
| dns,tls | modbus | tape | hybrid | 170101 | 0.822110 | 0.822110 | 0.214502 | 2.624251 |
| dns,tls | smb2 | tape | hybrid | 170101 | 0.002998 | 0.008074 | 6.272554 | -0.440087 |
| dns,tls | modbus | tape | route_sink | 170101 | 0.166494 | 0.166494 | 2.225904 | 0.612849 |
| dns,tls | smb2 | tape | route_sink | 170101 | 0.004412 | 0.004039 | 5.477549 | -0.184082 |
| dns,tls | modbus | tape | route_direct | 170101 | 0.392228 | 0.392228 | 1.335253 | 1.503500 |
| dns,tls | smb2 | tape | route_direct | 170101 | 0.004932 | 0.005473 | 5.369828 | 0.146192 |
| dns,tls | modbus | tape | route_joint | 170101 | 0.403403 | 0.403403 | 1.394828 | 1.443924 |
| dns,tls | smb2 | tape | route_joint | 170101 | 0.004005 | 0.004603 | 5.614392 | -0.060244 |
| dns,tls | modbus | tape | axis_direct | 170101 | 0.354816 | 0.354816 | 1.476646 | 1.362107 |
| dns,tls | smb2 | tape | axis_direct | 170101 | 0.004874 | 0.005191 | 5.376555 | 0.098463 |
| dns,tls | modbus | tape | attr_only | 170101 | 0.849721 | 0.849721 | 0.235719 | 2.603034 |
| dns,tls | smb2 | tape | attr_only | 170101 | 0.020059 | 0.021020 | 6.423652 | -1.111509 |
| dns,tls | modbus | tape | attr_content | 170101 | 0.996243 | 0.996243 | 0.003846 | 2.834907 |
| dns,tls | smb2 | tape | attr_content | 170101 | 0.021023 | 0.028487 | 6.019258 | -0.643372 |
| dns,tls | modbus | tape | attr_distance | 170101 | 0.783538 | 0.783538 | 0.268155 | 2.570598 |
| dns,tls | smb2 | tape | attr_distance | 170101 | 0.028149 | 0.033378 | 5.929359 | -0.451506 |
| dns,tls | modbus | tape | attr_product | 170101 | 0.851705 | 0.851705 | 0.248747 | 2.590005 |
| dns,tls | smb2 | tape | attr_product | 170101 | 0.063863 | 0.079271 | 5.987459 | 0.013356 |
| dns,tls | modbus | tape | attr_mix | 170101 | 0.826795 | 0.826795 | 0.275374 | 2.563379 |
| dns,tls | smb2 | tape | attr_mix | 170101 | 0.048298 | 0.054598 | 5.541284 | 0.448766 |
| dns,tls | modbus | tape | mix_half | 170101 | 0.514865 | 0.514865 | 0.674330 | 2.164423 |
| dns,tls | smb2 | tape | mix_half | 170101 | 0.002216 | 0.002391 | 6.159329 | -0.686030 |
| dns,tls | modbus | tape | mix_learned | 170101 | 0.774510 | 0.774510 | 0.357335 | 2.481418 |
| dns,tls | smb2 | tape | mix_learned | 170101 | 0.001686 | 0.002577 | 7.148594 | -1.107749 |
| dns,tls | modbus | tape | mix_entropy | 170101 | 0.780197 | 0.780197 | 0.277107 | 2.561646 |
| dns,tls | smb2 | tape | mix_entropy | 170101 | 0.000810 | 0.001074 | 8.586710 | -2.783518 |
| dns,tls | modbus | tape | power_learned | 170101 | 0.908678 | 0.908678 | 0.102851 | 2.735902 |
| dns,tls | smb2 | tape | power_learned | 170101 | 0.009187 | 0.020235 | 5.401992 | 0.736092 |
| dns,tls | modbus | tape | weak_product | 170101 | 0.861368 | 0.861368 | 0.265307 | 2.573446 |
| dns,tls | smb2 | tape | weak_product | 170101 | 0.001139 | 0.001695 | 7.627340 | -1.897437 |
| dns,tls | modbus | tape | stopgrad_product | 170101 | 0.833814 | 0.833814 | 0.337744 | 2.501009 |
| dns,tls | smb2 | tape | stopgrad_product | 170101 | 0.001423 | 0.002335 | 7.094430 | -1.415718 |
| dns,tls | modbus | tape | smooth_route | 170101 | 0.220477 | 0.220477 | 1.907892 | 0.930861 |
| dns,tls | smb2 | tape | smooth_route | 170101 | 0.004511 | 0.004190 | 5.454920 | -0.139340 |
| dns,tls | modbus | tape | soft_joint | 170101 | 0.158736 | 0.158736 | 2.140870 | 0.697883 |
| dns,tls | smb2 | tape | soft_joint | 170101 | 0.007185 | 0.012707 | 5.325308 | 0.598380 |
| dns,tls | modbus | tape | valid_mass_route | 170101 | 0.236399 | 0.236399 | 1.863098 | 0.975655 |
| dns,tls | smb2 | tape | valid_mass_route | 170101 | 0.004631 | 0.005061 | 5.422357 | 0.076290 |
| dns,tls | modbus | none | cnn_shared_route | 170101 | 0.204652 | 0.204652 | 2.281797 | 0.556956 |
| dns,tls | smb2 | none | cnn_shared_route | 170101 | 0.009383 | 0.024552 | 5.376904 | 0.882309 |
| dns,tls | modbus | none | cnn_shared_attr | 170101 | 0.912892 | 0.912892 | 0.092988 | 2.745765 |
| dns,tls | smb2 | none | cnn_shared_attr | 170101 | 0.081180 | 0.123984 | 5.883003 | 0.742123 |
| dns,tls | modbus | none | gru_shared_route | 170101 | 0.326112 | 0.326112 | 1.512760 | 1.325993 |
| dns,tls | smb2 | none | gru_shared_route | 170101 | 0.007364 | 0.014444 | 5.273947 | 0.704104 |
| dns,tls | modbus | none | gru_shared_attr | 170101 | 0.951295 | 0.951295 | 0.051982 | 2.786771 |
| dns,tls | smb2 | none | gru_shared_attr | 170101 | 0.069297 | 0.113087 | 5.782932 | 0.727060 |
| dns,tls | modbus | tape | shared_slot_hybrid | 170101 | 0.839627 | 0.839627 | 0.202487 | 2.636266 |
| dns,tls | smb2 | tape | shared_slot_hybrid | 170101 | 0.033910 | 0.050223 | 4.957559 | 0.962369 |
| dns,tls | modbus | tape | aux_small | 170101 | 0.848075 | 0.848075 | 0.181130 | 2.657623 |
| dns,tls | smb2 | tape | aux_small | 170101 | 0.008998 | 0.028852 | 5.258279 | 0.963897 |
| dns,tls | modbus | tape | aux_large | 170101 | 0.843448 | 0.843448 | 0.174145 | 2.664608 |
| dns,tls | smb2 | tape | aux_large | 170101 | 0.006891 | 0.009583 | 5.781971 | -0.188089 |
| dns,tls | modbus | tape | bilinear_program | 170101 | 0.429465 | 0.429465 | 1.194743 | 1.644010 |
| dns,tls | smb2 | tape | bilinear_program | 170101 | 0.004435 | 0.003688 | 5.544492 | -0.397722 |
| dns,tls | modbus | tape | shared_slot_route | 170101 | 0.391595 | 0.391595 | 1.245222 | 1.593531 |
| dns,tls | smb2 | tape | shared_slot_route | 170101 | 0.004183 | 0.003695 | 5.552459 | -0.304045 |
| dns,tls | modbus | tape | execute_score | 170101 | 0.589841 | 0.589841 | 0.690053 | 2.148700 |
| dns,tls | smb2 | tape | execute_score | 170101 | 0.006463 | 0.009293 | 5.280800 | 0.472748 |
| dns,tls | modbus | tape | equivalent_program | 170101 | 0.341008 | 0.341008 | 1.485940 | 1.352813 |
| dns,tls | smb2 | tape | equivalent_program | 170101 | 0.004663 | 0.005029 | 5.425581 | 0.063695 |
| dns,smb2 | modbus | tape | hybrid | 170101 | 0.214361 | 0.214361 | 1.802339 | 1.036414 |
| dns,smb2 | tls | tape | hybrid | 170101 | 0.043160 | 0.043160 | 3.753862 | 0.961468 |
| dns,smb2 | modbus | tape | route_sink | 170101 | 0.116019 | 0.116019 | 2.479873 | 0.358880 |
| dns,smb2 | tls | tape | route_sink | 170101 | 0.017357 | 0.017357 | 4.440820 | 0.274510 |
| dns,smb2 | modbus | tape | route_direct | 170101 | 0.467289 | 0.467289 | 1.376045 | 1.462708 |
| dns,smb2 | tls | tape | route_direct | 170101 | 0.022248 | 0.022248 | 5.149506 | -0.434177 |
| dns,smb2 | modbus | tape | route_joint | 170101 | 0.431787 | 0.431787 | 1.672836 | 1.165917 |
| dns,smb2 | tls | tape | route_joint | 170101 | 0.012704 | 0.012704 | 5.594844 | -0.879515 |
| dns,smb2 | modbus | tape | axis_direct | 170101 | 0.499657 | 0.499657 | 1.358477 | 1.480275 |
| dns,smb2 | tls | tape | axis_direct | 170101 | 0.023055 | 0.023055 | 5.052377 | -0.337048 |
| dns,smb2 | modbus | tape | attr_only | 170101 | 0.700579 | 0.700579 | 0.561082 | 2.277671 |
| dns,smb2 | tls | tape | attr_only | 170101 | 0.070403 | 0.070403 | 3.432782 | 1.282547 |
| dns,smb2 | modbus | tape | attr_content | 170101 | 0.525182 | 0.525182 | 0.831843 | 2.006910 |
| dns,smb2 | tls | tape | attr_content | 170101 | 0.191118 | 0.191118 | 2.233482 | 2.481848 |
| dns,smb2 | modbus | tape | attr_distance | 170101 | 0.619901 | 0.619901 | 0.841458 | 1.997295 |
| dns,smb2 | tls | tape | attr_distance | 170101 | 0.037947 | 0.037947 | 4.334037 | 0.381292 |
| dns,smb2 | modbus | tape | attr_product | 170101 | 0.608212 | 0.608212 | 0.984828 | 1.853925 |
| dns,smb2 | tls | tape | attr_product | 170101 | 0.033085 | 0.033085 | 4.525534 | 0.189796 |
| dns,smb2 | modbus | tape | attr_mix | 170101 | 0.489181 | 0.489181 | 1.329057 | 1.509696 |
| dns,smb2 | tls | tape | attr_mix | 170101 | 0.027178 | 0.027178 | 4.604424 | 0.110906 |
| dns,smb2 | modbus | tape | mix_half | 170101 | 0.339549 | 0.339549 | 1.185827 | 1.652926 |
| dns,smb2 | tls | tape | mix_half | 170101 | 0.019500 | 0.019500 | 4.193900 | 0.521429 |
| dns,smb2 | modbus | tape | mix_learned | 170101 | 0.298585 | 0.298585 | 1.314335 | 1.524417 |
| dns,smb2 | tls | tape | mix_learned | 170101 | 0.017846 | 0.017846 | 4.286912 | 0.428418 |
| dns,smb2 | modbus | tape | mix_entropy | 170101 | 0.235358 | 0.235358 | 1.533697 | 1.305056 |
| dns,smb2 | tls | tape | mix_entropy | 170101 | 0.085939 | 0.085939 | 2.725816 | 1.989514 |
| dns,smb2 | modbus | tape | power_learned | 170101 | 0.331038 | 0.331038 | 1.462976 | 1.375777 |
| dns,smb2 | tls | tape | power_learned | 170101 | 0.049685 | 0.049685 | 4.024340 | 0.690989 |
| dns,smb2 | modbus | tape | weak_product | 170101 | 0.187315 | 0.187315 | 1.817082 | 1.021671 |
| dns,smb2 | tls | tape | weak_product | 170101 | 0.039322 | 0.039322 | 3.782564 | 0.932765 |
| dns,smb2 | modbus | tape | stopgrad_product | 170101 | 0.195845 | 0.195845 | 1.824287 | 1.014466 |
| dns,smb2 | tls | tape | stopgrad_product | 170101 | 0.030118 | 0.030118 | 4.098908 | 0.616422 |
| dns,smb2 | modbus | tape | smooth_route | 170101 | 0.404097 | 0.404097 | 1.402159 | 1.436594 |
| dns,smb2 | tls | tape | smooth_route | 170101 | 0.020050 | 0.020050 | 4.648307 | 0.067022 |
| dns,smb2 | modbus | tape | soft_joint | 170101 | 0.410361 | 0.410361 | 1.435998 | 1.402755 |
| dns,smb2 | tls | tape | soft_joint | 170101 | 0.015636 | 0.015636 | 5.343220 | -0.627890 |
| dns,smb2 | modbus | tape | valid_mass_route | 170101 | 0.102409 | 0.102409 | 2.605070 | 0.233683 |
| dns,smb2 | tls | tape | valid_mass_route | 170101 | 0.017677 | 0.017677 | 4.414676 | 0.300654 |
| dns,smb2 | modbus | none | cnn_shared_route | 170101 | 0.324757 | 0.324757 | 1.762474 | 1.076279 |
| dns,smb2 | tls | none | cnn_shared_route | 170101 | 0.026592 | 0.026592 | 5.694974 | -0.979644 |
| dns,smb2 | modbus | none | cnn_shared_attr | 170101 | 0.748121 | 0.748121 | 0.383246 | 2.455507 |
| dns,smb2 | tls | none | cnn_shared_attr | 170101 | 0.072643 | 0.072643 | 3.521694 | 1.193636 |
| dns,smb2 | modbus | none | gru_shared_route | 170101 | 0.328782 | 0.328782 | 1.753493 | 1.085260 |
| dns,smb2 | tls | none | gru_shared_route | 170101 | 0.021387 | 0.021387 | 4.696559 | 0.018771 |
| dns,smb2 | modbus | none | gru_shared_attr | 170101 | 0.726139 | 0.726139 | 0.411712 | 2.427041 |
| dns,smb2 | tls | none | gru_shared_attr | 170101 | 0.071366 | 0.071366 | 3.089844 | 1.625486 |
| dns,smb2 | modbus | tape | shared_slot_hybrid | 170101 | 0.468892 | 0.468892 | 0.852036 | 1.986717 |
| dns,smb2 | tls | tape | shared_slot_hybrid | 170101 | 0.067859 | 0.067859 | 2.933895 | 1.781434 |
| dns,smb2 | modbus | tape | aux_small | 170101 | 0.038931 | 0.038931 | 3.927379 | -1.088626 |
| dns,smb2 | tls | tape | aux_small | 170101 | 0.002258 | 0.002258 | 6.685315 | -1.969986 |
| dns,smb2 | modbus | tape | aux_large | 170101 | 0.384147 | 0.384147 | 1.152740 | 1.686013 |
| dns,smb2 | tls | tape | aux_large | 170101 | 0.032753 | 0.032753 | 3.824787 | 0.890543 |
| dns,smb2 | modbus | tape | bilinear_program | 170101 | 0.461633 | 0.461633 | 1.366240 | 1.472512 |
| dns,smb2 | tls | tape | bilinear_program | 170101 | 0.022915 | 0.022915 | 5.070013 | -0.354684 |
| dns,smb2 | modbus | tape | shared_slot_route | 170101 | 0.496889 | 0.496889 | 1.190587 | 1.648166 |
| dns,smb2 | tls | tape | shared_slot_route | 170101 | 0.020277 | 0.020277 | 4.993626 | -0.278296 |
| dns,smb2 | modbus | tape | execute_score | 170101 | 0.548401 | 0.548401 | 1.139125 | 1.699628 |
| dns,smb2 | tls | tape | execute_score | 170101 | 0.028446 | 0.028446 | 4.101424 | 0.613906 |
| dns,smb2 | modbus | tape | equivalent_program | 170101 | 0.531825 | 0.531825 | 1.195964 | 1.642789 |
| dns,smb2 | tls | tape | equivalent_program | 170101 | 0.018008 | 0.018008 | 5.127513 | -0.412183 |
| modbus,tls | dns | tape | hybrid | 170101 | 0.016366 | 0.016390 | 4.900838 | -0.556473 |
| modbus,tls | smb2 | tape | hybrid | 170101 | 0.001599 | 0.004174 | 6.882740 | -1.095570 |
| modbus,tls | dns | tape | route_sink | 170101 | 0.013599 | 0.012239 | 4.625658 | -0.095929 |
| modbus,tls | smb2 | tape | route_sink | 170101 | 0.003451 | 0.004052 | 6.268271 | -0.616130 |
| modbus,tls | dns | tape | route_direct | 170101 | 0.002127 | 0.003547 | 7.026679 | -2.489565 |
| modbus,tls | smb2 | tape | route_direct | 170101 | 0.005901 | 0.013522 | 6.708980 | -0.355503 |
| modbus,tls | dns | tape | route_joint | 170101 | 0.005775 | 0.007445 | 6.380190 | -2.016740 |
| modbus,tls | smb2 | tape | route_joint | 170101 | 0.006931 | 0.014649 | 6.311083 | -0.107287 |
| modbus,tls | dns | tape | axis_direct | 170101 | 0.001814 | 0.004939 | 7.311654 | -2.649822 |
| modbus,tls | smb2 | tape | axis_direct | 170101 | 0.006069 | 0.014102 | 6.581584 | -0.248753 |
| modbus,tls | dns | tape | attr_only | 170101 | 0.000403 | 0.002396 | 25.250100 | -14.601389 |
| modbus,tls | smb2 | tape | attr_only | 170101 | 0.059601 | 0.050689 | 13.274992 | -5.921215 |
| modbus,tls | dns | tape | attr_content | 170101 | 0.064258 | 0.393139 | 9.186277 | -1.417984 |
| modbus,tls | smb2 | tape | attr_content | 170101 | 0.235503 | 0.214194 | 7.305151 | -0.664606 |
| modbus,tls | dns | tape | attr_distance | 170101 | 0.006752 | 0.040429 | 23.737783 | -11.882629 |
| modbus,tls | smb2 | tape | attr_distance | 170101 | 0.064708 | 0.059288 | 13.541252 | -4.776026 |
| modbus,tls | dns | tape | attr_product | 170101 | 0.004682 | 0.029412 | 31.920623 | -18.578710 |
| modbus,tls | smb2 | tape | attr_product | 170101 | 0.000203 | 0.000127 | 25.305306 | -17.762909 |
| modbus,tls | dns | tape | attr_mix | 170101 | 0.020508 | 0.115806 | 7.610733 | 0.025407 |
| modbus,tls | smb2 | tape | attr_mix | 170101 | 0.007558 | 0.006199 | 9.761308 | -3.609930 |
| modbus,tls | dns | tape | mix_half | 170101 | 0.009899 | 0.010084 | 5.432837 | -1.226551 |
| modbus,tls | smb2 | tape | mix_half | 170101 | 0.002594 | 0.005118 | 7.159114 | -0.925033 |
| modbus,tls | dns | tape | mix_learned | 170101 | 0.010245 | 0.010827 | 6.076976 | -1.330836 |
| modbus,tls | smb2 | tape | mix_learned | 170101 | 0.002542 | 0.004390 | 7.592686 | -1.248411 |
| modbus,tls | dns | tape | mix_entropy | 170101 | 0.018379 | 0.017532 | 4.988718 | -0.846622 |
| modbus,tls | smb2 | tape | mix_entropy | 170101 | 0.000778 | 0.001082 | 9.114272 | -2.765848 |
| modbus,tls | dns | tape | power_learned | 170101 | 0.012831 | 0.012500 | 5.132892 | -0.936444 |
| modbus,tls | smb2 | tape | power_learned | 170101 | 0.007609 | 0.023393 | 6.081071 | -0.239304 |
| modbus,tls | dns | tape | weak_product | 170101 | 0.022164 | 0.022451 | 5.918838 | -0.778711 |
| modbus,tls | smb2 | tape | weak_product | 170101 | 0.001271 | 0.001641 | 10.595191 | -3.146554 |
| modbus,tls | dns | tape | stopgrad_product | 170101 | 0.016907 | 0.017826 | 5.841802 | -0.934404 |
| modbus,tls | smb2 | tape | stopgrad_product | 170101 | 0.000806 | 0.001048 | 10.083623 | -3.069469 |
| modbus,tls | dns | tape | smooth_route | 170101 | 0.004246 | 0.004489 | 5.585173 | -1.196633 |
| modbus,tls | smb2 | tape | smooth_route | 170101 | 0.003844 | 0.007118 | 6.171135 | -0.142797 |
| modbus,tls | dns | tape | soft_joint | 170101 | 0.006907 | 0.010621 | 5.880218 | -1.350835 |
| modbus,tls | smb2 | tape | soft_joint | 170101 | 0.017524 | 0.041346 | 5.835317 | 0.610503 |
| modbus,tls | dns | tape | valid_mass_route | 170101 | 0.012518 | 0.011525 | 4.704326 | -0.146983 |
| modbus,tls | smb2 | tape | valid_mass_route | 170101 | 0.003424 | 0.004533 | 5.783130 | -0.119176 |
| modbus,tls | dns | none | cnn_shared_route | 170101 | 0.000710 | 0.001035 | 7.843241 | -3.406110 |
| modbus,tls | smb2 | none | cnn_shared_route | 170101 | 0.005806 | 0.010423 | 6.805650 | -0.319880 |
| modbus,tls | dns | none | cnn_shared_attr | 170101 | 0.030589 | 0.188209 | 17.114791 | -7.465750 |
| modbus,tls | smb2 | none | cnn_shared_attr | 170101 | 0.104018 | 0.127004 | 8.056860 | -0.319130 |
| modbus,tls | dns | none | gru_shared_route | 170101 | 0.000393 | 0.000299 | 8.042698 | -3.816519 |
| modbus,tls | smb2 | none | gru_shared_route | 170101 | 0.001816 | 0.003570 | 7.732602 | -1.294852 |
| modbus,tls | dns | none | gru_shared_attr | 170101 | 0.005675 | 0.034166 | 23.763384 | -13.795043 |
| modbus,tls | smb2 | none | gru_shared_attr | 170101 | 0.000664 | 0.002971 | 16.019357 | -7.965182 |
| modbus,tls | dns | tape | shared_slot_hybrid | 170101 | 0.013943 | 0.022796 | 4.960974 | 0.270323 |
| modbus,tls | smb2 | tape | shared_slot_hybrid | 170101 | 0.057391 | 0.096871 | 5.884300 | 0.863158 |
| modbus,tls | dns | tape | aux_small | 170101 | 0.020075 | 0.106434 | 6.202305 | 0.121784 |
| modbus,tls | smb2 | tape | aux_small | 170101 | 0.090779 | 0.125662 | 5.371287 | 1.527175 |
| modbus,tls | dns | tape | aux_large | 170101 | 0.013489 | 0.011702 | 5.431565 | -1.330886 |
| modbus,tls | smb2 | tape | aux_large | 170101 | 0.001213 | 0.003524 | 8.302263 | -1.673075 |
| modbus,tls | dns | tape | bilinear_program | 170101 | 0.003080 | 0.005475 | 6.812335 | -2.241129 |
| modbus,tls | smb2 | tape | bilinear_program | 170101 | 0.013875 | 0.033837 | 6.246727 | 0.259169 |
| modbus,tls | dns | tape | shared_slot_route | 170101 | 0.004933 | 0.007901 | 6.582075 | -1.814582 |
| modbus,tls | smb2 | tape | shared_slot_route | 170101 | 0.009674 | 0.024053 | 6.611630 | -0.090425 |
| modbus,tls | dns | tape | execute_score | 170101 | 0.006585 | 0.012853 | 6.050509 | -0.533567 |
| modbus,tls | smb2 | tape | execute_score | 170101 | 0.024424 | 0.053368 | 5.337820 | 1.187182 |
| modbus,tls | dns | tape | equivalent_program | 170101 | 0.002128 | 0.003548 | 7.026576 | -2.489477 |
| modbus,tls | smb2 | tape | equivalent_program | 170101 | 0.005902 | 0.013524 | 6.708939 | -0.355420 |
| modbus,smb2 | dns | tape | hybrid | 170101 | 0.011807 | 0.016682 | 4.847792 | -0.103709 |
| modbus,smb2 | tls | tape | hybrid | 170101 | 0.601134 | 0.601134 | 0.602447 | 4.112882 |
| modbus,smb2 | dns | tape | route_sink | 170101 | 0.013595 | 0.012234 | 4.502011 | -0.064366 |
| modbus,smb2 | tls | tape | route_sink | 170101 | 0.136561 | 0.136561 | 3.838496 | 0.876833 |
| modbus,smb2 | dns | tape | route_direct | 170101 | 0.020625 | 0.084409 | 7.588680 | -2.459436 |
| modbus,smb2 | tls | tape | route_direct | 170101 | 0.505962 | 0.505962 | 3.242513 | 1.472816 |
| modbus,smb2 | dns | tape | route_joint | 170101 | 0.025209 | 0.114573 | 7.730004 | -2.523993 |
| modbus,smb2 | tls | tape | route_joint | 170101 | 0.393506 | 0.393506 | 4.847716 | -0.132387 |
| modbus,smb2 | dns | tape | axis_direct | 170101 | 0.015950 | 0.065703 | 7.554736 | -2.410217 |
| modbus,smb2 | tls | tape | axis_direct | 170101 | 0.536617 | 0.536617 | 3.182871 | 1.532458 |
| modbus,smb2 | dns | tape | attr_only | 170101 | 0.000675 | 0.001690 | 20.056945 | -9.547147 |
| modbus,smb2 | tls | tape | attr_only | 170101 | 0.541720 | 0.541720 | 2.754618 | 1.960712 |
| modbus,smb2 | dns | tape | attr_content | 170101 | 0.003317 | 0.013251 | 8.095037 | -1.100890 |
| modbus,smb2 | tls | tape | attr_content | 170101 | 0.688076 | 0.688076 | 0.612289 | 4.103040 |
| modbus,smb2 | dns | tape | attr_distance | 170101 | 0.004882 | 0.004467 | 17.809122 | -8.791811 |
| modbus,smb2 | tls | tape | attr_distance | 170101 | 0.548356 | 0.548356 | 2.175404 | 2.539926 |
| modbus,smb2 | dns | tape | attr_product | 170101 | 0.005839 | 0.004035 | 17.006143 | -8.804096 |
| modbus,smb2 | tls | tape | attr_product | 170101 | 0.509124 | 0.509124 | 2.821425 | 1.893905 |
| modbus,smb2 | dns | tape | attr_mix | 170101 | 0.007482 | 0.029075 | 7.773626 | -2.544769 |
| modbus,smb2 | tls | tape | attr_mix | 170101 | 0.482790 | 0.482790 | 3.101185 | 1.614145 |
| modbus,smb2 | dns | tape | mix_half | 170101 | 0.013277 | 0.062854 | 6.648115 | -0.223292 |
| modbus,smb2 | tls | tape | mix_half | 170101 | 0.670684 | 0.670684 | 0.471356 | 4.243973 |
| modbus,smb2 | dns | tape | mix_learned | 170101 | 0.010698 | 0.049207 | 7.101462 | -0.458065 |
| modbus,smb2 | tls | tape | mix_learned | 170101 | 0.839814 | 0.839814 | 0.194841 | 4.520488 |
| modbus,smb2 | dns | tape | mix_entropy | 170101 | 0.024265 | 0.125071 | 6.901151 | 0.060144 |
| modbus,smb2 | tls | tape | mix_entropy | 170101 | 0.886469 | 0.886469 | 0.156123 | 4.559207 |
| modbus,smb2 | dns | tape | power_learned | 170101 | 0.008984 | 0.025273 | 6.353308 | -0.964602 |
| modbus,smb2 | tls | tape | power_learned | 170101 | 0.415503 | 0.415503 | 2.688012 | 2.027318 |
| modbus,smb2 | dns | tape | weak_product | 170101 | 0.024081 | 0.118465 | 6.409292 | 0.087558 |
| modbus,smb2 | tls | tape | weak_product | 170101 | 0.903502 | 0.903502 | 0.111587 | 4.603743 |
| modbus,smb2 | dns | tape | stopgrad_product | 170101 | 0.013177 | 0.039928 | 5.747345 | -0.232987 |
| modbus,smb2 | tls | tape | stopgrad_product | 170101 | 0.847576 | 0.847576 | 0.330991 | 4.384339 |
| modbus,smb2 | dns | tape | smooth_route | 170101 | 0.010483 | 0.033092 | 5.529464 | -0.768546 |
| modbus,smb2 | tls | tape | smooth_route | 170101 | 0.441221 | 0.441221 | 2.802512 | 1.912818 |
| modbus,smb2 | dns | tape | soft_joint | 170101 | 0.020915 | 0.095667 | 6.990373 | -1.964451 |
| modbus,smb2 | tls | tape | soft_joint | 170101 | 0.505245 | 0.505245 | 3.227848 | 1.487481 |
| modbus,smb2 | dns | tape | valid_mass_route | 170101 | 0.012757 | 0.011965 | 4.591477 | -0.088098 |
| modbus,smb2 | tls | tape | valid_mass_route | 170101 | 0.430198 | 0.430198 | 2.896342 | 1.818988 |
| modbus,smb2 | dns | none | cnn_shared_route | 170101 | 0.012161 | 0.029259 | 7.109683 | -2.300620 |
| modbus,smb2 | tls | none | cnn_shared_route | 170101 | 0.007183 | 0.007183 | 5.476817 | -0.761488 |
| modbus,smb2 | dns | none | cnn_shared_attr | 170101 | 0.003975 | 0.009495 | 11.907908 | -4.195769 |
| modbus,smb2 | tls | none | cnn_shared_attr | 170101 | 0.186412 | 0.186412 | 2.581434 | 2.133895 |
| modbus,smb2 | dns | none | gru_shared_route | 170101 | 0.007968 | 0.020035 | 6.617357 | -1.980471 |
| modbus,smb2 | tls | none | gru_shared_route | 170101 | 0.009873 | 0.009873 | 5.282936 | -0.567607 |
| modbus,smb2 | dns | none | gru_shared_attr | 170101 | 0.030030 | 0.182677 | 19.419790 | -8.705414 |
| modbus,smb2 | tls | none | gru_shared_attr | 170101 | 0.606014 | 0.606014 | 0.629815 | 4.085514 |
| modbus,smb2 | dns | tape | shared_slot_hybrid | 170101 | 0.029435 | 0.150898 | 5.417993 | 0.808818 |
| modbus,smb2 | tls | tape | shared_slot_hybrid | 170101 | 0.646396 | 0.646396 | 0.462396 | 4.252933 |
| modbus,smb2 | dns | tape | aux_small | 170101 | 0.027089 | 0.142090 | 6.971083 | -0.097011 |
| modbus,smb2 | tls | tape | aux_small | 170101 | 0.909076 | 0.909076 | 0.110627 | 4.604703 |
| modbus,smb2 | dns | tape | aux_large | 170101 | 0.012080 | 0.016633 | 4.925828 | -0.353221 |
| modbus,smb2 | tls | tape | aux_large | 170101 | 0.541513 | 0.541513 | 0.727771 | 3.987558 |
| modbus,smb2 | dns | tape | bilinear_program | 170101 | 0.017269 | 0.070533 | 7.323924 | -2.198677 |
| modbus,smb2 | tls | tape | bilinear_program | 170101 | 0.390904 | 0.390904 | 3.681132 | 1.034198 |
| modbus,smb2 | dns | tape | shared_slot_route | 170101 | 0.013427 | 0.057641 | 7.261250 | -2.197634 |
| modbus,smb2 | tls | tape | shared_slot_route | 170101 | 0.443816 | 0.443816 | 4.369672 | 0.345658 |
| modbus,smb2 | dns | tape | execute_score | 170101 | 0.012401 | 0.053206 | 6.615474 | -0.368935 |
| modbus,smb2 | tls | tape | execute_score | 170101 | 0.445981 | 0.445981 | 3.242239 | 1.473091 |
| modbus,smb2 | dns | tape | equivalent_program | 170101 | 0.013475 | 0.052077 | 7.169664 | -2.066422 |
| modbus,smb2 | tls | tape | equivalent_program | 170101 | 0.424553 | 0.424553 | 3.867472 | 0.847858 |
| tls,smb2 | dns | tape | hybrid | 170101 | 0.018536 | 0.072479 | 5.415999 | 0.267856 |
| tls,smb2 | modbus | tape | hybrid | 170101 | 0.855509 | 0.855509 | 0.292286 | 2.546467 |
| tls,smb2 | dns | tape | route_sink | 170101 | 0.015310 | 0.012671 | 4.254616 | -0.001740 |
| tls,smb2 | modbus | tape | route_sink | 170101 | 0.060364 | 0.060364 | 2.952398 | -0.113645 |
| tls,smb2 | dns | tape | route_direct | 170101 | 0.015508 | 0.061049 | 6.489489 | -1.514378 |
| tls,smb2 | modbus | tape | route_direct | 170101 | 0.023144 | 0.023144 | 4.090222 | -1.251469 |
| tls,smb2 | dns | tape | route_joint | 170101 | 0.019273 | 0.082862 | 6.885823 | -1.895600 |
| tls,smb2 | modbus | tape | route_joint | 170101 | 0.035464 | 0.035464 | 4.411692 | -1.572939 |
| tls,smb2 | dns | tape | axis_direct | 170101 | 0.014366 | 0.056663 | 6.854022 | -1.878180 |
| tls,smb2 | modbus | tape | axis_direct | 170101 | 0.016562 | 0.016562 | 4.491031 | -1.652278 |
| tls,smb2 | dns | tape | attr_only | 170101 | 0.009309 | 0.036880 | 17.854694 | -8.308635 |
| tls,smb2 | modbus | tape | attr_only | 170101 | 0.335132 | 0.335132 | 2.578023 | 0.260730 |
| tls,smb2 | dns | tape | attr_content | 170101 | 0.018784 | 0.098522 | 7.174929 | 0.096697 |
| tls,smb2 | modbus | tape | attr_content | 170101 | 0.708286 | 0.708286 | 0.386704 | 2.452049 |
| tls,smb2 | dns | tape | attr_distance | 170101 | 0.005567 | 0.026222 | 18.218725 | -8.709028 |
| tls,smb2 | modbus | tape | attr_distance | 170101 | 0.205600 | 0.205600 | 3.089563 | -0.250810 |
| tls,smb2 | dns | tape | attr_product | 170101 | 0.006094 | 0.019353 | 17.490540 | -8.363341 |
| tls,smb2 | modbus | tape | attr_product | 170101 | 0.148279 | 0.148279 | 3.969769 | -1.131016 |
| tls,smb2 | dns | tape | attr_mix | 170101 | 0.003161 | 0.010917 | 8.095379 | -2.508362 |
| tls,smb2 | modbus | tape | attr_mix | 170101 | 0.413224 | 0.413224 | 2.383077 | 0.455676 |
| tls,smb2 | dns | tape | mix_half | 170101 | 0.015929 | 0.077928 | 6.759122 | -0.053998 |
| tls,smb2 | modbus | tape | mix_half | 170101 | 0.454481 | 0.454481 | 0.831024 | 2.007729 |
| tls,smb2 | dns | tape | mix_learned | 170101 | 0.013195 | 0.069392 | 7.385381 | -0.097795 |
| tls,smb2 | modbus | tape | mix_learned | 170101 | 0.732578 | 0.732578 | 0.480220 | 2.358533 |
| tls,smb2 | dns | tape | mix_entropy | 170101 | 0.023458 | 0.123588 | 6.466292 | 0.046631 |
| tls,smb2 | modbus | tape | mix_entropy | 170101 | 0.479197 | 0.479197 | 0.831496 | 2.007257 |
| tls,smb2 | dns | tape | power_learned | 170101 | 0.009264 | 0.037998 | 6.986510 | -1.271105 |
| tls,smb2 | modbus | tape | power_learned | 170101 | 0.346036 | 0.346036 | 1.605894 | 1.232859 |
| tls,smb2 | dns | tape | weak_product | 170101 | 0.021484 | 0.092793 | 6.219980 | 0.092092 |
| tls,smb2 | modbus | tape | weak_product | 170101 | 0.859172 | 0.859172 | 0.182479 | 2.656274 |
| tls,smb2 | dns | tape | stopgrad_product | 170101 | 0.018743 | 0.077836 | 6.127147 | -0.130539 |
| tls,smb2 | modbus | tape | stopgrad_product | 170101 | 0.775429 | 0.775429 | 0.328992 | 2.509761 |
| tls,smb2 | dns | tape | smooth_route | 170101 | 0.005745 | 0.013435 | 5.679442 | -1.193980 |
| tls,smb2 | modbus | tape | smooth_route | 170101 | 0.030542 | 0.030542 | 3.923052 | -1.084299 |
| tls,smb2 | dns | tape | soft_joint | 170101 | 0.010831 | 0.025432 | 5.281615 | -0.695009 |
| tls,smb2 | modbus | tape | soft_joint | 170101 | 0.030705 | 0.030705 | 3.677091 | -0.838338 |
| tls,smb2 | dns | tape | valid_mass_route | 170101 | 0.012742 | 0.011254 | 4.479214 | -0.181823 |
| tls,smb2 | modbus | tape | valid_mass_route | 170101 | 0.083966 | 0.083966 | 2.840479 | -0.001727 |
| tls,smb2 | dns | none | cnn_shared_route | 170101 | 0.010555 | 0.003398 | 7.211953 | -3.081853 |
| tls,smb2 | modbus | none | cnn_shared_route | 170101 | 0.049258 | 0.049258 | 3.388247 | -0.549494 |
| tls,smb2 | dns | none | cnn_shared_attr | 170101 | 0.015953 | 0.040815 | 11.221788 | -3.365473 |
| tls,smb2 | modbus | none | cnn_shared_attr | 170101 | 0.370723 | 0.370723 | 1.266732 | 1.572021 |
| tls,smb2 | dns | none | gru_shared_route | 170101 | 0.003359 | 0.005289 | 7.162699 | -2.530139 |
| tls,smb2 | modbus | none | gru_shared_route | 170101 | 0.019516 | 0.019516 | 4.171988 | -1.333235 |
| tls,smb2 | dns | none | gru_shared_attr | 170101 | 0.024827 | 0.115417 | 16.476009 | -6.473613 |
| tls,smb2 | modbus | none | gru_shared_attr | 170101 | 0.612063 | 0.612063 | 0.535341 | 2.303412 |
| tls,smb2 | dns | tape | shared_slot_hybrid | 170101 | 0.016753 | 0.084649 | 5.833733 | 0.272483 |
| tls,smb2 | modbus | tape | shared_slot_hybrid | 170101 | 0.734196 | 0.734196 | 0.390280 | 2.448473 |
| tls,smb2 | dns | tape | aux_small | 170101 | 0.039925 | 0.233207 | 8.414644 | -0.494205 |
| tls,smb2 | modbus | tape | aux_small | 170101 | 0.846907 | 0.846907 | 0.501865 | 2.336888 |
| tls,smb2 | dns | tape | aux_large | 170101 | 0.010697 | 0.015594 | 5.467728 | -0.274818 |
| tls,smb2 | modbus | tape | aux_large | 170101 | 0.613953 | 0.613953 | 0.640327 | 2.198426 |
| tls,smb2 | dns | tape | bilinear_program | 170101 | 0.010979 | 0.037877 | 6.292223 | -1.425400 |
| tls,smb2 | modbus | tape | bilinear_program | 170101 | 0.014126 | 0.014126 | 4.665565 | -1.826813 |
| tls,smb2 | dns | tape | shared_slot_route | 170101 | 0.008092 | 0.024439 | 6.185431 | -1.349997 |
| tls,smb2 | modbus | tape | shared_slot_route | 170101 | 0.013334 | 0.013334 | 4.617170 | -1.778417 |
| tls,smb2 | dns | tape | execute_score | 170101 | 0.014770 | 0.046874 | 5.280483 | 0.248327 |
| tls,smb2 | modbus | tape | execute_score | 170101 | 0.084162 | 0.084162 | 2.712795 | 0.125958 |
| tls,smb2 | dns | tape | equivalent_program | 170101 | 0.007762 | 0.025392 | 6.749797 | -1.603102 |
| tls,smb2 | modbus | tape | equivalent_program | 170101 | 0.021747 | 0.021747 | 4.338709 | -1.499956 |

## Refine candidate scores — not final test results

| Outer target excluded | Formula | Balanced p | Balanced log gain | Evidence cells |
| --- | --- | --- | --- | --- |
| DNS | hybrid | 0.353451 | 1.092597 | 6 |
| DNS | aux_small | 0.533599 | 2.320747 | 6 |
| DNS | attr_content | 0.433103 | 1.866710 | 6 |
| DNS | shared_slot_hybrid | 0.347635 | 0.734159 | 6 |
| MODBUS | hybrid | 0.029798 | -0.913094 | 6 |
| MODBUS | attr_content | 0.053448 | -2.131983 | 6 |
| MODBUS | shared_slot_hybrid | 0.052246 | -1.183939 | 6 |
| MODBUS | mix_entropy | 0.054668 | -1.518751 | 6 |
| SMB2 | hybrid | 0.322268 | 1.296423 | 6 |
| SMB2 | attr_content | 0.558284 | 2.397909 | 6 |
| SMB2 | aux_small | 0.329393 | 1.543505 | 6 |
| SMB2 | weak_product | 0.501933 | 1.762300 | 6 |
| TLS | hybrid | 0.042603 | -0.576957 | 6 |
| TLS | gru_shared_attr | 0.212307 | -3.137853 | 6 |
| TLS | shared_slot_hybrid | 0.099307 | 0.300283 | 6 |
| TLS | attr_content | 0.244698 | -0.881362 | 6 |

## Refine complete validation matrix

Both excluded protocols are retained for transparency; only outer-target-free evidence enters each choice.

| Sources | Validation | Backbone | Formula | Seed | p(target) | Balanced p | NLL | Balanced log gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| modbus,tls | dns | tape | hybrid | 170201 | 0.009236 | 0.009553 | 5.941347 | -1.363735 |
| modbus,tls | smb2 | tape | hybrid | 170201 | 0.001102 | 0.001773 | 8.756288 | -2.276676 |
| modbus,tls | dns | tape | hybrid | 170202 | 0.010025 | 0.006692 | 5.502380 | -1.915852 |
| modbus,tls | smb2 | tape | hybrid | 170202 | 0.001130 | 0.002119 | 8.673789 | -2.513822 |
| modbus,tls | dns | tape | aux_small | 170201 | 0.013180 | 0.025181 | 5.092418 | 0.188036 |
| modbus,tls | smb2 | tape | aux_small | 170201 | 0.012057 | 0.020039 | 6.067880 | 0.408349 |
| modbus,tls | dns | tape | aux_small | 170202 | 0.015086 | 0.032247 | 5.405805 | 0.283938 |
| modbus,tls | smb2 | tape | aux_small | 170202 | 0.016159 | 0.022855 | 7.605271 | -0.179972 |
| modbus,tls | dns | tape | attr_content | 170201 | 0.027872 | 0.074386 | 4.600803 | 0.895127 |
| modbus,tls | smb2 | tape | attr_content | 170201 | 0.007650 | 0.014337 | 5.950692 | 0.310685 |
| modbus,tls | dns | tape | attr_content | 170202 | 0.046410 | 0.248182 | 6.343525 | 0.208605 |
| modbus,tls | smb2 | tape | attr_content | 170202 | 0.087270 | 0.103443 | 5.793597 | 0.912264 |
| modbus,tls | dns | tape | shared_slot_hybrid | 170201 | 0.001575 | 0.000778 | 8.849888 | -4.263805 |
| modbus,tls | smb2 | tape | shared_slot_hybrid | 170201 | 0.004360 | 0.014196 | 8.821869 | -1.811488 |
| modbus,tls | dns | tape | shared_slot_hybrid | 170202 | 0.009649 | 0.007693 | 6.304698 | -2.485753 |
| modbus,tls | smb2 | tape | shared_slot_hybrid | 170202 | 0.068369 | 0.113991 | 13.273512 | -3.712651 |
| modbus,smb2 | dns | tape | hybrid | 170201 | 0.007776 | 0.008841 | 5.830641 | -0.675620 |
| modbus,smb2 | tls | tape | hybrid | 170201 | 0.608976 | 0.608976 | 0.849338 | 3.865991 |
| modbus,smb2 | dns | tape | hybrid | 170202 | 0.016509 | 0.014365 | 4.717778 | -0.065654 |
| modbus,smb2 | tls | tape | hybrid | 170202 | 0.410739 | 0.410739 | 1.346895 | 3.368434 |
| modbus,smb2 | dns | tape | aux_small | 170201 | 0.009714 | 0.043561 | 6.414114 | -0.393242 |
| modbus,smb2 | tls | tape | aux_small | 170201 | 0.810683 | 0.810683 | 0.236653 | 4.478676 |
| modbus,smb2 | dns | tape | aux_small | 170202 | 0.025373 | 0.117694 | 5.381600 | 0.686292 |
| modbus,smb2 | tls | tape | aux_small | 170202 | 0.885241 | 0.885241 | 0.127119 | 4.588210 |
| modbus,smb2 | dns | tape | attr_content | 170201 | 0.031615 | 0.190295 | 8.074467 | -0.259079 |
| modbus,smb2 | tls | tape | attr_content | 170201 | 0.885846 | 0.885846 | 0.172342 | 4.542987 |
| modbus,smb2 | dns | tape | attr_content | 170202 | 0.015275 | 0.076539 | 12.293761 | -3.066977 |
| modbus,smb2 | tls | tape | attr_content | 170202 | 0.320903 | 0.320903 | 2.664033 | 2.051296 |
| modbus,smb2 | dns | tape | shared_slot_hybrid | 170201 | 0.022606 | 0.126740 | 6.756313 | 0.243324 |
| modbus,smb2 | tls | tape | shared_slot_hybrid | 170201 | 0.676003 | 0.676003 | 0.892030 | 3.823299 |
| modbus,smb2 | dns | tape | shared_slot_hybrid | 170202 | 0.017377 | 0.074349 | 5.567947 | 0.596624 |
| modbus,smb2 | tls | tape | shared_slot_hybrid | 170202 | 0.471417 | 0.471417 | 1.164834 | 3.550495 |
| tls,smb2 | dns | tape | hybrid | 170201 | 0.019460 | 0.089528 | 5.597646 | 0.475934 |
| tls,smb2 | modbus | tape | hybrid | 170201 | 0.598075 | 0.598075 | 0.819519 | 2.019234 |
| tls,smb2 | dns | tape | hybrid | 170202 | 0.015060 | 0.044244 | 5.022586 | 0.403880 |
| tls,smb2 | modbus | tape | hybrid | 170202 | 0.499022 | 0.499022 | 0.746331 | 2.092422 |
| tls,smb2 | dns | tape | aux_small | 170201 | 0.015877 | 0.095022 | 8.704617 | -1.679058 |
| tls,smb2 | modbus | tape | aux_small | 170201 | 0.649091 | 0.649091 | 0.701292 | 2.137461 |
| tls,smb2 | dns | tape | aux_small | 170202 | 0.012645 | 0.053552 | 5.951963 | 0.074864 |
| tls,smb2 | modbus | tape | aux_small | 170202 | 0.813687 | 0.813687 | 0.346995 | 2.491758 |
| tls,smb2 | dns | tape | attr_content | 170201 | 0.035936 | 0.210465 | 8.282553 | -0.132749 |
| tls,smb2 | modbus | tape | attr_content | 170201 | 0.913503 | 0.913503 | 0.518714 | 2.320039 |
| tls,smb2 | dns | tape | attr_content | 170202 | 0.005077 | 0.022409 | 10.982494 | -3.071195 |
| tls,smb2 | modbus | tape | attr_content | 170202 | 0.360588 | 0.360588 | 1.775763 | 1.062990 |
| tls,smb2 | dns | tape | shared_slot_hybrid | 170201 | 0.024288 | 0.146215 | 8.361923 | -0.964471 |
| tls,smb2 | modbus | tape | shared_slot_hybrid | 170201 | 0.646592 | 0.646592 | 0.687341 | 2.151412 |
| tls,smb2 | dns | tape | shared_slot_hybrid | 170202 | 0.016224 | 0.045597 | 4.697945 | 0.589454 |
| tls,smb2 | modbus | tape | shared_slot_hybrid | 170202 | 0.163613 | 0.163613 | 2.434868 | 0.403885 |
| dns,tls | modbus | tape | hybrid | 170201 | 0.775495 | 0.775495 | 0.282895 | 2.555858 |
| dns,tls | smb2 | tape | hybrid | 170201 | 0.021767 | 0.028055 | 5.931842 | -0.568987 |
| dns,tls | modbus | tape | hybrid | 170202 | 0.444712 | 0.444712 | 0.900281 | 1.938472 |
| dns,tls | smb2 | tape | hybrid | 170202 | 0.011434 | 0.011145 | 5.120216 | 0.226535 |
| dns,tls | modbus | tape | attr_content | 170201 | 0.958805 | 0.958805 | 0.050074 | 2.788679 |
| dns,tls | smb2 | tape | attr_content | 170201 | 0.014917 | 0.021460 | 8.411486 | -5.304064 |
| dns,tls | modbus | tape | attr_content | 170202 | 0.888881 | 0.888881 | 0.142200 | 2.696553 |
| dns,tls | smb2 | tape | attr_content | 170202 | 0.014878 | 0.019462 | 6.815252 | -2.386691 |
| dns,tls | modbus | tape | shared_slot_hybrid | 170201 | 0.537098 | 0.537098 | 1.050909 | 1.787844 |
| dns,tls | smb2 | tape | shared_slot_hybrid | 170201 | 0.019057 | 0.028234 | 7.193325 | -1.826907 |
| dns,tls | modbus | tape | shared_slot_hybrid | 170202 | 0.520913 | 0.520913 | 0.695046 | 2.143706 |
| dns,tls | smb2 | tape | shared_slot_hybrid | 170202 | 0.065577 | 0.086744 | 5.534842 | 0.238506 |
| dns,tls | modbus | tape | mix_entropy | 170201 | 0.524351 | 0.524351 | 0.710172 | 2.128580 |
| dns,tls | smb2 | tape | mix_entropy | 170201 | 0.013693 | 0.020801 | 8.489411 | -2.564239 |
| dns,tls | modbus | tape | mix_entropy | 170202 | 0.255667 | 0.255667 | 1.426174 | 1.412579 |
| dns,tls | smb2 | tape | mix_entropy | 170202 | 0.089972 | 0.094433 | 6.182463 | -0.297398 |
| dns,smb2 | modbus | tape | hybrid | 170201 | 0.170552 | 0.170552 | 2.364219 | 0.474534 |
| dns,smb2 | tls | tape | hybrid | 170201 | 0.004687 | 0.004687 | 6.676445 | -1.961115 |
| dns,smb2 | modbus | tape | hybrid | 170202 | 0.035436 | 0.035436 | 4.572126 | -1.733373 |
| dns,smb2 | tls | tape | hybrid | 170202 | 0.001128 | 0.001128 | 8.770140 | -4.054811 |
| dns,smb2 | modbus | tape | attr_content | 170201 | 0.547442 | 0.547442 | 1.413334 | 1.425419 |
| dns,smb2 | tls | tape | attr_content | 170201 | 0.008637 | 0.008637 | 5.994295 | -1.278965 |
| dns,smb2 | modbus | tape | attr_content | 170202 | 0.470174 | 0.470174 | 1.514151 | 1.324602 |
| dns,smb2 | tls | tape | attr_content | 170202 | 0.038252 | 0.038252 | 5.333561 | -0.618231 |
| dns,smb2 | modbus | tape | shared_slot_hybrid | 170201 | 0.165835 | 0.165835 | 2.102143 | 0.736610 |
| dns,smb2 | tls | tape | shared_slot_hybrid | 170201 | 0.002110 | 0.002110 | 7.905545 | -3.190216 |
| dns,smb2 | modbus | tape | shared_slot_hybrid | 170202 | 0.122400 | 0.122400 | 2.651732 | 0.187021 |
| dns,smb2 | tls | tape | shared_slot_hybrid | 170202 | 0.004574 | 0.004574 | 6.665327 | -1.949998 |
| dns,smb2 | modbus | tape | mix_entropy | 170201 | 0.315428 | 0.315428 | 1.894435 | 0.944317 |
| dns,smb2 | tls | tape | mix_entropy | 170201 | 0.003759 | 0.003759 | 7.192478 | -2.477148 |
| dns,smb2 | modbus | tape | mix_entropy | 170202 | 0.053157 | 0.053157 | 3.566312 | -0.727559 |
| dns,smb2 | tls | tape | mix_entropy | 170202 | 0.003609 | 0.003609 | 6.930146 | -2.214817 |
| tls,smb2 | dns | tape | mix_entropy | 170201 | 0.004171 | 0.013408 | 6.556898 | -0.670660 |
| tls,smb2 | modbus | tape | mix_entropy | 170201 | 0.306413 | 0.306413 | 2.248221 | 0.590532 |
| tls,smb2 | dns | tape | mix_entropy | 170202 | 0.031844 | 0.192001 | 8.382531 | -0.888243 |
| tls,smb2 | modbus | tape | mix_entropy | 170202 | 0.909034 | 0.909034 | 0.156540 | 2.682213 |
| dns,modbus | tls | tape | hybrid | 170201 | 0.189227 | 0.189227 | 1.880246 | 2.835084 |
| dns,modbus | smb2 | tape | hybrid | 170201 | 0.005306 | 0.007477 | 7.156556 | -1.394177 |
| dns,modbus | tls | tape | hybrid | 170202 | 0.507927 | 0.507927 | 0.986616 | 3.728713 |
| dns,modbus | smb2 | tape | hybrid | 170202 | 0.013546 | 0.018944 | 5.851350 | -0.067455 |
| dns,modbus | tls | tape | attr_content | 170201 | 0.619318 | 0.619318 | 0.930675 | 3.784654 |
| dns,modbus | smb2 | tape | attr_content | 170201 | 0.063253 | 0.095406 | 8.481413 | -4.655981 |
| dns,modbus | tls | tape | attr_content | 170202 | 0.560131 | 0.560131 | 0.701493 | 4.013836 |
| dns,modbus | smb2 | tape | attr_content | 170202 | 0.064699 | 0.088330 | 5.502600 | -0.056157 |
| dns,modbus | tls | tape | aux_small | 170201 | 0.562865 | 0.562865 | 0.867560 | 3.847770 |
| dns,modbus | smb2 | tape | aux_small | 170201 | 0.003083 | 0.002591 | 8.874246 | -3.665703 |
| dns,modbus | tls | tape | aux_small | 170202 | 0.546687 | 0.546687 | 0.833362 | 3.881967 |
| dns,modbus | smb2 | tape | aux_small | 170202 | 0.010043 | 0.013769 | 5.762165 | -0.168868 |
| dns,modbus | tls | tape | weak_product | 170201 | 0.848268 | 0.848268 | 0.218155 | 4.497175 |
| dns,modbus | smb2 | tape | weak_product | 170201 | 0.002628 | 0.004826 | 7.679307 | -1.194580 |
| dns,modbus | tls | tape | weak_product | 170202 | 0.839642 | 0.839642 | 0.212023 | 4.503307 |
| dns,modbus | smb2 | tape | weak_product | 170202 | 0.023885 | 0.034980 | 7.513159 | -1.280019 |
| dns,tls | modbus | tape | aux_small | 170201 | 0.079749 | 0.079749 | 4.222491 | -1.383738 |
| dns,tls | smb2 | tape | aux_small | 170201 | 0.000294 | 0.000451 | 10.682225 | -4.906990 |
| dns,tls | modbus | tape | aux_small | 170202 | 0.729632 | 0.729632 | 0.395699 | 2.443054 |
| dns,tls | smb2 | tape | aux_small | 170202 | 0.002074 | 0.002014 | 7.031422 | -1.472261 |
| dns,tls | modbus | tape | weak_product | 170201 | 0.878681 | 0.878681 | 0.155031 | 2.683722 |
| dns,tls | smb2 | tape | weak_product | 170201 | 0.017724 | 0.024571 | 6.437187 | -0.926574 |
| dns,tls | modbus | tape | weak_product | 170202 | 0.428728 | 0.428728 | 1.042552 | 1.796200 |
| dns,tls | smb2 | tape | weak_product | 170202 | 0.003743 | 0.003253 | 6.468116 | -1.501969 |
| modbus,tls | dns | tape | weak_product | 170201 | 0.009927 | 0.009879 | 7.071075 | -1.354007 |
| modbus,tls | smb2 | tape | weak_product | 170201 | 0.018792 | 0.028674 | 12.355307 | -3.770002 |
| modbus,tls | dns | tape | weak_product | 170202 | 0.011157 | 0.006402 | 7.041174 | -1.552596 |
| modbus,tls | smb2 | tape | weak_product | 170202 | 0.003499 | 0.005428 | 12.775829 | -3.903871 |
| dns,modbus | tls | none | gru_shared_attr | 170201 | 0.470551 | 0.470551 | 1.998612 | 2.716718 |
| dns,modbus | smb2 | none | gru_shared_attr | 170201 | 0.016667 | 0.017882 | 6.354952 | -1.911567 |
| dns,modbus | tls | none | gru_shared_attr | 170202 | 0.528274 | 0.528274 | 1.396719 | 3.318610 |
| dns,modbus | smb2 | none | gru_shared_attr | 170202 | 0.028036 | 0.031944 | 8.163075 | -2.022336 |
| dns,modbus | tls | tape | shared_slot_hybrid | 170201 | 0.258952 | 0.258952 | 1.788577 | 2.926752 |
| dns,modbus | smb2 | tape | shared_slot_hybrid | 170201 | 0.039529 | 0.066849 | 6.066314 | 0.487532 |
| dns,modbus | tls | tape | shared_slot_hybrid | 170202 | 0.646524 | 0.646524 | 0.666594 | 4.048736 |
| dns,modbus | smb2 | tape | shared_slot_hybrid | 170202 | 0.031273 | 0.039667 | 6.040610 | -0.449412 |
| dns,smb2 | modbus | none | gru_shared_attr | 170201 | 0.606942 | 0.606942 | 0.666792 | 2.171961 |
| dns,smb2 | tls | none | gru_shared_attr | 170201 | 0.014069 | 0.014069 | 5.231103 | -0.515773 |
| dns,smb2 | modbus | none | gru_shared_attr | 170202 | 0.609213 | 0.609213 | 0.623067 | 2.215686 |
| dns,smb2 | tls | none | gru_shared_attr | 170202 | 0.095458 | 0.095458 | 2.981948 | 1.733381 |
| modbus,smb2 | dns | none | gru_shared_attr | 170201 | 0.000794 | 0.004832 | 21.687124 | -11.945293 |
| modbus,smb2 | tls | none | gru_shared_attr | 170201 | 0.222382 | 0.222382 | 3.216990 | 1.498340 |
| modbus,smb2 | dns | none | gru_shared_attr | 170202 | 0.000489 | 0.003028 | 14.695342 | -7.335568 |
| modbus,smb2 | tls | none | gru_shared_attr | 170202 | 0.501461 | 0.501461 | 0.997154 | 3.718175 |

## Final endpoint metrics by protocol

| Target | Panel backbone | Cohort | N | Role | Formula | Actual backbone | p(target) [95% CI] | Hit@1 [95% CI] | NLL [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DNS | rope | ALL | 266 | off | off | rope | 0.0485 [0.0482, 0.0487] | 0.0489 [0.0489, 0.0489] | 13.1937 [9.2652, 17.1223] |
| DNS | rope | ALL | 266 | hybrid | hybrid | rope | 0.0155 [0.0116, 0.0194] | 0.0213 [-0.0387, 0.0813] | 5.8903 [4.7244, 7.0562] |
| DNS | rope | ALL | 266 | p_champion | aux_small | rope | 0.0194 [0.0123, 0.0266] | 0.0464 [0.0410, 0.0518] | 5.8887 [4.0250, 7.7525] |
| DNS | rope | ALL | 266 | nll_champion | aux_small | rope | 0.0194 [0.0123, 0.0266] | 0.0464 [0.0410, 0.0518] | 5.8887 [4.0250, 7.7525] |
| DNS | cope | ALL | 266 | off | off | cope | 0.0335 [0.0084, 0.0587] | 0.0401 [0.0166, 0.0636] | 9.6585 [7.5914, 11.7257] |
| DNS | cope | ALL | 266 | hybrid | hybrid | cope | 0.0126 [0.0081, 0.0172] | 0.0338 [-0.0156, 0.0833] | 6.0505 [4.8191, 7.2818] |
| DNS | cope | ALL | 266 | p_champion | aux_small | cope | 0.0183 [-0.0021, 0.0387] | 0.0338 [-0.0230, 0.0906] | 6.2337 [4.8884, 7.5789] |
| DNS | cope | ALL | 266 | nll_champion | aux_small | cope | 0.0183 [-0.0021, 0.0387] | 0.0338 [-0.0230, 0.0906] | 6.2337 [4.8884, 7.5789] |
| DNS | tape | ALL | 266 | off | off | tape | 0.0343 [0.0003, 0.0684] | 0.0363 [-0.0025, 0.0752] | 22.0606 [6.7557, 37.3656] |
| DNS | tape | ALL | 266 | hybrid | hybrid | tape | 0.0158 [0.0114, 0.0203] | 0.0276 [-0.0239, 0.0790] | 5.8928 [4.3995, 7.3862] |
| DNS | tape | ALL | 266 | p_champion | aux_small | tape | 0.0164 [0.0137, 0.0192] | 0.0388 [0.0088, 0.0689] | 6.5164 [1.5914, 11.4414] |
| DNS | tape | ALL | 266 | nll_champion | aux_small | tape | 0.0164 [0.0137, 0.0192] | 0.0388 [0.0088, 0.0689] | 6.5164 [1.5914, 11.4414] |
| DNS | sdpa | ALL | 266 | off | off | sdpa | 0.0455 [0.0380, 0.0529] | 0.0489 [0.0489, 0.0489] | 10.1279 [5.9914, 14.2645] |
| DNS | sdpa | ALL | 266 | hybrid | hybrid | sdpa | 0.0099 [0.0081, 0.0118] | 0.0088 [-0.0147, 0.0323] | 5.6505 [4.7858, 6.5152] |
| DNS | sdpa | ALL | 266 | p_champion | aux_small | sdpa | 0.0194 [0.0116, 0.0272] | 0.0451 [0.0358, 0.0545] | 6.2851 [5.9205, 6.6497] |
| DNS | sdpa | ALL | 266 | nll_champion | aux_small | sdpa | 0.0194 [0.0116, 0.0272] | 0.0451 [0.0358, 0.0545] | 6.2851 [5.9205, 6.6497] |
| MODBUS | rope | ALL | 6 | off | off | rope | 0.5288 [-0.2363, 1.2939] | 0.6667 [-0.4287, 1.7621] | 1.0431 [-1.7244, 3.8106] |
| MODBUS | rope | ALL | 6 | hybrid | hybrid | rope | 0.8162 [0.5873, 1.0452] | 1.0000 [1.0000, 1.0000] | 0.2463 [-0.0744, 0.5670] |
| MODBUS | rope | ALL | 6 | p_champion | mix_entropy | rope | 0.8081 [0.5912, 1.0250] | 1.0000 [1.0000, 1.0000] | 0.2224 [-0.0483, 0.4931] |
| MODBUS | rope | ALL | 6 | nll_champion | hybrid | rope | 0.8162 [0.5873, 1.0452] | 1.0000 [1.0000, 1.0000] | 0.2463 [-0.0744, 0.5670] |
| MODBUS | cope | ALL | 6 | off | off | cope | 0.3064 [0.0578, 0.5550] | 0.3333 [-0.0807, 0.7474] | 1.7655 [1.1044, 2.4266] |
| MODBUS | cope | ALL | 6 | hybrid | hybrid | cope | 0.8090 [0.5005, 1.1175] | 1.0000 [1.0000, 1.0000] | 0.2633 [-0.1947, 0.7212] |
| MODBUS | cope | ALL | 6 | p_champion | mix_entropy | cope | 0.7300 [0.2760, 1.1840] | 0.8333 [0.4193, 1.2474] | 0.3963 [-0.3412, 1.1338] |
| MODBUS | cope | ALL | 6 | nll_champion | hybrid | cope | 0.8090 [0.5005, 1.1175] | 1.0000 [1.0000, 1.0000] | 0.2633 [-0.1947, 0.7212] |
| MODBUS | tape | ALL | 6 | off | off | tape | 0.5225 [-0.1124, 1.1574] | 0.5000 [0.0860, 0.9140] | 1.1847 [-0.6805, 3.0499] |
| MODBUS | tape | ALL | 6 | hybrid | hybrid | tape | 0.8163 [0.3072, 1.3253] | 0.8889 [0.4108, 1.3670] | 0.2907 [-0.6502, 1.2316] |
| MODBUS | tape | ALL | 6 | p_champion | mix_entropy | tape | 0.7257 [0.4521, 0.9993] | 0.8889 [0.4108, 1.3670] | 0.3994 [-0.1852, 0.9839] |
| MODBUS | tape | ALL | 6 | nll_champion | hybrid | tape | 0.8163 [0.3072, 1.3253] | 0.8889 [0.4108, 1.3670] | 0.2907 [-0.6502, 1.2316] |
| MODBUS | sdpa | ALL | 6 | off | off | sdpa | 0.4398 [-0.0753, 0.9549] | 0.6111 [-0.2507, 1.4730] | 1.3229 [-0.7364, 3.3821] |
| MODBUS | sdpa | ALL | 6 | hybrid | hybrid | sdpa | 0.6448 [0.1473, 1.1422] | 0.7222 [0.0898, 1.3547] | 0.5992 [-0.5245, 1.7229] |
| MODBUS | sdpa | ALL | 6 | p_champion | mix_entropy | sdpa | 0.8246 [0.4571, 1.1921] | 0.8889 [0.4108, 1.3670] | 0.2196 [-0.3116, 0.7508] |
| MODBUS | sdpa | ALL | 6 | nll_champion | hybrid | sdpa | 0.6448 [0.1473, 1.1422] | 0.7222 [0.0898, 1.3547] | 0.5992 [-0.5245, 1.7229] |
| TLS | rope | ALL | 15 | off | off | rope | 0.9767 [0.9224, 1.0309] | 1.0000 [1.0000, 1.0000] | 0.0333 [-0.0546, 0.1211] |
| TLS | rope | ALL | 15 | hybrid | hybrid | rope | 0.8181 [0.8010, 0.8352] | 0.9556 [0.8599, 1.0512] | 0.2851 [0.1567, 0.4135] |
| TLS | rope | ALL | 15 | p_champion | attr_content | rope | 0.8650 [0.7619, 0.9682] | 0.8889 [0.7933, 0.9845] | 0.4126 [-0.3035, 1.1286] |
| TLS | rope | ALL | 15 | nll_champion | shared_slot_hybrid | rope | 0.8226 [0.2709, 1.3744] | 0.8889 [0.5441, 1.2336] | 0.3897 [-0.5996, 1.3791] |
| TLS | cope | ALL | 15 | off | off | cope | 0.9955 [0.9917, 0.9993] | 1.0000 [1.0000, 1.0000] | 0.0045 [0.0007, 0.0084] |
| TLS | cope | ALL | 15 | hybrid | hybrid | cope | 0.9992 [0.9977, 1.0006] | 1.0000 [1.0000, 1.0000] | 0.0008 [-0.0006, 0.0023] |
| TLS | cope | ALL | 15 | p_champion | attr_content | cope | 0.9957 [0.9838, 1.0076] | 1.0000 [1.0000, 1.0000] | 0.0046 [-0.0084, 0.0175] |
| TLS | cope | ALL | 15 | nll_champion | shared_slot_hybrid | cope | 0.9770 [0.9008, 1.0531] | 1.0000 [1.0000, 1.0000] | 0.0293 [-0.0724, 0.1310] |
| TLS | tape | ALL | 15 | off | off | tape | 0.9846 [0.9695, 0.9996] | 1.0000 [1.0000, 1.0000] | 0.0170 [-0.0005, 0.0344] |
| TLS | tape | ALL | 15 | hybrid | hybrid | tape | 0.8506 [0.5340, 1.1673] | 0.9556 [0.8599, 1.0512] | 0.2534 [-0.3141, 0.8208] |
| TLS | tape | ALL | 15 | p_champion | attr_content | tape | 0.8810 [0.5670, 1.1951] | 0.9111 [0.6581, 1.1641] | 0.3594 [-0.8298, 1.5487] |
| TLS | tape | ALL | 15 | nll_champion | shared_slot_hybrid | tape | 0.7431 [0.3810, 1.1053] | 0.9778 [0.8822, 1.0734] | 0.3472 [-0.2086, 0.9030] |
| TLS | sdpa | ALL | 15 | off | off | sdpa | 0.9989 [0.9982, 0.9997] | 1.0000 [1.0000, 1.0000] | 0.0011 [0.0003, 0.0018] |
| TLS | sdpa | ALL | 15 | hybrid | hybrid | sdpa | 0.9997 [0.9995, 1.0000] | 1.0000 [1.0000, 1.0000] | 0.0003 [0.0000, 0.0005] |
| TLS | sdpa | ALL | 15 | p_champion | attr_content | sdpa | 0.9953 [0.9789, 1.0117] | 1.0000 [1.0000, 1.0000] | 0.0051 [-0.0131, 0.0233] |
| TLS | sdpa | ALL | 15 | nll_champion | shared_slot_hybrid | sdpa | 0.9989 [0.9977, 1.0002] | 1.0000 [1.0000, 1.0000] | 0.0011 [-0.0002, 0.0023] |
| SMB2 | rope | ALL | 60 | off | off | rope | 0.0266 [-0.0285, 0.0817] | 0.0722 [-0.0140, 0.1584] | 7.8587 [5.3897, 10.3278] |
| SMB2 | rope | ALL | 60 | hybrid | hybrid | rope | 0.0335 [-0.0437, 0.1107] | 0.1611 [-0.1861, 0.5083] | 5.8313 [3.3289, 8.3337] |
| SMB2 | rope | ALL | 60 | p_champion | attr_content | rope | 0.0481 [-0.0785, 0.1747] | 0.1111 [-0.1884, 0.4106] | 8.9778 [5.8025, 12.1531] |
| SMB2 | rope | ALL | 60 | nll_champion | attr_content | rope | 0.0481 [-0.0785, 0.1747] | 0.1111 [-0.1884, 0.4106] | 8.9778 [5.8025, 12.1531] |
| SMB2 | cope | ALL | 60 | off | off | cope | 0.0524 [-0.0804, 0.1852] | 0.1222 [-0.1596, 0.4040] | 6.2865 [4.5217, 8.0514] |
| SMB2 | cope | ALL | 60 | hybrid | hybrid | cope | 0.0043 [-0.0082, 0.0167] | 0.0056 [-0.0183, 0.0295] | 7.7889 [3.1821, 12.3957] |
| SMB2 | cope | ALL | 60 | p_champion | attr_content | cope | 0.0506 [0.0275, 0.0737] | 0.1333 [-0.0857, 0.3524] | 10.0600 [6.3776, 13.7423] |
| SMB2 | cope | ALL | 60 | nll_champion | attr_content | cope | 0.0506 [0.0275, 0.0737] | 0.1333 [-0.0857, 0.3524] | 10.0600 [6.3776, 13.7423] |
| SMB2 | tape | ALL | 60 | off | off | tape | 0.0297 [-0.0025, 0.0619] | 0.0944 [-0.1685, 0.3574] | 7.5255 [6.1224, 8.9286] |
| SMB2 | tape | ALL | 60 | hybrid | hybrid | tape | 0.0613 [-0.1626, 0.2851] | 0.0778 [-0.2217, 0.3773] | 5.7042 [4.4713, 6.9372] |
| SMB2 | tape | ALL | 60 | p_champion | attr_content | tape | 0.0749 [-0.0590, 0.2089] | 0.1722 [-0.1273, 0.4717] | 9.0201 [6.8161, 11.2241] |
| SMB2 | tape | ALL | 60 | nll_champion | attr_content | tape | 0.0749 [-0.0590, 0.2089] | 0.1722 [-0.1273, 0.4717] | 9.0201 [6.8161, 11.2241] |
| SMB2 | sdpa | ALL | 60 | off | off | sdpa | 0.0403 [-0.0661, 0.1467] | 0.1278 [-0.1830, 0.4385] | 7.2114 [4.2680, 10.1549] |
| SMB2 | sdpa | ALL | 60 | hybrid | hybrid | sdpa | 0.0037 [-0.0021, 0.0095] | 0.0000 [0.0000, 0.0000] | 7.7875 [5.4718, 10.1032] |
| SMB2 | sdpa | ALL | 60 | p_champion | attr_content | sdpa | 0.0724 [-0.0484, 0.1932] | 0.1278 [-0.1384, 0.3940] | 10.5232 [5.2147, 15.8317] |
| SMB2 | sdpa | ALL | 60 | nll_champion | attr_content | sdpa | 0.0724 [-0.0484, 0.1932] | 0.1278 [-0.1384, 0.3940] | 10.5232 [5.2147, 15.8317] |

## Final endpoint metrics by semantic

| Target | Panel backbone | Cohort | N | Role | Formula | Actual backbone | p(target) [95% CI] | Hit@1 [95% CI] | NLL [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DNS | rope | LENGTH | 230 | off | off | rope | 0.0560 [0.0557, 0.0563] | 0.0565 [0.0565, 0.0565] | 13.2046 [9.5710, 16.8383] |
| DNS | rope | POINTER | 36 | off | off | rope | 0.0000 [-0.0000, 0.0001] | 0.0000 [0.0000, 0.0000] | 13.1241 [6.5058, 19.7423] |
| DNS | rope | LENGTH | 230 | hybrid | hybrid | rope | 0.0169 [0.0121, 0.0217] | 0.0246 [-0.0448, 0.0941] | 5.9177 [4.9444, 6.8910] |
| DNS | rope | POINTER | 36 | hybrid | hybrid | rope | 0.0068 [-0.0053, 0.0188] | 0.0000 [0.0000, 0.0000] | 5.7156 [3.3189, 8.1122] |
| DNS | rope | LENGTH | 230 | p_champion | aux_small | rope | 0.0217 [0.0129, 0.0305] | 0.0536 [0.0474, 0.0599] | 5.8896 [4.1341, 7.6450] |
| DNS | rope | POINTER | 36 | p_champion | aux_small | rope | 0.0050 [-0.0034, 0.0134] | 0.0000 [0.0000, 0.0000] | 5.8833 [3.1152, 8.6515] |
| DNS | rope | LENGTH | 230 | nll_champion | aux_small | rope | 0.0217 [0.0129, 0.0305] | 0.0536 [0.0474, 0.0599] | 5.8896 [4.1341, 7.6450] |
| DNS | rope | POINTER | 36 | nll_champion | aux_small | rope | 0.0050 [-0.0034, 0.0134] | 0.0000 [0.0000, 0.0000] | 5.8833 [3.1152, 8.6515] |
| DNS | cope | LENGTH | 230 | off | off | cope | 0.0386 [0.0095, 0.0677] | 0.0464 [0.0192, 0.0736] | 9.7382 [7.7479, 11.7284] |
| DNS | cope | POINTER | 36 | off | off | cope | 0.0013 [-0.0013, 0.0039] | 0.0000 [0.0000, 0.0000] | 9.1499 [5.4344, 12.8653] |
| DNS | cope | LENGTH | 230 | hybrid | hybrid | cope | 0.0134 [0.0066, 0.0202] | 0.0377 [-0.0256, 0.1010] | 6.1197 [4.9254, 7.3139] |
| DNS | cope | POINTER | 36 | hybrid | hybrid | cope | 0.0075 [-0.0024, 0.0174] | 0.0093 [-0.0306, 0.0491] | 5.6082 [4.1399, 7.0766] |
| DNS | cope | LENGTH | 230 | p_champion | aux_small | cope | 0.0199 [-0.0040, 0.0438] | 0.0377 [-0.0342, 0.1096] | 6.3509 [4.7952, 7.9066] |
| DNS | cope | POINTER | 36 | p_champion | aux_small | cope | 0.0080 [0.0051, 0.0109] | 0.0093 [-0.0306, 0.0491] | 5.4848 [5.4044, 5.5653] |
| DNS | cope | LENGTH | 230 | nll_champion | aux_small | cope | 0.0199 [-0.0040, 0.0438] | 0.0377 [-0.0342, 0.1096] | 6.3509 [4.7952, 7.9066] |
| DNS | cope | POINTER | 36 | nll_champion | aux_small | cope | 0.0080 [0.0051, 0.0109] | 0.0093 [-0.0306, 0.0491] | 5.4848 [5.4044, 5.5653] |
| DNS | tape | LENGTH | 230 | off | off | tape | 0.0397 [0.0003, 0.0791] | 0.0420 [-0.0029, 0.0870] | 22.5086 [7.5019, 37.5153] |
| DNS | tape | POINTER | 36 | off | off | tape | 0.0001 [-0.0003, 0.0006] | 0.0000 [0.0000, 0.0000] | 19.1988 [1.9714, 36.4262] |
| DNS | tape | LENGTH | 230 | hybrid | hybrid | tape | 0.0175 [0.0114, 0.0237] | 0.0319 [-0.0276, 0.0914] | 5.8926 [4.4873, 7.2978] |
| DNS | tape | POINTER | 36 | hybrid | hybrid | tape | 0.0051 [-0.0023, 0.0125] | 0.0000 [0.0000, 0.0000] | 5.8945 [3.6451, 8.1439] |
| DNS | tape | LENGTH | 230 | p_champion | aux_small | tape | 0.0179 [0.0163, 0.0195] | 0.0449 [0.0102, 0.0796] | 6.5797 [1.6508, 11.5087] |
| DNS | tape | POINTER | 36 | p_champion | aux_small | tape | 0.0070 [-0.0061, 0.0201] | 0.0000 [0.0000, 0.0000] | 6.1117 [1.2089, 11.0146] |
| DNS | tape | LENGTH | 230 | nll_champion | aux_small | tape | 0.0179 [0.0163, 0.0195] | 0.0449 [0.0102, 0.0796] | 6.5797 [1.6508, 11.5087] |
| DNS | tape | POINTER | 36 | nll_champion | aux_small | tape | 0.0070 [-0.0061, 0.0201] | 0.0000 [0.0000, 0.0000] | 6.1117 [1.2089, 11.0146] |
| DNS | sdpa | LENGTH | 230 | off | off | sdpa | 0.0524 [0.0435, 0.0613] | 0.0565 [0.0565, 0.0565] | 10.0661 [6.2650, 13.8672] |
| DNS | sdpa | POINTER | 36 | off | off | sdpa | 0.0010 [-0.0013, 0.0033] | 0.0000 [0.0000, 0.0000] | 10.5229 [4.0182, 17.0277] |
| DNS | sdpa | LENGTH | 230 | hybrid | hybrid | sdpa | 0.0104 [0.0084, 0.0123] | 0.0101 [-0.0170, 0.0373] | 5.6906 [4.6483, 6.7330] |
| DNS | sdpa | POINTER | 36 | hybrid | hybrid | sdpa | 0.0072 [0.0054, 0.0089] | 0.0000 [0.0000, 0.0000] | 5.3944 [5.0544, 5.7344] |
| DNS | sdpa | LENGTH | 230 | p_champion | aux_small | sdpa | 0.0216 [0.0130, 0.0302] | 0.0522 [0.0414, 0.0630] | 6.3268 [6.2064, 6.4473] |
| DNS | sdpa | POINTER | 36 | p_champion | aux_small | sdpa | 0.0055 [-0.0007, 0.0117] | 0.0000 [0.0000, 0.0000] | 6.0187 [3.7282, 8.3091] |
| DNS | sdpa | LENGTH | 230 | nll_champion | aux_small | sdpa | 0.0216 [0.0130, 0.0302] | 0.0522 [0.0414, 0.0630] | 6.3268 [6.2064, 6.4473] |
| DNS | sdpa | POINTER | 36 | nll_champion | aux_small | sdpa | 0.0055 [-0.0007, 0.0117] | 0.0000 [0.0000, 0.0000] | 6.0187 [3.7282, 8.3091] |
| MODBUS | rope | LENGTH | 6 | off | off | rope | 0.5288 [-0.2363, 1.2939] | 0.6667 [-0.4287, 1.7621] | 1.0431 [-1.7244, 3.8106] |
| MODBUS | rope | LENGTH | 6 | hybrid | hybrid | rope | 0.8162 [0.5873, 1.0452] | 1.0000 [1.0000, 1.0000] | 0.2463 [-0.0744, 0.5670] |
| MODBUS | rope | LENGTH | 6 | p_champion | mix_entropy | rope | 0.8081 [0.5912, 1.0250] | 1.0000 [1.0000, 1.0000] | 0.2224 [-0.0483, 0.4931] |
| MODBUS | rope | LENGTH | 6 | nll_champion | hybrid | rope | 0.8162 [0.5873, 1.0452] | 1.0000 [1.0000, 1.0000] | 0.2463 [-0.0744, 0.5670] |
| MODBUS | cope | LENGTH | 6 | off | off | cope | 0.3064 [0.0578, 0.5550] | 0.3333 [-0.0807, 0.7474] | 1.7655 [1.1044, 2.4266] |
| MODBUS | cope | LENGTH | 6 | hybrid | hybrid | cope | 0.8090 [0.5005, 1.1175] | 1.0000 [1.0000, 1.0000] | 0.2633 [-0.1947, 0.7212] |
| MODBUS | cope | LENGTH | 6 | p_champion | mix_entropy | cope | 0.7300 [0.2760, 1.1840] | 0.8333 [0.4193, 1.2474] | 0.3963 [-0.3412, 1.1338] |
| MODBUS | cope | LENGTH | 6 | nll_champion | hybrid | cope | 0.8090 [0.5005, 1.1175] | 1.0000 [1.0000, 1.0000] | 0.2633 [-0.1947, 0.7212] |
| MODBUS | tape | LENGTH | 6 | off | off | tape | 0.5225 [-0.1124, 1.1574] | 0.5000 [0.0860, 0.9140] | 1.1847 [-0.6805, 3.0499] |
| MODBUS | tape | LENGTH | 6 | hybrid | hybrid | tape | 0.8163 [0.3072, 1.3253] | 0.8889 [0.4108, 1.3670] | 0.2907 [-0.6502, 1.2316] |
| MODBUS | tape | LENGTH | 6 | p_champion | mix_entropy | tape | 0.7257 [0.4521, 0.9993] | 0.8889 [0.4108, 1.3670] | 0.3994 [-0.1852, 0.9839] |
| MODBUS | tape | LENGTH | 6 | nll_champion | hybrid | tape | 0.8163 [0.3072, 1.3253] | 0.8889 [0.4108, 1.3670] | 0.2907 [-0.6502, 1.2316] |
| MODBUS | sdpa | LENGTH | 6 | off | off | sdpa | 0.4398 [-0.0753, 0.9549] | 0.6111 [-0.2507, 1.4730] | 1.3229 [-0.7364, 3.3821] |
| MODBUS | sdpa | LENGTH | 6 | hybrid | hybrid | sdpa | 0.6448 [0.1473, 1.1422] | 0.7222 [0.0898, 1.3547] | 0.5992 [-0.5245, 1.7229] |
| MODBUS | sdpa | LENGTH | 6 | p_champion | mix_entropy | sdpa | 0.8246 [0.4571, 1.1921] | 0.8889 [0.4108, 1.3670] | 0.2196 [-0.3116, 0.7508] |
| MODBUS | sdpa | LENGTH | 6 | nll_champion | hybrid | sdpa | 0.6448 [0.1473, 1.1422] | 0.7222 [0.0898, 1.3547] | 0.5992 [-0.5245, 1.7229] |
| TLS | rope | LENGTH | 15 | off | off | rope | 0.9767 [0.9224, 1.0309] | 1.0000 [1.0000, 1.0000] | 0.0333 [-0.0546, 0.1211] |
| TLS | rope | LENGTH | 15 | hybrid | hybrid | rope | 0.8181 [0.8010, 0.8352] | 0.9556 [0.8599, 1.0512] | 0.2851 [0.1567, 0.4135] |
| TLS | rope | LENGTH | 15 | p_champion | attr_content | rope | 0.8650 [0.7619, 0.9682] | 0.8889 [0.7933, 0.9845] | 0.4126 [-0.3035, 1.1286] |
| TLS | rope | LENGTH | 15 | nll_champion | shared_slot_hybrid | rope | 0.8226 [0.2709, 1.3744] | 0.8889 [0.5441, 1.2336] | 0.3897 [-0.5996, 1.3791] |
| TLS | cope | LENGTH | 15 | off | off | cope | 0.9955 [0.9917, 0.9993] | 1.0000 [1.0000, 1.0000] | 0.0045 [0.0007, 0.0084] |
| TLS | cope | LENGTH | 15 | hybrid | hybrid | cope | 0.9992 [0.9977, 1.0006] | 1.0000 [1.0000, 1.0000] | 0.0008 [-0.0006, 0.0023] |
| TLS | cope | LENGTH | 15 | p_champion | attr_content | cope | 0.9957 [0.9838, 1.0076] | 1.0000 [1.0000, 1.0000] | 0.0046 [-0.0084, 0.0175] |
| TLS | cope | LENGTH | 15 | nll_champion | shared_slot_hybrid | cope | 0.9770 [0.9008, 1.0531] | 1.0000 [1.0000, 1.0000] | 0.0293 [-0.0724, 0.1310] |
| TLS | tape | LENGTH | 15 | off | off | tape | 0.9846 [0.9695, 0.9996] | 1.0000 [1.0000, 1.0000] | 0.0170 [-0.0005, 0.0344] |
| TLS | tape | LENGTH | 15 | hybrid | hybrid | tape | 0.8506 [0.5340, 1.1673] | 0.9556 [0.8599, 1.0512] | 0.2534 [-0.3141, 0.8208] |
| TLS | tape | LENGTH | 15 | p_champion | attr_content | tape | 0.8810 [0.5670, 1.1951] | 0.9111 [0.6581, 1.1641] | 0.3594 [-0.8298, 1.5487] |
| TLS | tape | LENGTH | 15 | nll_champion | shared_slot_hybrid | tape | 0.7431 [0.3810, 1.1053] | 0.9778 [0.8822, 1.0734] | 0.3472 [-0.2086, 0.9030] |
| TLS | sdpa | LENGTH | 15 | off | off | sdpa | 0.9989 [0.9982, 0.9997] | 1.0000 [1.0000, 1.0000] | 0.0011 [0.0003, 0.0018] |
| TLS | sdpa | LENGTH | 15 | hybrid | hybrid | sdpa | 0.9997 [0.9995, 1.0000] | 1.0000 [1.0000, 1.0000] | 0.0003 [0.0000, 0.0005] |
| TLS | sdpa | LENGTH | 15 | p_champion | attr_content | sdpa | 0.9953 [0.9789, 1.0117] | 1.0000 [1.0000, 1.0000] | 0.0051 [-0.0131, 0.0233] |
| TLS | sdpa | LENGTH | 15 | nll_champion | shared_slot_hybrid | sdpa | 0.9989 [0.9977, 1.0002] | 1.0000 [1.0000, 1.0000] | 0.0011 [-0.0002, 0.0023] |
| SMB2 | rope | LENGTH | 30 | off | off | rope | 0.0530 [-0.0573, 0.1632] | 0.1444 [-0.0279, 0.3168] | 5.8553 [2.4434, 9.2671] |
| SMB2 | rope | OFFSET | 30 | off | off | rope | 0.0002 [-0.0001, 0.0006] | 0.0000 [0.0000, 0.0000] | 9.8622 [8.3156, 11.4089] |
| SMB2 | rope | LENGTH | 30 | hybrid | hybrid | rope | 0.0647 [-0.0897, 0.2191] | 0.3222 [-0.3722, 1.0167] | 5.0323 [1.9689, 8.0957] |
| SMB2 | rope | OFFSET | 30 | hybrid | hybrid | rope | 0.0023 [-0.0018, 0.0064] | 0.0000 [0.0000, 0.0000] | 6.6304 [4.5583, 8.7025] |
| SMB2 | rope | LENGTH | 30 | p_champion | attr_content | rope | 0.0951 [-0.1565, 0.3468] | 0.2222 [-0.3768, 0.8212] | 6.8705 [0.5179, 13.2230] |
| SMB2 | rope | OFFSET | 30 | p_champion | attr_content | rope | 0.0011 [-0.0005, 0.0027] | 0.0000 [0.0000, 0.0000] | 11.0851 [10.9839, 11.1864] |
| SMB2 | rope | LENGTH | 30 | nll_champion | attr_content | rope | 0.0951 [-0.1565, 0.3468] | 0.2222 [-0.3768, 0.8212] | 6.8705 [0.5179, 13.2230] |
| SMB2 | rope | OFFSET | 30 | nll_champion | attr_content | rope | 0.0011 [-0.0005, 0.0027] | 0.0000 [0.0000, 0.0000] | 11.0851 [10.9839, 11.1864] |
| SMB2 | cope | LENGTH | 30 | off | off | cope | 0.1043 [-0.1608, 0.3693] | 0.2444 [-0.3192, 0.8081] | 4.0012 [2.7079, 5.2945] |
| SMB2 | cope | OFFSET | 30 | off | off | cope | 0.0005 [-0.0002, 0.0012] | 0.0000 [0.0000, 0.0000] | 8.5718 [6.3349, 10.8088] |
| SMB2 | cope | LENGTH | 30 | hybrid | hybrid | cope | 0.0076 [-0.0171, 0.0324] | 0.0111 [-0.0367, 0.0589] | 7.6927 [1.4367, 13.9487] |
| SMB2 | cope | OFFSET | 30 | hybrid | hybrid | cope | 0.0009 [-0.0001, 0.0019] | 0.0000 [0.0000, 0.0000] | 7.8851 [4.6073, 11.1630] |
| SMB2 | cope | LENGTH | 30 | p_champion | attr_content | cope | 0.1010 [0.0547, 0.1472] | 0.2667 [-0.1715, 0.7048] | 6.2628 [3.3075, 9.2182] |
| SMB2 | cope | OFFSET | 30 | p_champion | attr_content | cope | 0.0002 [-0.0002, 0.0007] | 0.0000 [0.0000, 0.0000] | 13.8571 [9.2370, 18.4771] |
| SMB2 | cope | LENGTH | 30 | nll_champion | attr_content | cope | 0.1010 [0.0547, 0.1472] | 0.2667 [-0.1715, 0.7048] | 6.2628 [3.3075, 9.2182] |
| SMB2 | cope | OFFSET | 30 | nll_champion | attr_content | cope | 0.0002 [-0.0002, 0.0007] | 0.0000 [0.0000, 0.0000] | 13.8571 [9.2370, 18.4771] |
| SMB2 | tape | LENGTH | 30 | off | off | tape | 0.0590 [-0.0059, 0.1238] | 0.1889 [-0.3370, 0.7148] | 5.2700 [4.6051, 5.9348] |
| SMB2 | tape | OFFSET | 30 | off | off | tape | 0.0005 [-0.0004, 0.0014] | 0.0000 [0.0000, 0.0000] | 9.7811 [7.5537, 12.0084] |
| SMB2 | tape | LENGTH | 30 | hybrid | hybrid | tape | 0.1199 [-0.3306, 0.5703] | 0.1556 [-0.4435, 0.7546] | 4.6831 [2.6103, 6.7560] |
| SMB2 | tape | OFFSET | 30 | hybrid | hybrid | tape | 0.0027 [-0.0037, 0.0091] | 0.0000 [0.0000, 0.0000] | 6.7253 [4.3346, 9.1161] |
| SMB2 | tape | LENGTH | 30 | p_champion | attr_content | tape | 0.1494 [-0.1181, 0.4170] | 0.3444 [-0.2546, 0.9435] | 6.7198 [1.5357, 11.9039] |
| SMB2 | tape | OFFSET | 30 | p_champion | attr_content | tape | 0.0004 [-0.0003, 0.0011] | 0.0000 [0.0000, 0.0000] | 11.3204 [10.2661, 12.3747] |
| SMB2 | tape | LENGTH | 30 | nll_champion | attr_content | tape | 0.1494 [-0.1181, 0.4170] | 0.3444 [-0.2546, 0.9435] | 6.7198 [1.5357, 11.9039] |
| SMB2 | tape | OFFSET | 30 | nll_champion | attr_content | tape | 0.0004 [-0.0003, 0.0011] | 0.0000 [0.0000, 0.0000] | 11.3204 [10.2661, 12.3747] |
| SMB2 | sdpa | LENGTH | 30 | off | off | sdpa | 0.0802 [-0.1314, 0.2918] | 0.2556 [-0.3659, 0.8770] | 5.1083 [0.8542, 9.3624] |
| SMB2 | sdpa | OFFSET | 30 | off | off | sdpa | 0.0004 [-0.0009, 0.0018] | 0.0000 [0.0000, 0.0000] | 9.3146 [6.9991, 11.6300] |
| SMB2 | sdpa | LENGTH | 30 | hybrid | hybrid | sdpa | 0.0067 [-0.0040, 0.0174] | 0.0000 [0.0000, 0.0000] | 6.9482 [4.9658, 8.9307] |
| SMB2 | sdpa | OFFSET | 30 | hybrid | hybrid | sdpa | 0.0007 [-0.0014, 0.0029] | 0.0000 [0.0000, 0.0000] | 8.6268 [5.9059, 11.3476] |
| SMB2 | sdpa | LENGTH | 30 | p_champion | attr_content | sdpa | 0.1445 [-0.0970, 0.3860] | 0.2556 [-0.2768, 0.7879] | 6.4856 [1.1310, 11.8403] |
| SMB2 | sdpa | OFFSET | 30 | p_champion | attr_content | sdpa | 0.0003 [-0.0003, 0.0009] | 0.0000 [0.0000, 0.0000] | 14.5608 [9.2655, 19.8561] |
| SMB2 | sdpa | LENGTH | 30 | nll_champion | attr_content | sdpa | 0.1445 [-0.0970, 0.3860] | 0.2556 [-0.2768, 0.7879] | 6.4856 [1.1310, 11.8403] |
| SMB2 | sdpa | OFFSET | 30 | nll_champion | attr_content | sdpa | 0.0003 [-0.0003, 0.0009] | 0.0000 [0.0000, 0.0000] | 14.5608 [9.2655, 19.8561] |

## Final endpoint metrics by relation

| Target | Panel backbone | Cohort | N | Role | Formula | Actual backbone | p(target) [95% CI] | Hit@1 [95% CI] | NLL [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DNS | rope | DNS RDLENGTH | 25 | off | off | rope | 0.3967 [0.3919, 0.4014] | 0.4000 [0.4000, 0.4000] | 8.4859 [4.8191, 12.1527] |
| DNS | rope | DNS TXT length | 1 | off | off | rope | 0.9938 [0.9831, 1.0045] | 1.0000 [1.0000, 1.0000] | 0.0062 [-0.0046, 0.0170] |
| DNS | rope | DNS label | 164 | off | off | rope | 0.0000 [-0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 13.8983 [10.5172, 17.2794] |
| DNS | rope | DNS pointer | 36 | off | off | rope | 0.0000 [-0.0000, 0.0001] | 0.0000 [0.0000, 0.0000] | 13.1241 [6.5058, 19.7423] |
| DNS | rope | DNS root terminator | 40 | off | off | rope | 0.0494 [0.0477, 0.0511] | 0.0500 [0.0500, 0.0500] | 13.6397 [7.3565, 19.9229] |
| DNS | rope | DNS RDLENGTH | 25 | hybrid | hybrid | rope | 0.0493 [-0.0667, 0.1652] | 0.1733 [-0.3366, 0.6832] | 4.9679 [2.4049, 7.5309] |
| DNS | rope | DNS TXT length | 1 | hybrid | hybrid | rope | 0.1357 [-0.1971, 0.4685] | 0.3333 [-1.1009, 1.7676] | 2.5059 [-0.9660, 5.9777] |
| DNS | rope | DNS label | 164 | hybrid | hybrid | rope | 0.0121 [-0.0030, 0.0272] | 0.0020 [-0.0067, 0.0108] | 6.1264 [5.3009, 6.9519] |
| DNS | rope | DNS pointer | 36 | hybrid | hybrid | rope | 0.0068 [-0.0053, 0.0188] | 0.0000 [0.0000, 0.0000] | 5.7156 [3.3189, 8.1122] |
| DNS | rope | DNS root terminator | 40 | hybrid | hybrid | rope | 0.0133 [0.0055, 0.0210] | 0.0167 [-0.0550, 0.0884] | 5.7410 [4.3940, 7.0881] |
| DNS | rope | DNS RDLENGTH | 25 | p_champion | aux_small | rope | 0.1191 [0.0627, 0.1756] | 0.3733 [0.3160, 0.4307] | 4.2509 [3.3800, 5.1218] |
| DNS | rope | DNS TXT length | 1 | p_champion | aux_small | rope | 0.2543 [0.1824, 0.3262] | 1.0000 [1.0000, 1.0000] | 1.3736 [1.0910, 1.6561] |
| DNS | rope | DNS label | 164 | p_champion | aux_small | rope | 0.0057 [0.0002, 0.0112] | 0.0000 [0.0000, 0.0000] | 6.2318 [4.4639, 7.9998] |
| DNS | rope | DNS pointer | 36 | p_champion | aux_small | rope | 0.0050 [-0.0034, 0.0134] | 0.0000 [0.0000, 0.0000] | 5.8833 [3.1152, 8.6515] |
| DNS | rope | DNS root terminator | 40 | p_champion | aux_small | rope | 0.0207 [0.0049, 0.0364] | 0.0500 [0.0500, 0.0500] | 5.6234 [3.1079, 8.1390] |
| DNS | rope | DNS RDLENGTH | 25 | nll_champion | aux_small | rope | 0.1191 [0.0627, 0.1756] | 0.3733 [0.3160, 0.4307] | 4.2509 [3.3800, 5.1218] |
| DNS | rope | DNS TXT length | 1 | nll_champion | aux_small | rope | 0.2543 [0.1824, 0.3262] | 1.0000 [1.0000, 1.0000] | 1.3736 [1.0910, 1.6561] |
| DNS | rope | DNS label | 164 | nll_champion | aux_small | rope | 0.0057 [0.0002, 0.0112] | 0.0000 [0.0000, 0.0000] | 6.2318 [4.4639, 7.9998] |
| DNS | rope | DNS pointer | 36 | nll_champion | aux_small | rope | 0.0050 [-0.0034, 0.0134] | 0.0000 [0.0000, 0.0000] | 5.8833 [3.1152, 8.6515] |
| DNS | rope | DNS root terminator | 40 | nll_champion | aux_small | rope | 0.0207 [0.0049, 0.0364] | 0.0500 [0.0500, 0.0500] | 5.6234 [3.1079, 8.1390] |
| DNS | cope | DNS RDLENGTH | 25 | off | off | cope | 0.2440 [0.0588, 0.4293] | 0.3200 [0.1213, 0.5187] | 5.9398 [2.8988, 8.9808] |
| DNS | cope | DNS TXT length | 1 | off | off | cope | 0.9209 [0.6387, 1.2030] | 1.0000 [1.0000, 1.0000] | 0.0878 [-0.2306, 0.4062] |
| DNS | cope | DNS label | 164 | off | off | cope | 0.0037 [-0.0021, 0.0095] | 0.0000 [0.0000, 0.0000] | 10.2013 [7.8650, 12.5375] |
| DNS | cope | DNS pointer | 36 | off | off | cope | 0.0013 [-0.0013, 0.0039] | 0.0000 [0.0000, 0.0000] | 9.1499 [5.4344, 12.8653] |
| DNS | cope | DNS root terminator | 40 | off | off | cope | 0.0311 [-0.0245, 0.0867] | 0.0417 [0.0058, 0.0775] | 10.4546 [8.4471, 12.4621] |
| DNS | cope | DNS RDLENGTH | 25 | hybrid | hybrid | cope | 0.0538 [-0.0013, 0.1088] | 0.2667 [-0.1470, 0.6804] | 4.2565 [3.7452, 4.7678] |
| DNS | cope | DNS TXT length | 1 | hybrid | hybrid | cope | 0.1852 [-0.0761, 0.4465] | 0.6667 [-0.7676, 2.1009] | 1.7857 [0.4650, 3.1063] |
| DNS | cope | DNS label | 164 | hybrid | hybrid | cope | 0.0066 [0.0031, 0.0101] | 0.0000 [0.0000, 0.0000] | 6.2213 [5.1180, 7.3246] |
| DNS | cope | DNS pointer | 36 | hybrid | hybrid | cope | 0.0075 [-0.0024, 0.0174] | 0.0093 [-0.0306, 0.0491] | 5.6082 [4.1399, 7.0766] |
| DNS | cope | DNS root terminator | 40 | hybrid | hybrid | cope | 0.0119 [-0.0055, 0.0293] | 0.0333 [-0.0384, 0.1050] | 6.9759 [4.0537, 9.8981] |
| DNS | cope | DNS RDLENGTH | 25 | p_champion | aux_small | cope | 0.1079 [-0.0863, 0.3021] | 0.2667 [-0.2235, 0.7568] | 4.3122 [2.0465, 6.5779] |
| DNS | cope | DNS TXT length | 1 | p_champion | aux_small | cope | 0.3330 [-0.2470, 0.9129] | 0.6667 [-0.7676, 2.1009] | 1.3814 [-1.2097, 3.9725] |
| DNS | cope | DNS label | 164 | p_champion | aux_small | cope | 0.0056 [0.0010, 0.0102] | 0.0000 [0.0000, 0.0000] | 6.3073 [4.7077, 7.9068] |
| DNS | cope | DNS pointer | 36 | p_champion | aux_small | cope | 0.0080 [0.0051, 0.0109] | 0.0093 [-0.0306, 0.0491] | 5.4848 [5.4044, 5.5653] |
| DNS | cope | DNS root terminator | 40 | p_champion | aux_small | cope | 0.0158 [-0.0049, 0.0364] | 0.0333 [-0.0384, 0.1050] | 7.9282 [3.9856, 11.8707] |
| DNS | cope | DNS RDLENGTH | 25 | nll_champion | aux_small | cope | 0.1079 [-0.0863, 0.3021] | 0.2667 [-0.2235, 0.7568] | 4.3122 [2.0465, 6.5779] |
| DNS | cope | DNS TXT length | 1 | nll_champion | aux_small | cope | 0.3330 [-0.2470, 0.9129] | 0.6667 [-0.7676, 2.1009] | 1.3814 [-1.2097, 3.9725] |
| DNS | cope | DNS label | 164 | nll_champion | aux_small | cope | 0.0056 [0.0010, 0.0102] | 0.0000 [0.0000, 0.0000] | 6.3073 [4.7077, 7.9068] |
| DNS | cope | DNS pointer | 36 | nll_champion | aux_small | cope | 0.0080 [0.0051, 0.0109] | 0.0093 [-0.0306, 0.0491] | 5.4848 [5.4044, 5.5653] |
| DNS | cope | DNS root terminator | 40 | nll_champion | aux_small | cope | 0.0158 [-0.0049, 0.0364] | 0.0333 [-0.0384, 0.1050] | 7.9282 [3.9856, 11.8707] |
| DNS | tape | DNS RDLENGTH | 25 | off | off | tape | 0.2725 [-0.0002, 0.5451] | 0.2933 [-0.0102, 0.5969] | 11.7003 [1.0448, 22.3557] |
| DNS | tape | DNS TXT length | 1 | off | off | tape | 0.6635 [-0.7254, 2.0525] | 0.6667 [-0.7676, 2.1009] | 1.3477 [-4.3914, 7.0868] |
| DNS | tape | DNS label | 164 | off | off | tape | 0.0005 [-0.0008, 0.0017] | 0.0000 [0.0000, 0.0000] | 23.6304 [8.8513, 38.4094] |
| DNS | tape | DNS pointer | 36 | off | off | tape | 0.0001 [-0.0003, 0.0006] | 0.0000 [0.0000, 0.0000] | 19.1988 [1.9714, 36.4262] |
| DNS | tape | DNS root terminator | 40 | off | off | tape | 0.0394 [-0.0025, 0.0813] | 0.0417 [0.0058, 0.0775] | 25.1934 [4.4330, 45.9538] |
| DNS | tape | DNS RDLENGTH | 25 | hybrid | hybrid | tape | 0.0534 [-0.0666, 0.1735] | 0.2400 [-0.2763, 0.7563] | 5.1074 [2.8873, 7.3275] |
| DNS | tape | DNS TXT length | 1 | hybrid | hybrid | tape | 0.1529 [-0.2026, 0.5083] | 0.6667 [-0.7676, 2.1009] | 3.1413 [-3.9096, 10.1921] |
| DNS | tape | DNS label | 164 | hybrid | hybrid | tape | 0.0107 [-0.0011, 0.0225] | 0.0020 [-0.0067, 0.0108] | 6.2327 [4.7234, 7.7420] |
| DNS | tape | DNS pointer | 36 | hybrid | hybrid | tape | 0.0051 [-0.0023, 0.0125] | 0.0000 [0.0000, 0.0000] | 5.8945 [3.6451, 8.1439] |
| DNS | tape | DNS root terminator | 40 | hybrid | hybrid | tape | 0.0195 [0.0022, 0.0367] | 0.0083 [-0.0275, 0.0442] | 5.0575 [1.8849, 8.2301] |
| DNS | tape | DNS RDLENGTH | 25 | p_champion | aux_small | tape | 0.0664 [0.0288, 0.1039] | 0.3067 [0.0998, 0.5135] | 5.0336 [2.8359, 7.2313] |
| DNS | tape | DNS TXT length | 1 | p_champion | aux_small | tape | 0.2246 [0.1476, 0.3016] | 1.0000 [1.0000, 1.0000] | 1.4997 [1.1638, 1.8356] |
| DNS | tape | DNS label | 164 | p_champion | aux_small | tape | 0.0096 [0.0057, 0.0136] | 0.0020 [-0.0067, 0.0108] | 6.8621 [1.9525, 11.7718] |
| DNS | tape | DNS pointer | 36 | p_champion | aux_small | tape | 0.0070 [-0.0061, 0.0201] | 0.0000 [0.0000, 0.0000] | 6.1117 [1.2089, 11.0146] |
| DNS | tape | DNS root terminator | 40 | p_champion | aux_small | tape | 0.0163 [-0.0088, 0.0413] | 0.0333 [-0.0384, 0.1050] | 6.5154 [-0.4091, 13.4399] |
| DNS | tape | DNS RDLENGTH | 25 | nll_champion | aux_small | tape | 0.0664 [0.0288, 0.1039] | 0.3067 [0.0998, 0.5135] | 5.0336 [2.8359, 7.2313] |
| DNS | tape | DNS TXT length | 1 | nll_champion | aux_small | tape | 0.2246 [0.1476, 0.3016] | 1.0000 [1.0000, 1.0000] | 1.4997 [1.1638, 1.8356] |
| DNS | tape | DNS label | 164 | nll_champion | aux_small | tape | 0.0096 [0.0057, 0.0136] | 0.0020 [-0.0067, 0.0108] | 6.8621 [1.9525, 11.7718] |
| DNS | tape | DNS pointer | 36 | nll_champion | aux_small | tape | 0.0070 [-0.0061, 0.0201] | 0.0000 [0.0000, 0.0000] | 6.1117 [1.2089, 11.0146] |
| DNS | tape | DNS root terminator | 40 | nll_champion | aux_small | tape | 0.0163 [-0.0088, 0.0413] | 0.0333 [-0.0384, 0.1050] | 6.5154 [-0.4091, 13.4399] |
| DNS | sdpa | DNS RDLENGTH | 25 | off | off | sdpa | 0.3685 [0.2969, 0.4401] | 0.4000 [0.4000, 0.4000] | 6.6882 [3.0113, 10.3652] |
| DNS | sdpa | DNS TXT length | 1 | off | off | sdpa | 0.9483 [0.7655, 1.1312] | 1.0000 [1.0000, 1.0000] | 0.0551 [-0.1423, 0.2525] |
| DNS | sdpa | DNS label | 164 | off | off | sdpa | 0.0015 [-0.0014, 0.0043] | 0.0000 [0.0000, 0.0000] | 10.5471 [6.8629, 14.2314] |
| DNS | sdpa | DNS pointer | 36 | off | off | sdpa | 0.0010 [-0.0013, 0.0033] | 0.0000 [0.0000, 0.0000] | 10.5229 [4.0182, 17.0277] |
| DNS | sdpa | DNS root terminator | 40 | off | off | sdpa | 0.0412 [0.0102, 0.0722] | 0.0500 [0.0500, 0.0500] | 10.4554 [5.9505, 14.9603] |
| DNS | sdpa | DNS RDLENGTH | 25 | hybrid | hybrid | sdpa | 0.0117 [0.0009, 0.0224] | 0.0667 [-0.0851, 0.2184] | 4.9391 [4.2620, 5.6162] |
| DNS | sdpa | DNS TXT length | 1 | hybrid | hybrid | sdpa | 0.0201 [-0.0271, 0.0673] | 0.3333 [-1.1009, 1.7676] | 4.1875 [1.9886, 6.3864] |
| DNS | sdpa | DNS label | 164 | hybrid | hybrid | sdpa | 0.0103 [0.0045, 0.0161] | 0.0000 [0.0000, 0.0000] | 5.6071 [4.3573, 6.8568] |
| DNS | sdpa | DNS pointer | 36 | hybrid | hybrid | sdpa | 0.0072 [0.0054, 0.0089] | 0.0000 [0.0000, 0.0000] | 5.3944 [5.0544, 5.7344] |
| DNS | sdpa | DNS root terminator | 40 | hybrid | hybrid | sdpa | 0.0097 [0.0012, 0.0182] | 0.0083 [-0.0275, 0.0442] | 6.5406 [5.5907, 7.4905] |
| DNS | sdpa | DNS RDLENGTH | 25 | p_champion | aux_small | sdpa | 0.1159 [0.0996, 0.1323] | 0.3733 [0.3160, 0.4307] | 3.8679 [3.6673, 4.0685] |
| DNS | sdpa | DNS TXT length | 1 | p_champion | aux_small | sdpa | 0.3533 [0.0402, 0.6664] | 1.0000 [1.0000, 1.0000] | 1.0925 [0.0625, 2.1225] |
| DNS | sdpa | DNS label | 164 | p_champion | aux_small | sdpa | 0.0063 [0.0020, 0.0106] | 0.0000 [0.0000, 0.0000] | 6.6575 [6.4290, 6.8859] |
| DNS | sdpa | DNS pointer | 36 | p_champion | aux_small | sdpa | 0.0055 [-0.0007, 0.0117] | 0.0000 [0.0000, 0.0000] | 6.0187 [3.7282, 8.3091] |
| DNS | sdpa | DNS root terminator | 40 | p_champion | aux_small | sdpa | 0.0172 [-0.0074, 0.0417] | 0.0417 [0.0058, 0.0775] | 6.6389 [5.1710, 8.1067] |
| DNS | sdpa | DNS RDLENGTH | 25 | nll_champion | aux_small | sdpa | 0.1159 [0.0996, 0.1323] | 0.3733 [0.3160, 0.4307] | 3.8679 [3.6673, 4.0685] |
| DNS | sdpa | DNS TXT length | 1 | nll_champion | aux_small | sdpa | 0.3533 [0.0402, 0.6664] | 1.0000 [1.0000, 1.0000] | 1.0925 [0.0625, 2.1225] |
| DNS | sdpa | DNS label | 164 | nll_champion | aux_small | sdpa | 0.0063 [0.0020, 0.0106] | 0.0000 [0.0000, 0.0000] | 6.6575 [6.4290, 6.8859] |
| DNS | sdpa | DNS pointer | 36 | nll_champion | aux_small | sdpa | 0.0055 [-0.0007, 0.0117] | 0.0000 [0.0000, 0.0000] | 6.0187 [3.7282, 8.3091] |
| DNS | sdpa | DNS root terminator | 40 | nll_champion | aux_small | sdpa | 0.0172 [-0.0074, 0.0417] | 0.0417 [0.0058, 0.0775] | 6.6389 [5.1710, 8.1067] |
| MODBUS | rope | Modbus MBAP length | 6 | off | off | rope | 0.5288 [-0.2363, 1.2939] | 0.6667 [-0.4287, 1.7621] | 1.0431 [-1.7244, 3.8106] |
| MODBUS | rope | Modbus MBAP length | 6 | hybrid | hybrid | rope | 0.8162 [0.5873, 1.0452] | 1.0000 [1.0000, 1.0000] | 0.2463 [-0.0744, 0.5670] |
| MODBUS | rope | Modbus MBAP length | 6 | p_champion | mix_entropy | rope | 0.8081 [0.5912, 1.0250] | 1.0000 [1.0000, 1.0000] | 0.2224 [-0.0483, 0.4931] |
| MODBUS | rope | Modbus MBAP length | 6 | nll_champion | hybrid | rope | 0.8162 [0.5873, 1.0452] | 1.0000 [1.0000, 1.0000] | 0.2463 [-0.0744, 0.5670] |
| MODBUS | cope | Modbus MBAP length | 6 | off | off | cope | 0.3064 [0.0578, 0.5550] | 0.3333 [-0.0807, 0.7474] | 1.7655 [1.1044, 2.4266] |
| MODBUS | cope | Modbus MBAP length | 6 | hybrid | hybrid | cope | 0.8090 [0.5005, 1.1175] | 1.0000 [1.0000, 1.0000] | 0.2633 [-0.1947, 0.7212] |
| MODBUS | cope | Modbus MBAP length | 6 | p_champion | mix_entropy | cope | 0.7300 [0.2760, 1.1840] | 0.8333 [0.4193, 1.2474] | 0.3963 [-0.3412, 1.1338] |
| MODBUS | cope | Modbus MBAP length | 6 | nll_champion | hybrid | cope | 0.8090 [0.5005, 1.1175] | 1.0000 [1.0000, 1.0000] | 0.2633 [-0.1947, 0.7212] |
| MODBUS | tape | Modbus MBAP length | 6 | off | off | tape | 0.5225 [-0.1124, 1.1574] | 0.5000 [0.0860, 0.9140] | 1.1847 [-0.6805, 3.0499] |
| MODBUS | tape | Modbus MBAP length | 6 | hybrid | hybrid | tape | 0.8163 [0.3072, 1.3253] | 0.8889 [0.4108, 1.3670] | 0.2907 [-0.6502, 1.2316] |
| MODBUS | tape | Modbus MBAP length | 6 | p_champion | mix_entropy | tape | 0.7257 [0.4521, 0.9993] | 0.8889 [0.4108, 1.3670] | 0.3994 [-0.1852, 0.9839] |
| MODBUS | tape | Modbus MBAP length | 6 | nll_champion | hybrid | tape | 0.8163 [0.3072, 1.3253] | 0.8889 [0.4108, 1.3670] | 0.2907 [-0.6502, 1.2316] |
| MODBUS | sdpa | Modbus MBAP length | 6 | off | off | sdpa | 0.4398 [-0.0753, 0.9549] | 0.6111 [-0.2507, 1.4730] | 1.3229 [-0.7364, 3.3821] |
| MODBUS | sdpa | Modbus MBAP length | 6 | hybrid | hybrid | sdpa | 0.6448 [0.1473, 1.1422] | 0.7222 [0.0898, 1.3547] | 0.5992 [-0.5245, 1.7229] |
| MODBUS | sdpa | Modbus MBAP length | 6 | p_champion | mix_entropy | sdpa | 0.8246 [0.4571, 1.1921] | 0.8889 [0.4108, 1.3670] | 0.2196 [-0.3116, 0.7508] |
| MODBUS | sdpa | Modbus MBAP length | 6 | nll_champion | hybrid | sdpa | 0.6448 [0.1473, 1.1422] | 0.7222 [0.0898, 1.3547] | 0.5992 [-0.5245, 1.7229] |
| TLS | rope | TLS record length | 15 | off | off | rope | 0.9767 [0.9224, 1.0309] | 1.0000 [1.0000, 1.0000] | 0.0333 [-0.0546, 0.1211] |
| TLS | rope | TLS record length | 15 | hybrid | hybrid | rope | 0.8181 [0.8010, 0.8352] | 0.9556 [0.8599, 1.0512] | 0.2851 [0.1567, 0.4135] |
| TLS | rope | TLS record length | 15 | p_champion | attr_content | rope | 0.8650 [0.7619, 0.9682] | 0.8889 [0.7933, 0.9845] | 0.4126 [-0.3035, 1.1286] |
| TLS | rope | TLS record length | 15 | nll_champion | shared_slot_hybrid | rope | 0.8226 [0.2709, 1.3744] | 0.8889 [0.5441, 1.2336] | 0.3897 [-0.5996, 1.3791] |
| TLS | cope | TLS record length | 15 | off | off | cope | 0.9955 [0.9917, 0.9993] | 1.0000 [1.0000, 1.0000] | 0.0045 [0.0007, 0.0084] |
| TLS | cope | TLS record length | 15 | hybrid | hybrid | cope | 0.9992 [0.9977, 1.0006] | 1.0000 [1.0000, 1.0000] | 0.0008 [-0.0006, 0.0023] |
| TLS | cope | TLS record length | 15 | p_champion | attr_content | cope | 0.9957 [0.9838, 1.0076] | 1.0000 [1.0000, 1.0000] | 0.0046 [-0.0084, 0.0175] |
| TLS | cope | TLS record length | 15 | nll_champion | shared_slot_hybrid | cope | 0.9770 [0.9008, 1.0531] | 1.0000 [1.0000, 1.0000] | 0.0293 [-0.0724, 0.1310] |
| TLS | tape | TLS record length | 15 | off | off | tape | 0.9846 [0.9695, 0.9996] | 1.0000 [1.0000, 1.0000] | 0.0170 [-0.0005, 0.0344] |
| TLS | tape | TLS record length | 15 | hybrid | hybrid | tape | 0.8506 [0.5340, 1.1673] | 0.9556 [0.8599, 1.0512] | 0.2534 [-0.3141, 0.8208] |
| TLS | tape | TLS record length | 15 | p_champion | attr_content | tape | 0.8810 [0.5670, 1.1951] | 0.9111 [0.6581, 1.1641] | 0.3594 [-0.8298, 1.5487] |
| TLS | tape | TLS record length | 15 | nll_champion | shared_slot_hybrid | tape | 0.7431 [0.3810, 1.1053] | 0.9778 [0.8822, 1.0734] | 0.3472 [-0.2086, 0.9030] |
| TLS | sdpa | TLS record length | 15 | off | off | sdpa | 0.9989 [0.9982, 0.9997] | 1.0000 [1.0000, 1.0000] | 0.0011 [0.0003, 0.0018] |
| TLS | sdpa | TLS record length | 15 | hybrid | hybrid | sdpa | 0.9997 [0.9995, 1.0000] | 1.0000 [1.0000, 1.0000] | 0.0003 [0.0000, 0.0005] |
| TLS | sdpa | TLS record length | 15 | p_champion | attr_content | sdpa | 0.9953 [0.9789, 1.0117] | 1.0000 [1.0000, 1.0000] | 0.0051 [-0.0131, 0.0233] |
| TLS | sdpa | TLS record length | 15 | nll_champion | shared_slot_hybrid | sdpa | 0.9989 [0.9977, 1.0002] | 1.0000 [1.0000, 1.0000] | 0.0011 [-0.0002, 0.0023] |
| SMB2 | rope | SMB2 ContextLength | 15 | off | off | rope | 0.0732 [-0.0867, 0.2331] | 0.1778 [-0.2047, 0.5602] | 4.0839 [-1.8082, 9.9760] |
| SMB2 | rope | SMB2 ContextOffset | 15 | off | off | rope | 0.0004 [-0.0002, 0.0010] | 0.0000 [0.0000, 0.0000] | 9.0357 [7.4884, 10.5831] |
| SMB2 | rope | SMB2 NameLength | 15 | off | off | rope | 0.0328 [-0.0424, 0.1079] | 0.1111 [0.0155, 0.2067] | 7.6266 [6.3172, 8.9359] |
| SMB2 | rope | SMB2 NameOffset | 15 | off | off | rope | 0.0001 [-0.0000, 0.0002] | 0.0000 [0.0000, 0.0000] | 10.6888 [8.8217, 12.5558] |
| SMB2 | rope | SMB2 ContextLength | 15 | hybrid | hybrid | rope | 0.0984 [-0.1389, 0.3358] | 0.5778 [-0.6652, 1.8208] | 3.6339 [-1.1775, 8.4452] |
| SMB2 | rope | SMB2 ContextOffset | 15 | hybrid | hybrid | rope | 0.0021 [-0.0026, 0.0068] | 0.0000 [0.0000, 0.0000] | 6.6185 [4.3825, 8.8546] |
| SMB2 | rope | SMB2 NameLength | 15 | hybrid | hybrid | rope | 0.0309 [-0.0412, 0.1031] | 0.0667 [-0.0989, 0.2323] | 6.4307 [1.7609, 11.1004] |
| SMB2 | rope | SMB2 NameOffset | 15 | hybrid | hybrid | rope | 0.0026 [-0.0011, 0.0062] | 0.0000 [0.0000, 0.0000] | 6.6422 [4.7340, 8.5503] |
| SMB2 | rope | SMB2 ContextLength | 15 | p_champion | attr_content | rope | 0.1265 [-0.3831, 0.6361] | 0.3111 [-0.8869, 1.5092] | 5.6663 [-2.8266, 14.1591] |
| SMB2 | rope | SMB2 ContextOffset | 15 | p_champion | attr_content | rope | 0.0022 [-0.0010, 0.0055] | 0.0000 [0.0000, 0.0000] | 7.2634 [3.7534, 10.7734] |
| SMB2 | rope | SMB2 NameLength | 15 | p_champion | attr_content | rope | 0.0638 [-0.0309, 0.1586] | 0.1333 [0.1333, 0.1333] | 8.0747 [1.8923, 14.2570] |
| SMB2 | rope | SMB2 NameOffset | 15 | p_champion | attr_content | rope | 0.0000 [-0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 14.9068 [11.5234, 18.2903] |
| SMB2 | rope | SMB2 ContextLength | 15 | nll_champion | attr_content | rope | 0.1265 [-0.3831, 0.6361] | 0.3111 [-0.8869, 1.5092] | 5.6663 [-2.8266, 14.1591] |
| SMB2 | rope | SMB2 ContextOffset | 15 | nll_champion | attr_content | rope | 0.0022 [-0.0010, 0.0055] | 0.0000 [0.0000, 0.0000] | 7.2634 [3.7534, 10.7734] |
| SMB2 | rope | SMB2 NameLength | 15 | nll_champion | attr_content | rope | 0.0638 [-0.0309, 0.1586] | 0.1333 [0.1333, 0.1333] | 8.0747 [1.8923, 14.2570] |
| SMB2 | rope | SMB2 NameOffset | 15 | nll_champion | attr_content | rope | 0.0000 [-0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 14.9068 [11.5234, 18.2903] |
| SMB2 | cope | SMB2 ContextLength | 15 | off | off | cope | 0.1584 [-0.3240, 0.6409] | 0.4000 [-0.6074, 1.4074] | 2.7899 [-0.2517, 5.8315] |
| SMB2 | cope | SMB2 ContextOffset | 15 | off | off | cope | 0.0008 [-0.0004, 0.0020] | 0.0000 [0.0000, 0.0000] | 7.8136 [6.3163, 9.3110] |
| SMB2 | cope | SMB2 NameLength | 15 | off | off | cope | 0.0501 [-0.0056, 0.1059] | 0.0889 [-0.1023, 0.2801] | 5.2126 [4.5513, 5.8738] |
| SMB2 | cope | SMB2 NameOffset | 15 | off | off | cope | 0.0002 [-0.0002, 0.0007] | 0.0000 [0.0000, 0.0000] | 9.3300 [5.6326, 13.0275] |
| SMB2 | cope | SMB2 ContextLength | 15 | hybrid | hybrid | cope | 0.0057 [-0.0175, 0.0288] | 0.0222 [-0.0734, 0.1178] | 8.7192 [-1.8484, 19.2868] |
| SMB2 | cope | SMB2 ContextOffset | 15 | hybrid | hybrid | cope | 0.0009 [-0.0011, 0.0029] | 0.0000 [0.0000, 0.0000] | 8.0279 [2.9685, 13.0873] |
| SMB2 | cope | SMB2 NameLength | 15 | hybrid | hybrid | cope | 0.0096 [-0.0168, 0.0361] | 0.0000 [0.0000, 0.0000] | 6.6661 [4.5241, 8.8082] |
| SMB2 | cope | SMB2 NameOffset | 15 | hybrid | hybrid | cope | 0.0009 [0.0008, 0.0010] | 0.0000 [0.0000, 0.0000] | 7.7423 [6.2171, 9.2675] |
| SMB2 | cope | SMB2 ContextLength | 15 | p_champion | attr_content | cope | 0.1139 [-0.0480, 0.2759] | 0.4000 [-0.4763, 1.2763] | 3.5439 [1.8603, 5.2275] |
| SMB2 | cope | SMB2 ContextOffset | 15 | p_champion | attr_content | cope | 0.0005 [-0.0005, 0.0014] | 0.0000 [0.0000, 0.0000] | 9.6644 [8.1928, 11.1360] |
| SMB2 | cope | SMB2 NameLength | 15 | p_champion | attr_content | cope | 0.0880 [0.0153, 0.1608] | 0.1333 [0.1333, 0.1333] | 8.9817 [4.0502, 13.9133] |
| SMB2 | cope | SMB2 NameOffset | 15 | p_champion | attr_content | cope | 0.0000 [-0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 18.0498 [7.8878, 28.2118] |
| SMB2 | cope | SMB2 ContextLength | 15 | nll_champion | attr_content | cope | 0.1139 [-0.0480, 0.2759] | 0.4000 [-0.4763, 1.2763] | 3.5439 [1.8603, 5.2275] |
| SMB2 | cope | SMB2 ContextOffset | 15 | nll_champion | attr_content | cope | 0.0005 [-0.0005, 0.0014] | 0.0000 [0.0000, 0.0000] | 9.6644 [8.1928, 11.1360] |
| SMB2 | cope | SMB2 NameLength | 15 | nll_champion | attr_content | cope | 0.0880 [0.0153, 0.1608] | 0.1333 [0.1333, 0.1333] | 8.9817 [4.0502, 13.9133] |
| SMB2 | cope | SMB2 NameOffset | 15 | nll_champion | attr_content | cope | 0.0000 [-0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 18.0498 [7.8878, 28.2118] |
| SMB2 | tape | SMB2 ContextLength | 15 | off | off | tape | 0.0744 [-0.1390, 0.2877] | 0.2889 [-0.9541, 1.5319] | 3.3962 [1.1493, 5.6431] |
| SMB2 | tape | SMB2 ContextOffset | 15 | off | off | tape | 0.0008 [-0.0010, 0.0026] | 0.0000 [0.0000, 0.0000] | 8.5274 [6.8895, 10.1653] |
| SMB2 | tape | SMB2 NameLength | 15 | off | off | tape | 0.0436 [-0.0422, 0.1293] | 0.0889 [-0.1023, 0.2801] | 7.1437 [3.6793, 10.6082] |
| SMB2 | tape | SMB2 NameOffset | 15 | off | off | tape | 0.0002 [0.0001, 0.0003] | 0.0000 [0.0000, 0.0000] | 11.0347 [7.3552, 14.7143] |
| SMB2 | tape | SMB2 ContextLength | 15 | hybrid | hybrid | tape | 0.2188 [-0.6796, 1.1173] | 0.2889 [-0.9541, 1.5319] | 3.5632 [-1.5038, 8.6302] |
| SMB2 | tape | SMB2 ContextOffset | 15 | hybrid | hybrid | tape | 0.0013 [-0.0012, 0.0037] | 0.0000 [0.0000, 0.0000] | 7.1600 [4.6918, 9.6281] |
| SMB2 | tape | SMB2 NameLength | 15 | hybrid | hybrid | tape | 0.0209 [-0.0159, 0.0577] | 0.0222 [-0.0734, 0.1178] | 5.8031 [4.7429, 6.8632] |
| SMB2 | tape | SMB2 NameOffset | 15 | hybrid | hybrid | tape | 0.0041 [-0.0067, 0.0148] | 0.0000 [0.0000, 0.0000] | 6.2907 [3.2864, 9.2950] |
| SMB2 | tape | SMB2 ContextLength | 15 | p_champion | attr_content | tape | 0.2249 [-0.2215, 0.6714] | 0.5556 [-0.6425, 1.7536] | 3.6892 [-1.6219, 9.0004] |
| SMB2 | tape | SMB2 ContextOffset | 15 | p_champion | attr_content | tape | 0.0009 [-0.0006, 0.0023] | 0.0000 [0.0000, 0.0000] | 8.1603 [6.6922, 9.6283] |
| SMB2 | tape | SMB2 NameLength | 15 | p_champion | attr_content | tape | 0.0739 [-0.0367, 0.1846] | 0.1333 [0.1333, 0.1333] | 9.7504 [2.0326, 17.4681] |
| SMB2 | tape | SMB2 NameOffset | 15 | p_champion | attr_content | tape | 0.0000 [-0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 14.4805 [10.9103, 18.0507] |
| SMB2 | tape | SMB2 ContextLength | 15 | nll_champion | attr_content | tape | 0.2249 [-0.2215, 0.6714] | 0.5556 [-0.6425, 1.7536] | 3.6892 [-1.6219, 9.0004] |
| SMB2 | tape | SMB2 ContextOffset | 15 | nll_champion | attr_content | tape | 0.0009 [-0.0006, 0.0023] | 0.0000 [0.0000, 0.0000] | 8.1603 [6.6922, 9.6283] |
| SMB2 | tape | SMB2 NameLength | 15 | nll_champion | attr_content | tape | 0.0739 [-0.0367, 0.1846] | 0.1333 [0.1333, 0.1333] | 9.7504 [2.0326, 17.4681] |
| SMB2 | tape | SMB2 NameOffset | 15 | nll_champion | attr_content | tape | 0.0000 [-0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 14.4805 [10.9103, 18.0507] |
| SMB2 | sdpa | SMB2 ContextLength | 15 | off | off | sdpa | 0.1260 [-0.1777, 0.4297] | 0.4667 [-0.6193, 1.5526] | 4.0577 [-3.6491, 11.7645] |
| SMB2 | sdpa | SMB2 ContextOffset | 15 | off | off | sdpa | 0.0008 [-0.0020, 0.0035] | 0.0000 [0.0000, 0.0000] | 8.2041 [3.8852, 12.5230] |
| SMB2 | sdpa | SMB2 NameLength | 15 | off | off | sdpa | 0.0345 [-0.1003, 0.1692] | 0.0444 [-0.1468, 0.2357] | 6.1589 [5.0570, 7.2609] |
| SMB2 | sdpa | SMB2 NameOffset | 15 | off | off | sdpa | 0.0001 [-0.0000, 0.0002] | 0.0000 [0.0000, 0.0000] | 10.4251 [9.9559, 10.8943] |
| SMB2 | sdpa | SMB2 ContextLength | 15 | hybrid | hybrid | sdpa | 0.0039 [-0.0041, 0.0119] | 0.0000 [0.0000, 0.0000] | 6.4254 [4.4763, 8.3746] |
| SMB2 | sdpa | SMB2 ContextOffset | 15 | hybrid | hybrid | sdpa | 0.0004 [-0.0003, 0.0011] | 0.0000 [0.0000, 0.0000] | 8.5781 [6.1317, 11.0245] |
| SMB2 | sdpa | SMB2 NameLength | 15 | hybrid | hybrid | sdpa | 0.0095 [-0.0071, 0.0260] | 0.0000 [0.0000, 0.0000] | 7.4710 [5.2259, 9.7162] |
| SMB2 | sdpa | SMB2 NameOffset | 15 | hybrid | hybrid | sdpa | 0.0011 [-0.0029, 0.0051] | 0.0000 [0.0000, 0.0000] | 8.6754 [5.2161, 12.1347] |
| SMB2 | sdpa | SMB2 ContextLength | 15 | p_champion | attr_content | sdpa | 0.2026 [-0.2592, 0.6644] | 0.3778 [-0.6869, 1.4425] | 3.1685 [-0.3461, 6.6830] |
| SMB2 | sdpa | SMB2 ContextOffset | 15 | p_champion | attr_content | sdpa | 0.0006 [-0.0008, 0.0020] | 0.0000 [0.0000, 0.0000] | 10.5478 [5.7018, 15.3939] |
| SMB2 | sdpa | SMB2 NameLength | 15 | p_champion | attr_content | sdpa | 0.0863 [0.0619, 0.1107] | 0.1333 [0.1333, 0.1333] | 9.8028 [-0.4864, 20.0919] |
| SMB2 | sdpa | SMB2 NameOffset | 15 | p_champion | attr_content | sdpa | 0.0000 [-0.0001, 0.0002] | 0.0000 [0.0000, 0.0000] | 18.5737 [9.1491, 27.9984] |
| SMB2 | sdpa | SMB2 ContextLength | 15 | nll_champion | attr_content | sdpa | 0.2026 [-0.2592, 0.6644] | 0.3778 [-0.6869, 1.4425] | 3.1685 [-0.3461, 6.6830] |
| SMB2 | sdpa | SMB2 ContextOffset | 15 | nll_champion | attr_content | sdpa | 0.0006 [-0.0008, 0.0020] | 0.0000 [0.0000, 0.0000] | 10.5478 [5.7018, 15.3939] |
| SMB2 | sdpa | SMB2 NameLength | 15 | nll_champion | attr_content | sdpa | 0.0863 [0.0619, 0.1107] | 0.1333 [0.1333, 0.1333] | 9.8028 [-0.4864, 20.0919] |
| SMB2 | sdpa | SMB2 NameOffset | 15 | nll_champion | attr_content | sdpa | 0.0000 [-0.0001, 0.0002] | 0.0000 [0.0000, 0.0000] | 18.5737 [9.1491, 27.9984] |

## Final endpoint metrics by target kind

| Target | Panel backbone | Cohort | N | Role | Formula | Actual backbone | p(target) [95% CI] | Hit@1 [95% CI] | NLL [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DNS | rope | END | 13 | off | off | rope | 0.9909 [0.9856, 0.9963] | 1.0000 [1.0000, 1.0000] | 0.0092 [0.0038, 0.0145] |
| DNS | rope | INTERIOR | 253 | off | off | rope | 0.0000 [-0.0000, 0.0001] | 0.0000 [0.0000, 0.0000] | 13.8712 [9.7408, 18.0016] |
| DNS | rope | END | 13 | hybrid | hybrid | rope | 0.1164 [-0.1815, 0.4144] | 0.4103 [-0.8904, 1.7110] | 2.9876 [-1.2402, 7.2153] |
| DNS | rope | INTERIOR | 253 | hybrid | hybrid | rope | 0.0103 [-0.0009, 0.0216] | 0.0013 [-0.0044, 0.0070] | 6.0395 [4.9677, 7.1113] |
| DNS | rope | END | 13 | p_champion | aux_small | rope | 0.2903 [0.1376, 0.4430] | 0.9487 [0.8384, 1.0590] | 1.3435 [0.6998, 1.9872] |
| DNS | rope | INTERIOR | 253 | p_champion | aux_small | rope | 0.0055 [-0.0008, 0.0118] | 0.0000 [0.0000, 0.0000] | 6.1223 [4.1512, 8.0934] |
| DNS | rope | END | 13 | nll_champion | aux_small | rope | 0.2903 [0.1376, 0.4430] | 0.9487 [0.8384, 1.0590] | 1.3435 [0.6998, 1.9872] |
| DNS | rope | INTERIOR | 253 | nll_champion | aux_small | rope | 0.0055 [-0.0008, 0.0118] | 0.0000 [0.0000, 0.0000] | 6.1223 [4.1512, 8.0934] |
| DNS | cope | END | 13 | off | off | cope | 0.6291 [0.0994, 1.1587] | 0.8205 [0.3396, 1.3014] | 0.9700 [-0.7484, 2.6884] |
| DNS | cope | INTERIOR | 253 | off | off | cope | 0.0029 [-0.0022, 0.0080] | 0.0000 [0.0000, 0.0000] | 10.1050 [7.8586, 12.3514] |
| DNS | cope | END | 13 | hybrid | hybrid | cope | 0.1280 [-0.0125, 0.2684] | 0.6667 [-0.4530, 1.7863] | 2.3318 [1.5934, 3.0702] |
| DNS | cope | INTERIOR | 253 | hybrid | hybrid | cope | 0.0067 [0.0032, 0.0102] | 0.0013 [-0.0044, 0.0070] | 6.2415 [4.9127, 7.5703] |
| DNS | cope | END | 13 | p_champion | aux_small | cope | 0.2672 [-0.2241, 0.7585] | 0.6667 [-0.6057, 1.9390] | 1.9577 [-1.9500, 5.8653] |
| DNS | cope | INTERIOR | 253 | p_champion | aux_small | cope | 0.0055 [0.0017, 0.0093] | 0.0013 [-0.0044, 0.0070] | 6.4534 [4.8446, 8.0622] |
| DNS | cope | END | 13 | nll_champion | aux_small | cope | 0.2672 [-0.2241, 0.7585] | 0.6667 [-0.6057, 1.9390] | 1.9577 [-1.9500, 5.8653] |
| DNS | cope | INTERIOR | 253 | nll_champion | aux_small | cope | 0.0055 [0.0017, 0.0093] | 0.0013 [-0.0044, 0.0070] | 6.4534 [4.8446, 8.0622] |
| DNS | tape | END | 13 | off | off | tape | 0.6764 [-0.0274, 1.3803] | 0.7436 [-0.0520, 1.5392] | 1.0605 [-1.7735, 3.8944] |
| DNS | tape | INTERIOR | 253 | off | off | tape | 0.0013 [-0.0007, 0.0034] | 0.0000 [0.0000, 0.0000] | 23.1397 [7.0072, 39.2722] |
| DNS | tape | END | 13 | hybrid | hybrid | tape | 0.1269 [-0.1755, 0.4293] | 0.5385 [-0.6239, 1.7008] | 3.3654 [-3.5153, 10.2461] |
| DNS | tape | INTERIOR | 253 | hybrid | hybrid | tape | 0.0101 [-0.0028, 0.0231] | 0.0013 [-0.0044, 0.0070] | 6.0227 [4.1368, 7.9086] |
| DNS | tape | END | 13 | p_champion | aux_small | tape | 0.1680 [0.0998, 0.2363] | 0.7692 [0.2637, 1.2748] | 2.0786 [1.7291, 2.4282] |
| DNS | tape | INTERIOR | 253 | p_champion | aux_small | tape | 0.0086 [0.0028, 0.0145] | 0.0013 [-0.0044, 0.0070] | 6.7444 [1.5520, 11.9368] |
| DNS | tape | END | 13 | nll_champion | aux_small | tape | 0.1680 [0.0998, 0.2363] | 0.7692 [0.2637, 1.2748] | 2.0786 [1.7291, 2.4282] |
| DNS | tape | INTERIOR | 253 | nll_champion | aux_small | tape | 0.0086 [0.0028, 0.0145] | 0.0013 [-0.0044, 0.0070] | 6.7444 [1.5520, 11.9368] |
| DNS | sdpa | END | 13 | off | off | sdpa | 0.9042 [0.7057, 1.1028] | 1.0000 [1.0000, 1.0000] | 0.1333 [-0.1453, 0.4120] |
| DNS | sdpa | INTERIOR | 253 | off | off | sdpa | 0.0013 [-0.0013, 0.0040] | 0.0000 [0.0000, 0.0000] | 10.6415 [6.2800, 15.0031] |
| DNS | sdpa | END | 13 | hybrid | hybrid | sdpa | 0.0215 [-0.0204, 0.0635] | 0.1795 [-0.3014, 0.6604] | 4.5223 [2.1304, 6.9141] |
| DNS | sdpa | INTERIOR | 253 | hybrid | hybrid | sdpa | 0.0093 [0.0056, 0.0131] | 0.0000 [0.0000, 0.0000] | 5.7085 [4.7193, 6.6978] |
| DNS | sdpa | END | 13 | p_champion | aux_small | sdpa | 0.2827 [0.1799, 0.3855] | 0.9231 [0.7320, 1.1142] | 1.5734 [1.0977, 2.0492] |
| DNS | sdpa | INTERIOR | 253 | p_champion | aux_small | sdpa | 0.0059 [0.0023, 0.0095] | 0.0000 [0.0000, 0.0000] | 6.5272 [6.1557, 6.8987] |
| DNS | sdpa | END | 13 | nll_champion | aux_small | sdpa | 0.2827 [0.1799, 0.3855] | 0.9231 [0.7320, 1.1142] | 1.5734 [1.0977, 2.0492] |
| DNS | sdpa | INTERIOR | 253 | nll_champion | aux_small | sdpa | 0.0059 [0.0023, 0.0095] | 0.0000 [0.0000, 0.0000] | 6.5272 [6.1557, 6.8987] |
| MODBUS | rope | END | 6 | off | off | rope | 0.5288 [-0.2363, 1.2939] | 0.6667 [-0.4287, 1.7621] | 1.0431 [-1.7244, 3.8106] |
| MODBUS | rope | END | 6 | hybrid | hybrid | rope | 0.8162 [0.5873, 1.0452] | 1.0000 [1.0000, 1.0000] | 0.2463 [-0.0744, 0.5670] |
| MODBUS | rope | END | 6 | p_champion | mix_entropy | rope | 0.8081 [0.5912, 1.0250] | 1.0000 [1.0000, 1.0000] | 0.2224 [-0.0483, 0.4931] |
| MODBUS | rope | END | 6 | nll_champion | hybrid | rope | 0.8162 [0.5873, 1.0452] | 1.0000 [1.0000, 1.0000] | 0.2463 [-0.0744, 0.5670] |
| MODBUS | cope | END | 6 | off | off | cope | 0.3064 [0.0578, 0.5550] | 0.3333 [-0.0807, 0.7474] | 1.7655 [1.1044, 2.4266] |
| MODBUS | cope | END | 6 | hybrid | hybrid | cope | 0.8090 [0.5005, 1.1175] | 1.0000 [1.0000, 1.0000] | 0.2633 [-0.1947, 0.7212] |
| MODBUS | cope | END | 6 | p_champion | mix_entropy | cope | 0.7300 [0.2760, 1.1840] | 0.8333 [0.4193, 1.2474] | 0.3963 [-0.3412, 1.1338] |
| MODBUS | cope | END | 6 | nll_champion | hybrid | cope | 0.8090 [0.5005, 1.1175] | 1.0000 [1.0000, 1.0000] | 0.2633 [-0.1947, 0.7212] |
| MODBUS | tape | END | 6 | off | off | tape | 0.5225 [-0.1124, 1.1574] | 0.5000 [0.0860, 0.9140] | 1.1847 [-0.6805, 3.0499] |
| MODBUS | tape | END | 6 | hybrid | hybrid | tape | 0.8163 [0.3072, 1.3253] | 0.8889 [0.4108, 1.3670] | 0.2907 [-0.6502, 1.2316] |
| MODBUS | tape | END | 6 | p_champion | mix_entropy | tape | 0.7257 [0.4521, 0.9993] | 0.8889 [0.4108, 1.3670] | 0.3994 [-0.1852, 0.9839] |
| MODBUS | tape | END | 6 | nll_champion | hybrid | tape | 0.8163 [0.3072, 1.3253] | 0.8889 [0.4108, 1.3670] | 0.2907 [-0.6502, 1.2316] |
| MODBUS | sdpa | END | 6 | off | off | sdpa | 0.4398 [-0.0753, 0.9549] | 0.6111 [-0.2507, 1.4730] | 1.3229 [-0.7364, 3.3821] |
| MODBUS | sdpa | END | 6 | hybrid | hybrid | sdpa | 0.6448 [0.1473, 1.1422] | 0.7222 [0.0898, 1.3547] | 0.5992 [-0.5245, 1.7229] |
| MODBUS | sdpa | END | 6 | p_champion | mix_entropy | sdpa | 0.8246 [0.4571, 1.1921] | 0.8889 [0.4108, 1.3670] | 0.2196 [-0.3116, 0.7508] |
| MODBUS | sdpa | END | 6 | nll_champion | hybrid | sdpa | 0.6448 [0.1473, 1.1422] | 0.7222 [0.0898, 1.3547] | 0.5992 [-0.5245, 1.7229] |
| TLS | rope | END | 15 | off | off | rope | 0.9767 [0.9224, 1.0309] | 1.0000 [1.0000, 1.0000] | 0.0333 [-0.0546, 0.1211] |
| TLS | rope | END | 15 | hybrid | hybrid | rope | 0.8181 [0.8010, 0.8352] | 0.9556 [0.8599, 1.0512] | 0.2851 [0.1567, 0.4135] |
| TLS | rope | END | 15 | p_champion | attr_content | rope | 0.8650 [0.7619, 0.9682] | 0.8889 [0.7933, 0.9845] | 0.4126 [-0.3035, 1.1286] |
| TLS | rope | END | 15 | nll_champion | shared_slot_hybrid | rope | 0.8226 [0.2709, 1.3744] | 0.8889 [0.5441, 1.2336] | 0.3897 [-0.5996, 1.3791] |
| TLS | cope | END | 15 | off | off | cope | 0.9955 [0.9917, 0.9993] | 1.0000 [1.0000, 1.0000] | 0.0045 [0.0007, 0.0084] |
| TLS | cope | END | 15 | hybrid | hybrid | cope | 0.9992 [0.9977, 1.0006] | 1.0000 [1.0000, 1.0000] | 0.0008 [-0.0006, 0.0023] |
| TLS | cope | END | 15 | p_champion | attr_content | cope | 0.9957 [0.9838, 1.0076] | 1.0000 [1.0000, 1.0000] | 0.0046 [-0.0084, 0.0175] |
| TLS | cope | END | 15 | nll_champion | shared_slot_hybrid | cope | 0.9770 [0.9008, 1.0531] | 1.0000 [1.0000, 1.0000] | 0.0293 [-0.0724, 0.1310] |
| TLS | tape | END | 15 | off | off | tape | 0.9846 [0.9695, 0.9996] | 1.0000 [1.0000, 1.0000] | 0.0170 [-0.0005, 0.0344] |
| TLS | tape | END | 15 | hybrid | hybrid | tape | 0.8506 [0.5340, 1.1673] | 0.9556 [0.8599, 1.0512] | 0.2534 [-0.3141, 0.8208] |
| TLS | tape | END | 15 | p_champion | attr_content | tape | 0.8810 [0.5670, 1.1951] | 0.9111 [0.6581, 1.1641] | 0.3594 [-0.8298, 1.5487] |
| TLS | tape | END | 15 | nll_champion | shared_slot_hybrid | tape | 0.7431 [0.3810, 1.1053] | 0.9778 [0.8822, 1.0734] | 0.3472 [-0.2086, 0.9030] |
| TLS | sdpa | END | 15 | off | off | sdpa | 0.9989 [0.9982, 0.9997] | 1.0000 [1.0000, 1.0000] | 0.0011 [0.0003, 0.0018] |
| TLS | sdpa | END | 15 | hybrid | hybrid | sdpa | 0.9997 [0.9995, 1.0000] | 1.0000 [1.0000, 1.0000] | 0.0003 [0.0000, 0.0005] |
| TLS | sdpa | END | 15 | p_champion | attr_content | sdpa | 0.9953 [0.9789, 1.0117] | 1.0000 [1.0000, 1.0000] | 0.0051 [-0.0131, 0.0233] |
| TLS | sdpa | END | 15 | nll_champion | shared_slot_hybrid | sdpa | 0.9989 [0.9977, 1.0002] | 1.0000 [1.0000, 1.0000] | 0.0011 [-0.0002, 0.0023] |
| SMB2 | rope | END | 15 | off | off | rope | 0.1053 [-0.1147, 0.3253] | 0.2889 [-0.0559, 0.6336] | 3.3476 [-2.2275, 8.9227] |
| SMB2 | rope | INTERIOR | 27 | off | off | rope | 0.0002 [-0.0003, 0.0007] | 0.0000 [0.0000, 0.0000] | 10.1976 [7.8138, 12.5813] |
| SMB2 | rope | NULL | 18 | off | off | rope | 0.0006 [-0.0001, 0.0013] | 0.0000 [0.0000, 0.0000] | 8.1098 [6.8808, 9.3387] |
| SMB2 | rope | END | 15 | hybrid | hybrid | rope | 0.1252 [-0.1877, 0.4381] | 0.6444 [-0.7444, 2.0333] | 3.0539 [-2.2863, 8.3941] |
| SMB2 | rope | INTERIOR | 27 | hybrid | hybrid | rope | 0.0022 [0.0005, 0.0040] | 0.0000 [0.0000, 0.0000] | 6.7890 [4.7612, 8.8168] |
| SMB2 | rope | NULL | 18 | hybrid | hybrid | rope | 0.0040 [-0.0100, 0.0181] | 0.0000 [0.0000, 0.0000] | 6.7093 [1.7585, 11.6601] |
| SMB2 | rope | END | 15 | p_champion | attr_content | rope | 0.1893 [-0.3137, 0.6924] | 0.4444 [-0.7536, 1.6425] | 4.0620 [-3.0035, 11.1276] |
| SMB2 | rope | INTERIOR | 27 | p_champion | attr_content | rope | 0.0017 [0.0001, 0.0033] | 0.0000 [0.0000, 0.0000] | 9.0624 [8.4980, 9.6267] |
| SMB2 | rope | NULL | 18 | p_champion | attr_content | rope | 0.0001 [-0.0003, 0.0006] | 0.0000 [0.0000, 0.0000] | 12.9474 [7.1062, 18.7886] |
| SMB2 | rope | END | 15 | nll_champion | attr_content | rope | 0.1893 [-0.3137, 0.6924] | 0.4444 [-0.7536, 1.6425] | 4.0620 [-3.0035, 11.1276] |
| SMB2 | rope | INTERIOR | 27 | nll_champion | attr_content | rope | 0.0017 [0.0001, 0.0033] | 0.0000 [0.0000, 0.0000] | 9.0624 [8.4980, 9.6267] |
| SMB2 | rope | NULL | 18 | nll_champion | attr_content | rope | 0.0001 [-0.0003, 0.0006] | 0.0000 [0.0000, 0.0000] | 12.9474 [7.1062, 18.7886] |
| SMB2 | cope | END | 15 | off | off | cope | 0.2045 [-0.3281, 0.7372] | 0.4889 [-0.6384, 1.6162] | 2.1599 [-0.8454, 5.1652] |
| SMB2 | cope | INTERIOR | 27 | off | off | cope | 0.0006 [0.0003, 0.0008] | 0.0000 [0.0000, 0.0000] | 8.4138 [6.4218, 10.4058] |
| SMB2 | cope | NULL | 18 | off | off | cope | 0.0034 [0.0019, 0.0049] | 0.0000 [0.0000, 0.0000] | 6.5345 [6.0478, 7.0212] |
| SMB2 | cope | END | 15 | hybrid | hybrid | cope | 0.0142 [-0.0336, 0.0620] | 0.0222 [-0.0734, 0.1178] | 7.5251 [-1.8610, 16.9111] |
| SMB2 | cope | INTERIOR | 27 | hybrid | hybrid | cope | 0.0011 [0.0000, 0.0021] | 0.0000 [0.0000, 0.0000] | 7.6741 [5.2052, 10.1430] |
| SMB2 | cope | NULL | 18 | hybrid | hybrid | cope | 0.0008 [-0.0004, 0.0020] | 0.0000 [0.0000, 0.0000] | 8.1810 [4.1898, 12.1721] |
| SMB2 | cope | END | 15 | p_champion | attr_content | cope | 0.1991 [0.1115, 0.2867] | 0.5333 [-0.3430, 1.4097] | 2.0809 [0.5201, 3.6418] |
| SMB2 | cope | INTERIOR | 27 | p_champion | attr_content | cope | 0.0018 [-0.0009, 0.0045] | 0.0000 [0.0000, 0.0000] | 11.0733 [7.6642, 14.4824] |
| SMB2 | cope | NULL | 18 | p_champion | attr_content | cope | 0.0000 [-0.0000, 0.0001] | 0.0000 [0.0000, 0.0000] | 15.1891 [8.3461, 22.0321] |
| SMB2 | cope | END | 15 | nll_champion | attr_content | cope | 0.1991 [0.1115, 0.2867] | 0.5333 [-0.3430, 1.4097] | 2.0809 [0.5201, 3.6418] |
| SMB2 | cope | INTERIOR | 27 | nll_champion | attr_content | cope | 0.0018 [-0.0009, 0.0045] | 0.0000 [0.0000, 0.0000] | 11.0733 [7.6642, 14.4824] |
| SMB2 | cope | NULL | 18 | nll_champion | attr_content | cope | 0.0000 [-0.0000, 0.0001] | 0.0000 [0.0000, 0.0000] | 15.1891 [8.3461, 22.0321] |
| SMB2 | tape | END | 15 | off | off | tape | 0.1147 [-0.0180, 0.2475] | 0.3778 [-0.6740, 1.4295] | 2.8330 [1.1812, 4.4848] |
| SMB2 | tape | INTERIOR | 27 | off | off | tape | 0.0004 [-0.0002, 0.0010] | 0.0000 [0.0000, 0.0000] | 10.4717 [7.7213, 13.2221] |
| SMB2 | tape | NULL | 18 | off | off | tape | 0.0029 [-0.0056, 0.0114] | 0.0000 [0.0000, 0.0000] | 7.0167 [4.3859, 9.6474] |
| SMB2 | tape | END | 15 | hybrid | hybrid | tape | 0.2367 [-0.6681, 1.1414] | 0.3111 [-0.8869, 1.5092] | 3.0624 [-2.4264, 8.5512] |
| SMB2 | tape | INTERIOR | 27 | hybrid | hybrid | tape | 0.0015 [-0.0009, 0.0039] | 0.0000 [0.0000, 0.0000] | 7.0349 [5.0114, 9.0584] |
| SMB2 | tape | NULL | 18 | hybrid | hybrid | tape | 0.0047 [-0.0059, 0.0154] | 0.0000 [0.0000, 0.0000] | 5.9097 [3.3205, 8.4989] |
| SMB2 | tape | END | 15 | p_champion | attr_content | tape | 0.2976 [-0.2410, 0.8362] | 0.6889 [-0.5092, 1.8869] | 2.1222 [-2.3720, 6.6164] |
| SMB2 | tape | INTERIOR | 27 | p_champion | attr_content | tape | 0.0011 [-0.0006, 0.0028] | 0.0000 [0.0000, 0.0000] | 9.0185 [6.4293, 11.6077] |
| SMB2 | tape | NULL | 18 | p_champion | attr_content | tape | 0.0001 [-0.0003, 0.0004] | 0.0000 [0.0000, 0.0000] | 14.7707 [8.1331, 21.4084] |
| SMB2 | tape | END | 15 | nll_champion | attr_content | tape | 0.2976 [-0.2410, 0.8362] | 0.6889 [-0.5092, 1.8869] | 2.1222 [-2.3720, 6.6164] |
| SMB2 | tape | INTERIOR | 27 | nll_champion | attr_content | tape | 0.0011 [-0.0006, 0.0028] | 0.0000 [0.0000, 0.0000] | 9.0185 [6.4293, 11.6077] |
| SMB2 | tape | NULL | 18 | nll_champion | attr_content | tape | 0.0001 [-0.0003, 0.0004] | 0.0000 [0.0000, 0.0000] | 14.7707 [8.1331, 21.4084] |
| SMB2 | sdpa | END | 15 | off | off | sdpa | 0.1591 [-0.2632, 0.5814] | 0.5111 [-0.7319, 1.7541] | 3.3744 [-3.8313, 10.5801] |
| SMB2 | sdpa | INTERIOR | 27 | off | off | sdpa | 0.0008 [-0.0005, 0.0020] | 0.0000 [0.0000, 0.0000] | 8.7989 [6.4639, 11.1338] |
| SMB2 | sdpa | NULL | 18 | off | off | sdpa | 0.0007 [-0.0003, 0.0017] | 0.0000 [0.0000, 0.0000] | 8.0279 [6.8809, 9.1749] |
| SMB2 | sdpa | END | 15 | hybrid | hybrid | sdpa | 0.0129 [-0.0082, 0.0341] | 0.0000 [0.0000, 0.0000] | 5.4282 [3.2841, 7.5724] |
| SMB2 | sdpa | INTERIOR | 27 | hybrid | hybrid | sdpa | 0.0008 [-0.0016, 0.0033] | 0.0000 [0.0000, 0.0000] | 8.5076 [4.8535, 12.1616] |
| SMB2 | sdpa | NULL | 18 | hybrid | hybrid | sdpa | 0.0003 [-0.0001, 0.0008] | 0.0000 [0.0000, 0.0000] | 8.6734 [7.3602, 9.9867] |
| SMB2 | sdpa | END | 15 | p_champion | attr_content | sdpa | 0.2870 [-0.1907, 0.7647] | 0.5111 [-0.5536, 1.5758] | 1.7651 [-0.7150, 4.2453] |
| SMB2 | sdpa | INTERIOR | 27 | p_champion | attr_content | sdpa | 0.0014 [-0.0017, 0.0045] | 0.0000 [0.0000, 0.0000] | 12.8203 [7.8704, 17.7702] |
| SMB2 | sdpa | NULL | 18 | p_champion | attr_content | sdpa | 0.0000 [-0.0000, 0.0001] | 0.0000 [0.0000, 0.0000] | 14.3759 [4.8943, 23.8575] |
| SMB2 | sdpa | END | 15 | nll_champion | attr_content | sdpa | 0.2870 [-0.1907, 0.7647] | 0.5111 [-0.5536, 1.5758] | 1.7651 [-0.7150, 4.2453] |
| SMB2 | sdpa | INTERIOR | 27 | nll_champion | attr_content | sdpa | 0.0014 [-0.0017, 0.0045] | 0.0000 [0.0000, 0.0000] | 12.8203 [7.8704, 17.7702] |
| SMB2 | sdpa | NULL | 18 | nll_champion | attr_content | sdpa | 0.0000 [-0.0000, 0.0001] | 0.0000 [0.0000, 0.0000] | 14.3759 [4.8943, 23.8575] |

## Paired gains

Positive favors the first role. NLL gain is reference NLL minus candidate NLL; other gains are candidate minus reference.

| Target | Backbone | Cohort | Contrast | p gain [95% CI] | Hit@1 gain [95% CI] | NLL gain [95% CI] |
| --- | --- | --- | --- | --- | --- | --- |
| DNS | rope | ALL | p_champion_minus_hybrid | 0.0039 [-0.0030, 0.0108] | 0.0251 [-0.0297, 0.0798] | 0.0016 [-1.3888, 1.3920] |
| DNS | rope | LENGTH | p_champion_minus_hybrid | 0.0048 [-0.0024, 0.0120] | 0.0290 [-0.0343, 0.0923] | 0.0281 [-1.3774, 1.4337] |
| DNS | rope | POINTER | p_champion_minus_hybrid | -0.0018 [-0.0110, 0.0075] | 0.0000 [0.0000, 0.0000] | -0.1678 [-1.4614, 1.1259] |
| DNS | rope | ALL | nll_champion_minus_hybrid | 0.0039 [-0.0030, 0.0108] | 0.0251 [-0.0297, 0.0798] | 0.0016 [-1.3888, 1.3920] |
| DNS | rope | LENGTH | nll_champion_minus_hybrid | 0.0048 [-0.0024, 0.0120] | 0.0290 [-0.0343, 0.0923] | 0.0281 [-1.3774, 1.4337] |
| DNS | rope | POINTER | nll_champion_minus_hybrid | -0.0018 [-0.0110, 0.0075] | 0.0000 [0.0000, 0.0000] | -0.1678 [-1.4614, 1.1259] |
| DNS | rope | ALL | p_champion_minus_off | -0.0290 [-0.0364, -0.0216] | -0.0025 [-0.0079, 0.0029] | 7.3050 [5.2390, 9.3710] |
| DNS | rope | LENGTH | p_champion_minus_off | -0.0343 [-0.0434, -0.0253] | -0.0029 [-0.0091, 0.0033] | 7.3151 [5.4367, 9.1934] |
| DNS | rope | POINTER | p_champion_minus_off | 0.0049 [-0.0034, 0.0132] | 0.0000 [0.0000, 0.0000] | 7.2408 [3.3606, 11.1210] |
| DNS | rope | ALL | nll_champion_minus_off | -0.0290 [-0.0364, -0.0216] | -0.0025 [-0.0079, 0.0029] | 7.3050 [5.2390, 9.3710] |
| DNS | rope | LENGTH | nll_champion_minus_off | -0.0343 [-0.0434, -0.0253] | -0.0029 [-0.0091, 0.0033] | 7.3151 [5.4367, 9.1934] |
| DNS | rope | POINTER | nll_champion_minus_off | 0.0049 [-0.0034, 0.0132] | 0.0000 [0.0000, 0.0000] | 7.2408 [3.3606, 11.1210] |
| DNS | rope | ALL | hybrid_minus_off | -0.0329 [-0.0368, -0.0291] | -0.0276 [-0.0876, 0.0325] | 7.3034 [4.0619, 10.5449] |
| DNS | rope | LENGTH | hybrid_minus_off | -0.0392 [-0.0440, -0.0343] | -0.0319 [-0.1013, 0.0376] | 7.2869 [4.1308, 10.4431] |
| DNS | rope | POINTER | hybrid_minus_off | 0.0067 [-0.0053, 0.0187] | 0.0000 [0.0000, 0.0000] | 7.4085 [2.9359, 11.8812] |
| DNS | cope | ALL | p_champion_minus_hybrid | 0.0057 [-0.0191, 0.0305] | 0.0000 [-0.0891, 0.0891] | -0.1832 [-2.7544, 2.3880] |
| DNS | cope | LENGTH | p_champion_minus_hybrid | 0.0065 [-0.0239, 0.0369] | 0.0000 [-0.1138, 0.1138] | -0.2312 [-2.9750, 2.5126] |
| DNS | cope | POINTER | p_champion_minus_hybrid | 0.0006 [-0.0120, 0.0131] | 0.0000 [-0.0690, 0.0690] | 0.1234 [-1.3596, 1.6063] |
| DNS | cope | ALL | nll_champion_minus_hybrid | 0.0057 [-0.0191, 0.0305] | 0.0000 [-0.0891, 0.0891] | -0.1832 [-2.7544, 2.3880] |
| DNS | cope | LENGTH | nll_champion_minus_hybrid | 0.0065 [-0.0239, 0.0369] | 0.0000 [-0.1138, 0.1138] | -0.2312 [-2.9750, 2.5126] |
| DNS | cope | POINTER | nll_champion_minus_hybrid | 0.0006 [-0.0120, 0.0131] | 0.0000 [-0.0690, 0.0690] | 0.1234 [-1.3596, 1.6063] |
| DNS | cope | ALL | p_champion_minus_off | -0.0152 [-0.0225, -0.0080] | -0.0063 [-0.0416, 0.0291] | 3.4249 [0.6657, 6.1840] |
| DNS | cope | LENGTH | p_champion_minus_off | -0.0187 [-0.0269, -0.0104] | -0.0087 [-0.0558, 0.0384] | 3.3873 [0.7496, 6.0249] |
| DNS | cope | POINTER | p_champion_minus_off | 0.0067 [0.0045, 0.0090] | 0.0093 [-0.0306, 0.0491] | 3.6650 [-0.0084, 7.3384] |
| DNS | cope | ALL | nll_champion_minus_off | -0.0152 [-0.0225, -0.0080] | -0.0063 [-0.0416, 0.0291] | 3.4249 [0.6657, 6.1840] |
| DNS | cope | LENGTH | nll_champion_minus_off | -0.0187 [-0.0269, -0.0104] | -0.0087 [-0.0558, 0.0384] | 3.3873 [0.7496, 6.0249] |
| DNS | cope | POINTER | nll_champion_minus_off | 0.0067 [0.0045, 0.0090] | 0.0093 [-0.0306, 0.0491] | 3.6650 [-0.0084, 7.3384] |
| DNS | cope | ALL | hybrid_minus_off | -0.0209 [-0.0506, 0.0088] | -0.0063 [-0.0738, 0.0613] | 3.6081 [1.3649, 5.8513] |
| DNS | cope | LENGTH | hybrid_minus_off | -0.0252 [-0.0611, 0.0108] | -0.0087 [-0.0931, 0.0757] | 3.6185 [1.2549, 5.9820] |
| DNS | cope | POINTER | hybrid_minus_off | 0.0062 [-0.0048, 0.0171] | 0.0093 [-0.0306, 0.0491] | 3.5416 [0.7628, 6.3205] |
| DNS | tape | ALL | p_champion_minus_hybrid | 0.0006 [-0.0066, 0.0078] | 0.0113 [-0.0701, 0.0927] | -0.6236 [-4.1750, 2.9279] |
| DNS | tape | LENGTH | p_champion_minus_hybrid | 0.0004 [-0.0070, 0.0078] | 0.0130 [-0.0811, 0.1072] | -0.6872 [-4.3899, 3.0156] |
| DNS | tape | POINTER | p_champion_minus_hybrid | 0.0019 [-0.0039, 0.0078] | 0.0000 [0.0000, 0.0000] | -0.2172 [-2.8802, 2.4457] |
| DNS | tape | ALL | nll_champion_minus_hybrid | 0.0006 [-0.0066, 0.0078] | 0.0113 [-0.0701, 0.0927] | -0.6236 [-4.1750, 2.9279] |
| DNS | tape | LENGTH | nll_champion_minus_hybrid | 0.0004 [-0.0070, 0.0078] | 0.0130 [-0.0811, 0.1072] | -0.6872 [-4.3899, 3.0156] |
| DNS | tape | POINTER | nll_champion_minus_hybrid | 0.0019 [-0.0039, 0.0078] | 0.0000 [0.0000, 0.0000] | -0.2172 [-2.8802, 2.4457] |
| DNS | tape | ALL | p_champion_minus_off | -0.0179 [-0.0539, 0.0181] | 0.0025 [-0.0663, 0.0713] | 15.5442 [3.7518, 27.3367] |
| DNS | tape | LENGTH | p_champion_minus_off | -0.0218 [-0.0615, 0.0179] | 0.0029 [-0.0767, 0.0825] | 15.9288 [4.4180, 27.4397] |
| DNS | tape | POINTER | p_champion_minus_off | 0.0069 [-0.0060, 0.0198] | 0.0000 [0.0000, 0.0000] | 13.0871 [-0.5561, 26.7302] |
| DNS | tape | ALL | nll_champion_minus_off | -0.0179 [-0.0539, 0.0181] | 0.0025 [-0.0663, 0.0713] | 15.5442 [3.7518, 27.3367] |
| DNS | tape | LENGTH | nll_champion_minus_off | -0.0218 [-0.0615, 0.0179] | 0.0029 [-0.0767, 0.0825] | 15.9288 [4.4180, 27.4397] |
| DNS | tape | POINTER | nll_champion_minus_off | 0.0069 [-0.0060, 0.0198] | 0.0000 [0.0000, 0.0000] | 13.0871 [-0.5561, 26.7302] |
| DNS | tape | ALL | hybrid_minus_off | -0.0185 [-0.0494, 0.0124] | -0.0088 [-0.0230, 0.0055] | 16.1678 [1.6217, 30.7139] |
| DNS | tape | LENGTH | hybrid_minus_off | -0.0222 [-0.0569, 0.0125] | -0.0101 [-0.0266, 0.0064] | 16.6160 [2.1998, 31.0322] |
| DNS | tape | POINTER | hybrid_minus_off | 0.0050 [-0.0023, 0.0122] | 0.0000 [0.0000, 0.0000] | 13.3043 [-2.0915, 28.7001] |
| DNS | sdpa | ALL | p_champion_minus_hybrid | 0.0095 [0.0010, 0.0180] | 0.0363 [0.0169, 0.0558] | -0.6346 [-1.7816, 0.5125] |
| DNS | sdpa | LENGTH | p_champion_minus_hybrid | 0.0112 [0.0016, 0.0209] | 0.0420 [0.0195, 0.0645] | -0.6362 [-1.6660, 0.3936] |
| DNS | sdpa | POINTER | p_champion_minus_hybrid | -0.0017 [-0.0061, 0.0027] | 0.0000 [0.0000, 0.0000] | -0.6242 [-2.8187, 1.5702] |
| DNS | sdpa | ALL | nll_champion_minus_hybrid | 0.0095 [0.0010, 0.0180] | 0.0363 [0.0169, 0.0558] | -0.6346 [-1.7816, 0.5125] |
| DNS | sdpa | LENGTH | nll_champion_minus_hybrid | 0.0112 [0.0016, 0.0209] | 0.0420 [0.0195, 0.0645] | -0.6362 [-1.6660, 0.3936] |
| DNS | sdpa | POINTER | nll_champion_minus_hybrid | -0.0017 [-0.0061, 0.0027] | 0.0000 [0.0000, 0.0000] | -0.6242 [-2.8187, 1.5702] |
| DNS | sdpa | ALL | p_champion_minus_off | -0.0260 [-0.0376, -0.0145] | -0.0038 [-0.0131, 0.0056] | 3.8428 [-0.3822, 8.0678] |
| DNS | sdpa | LENGTH | p_champion_minus_off | -0.0308 [-0.0447, -0.0169] | -0.0043 [-0.0151, 0.0065] | 3.7393 [-0.1657, 7.6443] |
| DNS | sdpa | POINTER | p_champion_minus_off | 0.0045 [-0.0026, 0.0117] | 0.0000 [0.0000, 0.0000] | 4.5043 [-2.7529, 11.7615] |
| DNS | sdpa | ALL | nll_champion_minus_off | -0.0260 [-0.0376, -0.0145] | -0.0038 [-0.0131, 0.0056] | 3.8428 [-0.3822, 8.0678] |
| DNS | sdpa | LENGTH | nll_champion_minus_off | -0.0308 [-0.0447, -0.0169] | -0.0043 [-0.0151, 0.0065] | 3.7393 [-0.1657, 7.6443] |
| DNS | sdpa | POINTER | nll_champion_minus_off | 0.0045 [-0.0026, 0.0117] | 0.0000 [0.0000, 0.0000] | 4.5043 [-2.7529, 11.7615] |
| DNS | sdpa | ALL | hybrid_minus_off | -0.0355 [-0.0411, -0.0299] | -0.0401 [-0.0636, -0.0166] | 4.4774 [-0.2065, 9.1613] |
| DNS | sdpa | LENGTH | hybrid_minus_off | -0.0420 [-0.0490, -0.0351] | -0.0464 [-0.0736, -0.0192] | 4.3755 [-0.1682, 8.9191] |
| DNS | sdpa | POINTER | hybrid_minus_off | 0.0062 [0.0030, 0.0094] | 0.0000 [0.0000, 0.0000] | 5.1285 [-1.0853, 11.3424] |
| MODBUS | rope | ALL | p_champion_minus_hybrid | -0.0081 [-0.0231, 0.0069] | 0.0000 [0.0000, 0.0000] | 0.0238 [-0.0280, 0.0757] |
| MODBUS | rope | LENGTH | p_champion_minus_hybrid | -0.0081 [-0.0231, 0.0069] | 0.0000 [0.0000, 0.0000] | 0.0238 [-0.0280, 0.0757] |
| MODBUS | rope | ALL | nll_champion_minus_hybrid | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| MODBUS | rope | LENGTH | nll_champion_minus_hybrid | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| MODBUS | rope | ALL | p_champion_minus_off | 0.2793 [-0.2704, 0.8290] | 0.3333 [-0.7621, 1.4287] | 0.8207 [-1.6761, 3.3175] |
| MODBUS | rope | LENGTH | p_champion_minus_off | 0.2793 [-0.2704, 0.8290] | 0.3333 [-0.7621, 1.4287] | 0.8207 [-1.6761, 3.3175] |
| MODBUS | rope | ALL | nll_champion_minus_off | 0.2874 [-0.2493, 0.8242] | 0.3333 [-0.7621, 1.4287] | 0.7968 [-1.6500, 3.2437] |
| MODBUS | rope | LENGTH | nll_champion_minus_off | 0.2874 [-0.2493, 0.8242] | 0.3333 [-0.7621, 1.4287] | 0.7968 [-1.6500, 3.2437] |
| MODBUS | rope | ALL | hybrid_minus_off | 0.2874 [-0.2493, 0.8242] | 0.3333 [-0.7621, 1.4287] | 0.7968 [-1.6500, 3.2437] |
| MODBUS | rope | LENGTH | hybrid_minus_off | 0.2874 [-0.2493, 0.8242] | 0.3333 [-0.7621, 1.4287] | 0.7968 [-1.6500, 3.2437] |
| MODBUS | cope | ALL | p_champion_minus_hybrid | -0.0790 [-0.2388, 0.0808] | -0.1667 [-0.5807, 0.2474] | -0.1330 [-0.4439, 0.1779] |
| MODBUS | cope | LENGTH | p_champion_minus_hybrid | -0.0790 [-0.2388, 0.0808] | -0.1667 [-0.5807, 0.2474] | -0.1330 [-0.4439, 0.1779] |
| MODBUS | cope | ALL | nll_champion_minus_hybrid | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| MODBUS | cope | LENGTH | nll_champion_minus_hybrid | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| MODBUS | cope | ALL | p_champion_minus_off | 0.4236 [-0.1849, 1.0320] | 0.5000 [-0.2171, 1.2171] | 1.3692 [-0.0286, 2.7671] |
| MODBUS | cope | LENGTH | p_champion_minus_off | 0.4236 [-0.1849, 1.0320] | 0.5000 [-0.2171, 1.2171] | 1.3692 [-0.0286, 2.7671] |
| MODBUS | cope | ALL | nll_champion_minus_off | 0.5026 [0.0538, 0.9514] | 0.6667 [0.2526, 1.0807] | 1.5023 [0.3871, 2.6174] |
| MODBUS | cope | LENGTH | nll_champion_minus_off | 0.5026 [0.0538, 0.9514] | 0.6667 [0.2526, 1.0807] | 1.5023 [0.3871, 2.6174] |
| MODBUS | cope | ALL | hybrid_minus_off | 0.5026 [0.0538, 0.9514] | 0.6667 [0.2526, 1.0807] | 1.5023 [0.3871, 2.6174] |
| MODBUS | cope | LENGTH | hybrid_minus_off | 0.5026 [0.0538, 0.9514] | 0.6667 [0.2526, 1.0807] | 1.5023 [0.3871, 2.6174] |
| MODBUS | tape | ALL | p_champion_minus_hybrid | -0.0906 [-0.3279, 0.1468] | 0.0000 [0.0000, 0.0000] | -0.1086 [-0.4675, 0.2503] |
| MODBUS | tape | LENGTH | p_champion_minus_hybrid | -0.0906 [-0.3279, 0.1468] | 0.0000 [0.0000, 0.0000] | -0.1086 [-0.4675, 0.2503] |
| MODBUS | tape | ALL | nll_champion_minus_hybrid | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| MODBUS | tape | LENGTH | nll_champion_minus_hybrid | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| MODBUS | tape | ALL | p_champion_minus_off | 0.2032 [-0.7021, 1.1085] | 0.3889 [-0.4730, 1.2507] | 0.7853 [-1.6640, 3.2347] |
| MODBUS | tape | LENGTH | p_champion_minus_off | 0.2032 [-0.7021, 1.1085] | 0.3889 [-0.4730, 1.2507] | 0.7853 [-1.6640, 3.2347] |
| MODBUS | tape | ALL | nll_champion_minus_off | 0.2938 [-0.8404, 1.4280] | 0.3889 [-0.4730, 1.2507] | 0.8940 [-1.9120, 3.7000] |
| MODBUS | tape | LENGTH | nll_champion_minus_off | 0.2938 [-0.8404, 1.4280] | 0.3889 [-0.4730, 1.2507] | 0.8940 [-1.9120, 3.7000] |
| MODBUS | tape | ALL | hybrid_minus_off | 0.2938 [-0.8404, 1.4280] | 0.3889 [-0.4730, 1.2507] | 0.8940 [-1.9120, 3.7000] |
| MODBUS | tape | LENGTH | hybrid_minus_off | 0.2938 [-0.8404, 1.4280] | 0.3889 [-0.4730, 1.2507] | 0.8940 [-1.9120, 3.7000] |
| MODBUS | sdpa | ALL | p_champion_minus_hybrid | 0.1798 [0.0027, 0.3569] | 0.1667 [-0.2474, 0.5807] | 0.3796 [-0.2445, 1.0037] |
| MODBUS | sdpa | LENGTH | p_champion_minus_hybrid | 0.1798 [0.0027, 0.3569] | 0.1667 [-0.2474, 0.5807] | 0.3796 [-0.2445, 1.0037] |
| MODBUS | sdpa | ALL | nll_champion_minus_hybrid | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| MODBUS | sdpa | LENGTH | nll_champion_minus_hybrid | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] | 0.0000 [0.0000, 0.0000] |
| MODBUS | sdpa | ALL | p_champion_minus_off | 0.3848 [0.1574, 0.6122] | 0.2778 [-0.3547, 0.9102] | 1.1033 [-0.5046, 2.7111] |
| MODBUS | sdpa | LENGTH | p_champion_minus_off | 0.3848 [0.1574, 0.6122] | 0.2778 [-0.3547, 0.9102] | 1.1033 [-0.5046, 2.7111] |
| MODBUS | sdpa | ALL | nll_champion_minus_off | 0.2050 [-0.1344, 0.5443] | 0.1111 [-0.9308, 1.1530] | 0.7237 [-0.7179, 2.1653] |
| MODBUS | sdpa | LENGTH | nll_champion_minus_off | 0.2050 [-0.1344, 0.5443] | 0.1111 [-0.9308, 1.1530] | 0.7237 [-0.7179, 2.1653] |
| MODBUS | sdpa | ALL | hybrid_minus_off | 0.2050 [-0.1344, 0.5443] | 0.1111 [-0.9308, 1.1530] | 0.7237 [-0.7179, 2.1653] |
| MODBUS | sdpa | LENGTH | hybrid_minus_off | 0.2050 [-0.1344, 0.5443] | 0.1111 [-0.9308, 1.1530] | 0.7237 [-0.7179, 2.1653] |
| TLS | rope | ALL | p_champion_minus_hybrid | 0.0469 [-0.0526, 0.1465] | -0.0667 [-0.2323, 0.0989] | -0.1275 [-0.7266, 0.4716] |
| TLS | rope | LENGTH | p_champion_minus_hybrid | 0.0469 [-0.0526, 0.1465] | -0.0667 [-0.2323, 0.0989] | -0.1275 [-0.7266, 0.4716] |
| TLS | rope | ALL | nll_champion_minus_hybrid | 0.0046 [-0.5301, 0.5392] | -0.0667 [-0.3535, 0.2202] | -0.1047 [-0.9788, 0.7694] |
| TLS | rope | LENGTH | nll_champion_minus_hybrid | 0.0046 [-0.5301, 0.5392] | -0.0667 [-0.3535, 0.2202] | -0.1047 [-0.9788, 0.7694] |
| TLS | rope | ALL | p_champion_minus_off | -0.1117 [-0.1863, -0.0370] | -0.1111 [-0.2067, -0.0155] | -0.3793 [-1.0076, 0.2490] |
| TLS | rope | LENGTH | p_champion_minus_off | -0.1117 [-0.1863, -0.0370] | -0.1111 [-0.2067, -0.0155] | -0.3793 [-1.0076, 0.2490] |
| TLS | rope | ALL | nll_champion_minus_off | -0.1540 [-0.6577, 0.3497] | -0.1111 [-0.4559, 0.2336] | -0.3565 [-1.2579, 0.5450] |
| TLS | rope | LENGTH | nll_champion_minus_off | -0.1540 [-0.6577, 0.3497] | -0.1111 [-0.4559, 0.2336] | -0.3565 [-1.2579, 0.5450] |
| TLS | rope | ALL | hybrid_minus_off | -0.1586 [-0.1987, -0.1185] | -0.0444 [-0.1401, 0.0512] | -0.2518 [-0.3126, -0.1910] |
| TLS | rope | LENGTH | hybrid_minus_off | -0.1586 [-0.1987, -0.1185] | -0.0444 [-0.1401, 0.0512] | -0.2518 [-0.3126, -0.1910] |
| TLS | cope | ALL | p_champion_minus_hybrid | -0.0035 [-0.0157, 0.0088] | 0.0000 [0.0000, 0.0000] | -0.0037 [-0.0170, 0.0096] |
| TLS | cope | LENGTH | p_champion_minus_hybrid | -0.0035 [-0.0157, 0.0088] | 0.0000 [0.0000, 0.0000] | -0.0037 [-0.0170, 0.0096] |
| TLS | cope | ALL | nll_champion_minus_hybrid | -0.0222 [-0.0992, 0.0549] | 0.0000 [0.0000, 0.0000] | -0.0285 [-0.1310, 0.0741] |
| TLS | cope | LENGTH | nll_champion_minus_hybrid | -0.0222 [-0.0992, 0.0549] | 0.0000 [0.0000, 0.0000] | -0.0285 [-0.1310, 0.0741] |
| TLS | cope | ALL | p_champion_minus_off | 0.0002 [-0.0127, 0.0132] | 0.0000 [0.0000, 0.0000] | -0.0000 [-0.0140, 0.0140] |
| TLS | cope | LENGTH | p_champion_minus_off | 0.0002 [-0.0127, 0.0132] | 0.0000 [0.0000, 0.0000] | -0.0000 [-0.0140, 0.0140] |
| TLS | cope | ALL | nll_champion_minus_off | -0.0185 [-0.0968, 0.0598] | 0.0000 [0.0000, 0.0000] | -0.0248 [-0.1285, 0.0790] |
| TLS | cope | LENGTH | nll_champion_minus_off | -0.0185 [-0.0968, 0.0598] | 0.0000 [0.0000, 0.0000] | -0.0248 [-0.1285, 0.0790] |
| TLS | cope | ALL | hybrid_minus_off | 0.0037 [0.0013, 0.0060] | 0.0000 [0.0000, 0.0000] | 0.0037 [0.0013, 0.0061] |
| TLS | cope | LENGTH | hybrid_minus_off | 0.0037 [0.0013, 0.0060] | 0.0000 [0.0000, 0.0000] | 0.0037 [0.0013, 0.0061] |
| TLS | tape | ALL | p_champion_minus_hybrid | 0.0304 [-0.3102, 0.3710] | -0.0444 [-0.2357, 0.1468] | -0.1061 [-1.2981, 1.0859] |
| TLS | tape | LENGTH | p_champion_minus_hybrid | 0.0304 [-0.3102, 0.3710] | -0.0444 [-0.2357, 0.1468] | -0.1061 [-1.2981, 1.0859] |
| TLS | tape | ALL | nll_champion_minus_hybrid | -0.1075 [-0.7862, 0.5712] | 0.0222 [-0.1690, 0.2135] | -0.0938 [-1.2150, 1.0273] |
| TLS | tape | LENGTH | nll_champion_minus_hybrid | -0.1075 [-0.7862, 0.5712] | 0.0222 [-0.1690, 0.2135] | -0.0938 [-1.2150, 1.0273] |
| TLS | tape | ALL | p_champion_minus_off | -0.1035 [-0.4175, 0.2105] | -0.0889 [-0.3419, 0.1641] | -0.3424 [-1.5267, 0.8418] |
| TLS | tape | LENGTH | p_champion_minus_off | -0.1035 [-0.4175, 0.2105] | -0.0889 [-0.3419, 0.1641] | -0.3424 [-1.5267, 0.8418] |
| TLS | tape | ALL | nll_champion_minus_off | -0.2414 [-0.5903, 0.1075] | -0.0222 [-0.1178, 0.0734] | -0.3302 [-0.8723, 0.2118] |
| TLS | tape | LENGTH | nll_champion_minus_off | -0.2414 [-0.5903, 0.1075] | -0.0222 [-0.1178, 0.0734] | -0.3302 [-0.8723, 0.2118] |
| TLS | tape | ALL | hybrid_minus_off | -0.1339 [-0.4641, 0.1963] | -0.0444 [-0.1401, 0.0512] | -0.2364 [-0.8190, 0.3462] |
| TLS | tape | LENGTH | hybrid_minus_off | -0.1339 [-0.4641, 0.1963] | -0.0444 [-0.1401, 0.0512] | -0.2364 [-0.8190, 0.3462] |
| TLS | sdpa | ALL | p_champion_minus_hybrid | -0.0044 [-0.0208, 0.0119] | 0.0000 [0.0000, 0.0000] | -0.0048 [-0.0230, 0.0133] |
| TLS | sdpa | LENGTH | p_champion_minus_hybrid | -0.0044 [-0.0208, 0.0119] | 0.0000 [0.0000, 0.0000] | -0.0048 [-0.0230, 0.0133] |
| TLS | sdpa | ALL | nll_champion_minus_hybrid | -0.0008 [-0.0021, 0.0004] | 0.0000 [0.0000, 0.0000] | -0.0008 [-0.0021, 0.0004] |
| TLS | sdpa | LENGTH | nll_champion_minus_hybrid | -0.0008 [-0.0021, 0.0004] | 0.0000 [0.0000, 0.0000] | -0.0008 [-0.0021, 0.0004] |
| TLS | sdpa | ALL | p_champion_minus_off | -0.0036 [-0.0207, 0.0135] | 0.0000 [0.0000, 0.0000] | -0.0040 [-0.0229, 0.0149] |
| TLS | sdpa | LENGTH | p_champion_minus_off | -0.0036 [-0.0207, 0.0135] | 0.0000 [0.0000, 0.0000] | -0.0040 [-0.0229, 0.0149] |
| TLS | sdpa | ALL | nll_champion_minus_off | 0.0000 [-0.0005, 0.0005] | 0.0000 [0.0000, 0.0000] | 0.0000 [-0.0005, 0.0005] |
| TLS | sdpa | LENGTH | nll_champion_minus_off | 0.0000 [-0.0005, 0.0005] | 0.0000 [0.0000, 0.0000] | 0.0000 [-0.0005, 0.0005] |
| TLS | sdpa | ALL | hybrid_minus_off | 0.0008 [0.0001, 0.0016] | 0.0000 [0.0000, 0.0000] | 0.0008 [0.0001, 0.0016] |
| TLS | sdpa | LENGTH | hybrid_minus_off | 0.0008 [0.0001, 0.0016] | 0.0000 [0.0000, 0.0000] | 0.0008 [0.0001, 0.0016] |
| SMB2 | rope | ALL | p_champion_minus_hybrid | 0.0146 [-0.1199, 0.1492] | -0.0500 [-0.3734, 0.2734] | -3.1465 [-4.0705, -2.2225] |
| SMB2 | rope | LENGTH | p_champion_minus_hybrid | 0.0304 [-0.2415, 0.3024] | -0.1000 [-0.7467, 0.5467] | -1.8382 [-5.6201, 1.9437] |
| SMB2 | rope | OFFSET | p_champion_minus_hybrid | -0.0012 [-0.0041, 0.0016] | 0.0000 [0.0000, 0.0000] | -4.4548 [-6.5357, -2.3739] |
| SMB2 | rope | ALL | nll_champion_minus_hybrid | 0.0146 [-0.1199, 0.1492] | -0.0500 [-0.3734, 0.2734] | -3.1465 [-4.0705, -2.2225] |
| SMB2 | rope | LENGTH | nll_champion_minus_hybrid | 0.0304 [-0.2415, 0.3024] | -0.1000 [-0.7467, 0.5467] | -1.8382 [-5.6201, 1.9437] |
| SMB2 | rope | OFFSET | nll_champion_minus_hybrid | -0.0012 [-0.0041, 0.0016] | 0.0000 [0.0000, 0.0000] | -4.4548 [-6.5357, -2.3739] |
| SMB2 | rope | ALL | p_champion_minus_off | 0.0215 [-0.1035, 0.1466] | 0.0389 [-0.2429, 0.3207] | -1.1191 [-4.8869, 2.6488] |
| SMB2 | rope | LENGTH | p_champion_minus_off | 0.0422 [-0.2071, 0.2915] | 0.0778 [-0.4859, 0.6414] | -1.0152 [-8.0754, 6.0450] |
| SMB2 | rope | OFFSET | p_champion_minus_off | 0.0009 [-0.0004, 0.0022] | 0.0000 [0.0000, 0.0000] | -1.2229 [-2.6723, 0.2266] |
| SMB2 | rope | ALL | nll_champion_minus_off | 0.0215 [-0.1035, 0.1466] | 0.0389 [-0.2429, 0.3207] | -1.1191 [-4.8869, 2.6488] |
| SMB2 | rope | LENGTH | nll_champion_minus_off | 0.0422 [-0.2071, 0.2915] | 0.0778 [-0.4859, 0.6414] | -1.0152 [-8.0754, 6.0450] |
| SMB2 | rope | OFFSET | nll_champion_minus_off | 0.0009 [-0.0004, 0.0022] | 0.0000 [0.0000, 0.0000] | -1.2229 [-2.6723, 0.2266] |
| SMB2 | rope | ALL | hybrid_minus_off | 0.0069 [-0.0154, 0.0292] | 0.0889 [-0.1741, 0.3518] | 2.0274 [-0.8185, 4.8733] |
| SMB2 | rope | LENGTH | hybrid_minus_off | 0.0117 [-0.0334, 0.0569] | 0.1778 [-0.3481, 0.7037] | 0.8230 [-2.5604, 4.2064] |
| SMB2 | rope | OFFSET | hybrid_minus_off | 0.0021 [-0.0017, 0.0059] | 0.0000 [0.0000, 0.0000] | 3.2319 [0.9208, 5.5430] |
| SMB2 | cope | ALL | p_champion_minus_hybrid | 0.0463 [0.0290, 0.0637] | 0.1278 [-0.0765, 0.3320] | -2.2711 [-3.4928, -1.0494] |
| SMB2 | cope | LENGTH | p_champion_minus_hybrid | 0.0933 [0.0573, 0.1293] | 0.2556 [-0.1529, 0.6640] | 1.4298 [-2.9357, 5.7954] |
| SMB2 | cope | OFFSET | p_champion_minus_hybrid | -0.0007 [-0.0021, 0.0007] | 0.0000 [0.0000, 0.0000] | -5.9720 [-7.8942, -4.0498] |
| SMB2 | cope | ALL | nll_champion_minus_hybrid | 0.0463 [0.0290, 0.0637] | 0.1278 [-0.0765, 0.3320] | -2.2711 [-3.4928, -1.0494] |
| SMB2 | cope | LENGTH | nll_champion_minus_hybrid | 0.0933 [0.0573, 0.1293] | 0.2556 [-0.1529, 0.6640] | 1.4298 [-2.9357, 5.7954] |
| SMB2 | cope | OFFSET | nll_champion_minus_hybrid | -0.0007 [-0.0021, 0.0007] | 0.0000 [0.0000, 0.0000] | -5.9720 [-7.8942, -4.0498] |
| SMB2 | cope | ALL | p_champion_minus_off | -0.0018 [-0.1575, 0.1539] | 0.0111 [-0.4794, 0.5016] | -3.7734 [-9.1997, 1.6528] |
| SMB2 | cope | LENGTH | p_champion_minus_off | -0.0033 [-0.3144, 0.3077] | 0.0222 [-0.9587, 1.0031] | -2.2616 [-6.4151, 1.8919] |
| SMB2 | cope | OFFSET | p_champion_minus_off | -0.0003 [-0.0007, 0.0002] | 0.0000 [0.0000, 0.0000] | -5.2852 [-12.1421, 1.5716] |
| SMB2 | cope | ALL | nll_champion_minus_off | -0.0018 [-0.1575, 0.1539] | 0.0111 [-0.4794, 0.5016] | -3.7734 [-9.1997, 1.6528] |
| SMB2 | cope | LENGTH | nll_champion_minus_off | -0.0033 [-0.3144, 0.3077] | 0.0222 [-0.9587, 1.0031] | -2.2616 [-6.4151, 1.8919] |
| SMB2 | cope | OFFSET | nll_champion_minus_off | -0.0003 [-0.0007, 0.0002] | 0.0000 [0.0000, 0.0000] | -5.2852 [-12.1421, 1.5716] |
| SMB2 | cope | ALL | hybrid_minus_off | -0.0481 [-0.1885, 0.0922] | -0.1167 [-0.4065, 0.1731] | -1.5024 [-7.8740, 4.8693] |
| SMB2 | cope | LENGTH | hybrid_minus_off | -0.0966 [-0.3761, 0.1828] | -0.2333 [-0.8130, 0.3463] | -3.6914 [-11.2159, 3.8330] |
| SMB2 | cope | OFFSET | hybrid_minus_off | 0.0004 [-0.0013, 0.0021] | 0.0000 [0.0000, 0.0000] | 0.6867 [-4.7383, 6.1117] |
| SMB2 | tape | ALL | p_champion_minus_hybrid | 0.0137 [-0.1910, 0.2184] | 0.0944 [-0.1685, 0.3574] | -3.3159 [-5.1356, -1.4962] |
| SMB2 | tape | LENGTH | p_champion_minus_hybrid | 0.0296 [-0.3780, 0.4371] | 0.1889 [-0.3370, 0.7148] | -2.0367 [-5.1489, 1.0755] |
| SMB2 | tape | OFFSET | p_champion_minus_hybrid | -0.0022 [-0.0091, 0.0046] | 0.0000 [0.0000, 0.0000] | -4.5951 [-6.1207, -3.0695] |
| SMB2 | tape | ALL | nll_champion_minus_hybrid | 0.0137 [-0.1910, 0.2184] | 0.0944 [-0.1685, 0.3574] | -3.3159 [-5.1356, -1.4962] |
| SMB2 | tape | LENGTH | nll_champion_minus_hybrid | 0.0296 [-0.3780, 0.4371] | 0.1889 [-0.3370, 0.7148] | -2.0367 [-5.1489, 1.0755] |
| SMB2 | tape | OFFSET | nll_champion_minus_hybrid | -0.0022 [-0.0091, 0.0046] | 0.0000 [0.0000, 0.0000] | -4.5951 [-6.1207, -3.0695] |
| SMB2 | tape | ALL | p_champion_minus_off | 0.0452 [-0.0752, 0.1656] | 0.0778 [-0.1884, 0.3440] | -1.4946 [-5.0828, 2.0936] |
| SMB2 | tape | LENGTH | p_champion_minus_off | 0.0905 [-0.1504, 0.3314] | 0.1556 [-0.3768, 0.6879] | -1.4498 [-7.2538, 4.3542] |
| SMB2 | tape | OFFSET | p_champion_minus_off | -0.0001 [-0.0003, 0.0002] | 0.0000 [0.0000, 0.0000] | -1.5393 [-2.9205, -0.1582] |
| SMB2 | tape | ALL | nll_champion_minus_off | 0.0452 [-0.0752, 0.1656] | 0.0778 [-0.1884, 0.3440] | -1.4946 [-5.0828, 2.0936] |
| SMB2 | tape | LENGTH | nll_champion_minus_off | 0.0905 [-0.1504, 0.3314] | 0.1556 [-0.3768, 0.6879] | -1.4498 [-7.2538, 4.3542] |
| SMB2 | tape | OFFSET | nll_champion_minus_off | -0.0001 [-0.0003, 0.0002] | 0.0000 [0.0000, 0.0000] | -1.5393 [-2.9205, -0.1582] |
| SMB2 | tape | ALL | hybrid_minus_off | 0.0315 [-0.1603, 0.2234] | -0.0167 [-0.0581, 0.0247] | 1.8213 [-0.3703, 4.0129] |
| SMB2 | tape | LENGTH | hybrid_minus_off | 0.0609 [-0.3249, 0.4467] | -0.0333 [-0.1161, 0.0495] | 0.5869 [-2.1168, 3.2905] |
| SMB2 | tape | OFFSET | hybrid_minus_off | 0.0022 [-0.0047, 0.0090] | 0.0000 [0.0000, 0.0000] | 3.0557 [0.9426, 5.1689] |
| SMB2 | sdpa | ALL | p_champion_minus_hybrid | 0.0687 [-0.0511, 0.1885] | 0.1278 [-0.1384, 0.3940] | -2.7357 [-9.3297, 3.8583] |
| SMB2 | sdpa | LENGTH | p_champion_minus_hybrid | 0.1378 [-0.1001, 0.3756] | 0.2556 [-0.2768, 0.7879] | 0.4626 [-5.4879, 6.4132] |
| SMB2 | sdpa | OFFSET | p_champion_minus_hybrid | -0.0004 [-0.0031, 0.0022] | 0.0000 [0.0000, 0.0000] | -5.9340 [-13.1970, 1.3290] |
| SMB2 | sdpa | ALL | nll_champion_minus_hybrid | 0.0687 [-0.0511, 0.1885] | 0.1278 [-0.1384, 0.3940] | -2.7357 [-9.3297, 3.8583] |
| SMB2 | sdpa | LENGTH | nll_champion_minus_hybrid | 0.1378 [-0.1001, 0.3756] | 0.2556 [-0.2768, 0.7879] | 0.4626 [-5.4879, 6.4132] |
| SMB2 | sdpa | OFFSET | nll_champion_minus_hybrid | -0.0004 [-0.0031, 0.0022] | 0.0000 [0.0000, 0.0000] | -5.9340 [-13.1970, 1.3290] |
| SMB2 | sdpa | ALL | p_champion_minus_off | 0.0321 [-0.1294, 0.1936] | -0.0000 [-0.3680, 0.3680] | -3.3118 [-10.7463, 4.1228] |
| SMB2 | sdpa | LENGTH | p_champion_minus_off | 0.0642 [-0.2579, 0.3864] | -0.0000 [-0.7360, 0.7360] | -1.3773 [-9.3549, 6.6003] |
| SMB2 | sdpa | OFFSET | p_champion_minus_off | -0.0001 [-0.0010, 0.0008] | 0.0000 [0.0000, 0.0000] | -5.2462 [-12.7396, 2.2472] |
| SMB2 | sdpa | ALL | nll_champion_minus_off | 0.0321 [-0.1294, 0.1936] | -0.0000 [-0.3680, 0.3680] | -3.3118 [-10.7463, 4.1228] |
| SMB2 | sdpa | LENGTH | nll_champion_minus_off | 0.0642 [-0.2579, 0.3864] | -0.0000 [-0.7360, 0.7360] | -1.3773 [-9.3549, 6.6003] |
| SMB2 | sdpa | OFFSET | nll_champion_minus_off | -0.0001 [-0.0010, 0.0008] | 0.0000 [0.0000, 0.0000] | -5.2462 [-12.7396, 2.2472] |
| SMB2 | sdpa | ALL | hybrid_minus_off | -0.0366 [-0.1487, 0.0755] | -0.1278 [-0.4385, 0.1830] | -0.5760 [-5.1419, 3.9898] |
| SMB2 | sdpa | LENGTH | hybrid_minus_off | -0.0735 [-0.2951, 0.1480] | -0.2556 [-0.8770, 0.3659] | -1.8399 [-7.9005, 4.2207] |
| SMB2 | sdpa | OFFSET | hybrid_minus_off | 0.0003 [-0.0025, 0.0032] | 0.0000 [0.0000, 0.0000] | 0.6878 [-2.3949, 3.7705] |

## Equal-four-protocol macro

| Backbone | Cohort | Role | p [95% CI] | Hit@1 [95% CI] | NLL [95% CI] | Balanced p [95% CI] | Balanced log gain [95% CI] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rope | all_fields | off | 0.3951 [0.2007, 0.5895] | 0.4469 [0.1516, 0.7423] | 5.5322 [3.2802, 7.7842] | 0.4917 [0.2943, 0.6891] | -0.1333 [-1.9910, 1.7244] |
| rope | all_fields | hybrid | 0.4208 [0.3458, 0.4959] | 0.5345 [0.4604, 0.6086] | 3.0632 [2.1700, 3.9565] | 0.4319 [0.3237, 0.5401] | 1.2714 [0.2681, 2.2746] |
| rope | all_fields | p_champion | 0.4352 [0.3800, 0.4904] | 0.5116 [0.4439, 0.5793] | 3.8754 [3.1535, 4.5972] | 0.4663 [0.4248, 0.5078] | 0.5071 [-0.2698, 1.2840] |
| rope | all_fields | nll_champion | 0.4266 [0.3292, 0.5240] | 0.5116 [0.4943, 0.5289] | 3.8756 [3.2153, 4.5360] | 0.4577 [0.3289, 0.5866] | 0.5069 [-0.2055, 1.2193] |
| rope | length | off | 0.4036 [0.1957, 0.6115] | 0.4669 [0.1500, 0.7838] | 5.0341 [2.6382, 7.4300] | 0.5167 [0.3055, 0.7279] | 0.4748 [-1.4513, 2.4010] |
| rope | length | hybrid | 0.4290 [0.3352, 0.5227] | 0.5756 [0.4135, 0.7377] | 2.8703 [1.8584, 3.8823] | 0.4410 [0.3094, 0.5726] | 1.4358 [0.3510, 2.5205] |
| rope | length | p_champion | 0.4475 [0.3631, 0.5319] | 0.5412 [0.4007, 0.6816] | 3.3488 [1.9512, 4.7463] | 0.4849 [0.4271, 0.5428] | 1.1059 [-0.0453, 2.2571] |
| rope | length | nll_champion | 0.4389 [0.3632, 0.5146] | 0.5412 [0.4756, 0.6068] | 3.3490 [2.0159, 4.6821] | 0.4763 [0.3474, 0.6053] | 1.1056 [0.0174, 2.1939] |
| cope | all_fields | off | 0.3470 [0.2846, 0.4093] | 0.3739 [0.2664, 0.4814] | 4.4288 [3.5998, 5.2578] | 0.4166 [0.3935, 0.4397] | 0.6223 [0.0371, 1.2076] |
| cope | all_fields | hybrid | 0.4563 [0.3808, 0.5317] | 0.5098 [0.5033, 0.5164] | 3.5259 [2.4974, 4.5543] | 0.4699 [0.4010, 0.5389] | 0.9490 [0.0787, 1.8194] |
| cope | all_fields | p_champion | 0.4486 [0.3377, 0.5596] | 0.5001 [0.4143, 0.5860] | 4.1736 [3.2135, 5.1338] | 0.4839 [0.3225, 0.6452] | 0.2084 [-0.3347, 0.7515] |
| cope | all_fields | nll_champion | 0.4637 [0.3809, 0.5466] | 0.5418 [0.4887, 0.5948] | 4.1465 [3.1319, 5.1612] | 0.4990 [0.3743, 0.6236] | 0.2355 [-0.3730, 0.8439] |
| cope | length | off | 0.3612 [0.2793, 0.4431] | 0.4060 [0.2530, 0.5591] | 3.8774 [3.1788, 4.5759] | 0.4412 [0.3931, 0.4892] | 1.1627 [0.7347, 1.5907] |
| cope | length | hybrid | 0.4573 [0.3827, 0.5319] | 0.5122 [0.5077, 0.5167] | 3.5191 [2.0261, 5.0121] | 0.4738 [0.4075, 0.5400] | 0.9810 [-0.2254, 2.1874] |
| cope | length | p_champion | 0.4616 [0.3551, 0.5682] | 0.5344 [0.4452, 0.6237] | 3.2536 [2.3681, 4.1392] | 0.5060 [0.3293, 0.6827] | 1.1222 [0.8905, 1.3538] |
| cope | length | nll_champion | 0.4767 [0.3993, 0.5541] | 0.5761 [0.4697, 0.6825] | 3.2266 [2.2699, 4.1833] | 0.5210 [0.3817, 0.6604] | 1.1492 [0.8378, 1.4606] |
| tape | all_fields | off | 0.3928 [0.2364, 0.5491] | 0.4077 [0.3430, 0.4724] | 7.6970 [4.5926, 10.8013] | 0.4598 [0.2392, 0.6805] | -1.3538 [-2.6539, -0.0537] |
| tape | all_fields | hybrid | 0.4360 [0.3072, 0.5648] | 0.4874 [0.3385, 0.6364] | 3.0353 [2.7300, 3.3406] | 0.4430 [0.3422, 0.5439] | 1.2825 [0.6432, 1.9219] |
| tape | all_fields | p_champion | 0.4245 [0.3681, 0.4810] | 0.5028 [0.3459, 0.6596] | 4.0738 [2.7185, 5.4291] | 0.4450 [0.3860, 0.5039] | 0.2608 [-0.9645, 1.4862] |
| tape | all_fields | nll_champion | 0.4127 [0.1688, 0.6566] | 0.5194 [0.2966, 0.7423] | 4.0436 [2.2489, 5.8383] | 0.4331 [0.1882, 0.6780] | 0.2910 [-1.3742, 1.9563] |
| tape | length | off | 0.4014 [0.2509, 0.5520] | 0.4327 [0.3557, 0.5098] | 7.2451 [4.0024, 10.4877] | 0.4805 [0.2452, 0.7159] | -0.6738 [-1.9535, 0.6059] |
| tape | length | hybrid | 0.4511 [0.2661, 0.6360] | 0.5080 [0.2895, 0.7264] | 2.7799 [2.0480, 3.5119] | 0.4538 [0.3292, 0.5785] | 1.4914 [0.6808, 2.3020] |
| tape | length | p_champion | 0.4435 [0.3586, 0.5284] | 0.5473 [0.3176, 0.7770] | 3.5146 [1.5755, 5.4536] | 0.4661 [0.3810, 0.5511] | 0.8704 [-0.7040, 2.4448] |
| tape | length | nll_champion | 0.4317 [0.1548, 0.7086] | 0.5640 [0.2657, 0.8623] | 3.4844 [1.0963, 5.8725] | 0.4542 [0.1825, 0.7260] | 0.9006 [-1.0984, 2.8996] |
| sdpa | all_fields | off | 0.3811 [0.2277, 0.5345] | 0.4469 [0.1567, 0.7372] | 4.6658 [2.3815, 6.9502] | 0.4663 [0.3135, 0.6190] | 0.3474 [-1.6384, 2.3332] |
| sdpa | all_fields | hybrid | 0.4145 [0.2913, 0.5378] | 0.4327 [0.2733, 0.5922] | 3.5094 [3.2615, 3.7573] | 0.4171 [0.2911, 0.5431] | 0.6574 [0.3819, 0.9329] |
| sdpa | all_fields | p_champion | 0.4779 [0.3668, 0.5891] | 0.5154 [0.3467, 0.6842] | 4.2583 [2.9996, 5.5170] | 0.5115 [0.4062, 0.6169] | 0.2571 [-0.9325, 1.4467] |
| sdpa | all_fields | nll_champion | 0.4339 [0.2844, 0.5834] | 0.4738 [0.2515, 0.6961] | 4.3521 [3.0254, 5.6789] | 0.4675 [0.3294, 0.6056] | 0.1632 [-1.1097, 1.4362] |
| sdpa | length | off | 0.3928 [0.2139, 0.5718] | 0.4808 [0.1146, 0.8470] | 4.1246 [1.6365, 6.6127] | 0.4909 [0.3105, 0.6714] | 0.9160 [-1.1375, 2.9695] |
| sdpa | length | hybrid | 0.4154 [0.2923, 0.5385] | 0.4331 [0.2734, 0.5928] | 3.3096 [3.0197, 3.5995] | 0.4190 [0.2923, 0.5456] | 0.8147 [0.6170, 1.0123] |
| sdpa | length | p_champion | 0.4965 [0.3607, 0.6323] | 0.5492 [0.3223, 0.7760] | 3.2593 [1.9288, 4.5897] | 0.5360 [0.4218, 0.6503] | 1.2013 [0.1956, 2.2071] |
| sdpa | length | nll_champion | 0.4524 [0.2763, 0.6286] | 0.5075 [0.2193, 0.7956] | 3.3532 [1.9625, 4.7439] | 0.4920 [0.3433, 0.6407] | 1.1075 [0.0170, 2.1979] |

## Stage decomposition

True source is used only for post-forward indexing. Source/program are pre-validity heads; route is the executed and smoothed destination prior.

| Target | Backbone | Role | Formula | Source p | Program p given true source | Route p | Final p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DNS | rope | off | off | N/A | N/A | N/A | 0.0485 [0.0482, 0.0487] |
| DNS | rope | hybrid | hybrid | 0.0105 [0.0022, 0.0187] | 0.0001 [-0.0003, 0.0005] | 0.0133 [0.0123, 0.0142] | 0.0155 [0.0116, 0.0194] |
| DNS | rope | p_champion | aux_small | 0.0078 [-0.0023, 0.0179] | 0.0017 [-0.0008, 0.0041] | 0.0132 [0.0125, 0.0139] | 0.0194 [0.0123, 0.0266] |
| DNS | rope | nll_champion | aux_small | 0.0078 [-0.0023, 0.0179] | 0.0017 [-0.0008, 0.0041] | 0.0132 [0.0125, 0.0139] | 0.0194 [0.0123, 0.0266] |
| DNS | cope | off | off | N/A | N/A | N/A | 0.0335 [0.0084, 0.0587] |
| DNS | cope | hybrid | hybrid | 0.0121 [0.0021, 0.0221] | 0.0706 [-0.0399, 0.1811] | 0.0235 [0.0223, 0.0247] | 0.0126 [0.0081, 0.0172] |
| DNS | cope | p_champion | aux_small | 0.0094 [0.0057, 0.0131] | 0.0189 [-0.0353, 0.0731] | 0.0228 [0.0209, 0.0247] | 0.0183 [-0.0021, 0.0387] |
| DNS | cope | nll_champion | aux_small | 0.0094 [0.0057, 0.0131] | 0.0189 [-0.0353, 0.0731] | 0.0228 [0.0209, 0.0247] | 0.0183 [-0.0021, 0.0387] |
| DNS | tape | off | off | N/A | N/A | N/A | 0.0343 [0.0003, 0.0684] |
| DNS | tape | hybrid | hybrid | 0.0092 [-0.0034, 0.0218] | 0.0002 [-0.0002, 0.0005] | 0.0135 [0.0133, 0.0138] | 0.0158 [0.0114, 0.0203] |
| DNS | tape | p_champion | aux_small | 0.0058 [-0.0066, 0.0182] | 0.0007 [0.0005, 0.0010] | 0.0134 [0.0121, 0.0148] | 0.0164 [0.0137, 0.0192] |
| DNS | tape | nll_champion | aux_small | 0.0058 [-0.0066, 0.0182] | 0.0007 [0.0005, 0.0010] | 0.0134 [0.0121, 0.0148] | 0.0164 [0.0137, 0.0192] |
| DNS | sdpa | off | off | N/A | N/A | N/A | 0.0455 [0.0380, 0.0529] |
| DNS | sdpa | hybrid | hybrid | 0.0130 [0.0057, 0.0203] | 0.0354 [-0.1058, 0.1766] | 0.0224 [0.0203, 0.0246] | 0.0099 [0.0081, 0.0118] |
| DNS | sdpa | p_champion | aux_small | 0.0080 [0.0064, 0.0096] | 0.0275 [-0.0378, 0.0928] | 0.0238 [0.0213, 0.0263] | 0.0194 [0.0116, 0.0272] |
| DNS | sdpa | nll_champion | aux_small | 0.0080 [0.0064, 0.0096] | 0.0275 [-0.0378, 0.0928] | 0.0238 [0.0213, 0.0263] | 0.0194 [0.0116, 0.0272] |
| MODBUS | rope | off | off | N/A | N/A | N/A | 0.5288 [-0.2363, 1.2939] |
| MODBUS | rope | hybrid | hybrid | 0.0300 [-0.0754, 0.1354] | 0.3030 [-0.2629, 0.8689] | 0.4752 [0.0450, 0.9054] | 0.8162 [0.5873, 1.0452] |
| MODBUS | rope | p_champion | mix_entropy | 0.0393 [-0.1154, 0.1940] | 0.0989 [0.0313, 0.1666] | 0.5444 [-0.0803, 1.1691] | 0.8081 [0.5912, 1.0250] |
| MODBUS | rope | nll_champion | hybrid | 0.0300 [-0.0754, 0.1354] | 0.3030 [-0.2629, 0.8689] | 0.4752 [0.0450, 0.9054] | 0.8162 [0.5873, 1.0452] |
| MODBUS | cope | off | off | N/A | N/A | N/A | 0.3064 [0.0578, 0.5550] |
| MODBUS | cope | hybrid | hybrid | 0.0667 [-0.0017, 0.1352] | 0.4067 [-0.2168, 1.0302] | 0.3582 [0.2179, 0.4984] | 0.8090 [0.5005, 1.1175] |
| MODBUS | cope | p_champion | mix_entropy | 0.0740 [0.0106, 0.1374] | 0.2593 [-0.3452, 0.8639] | 0.2657 [0.2162, 0.3153] | 0.7300 [0.2760, 1.1840] |
| MODBUS | cope | nll_champion | hybrid | 0.0667 [-0.0017, 0.1352] | 0.4067 [-0.2168, 1.0302] | 0.3582 [0.2179, 0.4984] | 0.8090 [0.5005, 1.1175] |
| MODBUS | tape | off | off | N/A | N/A | N/A | 0.5225 [-0.1124, 1.1574] |
| MODBUS | tape | hybrid | hybrid | 0.0281 [-0.0458, 0.1019] | 0.4759 [-0.0889, 1.0408] | 0.3972 [-0.0031, 0.7976] | 0.8163 [0.3072, 1.3253] |
| MODBUS | tape | p_champion | mix_entropy | 0.0244 [-0.0286, 0.0774] | 0.3670 [-0.6765, 1.4105] | 0.6583 [0.3509, 0.9657] | 0.7257 [0.4521, 0.9993] |
| MODBUS | tape | nll_champion | hybrid | 0.0281 [-0.0458, 0.1019] | 0.4759 [-0.0889, 1.0408] | 0.3972 [-0.0031, 0.7976] | 0.8163 [0.3072, 1.3253] |
| MODBUS | sdpa | off | off | N/A | N/A | N/A | 0.4398 [-0.0753, 0.9549] |
| MODBUS | sdpa | hybrid | hybrid | 0.1114 [-0.0562, 0.2790] | 0.5658 [-0.2532, 1.3848] | 0.2217 [-0.1213, 0.5647] | 0.6448 [0.1473, 1.1422] |
| MODBUS | sdpa | p_champion | mix_entropy | 0.1238 [0.0305, 0.2171] | 0.3247 [-0.1518, 0.8012] | 0.0928 [0.0506, 0.1349] | 0.8246 [0.4571, 1.1921] |
| MODBUS | sdpa | nll_champion | hybrid | 0.1114 [-0.0562, 0.2790] | 0.5658 [-0.2532, 1.3848] | 0.2217 [-0.1213, 0.5647] | 0.6448 [0.1473, 1.1422] |
| TLS | rope | off | off | N/A | N/A | N/A | 0.9767 [0.9224, 1.0309] |
| TLS | rope | hybrid | hybrid | 0.3467 [-0.0314, 0.7249] | 0.8662 [0.6950, 1.0374] | 0.3114 [0.0208, 0.6021] | 0.8181 [0.8010, 0.8352] |
| TLS | rope | p_champion | attr_content | 0.5420 [0.2370, 0.8469] | 0.9187 [0.7917, 1.0457] | 0.6311 [0.2866, 0.9756] | 0.8650 [0.7619, 0.9682] |
| TLS | rope | nll_champion | shared_slot_hybrid | 0.6234 [-0.2677, 1.5144] | 0.8610 [0.6783, 1.0437] | 0.5450 [-0.1594, 1.2494] | 0.8226 [0.2709, 1.3744] |
| TLS | cope | off | off | N/A | N/A | N/A | 0.9955 [0.9917, 0.9993] |
| TLS | cope | hybrid | hybrid | 0.7320 [0.6171, 0.8470] | 0.9808 [0.9449, 1.0167] | 0.7557 [0.6122, 0.8991] | 0.9992 [0.9977, 1.0006] |
| TLS | cope | p_champion | attr_content | 0.6950 [0.4822, 0.9078] | 0.9908 [0.9844, 0.9971] | 0.8600 [0.8392, 0.8807] | 0.9957 [0.9838, 1.0076] |
| TLS | cope | nll_champion | shared_slot_hybrid | 0.7613 [0.7209, 0.8017] | 0.9806 [0.9595, 1.0018] | 0.7686 [0.6618, 0.8755] | 0.9770 [0.9008, 1.0531] |
| TLS | tape | off | off | N/A | N/A | N/A | 0.9846 [0.9695, 0.9996] |
| TLS | tape | hybrid | hybrid | 0.5779 [0.1202, 1.0355] | 0.9311 [0.7360, 1.1261] | 0.5318 [0.1388, 0.9248] | 0.8506 [0.5340, 1.1673] |
| TLS | tape | p_champion | attr_content | 0.4432 [0.0435, 0.8429] | 0.8085 [0.4763, 1.1406] | 0.5584 [0.0132, 1.1037] | 0.8810 [0.5670, 1.1951] |
| TLS | tape | nll_champion | shared_slot_hybrid | 0.2689 [-0.1055, 0.6433] | 0.8378 [0.7014, 0.9742] | 0.2569 [-0.0765, 0.5904] | 0.7431 [0.3810, 1.1053] |
| TLS | sdpa | off | off | N/A | N/A | N/A | 0.9989 [0.9982, 0.9997] |
| TLS | sdpa | hybrid | hybrid | 0.7683 [0.7615, 0.7752] | 0.9901 [0.9771, 1.0031] | 0.7616 [0.5390, 0.9842] | 0.9997 [0.9995, 1.0000] |
| TLS | sdpa | p_champion | attr_content | 0.6950 [0.4780, 0.9120] | 0.9777 [0.9364, 1.0189] | 0.8465 [0.7622, 0.9307] | 0.9953 [0.9789, 1.0117] |
| TLS | sdpa | nll_champion | shared_slot_hybrid | 0.7591 [0.7192, 0.7990] | 0.9876 [0.9709, 1.0043] | 0.7653 [0.6524, 0.8782] | 0.9989 [0.9977, 1.0002] |
| SMB2 | rope | off | off | N/A | N/A | N/A | 0.0266 [-0.0285, 0.0817] |
| SMB2 | rope | hybrid | hybrid | 0.0026 [-0.0000, 0.0052] | 0.0076 [-0.0195, 0.0347] | 0.0057 [-0.0002, 0.0116] | 0.0335 [-0.0437, 0.1107] |
| SMB2 | rope | p_champion | attr_content | 0.0018 [0.0002, 0.0034] | 0.0055 [-0.0163, 0.0272] | 0.0045 [-0.0002, 0.0091] | 0.0481 [-0.0785, 0.1747] |
| SMB2 | rope | nll_champion | attr_content | 0.0018 [0.0002, 0.0034] | 0.0055 [-0.0163, 0.0272] | 0.0045 [-0.0002, 0.0091] | 0.0481 [-0.0785, 0.1747] |
| SMB2 | cope | off | off | N/A | N/A | N/A | 0.0524 [-0.0804, 0.1852] |
| SMB2 | cope | hybrid | hybrid | 0.0017 [0.0006, 0.0028] | 0.0035 [-0.0041, 0.0111] | 0.0036 [0.0023, 0.0048] | 0.0043 [-0.0082, 0.0167] |
| SMB2 | cope | p_champion | attr_content | 0.0014 [0.0014, 0.0014] | 0.0060 [-0.0047, 0.0168] | 0.0028 [0.0027, 0.0029] | 0.0506 [0.0275, 0.0737] |
| SMB2 | cope | nll_champion | attr_content | 0.0014 [0.0014, 0.0014] | 0.0060 [-0.0047, 0.0168] | 0.0028 [0.0027, 0.0029] | 0.0506 [0.0275, 0.0737] |
| SMB2 | tape | off | off | N/A | N/A | N/A | 0.0297 [-0.0025, 0.0619] |
| SMB2 | tape | hybrid | hybrid | 0.0027 [-0.0007, 0.0061] | 0.0062 [-0.0148, 0.0271] | 0.0046 [0.0004, 0.0088] | 0.0613 [-0.1626, 0.2851] |
| SMB2 | tape | p_champion | attr_content | 0.0019 [-0.0015, 0.0052] | 0.0060 [-0.0177, 0.0298] | 0.0058 [-0.0047, 0.0164] | 0.0749 [-0.0590, 0.2089] |
| SMB2 | tape | nll_champion | attr_content | 0.0019 [-0.0015, 0.0052] | 0.0060 [-0.0177, 0.0298] | 0.0058 [-0.0047, 0.0164] | 0.0749 [-0.0590, 0.2089] |
| SMB2 | sdpa | off | off | N/A | N/A | N/A | 0.0403 [-0.0661, 0.1467] |
| SMB2 | sdpa | hybrid | hybrid | 0.0015 [0.0011, 0.0018] | 0.0046 [-0.0052, 0.0144] | 0.0031 [0.0022, 0.0040] | 0.0037 [-0.0021, 0.0095] |
| SMB2 | sdpa | p_champion | attr_content | 0.0014 [0.0014, 0.0015] | 0.0066 [-0.0132, 0.0265] | 0.0028 [0.0027, 0.0028] | 0.0724 [-0.0484, 0.1932] |
| SMB2 | sdpa | nll_champion | attr_content | 0.0014 [0.0014, 0.0015] | 0.0066 [-0.0132, 0.0265] | 0.0028 [0.0027, 0.0028] | 0.0724 [-0.0484, 0.1932] |

## Typed exact-field F1 — a separate task

| Target | Backbone | Role | Formula | Field F1 [95% CI] |
| --- | --- | --- | --- | --- |
| DNS | rope | off | off | N/A (not trained) |
| DNS | rope | hybrid | hybrid | 0.0000 [0.0000, 0.0000] |
| DNS | rope | p_champion | aux_small | 0.0000 [0.0000, 0.0000] |
| DNS | rope | nll_champion | aux_small | 0.0000 [0.0000, 0.0000] |
| DNS | cope | off | off | N/A (not trained) |
| DNS | cope | hybrid | hybrid | 0.0000 [0.0000, 0.0000] |
| DNS | cope | p_champion | aux_small | 0.0000 [0.0000, 0.0000] |
| DNS | cope | nll_champion | aux_small | 0.0000 [0.0000, 0.0000] |
| DNS | tape | off | off | N/A (not trained) |
| DNS | tape | hybrid | hybrid | 0.0000 [0.0000, 0.0000] |
| DNS | tape | p_champion | aux_small | 0.0000 [0.0000, 0.0000] |
| DNS | tape | nll_champion | aux_small | 0.0000 [0.0000, 0.0000] |
| DNS | sdpa | off | off | N/A (not trained) |
| DNS | sdpa | hybrid | hybrid | 0.0000 [0.0000, 0.0000] |
| DNS | sdpa | p_champion | aux_small | 0.0000 [0.0000, 0.0000] |
| DNS | sdpa | nll_champion | aux_small | 0.0000 [0.0000, 0.0000] |
| MODBUS | rope | off | off | N/A (not trained) |
| MODBUS | rope | hybrid | hybrid | 0.0000 [0.0000, 0.0000] |
| MODBUS | rope | p_champion | mix_entropy | 0.0000 [0.0000, 0.0000] |
| MODBUS | rope | nll_champion | hybrid | 0.0000 [0.0000, 0.0000] |
| MODBUS | cope | off | off | N/A (not trained) |
| MODBUS | cope | hybrid | hybrid | 0.0000 [0.0000, 0.0000] |
| MODBUS | cope | p_champion | mix_entropy | 0.0000 [0.0000, 0.0000] |
| MODBUS | cope | nll_champion | hybrid | 0.0000 [0.0000, 0.0000] |
| MODBUS | tape | off | off | N/A (not trained) |
| MODBUS | tape | hybrid | hybrid | 0.0000 [0.0000, 0.0000] |
| MODBUS | tape | p_champion | mix_entropy | 0.0000 [0.0000, 0.0000] |
| MODBUS | tape | nll_champion | hybrid | 0.0000 [0.0000, 0.0000] |
| MODBUS | sdpa | off | off | N/A (not trained) |
| MODBUS | sdpa | hybrid | hybrid | 0.0000 [0.0000, 0.0000] |
| MODBUS | sdpa | p_champion | mix_entropy | 0.0000 [0.0000, 0.0000] |
| MODBUS | sdpa | nll_champion | hybrid | 0.0000 [0.0000, 0.0000] |
| TLS | rope | off | off | N/A (not trained) |
| TLS | rope | hybrid | hybrid | 0.3582 [-0.0436, 0.7601] |
| TLS | rope | p_champion | attr_content | 0.6643 [0.3107, 1.0178] |
| TLS | rope | nll_champion | shared_slot_hybrid | 0.4503 [-0.0153, 0.9158] |
| TLS | cope | off | off | N/A (not trained) |
| TLS | cope | hybrid | hybrid | 0.8576 [0.7967, 0.9185] |
| TLS | cope | p_champion | attr_content | 0.8708 [0.7205, 1.0212] |
| TLS | cope | nll_champion | shared_slot_hybrid | 0.6787 [0.3409, 1.0165] |
| TLS | tape | off | off | N/A (not trained) |
| TLS | tape | hybrid | hybrid | 0.6594 [0.2631, 1.0556] |
| TLS | tape | p_champion | attr_content | 0.5487 [0.0802, 1.0172] |
| TLS | tape | nll_champion | shared_slot_hybrid | 0.2763 [-0.2108, 0.7635] |
| TLS | sdpa | off | off | N/A (not trained) |
| TLS | sdpa | hybrid | hybrid | 0.9106 [0.7759, 1.0452] |
| TLS | sdpa | p_champion | attr_content | 0.8722 [0.8603, 0.8842] |
| TLS | sdpa | nll_champion | shared_slot_hybrid | 0.7941 [0.5969, 0.9913] |
| SMB2 | rope | off | off | N/A (not trained) |
| SMB2 | rope | hybrid | hybrid | 0.0000 [0.0000, 0.0000] |
| SMB2 | rope | p_champion | attr_content | 0.0000 [0.0000, 0.0000] |
| SMB2 | rope | nll_champion | attr_content | 0.0000 [0.0000, 0.0000] |
| SMB2 | cope | off | off | N/A (not trained) |
| SMB2 | cope | hybrid | hybrid | 0.0000 [0.0000, 0.0000] |
| SMB2 | cope | p_champion | attr_content | 0.0000 [0.0000, 0.0000] |
| SMB2 | cope | nll_champion | attr_content | 0.0000 [0.0000, 0.0000] |
| SMB2 | tape | off | off | N/A (not trained) |
| SMB2 | tape | hybrid | hybrid | 0.0000 [0.0000, 0.0000] |
| SMB2 | tape | p_champion | attr_content | 0.0000 [0.0000, 0.0000] |
| SMB2 | tape | nll_champion | attr_content | 0.0000 [0.0000, 0.0000] |
| SMB2 | sdpa | off | off | N/A (not trained) |
| SMB2 | sdpa | hybrid | hybrid | 0.0000 [0.0000, 0.0000] |
| SMB2 | sdpa | p_champion | attr_content | 0.0000 [0.0000, 0.0000] |
| SMB2 | sdpa | nll_champion | attr_content | 0.0000 [0.0000, 0.0000] |

## Deterministic sanity references

These are not prior-paper models. Uniform argmax ties choose index 0; expected sampled Hit@1 equals p(target). Zero-probability NLL is reported with a 1e-30 floor.

| Target | Semantic | N | Reference | p(target) | Hit@1 | NLL |
| --- | --- | --- | --- | --- | --- | --- |
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

## Audit boundaries

- Verified 180 screen, 64 refine, and 156 unique final models.
- Recomputed mappings and final probabilities for 12672 unique run-field predictions.
- Same-seed protocol-balanced training streams and native shared initial tensors were matched.
- All On variants retain four nonzero losses; aux_small/aux_large explicitly change auxiliary weights.
- Probability-selected and NLL-selected roles can disagree; final results do not alter either choice.
- A winning formula is best only under its precommitted selection objective and budget, not universally optimal.
- No historical prior-paper baseline is inserted as if retrained in this new architecture experiment.
