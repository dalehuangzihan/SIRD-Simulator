import sys
import subprocess
from pathlib import Path
import shutil

import fct_experiment

PATH_TO_SCRIPTS_R2P2 = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/scripts/r2p2/"
PATH_TO_POSTPROC = f"{PATH_TO_SCRIPTS_R2P2}post-process/"
PATH_TO_SIM_RESULTS = f"{PATH_TO_SCRIPTS_R2P2}coord/results/"

# Common experiment param; value is meaningful only when req_interval_distr is not 'manual'
CLIENT_INJECTION_RATE_GBPS = "60"
DCTCP_ECN_THRESH = 50

AGGR = "aggr"
HOST = "host"
TOR = "tor"

THROUGHPUT_COL = 1
QUEUEING_COL = 2

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

def do_plotting_for_experiment(num_byteloads, byteload_size_B, inter_byteload_period_us, nw_elem, src, dst, title_addendum=""):
    experiment_name = fct_experiment.FctExperiment.get_experiment_name(num_byteloads, byteload_size_B, inter_byteload_period_us) + title_addendum
    print(f"Plotting for experiment: {experiment_name}")

    ssird_results_dir = f"SSIRD-{experiment_name}/"
    shutil.copytree(f"{PATH_TO_SIM_RESULTS}{ssird_results_dir}data/", f"{PATH_TO_SIM_RESULTS}{experiment_name}/data/", dirs_exist_ok=True)

    dctcp_results_dir = f"DCTCP-{DCTCP_ECN_THRESH}-{experiment_name}/"
    shutil.copytree(f"{PATH_TO_SIM_RESULTS}{dctcp_results_dir}data/", f"{PATH_TO_SIM_RESULTS}{experiment_name}/data/", dirs_exist_ok=True)

    ssird_csv_rel_path = f"SSIRD/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"
    dctcp_csv_rel_path = f"DCTCP-{DCTCP_ECN_THRESH}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

    plot_comparison_graph(THROUGHPUT_COL, f"Throughput: SSIRD vs DCTCP ({experiment_name})", experiment_name, ssird_csv_rel_path, dctcp_csv_rel_path)
    plot_comparison_graph(QUEUEING_COL, f"Queueing: SSIRD vs DCTCP ({experiment_name})", experiment_name, ssird_csv_rel_path, dctcp_csv_rel_path)


if __name__ == "__main__":
    # do_plotting_for_experiment(5, 1000000, 50, HOST, "host_0", "tor_4")
    # do_plotting_for_experiment(5, 1000000, 1000, HOST, "host_0", "tor_4")
    do_plotting_for_experiment(5, 1000000, 10, HOST, "host_0", "tor_4", title_addendum="_dctcp_manyconns")
    do_plotting_for_experiment(5, 1000000, 1000, HOST, "host_0", "tor_4", title_addendum="_dctcp_manyconns")
    do_plotting_for_experiment(10, 10000000, 100, HOST, "host_0", "tor_4", title_addendum="_dctcp_manyconns")