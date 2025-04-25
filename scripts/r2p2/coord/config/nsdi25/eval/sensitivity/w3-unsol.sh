#!/bin/bash
# meant to be run from coord dir ..
source "config/paper-configs/nsdi24/large/large-scale-common.sh"

# ===================== Temporary Replacements =====================
r2p2_unsolicited_thresh_bytes_l="1400 100000 200000 400000 1600000 -1"
# ===================== General Settingss =====================
max_threads='26'

# ===================== Common Parameters =====================
client_injection_rate_gbps_list="50 60 70 95"
duration_modifier_l="${w3_dur}"
mean_req_size_B_l='2927.354'
req_size_distr='w3'

# ===================== HOMA Parametrs =====================
homa_workload_type=$(echo $req_size_distr | sed 's/[^0-9]*//g')

# ===================== Protocols =====================
transp_prots='micro-hybrid micro-hybrid micro-hybrid micro-hybrid micro-hybrid micro-hybrid'
simulation_name_l='PKT BDP 2xBDP 4xBDP 16xBDP all'
