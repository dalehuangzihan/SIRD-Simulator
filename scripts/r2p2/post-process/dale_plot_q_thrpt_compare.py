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

def do_comparison_graph_trimmed(nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum = ""):
    experiment_name = title_addendum + "_" + dale_experiment_rig.Experiment.get_experiment_name(num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us)

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
    plot_thrpt_comparison_graph_trimmed(ssird_thrpt_padded, dctcp_thrpt_padded, time_axis_padded_s, experiment_name, title_addendum)

    ssird_qing_padded = ssird_subpkt_result.queueing_KB_list +  [0]*(num_datapoints - len(ssird_subpkt_result.queueing_KB_list))
    dctcp_qing_padded = dctcp_subpkt_result.queueing_KB_list +  [0]*(num_datapoints - len(dctcp_subpkt_result.queueing_KB_list))
    plot_qing_comparison_graph_trimmed(ssird_qing_padded, dctcp_qing_padded, time_axis_padded_s, experiment_name, nw_elem, src, dst, title_addendum)
    
def do_comparison_graph_trimmed_new(nw_elem, src, dst, num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, title_addendum = ""):
    # experiment_name = title_addendum + "_" + dale_experiment_rig.Experiment.get_experiment_name(num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date)
    experiment_info = f"{title_addendum}_{nw_elem}_{src}_{dst}"

    ssird_subpkt_result = dale_compare_thrpt_vs_gdpt.get_qts_result_new(dale_compare_thrpt_vs_gdpt.SSIRD_PROTO_NAME, nw_elem, src, dst, num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, title_addendum)
    dctcp_subpkt_result = dale_compare_thrpt_vs_gdpt.get_qts_result_new(dale_compare_thrpt_vs_gdpt.DCTCP_PROTO_NAME, nw_elem, src, dst, num_flows, target_per_host_perflo_gdpt_gbps, byteload_size_B, inter_byteload_period_nanosec, experiment_date, title_addendum)
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

    
def do_ssird_graph_trimmed(nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum = ""):
    experiment_name = "SSIRD_" + title_addendum + dale_experiment_rig.Experiment.get_experiment_name(num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us)

    ssird_subpkt_result = dale_compare_thrpt_vs_gdpt.get_qts_result(dale_compare_thrpt_vs_gdpt.SSIRD_PROTO_NAME, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum)
    overall_activity_end_time_s = ssird_subpkt_result.activity_end_time_s
    
    # pad thrpt, q-ing & time to reach overall_activity_end_time_s
    end_time_padded_us = int((overall_activity_end_time_s * 1.1) * pow(10,6))
    time_axis_padded_us = range(0, end_time_padded_us, 1)
    time_axis_padded_s = [s * pow(10,-6) for s in time_axis_padded_us]
    num_datapoints = len(time_axis_padded_s)
    ssird_thrpt_padded = ssird_subpkt_result.throughput_gbps_list + [0]*(num_datapoints - len(ssird_subpkt_result.throughput_gbps_list))
    plot_thrpt_graph_trimmed(ssird_thrpt_padded, time_axis_padded_s, experiment_name, title_addendum)

    ssird_qing_padded = ssird_subpkt_result.queueing_KB_list +  [0]*(num_datapoints - len(ssird_subpkt_result.queueing_KB_list))

def do_dctcp_graph_trimmed(nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum = ""):
    experiment_name = "DCTCP_" + title_addendum + dale_experiment_rig.Experiment.get_experiment_name(num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us)

    ssird_subpkt_result = dale_compare_thrpt_vs_gdpt.get_qts_result(dale_compare_thrpt_vs_gdpt.DCTCP_PROTO_NAME, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, title_addendum)
    overall_activity_end_time_s = ssird_subpkt_result.activity_end_time_s
    
    # pad thrpt, q-ing & time to reach overall_activity_end_time_s
    end_time_padded_us = int((overall_activity_end_time_s * 1.1) * pow(10,6))
    time_axis_padded_us = range(0, end_time_padded_us, 1)
    time_axis_padded_s = [s * pow(10,-6) for s in time_axis_padded_us]
    num_datapoints = len(time_axis_padded_s)
    ssird_thrpt_padded = ssird_subpkt_result.throughput_gbps_list + [0]*(num_datapoints - len(ssird_subpkt_result.throughput_gbps_list))
    plot_thrpt_graph_trimmed(ssird_thrpt_padded, time_axis_padded_s, experiment_name, title_addendum)

    ssird_qing_padded = ssird_subpkt_result.queueing_KB_list +  [0]*(num_datapoints - len(ssird_subpkt_result.queueing_KB_list))


if __name__ == "__main__":
    # do_comparison_graph_trimmed(HOST, "host_0", "tor_4", 15, 10000, 4, 0.01, "_subpkt_multiflow_fastpace_extended")
    # do_comparison_graph_trimmed(HOST, "host_0", "tor_4", 15, 1000, 40, 0.1, "_subpkt_multiflow_fastpace_extended")
    # do_comparison_graph_trimmed(HOST, "host_0", "tor_4", 15, 100, 400, 1, "_subpkt_multiflow_fastpace_extended")
    # do_comparison_graph_trimmed(HOST, "host_0", "tor_4", 15, 10, 4000, 10, "_subpkt_multiflow_fastpace_extended")

    # do_comparison_graph_trimmed(HOST, "host_0", "tor_4", 31, 10000, 20, 0.1, "_fullrange_31flo")
    # do_comparison_graph_trimmed(HOST, "host_0", "tor_4", 31, 1000, 200, 1, "_fullrange_31flo")
    # do_comparison_graph_trimmed(HOST, "host_0", "tor_4", 31, 100, 2000, 10, "_fullrange_31flo")
    # do_comparison_graph_trimmed(HOST, "host_0", "tor_4", 31, 10, 20000, 100, "_fullrange_31flo")

    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 1, 10000, 20, 0.1, title_addendum="_fullrange_1flo_1pt6gbps_total_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 1, 1000, 200, 1.0, title_addendum="_fullrange_1flo_1pt6gbps_total_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 1, 100, 2000, 10, title_addendum="_fullrange_1flo_1pt6gbps_total_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 1, 10, 20000, 100, title_addendum="_fullrange_1flo_1pt6gbps_total_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 1, 1, 200000, 1000, title_addendum="_fullrange_1flo_1pt6gbps_total_1msRTT")

    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10000, 20, 0.1, title_addendum="_fullrange_5flo_8gbps_total_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 1000, 200, 1.0, title_addendum="_fullrange_5flo_8gbps_total_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 100, 2000, 10, title_addendum="_fullrange_5flo_8gbps_total_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10, 20000, 100, title_addendum="_fullrange_5flo_8gbps_total_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 1, 200000, 1000, title_addendum="_fullrange_5flo_8gbps_total_1msRTT")

    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 31, 10000, 20, 0.1, title_addendum="_fullrange_31flo_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 31, 1000, 200, 1.0, title_addendum="_fullrange_31flo_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 31, 100, 2000, 10, title_addendum="_fullrange_31flo_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 31, 10, 20000, 100, title_addendum="_fullrange_31flo_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 31, 1, 200000, 1000, title_addendum="_fullrange_31flo_1msRTT")

    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10000, 20, 10, title_addendum="_vary_num_bload_5flo_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 1000, 200, 10, title_addendum="_vary_num_bload_5flo_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 100, 2000, 10, title_addendum="_vary_num_bload_5flo_1msRTT")

    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 100, 20, 10, title_addendum="_vary_bload_size_5flo_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 100, 200, 10, title_addendum="_vary_bload_size_5flo_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 100, 2000, 10, title_addendum="_vary_bload_size_5flo_1msRTT")

    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10000, 20, 0.01, title_addendum="_vary_interval_5flo_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10000, 20, 0.1, title_addendum="_vary_interval_5flo_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10000, 20, 1, title_addendum="_vary_interval_5flo_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10000, 20, 10, title_addendum="_vary_interval_5flo_1msRTT")

    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10000, 2000, 10, title_addendum="_large_bload_20MBflo_5flo_8gbps_total_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 1000, 20000, 100, title_addendum="_large_bload_20MBflo_5flo_8gbps_total_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 100, 200000, 1000, title_addendum="_large_bload_20MBflo_5flo_8gbps_total_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 10, 2000000, 10000, title_addendum="_large_bload_20MBflo_5flo_8gbps_total_1msRTT")
    # do_ssird_graph_trimmed(HOST, "host_0", "tor_4", 5, 1, 20000000, 100000, title_addendum="_large_bload_20MBflo_5flo_8gbps_total_1msRTT")

    # do_comparison_graph_trimmed(TOR, "tor_4", "host_0", 5, 100, 2000, 1, title_addendum="_incast_3to1_5flo_16GbpsFlo_200KBflo")
    # do_comparison_graph_trimmed(TOR, "tor_4", "host_0", 31, 10, 2000, 10, title_addendum="_3to1_incast_test_31flo")

    # do_comparison_graph_trimmed_new(
    #     nw_elem=TOR,
    #     src="tor_4",
    #     dst="host_0",
    #     num_flows=8,
    #     target_per_host_perflo_gdpt_gbps=12,
    #     byteload_size_B=1560,
    #     inter_byteload_period_nanosec=1000,
    #     experiment_date="2025-08-12T_10-09-35Z",
    #     title_addendum="_incast_poisson_3to1_8flo_1560B_1us_99pt84Gbps"
    # )

    # do_comparison_graph_trimmed_new(
    #     nw_elem=TOR,
    #     src="tor_4",
    #     dst="host_0",
    #     num_flows=8,
    #     target_per_host_perflo_gdpt_gbps=12,
    #     byteload_size_B=1560,
    #     inter_byteload_period_nanosec=1000,
    #     experiment_date="2025-08-12T_10-09-58Z",
    #     title_addendum="_incast_poisson_3to1_8flo_1560B_1us_99pt84Gbps_fixed_bload"
    # )

    # ''' --- incast 3to1 8flo 1458B 1us --- '''
    # do_comparison_graph_trimmed_new(
    #     nw_elem=TOR,
    #     src="tor_4",
    #     dst="host_0",
    #     num_flows=8,
    #     target_per_host_perflo_gdpt_gbps=12,
    #     byteload_size_B=1458,
    #     inter_byteload_period_nanosec=1000,
    #     experiment_date="2025-08-12T_17-04-38Z",
    #     title_addendum="_incast_poisson_3to1_8flo_1458B_1us_93pt312Gbps"
    # )
    # do_comparison_graph_trimmed_new(
    #     nw_elem=HOST,
    #     src="host_1",
    #     dst="tor_4",
    #     num_flows=8,
    #     target_per_host_perflo_gdpt_gbps=12,
    #     byteload_size_B=1458,
    #     inter_byteload_period_nanosec=1000,
    #     experiment_date="2025-08-12T_17-04-38Z",
    #     title_addendum="_incast_poisson_3to1_8flo_1458B_1us_93pt312Gbps"
    # )
    # do_comparison_graph_trimmed_new(
    #     nw_elem=HOST,
    #     src="host_2",
    #     dst="tor_4",
    #     num_flows=8,
    #     target_per_host_perflo_gdpt_gbps=12,
    #     byteload_size_B=1458,
    #     inter_byteload_period_nanosec=1000,
    #     experiment_date="2025-08-12T_17-04-38Z",
    #     title_addendum="_incast_poisson_3to1_8flo_1458B_1us_93pt312Gbps"
    # )
    # do_comparison_graph_trimmed_new(
    #     nw_elem=HOST,
    #     src="host_3",
    #     dst="tor_4",
    #     num_flows=8,
    #     target_per_host_perflo_gdpt_gbps=12,
    #     byteload_size_B=1458,
    #     inter_byteload_period_nanosec=1000,
    #     experiment_date="2025-08-12T_17-04-38Z",
    #     title_addendum="_incast_poisson_3to1_8flo_1458B_1us_93pt312Gbps"
    # )

    # ''' --- incast 3to1 2flo 1458B 1us (low load) --- '''
    # do_comparison_graph_trimmed_new(
    #     nw_elem=TOR,
    #     src="tor_4",
    #     dst="host_0",
    #     num_flows=2,
    #     target_per_host_perflo_gdpt_gbps=12,
    #     byteload_size_B=1458,
    #     inter_byteload_period_nanosec=1000,
    #     experiment_date="2025-08-13T_11-34-13Z",
    #     title_addendum="_incast_poisson_3to1_2flo_1458B_1us_23pt33Gbps"
    # )

    
    ''' --- incast 9to1 8flo 1458B 1us --- '''
    do_comparison_graph_trimmed_new(
        nw_elem=TOR,
        src="tor_10",
        dst="host_0",
        num_flows=8,
        target_per_host_perflo_gdpt_gbps=12,
        byteload_size_B=1458,
        inter_byteload_period_nanosec=1000,
        experiment_date="2025-08-12T_18-35-13Z",
        title_addendum="_incast_poisson_9to1_8flo_1458B_1us_93pt312Gbps"
    )
    do_comparison_graph_trimmed_new(
        nw_elem=HOST,
        src="host_1",
        dst="tor_10",
        num_flows=8,
        target_per_host_perflo_gdpt_gbps=12,
        byteload_size_B=1458,
        inter_byteload_period_nanosec=1000,
        experiment_date="2025-08-12T_18-35-13Z",
        title_addendum="_incast_poisson_9to1_8flo_1458B_1us_93pt312Gbps"
    )
    do_comparison_graph_trimmed_new(
        nw_elem=HOST,
        src="host_2",
        dst="tor_10",
        num_flows=8,
        target_per_host_perflo_gdpt_gbps=12,
        byteload_size_B=1458,
        inter_byteload_period_nanosec=1000,
        experiment_date="2025-08-12T_18-35-13Z",
        title_addendum="_incast_poisson_9to1_8flo_1458B_1us_93pt312Gbps"
    )
    do_comparison_graph_trimmed_new(
        nw_elem=HOST,
        src="host_3",
        dst="tor_10",
        num_flows=8,
        target_per_host_perflo_gdpt_gbps=12,
        byteload_size_B=1458,
        inter_byteload_period_nanosec=1000,
        experiment_date="2025-08-12T_18-35-13Z",
        title_addendum="_incast_poisson_9to1_8flo_1458B_1us_93pt312Gbps"
    )

    # do_comparison_graph_trimmed_new(
    #     nw_elem=TOR,
    #     src="tor_4",
    #     dst="host_0",
    #     num_flows=8,
    #     target_per_host_perflo_gdpt_gbps=12,
    #     byteload_size_B=1458,
    #     inter_byteload_period_nanosec=1000,
    #     experiment_date="2025-08-12T_17-00-32Z",
    #     title_addendum="_incast_poisson_3to1_8flo_1458B_1us_93pt312Gbps_fixed_bload"
    # )

    # do_comparison_graph_trimmed_new(
    #     nw_elem=TOR,
    #     src="tor_4",
    #     dst="host_0",
    #     num_flows=8,
    #     target_per_host_perflo_gdpt_gbps=12,
    #     byteload_size_B=1458,
    #     inter_byteload_period_nanosec=1000,
    #     experiment_date="2025-08-12T_18-31-32Z",
    #     title_addendum="_incast_poisson_3to1_8flo_1458B_1us_93pt312Gbps_same_flo_interarr_same_interval"
    # )

    # do_comparison_graph_trimmed_new(
    #     nw_elem=TOR,
    #     src="tor_4",
    #     dst="host_0",
    #     num_flows=8,
    #     target_per_host_perflo_gdpt_gbps=12,
    #     byteload_size_B=1560,
    #     inter_byteload_period_nanosec=1000,
    #     experiment_date="2025-08-12T_18-33-42Z",
    #     title_addendum="_incast_poisson_3to1_8flo_1560B_1us_99pt84Gbps_same_flo_interarr_same_interval"
    # )