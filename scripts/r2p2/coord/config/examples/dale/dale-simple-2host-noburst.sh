#!/bin/bash
# meant to be run from coord dir ..
source "config/examples/example-common.sh"

# ===================== General Settingss =====================
max_threads='4'

# ===================== Common Parameters =====================
topology_file_l='4-hosts.yaml'
trace_last_ratio='1.0' # the % of the total simulation duration that will be traced / monitored
trace_cc='1'

state_polling_ival_s='0.000001' # sample switch queue lengths every 1us

req_interval_distr='manual'
req_target_distr='manual' # manual or uniform
req_size_distr='manual'
manual_req_interval_file_l='dale-simple-2host.csv'
client_injection_rate_gbps_list='60' # value is meaningful only when req_interval_distr is not 'manual'
duration_modifier_l='0.0004' # when manual, this specifies the sim duration in secods. For 3 1MB flows at 100Gbps, it takes approx 3*80us = 0.00024sec
mean_req_size_B_l='121848' # only meanigful if req_size_distr is not manual

# ===================== Debugging Options =====================
global_debug='6' # From 1 to 7 (7 = super verbose). Set it to 0 to enable the following, more fine-grain options

# ===================== R2P2 Parameters =====================
r2p2_budgets_intra_max_bytes_l='108000'
r2p2_elet_srpb_l='72000'
r2p2_unsolicited_thresh_bytes_l="0" # here we set UnschT = 0 i.e. no bursting.
r2p2_hybrid_sender_policy_l="1"
r2p2_sender_policy_ratio_l='0.5'
r2p2_sender_ecn_threshold_l="25"
r2p2_elet_account_unsched_l="1"
r2p2_hybrid_sender_algo_l="0"
# ===================== DCTCP Parameters =====================

# ===================== HOMA Parametrs =====================
homa_workload_type=5

# ===================== Protocols =====================
transp_prots='micro-hybrid'
simulation_name_l='SIRD-dale-2host'

