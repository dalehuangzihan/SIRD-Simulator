import csv
from pathlib import Path
import statistics
import matplotlib.pyplot as plt

# PATH_TO_SCRIPTS_R2P2 = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/scripts/r2p2/"
PATH_TO_SCRIPTS_R2P2 = "/data/dh1723/SIRD-Simulator/scripts/r2p2/" # NOTE: this is for batch1 server
PATH_TO_POSTPROC = f"{PATH_TO_SCRIPTS_R2P2}post-process/"
PATH_TO_SIM_RESULTS = f"{PATH_TO_SCRIPTS_R2P2}coord/results/"
PATH_TO_TMP_PLOT = PATH_TO_POSTPROC + "tmp_plot/"
PATH_TO_THRPT_COMPARE_PARENT_DIR = PATH_TO_TMP_PLOT + "nw_thrpt_compare_ssird_dctcp/"
PATH_TO_NW_DATA_COMPARE_PARENT_DIR = PATH_TO_TMP_PLOT + "nw_data_compare_ssird_dctcp/"

# Common experiment param; value is meaningful only when req_interval_distr is not 'manual'
CLIENT_INJECTION_RATE_GBPS = "60"
DCTCP_ECN_THRESH = 50

SSIRD_PROTO_NAME = 'SSIRD'
DCTCP_PROTO_NAME = 'DCTCP'

AGGR = "aggr"
HOST = "host"
TOR = "tor"

SSIRD_PLOT_COLOUR = 'tab:orange'
IDEAL_PLOT_COLOUR = 'tab:blue'


class QmonResults:
    def __init__(self, nw_elem, src, dst, timestamps_list, timestamp_cutoff_s, throughput_gbps_list, queueing_KB_list):
        self.nw_elem = nw_elem
        self.src = src
        self.dst = dst
        self.timestamps_list = timestamps_list
        self.throughput_gbps_list = throughput_gbps_list
        self.queueing_KB_list = queueing_KB_list
        self.activity_end_time_s = timestamp_cutoff_s # is when thrpt falls to 0 until the end of the experiment.
    
    def get_avg_thrpt_gbps(self,):
        return statistics.mean(self.throughput_gbps_list)

    def get_avg_qing_KB(self):
        # TODO
        pass

def get_qts_timestamp_cutoff_from_csv(path_to_qts_csv):
    with open(path_to_qts_csv, 'r') as file:
        prev_timestamp_s = None
        for row in reversed(list(csv.reader(file, delimiter=","))):
            timestamp_s = float(row[0])
            thrpt_gbps = float(row[1])
            qing_KB = float(row[2])
            if (thrpt_gbps == 0 and qing_KB == 0):
                prev_timestamp_s = timestamp_s
            else:
                return prev_timestamp_s if prev_timestamp_s else timestamp_s

def get_qts_results_from_csv(nw_elem, src, dst, path_to_qts_csv, timestamp_cutoff_s=None):
    with open(path_to_qts_csv, newline='') as file:
        reader = csv.reader(file, delimiter=',')
        headings = next(reader)

        timestamps_list = []
        throughput_gbps_list = []
        queueing_KB_list = []
        for row in reader:
            if timestamp_cutoff_s and float(row[0]) > timestamp_cutoff_s:
                break
            timestamps_list.append(float(row[0]))
            throughput_gbps_list.append(float(row[1]))
            queueing_KB_list.append(float(row[2]))

        return QmonResults(nw_elem, src, dst, timestamps_list, timestamp_cutoff_s, throughput_gbps_list, queueing_KB_list) 

# NOTE: this is the microsecond experiment name version
# def get_qts_result_path(proto, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum = ""):
#     if proto.upper() == SSIRD_PROTO_NAME: 
#         return f"{PATH_TO_SIM_RESULTS}{SSIRD_PROTO_NAME}-{num_flows}flo-{num_byteloads_per_flow}#-{byteload_size_B}B-{inter_byteload_period_us}us{title_addendum}/data/{SSIRD_PROTO_NAME}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

#     elif proto.upper() == DCTCP_PROTO_NAME:
#         return f"{PATH_TO_SIM_RESULTS}{DCTCP_PROTO_NAME}-{DCTCP_ECN_THRESH}-{num_flows}flo-{num_byteloads_per_flow}#-{byteload_size_B}B-{inter_byteload_period_us}us{title_addendum}/data/{DCTCP_PROTO_NAME}-{DCTCP_ECN_THRESH}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

#     else:
#         print(f"ERROR: proto name '{proto}' unrecognised!")

# NOTE: this is the nanosecond experiment name version
def get_qts_result_path(proto, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum = ""):
    inter_byteload_period_ns = int(inter_byteload_period_us * 1000)
    if proto.upper() == SSIRD_PROTO_NAME: 
        return f"{PATH_TO_SIM_RESULTS}{SSIRD_PROTO_NAME}-{num_flows}flo-{num_byteloads_per_flow}#-{byteload_size_B}B-{inter_byteload_period_ns}ns{title_addendum}/data/{SSIRD_PROTO_NAME}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

    elif proto.upper() == DCTCP_PROTO_NAME:
        return f"{PATH_TO_SIM_RESULTS}{DCTCP_PROTO_NAME}-{DCTCP_ECN_THRESH}-{num_flows}flo-{num_byteloads_per_flow}#-{byteload_size_B}B-{inter_byteload_period_ns}ns{title_addendum}/data/{DCTCP_PROTO_NAME}-{DCTCP_ECN_THRESH}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

    else:
        print(f"ERROR: proto name '{proto}' unrecognised!")

def get_qts_result_ssird_dctcp(nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum=""):
    ssird_qts_result_path = get_qts_result_path(SSIRD_PROTO_NAME, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum)
    print(ssird_qts_result_path)

    dctcp_qts_result_path = get_qts_result_path(DCTCP_PROTO_NAME, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum)
    print(dctcp_qts_result_path)

    ssird_timestamp_cutoff_s = get_qts_timestamp_cutoff_from_csv(ssird_qts_result_path)
    dctcp_timestamp_cutoff_s = get_qts_timestamp_cutoff_from_csv(dctcp_qts_result_path)

    ssird_qts_results_obj = get_qts_results_from_csv(nw_elem, src, dst, ssird_qts_result_path, ssird_timestamp_cutoff_s)
    dctcp_qts_results_obj = get_qts_results_from_csv(nw_elem, src, dst, dctcp_qts_result_path, dctcp_timestamp_cutoff_s)

    return ssird_qts_results_obj, dctcp_qts_results_obj

'''
========== NW OVERHEAD PLOTS ==========
'''
def get_qts_nw_data_B_ssird_dctcp(src, dst, num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, app_total_gdpt_gbps, title_addendum=""):
    ssird_thrpt_gbps_list, dctcp_thrpt_tbps_list, ssird_fct_list, dctcp_fct_list = get_qts_thrpt_ssird_dctcp(src, dst, num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, title_addendum)

    ssird_total_nw_data_w_overheads_B = [gbps * pow(10,9) * t / 8 for gbps, t in zip(ssird_thrpt_gbps_list, ssird_fct_list)]
    dctcp_total_nw_data_w_overheads_B = [gbps * pow(10,9) * t / 8 for gbps, t in zip(dctcp_thrpt_tbps_list, dctcp_fct_list)]
    ssird_app_data_total_actual_B = [app_total_gdpt_gbps * pow(10, 9) * t / 8 for t in ssird_fct_list]
    dctcp_app_data_total_actual_B = [app_total_gdpt_gbps * pow(10, 9) * t / 8 for t in dctcp_fct_list]

    app_data_total_theory_B = num_flows * num_byteloads_per_flow_list[0] * byteload_size_B_list[0]
    assert(all(num_flows * n * b == app_data_total_theory_B for n, b in zip(num_byteloads_per_flow_list, byteload_size_B_list)))

    app_data_total_measured_B = ssird_app_data_total_actual_B

    return ssird_total_nw_data_w_overheads_B, dctcp_total_nw_data_w_overheads_B, app_data_total_theory_B, app_data_total_measured_B

'''
def plot_nw_data_B_ssird_dctcp(ssird_nw_data_B_list, dctcp_nw_data_B_list, byteload_size_B_list, app_data_total_B, num_flows, flow_size_B, flow_rate_gbps, is_log_x=False, y_lim=None, is_per_flow=False,title_addendum=""):
    Path(PATH_TO_NW_DATA_COMPARE_PARENT_DIR).mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10,6))
    if y_lim:
        plt.ylim(y_lim)

    plt.plot(byteload_size_B_list, ssird_nw_data_B_list, label="SSIRD", linestyle="-", marker="o", color=SSIRD_PLOT_COLOUR)
    # plt.plot(byteload_size_B_list, dctcp_nw_data_B_list, label="DCTCP", linestyle="-", marker="o", color=IDEAL_PLOT_COLOUR)
    plt.plot(byteload_size_B_list, app_data_total_B, label="Application", linestyle=":", marker=None, color="g")

    plt.xlabel('Byteload Size (B)')
    plt.ylabel('Network Data (B)')

    filename_prefix = None
    if (is_per_flow):
        plt.title(f"SSIRD vs DCTCP: Per-Flow Network Data @ {num_flows * flow_size_B}B App Data\n({num_flows} x {flow_size_B}B flows, each at {flow_rate_gbps}Gbps; Total App Gdpt: {num_flows * flow_rate_gbps}Gbps)\n{title_addendum}")
        filename_prefix = "PERFLOW_"
    else:
        plt.title(f"SSIRD vs DCTCP: Total Network Data @ {num_flows * flow_size_B}B App Data\n({num_flows} x {flow_size_B}B flows, each at {flow_rate_gbps}Gbps; Total App Gdpt: {num_flows * flow_rate_gbps}Gbps)\n{title_addendum}")
        filename_prefix = "TOTAL_"
    
    plt.legend()
    if (is_log_x): plt.xscale('log')
    plt.grid(True)

    filename = f"{filename_prefix}ssird_vs_dctcp_subpkt_multiflow_nw_data_vs_byteload_size_{num_flows}flo_{flow_rate_gbps}Gbps_each{title_addendum}.png"
    plt.savefig(f"{PATH_TO_NW_DATA_COMPARE_PARENT_DIR}{filename}")
    plt.close()
'''

def plot_nw_data_MB_ssird_dctcp(ssird_nw_data_B_list, dctcp_nw_data_B_list, byteload_size_B_list, app_data_total_B_list, num_flows, flow_size_B, flow_rate_gbps, is_log_x=False, y_lim=None, is_per_flow=False,title_addendum=""):
    Path(PATH_TO_NW_DATA_COMPARE_PARENT_DIR).mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10,6))
    if y_lim:
        plt.ylim(y_lim)

    filename_prefix = None
    if (is_per_flow):
        plt.title(f"SSIRD: Per-Flow Network Data @ {num_flows * flow_size_B/pow(10,3)}KB Total App Data\n({num_flows} x {flow_size_B}B flows, each at {flow_rate_gbps}Gbps; Total App Gdpt: {num_flows * flow_rate_gbps}Gbps)\n{title_addendum}")
        filename_prefix = "PERFLOW_"
        ssird_nw_data_MB_list = [round(b/pow(10,3), 2) for b in ssird_nw_data_B_list]
        app_data_total_MB_list = [round(b/pow(10,3), 2) for b in app_data_total_B_list]
        plt.ylabel('Network Data (KB)')
    else:
        plt.title(f"SSIRD: Total Network Data @ {num_flows * flow_size_B/pow(10,6)}MB Total App Data\n({num_flows} x {flow_size_B}B flows, each at {flow_rate_gbps}Gbps; Total App Gdpt: {num_flows * flow_rate_gbps}Gbps)\n{title_addendum}")
        filename_prefix = "TOTAL_"
        ssird_nw_data_MB_list = [round(b/pow(10,6), 2) for b in ssird_nw_data_B_list]
        app_data_total_MB_list = [round(b/pow(10,6), 2) for b in app_data_total_B_list]
        plt.ylabel('Network Data (MB)')

    plt.plot(byteload_size_B_list, ssird_nw_data_MB_list, label="SSIRD", linestyle="-", marker="o", color=SSIRD_PLOT_COLOUR)
    # plt.plot(byteload_size_B_list, dctcp_nw_data_B_list, label="DCTCP", linestyle="-", marker="o", color=IDEAL_PLOT_COLOUR)
    plt.plot(byteload_size_B_list, app_data_total_MB_list, label="Application", linestyle=":", marker=None, color="g")

    plt.legend()

    plt.xlabel('Byteload Size (B)')
    if (is_log_x): plt.xscale('log')
    plt.grid(True)

    filename = f"{filename_prefix}ssird_subpkt_multiflow_nw_data_vs_byteload_size_{num_flows}flo_{flow_rate_gbps}Gbps_each{title_addendum}.png"
    plt.savefig(f"{PATH_TO_NW_DATA_COMPARE_PARENT_DIR}{filename}")
    plt.close()

def plot_nw_data_MB_overheads_ssird(ssird_total_nw_overheads_B_list, byteload_size_B_list, app_data_total_B_list, num_flows, flow_size_B, flow_rate_gbps, is_log_x=False, y_lim=None, is_per_flow=False, title_addendum=""):
    Path(PATH_TO_NW_DATA_COMPARE_PARENT_DIR).mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10,6))
    if y_lim:
        plt.ylim(y_lim)

    filename_prefix = None
    if (is_per_flow):
        plt.title(f"SSIRD: Per-Flow Network Overheads @ {num_flows * flow_size_B/pow(10,3)}KB Total App Data\n({num_flows} x {flow_size_B}B flows, each at {flow_rate_gbps}Gbps; Total App Gdpt: {num_flows * flow_rate_gbps}Gbps)\n{title_addendum}")
        filename_prefix = "DIFF_PERFLOW_"
        diff_MB_list = [round(d/pow(10,3), 2) for d in ssird_total_nw_overheads_B_list]
        plt.ylabel('Network Overhead (KB)')
    else:
        plt.title(f"SSIRD: Total Network Overheads @ {num_flows * flow_size_B/pow(10,6)}MB Total App Data\n({num_flows} x {flow_size_B}B flows, each at {flow_rate_gbps}Gbps; Total App Gdpt: {num_flows * flow_rate_gbps}Gbps)\n{title_addendum}")
        filename_prefix = "DIFF_TOTAL_"
        diff_MB_list = [round(d/pow(10,6), 2) for d in ssird_total_nw_overheads_B_list]
        plt.ylabel('Network Overhead (MB)')

    plt.plot(byteload_size_B_list, diff_MB_list, linestyle="-", marker="o", color=SSIRD_PLOT_COLOUR)
    plt.legend()

    plt.xlabel('Byteload Size (B)')
    if (is_log_x): plt.xscale('log')
    plt.grid(True)

    filename = f"{filename_prefix}ssird_subpkt_multiflow_nw_data_vs_byteload_size_{num_flows}flo_{flow_rate_gbps}Gbps_each{title_addendum}.png"
    plt.savefig(f"{PATH_TO_NW_DATA_COMPARE_PARENT_DIR}{filename}")
    plt.close()

def plot_overall_and_perflow_nw_data_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_total_gdpt_gbps, title_addendum="", y_lim_total=None, y_lim_perflow=None):
    flow_size_B = num_byteloads_per_flow_list[0] * byteload_size_B_list[0]
    assert(all(n * b == flow_size_B for n, b in zip(num_byteloads_per_flow_list, byteload_size_B_list)))

    # OVERALL: -----
    ssird_total_nw_data_h0tor4_B, dctcp_total_nw_data_h0tor4_B, app_data_total_theory_B, app_data_total_measured_h0tor4_B = get_qts_nw_data_B_ssird_dctcp("host_0", "tor_4", num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, overall_gdpt_gbps,title_addendum)

    ssird_total_nw_data_h1tor4_B, dctcp_total_nw_data_h1tor4_B, app_data_total_theory_B, app_data_total_measured_h1tor4_B = get_qts_nw_data_B_ssird_dctcp("host_1", "tor_4", num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, overall_gdpt_gbps,title_addendum)

    ssird_total_nw_data_B = [h0tor4 + h1tor4 for h0tor4, h1tor4 in zip(ssird_total_nw_data_h0tor4_B, ssird_total_nw_data_h1tor4_B)]
    dctcp_total_nw_data_B = [h0tor4 + h1tor4 for h0tor4, h1tor4 in zip(dctcp_total_nw_data_h0tor4_B, dctcp_total_nw_data_h1tor4_B)]
    
    ssird_overheads_total_theory_B = [s - app_data_total_theory_B for s in ssird_total_nw_data_B]
    app_data_total_theory_B = [app_data_total_theory_B] * len(ssird_overheads_total_theory_B)

    ssird_total_nw_data_B = list(map(lambda x: round(x, 2), ssird_total_nw_data_B))
    dctcp_total_nw_data_B = list(map(lambda x: round(x, 2), dctcp_total_nw_data_B))
    ssird_overheads_total_theory_B = list(map(lambda x: round(x,2), ssird_overheads_total_theory_B))

    plot_nw_data_MB_ssird_dctcp(ssird_total_nw_data_B, dctcp_total_nw_data_B, byteload_size_B_list, app_data_total_theory_B, num_flows, flow_size_B, flow_rate_gbps, is_log_x=True, y_lim=y_lim_total, title_addendum=title_addendum + "_overall")

    print(f"Theoretical Overall Gdpt Gbps: {theoretical_total_gdpt_gbps}")
    print(f"SSIRD NW Data Total (B): {ssird_total_nw_data_B}")
    print(f"DCTCP NW Data Total (B): {dctcp_total_nw_data_B}")
    print(f"** SSIRD Overheads Total (vs theory app data) (B): {ssird_overheads_total_theory_B}")

    # plot total overheads:
    plot_nw_data_MB_overheads_ssird(ssird_overheads_total_theory_B, byteload_size_B_list, app_data_total_theory_B, num_flows, flow_size_B, flow_rate_gbps, is_log_x=True, y_lim=y_lim_total, title_addendum=title_addendum + "_overall") 
    print(f"")

    print("---")
    # PER FLOW: -----
    # we can only do this cuz our experiment uses num_flows flows in parallel!
    ssird_perflow_nw_data_B = [x / num_flows for x in ssird_total_nw_data_B]
    dctcp_perflow_nw_data_B = [x / num_flows for x in dctcp_total_nw_data_B]
    app_data_perflow_theory_B = [flow_rate_gbps] * len(ssird_perflow_nw_data_B)
    ssird_overheads_perflow_theory_B = [s - a for s,a in zip(ssird_perflow_nw_data_B, app_data_perflow_theory_B)] 
    
    ssird_perflow_nw_data_B = list(map(lambda x: round(x, 2), ssird_perflow_nw_data_B))
    dctcp_perflow_nw_data_B = list(map(lambda x: round(x, 2), dctcp_perflow_nw_data_B))
    ssird_overheads_perflow_theory_B = list(map(lambda x: round(x, 2), ssird_overheads_perflow_theory_B))

    plot_nw_data_MB_ssird_dctcp(ssird_perflow_nw_data_B, dctcp_perflow_nw_data_B, byteload_size_B_list, app_data_perflow_theory_B, num_flows, flow_size_B, flow_rate_gbps, is_per_flow=True, y_lim=y_lim_perflow, is_log_x=True, title_addendum=title_addendum + "_perflow")

    print(f"Theoretical Perflow Gdpt Gbps: {flow_rate_gbps}")
    print(f"SSIRD NW Data Per Flow (B): {ssird_perflow_nw_data_B}")
    print(f"DCTCP NW Data Per Flow (B): {dctcp_perflow_nw_data_B}")
    print(f"** SSIRD Overheads Per Flow (vs theory app data) (B): {ssird_overheads_perflow_theory_B}")


def compare_nw_data_subpkt_multiflow_4B_to_4000B_1flo(y_lim_total=None, y_lim_perflow=None):
    # INFO:__main__:Total Flow Size (Bytes): 40000
    # INFO:__main__:Total Injection Period (us): 10000
    # INFO:__main__:Byteload Size (Bytes): [4, 40, 400, 4000]
    # INFO:__main__:Num Byteloads: [10000, 1000, 100, 10]
    # INFO:__main__:Intervals (us): [1, 10, 100, 1000]
    # INFO:__main__:Num flows: 1
    # DEBUG:__main__:Flow start times (us): [0]
    # INFO:__main__:Gdpt Gbps theoretical: [0.032, 0.03200000000000001, 0.03200000000000001, 0.032]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [0.03199999999999829, 0.03199999999999947, 0.03199999999999994, 0.031999999999998786]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [0.03199999999999829, 0.03199999999999947, 0.03199999999999994, 0.031999999999998786]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[0.03199999999999829], [0.03199999999999947], [0.03199999999999994], [0.031999999999998786]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[0.03199999999999829], [0.03199999999999947], [0.03199999999999994], [0.031999999999998786]]
    # INFO:__main__:* Sim duration (SSIRD): [0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* Sim duration (DCTCP): [0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* SSIRD FCT: [[0.010001574000000346], [0.009997559000000322], [0.009907617000001423], [0.009008002000001625]]
    # INFO:__main__:* DCTCP FCT: [[0.010001513000000628], [0.009992519000000755], [0.009902575999999996], [0.00900296200000028]]

    print("@@ 1 FLO")
    title_addendum = "_subpkt_multiflow"

    num_flows = 1
    num_byteloads_per_flow_list = [10000, 1000, 100, 10] # should be [10000, 1000, 100, 10] but there was a naming bug in the experiment
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [1, 10, 100, 1000]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 0.032
    overall_gdpt_gbps = 0.032

    plot_overall_and_perflow_nw_data_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def compare_nw_data_subpkt_multiflow_4B_to_4000B_2flo(y_lim_total=None, y_lim_perflow=None):
    # INFO:__main__:Total Flow Size (Bytes): 40000
    # INFO:__main__:Total Injection Period (us): 10000
    # INFO:__main__:Byteload Size (Bytes): [4, 40, 400, 4000]
    # INFO:__main__:Num Byteloads: 10
    # INFO:__main__:Intervals (us): [1, 10, 100, 1000]
    # INFO:__main__:Num flows: 2
    # DEBUG:__main__:Flow start times (us): [0, 1]
    # INFO:__main__:Gdpt Gbps theoretical: [0.064, 0.06400000000000002, 0.06400000000000002, 0.064]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [0.06399999999999657, 0.06399999999999895, 0.06399999999999988, 0.06399999999999757]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [0.06399999999999657, 0.06399999999999895, 0.06399999999999988, 0.06399999999999757]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[0.03199999999999829, 0.03199999999999829], [0.03199999999999947, 0.03199999999999947], [0.03199999999999994, 0.03199999999999994], [0.031999999999998786, 0.031999999999998786]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[0.03199999999999829, 0.03199999999999829], [0.03199999999999947, 0.03199999999999947], [0.03199999999999994, 0.03199999999999994], [0.031999999999998786, 0.031999999999998786]]
    # INFO:__main__:* Sim duration (SSIRD): [0.011, 0.011, 0.011, 0.011]
    # INFO:__main__:* Sim duration (DCTCP): [0.011, 0.011, 0.011, 0.011]
    # INFO:__main__:* SSIRD FCT: [[0.010001604000001052, 0.010001563999999519], [0.009998579000001229, 0.009996558999999294], [0.009908637000000553, 0.009906617000000395], [0.009009022000000755, 0.009007002000000597]]
    # INFO:__main__:* DCTCP FCT: [[0.010001513000000628, 0.010001512999998852], [0.009992519000000755, 0.009992518999998978], [0.009902575999999996, 0.009902575999999996], [0.00900296200000028, 0.00900296200000028]]

    print("@@ 2 FLO")
    title_addendum = "_subpkt_multiflow_full_parallel"

    num_flows = 2
    num_byteloads_per_flow_list = [10000, 1000, 100, 10] # should be [10000, 1000, 100, 10] but there was a naming bug in the experiment
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [1, 10, 100, 1000]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 0.032
    overall_gdpt_gbps = 0.064

    plot_overall_and_perflow_nw_data_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def compare_nw_data_subpkt_multiflow_4B_to_4000B_10flo_slowpace(y_lim_total=None, y_lim_perflow=None):
    # INFO:__main__:Total Flow Size (Bytes): 40000
    # INFO:__main__:Total Injection Period (us): 10000
    # INFO:__main__:Byteload Size (Bytes): [4, 40, 400, 4000]
    # INFO:__main__:Num Byteloads: [10000, 1000, 100, 10]
    # INFO:__main__:Intervals (us): [1.0, 10.0, 100.0, 1000.0]
    # INFO:__main__:Num flows: 10
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [0.32, 0.32, 0.32, 0.32]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [0.3200288028802709, 0.320288288288283, 0.3229090909090903, 0.35199999999998666]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [0.3200288028802709, 0.320288288288283, 0.3229090909090903, 0.35199999999998666]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829], [0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947], [0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994], [0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829], [0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947], [0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994], [0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786]]
    # INFO:__main__:* Sim duration (SSIRD): [0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* Sim duration (DCTCP): [0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* SSIRD FCT: [[0.010001581000000925, 0.010001604000001052, 0.010001633999999981, 0.010001664000000687, 0.010001694000001393, 0.010001724000000323, 0.010001754000001029, 0.010001783999999958, 0.010001814000000664, 0.01000184400000137], [0.009997559000000322, 0.009997589000001028, 0.009997618999999958, 0.009997649000000663, 0.00999767900000137, 0.009997709000000299, 0.009997739000001005, 0.009997768999999934, 0.00999779900000064, 0.009997829000001346], [0.009907617000001423, 0.009907655000001014, 0.009907694000000689, 0.00990773200000028, 0.009907770999999954, 0.009907809000001322, 0.009907847000000913, 0.009907886000000588, 0.009907924000000179, 0.00990796300000163], [0.009008002000001625, 0.009008342000001335, 0.009008692000000096, 0.009009032000001582, 0.00900937100000121, 0.009009712000001002, 0.009010052000000712, 0.00901039100000034, 0.009010729999999967, 0.00901106900000137]]
    # INFO:__main__:* DCTCP FCT: [[0.012581681000000344, 0.012581693000001337, 0.012581706000000636, 0.012581718999999936, 0.012581732000001011, 0.01258174500000031, 0.012581757000001303, 0.012581770000000603, 0.012581782999999902, 0.012581796000000978], [0.009992519000000755, 0.0099925280000015, 0.00999253800000055, 0.009992547000001295, 0.009992557000000346, 0.00999256600000109, 0.009992576000000142, 0.009992585000000886, 0.009992594000001631, 0.009992604000000682], [0.009902575999999996, 0.009902615000001447, 0.009902653000001038, 0.00990269100000063, 0.009902729000000221, 0.009902767999999895, 0.009902806000001263, 0.009902844000000854, 0.009902882000000446, 0.00990292100000012], [0.00900296200000028, 0.009003300000001602, 0.009003639000001229, 0.009003978000000856, 0.009004317000000484, 0.009004655000000028, 0.009004994000001432, 0.009005333000001059, 0.009005672000000686, 0.00900601000000023]]
    print("@@ 10 FLO SLOWPACE")
    title_addendum = "_subpkt_multiflow_slowpace"

    num_flows = 10
    num_byteloads_per_flow_list = [10000, 1000, 100, 10] # should be [10000, 1000, 100, 10] but there was a naming bug in the experiment
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [1, 10, 100, 1000]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 0.032
    overall_gdpt_gbps = 0.32

    plot_overall_and_perflow_nw_data_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def compare_nw_data_subpkt_multiflow_4B_to_4000B_15flo_fastpace(y_lim_total=None, y_lim_perflow=None):
    # INFO:__main__:Total Flow Size (Bytes): 40000
    # INFO:__main__:Total Injection Period (us): 100.0
    # INFO:__main__:Byteload Size (Bytes): [4, 40, 400, 4000]
    # INFO:__main__:Num Byteloads: [10000, 1000, 100, 10]
    # INFO:__main__:Intervals (us): [0.01, 0.1, 1.0, 10.0]
    # INFO:__main__:Num flows: 15
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [48.0, 48.0, 48.0, 48.0]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [48.00448044770111, 48.044844844664645, 48.452525252273034, 52.97777777769212]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [48.00448044770111, 48.044844844664645, 48.452525252273034, 52.97777777769212]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089], [3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982], [3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343], [3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089], [3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982], [3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343], [3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826]]
    # INFO:__main__:* Sim duration (SSIRD): [0.00106, 0.00106, 0.00106, 0.00106]
    # INFO:__main__:* Sim duration (DCTCP): [0.02, 0.017, 0.017, 0.017]
    # INFO:__main__:* SSIRD FCT: [[0.0003420990000009283, 0.00034547899999992637, 0.00034886500000119725, 0.00035225100000069176, 0.00035563600000010354, 0.0003590220000013744, 0.0003624080000008689, 0.00036579400000036344, 0.0003691800000016343, 0.00037256600000112883, 0.00037595200000062334, 0.00037933800000011786, 0.00038272400000138873, 0.00038611000000088325, 0.00038949600000037776], [0.00010683200000016768, 0.00011021100000085937, 0.00011359700000035389, 0.00011698300000162476, 0.00012036900000111928, 0.0001237550000006138, 0.0001271410000001083, 0.00013052700000137918, 0.0001339130000008737, 0.0001372990000003682, 0.00014068499999986273, 0.0001440710000011336, 0.0001474570000006281, 0.0001508420000000399, 0.00015422800000131076], [0.00010167800000004945, 0.00010171600000141723, 0.00010175400000100865, 0.00010179300000068281, 0.00010183100000027423, 0.00010186999999994839, 0.00010190800000131617, 0.00010194600000090759, 0.00010198500000058175, 0.00010202300000017317, 0.00010206200000162369, 0.00010210000000121511, 0.00010213800000080653, 0.00010217700000048069, 0.00010513900000042042], [9.307800000080135e-05, 9.815200000140578e-05, 9.849800000161224e-05, 9.883700000123952e-05, 9.917700000094953e-05, 9.951600000057681e-05, 9.985500000020409e-05, 0.00010019400000160772, 0.000100533000001235, 0.00010087300000094501, 0.00010121200000057229, 0.00010155100000019956, 0.0001018900000016032, 0.00010222900000123047, 0.00010294900000040741]]
    # INFO:__main__:* DCTCP FCT: [[0.018869601000000458, 0.01886961300000145, 0.01886962600000075, 0.01886963900000005, 0.018869652000001125, 0.018869665000000424, 0.018869677000001417, 0.018869690000000716, 0.018869703000000015, 0.01886971600000109, 0.01886972900000039, 0.018869741000001383, 0.018869754000000682, 0.018869766999999982, 0.018869780000001057], [0.0018871410000009803, 0.0018871530000001968, 0.0018871660000012724, 0.0018871790000005717, 0.001887191999999871, 0.0018872050000009466, 0.0018872170000001631, 0.0018872300000012387, 0.001887243000000538, 0.0018872560000016136, 0.001887269000000913, 0.0018872810000001294, 0.001887294000001205, 0.0018873070000005043, 0.00188732000000158], [0.00019131400000027554, 0.00019135199999986696, 0.00019139000000123474, 0.00019142800000082616, 0.00019146700000050032, 0.00019150500000009174, 0.00019154300000145952, 0.00019158100000105094, 0.0001916200000007251, 0.00019165800000031652, 0.0001921230000014873, 0.00019216100000107872, 0.00019219900000067014, 0.00019223700000026156, 0.00019227599999993572], [9.296200000008525e-05, 9.330000000140615e-05, 9.363900000103342e-05, 9.39780000006607e-05, 9.431700000028798e-05, 9.465500000160887e-05, 9.499400000123615e-05, 9.533300000086342e-05, 9.56720000004907e-05, 9.601000000003523e-05, 9.634900000143887e-05, 9.668800000106614e-05, 9.702600000061068e-05, 9.736500000023796e-05, 9.770399999986523e-05]]
    print("\n@@ 15 FLO FASTPACE NW DATA")
    title_addendum = "_subpkt_multiflow_fastpace"

    num_flows = 15
    num_byteloads_per_flow_list = [10000, 1000, 100, 10] # should be [10000, 1000, 100, 10] but there was a naming bug in the experiment
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [0.01, 0.1, 1, 10]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 3.2
    overall_gdpt_gbps = 48.0

    plot_overall_and_perflow_nw_data_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def compare_nw_data_subpkt_multiflow_4B_to_4000B_15flo_slowpace(y_lim_total=None, y_lim_perflow=None):
    # INFO:__main__:Total Flow Size (Bytes): 40000
    # INFO:__main__:Total Injection Period (us): 10000
    # INFO:__main__:Byteload Size (Bytes): [4, 40, 400, 4000]
    # INFO:__main__:Num Byteloads: [10000, 1000, 100, 10]
    # INFO:__main__:Intervals (us): [1.0, 10.0, 100.0, 1000.0]
    # INFO:__main__:Num flows: 15
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [0.48, 0.48, 0.48, 0.48]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [0.4800448044804224, 0.48044844844844053, 0.4845252525252516, 0.5297777777777577]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [0.4800448044804224, 0.48044844844844053, 0.4845252525252516, 0.5297777777777577]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829], [0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947], [0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994], [0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03199999999999829], [0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947], [0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994], [0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786]]
    # INFO:__main__:* Sim duration (SSIRD): [0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* Sim duration (DCTCP): [0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* SSIRD FCT: [[0.010001614000000103, 0.010001621000000682, 0.010001633999999981, 0.010001664000000687, 0.010001694000001393, 0.010001724000000323, 0.010001754000001029, 0.010001783999999958, 0.010001814000000664, 0.01000184400000137, 0.0100018740000003, 0.010001904000001005, 0.010001933999999935, 0.01000196400000064, 0.010001994000001346], [0.009997559000000322, 0.009997589000001028, 0.009997618999999958, 0.009997649000000663, 0.00999767900000137, 0.009997709000000299, 0.009997739000001005, 0.009997768999999934, 0.00999779900000064, 0.009997829000001346, 0.009997859000000275, 0.009997889000000981, 0.00999791899999991, 0.009997949000000617, 0.009997979000001322], [0.009907617000001423, 0.009907655000001014, 0.009907694000000689, 0.00990773200000028, 0.009907770999999954, 0.009907809000001322, 0.009907847000000913, 0.009907886000000588, 0.009907924000000179, 0.00990796300000163, 0.00990800100000122, 0.009908039000000812, 0.009908078000000486, 0.009908116000000078, 0.009908155000001528], [0.009008002000001625, 0.009008342000001335, 0.009008692000000096, 0.009009032000001582, 0.00900937100000121, 0.009009712000001002, 0.009010052000000712, 0.00901039100000034, 0.009010729999999967, 0.00901106900000137, 0.009011408000000998, 0.009011748000000708, 0.009012087000000335, 0.009012425999999962, 0.009012765000001366]]
    # INFO:__main__:* DCTCP FCT: [[0.018870409000001587, 0.018870421000000803, 0.018870434000000103, 0.018870447000001178, 0.018870460000000477, 0.018871281000000906, 0.018871293000000122, 0.018871306000001198, 0.018871319000000497, 0.018871332000001573, 0.018871345000000872, 0.01887135700000009, 0.018871370000001164, 0.018871383000000463, 0.01887139600000154], [0.009992519000000755, 0.0099925280000015, 0.00999253800000055, 0.009992547000001295, 0.009992557000000346, 0.00999256600000109, 0.009992576000000142, 0.009992585000000886, 0.009992594000001631, 0.009992604000000682, 0.009992613000001427, 0.009992623000000478, 0.009992632000001223, 0.009992642000000274, 0.009992651000001018], [0.009902575999999996, 0.009902615000001447, 0.009902653000001038, 0.00990269100000063, 0.009902729000000221, 0.009902767999999895, 0.009902806000001263, 0.009902844000000854, 0.009902882000000446, 0.00990292100000012, 0.009902959000001488, 0.00990299700000108, 0.00990303500000067, 0.009903074000000345, 0.009903111999999936], [0.00900296200000028, 0.009003300000001602, 0.009003639000001229, 0.009003978000000856, 0.009004317000000484, 0.009004655000000028, 0.009004994000001432, 0.009005333000001059, 0.009005672000000686, 0.00900601000000023, 0.009006349000001634, 0.009006688000001262, 0.009007026000000806, 0.009007365000000433, 0.00900770400000006]]

    print("\n@@ 15 FLO SLOWPACE NW DATA")
    title_addendum = "_subpkt_multiflow_slowpace"

    num_flows = 15
    num_byteloads_per_flow_list = [10000, 1000, 100, 10] # should be [10000, 1000, 100, 10] but there was a naming bug in the experiment
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [1, 10, 100, 1000]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 0.32
    overall_gdpt_gbps = 4.8

    plot_overall_and_perflow_nw_data_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def do_nw_data_plots():
    # compare_nw_data_subpkt_multiflow_4B_to_4000B_1flo()
    # print("=====")
    # compare_nw_data_subpkt_multiflow_4B_to_4000B_2flo()
    # print("=====")
    compare_nw_data_subpkt_multiflow_4B_to_4000B_10flo_slowpace()
    compare_nw_data_subpkt_multiflow_4B_to_4000B_15flo_fastpace()
    compare_nw_data_subpkt_multiflow_4B_to_4000B_15flo_slowpace()

'''
========== THRPT vs GDPT PLOTS ========== 
'''
def get_qts_thrpt_ssird_dctcp(src, dst, num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, title_addendum=""):
    num_experiments = len(num_byteloads_per_flow_list)
    assert(len(byteload_size_B_list) == num_experiments)
    assert(len(inter_byteload_period_us_list) == num_experiments)

    ssird_qts_results_list = []
    dctcp_qts_results_list = []
    ssird_fct_list = []
    dctcp_fct_list = []
    for i in range(0, num_experiments):
        ssird_subpkt_result, dctcp_subpkt_result = get_qts_result_ssird_dctcp(HOST, src, dst, num_flows, num_byteloads_per_flow_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i], title_addendum) 
        ssird_qts_results_list.append(ssird_subpkt_result)
        dctcp_qts_results_list.append(dctcp_subpkt_result)
        ssird_fct_list.append(ssird_subpkt_result.activity_end_time_s)
        dctcp_fct_list.append(dctcp_subpkt_result.activity_end_time_s)

    ssird_thrpt_gbps_list = [x.get_avg_thrpt_gbps() for x in ssird_qts_results_list]
    dctcp_thrpt_gbps_list = [x.get_avg_thrpt_gbps() for x in dctcp_qts_results_list]

    return ssird_thrpt_gbps_list, dctcp_thrpt_gbps_list, ssird_fct_list, dctcp_fct_list 

'''
NOTE: these only use traffic from qts_host_0_tor4!
def plot_thrpt_ssird_dctcp(ssird_thrpt_gbps_list, dctcp_thrpt_gbps_list, byteload_size_B_list, overall_gdpt_gbps, num_flows, flow_size_B, flow_rate_gbps, is_log_x=False, y_lim=None, is_per_flow=False,title_addendum=""):
    Path(PATH_TO_THRPT_COMPARE_PARENT_DIR).mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10,6))
    if y_lim:
        plt.ylim(y_lim)

    plt.plot(byteload_size_B_list, ssird_thrpt_gbps_list, label="SSIRD", linestyle="-", marker="o", color=SSIRD_PLOT_COLOUR)
    # plt.plot(byteload_size_B_list, dctcp_thrpt_gbps_list, label="DCTCP", linestyle="-", marker="o", color=IDEAL_PLOT_COLOUR)
    plt.plot(byteload_size_B_list, [flow_rate_gbps]*len(ssird_thrpt_gbps_list), label="Application Goodput", linestyle=":", marker=None, color="g")

    plt.xlabel('Byteload Size (B)')
    plt.ylabel('Network Throughput (Gbps)')

    filename_prefix = None
    if (is_per_flow):
        plt.title(f"SSIRD vs DCTCP: Per-Flow Network Throughput @ {overall_gdpt_gbps}Gbps Application Goodput\n({num_flows} x {flow_size_B}B flows, each at {flow_rate_gbps}Gbps)\n{title_addendum}")
        filename_prefix = "PERFLOW_"
    else:
        plt.title(f"SSIRD vs DCTCP: Total Network Throughput @ {overall_gdpt_gbps}Gbps Application Goodput\n({num_flows} x {flow_size_B}B flows, each at {flow_rate_gbps}Gbps)\n{title_addendum}")
        filename_prefix = "TOTAL_"
    
    plt.legend()
    if (is_log_x): plt.xscale('log')
    plt.grid(True)

    filename = f"{filename_prefix}ssird_vs_dctcp_subpkt_multiflow_thrpt_vs_byteload_size_{num_flows}flo_{flow_rate_gbps}Gbps_each{title_addendum}.png"
    plt.savefig(f"{PATH_TO_THRPT_COMPARE_PARENT_DIR}{filename}")
    plt.close()

def plot_overall_and_perflow_thrpt_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_total_gdpt_gbps, title_addendum="", y_lim_total=None, y_lim_perflow=None):
    flow_size_B = num_byteloads_per_flow_list[0] * byteload_size_B_list[0]
    assert(all(n * b == flow_size_B for n, b in zip(num_byteloads_per_flow_list, byteload_size_B_list)))

    # OVERALL: -----
    ssird_thrpt_gbps_list, dctcp_thrpt_gbps_list, ssird_fct_s_list, dctcp_fct_s_list = get_qts_thrpt_ssird_dctcp("host_0", "tor_4", num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, title_addendum)

    plot_thrpt_ssird_dctcp(ssird_thrpt_gbps_list, dctcp_thrpt_gbps_list, byteload_size_B_list, overall_gdpt_gbps, num_flows, flow_size_B, flow_rate_gbps, is_log_x=True, y_lim=y_lim_total, title_addendum=title_addendum + "_overall")

    print(f"Theoretical Overall Gdpt Gbps: {theoretical_total_gdpt_gbps}")
    print(f"SSIRD Thrpt Gbps: {ssird_thrpt_gbps_list}")
    print(f"DCTCP Thrpt Gbps: {dctcp_thrpt_gbps_list}")
    print(f"SSIRD NW Active Duration (s): {ssird_fct_s_list}")
    print(f"DCTCP NW Active Duration (s): {dctcp_fct_s_list}")

    print("---")
    # PER FLOW: -----
    # we can only do this cuz our experiment uses num_flows flows in parallel!
    ssird_thrpt_gbps_per_flow_list = [x / num_flows for x in ssird_thrpt_gbps_list]
    dctcp_thrpt_gbps_per_flow_list = [x / num_flows for x in dctcp_thrpt_gbps_list]

    plot_thrpt_ssird_dctcp(ssird_thrpt_gbps_per_flow_list, dctcp_thrpt_gbps_per_flow_list, byteload_size_B_list, flow_rate_gbps, num_flows, flow_size_B, flow_rate_gbps, is_per_flow=True, y_lim=y_lim_perflow, is_log_x=True, title_addendum=title_addendum + "_perflow")

    print(f"Theoretical Overall Gdpt Gbps: {theoretical_total_gdpt_gbps}")
    print(f"SSIRD Thrpt Per Flow Gbps: {ssird_thrpt_gbps_per_flow_list}")
    print(f"DCTCP Thrpt Per Flow Gbps: {dctcp_thrpt_gbps_per_flow_list}")

def compare_thrpt_subpkt_multiflow_4B_to_4000B_1flo(y_lim_total=None, y_lim_perflow=None):
    # INFO:__main__:Total Flow Size (Bytes): 40000
    # INFO:__main__:Total Injection Period (us): 10000
    # INFO:__main__:Byteload Size (Bytes): [4, 40, 400, 4000]
    # INFO:__main__:Num Byteloads: [10000, 1000, 100, 10]
    # INFO:__main__:Intervals (us): [1, 10, 100, 1000]
    # INFO:__main__:Num flows: 1
    # DEBUG:__main__:Flow start times (us): [0]
    # INFO:__main__:Gdpt Gbps theoretical: [0.032, 0.03200000000000001, 0.03200000000000001, 0.032]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [0.03199999999999829, 0.03199999999999947, 0.03199999999999994, 0.031999999999998786]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [0.03199999999999829, 0.03199999999999947, 0.03199999999999994, 0.031999999999998786]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[0.03199999999999829], [0.03199999999999947], [0.03199999999999994], [0.031999999999998786]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[0.03199999999999829], [0.03199999999999947], [0.03199999999999994], [0.031999999999998786]]
    # INFO:__main__:* Sim duration (SSIRD): [0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* Sim duration (DCTCP): [0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* SSIRD FCT: [[0.010001574000000346], [0.009997559000000322], [0.009907617000001423], [0.009008002000001625]]
    # INFO:__main__:* DCTCP FCT: [[0.010001513000000628], [0.009992519000000755], [0.009902575999999996], [0.00900296200000028]]

    print("@@ 1 FLO")
    title_addendum = "_subpkt_multiflow"

    num_flows = 1
    num_byteloads_per_flow_list = [10000, 1000, 100, 10] # should be [10000, 1000, 100, 10] but there was a naming bug in the experiment
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [1, 10, 100, 1000]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 0.032
    overall_gdpt_gbps = 0.032

    plot_overall_and_perflow_thrpt_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def compare_thrpt_subpkt_multiflow_4B_to_4000B_2flo(y_lim_total=None, y_lim_perflow=None):
    # INFO:__main__:Total Flow Size (Bytes): 40000
    # INFO:__main__:Total Injection Period (us): 10000
    # INFO:__main__:Byteload Size (Bytes): [4, 40, 400, 4000]
    # INFO:__main__:Num Byteloads: 10
    # INFO:__main__:Intervals (us): [1, 10, 100, 1000]
    # INFO:__main__:Num flows: 2
    # DEBUG:__main__:Flow start times (us): [0, 1]
    # INFO:__main__:Gdpt Gbps theoretical: [0.064, 0.06400000000000002, 0.06400000000000002, 0.064]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [0.06399999999999657, 0.06399999999999895, 0.06399999999999988, 0.06399999999999757]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [0.06399999999999657, 0.06399999999999895, 0.06399999999999988, 0.06399999999999757]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[0.03199999999999829, 0.03199999999999829], [0.03199999999999947, 0.03199999999999947], [0.03199999999999994, 0.03199999999999994], [0.031999999999998786, 0.031999999999998786]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[0.03199999999999829, 0.03199999999999829], [0.03199999999999947, 0.03199999999999947], [0.03199999999999994, 0.03199999999999994], [0.031999999999998786, 0.031999999999998786]]
    # INFO:__main__:* Sim duration (SSIRD): [0.011, 0.011, 0.011, 0.011]
    # INFO:__main__:* Sim duration (DCTCP): [0.011, 0.011, 0.011, 0.011]
    # INFO:__main__:* SSIRD FCT: [[0.010001604000001052, 0.010001563999999519], [0.009998579000001229, 0.009996558999999294], [0.009908637000000553, 0.009906617000000395], [0.009009022000000755, 0.009007002000000597]]
    # INFO:__main__:* DCTCP FCT: [[0.010001513000000628, 0.010001512999998852], [0.009992519000000755, 0.009992518999998978], [0.009902575999999996, 0.009902575999999996], [0.00900296200000028, 0.00900296200000028]]

    print("@@ 2 FLO")
    title_addendum = "_subpkt_multiflow_full_parallel"

    num_flows = 2
    num_byteloads_per_flow_list = [10000, 1000, 100, 10] # should be [10000, 1000, 100, 10] but there was a naming bug in the experiment
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [1, 10, 100, 1000]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 0.032
    overall_gdpt_gbps = 0.064

    plot_overall_and_perflow_thrpt_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def compare_thrpt_subpkt_multiflow_4B_to_4000B_10flo(y_lim_total=None, y_lim_perflow=None):
    # INFO:__main__:Total Flow Size (Bytes): 40000
    # INFO:__main__:Total Injection Period (us): 10000
    # INFO:__main__:Byteload Size (Bytes): [4, 40, 400, 4000]
    # INFO:__main__:Num Byteloads: [10000, 1000, 100, 10]
    # INFO:__main__:Intervals (us): [1, 10, 100, 1000]
    # INFO:__main__:Num flows: 10
    # DEBUG:__main__:Flow start times (us): [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    # INFO:__main__:Thrpt Gbps theoretical: [0.32, 0.32, 0.32, 0.32]
    # INFO:__main__:Thrpt Gbps measured (SSIRD): [0.3199999999999999, 0.3200000000000004, 0.3199999999999994, 0.3200000000000005]
    # INFO:__main__:Thrpt Gbps measured (DCTCP): [0.3199999999999999, 0.3200000000000004, 0.3199999999999994, 0.3200000000000005]
    # DEBUG:__main__:Thrpt Gbps measured per flow (SSIRD): [[0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03200000000000397, 0.03199999999999829, 0.03200000000000397, 0.03199999999999829, 0.03199999999999829, 0.03200000000000397, 0.03199999999999829], [0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03200000000000516, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947], [0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994], [0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.03200000000000511, 0.031999999999998786, 0.03200000000000511, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786]]
    # DEBUG:__main__:Thrpt Gbps measured per flow (DCTCP): [[0.03199999999999829, 0.03199999999999829, 0.03199999999999829, 0.03200000000000397, 0.03199999999999829, 0.03200000000000397, 0.03199999999999829, 0.03199999999999829, 0.03200000000000397, 0.03199999999999829], [0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03200000000000516, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947, 0.03199999999999947], [0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994, 0.03199999999999994], [0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.03200000000000511, 0.031999999999998786, 0.03200000000000511, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786, 0.031999999999998786]]
    # INFO:__main__:* Sim duration (SSIRD): [0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* Sim duration (DCTCP): [0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* SSIRD FCT: [[0.01000184400000137, 0.010001803999999836, 0.01000176400000008, 0.010001724000000323, 0.010001684000000566, 0.01000155699999894, 0.010001540999999392, 0.010001554000000468, 0.010001536999999061, 0.010001520000001207], [0.00999257900000039, 0.009992568999999563, 0.009992559000000512, 0.009992578999998614, 0.009992568999999563, 0.009992558999998735, 0.00999257900000039, 0.009992569000001339, 0.009992559000000512, 0.00999257900000039], [0.009916617000000016, 0.009914627000000564, 0.009912637000001112, 0.009910616999999178, 0.009908626999999726, 0.009902616999999836, 0.009902636999999714, 0.009902627000000663, 0.009902616999999836, 0.009902636999999714], [0.009017002000000218, 0.00901501199999899, 0.009013022000001314, 0.00901100199999938, 0.009009011999999927, 0.009003002000000038, 0.009003021999999916, 0.009003012000000865, 0.009003002000000038, 0.009003021999999916]]
    # INFO:__main__:* DCTCP FCT: [[0.012579699000001554, 0.012579737999999452, 0.012579751000000527, 0.012579737999999452, 0.012579732000000732, 0.012579731999998955, 0.012579706000000357, 0.012578756999999996, 0.01257869300000003, 0.012577719000001153], [0.009992519000000755, 0.009992518999998978, 0.009992519000000755, 0.009992518999998978, 0.009992519000000755, 0.009992518999998978, 0.009992519000000755, 0.009992519000000755, 0.009992518999998978, 0.009992519000000755], [0.009902575999999996, 0.009902575999999996, 0.009902575999999996, 0.009902575999999996, 0.009902575999999996, 0.009902575999999996, 0.009902575999999996, 0.009902575999999996, 0.009902575999999996, 0.009902575999999996], [0.00900296200000028, 0.00900296200000028, 0.00900296200000028, 0.00900296200000028, 0.00900296200000028, 0.009002961999998504, 0.00900296200000028, 0.00900296200000028, 0.00900296200000028, 0.00900296200000028]]

    print("@@ 10 FLO")
    title_addendum = "_subpkt_multiflow"

    num_flows = 10
    num_byteloads_per_flow_list = [10000, 1000, 100, 10] # should be [10000, 1000, 100, 10] but there was a naming bug in the experiment
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [1, 10, 100, 1000]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 0.032
    overall_gdpt_gbps = 0.32

    plot_overall_and_perflow_thrpt_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def compare_thrpt_subpkt_multiflow_4B_to_4000B_15flo_fastpace(y_lim_total=None, y_lim_perflow=None):
    # INFO:__main__:Total Flow Size (Bytes): 40000
    # INFO:__main__:Total Injection Period (us): 100.0
    # INFO:__main__:Byteload Size (Bytes): [4, 40, 400, 4000]
    # INFO:__main__:Num Byteloads: [10000, 1000, 100, 10]
    # INFO:__main__:Intervals (us): [0.01, 0.1, 1.0, 10.0]
    # INFO:__main__:Num flows: 15
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [48.0, 48.0, 48.0, 48.0]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [48.00448044770111, 48.044844844664645, 48.452525252273034, 52.97777777769212]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [48.00448044770111, 48.044844844664645, 48.452525252273034, 52.97777777769212]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089], [3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982], [3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343], [3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089], [3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982], [3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343], [3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826]]
    # INFO:__main__:* Sim duration (SSIRD): [0.00106, 0.00106, 0.00106, 0.00106]
    # INFO:__main__:* Sim duration (DCTCP): [0.02, 0.017, 0.017, 0.017]
    # INFO:__main__:* SSIRD FCT: [[0.0003420990000009283, 0.00034547899999992637, 0.00034886500000119725, 0.00035225100000069176, 0.00035563600000010354, 0.0003590220000013744, 0.0003624080000008689, 0.00036579400000036344, 0.0003691800000016343, 0.00037256600000112883, 0.00037595200000062334, 0.00037933800000011786, 0.00038272400000138873, 0.00038611000000088325, 0.00038949600000037776], [0.00010683200000016768, 0.00011021100000085937, 0.00011359700000035389, 0.00011698300000162476, 0.00012036900000111928, 0.0001237550000006138, 0.0001271410000001083, 0.00013052700000137918, 0.0001339130000008737, 0.0001372990000003682, 0.00014068499999986273, 0.0001440710000011336, 0.0001474570000006281, 0.0001508420000000399, 0.00015422800000131076], [0.00010167800000004945, 0.00010171600000141723, 0.00010175400000100865, 0.00010179300000068281, 0.00010183100000027423, 0.00010186999999994839, 0.00010190800000131617, 0.00010194600000090759, 0.00010198500000058175, 0.00010202300000017317, 0.00010206200000162369, 0.00010210000000121511, 0.00010213800000080653, 0.00010217700000048069, 0.00010513900000042042], [9.307800000080135e-05, 9.815200000140578e-05, 9.849800000161224e-05, 9.883700000123952e-05, 9.917700000094953e-05, 9.951600000057681e-05, 9.985500000020409e-05, 0.00010019400000160772, 0.000100533000001235, 0.00010087300000094501, 0.00010121200000057229, 0.00010155100000019956, 0.0001018900000016032, 0.00010222900000123047, 0.00010294900000040741]]
    # INFO:__main__:* DCTCP FCT: [[0.018869601000000458, 0.01886961300000145, 0.01886962600000075, 0.01886963900000005, 0.018869652000001125, 0.018869665000000424, 0.018869677000001417, 0.018869690000000716, 0.018869703000000015, 0.01886971600000109, 0.01886972900000039, 0.018869741000001383, 0.018869754000000682, 0.018869766999999982, 0.018869780000001057], [0.0018871410000009803, 0.0018871530000001968, 0.0018871660000012724, 0.0018871790000005717, 0.001887191999999871, 0.0018872050000009466, 0.0018872170000001631, 0.0018872300000012387, 0.001887243000000538, 0.0018872560000016136, 0.001887269000000913, 0.0018872810000001294, 0.001887294000001205, 0.0018873070000005043, 0.00188732000000158], [0.00019131400000027554, 0.00019135199999986696, 0.00019139000000123474, 0.00019142800000082616, 0.00019146700000050032, 0.00019150500000009174, 0.00019154300000145952, 0.00019158100000105094, 0.0001916200000007251, 0.00019165800000031652, 0.0001921230000014873, 0.00019216100000107872, 0.00019219900000067014, 0.00019223700000026156, 0.00019227599999993572], [9.296200000008525e-05, 9.330000000140615e-05, 9.363900000103342e-05, 9.39780000006607e-05, 9.431700000028798e-05, 9.465500000160887e-05, 9.499400000123615e-05, 9.533300000086342e-05, 9.56720000004907e-05, 9.601000000003523e-05, 9.634900000143887e-05, 9.668800000106614e-05, 9.702600000061068e-05, 9.736500000023796e-05, 9.770399999986523e-05]]

    print("\n@@ 15 FLO NW THRPT")
    title_addendum = "_subpkt_multiflow_fastpace"

    num_flows = 15
    num_byteloads_per_flow_list = [10000, 1000, 100, 10] # should be [10000, 1000, 100, 10] but there was a naming bug in the experiment
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [0.01, 0.1, 1, 10]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 3.2
    overall_gdpt_gbps = 48.0

    plot_overall_and_perflow_thrpt_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)
    
def do_thrpt_plots():
    # y_lim_perflow = (0, 1.5)
    # y_lim_total = (0, 15)

    # compare_thrpt_subpkt_multiflow_4B_to_4000B_1flo(y_lim_total, y_lim_perflow)
    # print("========")
    # compare_thrpt_subpkt_multiflow_4B_to_4000B_2flo(y_lim_total, y_lim_perflow)
    # print("========")
    # compare_thrpt_subpkt_multiflow_4B_to_4000B_10flo(y_lim_total, y_lim_perflow)

    compare_thrpt_subpkt_multiflow_4B_to_4000B_15flo_fastpace()
'''

if __name__ == "__main__":
    # do_thrpt_plots()
    do_nw_data_plots()

    # # The following is for is for host1 to tor 4:
    # # 4B per byteload:
    # ssird_subpkt_result_4B, _ = get_qts_result_ssird_dctcp(HOST, "host_1", "tor_4", num_flows=15, num_byteloads_per_flow=10000, byteload_size_B=4, inter_byteload_period_us=0.01, title_addendum="_subpkt_multiflow_fastpace") 
    # ssird_thrpt_4B = ssird_subpkt_result_4B.get_avg_thrpt_gbps()
    # ssird_fct_4B = ssird_subpkt_result_4B.activity_end_time_s
    # ssird_total_nw_data_w_overheads_4B_B = ssird_thrpt_4B * pow(10,9) * ssird_fct_4B / 8
    # print(ssird_total_nw_data_w_overheads_4B_B)

    # # 4KB per byteload:
    # ssird_subpkt_result_4KB, _ = get_qts_result_ssird_dctcp(HOST, "host_1", "tor_4", num_flows=15, num_byteloads_per_flow=10, byteload_size_B=4000, inter_byteload_period_us=10, title_addendum="_subpkt_multiflow_fastpace") 
    # ssird_thrpt_4KB = ssird_subpkt_result_4KB.get_avg_thrpt_gbps()
    # ssird_fct_4KB = ssird_subpkt_result_4KB.activity_end_time_s
    # ssird_total_nw_data_w_overheads_4KB_B = ssird_thrpt_4KB * pow(10,9) * ssird_fct_4KB / 8
    # print(ssird_total_nw_data_w_overheads_4KB_B)