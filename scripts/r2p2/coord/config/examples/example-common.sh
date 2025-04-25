#!/bin/bash
# ===================== Common Parameters =====================
req_interval_distr='exponential'
req_target_distr='uniform' # manual or uniform
mean_service_time_us='0.00001'
mean_resp_size_B='20'
topology_file_l='eval.yaml'
manual_req_interval_file_l='-'
resp_proc_time_distr='exponential'
resp_size_distr='fixed'
lognormal_sigma='1.8'
tcp_connections_per_thread_pair='40'

switch_queue_type_l="per-port" # "per-port" or "shared"
load_pattern="fixed" 
lp_period="0.002"
lp_step_high_ratio="0.5"
lp_high_value_mul="1.8"
lp_low_value_mul="0.2"

oversub_topo="0"
drop_tail_num_prios_l="8"

w3_loads="25 50 60 70 80 85 90 95"
w4_loads="25 50 60 70 80 85 90 95"
w5_loads="25 50 60 70 80 85 90 95"

# ======= Incast =======
incast_workload_ratio_l="0.0" # 0.07
incast_size_l="30"
incast_request_size_bytes_l="500000"
# ===================== Tracing/Monitoring Parameters =====================
w3_dur="0.09"
w4_dur="0.4"
w5_dur="0.5"

simple_trace_all='0'
trace_r2p2_layer_cl='0'
trace_r2p2_layer_sr='0'
trace_router='0'
trace_application='1'
trace_cc='1'

capture_pkt_trace='0'
capture_msg_trace='0'

trace_last_ratio='0.1' # the % of the total simulation duration that will be traced / monitored
state_polling_ival_s='0.00001' # switch buffer length sampling frequency

# ===================== Debugging Options =====================
global_debug='1' # From 1 to 7 (7 = super verbose). Set it to 0 to enable the following, more fine-grain options
app_debug='2'
full_tcp_debug='2' # pfabric and dctcp
r2p2_tranport_debug='2'
r2p2_udp_debug='2'
r2p2_router_debug='2'
r2p2_cc_debug='2' # dubug level for r2p2 congestion control module
homa_transport_debug='2'
homa_udp_debug='2'

# ===================== Common Parameters =====================

# ===================== R2P2 Parameters =====================
# --- general params
r2p2_ecn_threshold_min_l='82' # packets
r2p2_ecn_threshold_max_l='82' # packets
r2p2_ce_new_weight_l='0.08'
r2p2_ecn_min_mul_l='0.1'
r2p2_ecn_min_mul_nw_l='0.03'

# --- hybrid params
r2p2_budgets_intra_max_bytes_l='150000'
r2p2_elet_srpb_l='100000'
r2p2_elet_receiver_policy_l='3' # 0: TS among msgs, 1: fifo among senders, 2: fifo among messages 3: SRPT
r2p2_hybrid_sender_algo_l="0"
r2p2_unsolicited_limit_senders_l="0"
r2p2_unsolicited_burst_when_idle_l="0"
r2p2_hybrid_in_network_prios_l="1"
r2p2_data_prio_l="1"
r2p2_hybrid_sender_policy_l="1"
r2p2_sender_policy_ratio_l='0.5'
r2p2_hybrid_pace_grants_l="1"
r2p2_elet_account_unsched_l="1"

# DCTCP algo config
r2p2_sender_ecn_threshold_l="33"

# HPCC algo config
r2p2_hybrid_eta_l="1.5"
r2p2_hybrid_max_stage_l="1"

single_path_per_msg_l='0' # 1: all uRPCs follow the same path
r2p2_ecn_at_core_l='1' # 0 to disable - 1: only mark at core links (tor<->spine), 0: no ecn
urpc_sz_bytes_l='1500'

r2p2_ecn_mechanism_influence_l='1.0'
r2p2_host_uplink_prio_l='1'

r2p2_hybrid_additive_incr_mul_l="1"

r2p2_ecn_init_slash_mul_l='0.5'
r2p2_hybrid_wai_l="1550" # bytes
r2p2_priority_flow_l="0"
r2p2_hybrid_reset_after_x_rtt_l="-1"
r2p2_unsolicited_thresh_bytes_l="100000"

# ===================== DCTCP Parameters =====================
dctcp_init_cwnd_l='66' # in packets
dctcp_min_rto='0.000200' 
general_queue_size_l='300000' #pkts
dctcp_g_l='0.08'
dctcp_K_l="$r2p2_ecn_threshold_max_l"

# ===================== Pfabric Parameters =====================
queue_size_pfab='54' # See config doc
pfab_g='0.0625'
pfab_K='10000' # useless, pfabric does not mark
pfab_min_rto='0.000024'

# ===================== Swift Parametrs =====================
swift_base_target_delay_l="0.0000150"
swift_max_scaling_range_l="0.0000750"
swift_per_hop_scaling_factor_l="0.000001"
swift_max_cwnd_target_scaling_l="100"
swift_min_cwnd_target_scaling_l="0.1"
swift_additive_increase_constant_l="1"
swift_multiplicative_decrease_constant_l="0.8"
swift_max_mdf_l="0.5"

# ===================== HOMA Parametrs =====================
homa_grant_max_bytes='1472'
homa_account_for_grant_traffic='1'
homa_unsched_prio_usage_weight='1'
homa_is_round_robin_scheduler='0'
homa_link_check_bytes_l='-1'
homa_default_req_bytes='1442'  # based on homa sim config
homa_boost_tail_bytes_prio_l="0"
homa_use_unsch_rate_in_scheduler='0'
homa_in_network_prios_l='1'

homa_rtt_bytes="100000"
homa_all_prio_l='8'
homa_adaptive_sched_prio_levels_l='7'
homa_default_unsched_bytes_l="$(($homa_rtt_bytes - $homa_default_req_bytes))"
