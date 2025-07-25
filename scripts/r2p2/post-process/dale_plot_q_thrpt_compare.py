import sys
import subprocess
from pathlib import Path
import shutil
import numpy as np
import matplotlib.pyplot as plt

import dale_fct_experiment
import dale_multiflow_serialiser
import dale_experiment_rig
import dale_compare_thrpt_vs_gdpt

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

SSIRD_PLOT_COLOUR = 'tab:orange'
DCTCP_PLOT_COLOUR = 'tab:blue'

def plot_comparison_graph(y_col, title, experiment_name, ssird_csv_rel_path, dctcp_csv_rel_path):
    try:
        result = subprocess.run(
            ["python3", "plot_xy.py", "0", f"{y_col}", title, experiment_name, f"SSIRD,{ssird_csv_rel_path}", f"DCTCP-50,{dctcp_csv_rel_path}"],
            cwd=PATH_TO_POSTPROC,
            check=True,
            text=True,
            stdout=sys.stdout.buffer
        )
    except subprocess.CalledProcessError as e:
        print(f"Script failed with exit code {e.returncode}")
        print("Error output:", e.stderr)
        sys.exit(1)

def do_throughput_plotting_for_experiment(num_byteloads, byteload_size_B, inter_byteload_period_us, nw_elem, src, dst, title_addendum=""):
    experiment_name = dale_fct_experiment.FctExperiment.get_experiment_name(num_byteloads, byteload_size_B, inter_byteload_period_us) + title_addendum
    print(f"Plotting for experiment: {experiment_name}")

    ssird_results_dir = f"SSIRD-{experiment_name}/"
    shutil.copytree(f"{PATH_TO_SIM_RESULTS}{ssird_results_dir}data/", f"{PATH_TO_SIM_RESULTS}{experiment_name}/data/", dirs_exist_ok=True)

    dctcp_results_dir = f"DCTCP-{DCTCP_ECN_THRESH}-{experiment_name}/"
    shutil.copytree(f"{PATH_TO_SIM_RESULTS}{dctcp_results_dir}data/", f"{PATH_TO_SIM_RESULTS}{experiment_name}/data/", dirs_exist_ok=True)

    ssird_csv_rel_path = f"SSIRD/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"
    dctcp_csv_rel_path = f"DCTCP-{DCTCP_ECN_THRESH}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

    plot_comparison_graph(THROUGHPUT_COL, f"Throughput: SSIRD vs DCTCP ({experiment_name})", experiment_name, ssird_csv_rel_path, dctcp_csv_rel_path)

def do_queuing_plotting_for_experiment(num_byteloads, byteload_size_B, inter_byteload_period_us, nw_elem, src, dst, title_addendum=""):
    experiment_name = dale_fct_experiment.FctExperiment.get_experiment_name(num_byteloads, byteload_size_B, inter_byteload_period_us) + title_addendum
    print(f"Plotting for experiment: {experiment_name}")

    ssird_results_dir = f"SSIRD-{experiment_name}/"
    shutil.copytree(f"{PATH_TO_SIM_RESULTS}{ssird_results_dir}data/", f"{PATH_TO_SIM_RESULTS}{experiment_name}/data/", dirs_exist_ok=True)

    dctcp_results_dir = f"DCTCP-{DCTCP_ECN_THRESH}-{experiment_name}/"
    shutil.copytree(f"{PATH_TO_SIM_RESULTS}{dctcp_results_dir}data/", f"{PATH_TO_SIM_RESULTS}{experiment_name}/data/", dirs_exist_ok=True)

    ssird_csv_rel_path = f"SSIRD/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"
    dctcp_csv_rel_path = f"DCTCP-{DCTCP_ECN_THRESH}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

    plot_comparison_graph(QUEUEING_COL, f"Queueing: SSIRD vs DCTCP ({experiment_name})", experiment_name, ssird_csv_rel_path, dctcp_csv_rel_path)

def do_thrpt_plot_multiflow_exp(num_flows, num_byteloads, byteload_size_B, inter_byteload_period_us, nw_elem, src, dst, title_addendum=""):
    # experiment name with interval in us:
    # experiment_name = dale_multiflow_serialiser.MultiFlowExperiment.get_experiment_name(num_flows, num_byteloads, byteload_size_B, inter_byteload_period_us) + title_addendum
    # experiment name with interval in ns:
    experiment_name = dale_experiment_rig.Experiment.get_experiment_name(num_flows, num_byteloads, byteload_size_B, inter_byteload_period_us) + title_addendum
    print(f"Plotting for experiment: {experiment_name}")

    ssird_results_dir = f"SSIRD-{experiment_name}/"
    shutil.copytree(f"{PATH_TO_SIM_RESULTS}{ssird_results_dir}data/", f"{PATH_TO_SIM_RESULTS}{experiment_name}/data/", dirs_exist_ok=True)

    dctcp_results_dir = f"DCTCP-{DCTCP_ECN_THRESH}-{experiment_name}/"
    shutil.copytree(f"{PATH_TO_SIM_RESULTS}{dctcp_results_dir}data/", f"{PATH_TO_SIM_RESULTS}{experiment_name}/data/", dirs_exist_ok=True)

    ssird_csv_rel_path = f"SSIRD/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"
    dctcp_csv_rel_path = f"DCTCP-{DCTCP_ECN_THRESH}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

    plot_comparison_graph(THROUGHPUT_COL, f"Throughput: SSIRD vs DCTCP ({experiment_name})", experiment_name, ssird_csv_rel_path, dctcp_csv_rel_path)

def do_q_plot_multiflow_exp(num_flows, num_byteloads, byteload_size_B, inter_byteload_period_us, nw_elem, src, dst, title_addendum=""):
    experiment_name = dale_multiflow_serialiser.MultiFlowExperiment.get_experiment_name(num_flows, num_byteloads, byteload_size_B, inter_byteload_period_us) + title_addendum
    print(f"Plotting for experiment: {experiment_name}")

    ssird_results_dir = f"SSIRD-{experiment_name}/"
    shutil.copytree(f"{PATH_TO_SIM_RESULTS}{ssird_results_dir}data/", f"{PATH_TO_SIM_RESULTS}{experiment_name}/data/", dirs_exist_ok=True)

    dctcp_results_dir = f"DCTCP-{DCTCP_ECN_THRESH}-{experiment_name}/"
    shutil.copytree(f"{PATH_TO_SIM_RESULTS}{dctcp_results_dir}data/", f"{PATH_TO_SIM_RESULTS}{experiment_name}/data/", dirs_exist_ok=True)

    ssird_csv_rel_path = f"SSIRD/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"
    dctcp_csv_rel_path = f"DCTCP-{DCTCP_ECN_THRESH}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

    plot_comparison_graph(QUEUEING_COL, f"Queueing: SSIRD vs DCTCP ({experiment_name})", experiment_name, ssird_csv_rel_path, dctcp_csv_rel_path)

def plot_thrpt_comparison_graph_trimmed(ssird_thrpt_list, dctcp_thrpt_list, time_axis_s_list, experiment_name):
    plt.figure(figsize=(10,6))

    time_axis_ms_list = [s * 1000 for s in time_axis_s_list]
    plt.plot(time_axis_ms_list, ssird_thrpt_list, label="SSIRD", linestyle="-", marker=None, color=SSIRD_PLOT_COLOUR)
    plt.plot(time_axis_ms_list, dctcp_thrpt_list, label="DCTCP", linestyle="-", marker=None, color=DCTCP_PLOT_COLOUR)
    plt.ylabel('Network Throughput (Gbps)')
    plt.xlabel('Time (ms)')
    plt.title(f"SSIRD vs DCTCP: Network Throughput (Gbps)\nExperiment: {experiment_name}")
    plt.legend()
    plt.grid(True)

    filename = f"THRPT_{experiment_name}_ssird_dctcp_qts_direct_compare.png"
    plt.savefig(f"{PATH_TO_QTS_COMPARE_PARENT_DIR}{filename}")
    plt.close()

def plot_thrpt_graph_trimmed(thrpt_list, time_axis_s_list, experiment_name):
    plt.figure(figsize=(10,6))

    time_axis_ms_list = [s * 1000 for s in time_axis_s_list]
    plt.plot(time_axis_ms_list, thrpt_list, label=None, linestyle="-", marker=None, color=SSIRD_PLOT_COLOUR)
    plt.ylabel('Network Throughput (Gbps)')
    plt.xlabel('Time (ms)')
    plt.title(f"Network Throughput (Gbps)\nExperiment: {experiment_name}")
    plt.grid(True)

    filename = f"THRPT_{experiment_name}_qts.png"
    plt.savefig(f"{PATH_TO_QTS_COMPARE_PARENT_DIR}{filename}")
    plt.close()

def do_comparison_graph_trimmed(nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum = ""):
    Path(PATH_TO_QTS_COMPARE_PARENT_DIR).mkdir(parents=True, exist_ok=True)
    experiment_name = dale_experiment_rig.Experiment.get_experiment_name(num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us)

    ssird_subpkt_result = dale_compare_thrpt_vs_gdpt.get_qts_result(dale_compare_thrpt_vs_gdpt.SSIRD_PROTO_NAME, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum)
    dctcp_subpkt_result = dale_compare_thrpt_vs_gdpt.get_qts_result(dale_compare_thrpt_vs_gdpt.DCTCP_PROTO_NAME, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum)
    overall_activity_end_time_s = max(ssird_subpkt_result.activity_end_time_s, dctcp_subpkt_result.activity_end_time_s) 
    
    # pad thrpt, q-ing & time to reach overall_activity_end_time_s
    end_time_padded_us = int((overall_activity_end_time_s * 1.1) * pow(10,6))
    time_axis_padded_us = range(0, end_time_padded_us, 1)
    time_axis_padded_s = [s * pow(10,-6) for s in time_axis_padded_us]
    num_datapoints = len(time_axis_padded_s)
    ssird_thrpt_padded = ssird_subpkt_result.throughput_gbps_list + [0]*(num_datapoints - len(ssird_subpkt_result.throughput_gbps_list))
    dctcp_thrpt_padded = dctcp_subpkt_result.throughput_gbps_list + [0]*(num_datapoints - len(dctcp_subpkt_result.throughput_gbps_list))
    plot_thrpt_comparison_graph_trimmed(ssird_thrpt_padded, dctcp_thrpt_padded, time_axis_padded_s, experiment_name)

    ssird_qing_padded = ssird_subpkt_result.queueing_KB_list +  [0]*(num_datapoints - len(ssird_subpkt_result.queueing_KB_list))
    dctcp_qing_padded = dctcp_subpkt_result.queueing_KB_list +  [0]*(num_datapoints - len(dctcp_subpkt_result.queueing_KB_list))
    
def do_ssird_graph_trimmed(nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum = ""):
    Path(PATH_TO_QTS_COMPARE_PARENT_DIR).mkdir(parents=True, exist_ok=True)
    experiment_name = "SSIRD_" + title_addendum + dale_experiment_rig.Experiment.get_experiment_name(num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us)

    ssird_subpkt_result = dale_compare_thrpt_vs_gdpt.get_qts_result(dale_compare_thrpt_vs_gdpt.SSIRD_PROTO_NAME, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum)
    overall_activity_end_time_s = ssird_subpkt_result.activity_end_time_s
    
    # pad thrpt, q-ing & time to reach overall_activity_end_time_s
    end_time_padded_us = int((overall_activity_end_time_s * 1.1) * pow(10,6))
    time_axis_padded_us = range(0, end_time_padded_us, 1)
    time_axis_padded_s = [s * pow(10,-6) for s in time_axis_padded_us]
    num_datapoints = len(time_axis_padded_s)
    ssird_thrpt_padded = ssird_subpkt_result.throughput_gbps_list + [0]*(num_datapoints - len(ssird_subpkt_result.throughput_gbps_list))
    plot_thrpt_graph_trimmed(ssird_thrpt_padded, time_axis_padded_s, experiment_name)

    ssird_qing_padded = ssird_subpkt_result.queueing_KB_list +  [0]*(num_datapoints - len(ssird_subpkt_result.queueing_KB_list))

def do_dctcp_graph_trimmed(nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum = ""):
    Path(PATH_TO_QTS_COMPARE_PARENT_DIR).mkdir(parents=True, exist_ok=True)
    experiment_name = "DCTCP_" + dale_experiment_rig.Experiment.get_experiment_name(num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us)

    ssird_subpkt_result = dale_compare_thrpt_vs_gdpt.get_qts_result(dale_compare_thrpt_vs_gdpt.DCTCP_PROTO_NAME, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum)
    overall_activity_end_time_s = ssird_subpkt_result.activity_end_time_s
    
    # pad thrpt, q-ing & time to reach overall_activity_end_time_s
    end_time_padded_us = int((overall_activity_end_time_s * 1.1) * pow(10,6))
    time_axis_padded_us = range(0, end_time_padded_us, 1)
    time_axis_padded_s = [s * pow(10,-6) for s in time_axis_padded_us]
    num_datapoints = len(time_axis_padded_s)
    ssird_thrpt_padded = ssird_subpkt_result.throughput_gbps_list + [0]*(num_datapoints - len(ssird_subpkt_result.throughput_gbps_list))
    plot_thrpt_graph_trimmed(ssird_thrpt_padded, time_axis_padded_s, experiment_name)

    ssird_qing_padded = ssird_subpkt_result.queueing_KB_list +  [0]*(num_datapoints - len(ssird_subpkt_result.queueing_KB_list))


if __name__ == "__main__":

    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10000, 20, 0.1, title_addendum="_fullrange_5flo_8gbps_total_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 1000, 200, 1.0, title_addendum="_fullrange_5flo_8gbps_total_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 100, 2000, 10, title_addendum="_fullrange_5flo_8gbps_total_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10, 20000, 100, title_addendum="_fullrange_5flo_8gbps_total_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 1, 200000, 1000, title_addendum="_fullrange_5flo_8gbps_total_1msRTT")

    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 31, 10000, 20, 0.1, title_addendum="_fullrange_31flo_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 31, 1000, 200, 1.0, title_addendum="_fullrange_31flo_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 31, 100, 2000, 10, title_addendum="_fullrange_31flo_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 31, 10, 20000, 100, title_addendum="_fullrange_31flo_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 31, 1, 200000, 1000, title_addendum="_fullrange_31flo_1msRTT")

    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10000, 20, 10, title_addendum="_vary_num_bload_5flo_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 1000, 200, 10, title_addendum="_vary_num_bload_5flo_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 100, 2000, 10, title_addendum="_vary_num_bload_5flo_1msRTT")

    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 100, 20, 10, title_addendum="_vary_bload_size_5flo_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 100, 200, 10, title_addendum="_vary_bload_size_5flo_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 100, 2000, 10, title_addendum="_vary_bload_size_5flo_1msRTT")

    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10000, 20, 0.01, title_addendum="_vary_interval_5flo_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10000, 20, 0.1, title_addendum="_vary_interval_5flo_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10000, 20, 1, title_addendum="_vary_interval_5flo_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10000, 20, 10, title_addendum="_vary_interval_5flo_1msRTT")

    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10000, 2000, 10, title_addendum="_large_bload_20MBflo_5flo_8gbps_total_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 1000, 20000, 100, title_addendum="_large_bload_20MBflo_5flo_8gbps_total_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 100, 200000, 1000, title_addendum="_large_bload_20MBflo_5flo_8gbps_total_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10, 2000000, 10000, title_addendum="_large_bload_20MBflo_5flo_8gbps_total_1msRTT")
    do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 1, 20000000, 100000, title_addendum="_large_bload_20MBflo_5flo_8gbps_total_1msRTT")
