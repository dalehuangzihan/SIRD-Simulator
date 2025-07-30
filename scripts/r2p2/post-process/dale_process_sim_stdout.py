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
    # INFO:__main__:Total Flow Size (Bytes): 40000
    # INFO:__main__:Total Injection Period (us): 100.0
    # INFO:__main__:Byteload Size (Bytes): [4, 40, 400, 4000, 40000]
    # INFO:__main__:Num Byteloads: [10000, 1000, 100, 10, 1]
    # INFO:__main__:Intervals (us): [0.01, 0.1, 1.0, 10.0, 100.0]
    # INFO:__main__:Num flows: 15
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [48.0, 48.0, 48.0, 48.0, 48.0]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [48.00448044770111, 48.044844844664645, 48.452525252273034, 52.97777777769212, -1]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [48.00448044770111, 48.044844844664645, 48.452525252273034, 52.97777777769212, -1]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089], [3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982], [3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343], [3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826], [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089], [3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982], [3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343], [3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826], [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]]
    # INFO:__main__:* Sim duration (SSIRD): [0.02, 0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* Sim duration (DCTCP): [0.02, 0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* SSIRD FCT: [[0.0003420990000009283, 0.00034547899999992637, 0.00034886500000119725, 0.00035225100000069176, 0.00035563600000010354, 0.0003590220000013744, 0.0003624080000008689, 0.00036579400000036344, 0.0003691800000016343, 0.00037256600000112883, 0.00037595200000062334, 0.00037933800000011786, 0.00038272400000138873, 0.00038611000000088325, 0.00038949600000037776], [0.00010683200000016768, 0.00011021100000085937, 0.00011359700000035389, 0.00011698300000162476, 0.00012036900000111928, 0.0001237550000006138, 0.0001271410000001083, 0.00013052700000137918, 0.0001339130000008737, 0.0001372990000003682, 0.00014068499999986273, 0.0001440710000011336, 0.0001474570000006281, 0.0001508420000000399, 0.00015422800000131076], [0.00010167800000004945, 0.00010171600000141723, 0.00010175400000100865, 0.00010179300000068281, 0.00010183100000027423, 0.00010186999999994839, 0.00010190800000131617, 0.00010194600000090759, 0.00010198500000058175, 0.00010202300000017317, 0.00010206200000162369, 0.00010210000000121511, 0.00010213800000080653, 0.00010217700000048069, 0.00010513900000042042], [9.307800000080135e-05, 9.815200000140578e-05, 9.849800000161224e-05, 9.883700000123952e-05, 9.917700000094953e-05, 9.951600000057681e-05, 9.985500000020409e-05, 0.00010019400000160772, 0.000100533000001235, 0.00010087300000094501, 0.00010121200000057229, 0.00010155100000019956, 0.0001018900000016032, 0.00010222900000123047, 0.00010294900000040741], [1.1102000000207113e-05, 1.4481000000898803e-05, 1.7867000000393318e-05, 2.1252999999887834e-05, 2.4639000001158706e-05, 2.8025000000653222e-05, 3.141100000014774e-05, 3.479700000141861e-05, 3.8183000000913125e-05, 4.156900000040764e-05, 4.4954999999902157e-05, 4.834100000117303e-05, 5.1727000000667545e-05, 5.511200000007932e-05, 5.849800000135019e-05]]
    # INFO:__main__:* DCTCP FCT: [[0.018869601000000458, 0.01886961300000145, 0.01886962600000075, 0.01886963900000005, 0.018869652000001125, 0.018869665000000424, 0.018869677000001417, 0.018869690000000716, 0.018869703000000015, 0.01886971600000109, 0.01886972900000039, 0.018869741000001383, 0.018869754000000682, 0.018869766999999982, 0.018869780000001057], [0.0018871410000009803, 0.0018871530000001968, 0.0018871660000012724, 0.0018871790000005717, 0.001887191999999871, 0.0018872050000009466, 0.0018872170000001631, 0.0018872300000012387, 0.001887243000000538, 0.0018872560000016136, 0.001887269000000913, 0.0018872810000001294, 0.001887294000001205, 0.0018873070000005043, 0.00188732000000158], [0.00019131400000027554, 0.00019135199999986696, 0.00019139000000123474, 0.00019142800000082616, 0.00019146700000050032, 0.00019150500000009174, 0.00019154300000145952, 0.00019158100000105094, 0.0001916200000007251, 0.00019165800000031652, 0.0001921230000014873, 0.00019216100000107872, 0.00019219900000067014, 0.00019223700000026156, 0.00019227599999993572], [9.296200000008525e-05, 9.330000000140615e-05, 9.363900000103342e-05, 9.39780000006607e-05, 9.431700000028798e-05, 9.465500000160887e-05, 9.499400000123615e-05, 9.533300000086342e-05, 9.56720000004907e-05, 9.601000000003523e-05, 9.634900000143887e-05, 9.668800000106614e-05, 9.702600000061068e-05, 9.736500000023796e-05, 9.770399999986523e-05], [5.998000000673187e-06, 9.372000000951175e-06, 1.2747000001311903e-05, 1.6121999999896275e-05, 1.9497000000257003e-05, 2.287100000053499e-05, 2.624600000089572e-05, 2.9621000001256448e-05, 3.2996000001617176e-05, 3.637000000011881e-05, 3.9745000000479536e-05, 4.3120000000840264e-05, 4.649400000111825e-05, 4.986900000147898e-05, 5.324400000006335e-05]]

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
    # INFO:__main__:Total Flow Size (Bytes): 2000000
    # INFO:__main__:Total Injection Period (us): 10000
    # INFO:__main__:Byteload Size (Bytes): [200, 2000, 20000, 200000, 2000000]
    # INFO:__main__:Num Byteloads: [10000, 1000, 100, 10, 1]
    # INFO:__main__:Intervals (us): [1.0, 10.0, 100.0, 1000.0, 10000.0]
    # INFO:__main__:Num flows: 31
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [49.6, 49.6, 49.6, 49.6, 49.6]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [49.604800480045355, 49.64804804804723, 50.084848484848386, 54.933333333331255, -1]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [49.604800480045355, 49.64804804804723, 50.084848484848386, 54.933333333331255, -1]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146], [1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737], [1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997], [1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395], [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146], [1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737, 1.5999999999999737], [1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997], [1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395, 1.5999999999999395], [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]]
    # INFO:__main__:* Sim duration (SSIRD): [0.02, 0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* Sim duration (DCTCP): [0.02, 0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* SSIRD FCT: [[0.010001875000000382, 0.010001995000001429, 0.01000223499999997, 0.010001935000000017, 0.010001776000001072, 0.010001821000001243, 0.010002695000000728, 0.010002295000001382, 0.010002325000000312, 0.010002084999999994, 0.0100021150000007, 0.010002025000000359, 0.010002205000001041, 0.010001965000000723, 0.010002505000000994, 0.010001798000001116, 0.010002475000000288, 0.010002265000000676, 0.010002175000000335, 0.010171495999999891, 0.010340277000000953, 0.010509058000000238, 0.010001845000001452, 0.010002355000001018, 0.010002145000001406, 0.010001753000000946, 0.010002055000001064, 0.010001905000001088, 0.010002384999999947, 0.010002445000001359, 0.010002415000000653], [0.010000810000001081, 0.010001846000001535, 0.010001674000001515, 0.009999773000000545, 0.009998212000001061, 0.009993350000000234, 0.010002191999999965, 0.010000464000000875, 0.009998557000001185, 0.009998736000000008, 0.010002018999999862, 0.010000118000000668, 0.009993004000000028, 0.009999082000000215, 0.009998909000000111, 0.010000291000000772, 0.009997866000000855, 0.009998384000001082, 0.010000982000001102, 0.009999427000000338, 0.00999317700000013, 0.009999254000000235, 0.010002365000000069, 0.009999600000000441, 0.010000637000000978, 0.010001155000001205, 0.009998039000000958, 0.010001501000001412, 0.009999946000000648, 0.010001328000001308, 0.010002538000000172], [0.009916161000001367, 0.009926297999999889, 0.009949953000001344, 0.009946574000000652, 0.009944884000001153, 0.009948263000000068, 0.009955022000001534, 0.009924609000000473, 0.009941505000000461, 0.009911060000000305, 0.009953333000000342, 0.009917850000000783, 0.009929678000000663, 0.009922919000000974, 0.009912782000000675, 0.009914471000000091, 0.009919540000000282, 0.009960090999999949, 0.009927988000001164, 0.009943193999999878, 0.009921230000001557, 0.009938126000001546, 0.00993136700000008, 0.009956712000001033, 0.009909353000001175, 0.00993643600000027, 0.009933057000001355, 0.00995164200000076, 0.009939815000000962, 0.009934746000000771, 0.009958402000000532], [0.009413096000001175, 0.00949754500000033, 0.009328646000000163, 0.009142857000000504, 0.009244197000001009, 0.009345536000001431, 0.009379316000000415, 0.00927797599999991, 0.009159746999999996, 0.00944687600000016, 0.009176637000001264, 0.00931175600000067, 0.00907529700000076, 0.009125967000001012, 0.00902454600000091, 0.009210417000000248, 0.009362426000000923, 0.009193527000000756, 0.00953132500000109, 0.009429986000000667, 0.009480655000000837, 0.009463766000001428, 0.009514435000001598, 0.0092610870000005, 0.009227307000001517, 0.009396205999999907, 0.009058407000001267, 0.00910907700000152, 0.009092187000000251, 0.009041518000000082, 0.009294866000001178], [0.0035522679999999696, 0.0011892430000006726, 0.0013580300000004542, 0.0015268180000003184, 0.0016956060000001827, 0.002033181000001605, 0.0022019680000013864, 0.0023707560000012506, 0.002539543000001032, 0.0027083310000008964, 0.0008516680000010268, 0.0006828800000011626, 0.004058631000001256, 0.0032146930000003238, 0.003383481000000188, 0.00372105600000161, 0.00017650400000057687, 0.0010204550000008084, 0.0042274180000010375, 0.0038898430000013917, 0.000514093000001381, 0.00034530500000151676, 0.0018643929999999642, 0.004396206000000902, 0.0030459060000005422, 0.002877118000000678, 0.004564993000000683, 0.004733781000000548, 0.004902568000000329, 0.005071356000000193, 0.005240142999999975]]
    # INFO:__main__:* DCTCP FCT: [[0.020298681999999957, 0.020298704, 0.020298727000000127, 0.02029874900000017, 0.020298771000000215, 0.02029879300000026, 0.020298816000000386, 0.02029883800000043, 0.020298860000000474, 0.020298882000000518, 0.02029890400000056, 0.02029892700000069, 0.020298949000000732, 0.020298971000000776, 0.02029899300000082, 0.020294463000000817, 0.02029448500000086, 0.020294507000000905, 0.02029452900000095, 0.020298415000000958, 0.020298437000001, 0.02029846000000113, 0.020298482000001172, 0.020298504000001216, 0.02029852600000126, 0.020298549000001387, 0.02029857100000143, 0.020298593000001475, 0.02029861500000152, 0.02029863799999987, 0.020298659999999913], [0.009992796000000581, 0.009992968000000602, 0.009993140000000622, 0.009993313000000725, 0.009993485000000746, 0.009993658000000849, 0.00999383000000087, 0.009994003000000973, 0.009994175000000993, 0.009994348000001096, 0.009994520000001117, 0.00999469300000122, 0.00999486500000124, 0.009995038000001344, 0.009995210000001364, 0.009995383000001468, 0.009995555000001488, 0.009995728000001591, 0.009995900000001612, 0.009996072999999939, 0.00999624499999996, 0.009996418000000062, 0.009996590000000083, 0.009996763000000186, 0.009996935000000207, 0.00999710800000031, 0.00999728000000033, 0.00999745200000035, 0.009997625000000454, 0.009997797000000475, 0.009997970000000578], [0.00990431000000136, 0.009905998000000693, 0.009907684999999944, 0.009909372000000971, 0.009911060000000305, 0.009912747000001332, 0.009914435000000665, 0.009916121999999916, 0.009917809000000943, 0.009919497000000277, 0.009921184000001304, 0.009922871000000555, 0.009924558999999888, 0.009926246000000916, 0.009927933000000166, 0.009929621000001276, 0.009931308000000527, 0.00993299599999986, 0.009934683000000888, 0.009936370000000139, 0.009938058000001249, 0.0099397450000005, 0.009941432000001527, 0.00994312000000086, 0.009944807000000111, 0.009946494000001138, 0.009948182000000472, 0.009949869000001499, 0.00995155600000075, 0.009953244000000083, 0.00995493100000111], [0.009397949000000239, 0.009474854000000477, 0.00951201200000007, 0.00951274800000057, 0.009513485000001154, 0.00951397500000084, 0.00951446600000061, 0.009528285000000025, 0.009528653000000276, 0.009529020000000443, 0.009529388000000694, 0.009529755000000861, 0.009530123000001112, 0.00953049000000128, 0.00953085800000153, 0.009531224999999921, 0.009531593000000171, 0.009531960000000339, 0.00953232800000059, 0.009532695000000757, 0.009533063000001007, 0.009533430000001175, 0.009526029999999963, 0.009526767000000547, 0.009527503000001047, 0.009505489000000367, 0.009505733000001015, 0.009527637000001477, 0.009527759000000913, 0.009527880000000266, 0.009511269000000766], [0.006056953999999948, 0.00574259100000063, 0.006099590999999904, 0.006105856000001353, 0.0061069250000009845, 0.0060616140000000485, 0.005992653000001624, 0.00602116300000155, 0.006008254000001045, 0.005965717000000481, 0.00589698700000163, 0.005926753000000673, 0.005869682000000154, 0.005926983000000163, 0.0054261910000015234, 0.0046150080000000315, 0.0049654160000009995, 0.005442914000001409, 0.0055182050000013305, 0.005703371000000956, 0.005718864000000323, 0.005718971000000295, 0.0059397749999998695, 0.0060358010000012285, 0.00594062100000059, 0.005996328000000162, 0.006087064000000808, 0.006076006000000689, 0.006088776000000351, 0.006115259000001316, 0.006091836000001294]]

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

def proc_31flow_fullrange_exp_sim_outputs():
    # INFO:__main__:Total Flow Size (Bytes): 200000
    # INFO:__main__:Total Injection Period (us): 1000.0
    # INFO:__main__:Byteload Size (Bytes): [20, 200, 2000, 20000, 200000]
    # INFO:__main__:Num Byteloads: [10000, 1000, 100, 10, 1]
    # INFO:__main__:Intervals (us): [0.1, 1.0, 10.0, 100.0, 1000.0]
    # INFO:__main__:Num flows: 31
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [49.6, 49.6, 49.6, 49.6, 49.6]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [49.604800480045355, 49.648048048038405, 50.084848484767505, 54.93333333324452, -1]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [49.604800480045355, 49.648048048038405, 50.084848484767505, 54.93333333324452, -1]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146], [1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892], [1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413], [1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413], [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146], [1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892], [1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413], [1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413], [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]]
    # INFO:__main__:* Sim duration (SSIRD): [0.02, 0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* Sim duration (DCTCP): [0.02, 0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* SSIRD FCT: [[0.002220966000001212, 0.002423645000000363, 0.002406755000000871, 0.002254746000000196, 0.0021196260000007072, 0.0021365160000001993, 0.0021534060000014676, 0.0021702960000009597, 0.0022040759999999437, 0.002237856000000704, 0.0022716360000014646, 0.0024912050000001074, 0.0024743150000006153, 0.0024574250000011233, 0.0023560850000006184, 0.002102736000001215, 0.0024405350000016313, 0.0026094340000000216, 0.0025925440000005295, 0.0025756540000010375, 0.0025587640000015455, 0.002541874000000277, 0.002524984000000785, 0.002508094000001293, 0.0022885260000009566, 0.002389865000001379, 0.0023729750000001104, 0.0021871860000004517, 0.002305415000000366, 0.0023223050000016343, 0.0023391950000011263], [0.001001875000000041, 0.001001995000001088, 0.0010022350000014058, 0.0010019350000014526, 0.0010017760000007314, 0.0010018200000008193, 0.0010026950000003865, 0.001002295000001041, 0.0010023249999999706, 0.0010020850000014292, 0.0010021150000003587, 0.0010020250000000175, 0.0010022050000007, 0.0010019650000003821, 0.001002505000000653, 0.0010017980000007753, 0.0010024749999999472, 0.0010022650000003352, 0.001002174999999994, 0.0010195990000010369, 0.0010364819999999497, 0.001053365000000639, 0.0010018450000011114, 0.0010023550000006765, 0.0010021450000010645, 0.0010017530000006047, 0.0010020550000007233, 0.0010019050000007468, 0.0010023850000013823, 0.0010024450000010177, 0.0010024150000003118], [0.0010024160000003945, 0.0010017250000000644, 0.0010025890000004978, 0.0010003430000011804, 0.001000688000001304, 0.0010022430000002913, 0.0010020710000002708, 0.0010028619999999933, 0.000998226000000102, 0.0009993060000006437, 0.0009989170000004322, 0.0009933939999999808, 0.0010005150000012009, 0.0009998240000008707, 0.0010015519999999611, 0.000998744000000329, 0.0009983990000002052, 0.0010001700000010771, 0.0009932209999998776, 0.0010012070000016138, 0.0009996510000007675, 0.000999997000000974, 0.000999479000000747, 0.0009991259999999613, 0.0010018980000001676, 0.0009930480000015507, 0.00099801600000049, 0.0010008610000014073, 0.0010013790000016343, 0.0010010340000015105, 0.0009985710000002257], [0.0009433080000000871, 0.0009263449999998841, 0.0009382190000000179, 0.0009127810000002512, 0.0009483970000001563, 0.0009399160000000961, 0.0009602720000003728, 0.0009331310000000315, 0.0009500940000002345, 0.0009246489999998886, 0.0009161670000015221, 0.0009297379999999578, 0.0009212560000015912, 0.0009551830000003037, 0.0009450050000001653, 0.0009229529999998931, 0.0009314339999999532, 0.0009144710000015266, 0.0009348270000000269, 0.0009365230000000224, 0.0009195600000015958, 0.0009110599999999636, 0.00095179000000023, 0.0009467010000001608, 0.0009534860000002254, 0.0009416120000000916, 0.0009568790000002991, 0.0009178640000016003, 0.0009280419999999623, 0.0009585750000002946, 0.0009093530000008343], [0.0002442560000002203, 0.0003118159999999648, 7.535700000005363e-05, 4.1577000001069564e-05, 5.84670000005616e-05, 0.00010913700000081406, 0.00014291700000157448, 0.0001260270000003061, 0.0001598070000010665, 0.00019358700000005058, 0.0004131560000004697, 0.00039626600000097767, 0.00037937600000148564, 0.0002780360000009807, 0.0002611460000014887, 0.00017669700000055855, 2.460600000020463e-05, 0.0003287060000012332, 0.0003455960000007252, 0.00036248600000021725, 0.0005313850000003839, 0.0005144950000008919, 0.0004976050000013998, 0.00048071500000013145, 0.0004638250000006394, 0.0004469350000011474, 0.00043004599999996174, 0.00021047700000131897, 0.00029492600000047275, 9.224700000132202e-05, 0.00022736600000072826]]
    # INFO:__main__:* DCTCP FCT: [[0.02029412400000119, 0.020294136000000407, 0.020294149000001482, 0.02029416200000078, 0.02029417500000008, 0.020294188000001157, 0.020294200000000373, 0.02029421300000145, 0.020294226000000748, 0.020298762000001247, 0.020298775000000546, 0.020298788000001622, 0.02029880000000084, 0.020298813000000138, 0.020298826000001213, 0.020298839000000513, 0.020298852000001588, 0.020298864000000805, 0.020298877000000104, 0.02029889000000118, 0.02029890300000048, 0.020298916000001554, 0.02029892800000077, 0.02029894100000007, 0.020298954000001146, 0.020298967000000445, 0.02029898000000152, 0.020298992000000737, 0.020294085000001516, 0.020294098000000815, 0.020294111000000115], [0.003922156999999871, 0.003922178999999915, 0.0039222009999999585, 0.003922224000000085, 0.003922246000000129, 0.003922268000000173, 0.003922290000000217, 0.003922312000000261, 0.003922335000000388, 0.0039223570000004315, 0.0039223790000004755, 0.003922401000000519, 0.003922424000000646, 0.00392244600000069, 0.003922468000000734, 0.003922490000000778, 0.0039225130000009045, 0.0039225350000009485, 0.003922557000000992, 0.003922579000001036, 0.003922602000001163, 0.003922624000001207, 0.003922957000000338, 0.003922979000000382, 0.003923001000000426, 0.0039230230000004696, 0.003923046000000596, 0.00392306800000064, 0.003923090000000684, 0.003923112000000728, 0.003923135000000855], [0.00099279600000024, 0.0009929680000002605, 0.000993140000000281, 0.0009933130000003842, 0.0009934850000004047, 0.000993658000000508, 0.0009938300000005285, 0.0009940030000006317, 0.0009941750000006522, 0.0009943480000007554, 0.000994520000000776, 0.0009946930000008791, 0.0009948650000008996, 0.0009950380000010028, 0.0009952100000010233, 0.0009953830000011266, 0.000995555000001147, 0.0009957280000012503, 0.0009959000000012708, 0.000996073000001374, 0.0009962450000013945, 0.0009964180000014977, 0.0009965900000015182, 0.0009967630000016214, 0.0009969349999998656, 0.0009971079999999688, 0.0009972799999999893, 0.0009974520000000098, 0.000997625000000113, 0.0009977970000001335, 0.0009979700000002367], [0.0009043100000010185, 0.000905998000000352, 0.0009076850000013792, 0.00090937200000063, 0.0009110599999999636, 0.0009127470000009907, 0.0009144350000003243, 0.0009161220000013515, 0.0009178090000006023, 0.0009194969999999358, 0.000921184000000963, 0.0009228710000002138, 0.0009245590000013237, 0.0009262460000005746, 0.0009279330000016017, 0.0009296210000009353, 0.0009313080000001861, 0.000932996000001296, 0.0009346830000005468, 0.000936370000001574, 0.0009380580000009076, 0.0009397450000001584, 0.0009414320000011855, 0.0009431200000005191, 0.0009448070000015463, 0.0009464940000007971, 0.0009481820000001306, 0.0009498690000011578, 0.0009515560000004086, 0.0009532440000015185, 0.0009549310000007694], [0.0005139760000005822, 0.0005225870000007404, 0.0005313210000004176, 0.0005400550000000948, 0.000548790000001631, 0.0005575240000013082, 0.0005662580000009854, 0.0005749920000006625, 0.0005837270000004224, 0.0005924610000000996, 0.0006011950000015531, 0.0006099290000012303, 0.0006186640000009902, 0.0006273980000006674, 0.0006361320000003445, 0.0006448660000000217, 0.0006534770000001799, 0.0006622119999999398, 0.0006708230000000981, 0.0006795570000015516, 0.0006882910000012288, 0.0006970260000009887, 0.0007058830000001848, 0.000714616999999862, 0.000799754000000874, 0.0008007430000009919, 0.0008017320000011097, 0.0008027210000012275, 0.0008037100000013453, 0.000804822000000982, 0.0008059340000006188]]

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
    # INFO:__main__:Total Flow Size (Bytes): 200000
    # INFO:__main__:Total Injection Period (us): 1000.0
    # INFO:__main__:Byteload Size (Bytes): [20, 200, 2000, 20000, 200000]
    # INFO:__main__:Num Byteloads: [10000, 1000, 100, 10, 1]
    # INFO:__main__:Intervals (us): [0.1, 1.0, 10.0, 100.0, 1000.0]
    # INFO:__main__:Num flows: 5
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [8.0, 8.0, 8.0, 8.0, 8.0]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [8.000640064005973, 8.006406406404851, 8.064646464633425, 8.711111111097027, -1]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [8.000640064005973, 8.006406406404851, 8.064646464633425, 8.711111111097027, -1]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146], [1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892], [1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413], [1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413], [None, None, None, None, None]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146, 1.5999999999999146], [1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892, 1.5999999999996892], [1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413], [1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413], [None, None, None, None, None]]
    # INFO:__main__:* Sim duration (SSIRD): [0.05, 0.05, 0.05, 0.05, 0.05]
    # INFO:__main__:* Sim duration (DCTCP): [0.25, 0.15, 0.15, 0.15, 0.15]
    # INFO:__main__:* SSIRD FCT: [[0.0018000960000001953, 0.0021000960000012725, 0.0024000960000005733, 0.002700095999999874, 0.0030000960000009513], [0.0016992350000002432, 0.0018992149999998986, 0.00209922500000026, 0.002299235000000621, 0.0024992150000002766], [0.0016911090000011342, 0.0018910890000007896, 0.002091099000001151, 0.002291109000001512, 0.0024910890000011676], [0.001608652000001598, 0.0018086320000012535, 0.0020086420000016147, 0.0022086520000001997, 0.0024086320000016315], [0.0015171160000004846, 0.0015339990000011738, 0.0015508830000001694, 0.0015677660000008586, 0.0015846490000015478]]
    # INFO:__main__:* DCTCP FCT: [[0.001499916000000212, 0.001499924000000874, 0.0014999310000014532, 0.0014999390000003388, 0.0014999470000010007], [0.001499044000000893, 0.0014990670000010198, 0.0014990890000010637, 0.0014991110000011076, 0.0014991330000011516], [0.0014902960000000576, 0.001490468000000078, 0.0014906400000000986, 0.0014908130000002018, 0.0014909850000002223], [0.001401810000000836, 0.0014034980000001696, 0.0014051850000011967, 0.0014068720000004475, 0.0014085600000015575], [0.0025011310000007114, 0.002509867000000554, 0.002518602000000314, 0.0025267230000007856, 0.0025348440000012573]]

    print("\n--- 5 FLO FULLRANGE 8Gbps RTT=1ms: ---")
    title_addendum = "_fullrange_5flo_8gbps_total_1msRTT"
    rel_path_to_exp_family_output_dir = "FCT_Fullrange_Byteloads_fullrange_5flo_8gbps_total_1msRTT/"
    num_flows = 5
    num_byteloads_list = [10000, 1000, 100, 10, 1]
    byteload_size_B_list = [20, 200, 2000, 20000, 200000]
    inter_byteload_period_us_list = [0.1, 1.0, 10.0, 100.0, 1000.0]

    # nw_overheads_theory_total_B_list, nw_overheads_theory_s_to_r_B_list, _ = process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

    # nw_overheads_measured_total_B_list = [8456442.49, 896117.5, 182478.75, 119482.5, 114861.25]
    # nw_overheads_measured_s_to_r_B_list = [4255605.0, 475280.0, 97641.25, 59807.5, 56025.0]

    # measured_vs_theoretical_total_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_total_B_list, nw_overheads_theory_total_B_list)]
    # measured_vs_theoretical_s_to_r_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_s_to_r_B_list, nw_overheads_theory_s_to_r_B_list)]

    # print(f"Total: {measured_vs_theoretical_total_ratio}")
    # print(f"Sendr to Recvr only: {measured_vs_theoretical_s_to_r_ratio}")
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
    # INFO:__main__:Total Flow Size (Bytes): 200000
    # INFO:__main__:Total Injection Period (us): 1000.0
    # INFO:__main__:Byteload Size (Bytes): [20, 200, 2000, 20000, 200000]
    # INFO:__main__:Num Byteloads: [10000, 1000, 100, 10, 1]
    # INFO:__main__:Intervals (us): [0.1, 1.0, 10.0, 100.0, 1000.0]
    # INFO:__main__:Num flows: 1
    # DEBUG:__main__:Flow start times (us): [0]
    # INFO:__main__:Gdpt Gbps theoretical: [1.6, 1.6, 1.6, 1.6, 1.6]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [1.5999999999999146, 1.5999999999996892, 1.599999999997413, 1.599999999997413, -1]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [None, None, None, None, None]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[1.5999999999999146], [1.5999999999996892], [1.599999999997413], [1.599999999997413], [None]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [None, None, None, None, None]
    # INFO:__main__:* Sim duration (SSIRD): [0.01, 0.01, 0.01, 0.01, 0.01]
    # INFO:__main__:* Sim duration (DCTCP): [0.25, 0.15, 0.15, 0.15, 0.15]
    # INFO:__main__:* SSIRD FCT: [[0.002499966000000242], [0.002499095000001006], [0.0024903460000000877], [0.0024018630000011143], [0.0015171160000004846]]
    # INFO:__main__:* DCTCP FCT: [None, None, None, None, None]

    print("\n--- 1 FLO FULLRANGE 1.6Gbps RTT=1ms: ---")
    title_addendum = "_fullrange_1flo_1pt6gbps_total_1msRTT"
    rel_path_to_exp_family_output_dir = "FCT_Fullrange_Byteloads_fullrange_1flo_1pt6gbps_total_1msRTT/"
    num_flows = 1
    num_byteloads_list = [10000, 1000, 100, 10, 1]
    byteload_size_B_list = [20, 200, 2000, 20000, 200000]
    inter_byteload_period_us_list = [0.1, 1.0, 10.0, 100.0, 1000.0]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_5flo_large_bload_8gbps_exp_sim_outputs_1msRTT():
    # INFO:__main__:Total Flow Size (Bytes): 20000000
    # INFO:__main__:Total Injection Period (us): 100000
    # INFO:__main__:Byteload Size (Bytes): [2000, 20000, 200000, 2000000, 20000000]
    # INFO:__main__:Num Byteloads: [10000, 1000, 100, 10, 1]
    # INFO:__main__:Intervals (us): [10.0, 100.0, 1000.0, 10000.0, 100000.0]
    # INFO:__main__:Num flows: 5
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [8.0, 8.0, 8.0, 8.0, 8.0]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [8.000640064006399, 8.006406406406416, 8.064646464646449, 8.711111111110952, -1]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [None, None, None, None, None]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[1.5999999999999996, 1.5999999999999996, 1.5999999999999996, 1.5999999999999996, 1.5999999999999996], [1.600000000000002, 1.600000000000002, 1.600000000000002, 1.600000000000002, 1.600000000000002], [1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997, 1.599999999999997], [1.599999999999971, 1.599999999999971, 1.599999999999971, 1.599999999999971, 1.599999999999971], [None, None, None, None, None]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [None, None, None, None, None]
    # INFO:__main__:* Sim duration (SSIRD): [0.2, 0.2, 0.2, 0.2, 0.2]
    # INFO:__main__:* Sim duration (DCTCP): [0, 0, 0, 0, 0]
    # INFO:__main__:* SSIRD FCT: [[0.10049035800000006, 0.10049053100000016, 0.10049071100000084, 0.10049089000000144, 0.10098098899999997], [0.10040187500000108, 0.10040358900000079, 0.10040528500000079, 0.10040698100000078, 0.1014067720000007], [0.0995170690000009, 0.09953395800000031, 0.09955084800000158, 0.09956773800000107, 0.10058411300000003], [0.09166895600000124, 0.09183773700000053, 0.09200651800000159, 0.0921752980000008, 0.09234407900000008], [0.003188028000000287, 0.004875830000001358, 0.006563632000000652, 0.008251433999999946, 0.009939236000001017]]
    # INFO:__main__:* DCTCP FCT: [None, None, None, None, None]

    print("\n--- 5 FLO FULLRANGE 8Gbps RTT=1ms: ---")
    title_addendum = "_large_bload_20MBflo_5flo_8gbps_total_1msRTT"
    rel_path_to_exp_family_output_dir = "FCT_LARGE_Byteloads_SSIRD_ONLY_large_bload_20MBflo_5flo_8gbps_total_1msRTT/"
    num_flows = 5
    num_byteloads_list = [10000, 1000, 100, 10, 1]
    byteload_size_B_list = [2000, 20000, 200000, 2000000, 20000000]
    inter_byteload_period_us_list = [10.0, 100.0, 1000.0, 10000.0, 100000.0]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_5flo_test_vary_bload_num_1msRTT():
    # INFO:__main__:Total Flow Size (Bytes): 200000
    # INFO:__main__:Byteload Size (Bytes): [20, 200, 2000]
    # INFO:__main__:Num Byteloads: [10000, 1000, 100]
    # INFO:__main__:Intervals (us): [10.0, 10.0, 10.0]
    # INFO:__main__:Num flows: 5
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [0.08, 0.8, 8.0]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [0.080006400640064, 0.8006406406406275, 8.064646464633425]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [0.080006400640064, 0.8006406406406275, 8.064646464633425]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[0.015999999999999997, 0.015999999999999997, 0.015999999999999997, 0.015999999999999997, 0.015999999999999997], [0.15999999999999737, 0.15999999999999737, 0.15999999999999737, 0.15999999999999737, 0.15999999999999737], [1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[0.015999999999999997, 0.015999999999999997, 0.015999999999999997, 0.015999999999999997, 0.015999999999999997], [0.15999999999999737, 0.15999999999999737, 0.15999999999999737, 0.15999999999999737, 0.15999999999999737], [1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413]]
    # INFO:__main__:* Sim duration (SSIRD): [0.12, 0.12, 0.12]
    # INFO:__main__:* Sim duration (DCTCP): [0.2, 0.2, 0.2]
    # INFO:__main__:* SSIRD FCT: [[0.10049007799999998, 0.10049010800000069, 0.1004901380000014, 0.1004901750000009, 0.10049020500000161], [0.010490079000000208, 0.010490105000000582, 0.010490135000001288, 0.010490165000000218, 0.010620380000000651], [0.00169073600000047, 0.0018903230000013593, 0.0020808350000010023, 0.0022803230000008057, 0.002470859000000658]]
    # INFO:__main__:* DCTCP FCT: [[0.10049001600000018, 0.10049002400000084, 0.10049003100000142, 0.10049003900000031, 0.10049004700000097], [0.010490044000000864, 0.010490067000000991, 0.010490089000001035, 0.010490111000001079, 0.010490133000001123], [0.0014902960000000576, 0.001490468000000078, 0.0014906400000000986, 0.0014908130000002018, 0.0014909850000002223]]
    print("\nTESTING: 5FLO VARY BLOAD NUMBER (1ms RTT)")
    title_addendum = "_vary_num_bload_5flo_1msRTT"
    rel_path_to_exp_family_output_dir = "FCT_VARY_NUM_BLOAD_vary_num_bload_5flo_1msRTT/"

    num_flows = 5
    inter_byteload_period_us_list = [10.0, 10.0, 10.0]
    num_byteloads_list = [10000, 1000, 100]
    byteload_size_B_list = [20, 200, 2000]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_5flo_test_vary_bload_size_1msRTT():
    # INFO:__main__:Byteload Size (Bytes): [20, 200, 2000]
    # INFO:__main__:Num Byteloads: [100, 100, 100]
    # INFO:__main__:Intervals (us): [10.0, 10.0, 10.0]
    # INFO:__main__:Num flows: 5
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [0.08, 0.8, 8.0]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [0.08064646464633425, 0.8064646464633426, 8.064646464633425]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [0.08064646464633425, 0.8064646464633426, 8.064646464633425]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[0.015999999999974132, 0.015999999999974132, 0.015999999999974132, 0.015999999999974132, 0.015999999999974132], [0.1599999999997413, 0.1599999999997413, 0.1599999999997413, 0.1599999999997413, 0.1599999999997413], [1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[0.015999999999974132, 0.015999999999974132, 0.015999999999974132, 0.015999999999974132, 0.015999999999974132], [0.1599999999997413, 0.1599999999997413, 0.1599999999997413, 0.1599999999997413, 0.1599999999997413], [1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413, 1.599999999997413]]
    # INFO:__main__:* Sim duration (SSIRD): [0.01, 0.01, 0.01]
    # INFO:__main__:* Sim duration (DCTCP): [0.1, 0.1, 0.1]
    # INFO:__main__:* SSIRD FCT: [[0.0015402000000008798, 0.0015801900000003144, 0.0016201800000015254, 0.00167019000000046, 0.0017101799999998946], [0.001650230000000974, 0.0018002300000006244, 0.0019502600000009807, 0.002100260000000631, 0.0022502600000002815], [0.00169073600000047, 0.0018903230000013593, 0.0020808350000010023, 0.0022803230000008057, 0.002470859000000658]]
    # INFO:__main__:* DCTCP FCT: [[0.001490015999999983, 0.0014900240000006448, 0.001490031000001224, 0.0014900390000001096, 0.0014900470000007715], [0.0014900440000005233, 0.00149006700000065, 0.0014900890000006939, 0.0014901110000007378, 0.0014901330000007817], [0.0014902960000000576, 0.001490468000000078, 0.0014906400000000986, 0.0014908130000002018, 0.0014909850000002223]]
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
    # INFO:__main__:Total Flow Size (Bytes): 145800
    # INFO:__main__:Total Injection Period (us): 100
    # INFO:__main__:Byteload Size (Bytes): [1458]
    # INFO:__main__:Num Byteloads: [100]
    # INFO:__main__:Intervals (us): [1.0]
    # INFO:__main__:Num flows: 8
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [93.312]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [94.13672727223725]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [None]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[11.663999999939284, 11.663999999939284, 11.663999999939284, 11.663999999939284, 11.663999999939284, 11.663999999939284, 11.663999999939284, 11.663999999939284]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [None]
    # INFO:__main__:* Sim duration (SSIRD): [0.005, 0.005, 0.005, 0.005, 0.005]
    # INFO:__main__:* Sim duration (DCTCP): [0.3, 0.3, 0.3, 0.3, 0.3]
    # INFO:__main__:* SSIRD FCT: [[0.00010190200000081973, 0.00010203200000091783, 0.00010216200000101594, 0.00010229100000103131, 0.00010242100000112941, 0.00010255100000122752, 0.00010268100000132563, 0.00011486400000038088]]
    # INFO:__main__:* DCTCP FCT: [None]
    print("\nNormal Bloads: 1458B, 8Flo, 99.312Gbps, 5usRTT")
    title_addendum = "_1458B_8flo_93pt312Gbps"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1458B_8flo_93pt312Gbps/"

    num_flows = 8
    inter_byteload_period_us_list = [1]
    num_byteloads_list = [100]
    byteload_size_B_list = [1458]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_normal_bloads_1458B_8flo_99pt312Gbps_1msRTT():
    # INFO:__main__:Total Flow Size (Bytes): 145800
    # INFO:__main__:Total Injection Period (us): 100
    # INFO:__main__:Byteload Size (Bytes): [1458]
    # INFO:__main__:Num Byteloads: [100]
    # INFO:__main__:Intervals (us): [1.0]
    # INFO:__main__:Num flows: 8
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [93.312]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [94.13672727223725]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [None]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[11.663999999939284, 11.663999999939284, 11.663999999939284, 11.663999999939284, 11.663999999939284, 11.663999999939284, 11.663999999939284, 11.663999999939284]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [None]
    # INFO:__main__:* Sim duration (SSIRD): [0.005, 0.005, 0.005, 0.005, 0.005]
    # INFO:__main__:* Sim duration (DCTCP): [0.3, 0.3, 0.3, 0.3, 0.3]
    # INFO:__main__:* SSIRD FCT: [[0.001512664999999913, 0.0015251570000014425, 0.0015376850000006215, 0.0015501770000003745, 0.001562675000000624, 0.001575167000000377, 0.0015876650000006265, 0.0016001570000003795]]
    # INFO:__main__:* DCTCP FCT: [None]
    print("\nNormal Bloads: 1458B, 8Flo, 99.312Gbps, 1msRTT")
    title_addendum = "_1458B_8flo_93pt312Gbps_1msRTT"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1458B_8flo_93pt312Gbps_1msRTT/"

    num_flows = 8
    inter_byteload_period_us_list = [1]
    num_byteloads_list = [100]
    byteload_size_B_list = [1458]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_normal_bloads_1458B_85flo_99pt144Gbps_5usRTT():
    # INFO:__main__:Total Flow Size (Bytes): 145800
    # INFO:__main__:Total Injection Period (us): 1000
    # INFO:__main__:Byteload Size (Bytes): [1458]
    # INFO:__main__:Num Byteloads: [100]
    # INFO:__main__:Intervals (us): [10.0]
    # INFO:__main__:Num flows: 85
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [99.144]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [100.13367272711083]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [None]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [None]
    # INFO:__main__:* Sim duration (SSIRD): [0.005, 0.005, 0.005, 0.005, 0.005]
    # INFO:__main__:* Sim duration (DCTCP): [0.3, 0.3, 0.3, 0.3, 0.3]
    # INFO:__main__:* SSIRD FCT: [[0.0009955380000015168, 0.0009972600000001108, 0.0009991060000000829, 0.000996522000001221, 0.0009961530000008878, 0.0010007050000009343, 0.001001321000000388, 0.000997014000001073, 0.0010020590000010543, 0.0010021820000005732, 0.0009950459999998884, 0.000999352000000897, 0.001001443999999907, 0.0010666550000006936, 0.0009941840000013968, 0.0009962760000004067, 0.0009966450000007399, 0.0009981220000003788, 0.0009973830000014061, 0.0009998440000007491, 0.0010008280000004532, 0.0009997210000012302, 0.000997876000001341, 0.0009943070000009158, 0.00100181300000024, 0.0010174389999999534, 0.0009935690000002495, 0.0009982449999998977, 0.0009936920000015448, 0.0010023050000000922, 0.0010005820000014154, 0.0009934460000007306, 0.0009957840000005547, 0.0010011980000008691, 0.000998491000000712, 0.0010025510000009064, 0.0009944300000004347, 0.0009959070000000736, 0.0009939380000005826, 0.0010000900000015633, 0.0010543510000005085, 0.000998860000001045, 0.0009977519999999629, 0.0009960300000013689, 0.000999475000000416, 0.000999597999999935, 0.0010003360000006012, 0.0010912630000010637, 0.0010015670000012022, 0.0011035670000012487, 0.0009954150000002215, 0.0010004590000001201, 0.0009940610000001016, 0.000999967000000268, 0.0009967680000002588, 0.0009938150000010637, 0.000998368000001193, 0.000997629000000444, 0.0009945529999999536, 0.0011158710000014338, 0.001000952000000055, 0.0009951690000011837, 0.0009963989999999256, 0.0009992290000013782, 0.0009948000000008506, 0.000997506000000925, 0.0010789590000008786, 0.0010420470000003235, 0.0010051350000015447, 0.000994676000001249, 0.0009979990000008598, 0.0010002130000010823, 0.0010297430000001384, 0.0009952920000007026, 0.0010010750000013502, 0.000997137000000592, 0.000998983000000564, 0.0009956610000010357, 0.0009986140000002308, 0.0009949230000003695, 0.0010019360000015354, 0.0010016900000007212, 0.000998737000001526, 0.0010024280000013874, 0.000996891000001554]]
    # INFO:__main__:* DCTCP FCT: [None]
    print("\nNormal Bloads: 1458B, 85Flo, 99.144Gbps, 5usRTT")
    title_addendum = "_1458B_85flo_99pt144Gbps"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1458B_85flo_99pt144Gbps/"

    num_flows = 85
    inter_byteload_period_us_list = [10]
    num_byteloads_list = [100]
    byteload_size_B_list = [1458]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_normal_bloads_1458B_85flo_99pt144Gbps_1msRTT():
    # INFO:__main__:Total Flow Size (Bytes): 145800
    # INFO:__main__:Total Injection Period (us): 1000
    # INFO:__main__:Byteload Size (Bytes): [1458]
    # INFO:__main__:Num Byteloads: [100]
    # INFO:__main__:Intervals (us): [10.0]
    # INFO:__main__:Num flows: 85
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [99.144]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [100.13367272711083]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [None]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143, 1.1663999999981143]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [None]
    # INFO:__main__:* Sim duration (SSIRD): [0.005, 0.005, 0.005, 0.005, 0.005]
    # INFO:__main__:* Sim duration (DCTCP): [0.3, 0.3, 0.3, 0.3, 0.3]
    # INFO:__main__:* SSIRD FCT: [[0.0021892570000012768, 0.00239842500000087, 0.0018201370000010542, 0.0015740570000009058, 0.0019923930000000922, 0.002287689000000981, 0.0017463129999999438, 0.0021031289999999814, 0.002484553000000389, 0.0015986650000012759, 0.0020908250000015727, 0.0016232729999998696, 0.0025337820000004285, 0.0019308730000009433, 0.001881657000000203, 0.0020293050000006474, 0.00242303300000124, 0.0021154330000001664, 0.0019185690000007583, 0.0017340090000015351, 0.0016478810000002397, 0.00169709700000098, 0.0022261690000000556, 0.002201561000001462, 0.002386121000000685, 0.001684793000000795, 0.0022384730000002406, 0.00172170500000135, 0.0019554810000013134, 0.002472249000000204, 0.001783225000000499, 0.0020662170000012026, 0.0021523450000007216, 0.0018324410000012392, 0.0015863610000010908, 0.0019677850000014985, 0.002312297000001351, 0.0023738170000005, 0.001610969000001461, 0.0016355770000000547, 0.0025460930000011928, 0.0024476410000016102, 0.0021400410000005365, 0.001770921000000314, 0.001869353000000018, 0.0019062650000005732, 0.0022138649999998705, 0.002324601000001536, 0.0021277370000003515, 0.0015617530000007207, 0.0022630810000006107, 0.002361513000000315, 0.0018447450000014243, 0.0018570490000016093, 0.0025214720000015234, 0.0018939610000003881, 0.0016601850000004248, 0.002509161000000759, 0.002275385000000796, 0.002299993000001166, 0.001980088999999907, 0.002435337000001425, 0.0020046970000002773, 0.0015248410000001655, 0.002410729000001055, 0.0015494490000005356, 0.0021646490000009067, 0.002496857000000574, 0.0022507770000004257, 0.0023492090000001298, 0.001709401000001165, 0.0020416090000008325, 0.0020785210000013876, 0.002459945000000019, 0.0021769530000010917, 0.0015125369999999805, 0.0016724890000006098, 0.0017586170000001289, 0.0020170010000004623, 0.0023369049999999447, 0.001807833000000869, 0.0019431770000011284, 0.0020539130000010175, 0.0015371450000003506, 0.001795529000000684]]
    # INFO:__main__:* DCTCP FCT: [None]
    print("\nNormal Bloads: 1458B, 85Flo, 99.144Gbps, 1msRTT")
    title_addendum = "_1458B_85flo_99pt144Gbps_1msRTT"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1458B_85flo_99pt144Gbps_1msRTT/"

    num_flows = 85
    inter_byteload_period_us_list = [10]
    num_byteloads_list = [100]
    byteload_size_B_list = [1458]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_normal_bloads_1560B_8flo_99pt84Gbps_5usRTT():
    # INFO:__main__:Total Flow Size (Bytes): 156000
    # INFO:__main__:Total Injection Period (us): 100
    # INFO:__main__:Byteload Size (Bytes): [1560]
    # INFO:__main__:Num Byteloads: [100]
    # INFO:__main__:Intervals (us): [1.0]
    # INFO:__main__:Num flows: 8
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [99.84]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [100.72242424189994]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [None]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[12.479999999935037, 12.479999999935037, 12.479999999935037, 12.479999999935037, 12.479999999935037, 12.479999999935037, 12.479999999935037, 12.479999999935037]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [None]
    # INFO:__main__:* Sim duration (SSIRD): [0.005, 0.005, 0.005, 0.005, 0.005]
    # INFO:__main__:* Sim duration (DCTCP): [0.3, 0.3, 0.3, 0.3, 0.3]
    # INFO:__main__:* SSIRD FCT: [[0.00010188400000110676, 0.00010202200000009043, 0.0001021660000013469, 0.00010231000000082702, 0.00010245500000038987, 0.00010259899999986999, 0.00011129000000131839, 0.00012446100000040872]]
    # INFO:__main__:* DCTCP FCT: [None]
    print("\nNormal Bloads: 1560B, 8Flo, 99.84Gbps, 5usRTT")
    title_addendum = "_1560B_8flo_99pt84Gbps"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1560B_8flo_99pt84Gbps/"

    num_flows = 8
    inter_byteload_period_us_list = [1]
    num_byteloads_list = [100]
    byteload_size_B_list = [1560]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_normal_bloads_1560B_8flo_99pt84Gbps_1msRTT():
    # INFO:__main__:Total Flow Size (Bytes): 156000
    # INFO:__main__:Total Injection Period (us): 100
    # INFO:__main__:Byteload Size (Bytes): [1560]
    # INFO:__main__:Num Byteloads: [100]
    # INFO:__main__:Intervals (us): [1.0]
    # INFO:__main__:Num flows: 8
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [99.84]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [100.72242424189994]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [None]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[12.479999999935037, 12.479999999935037, 12.479999999935037, 12.479999999935037, 12.479999999935037, 12.479999999935037, 12.479999999935037, 12.479999999935037]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [None]
    # INFO:__main__:* Sim duration (SSIRD): [0.005, 0.005, 0.005, 0.005, 0.005]
    # INFO:__main__:* Sim duration (DCTCP): [0.3, 0.3, 0.3, 0.3, 0.3]
    # INFO:__main__:* SSIRD FCT: [[0.001513491000000755, 0.0015266680000003419, 0.0015398320000006294, 0.0015529970000009996, 0.0015661620000013698, 0.0015793269999999637, 0.0015924930000004167, 0.0016056570000007042]]
    # INFO:__main__:* DCTCP FCT: [None]
    print("\nNormal Bloads: 1560B, 8Flo, 99.84Gbps, 1msRTT")
    title_addendum = "_1560B_8flo_99pt84Gbps_1msRTT"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1560B_8flo_99pt84Gbps_1msRTT/"

    num_flows = 8
    inter_byteload_period_us_list = [1]
    num_byteloads_list = [100]
    byteload_size_B_list = [1560]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_credit_leak_investigation_1458B_1flo_5usRTT():
    # INFO:__main__:Total Flow Size (Bytes): 7290
    # INFO:__main__:Total Injection Period (us): 50
    # INFO:__main__:Byteload Size (Bytes): [1458]
    # INFO:__main__:Num Byteloads: [5]
    # INFO:__main__:Intervals (us): [10.0]
    # INFO:__main__:Num flows: 1
    # DEBUG:__main__:Flow start times (us): [0]
    # INFO:__main__:Gdpt Gbps theoretical: [1.1664]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [1.1663999999923587]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [None]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[1.1663999999923587]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [None]
    # INFO:__main__:* Sim duration (SSIRD): [0.01]
    # INFO:__main__:* Sim duration (DCTCP): [0.0]
    # INFO:__main__:* SSIRD FCT: [[4.780600000131585e-05]]
    # INFO:__main__:* DCTCP FCT: [None]
    print("\nCredit leak Investigation: 1458B, 10us, 1Flo, 5usRTT")
    title_addendum = "_1458B_1flo_credit_leak"
    rel_path_to_exp_family_output_dir = "Normal_Byteloads_1458B_1flo_credit_leak/"

    num_flows = 1
    inter_byteload_period_us_list = [10]
    num_byteloads_list = [5]
    byteload_size_B_list = [1458]

    process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family_output_dir, title_addendum)

def proc_credit_leak_investigation_1458B_1flo_1msRTT():
    # INFO:__main__:Total Flow Size (Bytes): 7290
    # INFO:__main__:Total Injection Period (us): 50
    # INFO:__main__:Byteload Size (Bytes): [1458]
    # INFO:__main__:Num Byteloads: [5]
    # INFO:__main__:Intervals (us): [10.0]
    # INFO:__main__:Num flows: 1
    # DEBUG:__main__:Flow start times (us): [0]
    # INFO:__main__:Gdpt Gbps theoretical: [1.1664]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [1.1663999999923587]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [None]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[1.1663999999923587]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [None]
    # INFO:__main__:* Sim duration (SSIRD): [0.01]
    # INFO:__main__:* Sim duration (DCTCP): [0.0]
    # INFO:__main__:* SSIRD FCT: [[0.0015403160000015959]]
    # INFO:__main__:* DCTCP FCT: [None]
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
    # proc_5flo_fullrange_exp_sim_outputs_5usRTT()
    # proc_5flo_fullrange_exp_sim_outputs_1msRTT()
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
    proc_credit_leak_investigation_1462B_5flo_5usRTT()
    proc_1flo_fullrange_exp_sim_outputs_5usRTT()
    # proc_5flo_fullrange_exp_sim_outputs_5usRTT()

    # ''' --- CREDIT LEAK INVESTIGATION (RTT = 1ms) --- '''
    # # proc_credit_leak_investigation_1458B_1flo_1msRTT()
    # proc_credit_leak_investigation_1462B_1flo_1msRTT()
    proc_credit_leak_investigation_1462B_5flo_1msRTT()
    proc_1flo_fullrange_exp_sim_outputs_1msRTT()
    # proc_5flo_fullrange_exp_sim_outputs_1msRTT()