import sys
import subprocess
from pathlib import Path
import shutil
import numpy as np
import matplotlib.pyplot as plt
import csv

import dale_multiflow_serialiser
import dale_experiment_rig

PATH_TO_SCRIPTS_R2P2 = "/data/dh1723/SIRD-Simulator/scripts/r2p2/"
# PATH_TO_SCRIPTS_R2P2 = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/scripts/r2p2/"
PATH_TO_POSTPROC = f"{PATH_TO_SCRIPTS_R2P2}post-process/"
PATH_TO_SIM_RESULTS = f"{PATH_TO_SCRIPTS_R2P2}coord/results/"
PATH_TO_TMP_PLOT = PATH_TO_POSTPROC + "tmp_plot/"
PATH_TO_QTS_COMPARE_PARENT_DIR = PATH_TO_TMP_PLOT + "qts_direct_comparison_graphs/"

# Common experiment param; value is meaningful only when req_interval_distr is not 'manual'
CLIENT_INJECTION_RATE_GBPS = "60"
DCTCP_ECN_THRESH = 50

AGGR = "aggr"
HOST = "host"
TOR = "tor"

THROUGHPUT_COL = 1
QUEUEING_COL = 2

QTS_CSV_TIMESTEP_S = 0.000001 # 1us

SSIRD_PROTO_NAME = 'SSIRD'
DCTCP_PROTO_NAME = 'DCTCP'

SSIRD_PLOT_COLOUR = 'tab:orange'
DCTCP_PLOT_COLOUR = 'tab:blue'

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

def get_qts_result_path_new(proto, nw_elem, src, dst, num_flows, target_per_flow_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum=""):
    if proto.upper() == SSIRD_PROTO_NAME: 
        return f"{PATH_TO_SIM_RESULTS}{SSIRD_PROTO_NAME}-{experiment_family}{title_addendum}__{num_flows}flo-{round(target_per_flow_gdpt_gbps)}Gbps-{byteload_size_B}B-{inter_byteload_period_nanosec}ns-{experiment_date}/data/{SSIRD_PROTO_NAME}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

    elif proto.upper() == DCTCP_PROTO_NAME:
        return f"{PATH_TO_SIM_RESULTS}{DCTCP_PROTO_NAME}-{DCTCP_ECN_THRESH}-{experiment_family}{title_addendum}__{num_flows}flo-{round(target_per_flow_gdpt_gbps)}Gbps-{byteload_size_B}B-{inter_byteload_period_nanosec}ns-{experiment_date}/data/{DCTCP_PROTO_NAME}-{DCTCP_ECN_THRESH}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

    else:
        print(f"ERROR: proto name '{proto}' unrecognised!")

def get_qts_result_new(proto, nw_elem, src, dst, num_flows, target_per_flow_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum):
    qts_result_path = get_qts_result_path_new(proto, nw_elem, src, dst, num_flows, target_per_flow_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum)
    # print(ssird_qts_result_path)

    timestamp_cutoff_s = get_qts_timestamp_cutoff_from_csv(qts_result_path)
    qts_results_obj = get_qts_results_from_csv(nw_elem, src, dst, qts_result_path, timestamp_cutoff_s)
    return qts_results_obj

def plot_thrpt_comparison_graph_trimmed(ssird_thrpt_list, dctcp_thrpt_list, time_axis_s_list, experiment_name, title_addendum):
    plt.figure(figsize=(10,6))

    time_axis_ms_list = [s * 1000 for s in time_axis_s_list]
    plt.plot(time_axis_ms_list, ssird_thrpt_list, label="SSIRD", linestyle="-", marker=None, color=SSIRD_PLOT_COLOUR)
    plt.plot(time_axis_ms_list, dctcp_thrpt_list, label="DCTCP", linestyle="-", marker=None, color=DCTCP_PLOT_COLOUR)
    plt.ylabel('Network Throughput (Gbps)')
    plt.xlabel('Time (ms)')
    plt.title(f"SSIRD vs DCTCP: Network Throughput (Gbps)\nExperiment: {experiment_name}")
    plt.legend()
    plt.grid(True)

    filename = f"THRPT_{experiment_name}_ssird_dctcp_qts_compare.png"
    parent_dir = f"{PATH_TO_QTS_COMPARE_PARENT_DIR}{title_addendum}/"
    Path(parent_dir).mkdir(parents=True, exist_ok=True)
    plt.savefig(f"{parent_dir}{filename}")
    plt.close()

def plot_thrpt_graph_trimmed(thrpt_list, time_axis_s_list, experiment_name, title_addendum):
    plt.figure(figsize=(10,6))

    time_axis_ms_list = [s * 1000 for s in time_axis_s_list]
    plt.plot(time_axis_ms_list, thrpt_list, label=None, linestyle="-", marker=None, color=SSIRD_PLOT_COLOUR)
    plt.ylabel('Network Throughput (Gbps)')
    plt.xlabel('Time (ms)')
    plt.title(f"Network Throughput (Gbps)\nExperiment: {experiment_name}")
    plt.grid(True)

    filename = f"THRPT_{experiment_name}_qts.png"
    parent_dir = f"{PATH_TO_QTS_COMPARE_PARENT_DIR}{title_addendum}/"
    Path(parent_dir).mkdir(parents=True, exist_ok=True)
    plt.savefig(f"{parent_dir}{filename}")
    plt.close()

def plot_qing_comparison_graph_trimmed(ssird_qing_list, dctcp_qing_list, time_axis_s_list, experiment_name, nw_elem, src, dst, title_addendum):
    plt.figure(figsize=(10,6))

    time_axis_ms_list = [s * 1000 for s in time_axis_s_list]
    plt.plot(time_axis_ms_list, ssird_qing_list, label="SSIRD", linestyle="-", marker=None, color=SSIRD_PLOT_COLOUR)
    plt.plot(time_axis_ms_list, dctcp_qing_list, label="DCTCP", linestyle="-", marker=None, color=DCTCP_PLOT_COLOUR)
    plt.ylabel('Queuing (KB)')
    plt.xlabel('Time (ms)')
    plt.title(f"SSIRD vs DCTCP: Queuing (KB)\nnw_elem={nw_elem}, src={src}, dst={dst}\nExperiment: {experiment_name}")
    plt.legend()
    plt.grid(True)

    filename = f"QING_{experiment_name}_ssird_dctcp_qts_compare.png"
    parent_dir = f"{PATH_TO_QTS_COMPARE_PARENT_DIR}{title_addendum}/"
    Path(parent_dir).mkdir(parents=True, exist_ok=True)
    plt.savefig(f"{parent_dir}{filename}")
    plt.close()

def do_comparison_graph_trimmed_new(nw_elem, src, dst, num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum):
    # experiment_name = title_addendum + "_" + dale_experiment_rig.Experiment.get_experiment_name(num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date)
    experiment_info = f"{title_addendum}_{nw_elem}_{src}_{dst}"

    ssird_subpkt_result = get_qts_result_new(SSIRD_PROTO_NAME, nw_elem, src, dst, num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum)
    dctcp_subpkt_result = get_qts_result_new(DCTCP_PROTO_NAME, nw_elem, src, dst, num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum)
    overall_activity_end_time_s = max(ssird_subpkt_result.activity_end_time_s, dctcp_subpkt_result.activity_end_time_s) 
    
    # pad thrpt, q-ing & time to reach overall_activity_end_time_s
    end_time_padded_us = int((overall_activity_end_time_s * 1.1) * pow(10,6))
    time_axis_padded_us = range(0, end_time_padded_us, 1)
    time_axis_padded_s = [s * pow(10,-6) for s in time_axis_padded_us]
    num_datapoints = len(time_axis_padded_s)
    ssird_thrpt_padded = ssird_subpkt_result.throughput_gbps_list + [0]*(num_datapoints - len(ssird_subpkt_result.throughput_gbps_list))
    dctcp_thrpt_padded = dctcp_subpkt_result.throughput_gbps_list + [0]*(num_datapoints - len(dctcp_subpkt_result.throughput_gbps_list))
    plot_thrpt_comparison_graph_trimmed(ssird_thrpt_padded, dctcp_thrpt_padded, time_axis_padded_s, experiment_info, title_addendum)

    ssird_qing_padded = ssird_subpkt_result.queueing_KB_list +  [0]*(num_datapoints - len(ssird_subpkt_result.queueing_KB_list))
    dctcp_qing_padded = dctcp_subpkt_result.queueing_KB_list +  [0]*(num_datapoints - len(dctcp_subpkt_result.queueing_KB_list))
    plot_qing_comparison_graph_trimmed(ssird_qing_padded, dctcp_qing_padded, time_axis_padded_s, experiment_info, nw_elem, src, dst, title_addendum)

    
# def do_ssird_graph_trimmed(nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, experiment_family="", title_addendum = ""):
#     experiment_name = "SSIRD_" + title_addendum + dale_experiment_rig.Experiment.get_experiment_name(num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us)

#     ssird_subpkt_result = get_qts_result_new(SSIRD_PROTO_NAME, nw_elem, src, dst, num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum)
#     overall_activity_end_time_s = ssird_subpkt_result.activity_end_time_s
    
#     # pad thrpt, q-ing & time to reach overall_activity_end_time_s
#     end_time_padded_us = int((overall_activity_end_time_s * 1.1) * pow(10,6))
#     time_axis_padded_us = range(0, end_time_padded_us, 1)
#     time_axis_padded_s = [s * pow(10,-6) for s in time_axis_padded_us]
#     num_datapoints = len(time_axis_padded_s)
#     ssird_thrpt_padded = ssird_subpkt_result.throughput_gbps_list + [0]*(num_datapoints - len(ssird_subpkt_result.throughput_gbps_list))
#     plot_thrpt_graph_trimmed(ssird_thrpt_padded, time_axis_padded_s, experiment_name, title_addendum)

#     ssird_qing_padded = ssird_subpkt_result.queueing_KB_list +  [0]*(num_datapoints - len(ssird_subpkt_result.queueing_KB_list))

# def do_dctcp_graph_trimmed(nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, experiment_family="", title_addendum = ""):
#     experiment_name = "DCTCP_" + title_addendum + dale_experiment_rig.Experiment.get_experiment_name(num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us)

#     dctcp_subpkt_result = get_qts_result_new(DCTCP_PROTO_NAME, nw_elem, src, dst, num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum)
#     overall_activity_end_time_s = ssird_subpkt_result.activity_end_time_s
    
#     # pad thrpt, q-ing & time to reach overall_activity_end_time_s
#     end_time_padded_us = int((overall_activity_end_time_s * 1.1) * pow(10,6))
#     time_axis_padded_us = range(0, end_time_padded_us, 1)
#     time_axis_padded_s = [s * pow(10,-6) for s in time_axis_padded_us]
#     num_datapoints = len(time_axis_padded_s)
#     ssird_thrpt_padded = ssird_subpkt_result.throughput_gbps_list + [0]*(num_datapoints - len(ssird_subpkt_result.throughput_gbps_list))
#     plot_thrpt_graph_trimmed(ssird_thrpt_padded, time_axis_padded_s, experiment_name, title_addendum)

#     ssird_qing_padded = ssird_subpkt_result.queueing_KB_list +  [0]*(num_datapoints - len(ssird_subpkt_result.queueing_KB_list))


if __name__ == "__main__":
    ''' --- incast 10to1 40flo 1458B 0.1us fabHvyMid loadtest --- '''
    do_comparison_graph_trimmed_new(
        nw_elem=TOR,
        src="tor_12",
        dst="host_0",
        num_flows=40,
        target_per_host_perflo_gdpt_gbps=117,
        byteload_size_B=1458,
        inter_byteload_period_nanosec=100,
        experiment_date="nodate",
        experiment_family="FE_incast_",
        title_addendum="_12host_topo_fabHvyMid_loadtest"
    )    

    ''' --- incast 10to1 10flo 1458B 1us DctcpMsgSizeDist loadtest --- '''
    do_comparison_graph_trimmed_new(
        nw_elem=TOR,
        src="tor_12",
        dst="host_0",
        num_flows=10,
        target_per_host_perflo_gdpt_gbps=12,
        byteload_size_B=1458,
        inter_byteload_period_nanosec=1000,
        experiment_date="2025-08-18T_11-12-46Z",
        experiment_family="FE_incast_",
        title_addendum="_10host_DctcpMsgSizeDist_loadtest"
    )

    ''' --- incast 10to1 10flo 1458B 1us fbHadoopDist loadtest --- '''
    do_comparison_graph_trimmed_new(
        nw_elem=TOR,
        src="tor_12",
        dst="host_0",
        num_flows=10,
        target_per_host_perflo_gdpt_gbps=12,
        byteload_size_B=1458,
        inter_byteload_period_nanosec=1000,
        experiment_date="2025-08-18T_11-09-28Z",
        experiment_family="FE_incast_",
        title_addendum="_10host_fbHadoopDist_loadtest"
    )