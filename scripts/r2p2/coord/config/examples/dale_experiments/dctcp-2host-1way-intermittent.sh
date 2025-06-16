#!/bin/bash
# meant to be run from coord dir ..
source "config/examples/example-common.sh"

# ===================== general settingss =====================
max_threads='4'

# ===================== common parameters =====================
topology_file_l='4-hosts.yaml'
trace_last_ratio='1.0' # the % of the total simulation duration that will be traced / monitored
trace_cc='1'

state_polling_ival_s='0.000001' # sample switch queue lengths every 1us

req_interval_distr='manual'
req_target_distr='manual' # manual or uniform
req_size_distr='manual'
manual_req_interval_file_l='dale_experiments/2host-1way-intermittent.csv'
client_injection_rate_gbps_list='60' # value is meaningful only when req_interval_distr is not 'manual'
duration_modifier_l='0.0004' # when manual, this specifies the sim duration in secods. for 3 1mb flows at 100gbps, it takes approx 3*80us = 0.00024sec
mean_req_size_B_l='121848' # only meanigful if req_size_distr is not manual

# ===================== debugging options =====================
global_debug='6' # from 1 to 7 (7 = super verbose). set it to 0 to enable the following, more fine-grain options

# ===================== r2p2 parameters =====================

# ===================== dctcp parameters =====================
dctcp_k_l="82 50" # dctcp's ecn marking threshold in packets

# ===================== homa parametrs =====================
homa_workload_type=5

# ===================== protocols =====================
transp_prots='dctcp dctcp'
simulation_name_l='dctcp-82 dctcp-50'

