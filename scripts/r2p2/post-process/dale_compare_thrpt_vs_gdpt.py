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

def get_qts_result(proto, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum=""):
    qts_result_path = get_qts_result_path(proto, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum)
    # print(ssird_qts_result_path)

    timestamp_cutoff_s = get_qts_timestamp_cutoff_from_csv(qts_result_path)
    qts_results_obj = get_qts_results_from_csv(nw_elem, src, dst, qts_result_path, timestamp_cutoff_s)
    return qts_results_obj

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
        # diff_MB_list = [round(d/pow(10,3), 2) for d in ssird_total_nw_overheads_B_list]
        # plt.ylabel('Network Overhead (KB)')
    else:
        plt.title(f"SSIRD: Total Network Overheads @ {num_flows * flow_size_B/pow(10,6)}MB Total App Data\n({num_flows} x {flow_size_B}B flows, each at {flow_rate_gbps}Gbps; Total App Gdpt: {num_flows * flow_rate_gbps}Gbps)\n{title_addendum}")
        filename_prefix = "DIFF_TOTAL_"
        # diff_MB_list = [round(d/pow(10,6), 2) for d in ssird_total_nw_overheads_B_list]
        # plt.ylabel('Network Overhead (MB)')

    ssird_overhead_per_app_data_byte_B = [overhead / app_data for overhead, app_data in zip(ssird_total_nw_overheads_B_list, app_data_total_B_list)]
    plt.plot(byteload_size_B_list, ssird_overhead_per_app_data_byte_B, label="Total Network Data - App Data", linestyle="-", marker="o", color=SSIRD_PLOT_COLOUR)
    plt.ylabel("Overhead per Byte of App Data (B)")
    plt.legend()

    plt.xlabel('Byteload Size (B)')
    if (is_log_x): plt.xscale('log')
    plt.grid(True)

    filename = f"{filename_prefix}ssird_subpkt_multiflow_nw_data_vs_byteload_size_{num_flows}flo_{flow_rate_gbps}Gbps_each{title_addendum}.png"
    plt.savefig(f"{PATH_TO_NW_DATA_COMPARE_PARENT_DIR}{filename}")
    plt.close()
    print(f"** SSIRD Overhead per App Data (B): {ssird_overhead_per_app_data_byte_B}")

def plot_overall_and_perflow_nw_data_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_total_gdpt_gbps, title_addendum="", y_lim_total=None, y_lim_perflow=None):
    flow_size_B = num_byteloads_per_flow_list[0] * byteload_size_B_list[0]
    assert(all(n * b == flow_size_B for n, b in zip(num_byteloads_per_flow_list, byteload_size_B_list)))

    # OVERALL: -----
    ssird_total_nw_data_h0tor4_B, dctcp_total_nw_data_h0tor4_B, app_data_total_theory_B, app_data_total_measured_h0tor4_B = get_qts_nw_data_B_ssird_dctcp("host_0", "tor_4", num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, overall_gdpt_gbps,title_addendum)
    ssird_total_nw_data_h1tor4_B, dctcp_total_nw_data_h1tor4_B, app_data_total_theory_B, app_data_total_measured_h1tor4_B = get_qts_nw_data_B_ssird_dctcp("host_1", "tor_4", num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, overall_gdpt_gbps,title_addendum)

    ssird_total_nw_data_B = [h0tor4 + h1tor4 for h0tor4, h1tor4 in zip(ssird_total_nw_data_h0tor4_B, ssird_total_nw_data_h1tor4_B)]
    dctcp_total_nw_data_B = [h0tor4 + h1tor4 for h0tor4, h1tor4 in zip(dctcp_total_nw_data_h0tor4_B, dctcp_total_nw_data_h1tor4_B)]
    
    ssird_overheads_total_theory_B = [s - app_data_total_theory_B for s in ssird_total_nw_data_B]
    app_data_total_theory_B_list = [app_data_total_theory_B] * len(ssird_overheads_total_theory_B)

    ssird_total_nw_data_B = list(map(lambda x: round(x, 2), ssird_total_nw_data_B))
    dctcp_total_nw_data_B = list(map(lambda x: round(x, 2), dctcp_total_nw_data_B))
    ssird_overheads_total_theory_B = list(map(lambda x: round(x,2), ssird_overheads_total_theory_B))

    plot_nw_data_MB_ssird_dctcp(ssird_total_nw_data_B, dctcp_total_nw_data_B, byteload_size_B_list, app_data_total_theory_B_list, num_flows, flow_size_B, flow_rate_gbps, is_log_x=True, y_lim=y_lim_total, title_addendum=title_addendum + "_overall")

    print(f"Theoretical Overall Gdpt Gbps: {theoretical_total_gdpt_gbps}")
    print(f"SSIRD NW Data Total (B): {ssird_total_nw_data_B}")
    print(f"DCTCP NW Data Total (B): {dctcp_total_nw_data_B}")
    print(f"** SSIRD Overheads Total (vs theory app data) (B): {ssird_overheads_total_theory_B}")

    # plot total overheads:
    plot_nw_data_MB_overheads_ssird(ssird_overheads_total_theory_B, byteload_size_B_list, app_data_total_theory_B_list, num_flows, flow_size_B, flow_rate_gbps, is_log_x=True, y_lim=y_lim_total, title_addendum=title_addendum + "_overall") 

    print("---")
    # OVERALL (SENDER TO RECEIVER ONLY): -----
    ssird_total_nw_data_sendr_to_recvr_B = ssird_total_nw_data_h0tor4_B
    dctcp_total_nw_data_sendr_to_recvr_B = dctcp_total_nw_data_h0tor4_B

    ssird_overheads_total_s_to_r_theory_B = [s - app_data_total_theory_B for s in ssird_total_nw_data_sendr_to_recvr_B]

    ssird_total_nw_data_sendr_to_recvr_B = list(map(lambda x: round(x, 2), ssird_total_nw_data_sendr_to_recvr_B))
    dctcp_total_nw_data_sendr_to_recvr_B = list(map(lambda x: round(x, 2), dctcp_total_nw_data_sendr_to_recvr_B))
    ssird_overheads_total_s_to_r_theory_B = list(map(lambda x: round(x,2), ssird_overheads_total_s_to_r_theory_B))

    plot_nw_data_MB_ssird_dctcp(ssird_total_nw_data_sendr_to_recvr_B, dctcp_total_nw_data_sendr_to_recvr_B, byteload_size_B_list, app_data_total_theory_B_list, num_flows, flow_size_B, flow_rate_gbps, is_log_x=True, y_lim=y_lim_total, title_addendum=title_addendum + "_overall_s_to_r")

    print(f"Theoretical Overall Gdpt Gbps: {theoretical_total_gdpt_gbps}")
    print(f"SSIRD NW Data Total (Sendr to Recvr Only) (B): {ssird_total_nw_data_sendr_to_recvr_B}")
    print(f"DCTCP NW Data Total (Sendr to Recvr Only) (B): {dctcp_total_nw_data_sendr_to_recvr_B}")
    print(f"** SSIRD Overheads Total (vs theory app data) (Sendr to Recvr Only) (B): {ssird_overheads_total_s_to_r_theory_B}")

    # plot total overheads:
    plot_nw_data_MB_overheads_ssird(ssird_overheads_total_s_to_r_theory_B, byteload_size_B_list, app_data_total_theory_B_list, num_flows, flow_size_B, flow_rate_gbps, is_log_x=True, y_lim=y_lim_total, title_addendum=title_addendum + "_overall_s_to_r") 

    # print("---")
    # # PER FLOW: -----
    # # we can only do this cuz our experiment uses num_flows flows in parallel!
    # ssird_perflow_nw_data_B = [x / num_flows for x in ssird_total_nw_data_B]
    # dctcp_perflow_nw_data_B = [x / num_flows for x in dctcp_total_nw_data_B]
    # app_data_perflow_theory_B = [flow_rate_gbps] * len(ssird_perflow_nw_data_B)
    # ssird_overheads_perflow_theory_B = [s - a for s,a in zip(ssird_perflow_nw_data_B, app_data_perflow_theory_B)] 
    
    # ssird_perflow_nw_data_B = list(map(lambda x: round(x, 2), ssird_perflow_nw_data_B))
    # dctcp_perflow_nw_data_B = list(map(lambda x: round(x, 2), dctcp_perflow_nw_data_B))
    # ssird_overheads_perflow_theory_B = list(map(lambda x: round(x, 2), ssird_overheads_perflow_theory_B))

    # plot_nw_data_MB_ssird_dctcp(ssird_perflow_nw_data_B, dctcp_perflow_nw_data_B, byteload_size_B_list, app_data_perflow_theory_B, num_flows, flow_size_B, flow_rate_gbps, is_per_flow=True, y_lim=y_lim_perflow, is_log_x=True, title_addendum=title_addendum + "_perflow")

    # print(f"Theoretical Perflow Gdpt Gbps: {flow_rate_gbps}")
    # print(f"SSIRD NW Data Per Flow (B): {ssird_perflow_nw_data_B}")
    # print(f"DCTCP NW Data Per Flow (B): {dctcp_perflow_nw_data_B}")
    # print(f"** SSIRD Overheads Per Flow (vs theory app data) (B): {ssird_overheads_perflow_theory_B}")


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


def compare_nw_data_subpkt_4B_to_40000B_15flo_fastpace_extended(y_lim_total=None, y_lim_perflow=None):
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

    print("\n@@ 15 FLO SUBPKT (EXTENDED) FASTPACE NW DATA")
    title_addendum = "_subpkt_multiflow_fastpace_extended"

    num_flows = 15
    num_byteloads_per_flow_list = [10000, 1000, 100, 10, 1] 
    byteload_size_B_list = [4, 40, 400, 4000, 40000]
    inter_byteload_period_us_list = [0.01, 0.1, 1.0, 10.0, 100.0]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 3.2
    overall_gdpt_gbps = 48

    plot_overall_and_perflow_nw_data_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def compare_nw_data_largepkt_200B_to_2MB_31flo_extended(y_lim_total=None, y_lim_perflow=None):
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
    
    print("\n@@ 31 FLO LARGEPKT (EXTENDED) NW DATA")
    title_addendum = "_largepkt_multiflow_extended_31flo"

    num_flows = 31
    num_byteloads_per_flow_list = [10000, 1000, 100, 10, 1] 
    byteload_size_B_list = [200, 2000, 20000, 200000, 2000000]
    inter_byteload_period_us_list = [1.0, 10.0, 100.0, 1000.0, 10000.0]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 1.6
    overall_gdpt_gbps = 49.6

    plot_overall_and_perflow_nw_data_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def compare_nw_data_fullrange_20B_to_2MB_31flo(y_lim_total=None, y_lim_perflow=None):
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
    
    print("\n@@ 31 FLO FULLRANGE NW DATA")
    title_addendum = "_fullrange_31flo"

    num_flows = 31
    num_byteloads_per_flow_list = [10000, 1000, 100, 10, 1] 
    byteload_size_B_list = [20, 200, 2000, 20000, 200000]
    inter_byteload_period_us_list = [0.1, 1.0, 10.0, 100.0, 1000.0]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 1.6
    overall_gdpt_gbps = 49.6

    plot_overall_and_perflow_nw_data_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def compare_nw_data_fullrange_5flo_8gbps_1msRTT(y_lim_total=None, y_lim_perflow=None):
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
    # INFO:__main__:* Sim duration (SSIRD): [0.01, 0.01, 0.01, 0.01, 0.01]
    # INFO:__main__:* Sim duration (DCTCP): [0.25, 0.15, 0.15, 0.15, 0.15]
    # INFO:__main__:* SSIRD FCT: [[0.0015424730000006548, 0.0015846530000001025, 0.001626863000000256, 0.0016690730000004095, 0.0017112530000016335], [0.001650353000000493, 0.0018013730000010497, 0.0019521430000004614, 0.002102363000000551, 0.002253353000000402], [0.00169073600000047, 0.0018903230000013593, 0.0020808350000010023, 0.0022803230000008057, 0.002470859000000658], [0.0016087169999998707, 0.0018086970000013025, 0.0020087000000010846, 0.002208710000001446, 0.0024086410000005998], [0.0015171160000004846, 0.0015339990000011738, 0.0015508830000001694, 0.0015677660000008586, 0.0015846490000015478]]
    # INFO:__main__:* DCTCP FCT: [[0.001499916000000212, 0.001499924000000874, 0.0014999310000014532, 0.0014999390000003388, 0.0014999470000010007], [0.001499044000000893, 0.0014990670000010198, 0.0014990890000010637, 0.0014991110000011076, 0.0014991330000011516], [0.0014902960000000576, 0.001490468000000078, 0.0014906400000000986, 0.0014908130000002018, 0.0014909850000002223], [0.001401810000000836, 0.0014034980000001696, 0.0014051850000011967, 0.0014068720000004475, 0.0014085600000015575], [0.0025011310000007114, 0.002509867000000554, 0.002518602000000314, 0.0025267230000007856, 0.0025348440000012573]]

    print("\n@@ 5 FLO FULLRANGE NW DATA")
    title_addendum = "_fullrange_5flo_8gbps_total_1msRTT"

    num_flows = 5
    num_byteloads_per_flow_list = [10000, 1000, 100, 10, 1] 
    byteload_size_B_list = [20, 200, 2000, 20000, 200000]
    inter_byteload_period_us_list = [0.1, 1.0, 10.0, 100.0, 1000.0]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 1.6
    overall_gdpt_gbps = 8.0

    plot_overall_and_perflow_nw_data_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def do_nw_data_plots():
    # compare_nw_data_subpkt_multiflow_4B_to_4000B_1flo()
    # print("=====")
    # compare_nw_data_subpkt_multiflow_4B_to_4000B_2flo()
    # print("=====")
    # compare_nw_data_subpkt_multiflow_4B_to_4000B_10flo_slowpace()
    # compare_nw_data_subpkt_multiflow_4B_to_4000B_15flo_fastpace()
    # compare_nw_data_subpkt_multiflow_4B_to_4000B_15flo_slowpace()

    compare_nw_data_subpkt_4B_to_40000B_15flo_fastpace_extended()
    # compare_nw_data_largepkt_200B_to_2MB_31flo_extended()
    compare_nw_data_fullrange_20B_to_2MB_31flo()
    compare_nw_data_fullrange_5flo_8gbps_1msRTT()

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
        ssird_subpkt_result = get_qts_result(SSIRD_PROTO_NAME, HOST, src, dst, num_flows, num_byteloads_per_flow_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i], title_addendum) 
        dctcp_subpkt_result = get_qts_result(DCTCP_PROTO_NAME, HOST, src, dst, num_flows, num_byteloads_per_flow_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i], title_addendum) 
        ssird_qts_results_list.append(ssird_subpkt_result)
        dctcp_qts_results_list.append(dctcp_subpkt_result)
        ssird_fct_list.append(ssird_subpkt_result.activity_end_time_s)
        dctcp_fct_list.append(dctcp_subpkt_result.activity_end_time_s)

    ssird_thrpt_gbps_list = [x.get_avg_thrpt_gbps() for x in ssird_qts_results_list]
    dctcp_thrpt_gbps_list = [x.get_avg_thrpt_gbps() for x in dctcp_qts_results_list]

    return ssird_thrpt_gbps_list, dctcp_thrpt_gbps_list, ssird_fct_list, dctcp_fct_list 

''' # NOTE: these only use traffic from qts_host_0_tor4! '''
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
    print(f"SSIRD Measured Thrpt Gbps: {ssird_thrpt_gbps_list}")
    print(f"DCTCP Measured Thrpt Gbps: {dctcp_thrpt_gbps_list}")
    print(f"SSIRD Measured NW Active Duration (s): {ssird_fct_s_list}")
    print(f"DCTCP Measured NW Active Duration (s): {dctcp_fct_s_list}")

    print("---")
    # PER FLOW: -----
    # we can only do this cuz our experiment uses num_flows flows in parallel!
    ssird_thrpt_gbps_per_flow_list = [x / num_flows for x in ssird_thrpt_gbps_list]
    dctcp_thrpt_gbps_per_flow_list = [x / num_flows for x in dctcp_thrpt_gbps_list]

    plot_thrpt_ssird_dctcp(ssird_thrpt_gbps_per_flow_list, dctcp_thrpt_gbps_per_flow_list, byteload_size_B_list, flow_rate_gbps, num_flows, flow_size_B, flow_rate_gbps, is_per_flow=True, y_lim=y_lim_perflow, is_log_x=True, title_addendum=title_addendum + "_perflow")

    print(f"Theoretical Overall Gdpt Gbps: {theoretical_total_gdpt_gbps}")
    print(f"SSIRD Measured Thrpt Per Flow Gbps: {ssird_thrpt_gbps_per_flow_list}")
    print(f"DCTCP Measured Thrpt Per Flow Gbps: {dctcp_thrpt_gbps_per_flow_list}")

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

    print("\n@@ 15 FLO NW THRPT FASTPACE")
    title_addendum = "_subpkt_multiflow_fastpace"

    num_flows = 15
    num_byteloads_per_flow_list = [10000, 1000, 100, 10] # should be [10000, 1000, 100, 10] but there was a naming bug in the experiment
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [0.01, 0.1, 1, 10]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 3.2
    overall_gdpt_gbps = 48.0

    plot_overall_and_perflow_thrpt_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def compare_thrpt_subpkt_multiflow_4B_to_40KB_15flo_fastpace_extended(y_lim_total=None, y_lim_perflow=None):
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

    print("\n@@ 15 FLO NW THRPT FASTPACE EXTENDED")
    title_addendum = "_subpkt_multiflow_fastpace_extended"

    num_flows = 15
    num_byteloads_per_flow_list = [10000, 1000, 100, 10, 1]
    byteload_size_B_list = [4, 40, 400, 4000, 40000]
    inter_byteload_period_us_list = [0.01, 0.1, 1.0, 10.0, 100.0]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 3.2
    overall_gdpt_gbps = 48.0

    plot_overall_and_perflow_thrpt_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)
    
def compare_thrpt_largepkt_200B_to_2MB_31flo_extended(y_lim_total=None, y_lim_perflow=None):
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
    
    print("\n@@ 31 FLO LARGEPKT (EXTENDED) THRPT")
    title_addendum = "_largepkt_multiflow_extended_31flo"

    num_flows = 31
    num_byteloads_per_flow_list = [10000, 1000, 100, 10, 1] 
    byteload_size_B_list = [200, 2000, 20000, 200000, 2000000]
    inter_byteload_period_us_list = [1.0, 10.0, 100.0, 1000.0, 10000.0]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 1.6
    overall_gdpt_gbps = 49.6

    plot_overall_and_perflow_thrpt_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def compare_thrpt_fullrange_20B_to_2MB_31flo(y_lim_total=None, y_lim_perflow=None):
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

    print("\n@@ 31 FLO FULLRANGE THRPT")
    title_addendum = "_fullrange_31flo"

    num_flows = 31
    num_byteloads_per_flow_list = [10000, 1000, 100, 10, 1] 
    byteload_size_B_list = [20, 200, 2000, 20000, 200000]
    inter_byteload_period_us_list = [0.1, 1.0, 10.0, 100.0, 1000.0]

    theoretical_gdpt_total_parallel_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 1.6
    overall_gdpt_gbps = 49.6

    plot_overall_and_perflow_thrpt_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def do_thrpt_plots():
    # y_lim_perflow = (0, 1.5)
    # y_lim_total = (0, 15)

    # compare_thrpt_subpkt_multiflow_4B_to_4000B_1flo(y_lim_total, y_lim_perflow)
    # print("========")
    # compare_thrpt_subpkt_multiflow_4B_to_4000B_2flo(y_lim_total, y_lim_perflow)
    # print("========")
    # compare_thrpt_subpkt_multiflow_4B_to_4000B_10flo(y_lim_total, y_lim_perflow)

    compare_thrpt_subpkt_multiflow_4B_to_40KB_15flo_fastpace_extended()
    # compare_thrpt_largepkt_200B_to_2MB_31flo_extended()
    compare_thrpt_fullrange_20B_to_2MB_31flo()

if __name__ == "__main__":
    do_thrpt_plots()
    print("=====")
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