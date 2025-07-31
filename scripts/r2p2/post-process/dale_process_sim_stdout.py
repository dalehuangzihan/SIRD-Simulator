from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import math
import dale_experiment_rig

CR_PKT_SUBSTRING = "Forwarded standalone grant_request asking for"
C_PKT_SUBSTRING = ">>>>Sending credit to:"
D_PKT_SUBSTRING = "Sending pkt of msg"
C_PKT_RECV_SUBSTRING = "R2p2CCHybrid::received_credit() from receiver"
SUBSTR_LIST = [CR_PKT_SUBSTRING, C_PKT_SUBSTRING, D_PKT_SUBSTRING]
CREDITREQ_PKT_OVERHEAD_B = 84
CREDIT_PKT_OVERHEAD_B = 84
PKT_HDR_SIZE_B = 80

# PATH_TO_SIM_OUTPUTS = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/scripts/r2p2/coord/outputs/"
PATH_TO_SIM_OUTPUTS = "/data/dh1723/SIRD-Simulator/scripts/r2p2/coord/outputs/" # NOTE: use this for batch1 server
REL_PATH_TO_EXP_FAMILY = "FCT_Subpkt_Byteloads_subpkt_multiflow/"
REL_PATH_TO_EXP_FAMILY_FASTPACE = "FCT_Subpkt_Byteloads_subpkt_multiflow_fastpace/"
REL_PATH_TO_EXP_FAMILY_FASTPACE_EXTENDED = "FCT_Subpkt_Byteloads_subpkt_multiflow_fastpace_extended/"
REL_PATH_TO_EXP_FAMILY_SLOWPACE = "FCT_Subpkt_Byteloads_subpkt_multiflow_slowpace/"

# PATH_TO_SCRIPTS_R2P2 = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/scripts/r2p2/"
PATH_TO_SCRIPTS_R2P2 = "/data/dh1723/SIRD-Simulator/scripts/r2p2/" # NOTE: use this for batch1 server
PATH_TO_POSTPROC = f"{PATH_TO_SCRIPTS_R2P2}post-process/"
PATH_TO_TMP_PLOT = PATH_TO_POSTPROC + "tmp_plot/"
PATH_TO_PROC_SIM_OUTPUT_DIR = PATH_TO_TMP_PLOT + "proc_sim_outputs/"

class SimOutputStats:
    def __init__(self, num_creditreq_pkts, num_credit_pkts, num_data_pkts):
        self.num_creditreq_pkts = num_creditreq_pkts
        self.num_credit_pkts = num_credit_pkts
        self.num_data_pkts = num_data_pkts
        self.total_overheads_B = self.num_creditreq_pkts * CREDITREQ_PKT_OVERHEAD_B + self.num_credit_pkts * CREDIT_PKT_OVERHEAD_B + self.num_data_pkts * PKT_HDR_SIZE_B
        self.total_overheads_sendr_to_recvr_B = self.num_creditreq_pkts * CREDITREQ_PKT_OVERHEAD_B + self.num_data_pkts * PKT_HDR_SIZE_B

    def pretty_print(self):
        print(f"Num Credit Req Pkts: {self.num_creditreq_pkts}")
        print(f"Num Credit Pkts: {self.num_credit_pkts}")
        print(f"Num Data Pkts: {self.num_data_pkts}")
        print(f"Total Overheads (B): {self.total_overheads_B}")
        print(f"Total Overheads (sendr to recvr only) (B): {self.total_overheads_sendr_to_recvr_B}")

class DataPktStats:
    def __init__(self, count_d_pkts, total_data_sent_B, start_time_s, end_time_s, thrpt_bps, timestamps_s_list, data_sent_cumu_B_list):
        self.count_d_pkts = count_d_pkts
        self.total_data_sent_B = total_data_sent_B
        self.start_time_s = start_time_s
        self.end_time_s = end_time_s
        self.thrpt_bps = thrpt_bps
        self.timestamps_s_list = timestamps_s_list
        self.data_sent_cumu_B_list = data_sent_cumu_B_list

class CreditPktStats:
    def __init__(self, count_credit_pkts, total_credit_B, start_time_s, end_time_s, credit_rate_bps, timestamps_s_list, credit_cumu_B_list):
        self.count_credit_pkts = count_credit_pkts
        self.total_credit_B = total_credit_B
        self.start_time_s = start_time_s
        self.end_time_s = end_time_s
        self.credit_rate_bps = credit_rate_bps
        self.timestamps_s_list = timestamps_s_list
        self.credit_cumu_B_list = credit_cumu_B_list

def count_cr_r_d_pkts_in_sim_stdout(filepath):
    num_creditreq_pkts = 0
    num_creditreq_pkts_0_to_1 = 0
    num_credit_pkts = 0
    num_credit_pkts_1_to_0 = 0
    num_data_pkts = 0
    num_data_pkts_0_to_1 = 0

    with open(filepath, 'r') as file:
        for line in file:
            if CR_PKT_SUBSTRING in line:
                num_creditreq_pkts += 1
                if f"0 {CR_PKT_SUBSTRING}" in line: num_creditreq_pkts_0_to_1 += 1

            elif C_PKT_SUBSTRING in line:
                num_credit_pkts += 1
                if f"1 {C_PKT_SUBSTRING}" in line: num_credit_pkts_1_to_0 += 1

            elif D_PKT_SUBSTRING in line:
                num_data_pkts += 1
                if f"0 {D_PKT_SUBSTRING}" in line: num_data_pkts_0_to_1 += 1

            else:
                pass

            num_matching_substrings = sum(substr in line for substr in SUBSTR_LIST)
            if num_matching_substrings > 1:
                print(line)
                assert(False)

    sim_output_stats_overall_nw = SimOutputStats(num_creditreq_pkts, num_credit_pkts, num_data_pkts) 
    sim_output_stats_p2p_data_transf_only = SimOutputStats(num_creditreq_pkts_0_to_1, num_credit_pkts_1_to_0, num_data_pkts_0_to_1)
    return sim_output_stats_overall_nw, sim_output_stats_p2p_data_transf_only

def get_actual_sender_thrpt_bps(filepath):
    timestamps_s_list = []
    data_sent_cumu_B_list = []

    count_d_pkts = 0
    total_data_sent_B = 0
    start_time_s = math.inf
    end_time_s = -1
    with open(filepath, 'r') as file:
        for line in file:
            if f"0 {D_PKT_SUBSTRING}" in line:
                count_d_pkts += 1
                tokens_list = line.split(" ")
                timestamp_s = float(tokens_list[0])
                data_to_send_B = int(tokens_list[-1])

                total_data_sent_B += data_to_send_B
                start_time_s = min(timestamp_s, start_time_s)
                end_time_s = max(timestamp_s, end_time_s)

                timestamps_s_list.append(timestamp_s)
                data_sent_cumu_B_list.append(total_data_sent_B)
    
    thrpt_bps = total_data_sent_B * 8/(end_time_s - start_time_s)
    return DataPktStats(count_d_pkts, total_data_sent_B, start_time_s, end_time_s, thrpt_bps, timestamps_s_list, data_sent_cumu_B_list)
    # return count_d_pkts, total_data_sent_B, start_time_s, end_time_s, thrpt_bps, timestamps_s_list, data_sent_cumu_B_list

def get_actual_sender_gdpt_bps(filepath):
    timestamps_s_list = []
    data_sent_cumu_B_list = []

    count_d_pkts = 0
    total_data_sent_B = 0
    start_time_s = math.inf
    end_time_s = -1
    with open(filepath, 'r') as file:
        for line in file:
            if f"0 {D_PKT_SUBSTRING}" in line:
                count_d_pkts += 1
                tokens_list = line.split(" ")
                timestamp_s = float(tokens_list[0])
                data_to_send_B = int(tokens_list[-1])

                total_data_sent_B += (data_to_send_B - PKT_HDR_SIZE_B)
                start_time_s = min(timestamp_s, start_time_s)
                end_time_s = max(timestamp_s, end_time_s)

                timestamps_s_list.append(timestamp_s)
                data_sent_cumu_B_list.append(total_data_sent_B)
    
    gdpt_bps = total_data_sent_B * 8/(end_time_s - start_time_s)

    return DataPktStats(count_d_pkts, total_data_sent_B, start_time_s, end_time_s, gdpt_bps, timestamps_s_list, data_sent_cumu_B_list)
    # return count_d_pkts, total_data_sent_B, start_time_s, end_time_s, gdpt_bps, timestamps_s_list, data_sent_cumu_B_list

def get_credit_send_rate_bps(filepath):
    timestamps_s_list = []
    credit_sent_cumu_B_list = []

    count_credit_pkts = 0
    total_credit_B = 0
    start_time_s = math.inf
    end_time_s = -1
    with open(filepath, 'r') as file:
        for line in file:
            if f"1 {C_PKT_SUBSTRING}" in line:
                count_credit_pkts += 1
                tokens_list = line.split(" ")
                timestamp_s = float(tokens_list[0])

                idx_of_credit_data_token = tokens_list.index("credit_needed:") + 1
                credit_B = int(tokens_list[idx_of_credit_data_token])
                total_credit_B += credit_B

                start_time_s = min(timestamp_s, start_time_s)
                end_time_s = max(timestamp_s, end_time_s)

                timestamps_s_list.append(timestamp_s)
                credit_sent_cumu_B_list.append(total_credit_B)

    credit_send_rate_bps = total_credit_B * 8 / (end_time_s - start_time_s)
    return CreditPktStats(count_credit_pkts, total_credit_B, start_time_s, end_time_s, credit_send_rate_bps, timestamps_s_list, credit_sent_cumu_B_list)
    # return count_credit_pkts, total_credit_B, start_time_s, end_time_s, credit_send_rate_bps, timestamps_s_list, credit_sent_cumu_B_list

def get_credit_data_send_rate_bps(filepath):
    timestamps_s_list = []
    credit_sent_cumu_B_list = []

    count_credit_pkts = 0
    total_credit_data_B = 0
    start_time_s = math.inf
    end_time_s = -1
    with open(filepath, 'r') as file:
        for line in file:
            if f"1 {C_PKT_SUBSTRING}" in line:
                count_credit_pkts += 1
                tokens_list = line.split(" ")
                timestamp_s = float(tokens_list[0])

                idx_of_credit_data_token = tokens_list.index("credit_needed_data") + 1
                credit_data_B = int(tokens_list[idx_of_credit_data_token])
                total_credit_data_B += credit_data_B

                start_time_s = min(timestamp_s, start_time_s)
                end_time_s = max(timestamp_s, end_time_s)

                timestamps_s_list.append(timestamp_s)
                credit_sent_cumu_B_list.append(total_credit_data_B)

    credit_data_send_rate_bps = total_credit_data_B * 8 / (end_time_s - start_time_s)
    return CreditPktStats(count_credit_pkts, total_credit_data_B, start_time_s, end_time_s, credit_data_send_rate_bps, timestamps_s_list, credit_sent_cumu_B_list)
    # return count_credit_pkts, total_credit_data_B, start_time_s, end_time_s, credit_data_send_rate_bps, timestamps_s_list, credit_sent_cumu_B_list

def get_credit_recv_rate_bps(filepath):
    timestamps_s_list = []
    credit_recv_cumu_B_list = []

    count_credit_pkts = 0
    total_credit_B = 0
    start_time_s = math.inf
    end_time_s = -1
    with open(filepath, 'r') as file:
        for line in file:
            if f"0 {C_PKT_RECV_SUBSTRING}" in line:
                count_credit_pkts += 1
                tokens_list = line.split(" ")
                timestamp_s = float(tokens_list[0])
                idx_of_credit_token = tokens_list.index("credits:") + 1
                credit_B = int(tokens_list[idx_of_credit_token])

                total_credit_B += credit_B
                start_time_s = min(timestamp_s, start_time_s)
                end_time_s = max(timestamp_s, end_time_s)

                timestamps_s_list.append(timestamp_s)
                credit_recv_cumu_B_list.append(total_credit_B)

    credit_recv_rate_bps = total_credit_B * 8 / (end_time_s - start_time_s)
    return CreditPktStats(count_credit_pkts, total_credit_B, start_time_s, end_time_s, credit_recv_rate_bps, timestamps_s_list, credit_recv_cumu_B_list)
    # return count_credit_pkts, total_credit_B, start_time_s, end_time_s, credit_recv_rate_bps, timestamps_s_list, credit_recv_cumu_B_list

def get_credit_data_recv_rate_bps(filepath):
    timestamps_s_list = []
    credit_data_recv_cumu_B_list = []

    count_credit_pkts = 0
    total_credit_data_B = 0
    start_time_s = math.inf
    end_time_s = -1
    with open(filepath, 'r') as file:
        for line in file:
            if f"0 {C_PKT_RECV_SUBSTRING}" in line:
                count_credit_pkts += 1
                tokens_list = line.split(" ")
                timestamp_s = float(tokens_list[0])
                idx_of_credit_data_token = tokens_list.index("credits:") + 1
                credit_data_B = int(tokens_list[idx_of_credit_data_token]) - PKT_HDR_SIZE_B

                total_credit_data_B += credit_data_B
                start_time_s = min(timestamp_s, start_time_s)
                end_time_s = max(timestamp_s, end_time_s)

                timestamps_s_list.append(timestamp_s)
                credit_data_recv_cumu_B_list.append(total_credit_data_B)

    credit_data_recv_rate_bps = total_credit_data_B * 8 / (end_time_s - start_time_s)
    return CreditPktStats(count_credit_pkts, total_credit_data_B, start_time_s, end_time_s, credit_data_recv_rate_bps, timestamps_s_list, credit_data_recv_cumu_B_list)
    # return count_credit_pkts, total_credit_data_B, start_time_s, end_time_s, credit_data_recv_rate_bps, timestamps_s_list, credit_data_recv_cumu_B_list

# '''
# ======== 1 FLO SUBPKT EXPERIMENTS ========
# '''
# def proc_1flo_4B_per_bload_sim_outputs(): 
#     sim_output_4B_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY + "ssird_1flo-10000#-4B-1us_subpkt_multiflow_stdout.out"
#     sim_4B_bload_stats, _ = count_cr_r_d_pkts_in_sim_stdout(sim_output_4B_byteloads_path)
#     print("4B per byteload:")
#     sim_4B_bload_stats.pretty_print()

# def proc_1flo_4KB_per_bload_sim_outputs():
#     sim_output_4KB_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY + "ssird_1flo-10#-4000B-1000us_subpkt_multiflow_stdout.out"
#     sim_4KB_bload_stats, _ = count_cr_r_d_pkts_in_sim_stdout(sim_output_4KB_byteloads_path)
#     print("4KB per byteload")
#     sim_4KB_bload_stats.pretty_print()

# def proc_1flo_subpkt_exp_sim_outputs():
#     # 4B per byteload:
#     # Num Credit Req Pkts: 10000
#     # Num Credit Pkts: 10000
#     # Num Data Pkts: 9994
#     # Total Overheads (B): 2479520
#     # -----
#     # 4KB per byteload
#     # Num Credit Req Pkts: 10
#     # Num Credit Pkts: 30
#     # Num Data Pkts: 30
#     # Total Overheads (B): 5760

#     proc_1flo_4B_per_bload_sim_outputs()
#     print("-----")
#     proc_1flo_4KB_per_bload_sim_outputs()

# '''
# ======== 10 FLO SUBPKT EXPERIMENTS ========
# '''
# def proc_10flo_4B_per_bload_sim_outputs(): 
#     sim_output_4B_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY + "ssird_10flo-10000#-4B-1us_subpkt_multiflow_stdout.out"
#     sim_4B_bload_stats, _= count_cr_r_d_pkts_in_sim_stdout(sim_output_4B_byteloads_path)
#     print("4B per byteload:")
#     sim_4B_bload_stats.pretty_print()

# def proc_10flo_4KB_per_bload_sim_outputs():
#     sim_output_4KB_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY + "ssird_10flo-10#-4000B-1000us_subpkt_multiflow_stdout.out"
#     sim_4KB_bload_stats, _ = count_cr_r_d_pkts_in_sim_stdout(sim_output_4KB_byteloads_path)
#     print("4KB per byteload")
#     sim_4KB_bload_stats.pretty_print()

# def proc_10flo_subpkt_exp_sim_outputs():
#     # output:
#     # 4B per byteload:
#     # Num Credit Req Pkts: 100000
#     # Num Credit Pkts: 100000
#     # Num Data Pkts: 99947
#     # Total Overheads (B): 24795760
#     # -----
#     # 4KB per byteload
#     # Num Credit Req Pkts: 100
#     # Num Credit Pkts: 300
#     # Num Data Pkts: 300
#     # Total Overheads (B): 57600

#     proc_10flo_4B_per_bload_sim_outputs()
#     print("-----")
#     proc_10flo_4KB_per_bload_sim_outputs()

# def proc_10flo_subpkt_exp_sim_outputs_slowpace():
#     print("\n--- 10 FLO SLOWPACE: ---") 
#     title_addendum = "_subpkt_multiflow_slowpace"
#     num_byteloads_list = [10000, 1000, 100, 10]
#     byteload_size_B_list = [4, 40, 400, 4000]
#     inter_byteload_period_us_list = [1, 10, 100, 1000]
#     nw_overheads_theoretical_15flo_B_list, _ = process_ssird_sim_outputs(10, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, REL_PATH_TO_EXP_FAMILY_SLOWPACE, title_addendum)
#     nw_overheads_measured_15flo_B_list = [33335286.23, 3463891.25, 475893.74, 82826.25]
#     measured_vs_theoretical_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_15flo_B_list, nw_overheads_theoretical_15flo_B_list)]
#     print(measured_vs_theoretical_ratio)


def process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family, title_addendum=""):
    assert(len(set([
        len(num_byteloads_list),
        len(byteload_size_B_list),
        len(inter_byteload_period_us_list)
    ])) == 1)
    num_experiments = len(num_byteloads_list)

    nw_overheads_B_list = [] 
    nw_overheads_s_to_r_only_B_list = []
    actual_app_thrpt_gbps = []
    for i in range(0, num_experiments):
        print(f"bload_size={byteload_size_B_list[i]}B, interval={inter_byteload_period_us_list[i]}us")

        experiment_name = dale_experiment_rig.Experiment.get_experiment_name(num_flows, num_byteloads_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i]) + title_addendum
        sim_output_path = PATH_TO_SIM_OUTPUTS + rel_path_to_exp_family + f"ssird_{experiment_name}_stdout.out" 
        
        # Get theoretical overheads
        sim_stats_nw_overall, sim_stats_p2p_only = count_cr_r_d_pkts_in_sim_stdout(sim_output_path)
        nw_overheads_B_list.append(sim_stats_nw_overall.total_overheads_B)
        nw_overheads_s_to_r_only_B_list.append(sim_stats_p2p_only.total_overheads_sendr_to_recvr_B)
        print(f"{byteload_size_B_list[i]}B per byteload:")
        print(f"* NW Overall:")
        sim_stats_nw_overall.pretty_print()
        print(f"* P2P Only:")
        sim_stats_p2p_only.pretty_print()
        print("---")

        # Get SSIRD sender actual gdpt (data)
        data_send_stats = get_actual_sender_gdpt_bps(sim_output_path)
        actual_app_thrpt_gbps.append(data_send_stats.thrpt_bps)
        print(f"Sender: DATA Gdpt (Gbps): {data_send_stats.thrpt_bps/pow(10,9)}, data sent (B): {data_send_stats.total_data_sent_B}, Start timestamp (s): {data_send_stats.start_time_s}, End timestamp (s) {data_send_stats.end_time_s}, Data pkts count: {data_send_stats.count_d_pkts}")

        # Get SSIRD sender credit (data) send rate
        credit_data_send_stats = get_credit_data_send_rate_bps(sim_output_path)
        print(f"Receiver: Credit DATA Send Rate (Gbps): {credit_data_send_stats.credit_rate_bps/pow(10,9)}, credit data sent (B): {credit_data_send_stats.total_credit_B}, Start timestamp (s): {credit_data_send_stats.start_time_s}, End timestamp (s) {credit_data_send_stats.end_time_s}, Credit pkts count: {credit_data_send_stats.count_credit_pkts}")

        # Get SSIRD sender credit (data) recv rate
        credit_data_recv_stats = get_credit_data_recv_rate_bps(sim_output_path)
        print(f"Sender: Credit DATA Recv Rate (Gbps): {credit_data_recv_stats.credit_rate_bps/pow(10,9)}, credit data recv (B): {credit_data_recv_stats.total_credit_B}, Start timestamp (s): {credit_data_recv_stats.start_time_s}, End timestamp (s) {credit_data_recv_stats.end_time_s}, Credit pkts count: {credit_data_recv_stats.count_credit_pkts}")

        print(f"DATA CREDITS RECV BYTES = {credit_data_recv_stats.total_credit_B}, DATA CREDITS USED BYTES = {data_send_stats.total_data_sent_B}, DIFF = {credit_data_recv_stats.total_credit_B - data_send_stats.total_data_sent_B}")

        plot_c_d_timeseries_cumu(f"DATA_ONLY_{experiment_name}", credit_data_send_stats.timestamps_s_list, credit_data_send_stats.credit_cumu_B_list, credit_data_recv_stats.timestamps_s_list, credit_data_recv_stats.credit_cumu_B_list, data_send_stats.timestamps_s_list, data_send_stats.data_sent_cumu_B_list, title_addendum)

        print("===")

        # Get SSIRD sender thrpt
        data_send_raw_stats = get_actual_sender_thrpt_bps(sim_output_path)
        print(f"Sender: RAW Thrpt (Gbps): {data_send_raw_stats.thrpt_bps/pow(10,9)}, data+hdrs sent (B): {data_send_raw_stats.total_data_sent_B}, Start timestamp (s): {data_send_raw_stats.start_time_s}, End timestamp (s) {data_send_raw_stats.end_time_s}, Credit pkts count: {data_send_raw_stats.count_d_pkts}")

        # Get SSIRD sender credit (raw) send rate
        credit_send_stats = get_credit_send_rate_bps(sim_output_path)
        print(f"Receiver: Credit RAW Send Rate (Gbps): {credit_send_stats.credit_rate_bps/pow(10,9)}, credit sent (B): {credit_send_stats.total_credit_B}, Start timestamp (s): {credit_send_stats.start_time_s}, End timestamp (s) {credit_send_stats.end_time_s}, Credit pkts count: {credit_send_stats.count_credit_pkts}")

        # Get SSIRD sender credit(raw) recv rate
        credit_recv_stats = get_credit_recv_rate_bps(sim_output_path)
        print(f"Sender: Credit RAW Recv Rate (Gbps): {credit_recv_stats.credit_rate_bps/pow(10,9)}, credit recv (B): {credit_recv_stats.total_credit_B}, Start timestamp (s): {credit_recv_stats.start_time_s}, End timestamp (s) {credit_recv_stats.end_time_s}, Credit pkts count: {credit_recv_stats.count_credit_pkts}")

        print(f"TOTAL CREDITS RECV BYTES = {credit_recv_stats.total_credit_B}, TOTAL CREDITS USED BYTES = {data_send_raw_stats.total_data_sent_B}, DIFF = {credit_recv_stats.total_credit_B - data_send_raw_stats.total_data_sent_B}")

        plot_c_d_timeseries_cumu(f"RAW_{experiment_name}", credit_send_stats.timestamps_s_list, credit_send_stats.credit_cumu_B_list, credit_recv_stats.timestamps_s_list, credit_recv_stats.credit_cumu_B_list, data_send_raw_stats.timestamps_s_list, data_send_raw_stats.data_sent_cumu_B_list, title_addendum)

        print("##########")

    return nw_overheads_B_list, nw_overheads_s_to_r_only_B_list, actual_app_thrpt_gbps

def plot_c_d_timeseries_cumu(plot_name, c_sent_timestamps_s_list, c_sent_cumu_B_list, c_recv_timestamps_s_list, c_recv_cumu_B_list, d_sent_timestamps_s_list, d_sent_cumu_B_list, title_addendum):
    sim_start_time_s = 10
    # Convert to pandas series and aggregate values with the same timestamp together
    c_sent_time_series_cumu = pd.Series(c_sent_cumu_B_list, index=[(t-sim_start_time_s)*1000 for t in c_sent_timestamps_s_list]).groupby(level=0).sum()
    c_recv_time_series_cumu = pd.Series(c_recv_cumu_B_list, index=[(t-sim_start_time_s)*1000 for t in c_recv_timestamps_s_list]).groupby(level=0).sum()
    d_sent_time_series_cumu = pd.Series(d_sent_cumu_B_list, index=[(t-sim_start_time_s)*1000 for t in d_sent_timestamps_s_list]).groupby(level=0).sum()

    # Get the union of all time series
    all_times = c_sent_time_series_cumu.index.union(c_recv_time_series_cumu.index).union(d_sent_time_series_cumu.index)

    # Reindex each series to include all times, filling missing value with Nan and then forward-fill
    c_sent_time_series_cumu_aligned = c_sent_time_series_cumu.reindex(all_times).ffill().fillna(0)
    c_recv_time_series_cumu_aligned = c_recv_time_series_cumu.reindex(all_times).ffill().fillna(0)
    d_sent_time_series_cumu_aligned = d_sent_time_series_cumu.reindex(all_times).ffill().fillna(0)

    # plot
    plt.figure(figsize=(10,6))
    plt.plot(c_sent_time_series_cumu_aligned, label="C Sent by Receiver")
    plt.plot(c_recv_time_series_cumu_aligned, label="C Recv by Sender")
    plt.plot(d_sent_time_series_cumu_aligned, label="D Sent by Sender")
    plt.xlabel('Time (ms)')
    plt.ylabel('Bytes (Cumulative) (B)')
    plt.title(f"Cumulative Credit pkt, Data pkt bytes exchanged btw Sender & Receiver\n{plot_name}")
    plt.legend()
    plt.grid(True)
    
    plt.xlim(left=0)

    plot_save_dir = f"{PATH_TO_PROC_SIM_OUTPUT_DIR}{title_addendum}/"
    Path(plot_save_dir).mkdir(parents=True, exist_ok=True)
    filename = f"{plot_name}_c_d_timeseries_cumu.png"
    plt.savefig(f"{plot_save_dir}{filename}")
    plt.close()

'''
======== 15 FLO SUBPKT FASTPACE EXPERIMENTS ========
'''

def proc_15flo_4B_per_bload_sim_outputs(): 
    experiment_name = dale_experiment_rig.Experiment.get_experiment_name(num_flows=15, num_byteloads=10000, byteload_size_B=4, inter_byteload_period_us=0.01)
    sim_output_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY_FASTPACE + f"ssird_{experiment_name}_subpkt_multiflow_fastpace_stdout.out" #"ssird_15flo-10000#-4B-10ns_subpkt_multiflow_fastpace_stdout.out"
    sim_stats, _ = count_cr_r_d_pkts_in_sim_stdout(sim_output_path)
    print("4B per byteload:")
    sim_stats.pretty_print()

def proc_15flo_4KB_per_bload_sim_outputs():
    sim_output_4KB_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY_FASTPACE + "ssird_15flo-10#-4000B-10000ns_subpkt_multiflow_fastpace_stdout.out"
    sim_4KB_bload_stats, _ = count_cr_r_d_pkts_in_sim_stdout(sim_output_4KB_byteloads_path)
    print("4KB per byteload")
    sim_4KB_bload_stats.pretty_print()

def proc_15flo_subpkt_exp_sim_outputs_fastpace():
    print("\n--- 15 FLO FASTPACE: ---")
    title_addendum = "_subpkt_multiflow_fastpace"
    num_byteloads_list = [10000, 1000, 100, 10]
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [0.01, 0.1, 1.0, 10.0]
    nw_overheads_theory_total_15flo_B_list, nw_overheads_theory_s_to_r_15flo_B_list, _ = process_ssird_sim_outputs(15, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, REL_PATH_TO_EXP_FAMILY_FASTPACE, title_addendum)
    nw_overheads_measured_total_15flo_B_list = [4337187.5, 1379893.75, 600348.75, 121467.5]
    nw_overheads_measured_s_to_r_15flo_B_list = [4235785.0, 1294872.5, 300791.25, 60220.0]
    measured_vs_theoretical_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_total_15flo_B_list, nw_overheads_theory_total_15flo_B_list)]
    measured_vs_theoretical_s_to_r_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_s_to_r_15flo_B_list, nw_overheads_theory_s_to_r_15flo_B_list)]
    print(f"Total: {measured_vs_theoretical_ratio}")
    print(f"Sendr to Recvr only: {measured_vs_theoretical_s_to_r_ratio}")

def proc_15flo_subpkt_exp_sim_outputs_slowpace():
    print("\n--- 15 FLO SLOWPACE: ---") 
    title_addendum = "_subpkt_multiflow_slowpace"
    num_byteloads_list = [10000, 1000, 100, 10]
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [1, 10, 100, 1000]
    nw_overheads_theoretical_15flo_B_list, _, _ = process_ssird_sim_outputs(15, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, REL_PATH_TO_EXP_FAMILY_SLOWPACE, title_addendum)
    nw_overheads_measured_15flo_B_list = [49931017.46, 5123891.25, 641893.75, 124286.25]
    measured_vs_theoretical_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_15flo_B_list, nw_overheads_theoretical_15flo_B_list)]
    print(measured_vs_theoretical_ratio)


def proc_15flow_subpkt_exp_sim_outputs_fastpace_extended():

    print("\n--- 15 FLO SUBPKT FASTPACE (EXTENDED): ---") 
    title_addendum = "_subpkt_multiflow_fastpace_extended"
    num_byteloads_list = [10000, 1000, 100, 10, 1]
    byteload_size_B_list = [4, 40, 400, 4000, 40000]
    inter_byteload_period_us_list = [0.01, 0.1, 1.0, 10.0, 100.0]

    nw_overheads_theory_total_B_list, nw_overheads_theory_s_to_r_B_list, _ = process_ssird_sim_outputs(15, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, REL_PATH_TO_EXP_FAMILY_FASTPACE_EXTENDED, title_addendum)
    
    nw_overheads_measured_total_B_list = [4337187.5, 1379893.75, 600348.75, 121467.5, 73920.0]
    nw_overheads_measured_s_to_r_B_list = [4235785.0, 1294872.5, 300791.25, 60220.0, 36105.0]

    measured_vs_theoretical_total_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_total_B_list, nw_overheads_theory_total_B_list)]
    measured_vs_theoretical_s_to_r_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_s_to_r_B_list, nw_overheads_theory_s_to_r_B_list)]

    print(f"Total: {measured_vs_theoretical_total_ratio}")
    print(f"Sendr to Recvr only: {measured_vs_theoretical_s_to_r_ratio}")

def proc_31flow_largepkt_exp_sim_outputs_fastpace_extended():

    print("\n--- 31 FLO LARGEPKT (EXTENDED) 49.6Gbps: ---")
    title_addendum = "_largepkt_multiflow_extended_31flo"
    rel_path_to_exp_family_output_dir = "FCT_Large_Byteloads_largepkt_multiflow_extended_31flo/"
    num_flows = 31
    num_byteloads_list = [10000, 1000, 100, 10, 1]
    byteload_size_B_list = [200, 2000, 20000, 200000, 2000000]
    inter_byteload_period_us_list = [1.0, 10.0, 100.0, 1000.0, 10000.0]

    nw_overheads_theory_total_B_list, nw_overheads_theory_s_to_r_B_list, _ = process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

    nw_overheads_measured_total_B_list = [93441891.13, 15464813.7, 7783916.2, 7121309.95, 6987276.2]
    nw_overheads_measured_s_to_r_B_list = [47878407.42, 7628427.45, 3804767.45, 3473483.7, 3406948.7]

    measured_vs_theoretical_total_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_total_B_list, nw_overheads_theory_total_B_list)]
    measured_vs_theoretical_s_to_r_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_s_to_r_B_list, nw_overheads_theory_s_to_r_B_list)]

    print(f"Total Overheads (B): {measured_vs_theoretical_total_ratio}")
    print(f"Sendr to Recvr Only Overheads (B): {measured_vs_theoretical_s_to_r_ratio}")

''' ----- FULLRANGE EXPERIMENTS ----- '''

def proc_31flow_fullrange_exp_sim_outputs():

    print("\n--- 31 FLO FULLRANGE 49.6Gbps: ---")
    title_addendum = "_fullrange_31flo"
    rel_path_to_exp_family_output_dir = "FCT_Fullrange_Byteloads_fullrange_31flo/"
    num_flows = 31
    num_byteloads_list = [10000, 1000, 100, 10, 1]
    byteload_size_B_list = [20, 200, 2000, 20000, 200000]
    inter_byteload_period_us_list = [0.1, 1.0, 10.0, 100.0, 1000.0]

    nw_overheads_theory_total_B_list, nw_overheads_theory_s_to_r_B_list, _ = process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

    nw_overheads_measured_total_B_list = [26805846.22, 9423469.99, 1666364.99, 815961.24, 712132.5]
    nw_overheads_measured_s_to_r_B_list = [26385364.98, 4828567.49, 823059.99, 399261.24, 347348.75]

    measured_vs_theoretical_total_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_total_B_list, nw_overheads_theory_total_B_list)]
    measured_vs_theoretical_s_to_r_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_s_to_r_B_list, nw_overheads_theory_s_to_r_B_list)]

    print(f"Total: {measured_vs_theoretical_total_ratio}")
    print(f"Sendr to Recvr only: {measured_vs_theoretical_s_to_r_ratio}")

def proc_5flo_fullrange_exp_sim_outputs_5usRTT():
    print("\n--- 5 FLO FULLRANGE 8Gbps RTT=5us: ---")
    title_addendum = "_fullrange_5flo_8gbps_total"
    rel_path_to_exp_family_output_dir = "FCT_Fullrange_Byteloads_fullrange_5flo_8gbps_total/"
    num_flows = 5
    num_byteloads_list = [10000, 1000, 100, 10, 1]
    byteload_size_B_list = [20, 200, 2000, 20000, 200000]
    inter_byteload_period_us_list = [0.1, 1.0, 10.0, 100.0, 1000.0]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_5flo_fullrange_exp_sim_outputs_1msRTT():

    print("\n--- 5 FLO FULLRANGE 8Gbps RTT=1ms: ---")
    title_addendum = "_fullrange_5flo_8gbps_total_1msRTT"
    rel_path_to_exp_family_output_dir = "FCT_Fullrange_Byteloads_fullrange_5flo_8gbps_total_1msRTT/"
    num_flows = 5
    num_byteloads_list = [10000, 1000, 100, 10, 1]
    byteload_size_B_list = [20, 200, 2000, 20000, 200000]
    inter_byteload_period_us_list = [0.1, 1.0, 10.0, 100.0, 1000.0]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_1flo_fullrange_exp_sim_outputs_5usRTT():
    print("\n--- 1 FLO FULLRANGE 1.6Gbps RTT=5us: ---")
    title_addendum = "_fullrange_1flo_1pt6gbps_total"
    rel_path_to_exp_family_output_dir = "FCT_Fullrange_Byteloads_fullrange_1flo_1pt6gbps_total/"
    num_flows = 1
    num_byteloads_list = [10000, 1000, 100, 10, 1]
    byteload_size_B_list = [20, 200, 2000, 20000, 200000]
    inter_byteload_period_us_list = [0.1, 1.0, 10.0, 100.0, 1000.0]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_1flo_fullrange_exp_sim_outputs_1msRTT():

    print("\n--- 1 FLO FULLRANGE 1.6Gbps RTT=1ms: ---")
    title_addendum = "_fullrange_1flo_1pt6gbps_total_1msRTT"
    rel_path_to_exp_family_output_dir = "FCT_Fullrange_Byteloads_fullrange_1flo_1pt6gbps_total_1msRTT/"
    num_flows = 1
    num_byteloads_list = [10000, 1000, 100, 10, 1]
    byteload_size_B_list = [20, 200, 2000, 20000, 200000]
    inter_byteload_period_us_list = [0.1, 1.0, 10.0, 100.0, 1000.0]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

''' ----- OTHER EXPERIMENTS ----- '''

def proc_5flo_large_bload_8gbps_exp_sim_outputs_1msRTT():

    print("\n--- 5 FLO FULLRANGE 8Gbps RTT=1ms: ---")
    title_addendum = "_large_bload_20MBflo_5flo_8gbps_total_1msRTT"
    rel_path_to_exp_family_output_dir = "FCT_LARGE_Byteloads_SSIRD_ONLY_large_bload_20MBflo_5flo_8gbps_total_1msRTT/"
    num_flows = 5
    num_byteloads_list = [10000, 1000, 100, 10, 1]
    byteload_size_B_list = [2000, 20000, 200000, 2000000, 20000000]
    inter_byteload_period_us_list = [10.0, 100.0, 1000.0, 10000.0, 100000.0]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_5flo_test_vary_bload_num_1msRTT():
    print("\nTESTING: 5FLO VARY BLOAD NUMBER (1ms RTT)")
    title_addendum = "_vary_num_bload_5flo_1msRTT"
    rel_path_to_exp_family_output_dir = "FCT_VARY_NUM_BLOAD_vary_num_bload_5flo_1msRTT/"

    num_flows = 5
    inter_byteload_period_us_list = [10.0, 10.0, 10.0]
    num_byteloads_list = [10000, 1000, 100]
    byteload_size_B_list = [20, 200, 2000]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_5flo_test_vary_bload_size_1msRTT():
    print("\nTESTING: 5FLO VARY BLOAD SIZE (1ms RTT)")
    title_addendum = "_vary_bload_size_5flo_1msRTT"
    rel_path_to_exp_family_output_dir = "FCT_VARY_BLOAD_SIZE_vary_bload_size_5flo_1msRTT/"

    num_flows = 5
    inter_byteload_period_us_list = [10.0, 10.0, 10.0]
    num_byteloads_list = [100, 100, 100]
    byteload_size_B_list = [20, 200, 2000]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_5flo_test_vary_interval_1msRTT():
    # INFO:__main__:Total Flow Size (Bytes): 200000
    # INFO:__main__:Byteload Size (Bytes): [20, 20, 20, 20]
    # INFO:__main__:Num Byteloads: [10000, 10000, 10000, 10000]
    # INFO:__main__:Intervals (us): [0.01, 0.1, 1, 10]
    # INFO:__main__:Num flows: 5
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [80.0, 8.0, 0.8, 0.08]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [80.00640063949119, 8.000640064005973, 0.8000640064005973, 0.080006400640064]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [80.00640063949119, 8.000640064005973, 0.8000640064005973, 0.080006400640064]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[15.999999999885446, 15.999999999885446, 15.999999999885446, 15.999999999885446, 15.999999999885446], [1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146], [0.15999999999999145, 0.15999999999999145, 0.15999999999999145, 0.15999999999999145, 0.15999999999999145], [0.015999999999999997, 0.015999999999999997, 0.015999999999999997, 0.015999999999999997, 0.015999999999999997]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[15.999999999885446, 15.999999999885446, 15.999999999885446, 15.999999999885446, 15.999999999885446], [1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146], [0.15999999999999145, 0.15999999999999145, 0.15999999999999145, 0.15999999999999145, 0.15999999999999145], [0.015999999999999997, 0.015999999999999997, 0.015999999999999997, 0.015999999999999997, 0.015999999999999997]]
    # INFO:__main__:* Sim duration (SSIRD): [0.0015, 0.002, 0.02, 0.12]
    # INFO:__main__:* Sim duration (DCTCP): [0.02, 0.02, 0.2, 0.3]
    # INFO:__main__:* SSIRD FCT: [[0.001517223000000456, 0.0015341060000011453, 0.0015509890000000581, 0.0015678720000007473, 0.0015847560000015193], [0.0015424730000006548, 0.0015846530000001025, 0.001626863000000256, 0.0016690730000004095, 0.0017112530000016335], [0.01049907600000033, 0.010499106000001035, 0.010499135999999964, 0.01049917300000125, 0.010499203000000179], [0.10049007799999998, 0.10049010800000069, 0.1004901380000014, 0.1004901750000009, 0.10049020500000161]]
    # INFO:__main__:* DCTCP FCT: [[0.0008919770000002103, 0.0008919840000007895, 0.0008919920000014514, 0.000892000000000337, 0.0008920080000009989], [0.001499916000000212, 0.001499924000000874, 0.0014999310000014532, 0.0014999390000003388, 0.0014999470000010007], [0.010499016000000694, 0.010499024000001356, 0.010499031000000159, 0.01049903900000082, 0.010499047000001482], [0.10049001600000018, 0.10049002400000084, 0.10049003100000142, 0.10049003900000031, 0.10049004700000097]]
    print("\nTESTING: 5FLO VARY BLOAD INTERVAL (1ms RTT)")
    title_addendum = "_vary_interval_5flo_1msRTT"
    rel_path_to_exp_family_output_dir = "FCT_VARY_INTERVAL_vary_interval_5flo_1msRTT/"

    num_flows = 5
    inter_byteload_period_us_list = [0.01, 0.1, 1, 10]
    num_byteloads_list = [10000, 10000, 10000, 10000]
    byteload_size_B_list = [20, 20, 20, 20]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_normal_bloads_1458B_8flo_99pt312Gbps_5usRTT():
    print("\nNormal Bloads: 1458B, 8Flo, 99.312Gbps, 5usRTT")
    title_addendum = "_1458B_8flo_93pt312Gbps"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1458B_8flo_93pt312Gbps/"

    num_flows = 8
    inter_byteload_period_us_list = [1]
    num_byteloads_list = [100]
    byteload_size_B_list = [1458]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_normal_bloads_1458B_8flo_99pt312Gbps_1msRTT():
    print("\nNormal Bloads: 1458B, 8Flo, 99.312Gbps, 1msRTT")
    title_addendum = "_1458B_8flo_93pt312Gbps_1msRTT"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1458B_8flo_93pt312Gbps_1msRTT/"

    num_flows = 8
    inter_byteload_period_us_list = [1]
    num_byteloads_list = [100]
    byteload_size_B_list = [1458]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_normal_bloads_1458B_85flo_99pt144Gbps_5usRTT():
    print("\nNormal Bloads: 1458B, 85Flo, 99.144Gbps, 5usRTT")
    title_addendum = "_1458B_85flo_99pt144Gbps"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1458B_85flo_99pt144Gbps/"

    num_flows = 85
    inter_byteload_period_us_list = [10]
    num_byteloads_list = [100]
    byteload_size_B_list = [1458]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_normal_bloads_1458B_85flo_99pt144Gbps_1msRTT():
    print("\nNormal Bloads: 1458B, 85Flo, 99.144Gbps, 1msRTT")
    title_addendum = "_1458B_85flo_99pt144Gbps_1msRTT"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1458B_85flo_99pt144Gbps_1msRTT/"

    num_flows = 85
    inter_byteload_period_us_list = [10]
    num_byteloads_list = [100]
    byteload_size_B_list = [1458]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_normal_bloads_1560B_8flo_99pt84Gbps_5usRTT():
    print("\nNormal Bloads: 1560B, 8Flo, 99.84Gbps, 5usRTT")
    title_addendum = "_1560B_8flo_99pt84Gbps"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1560B_8flo_99pt84Gbps/"

    num_flows = 8
    inter_byteload_period_us_list = [1]
    num_byteloads_list = [100]
    byteload_size_B_list = [1560]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_normal_bloads_1560B_8flo_99pt84Gbps_1msRTT():
    print("\nNormal Bloads: 1560B, 8Flo, 99.84Gbps, 1msRTT")
    title_addendum = "_1560B_8flo_99pt84Gbps_1msRTT"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1560B_8flo_99pt84Gbps_1msRTT/"

    num_flows = 8
    inter_byteload_period_us_list = [1]
    num_byteloads_list = [100]
    byteload_size_B_list = [1560]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_credit_leak_investigation_1458B_1flo_5usRTT():
    print("\nCredit leak Investigation: 1458B, 10us, 1Flo, 5usRTT")
    title_addendum = "_1458B_1flo_credit_leak"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1458B_1flo_credit_leak/"

    num_flows = 1
    inter_byteload_period_us_list = [10]
    num_byteloads_list = [5]
    byteload_size_B_list = [1458]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_credit_leak_investigation_1458B_1flo_1msRTT():
    print("\nCredit leak Investigation: 1458B, 10us, 1Flo, 1msRTT")
    title_addendum = "_1458B_1flo_credit_leak_1msRTT"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1458B_1flo_credit_leak_1msRTT/"

    num_flows = 1
    inter_byteload_period_us_list = [10]
    num_byteloads_list = [5]
    byteload_size_B_list = [1458]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_credit_leak_investigation_1462B_1flo_5usRTT():
    print("\nCredit leak Investigation: 1462B, 10us, 1Flo, 5usRTT")
    title_addendum = "_1462B_1flo_3bload_credit_leak_test"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1462B_1flo_3bload_credit_leak_test/"

    num_flows = 1
    inter_byteload_period_us_list = [10]
    num_byteloads_list = [3]
    byteload_size_B_list = [1462]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_credit_leak_investigation_1462B_5flo_5usRTT():
    print("\nCredit leak Investigation: 1462B, 10us, 5Flo, 5usRTT")
    title_addendum = "_1462B_5flo_3bload_credit_leak_test"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1462B_5flo_3bload_credit_leak_test/"

    num_flows = 5
    inter_byteload_period_us_list = [10]
    num_byteloads_list = [3]
    byteload_size_B_list = [1462]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_credit_leak_investigation_1462B_1flo_1msRTT():
    print("\nCredit leak Investigation: 1462B, 10us, 1Flo, 1msRTT")
    title_addendum = "_1462B_1flo_3bload_credit_leak_1msRTT_test"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1462B_1flo_3bload_credit_leak_1msRTT_test/"

    num_flows = 1
    inter_byteload_period_us_list = [10]
    num_byteloads_list = [3]
    byteload_size_B_list = [1462]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_credit_leak_investigation_1462B_5flo_1msRTT():
    print("\nCredit leak Investigation: 1462B, 10us, 5Flo, 1msRTT")
    title_addendum = "_1462B_5flo_3bload_credit_leak_1msRTT_test"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1462B_5flo_3bload_credit_leak_1msRTT_test/"

    num_flows = 5
    inter_byteload_period_us_list = [10]
    num_byteloads_list = [3]
    byteload_size_B_list = [1462]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

if __name__ == "__main__":
    ## proc_1flo_subpkt_exp_sim_outputs()
    ## proc_10flo_subpkt_exp_sim_outputs()

    # analysing 10 flow subpkt experiment (slowpace)
    ## proc_10flo_subpkt_exp_sim_outputs_slowpace()

    # analysing 15 flow subpkt experiment (fastpace)
    ## proc_15flo_subpkt_exp_sim_outputs_slowpace()
    ## proc_15flo_subpkt_exp_sim_outputs_fastpace()
    # proc_15flow_subpkt_exp_sim_outputs_fastpace_extended()

    # analysing 31 flow large pkt experiment
    ## proc_31flow_largepkt_exp_sim_outputs_fastpace_extended()
    # proc_31flow_fullrange_exp_sim_outputs()

    # 1RTT verification experiments ---
    ## proc_5flo_large_bload_8gbps_exp_sim_outputs_1msRTT()
    proc_5flo_fullrange_exp_sim_outputs_5usRTT()
    proc_5flo_fullrange_exp_sim_outputs_1msRTT()
    # proc_1flo_fullrange_exp_sim_outputs_5usRTT()
    # proc_1flo_fullrange_exp_sim_outputs_1msRTT()

    # proc_5flo_test_vary_bload_num_1msRTT()
    # proc_5flo_test_vary_bload_size_1msRTT()
    # proc_5flo_test_vary_interval_1msRTT()

    # ''' Normal Bload Size Experiments (RTT = 5us) --- '''
    # proc_normal_bloads_1458B_8flo_99pt312Gbps_5usRTT()
    # proc_normal_bloads_1560B_8flo_99pt84Gbps_5usRTT()
    # proc_normal_bloads_1458B_85flo_99pt144Gbps_5usRTT()

    # ''' Normal Bload Size Experiments (RTT = 1ms) --- '''
    # proc_normal_bloads_1458B_8flo_99pt312Gbps_1msRTT()
    # proc_normal_bloads_1560B_8flo_99pt84Gbps_1msRTT()
    # proc_normal_bloads_1458B_85flo_99pt144Gbps_1msRTT()

    # ''' --- CREDIT LEAK INVESTIGATION (RTT = 5us) ---'''
    # # proc_credit_leak_investigation_1458B_1flo_5usRTT()
    # proc_credit_leak_investigation_1462B_1flo_5usRTT()
    # proc_credit_leak_investigation_1462B_5flo_5usRTT()
    # proc_1flo_fullrange_exp_sim_outputs_5usRTT()
    # proc_5flo_fullrange_exp_sim_outputs_5usRTT()

    # ''' --- CREDIT LEAK INVESTIGATION (RTT = 1ms) --- '''
    # # proc_credit_leak_investigation_1458B_1flo_1msRTT()
    # proc_credit_leak_investigation_1462B_1flo_1msRTT()
    # proc_credit_leak_investigation_1462B_5flo_1msRTT()
    # proc_1flo_fullrange_exp_sim_outputs_1msRTT()
    # proc_5flo_fullrange_exp_sim_outputs_1msRTT()