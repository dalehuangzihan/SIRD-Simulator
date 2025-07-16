import csv
from pathlib import Path
import statistics
import matplotlib.pyplot as plt

PATH_TO_SCRIPTS_R2P2 = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/scripts/r2p2/"
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

def get_qts_result_path(proto, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum = ""):
    if proto.upper() == SSIRD_PROTO_NAME: 
        return f"{PATH_TO_SIM_RESULTS}{SSIRD_PROTO_NAME}-{num_flows}flo-{num_byteloads_per_flow}#-{byteload_size_B}B-{inter_byteload_period_us}us{title_addendum}/data/{SSIRD_PROTO_NAME}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

    elif proto.upper() == DCTCP_PROTO_NAME:
        return f"{PATH_TO_SIM_RESULTS}{DCTCP_PROTO_NAME}-{DCTCP_ECN_THRESH}-{num_flows}flo-{num_byteloads_per_flow}#-{byteload_size_B}B-{inter_byteload_period_us}us{title_addendum}/data/{DCTCP_PROTO_NAME}-{DCTCP_ECN_THRESH}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

    else:
        print(f"ERROR: proto name '{proto}' unrecognised!")

def get_qts_result_ssird_dctcp(nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum=""):
    ssird_qts_result_path = get_qts_result_path(SSIRD_PROTO_NAME, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum)

    dctcp_qts_result_path = get_qts_result_path(DCTCP_PROTO_NAME, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum)

    ssird_timestamp_cutoff_s = get_qts_timestamp_cutoff_from_csv(ssird_qts_result_path)
    dctcp_timestamp_cutoff_s = get_qts_timestamp_cutoff_from_csv(dctcp_qts_result_path)

    ssird_qts_results_obj = get_qts_results_from_csv(nw_elem, src, dst, ssird_qts_result_path, ssird_timestamp_cutoff_s)
    dctcp_qts_results_obj = get_qts_results_from_csv(nw_elem, src, dst, dctcp_qts_result_path, dctcp_timestamp_cutoff_s)

    return ssird_qts_results_obj, dctcp_qts_results_obj

'''
========== NW OVERHEAD PLOTS ==========
'''
def get_qts_nw_data_B_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, title_addendum=""):
    ssird_thrpt_gbps_list, dctcp_thrpt_tbps_list, ssird_fct_list, dctcp_fct_list = get_qts_thrpt_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, title_addendum)

    ssird_total_nw_data_w_overheads_B = [gbps * pow(10,9) * t / 8 for gbps, t in zip(ssird_thrpt_gbps_list, ssird_fct_list)]
    dctcp_total_nw_data_w_overheads_B = [gbps * pow(10,9) * t / 8 for gbps, t in zip(dctcp_thrpt_tbps_list, dctcp_fct_list)]

    app_data_total_B = num_flows * num_byteloads_per_flow_list[0] * byteload_size_B_list[0]
    assert(all(num_flows * n * b == app_data_total_B for n, b in zip(num_byteloads_per_flow_list, byteload_size_B_list)))

    return ssird_total_nw_data_w_overheads_B, dctcp_total_nw_data_w_overheads_B, app_data_total_B

def plot_nw_data_B_ssird_dctcp(ssird_nw_data_B_list, dctcp_nw_data_B_list, byteload_size_B_list, app_data_total_B, num_flows, flow_size_B, flow_rate_gbps, is_log_x=False, y_lim=None, is_per_flow=False,title_addendum=""):
    Path(PATH_TO_NW_DATA_COMPARE_PARENT_DIR).mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10,6))
    if y_lim:
        plt.ylim(y_lim)

    plt.plot(byteload_size_B_list, ssird_nw_data_B_list, label="SSIRD", linestyle="-", marker="o", color=SSIRD_PLOT_COLOUR)
    plt.plot(byteload_size_B_list, dctcp_nw_data_B_list, label="DCTCP", linestyle="-", marker="o", color=IDEAL_PLOT_COLOUR)
    plt.plot(byteload_size_B_list, [app_data_total_B]*len(ssird_nw_data_B_list), label="Application", linestyle=":", marker=None, color="g")

    plt.xlabel('Byteload Size (B)')
    plt.ylabel('Network Data (B)')

    filename_prefix = None
    if (is_per_flow):
        plt.title(f"SSIRD vs DCTCP: Per-Flow Network Data @ {app_data_total_B}B App Data\n({num_flows} x {flow_size_B}B flows, each at {flow_rate_gbps}Gbps)\n{title_addendum}")
        filename_prefix = "PERFLOW_"
    else:
        plt.title(f"SSIRD vs DCTCP: Total Network Data @ {app_data_total_B}B App Data\n({num_flows} x {flow_size_B}B flows, each at {flow_rate_gbps}Gbps)\n{title_addendum}")
        filename_prefix = "TOTAL_"
    
    plt.legend()
    if (is_log_x): plt.xscale('log')
    plt.grid(True)

    filename = f"{filename_prefix}ssird_vs_dctcp_subpkt_multiflow_nw_data_vs_byteload_size_{num_flows}flo_{flow_rate_gbps}Gbps_each{title_addendum}.png"
    plt.savefig(f"{PATH_TO_NW_DATA_COMPARE_PARENT_DIR}{filename}")
    plt.close()

def plot_overall_and_perflow_nw_data_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_total_gdpt_gbps, title_addendum="", y_lim_total=None, y_lim_perflow=None):
    flow_size_B = num_byteloads_per_flow_list[0] * byteload_size_B_list[0]
    assert(all(n * b == flow_size_B for n, b in zip(num_byteloads_per_flow_list, byteload_size_B_list)))

    # OVERALL: -----
    ssird_total_nw_data_B, dctcp_total_nw_data_B, app_data_total_B = get_qts_nw_data_B_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, title_addendum)
    ssird_overheads_total_B = [s - app_data_total_B for s in ssird_total_nw_data_B]
    ssird_total_nw_data_B = list(map(lambda x: round(x, 2), ssird_total_nw_data_B))
    dctcp_total_nw_data_B = list(map(lambda x: round(x, 2), dctcp_total_nw_data_B))
    ssird_overheads_total_B = list(map(lambda x: round(x,2), ssird_overheads_total_B))

    plot_nw_data_B_ssird_dctcp(ssird_total_nw_data_B, dctcp_total_nw_data_B, byteload_size_B_list, app_data_total_B, num_flows, flow_size_B, flow_rate_gbps, is_log_x=True, y_lim=y_lim_total, title_addendum=title_addendum + "_overall")

    print(f"Theoretical Overall Gdpt Gbps: {theoretical_total_gdpt_gbps}")
    print(f"Total App Data (B): {app_data_total_B}")
    print(f"SSIRD NW Data Total (B): {ssird_total_nw_data_B}")
    print(f"DCTCP NW Data Total (B): {dctcp_total_nw_data_B}")
    print(f"SSIRD Overheads Total (B): {ssird_overheads_total_B}")

    print("---")
    # PER FLOW: -----
    # we can only do this cuz our experiment uses num_flows flows in parallel!
    ssird_perflow_nw_data_B = [x / num_flows for x in ssird_total_nw_data_B]
    dctcp_perflow_nw_data_B = [x / num_flows for x in dctcp_total_nw_data_B]
    app_data_perflow_B = app_data_total_B / num_flows
    ssird_overheads_perflow_B = [s - app_data_perflow_B for s in ssird_perflow_nw_data_B]
    ssird_perflow_nw_data_B = list(map(lambda x: round(x, 2), ssird_perflow_nw_data_B))
    dctcp_perflow_nw_data_B = list(map(lambda x: round(x, 2), dctcp_perflow_nw_data_B))
    ssird_overheads_perflow_B = list(map(lambda x: round(x,2), ssird_overheads_perflow_B))

    plot_nw_data_B_ssird_dctcp(ssird_perflow_nw_data_B, dctcp_perflow_nw_data_B, byteload_size_B_list, app_data_perflow_B, num_flows, flow_size_B, flow_rate_gbps, is_per_flow=True, y_lim=y_lim_perflow, is_log_x=True, title_addendum=title_addendum + "_perflow")

    print(f"Theoretical Overall Gdpt Gbps: {theoretical_total_gdpt_gbps}")
    print(f"App Data Per Flow (B): {app_data_perflow_B}")
    print(f"SSIRD NW Data Per Flow (B): {ssird_perflow_nw_data_B}")
    print(f"DCTCP NW Data Per Flow (B): {dctcp_perflow_nw_data_B}")
    print(f"SSIRD Overheads Per Flow (B): {ssird_overheads_perflow_B}")

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

def compare_nw_data_subpkt_multiflow_4B_to_4000B_10flo(y_lim_total=None, y_lim_perflow=None):
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

    plot_overall_and_perflow_nw_data_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, flow_rate_gbps, overall_gdpt_gbps, theoretical_gdpt_total_parallel_gbps, title_addendum, y_lim_total, y_lim_perflow)

def do_nw_data_plots():
    compare_nw_data_subpkt_multiflow_4B_to_4000B_1flo()
    print("=====")
    compare_nw_data_subpkt_multiflow_4B_to_4000B_2flo()
    print("=====")
    compare_nw_data_subpkt_multiflow_4B_to_4000B_10flo()

'''
========== THRPT vs GDPT PLOTS ========== 
'''
def get_qts_thrpt_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, title_addendum=""):
    num_experiments = len(num_byteloads_per_flow_list)
    assert(len(byteload_size_B_list) == num_experiments)
    assert(len(inter_byteload_period_us_list) == num_experiments)

    ssird_qts_results_list = []
    dctcp_qts_results_list = []
    ssird_fct_list = []
    dctcp_fct_list = []
    for i in range(0, num_experiments):
        ssird_subpkt_result, dctcp_subpkt_result = get_qts_result_ssird_dctcp(HOST, "host_0", "tor_4", num_flows, num_byteloads_per_flow_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i], title_addendum) 
        ssird_qts_results_list.append(ssird_subpkt_result)
        dctcp_qts_results_list.append(dctcp_subpkt_result)
        ssird_fct_list.append(ssird_subpkt_result.activity_end_time_s)
        dctcp_fct_list.append(dctcp_subpkt_result.activity_end_time_s)

    ssird_thrpt_gbps_list = [x.get_avg_thrpt_gbps() for x in ssird_qts_results_list]
    dctcp_thrpt_gbps_list = [x.get_avg_thrpt_gbps() for x in dctcp_qts_results_list]

    return ssird_thrpt_gbps_list, dctcp_thrpt_gbps_list, ssird_fct_list, dctcp_fct_list 

def plot_thrpt_ssird_dctcp(ssird_thrpt_gbps_list, dctcp_thrpt_gbps_list, byteload_size_B_list, overall_gdpt_gbps, num_flows, flow_size_B, flow_rate_gbps, is_log_x=False, y_lim=None, is_per_flow=False,title_addendum=""):
    Path(PATH_TO_THRPT_COMPARE_PARENT_DIR).mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10,6))
    if y_lim:
        plt.ylim(y_lim)

    plt.plot(byteload_size_B_list, ssird_thrpt_gbps_list, label="SSIRD", linestyle="-", marker="o", color=SSIRD_PLOT_COLOUR)
    plt.plot(byteload_size_B_list, dctcp_thrpt_gbps_list, label="DCTCP", linestyle="-", marker="o", color=IDEAL_PLOT_COLOUR)
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
    ssird_thrpt_gbps_list, dctcp_thrpt_gbps_list, ssird_fct_s_list, dctcp_fct_s_list = get_qts_thrpt_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, title_addendum)

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

def do_thrpt_plots():
    y_lim_perflow = (0, 1.5)
    y_lim_total = (0, 15)

    compare_thrpt_subpkt_multiflow_4B_to_4000B_1flo(y_lim_total, y_lim_perflow)
    print("========")
    compare_thrpt_subpkt_multiflow_4B_to_4000B_2flo(y_lim_total, y_lim_perflow)
    print("========")
    compare_thrpt_subpkt_multiflow_4B_to_4000B_10flo(y_lim_total, y_lim_perflow)


if __name__ == "__main__":
    # do_thrpt_plots()
    do_nw_data_plots()