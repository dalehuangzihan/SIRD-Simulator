#!/bin/bash
# meant to be run from coord dir ..
source "config/paper/large-scale-common-oversub.default"

# ===================== Temporary Replacements =====================

# ===================== General Settingss =====================
max_threads='24'

# ===================== Common Parameters =====================
client_injection_rate_gbps_list="$w5_loads"
duration_modifier_l="${w5_dur}"
mean_req_size_B_l='2515857.4'
req_size_distr='w5'

# ===================== HOMA Parametrs =====================
homa_workload_type=$(echo $req_size_distr | sed 's/[^0-9]*//g')

# ===================== Protocols =====================
transp_prots='micro-hybrid'
simulation_name_l='SIRD'
