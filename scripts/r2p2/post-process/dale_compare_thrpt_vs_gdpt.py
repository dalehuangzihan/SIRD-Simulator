import csv
from pathlib import Path
import statistics
import matplotlib.pyplot as plt

PATH_TO_SCRIPTS_R2P2 = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/scripts/r2p2/"
PATH_TO_POSTPROC = f"{PATH_TO_SCRIPTS_R2P2}post-process/"
PATH_TO_SIM_RESULTS = f"{PATH_TO_SCRIPTS_R2P2}coord/results/"
PATH_TO_TMP_PLOT = PATH_TO_POSTPROC + "tmp_plot/"
PATH_TO_GRAPH_FAMILY_PARENT_DIR = PATH_TO_TMP_PLOT + "nw_thrpt_compare_ssird_dctcp/"

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
    def __init__(self, nw_elem, src, dst, timestamps_list, throughput_gbps_list, queueing_KB_list):
        self.nw_elem = nw_elem
        self.src = src
        self.dst = dst
        self.timestamps_list = timestamps_list
        self.throughput_gbps_list = throughput_gbps_list
        self.queueing_KB_list = queueing_KB_list
    
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

        return QmonResults(nw_elem, src, dst, timestamps_list, throughput_gbps_list, queueing_KB_list) 

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
    overall_timestamp_cutoff_s = max(ssird_timestamp_cutoff_s, dctcp_timestamp_cutoff_s)

    ssird_qts_results_obj = get_qts_results_from_csv(nw_elem, src, dst, ssird_qts_result_path, overall_timestamp_cutoff_s)
    dctcp_qts_results_obj = get_qts_results_from_csv(nw_elem, src, dst, dctcp_qts_result_path, overall_timestamp_cutoff_s)

    return ssird_qts_results_obj, dctcp_qts_results_obj

def get_qts_thrpt_diff_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list):
    num_experiments = len(num_byteloads_per_flow_list)
    assert(len(byteload_size_B_list) == num_experiments)
    assert(len(inter_byteload_period_us_list) == num_experiments)

    ssird_qts_results_list = []
    dctcp_qts_results_list = []
    for i in range(0, num_experiments):
        ssird_subpkt_result, dctcp_subpkt_result = get_qts_result_ssird_dctcp(HOST, "host_0", "tor_4", num_flows, num_byteloads_per_flow_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i], title_addendum="_subpkt_multiflow") 
        ssird_qts_results_list.append(ssird_subpkt_result)
        dctcp_qts_results_list.append(dctcp_subpkt_result)

    ssird_thrpt_gbps_list = [x.get_avg_thrpt_gbps() for x in ssird_qts_results_list]
    dctcp_thrpt_gbps_list = [x.get_avg_thrpt_gbps() for x in dctcp_qts_results_list]
    diff_thrpt_gbps_list = [s - d for s, d in zip(ssird_thrpt_gbps_list, dctcp_thrpt_gbps_list)]

    return ssird_thrpt_gbps_list, dctcp_thrpt_gbps_list, diff_thrpt_gbps_list

def plot_thrpt_ssird_dctcp(ssird_thrpt_gbps_list, dctcp_thrpt_gbps_list, byteload_size_B_list, gdpt_gbps, num_flows, flow_size_B, flow_rate_gbps, is_log_x=False, title_addendum=""):
    Path(PATH_TO_GRAPH_FAMILY_PARENT_DIR).mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(10,6))
    plt.plot(byteload_size_B_list, ssird_thrpt_gbps_list, label="SSIRD", linestyle="-", marker="o", color=SSIRD_PLOT_COLOUR)
    plt.plot(byteload_size_B_list, dctcp_thrpt_gbps_list, label="DCTCP", linestyle="-", marker="o", color=IDEAL_PLOT_COLOUR)
    plt.xlabel('Byteload Size (B)')
    plt.ylabel('Network Throughput (Gbps)')
    plt.title(f"SSIRD vs DCTCP: Network Throughput @ {gdpt_gbps}Gbps Application Goodput {title_addendum}\n({num_flows} x {flow_size_B}B flows, each at {flow_rate_gbps}Gbps)")
    plt.legend()
    if (is_log_x): plt.xscale('log')
    plt.grid(True)
    filename = f"ssird_vs_dctcp_subpkt_multiflow_thrpt_vs_byteload_size_{num_flows}flo_{flow_rate_gbps}B_each{title_addendum}.png"
    plt.savefig(f"{PATH_TO_GRAPH_FAMILY_PARENT_DIR}{filename}")
    plt.close()


def compare_thrpt_subpkt_multiflow_4B_to_4000B_2flo():
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

    num_flows = 2
    flow_size_B = 40000
    num_byteloads_per_flow_list = [10000, 1000, 100, 10] # should be [10000, 1000, 100, 10] but there was a naming bug in the experiment
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [1, 10, 100, 1000]

    theoretical_goodput_gbps = num_flows * max(byteload_size_B_list) * 8 / (max(inter_byteload_period_us_list) * pow(10,-6)) * pow(10,-9)

    flow_rate_gbps = 0.032
    overall_gdpt_gbps = 0.064

    ssird_thrpt_gbps_list, dctcp_thrpt_gbps_list, diff_thrpt_gbps_list = get_qts_thrpt_diff_ssird_dctcp(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list)

    plot_thrpt_ssird_dctcp(ssird_thrpt_gbps_list, dctcp_thrpt_gbps_list, byteload_size_B_list, flow_rate_gbps, num_flows, flow_size_B, overall_gdpt_gbps, is_log_x=True)

    print(theoretical_goodput_gbps)
    print(ssird_thrpt_gbps_list)
    print(dctcp_thrpt_gbps_list)
    print(diff_thrpt_gbps_list)

if __name__ == "__main__":
    compare_thrpt_subpkt_multiflow_4B_to_4000B_2flo()

