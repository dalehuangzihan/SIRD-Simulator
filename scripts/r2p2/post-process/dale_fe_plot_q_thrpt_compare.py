import sys
import subprocess
from pathlib import Path
import shutil
import numpy as np
import statistics
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import csv

import dale_experiment_rig

PATH_TO_SCRIPTS_R2P2 = "/home/dh1723/SIRD-Simulator/scripts/r2p2/"
# PATH_TO_SCRIPTS_R2P2 = "/data/dh1723/SIRD-Simulator/scripts/r2p2/"
# PATH_TO_SCRIPTS_R2P2 = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/scripts/r2p2/"
PATH_TO_POSTPROC = f"{PATH_TO_SCRIPTS_R2P2}post-process/"
PATH_TO_SIM_RESULTS = f"{PATH_TO_SCRIPTS_R2P2}coord/results/"
PATH_TO_TMP_PLOT = PATH_TO_POSTPROC + "tmp_plot/"
PATH_TO_QTS_COMPARE_PARENT_DIR = PATH_TO_TMP_PLOT + "qts_direct_comparison_graphs/"
PATH_TO_LOAD_VS_QING_DIR = PATH_TO_TMP_PLOT + "load_vs_qing_graphs/"

# Common experiment param; value is meaningful only when req_interval_distr is not 'manual'
CLIENT_INJECTION_RATE_GBPS = "60"
DCTCP_ECN_THRESH = 50
LINK_SPEED_GBPS = 100

AGGR = "aggr"
HOST = "host"
TOR = "tor"

THROUGHPUT_COL = 1
QUEUEING_COL = 2

QTS_CSV_TIMESTEP_S = 0.000001 # 1us

SSIRD_PROTO_NAME = 'SSIRD'
DCTCP_PROTO_NAME = 'DCTCP'
XPASS_PROTO_NAME = 'ExpressPass'

SSIRD_PLOT_COLOUR = 'tab:orange'
XPASS_PLOT_COLOUR = 'tab:green'
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
        return statistics.mean(self.queueing_KB_list)         
    
    def get_max_qing_KB(self):
        return max(self.queueing_KB_list)

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

    elif proto.upper() == XPASS_PROTO_NAME.upper(): 
        return f"{PATH_TO_SIM_RESULTS}{XPASS_PROTO_NAME}-{experiment_family}{title_addendum}__{num_flows}flo-{round(target_per_flow_gdpt_gbps)}Gbps-{byteload_size_B}B-{inter_byteload_period_nanosec}ns-{experiment_date}/data/{XPASS_PROTO_NAME}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

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

def plot_thrpt_comparison_graph_trimmed(ssird_thrpt_list, dctcp_thrpt_list, xpass_thrpt_list, time_axis_s_list, experiment_name, title_addendum):
    plt.figure(figsize=(10,6))

    time_axis_ms_list = [s * 1000 for s in time_axis_s_list]
    plt.plot(time_axis_ms_list, ssird_thrpt_list, label="SSIRD", linestyle="-", marker=None, color=SSIRD_PLOT_COLOUR)
    plt.plot(time_axis_ms_list, dctcp_thrpt_list, label="DCTCP", linestyle="-", marker=None, color=DCTCP_PLOT_COLOUR)
    plt.plot(time_axis_ms_list, xpass_thrpt_list, label="ExpressPass", linestyle="-", marker=None, color=XPASS_PLOT_COLOUR)
    plt.ylabel('Network Throughput (Gbps)')
    plt.xlabel('Time (ms)')
    plt.title(f"SSIRD vs ExpressPass vs DCTCP: Network Throughput (Gbps)\nExperiment: {experiment_name}")
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

def plot_qing_comparison_graph_trimmed(ssird_qing_list, dctcp_qing_list, xpass_qing_list, time_axis_s_list, experiment_name, nw_elem, src, dst, title_addendum):
    plt.figure(figsize=(10,6))

    time_axis_ms_list = [s * 1000 for s in time_axis_s_list]
    plt.plot(time_axis_ms_list, ssird_qing_list, label="SSIRD", linestyle="-", marker=None, color=SSIRD_PLOT_COLOUR)
    plt.plot(time_axis_ms_list, dctcp_qing_list, label="DCTCP", linestyle="-", marker=None, color=DCTCP_PLOT_COLOUR)
    plt.plot(time_axis_ms_list, xpass_qing_list, label="ExpressPass", linestyle="-", marker=None, color=XPASS_PLOT_COLOUR)
    plt.ylabel('Queuing (KB)')
    plt.xlabel('Time (ms)')
    plt.title(f"SSIRD vs ExpressPass vs DCTCP: Queuing (KB)\nnw_elem={nw_elem}, src={src}, dst={dst}\nExperiment: {experiment_name}")
    plt.legend()
    plt.grid(True)

    filename = f"QING_{experiment_name}_ssird_dctcp_qts_compare.png"
    parent_dir = f"{PATH_TO_QTS_COMPARE_PARENT_DIR}{title_addendum}/"
    Path(parent_dir).mkdir(parents=True, exist_ok=True)
    plt.savefig(f"{parent_dir}{filename}")
    plt.close()

def do_thrpt_qing_comparison_graphs_trimmed_new(nw_elem, src, dst, num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum):
    # experiment_name = title_addendum + "_" + dale_experiment_rig.Experiment.get_experiment_name(num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date)
    experiment_info = f"{title_addendum}_{num_flows}flo_{nw_elem}_{src}_{dst}"

    ssird_qts_result = get_qts_result_new(SSIRD_PROTO_NAME, nw_elem, src, dst, num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum)
    dctcp_qts_result = get_qts_result_new(DCTCP_PROTO_NAME, nw_elem, src, dst, num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum)
    xpass_qts_result = get_qts_result_new(XPASS_PROTO_NAME, nw_elem, src, dst, num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum)
    overall_activity_end_time_s = max(ssird_qts_result.activity_end_time_s, dctcp_qts_result.activity_end_time_s, xpass_qts_result.activity_end_time_s) 
    
    # pad thrpt, q-ing & time to reach overall_activity_end_time_s
    end_time_padded_us = int((overall_activity_end_time_s * 1.1) * pow(10,6))
    time_axis_padded_us = range(0, end_time_padded_us, 1)
    time_axis_padded_s = [s * pow(10,-6) for s in time_axis_padded_us]
    num_datapoints = len(time_axis_padded_s)
    ssird_thrpt_padded = ssird_qts_result.throughput_gbps_list + [0]*(num_datapoints - len(ssird_qts_result.throughput_gbps_list))
    dctcp_thrpt_padded = dctcp_qts_result.throughput_gbps_list + [0]*(num_datapoints - len(dctcp_qts_result.throughput_gbps_list))
    xpass_thrpt_padded = xpass_qts_result.throughput_gbps_list + [0]*(num_datapoints - len(xpass_qts_result.throughput_gbps_list))
    plot_thrpt_comparison_graph_trimmed(ssird_thrpt_padded, dctcp_thrpt_padded, xpass_thrpt_padded, time_axis_padded_s, experiment_info, title_addendum)

    ssird_qing_padded = ssird_qts_result.queueing_KB_list +  [0]*(num_datapoints - len(ssird_qts_result.queueing_KB_list))
    dctcp_qing_padded = dctcp_qts_result.queueing_KB_list +  [0]*(num_datapoints - len(dctcp_qts_result.queueing_KB_list))
    xpass_qing_padded = xpass_qts_result.queueing_KB_list +  [0]*(num_datapoints - len(xpass_qts_result.queueing_KB_list))
    plot_qing_comparison_graph_trimmed(ssird_qing_padded, dctcp_qing_padded, xpass_qing_padded, time_axis_padded_s, experiment_info, nw_elem, src, dst, title_addendum)

def get_max_qing_lists_for_experiments(nw_elem, src, dst, num_flows_list, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum):

    ssird_max_qing_KB_list = []
    xpass_max_qing_KB_list = []
    dctcp_max_qing_KB_list = []

    for num_flows in num_flows_list:
        ssird_qts_result = get_qts_result_new(SSIRD_PROTO_NAME, nw_elem, src, dst, num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum)
        dctcp_qts_result = get_qts_result_new(DCTCP_PROTO_NAME, nw_elem, src, dst, num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum)
        xpass_qts_result = get_qts_result_new(XPASS_PROTO_NAME, nw_elem, src, dst, num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum)
    
        ssird_max_qing_KB_list.append(ssird_qts_result.get_max_qing_KB())
        xpass_max_qing_KB_list.append(xpass_qts_result.get_max_qing_KB())
        dctcp_max_qing_KB_list.append(dctcp_qts_result.get_max_qing_KB())
    
    return ssird_max_qing_KB_list, xpass_max_qing_KB_list, dctcp_max_qing_KB_list


''' --- Plot graphs for specific experiments --- '''

def do_thrpt_qing_comparison_10to1_800ns_DctcpMsgSizeDist_load_fullsweep_experiment(): 
    ''' --- incast 10to1 40flo 1458B 0.8us DctcpMsgSizeDist load fullsweep --- '''
    do_thrpt_qing_comparison_graphs_trimmed_new(
        nw_elem=TOR,
        src="tor_12",
        dst="host_0",
        num_flows=40,
        target_per_host_perflo_gdpt_gbps=15,
        byteload_size_B=1458,
        inter_byteload_period_nanosec=800,
        experiment_date="2025-08-20T_22-41-38Z",
        experiment_family="FE_incast_12host_fullsweep_",
        title_addendum="_12host_DctcpMsgSizeDist_load_fullsweep_800ns_fromjson"
    )    
    do_thrpt_qing_comparison_graphs_trimmed_new(
        nw_elem=TOR,
        src="tor_12",
        dst="host_0",
        num_flows=30,
        target_per_host_perflo_gdpt_gbps=15,
        byteload_size_B=1458,
        inter_byteload_period_nanosec=800,
        experiment_date="2025-08-20T_22-41-38Z",
        experiment_family="FE_incast_12host_fullsweep_",
        title_addendum="_12host_DctcpMsgSizeDist_load_fullsweep_800ns_fromjson"
    )    
    do_thrpt_qing_comparison_graphs_trimmed_new(
        nw_elem=TOR,
        src="tor_12",
        dst="host_0",
        num_flows=20,
        target_per_host_perflo_gdpt_gbps=15,
        byteload_size_B=1458,
        inter_byteload_period_nanosec=800,
        experiment_date="2025-08-20T_22-41-38Z",
        experiment_family="FE_incast_12host_fullsweep_",
        title_addendum="_12host_DctcpMsgSizeDist_load_fullsweep_800ns_fromjson"
    )    
    do_thrpt_qing_comparison_graphs_trimmed_new(
        nw_elem=TOR,
        src="tor_12",
        dst="host_0",
        num_flows=10,
        target_per_host_perflo_gdpt_gbps=15,
        byteload_size_B=1458,
        inter_byteload_period_nanosec=800,
        experiment_date="2025-08-20T_22-41-38Z",
        experiment_family="FE_incast_12host_fullsweep_",
        title_addendum="_12host_DctcpMsgSizeDist_load_fullsweep_800ns_fromjson"
    )    
    do_thrpt_qing_comparison_graphs_trimmed_new(
        nw_elem=TOR,
        src="tor_12",
        dst="host_0",
        num_flows=5,
        target_per_host_perflo_gdpt_gbps=15,
        byteload_size_B=1458,
        inter_byteload_period_nanosec=800,
        experiment_date="2025-08-20T_22-41-38Z",
        experiment_family="FE_incast_12host_fullsweep_",
        title_addendum="_12host_DctcpMsgSizeDist_load_fullsweep_800ns_fromjson"
    )    

def get_max_qing_for_10to1_800ns_DctcpMsgSizeDist_load_fullsweep_experiment():
    ssird_max_qing_KB_list, xpass_max_qing_KB_list, dctcp_max_qing_KB_list = get_max_qing_lists_for_experiments(
        nw_elem=TOR,
        src="tor_12",
        dst="host_0",
        num_flows_list=[1, 5, 10, 20, 30, 40],
        target_per_host_perflo_gdpt_gbps=15,
        byteload_size_B=1458,
        inter_byteload_period_nanosec=800,
        experiment_date="2025-08-20T_22-41-38Z",
        experiment_family="FE_incast_12host_fullsweep_",
        title_addendum="_12host_DctcpMsgSizeDist_load_fullsweep_800ns_fromjson"
    )    
    print(f"ssird_max_qing_KB_list={ssird_max_qing_KB_list}")
    print(f"xpass_max_qing_KB_list={xpass_max_qing_KB_list}")
    print(f"dctcp_max_qing_KB_list={dctcp_max_qing_KB_list}")

def plot_applied_downlink_load_vs_max_qing_KB(applied_downlink_gdpt_list_gbps, nw_elem, src, dst, num_flows_list, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum):

    ssird_max_qing_KB_list, xpass_max_qing_KB_list, dctcp_max_qing_KB_list = get_max_qing_lists_for_experiments(
        nw_elem=nw_elem,
        src=src,
        dst=dst,
        num_flows_list=num_flows_list,
        target_per_host_perflo_gdpt_gbps=target_per_host_perflo_gdpt_gbps,
        byteload_size_B=byteload_size_B,
        inter_byteload_period_nanosec=inter_byteload_period_nanosec,
        experiment_date=experiment_date,
        experiment_family=experiment_family,
        title_addendum=title_addendum
    )    
    print(f"ssird_max_qing_KB_list={ssird_max_qing_KB_list}")
    print(f"xpass_max_qing_KB_list={xpass_max_qing_KB_list}")
    print(f"dctcp_max_qing_KB_list={dctcp_max_qing_KB_list}")

    load_percent_list = [round(thrpt_gbps/LINK_SPEED_GBPS * 100, 1) for thrpt_gbps in applied_downlink_gdpt_list_gbps]

    plt.figure(figsize=(10, 6))
    plt.xlabel(f'Total Applied App Load at Receiver Downlink (percent)')

    plt.plot(load_percent_list, ssird_max_qing_KB_list, label="SSIRD", linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.plot(load_percent_list, xpass_max_qing_KB_list, label="ExpressPass", linestyle='-', marker='o', color=XPASS_PLOT_COLOUR)
    plt.plot(load_percent_list, dctcp_max_qing_KB_list, label="DCTCP", linestyle='-', marker='o', color=DCTCP_PLOT_COLOUR)

    plt.ylabel('Peak Queuing (KB)')
    plt.title(f"Peak Queuing vs Total Applied App Load at Downlink\n{experiment_family}{title_addendum}")
    plt.legend()

    ax = plt.gca()

    ax.grid(True, which='both')

    Path(PATH_TO_LOAD_VS_QING_DIR).mkdir(parents=True, exist_ok=True)
    filename = f"allproto_applied_downlink_load_vs_qing_{experiment_family}{title_addendum}.png"
    plt.savefig(f"{PATH_TO_LOAD_VS_QING_DIR}{filename}")
    plt.close()

def plot_achieved_gdpt_vs_max_qing_KB(
        ssird_downlink_gdpt_list, xpass_downlink_gdpt_list, dctcp_downlink_gdpt_list, 
        nw_elem, src, dst, num_flows_list, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, experiment_family, title_addendum,
        x_lim=None, y_lim=None
    ):

    ssird_max_qing_KB_list, xpass_max_qing_KB_list, dctcp_max_qing_KB_list = get_max_qing_lists_for_experiments(
        nw_elem=nw_elem,
        src=src,
        dst=dst,
        num_flows_list=num_flows_list,
        target_per_host_perflo_gdpt_gbps=target_per_host_perflo_gdpt_gbps,
        byteload_size_B=byteload_size_B,
        inter_byteload_period_nanosec=inter_byteload_period_nanosec,
        experiment_date=experiment_date,
        experiment_family=experiment_family,
        title_addendum=title_addendum
    )    
    print(f"ssird_max_qing_KB_list={ssird_max_qing_KB_list}")
    print(f"xpass_max_qing_KB_list={xpass_max_qing_KB_list}")
    print(f"dctcp_max_qing_KB_list={dctcp_max_qing_KB_list}")

    ssird_downlink_gdpt_list_processed = [round(x, 1) for x in ssird_downlink_gdpt_list]
    xpass_downlink_gdpt_list_processed = [round(x, 1) for x in xpass_downlink_gdpt_list]
    dctcp_downlink_gdpt_list_processed = [round(x, 1) for x in dctcp_downlink_gdpt_list]

    plt.figure(figsize=(10, 6))
    plt.xlabel(f'Acheived Goodput (Gbps)')

    # ssird_max_qing_list = [x * 1000 for x in ssird_max_qing_KB_list]
    # xpass_max_qing_list = [x * 1000 for x in xpass_max_qing_KB_list]
    # dctcp_max_qing_list = [x * 1000 for x in dctcp_max_qing_KB_list]
    # plt.yscale('log')
    # plt.ylabel('Peak Queuing (Bytes) (Log Scale)')
    ssird_max_qing_list = ssird_max_qing_KB_list
    xpass_max_qing_list = xpass_max_qing_KB_list
    dctcp_max_qing_list = dctcp_max_qing_KB_list
    plt.ylabel('Peak Queuing (KB)')

    plt.plot(ssird_downlink_gdpt_list_processed, ssird_max_qing_list, label="SSIRD", linestyle='-', marker='^', color=SSIRD_PLOT_COLOUR, markersize=8)
    plt.plot(xpass_downlink_gdpt_list_processed, xpass_max_qing_list, label="ExpressPass", linestyle='-', marker='s', color=XPASS_PLOT_COLOUR, markersize=7)
    plt.plot(dctcp_downlink_gdpt_list_processed, dctcp_max_qing_list, label="DCTCP", linestyle='-', marker='o', color=DCTCP_PLOT_COLOUR, markersize=7)

    plt.title(f"Peak Queuing vs Achieved Goodput\n{experiment_family}{title_addendum}")
    plt.legend()

    ax = plt.gca()
    ax.grid(True, which='both')

    if (x_lim is not None):
        ax.set_xlim(x_lim)
    if (y_lim is not None):
        ax.set_ylim(y_lim)

    # # place ticks at the exact datapoints
    # all_y_vals_list = []
    # all_y_vals_list.extend(ssird_max_qing_B_list)
    # all_y_vals_list.extend(xpass_max_qing_B_list)
    # all_y_vals_list.extend(dctcp_max_qing_B_list)
    # yticks = sorted({float(y) for y in all_y_vals_list})
    # ax.yaxis.set_major_locator(mticker.FixedLocator(yticks))
    # # show their raw values as labels
    # labels = []
    # for y in yticks:
    #     labels.append(f"{int(y)}" if float(y).is_integer() else f"{y:g}")
    #     ax.yaxis.set_major_formatter(mticker.FixedFormatter(labels))
    #     # improve readability (optional)
    #     plt.setp(ax.get_yticklabels(), rotation=45, ha='right')
    #     # plt.setp(ax.get_yticklabels(), rotation=0, ha='center')
    #     ax.minorticks_off() # keep only your custom ticks

    Path(PATH_TO_LOAD_VS_QING_DIR).mkdir(parents=True, exist_ok=True)
    filename = f"allproto_achieved_gdpt_vs_qing_{experiment_family}{title_addendum}.png"
    plt.savefig(f"{PATH_TO_LOAD_VS_QING_DIR}{filename}")
    plt.close()

if __name__ == "__main__":

    # do_thrpt_qing_comparison_10to1_800ns_DctcpMsgSizeDist_load_fullsweep_experiment()
    # get_max_qing_for_10to1_800ns_DctcpMsgSizeDist_load_fullsweep_experiment()
    plot_applied_downlink_load_vs_max_qing_KB(
        applied_downlink_gdpt_list_gbps=[20.32142857245574, 53.50592678031138, 51.729513662789095, 146.79326701476757, 210.51215223019966, 217.243663555441],
        nw_elem=TOR,
        src="tor_12",
        dst="host_0",
        num_flows_list=[1, 5, 10, 20, 30, 40],
        target_per_host_perflo_gdpt_gbps=15,
        byteload_size_B=1458,
        inter_byteload_period_nanosec=800,
        experiment_date="2025-08-20T_22-41-38Z",
        experiment_family="FE_incast_12host_fullsweep_",
        title_addendum="_12host_DctcpMsgSizeDist_load_fullsweep_800ns_fromjson"
    )    

    plot_achieved_gdpt_vs_max_qing_KB(
        ssird_downlink_gdpt_list=[8.875727129025025, 26.916826646915467, 27.45587587126008, 71.10769543567022, 73.4341733177687, 78.76356439030432],
        xpass_downlink_gdpt_list=[1.1625338901008542, 4.599414841697087, 5.375402380257017, 11.501608118880105, 12.803975226054224, 16.591948045500907],
        dctcp_downlink_gdpt_list=[14.352308822137951, 42.455847449796664, 40.0246754922329, 83.60861562200749, 84.2705031805067, 88.31901189364444],
        nw_elem=TOR,
        src="tor_12",
        dst="host_0",
        num_flows_list=[1, 5, 10, 20, 30, 40],
        target_per_host_perflo_gdpt_gbps=15,
        byteload_size_B=1458,
        inter_byteload_period_nanosec=800,
        experiment_date="2025-08-20T_22-41-38Z",
        experiment_family="FE_incast_12host_fullsweep_",
        title_addendum="_12host_DctcpMsgSizeDist_load_fullsweep_800ns_fromjson",
        y_lim=(-10, 300)
    )    
