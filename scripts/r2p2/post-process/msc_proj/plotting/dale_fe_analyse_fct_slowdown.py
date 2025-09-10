from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import math, statistics
import numpy as np

SSIRD_PLOT_COLOUR = 'tab:orange'
XPASS_PLOT_COLOUR = 'tab:green'
IDEAL_PLOT_COLOUR = 'tab:blue'

LINK_SPEED_GIGABITS_PER_SEC = 100 # 100 GBps link speed
LINK_SPEED_BITS_PER_SEC = LINK_SPEED_GIGABITS_PER_SEC * pow(10,9)

RTT_5US_S = 5 * pow(10,-6) # 5us RTT
RTT_1MS_S = 1 * pow(10,-3) # 1ms RTT

MAX_R2P2_PAYLOAD_B = 1458
DATA_PKT_HEADER_SIZE_B = 80
CREDIT_REQ_PKT_SIZE_B = 84

# PATH_TO_SCRIPTS_R2P2 = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/scripts/r2p2/"
# PATH_TO_SCRIPTS_R2P2 = "/data/dh1723/SIRD-Simulator/scripts/r2p2/" # NOTE: this is for batch1 server
PATH_TO_SCRIPTS_R2P2 = "/home/dh1723/SIRD-Simulator/scripts/r2p2/" # NOTE: this is for octopus server
PATH_TO_POSTPROC = f"{PATH_TO_SCRIPTS_R2P2}post-process/"
PATH_TO_TMP_PLOT = PATH_TO_POSTPROC + "tmp_plot/"
PATH_TO_FCT_SLOWDOWN_PLOTS = PATH_TO_TMP_PLOT + "fct_slowdown_analysis/"

VARY_BLOAD_SIZE = "Varying Byteload Size"
VARY_INTERVAL = "Varying Intervals"
VARY_FLOWRATE = "Varying Flow Rate"


def get_theoretical_fct_single_flow_s(flow_size_B, byteload_size_B, inter_byteload_interval_nanosec, rtt_s):
    fct = None

    byteloads_B_list = []
    remaining_flow_size_B = flow_size_B
    while(remaining_flow_size_B >= byteload_size_B):
        byteloads_B_list.append(byteload_size_B)
        remaining_flow_size_B -= byteload_size_B
    if (remaining_flow_size_B > 0):
        byteloads_B_list.append(remaining_flow_size_B)

    if (len(byteloads_B_list) == 1):
        total_data_transmitted_b = byteloads_B_list[0] * 8
        fct = 0.5*rtt_s +  total_data_transmitted_b / LINK_SPEED_BITS_PER_SEC
        return fct

    app_gdpt_bps = byteload_size_B * 8 / (inter_byteload_interval_nanosec * pow(10, -9))
    # print(app_gdpt_bps*pow(10,-9))
    if (app_gdpt_bps > LINK_SPEED_BITS_PER_SEC):
        flow_size_b = sum(byteloads_B_list) * 8
        fct = 0.5*rtt_s + flow_size_b/LINK_SPEED_BITS_PER_SEC
    else:
        flow_size_b = sum(byteloads_B_list[:-1]) * 8
        # print(flow_size_b/8)
        final_byteload_size_b = byteloads_B_list[-1] * 8
        # print(final_byteload_size_b/8)
        fct = 0.5*rtt_s + flow_size_b/app_gdpt_bps + final_byteload_size_b/app_gdpt_bps

    assert(fct is not None)
    return fct

def get_theoretical_fct_single_flow_s_exact(flow_size_B, byteload_size_B, inter_byteload_interval_nanosec, rtt_s):
    fct = None

    byteloads_B_list = []
    remaining_flow_size_B = flow_size_B
    while(remaining_flow_size_B >= byteload_size_B):
        byteloads_B_list.append(byteload_size_B)
        remaining_flow_size_B -= byteload_size_B
    if (remaining_flow_size_B > 0):
        byteloads_B_list.append(remaining_flow_size_B)

    if (len(byteloads_B_list) == 1):
        total_data_transmitted_b = byteloads_B_list[0] * 8
        fct = 0.5*rtt_s +  total_data_transmitted_b / LINK_SPEED_BITS_PER_SEC
        return fct

    app_gdpt_bps = byteload_size_B * 8 / (inter_byteload_interval_nanosec * pow(10, -9))
    # print(app_gdpt_bps*pow(10,-9))
    if (app_gdpt_bps > LINK_SPEED_BITS_PER_SEC):
        flow_size_b = sum(byteloads_B_list) * 8
        fct = 0.5*rtt_s + flow_size_b/LINK_SPEED_BITS_PER_SEC
    else:
        flow_size_b = sum(byteloads_B_list[:-1]) * 8
        # print(flow_size_b/8)
        final_byteload_size_b = byteloads_B_list[-1] * 8
        # print(final_byteload_size_b/8)
        fct = 0.5*rtt_s + flow_size_b/app_gdpt_bps + final_byteload_size_b/LINK_SPEED_BITS_PER_SEC

    assert(fct is not None)
    return fct

def get_theoretical_fct_parallel_flows_s(num_flows, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_interval_us_list, rtt_s):
    '''
    NOTE: don't use this.
    '''
    num_experiments = len(num_byteloads_per_flow_list)
    assert(num_experiments == len(byteload_size_B_list))
    assert(num_experiments == len(inter_byteload_interval_us_list))
    inter_byteload_interval_s_list = [s * pow(10,-6) for s in inter_byteload_interval_us_list]

    theoretical_fct_s_list = []
    theoretical_thrpt_gbps_list = []
    for i in range(0, num_experiments):
        fct = None

        app_gdpt_bps = num_flows * byteload_size_B_list[i] * 8 / inter_byteload_interval_s_list[i]
        if (app_gdpt_bps > LINK_SPEED_BITS_PER_SEC):
            flow_size_b = num_byteloads_per_flow_list[i] * byteload_size_B_list[i] * 8
            total_data_transmitted_b = num_flows * flow_size_b
            fct = 0.5*rtt_s + total_data_transmitted_b/LINK_SPEED_BITS_PER_SEC 
        else:
            if (num_byteloads_per_flow_list[i] > 1):
                flow_size_b = (num_byteloads_per_flow_list[i] - 1) * byteload_size_B_list[i] * 8
                total_data_transmitted_b = num_flows * flow_size_b
                fct = 0.5*rtt_s + total_data_transmitted_b/app_gdpt_bps + num_flows*byteload_size_B_list[i]*8/LINK_SPEED_BITS_PER_SEC
            else:
                fct = 0.5*rtt_s + num_flows*byteload_size_B_list[i]*8/LINK_SPEED_BITS_PER_SEC

        # # Exact-ish way:
        num_data_pkts_per_byteload = max(math.ceil(byteload_size_B_list[i] / MAX_R2P2_PAYLOAD_B), 1)
        d_hdr_overhead_per_byteload_B = DATA_PKT_HEADER_SIZE_B * num_data_pkts_per_byteload
        
        theoretical_total_data_per_interval_B = num_flows * (byteload_size_B_list[i] + d_hdr_overhead_per_byteload_B + CREDIT_REQ_PKT_SIZE_B)
        theoretical_thrpt_per_interval_bps = theoretical_total_data_per_interval_B * 8 / inter_byteload_interval_s_list[i]
        theoretical_thrpt_gbps_list.append(theoretical_thrpt_per_interval_bps/pow(10,9))
        if (theoretical_thrpt_per_interval_bps > LINK_SPEED_BITS_PER_SEC):
            print(f"NB: Theoretical thrpt (with overheads) exceeds link speed! Bload size: {byteload_size_B_list[i]}B, Interval: {inter_byteload_interval_us_list[i]}us; Theoretical total data per interval: {theoretical_total_data_per_interval_B}B, Theoretical Thrpt: {theoretical_thrpt_per_interval_bps/pow(10,9)}Gbps")

        theoretical_fct_s_list.append(fct)

    print(f"-- Theoretical thrpt per interval: {theoretical_thrpt_gbps_list}")
    return theoretical_fct_s_list

def plot_fct_vs_interval_ssird_xpass_vs_dctcp(inter_byteload_period_us_list, ssird_fct_s_list, xpass_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, title_addendum="", is_log_x=False, is_log_y=False, y_lim=None):
    ssird_fct_ms_list = [t * 1000 for t in ssird_fct_s_list]
    xpass_fct_ms_list = [t * 1000 for t in xpass_fct_s_list]
    ideal_fct_ms_list = [t * 1000 for t in ideal_fct_s_list]

    plt.figure(figsize=(10, 6))
    plt.plot(inter_byteload_period_us_list, ssird_fct_ms_list, label="SSIRD", linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.plot(inter_byteload_period_us_list, xpass_fct_ms_list, label="ExpressPass", linestyle='-', marker='o', color=XPASS_PLOT_COLOUR)
    plt.plot(inter_byteload_period_us_list, ideal_fct_ms_list, label="Ideal (DCTCP)", linestyle='-', marker='o', color=IDEAL_PLOT_COLOUR)
    plt.xlabel('Inter-Byteload Interval (us)')
    plt.ylabel('Flow Completion Time (ms)')
    plt.title(f"FCT: SSIRD, ExpressPass vs Ideal: Varying Intervals\n({num_flows} Flows; {flow_size_B}B per Flow; {total_gdpt_gbps}Gbps Total Goodput)\n {title_addendum}")
    plt.legend()
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log')
    if (y_lim): plt.ylim(y_lim)

    Path(PATH_TO_FCT_SLOWDOWN_PLOTS).mkdir(parents=True, exist_ok=True)
    filename_prefix = "FCT_VARY_INTERVAL_"
    filename = f"{filename_prefix}ssird_vs_xpass_vs_dctcp_{num_flows}flo_{flow_size_B}BperFlo_{total_gdpt_gbps}GbpsGdpt{title_addendum}.png"
    plt.savefig(f"{PATH_TO_FCT_SLOWDOWN_PLOTS}{filename}")
    plt.close()

def plot_fct_vs_byteload_size_ssird_xpass_vs_dctcp(byteload_size_B_list, ssird_fct_s_list, xpass_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, title_addendum="", is_log_x=False, is_log_y=False, y_lim=None):
    ssird_fct_ms_list = [t * 1000 for t in ssird_fct_s_list]
    xpass_fct_ms_list = [t * 1000 for t in xpass_fct_s_list]
    ideal_fct_ms_list = [t * 1000 for t in ideal_fct_s_list]

    plt.figure(figsize=(10, 6))
    plt.plot(byteload_size_B_list, ssird_fct_ms_list, label="SSIRD", linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.plot(byteload_size_B_list, xpass_fct_ms_list, label="ExpressPass", linestyle='-', marker='o', color=XPASS_PLOT_COLOUR)
    plt.plot(byteload_size_B_list, ideal_fct_ms_list, label="Ideal (DCTCP)", linestyle='-', marker='o', color=IDEAL_PLOT_COLOUR)
    plt.xlabel('Byteload Size (B)')
    plt.ylabel('Flow Completion Time (ms)')
    plt.title(f"FCT: SSIRD, ExpressPass vs Ideal: Varying Byteload Size\n({num_flows} Flows; {flow_size_B}B per Flow; {total_gdpt_gbps}Gbps Total Goodput)\n {title_addendum}")
    plt.legend()
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log')
    if (y_lim): plt.ylim(y_lim)

    Path(PATH_TO_FCT_SLOWDOWN_PLOTS).mkdir(parents=True, exist_ok=True)
    filename_prefix = "FCT_VARY_BLOAD_SIZE_"
    filename = f"{filename_prefix}ssird_vs_xpass_vs_dctcp_{num_flows}flo_{flow_size_B}BperFlo_{total_gdpt_gbps}GbpsGdpt{title_addendum}.png"
    plt.savefig(f"{PATH_TO_FCT_SLOWDOWN_PLOTS}{filename}")
    plt.close()

def plot_fct_diff_ssird_xpass_vs_dctcp(experiment_type, x_vals_list, ssird_fct_s_list, xpass_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, title_addendum="", is_log_x=False, is_log_y=False, y_lim=None):
    ssird_fct_diff_s_list = [s - i for s, i in zip(ssird_fct_s_list, ideal_fct_s_list)]
    ssird_fct_diff_us_list = [x * pow(10,6) for x in ssird_fct_diff_s_list]

    xpass_fct_diff_s_list = [s - i for s, i in zip(xpass_fct_s_list, ideal_fct_s_list)]
    xpass_fct_diff_us_list = [x * pow(10,6) for x in xpass_fct_diff_s_list]

    plt.figure(figsize=(10, 6))
    plt.plot(x_vals_list, ssird_fct_diff_us_list, label="SSIRD vs DCTCP", linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.plot(x_vals_list, xpass_fct_diff_us_list, label="ExpressPass vs DCTCP", linestyle='-', marker='o', color=XPASS_PLOT_COLOUR)

    if experiment_type == VARY_BLOAD_SIZE:
        plt.xlabel('Byteload Size (B)')
        filename_prefix = "FCT_DIFF_VARY_BLOAD_SIZE_"
    elif experiment_type == VARY_INTERVAL:
        plt.xlabel('Inter-Byteload Interval (us)')
        filename_prefix = "FCT_DIFF_VARY_INTERVAL_"
    elif experiment_type == VARY_FLOWRATE:
        plt.xlabel('Flow Rate (Gbps)')
        filename_prefix = "FCT_DIFF_VARY_FLOWRATE_"
    else:
        raise ValueError(f"Unknown experiment type: {experiment_type}")
    print(f"{filename_prefix:} FCT Diff (us): {ssird_fct_diff_us_list}")

    plt.ylabel('Flow Completion Time DIFF (us)')
    plt.title(f"FCT Diff: SSIRD, ExpressPass vs Ideal (DCTCP): {experiment_type}\n({num_flows} Flows; {flow_size_B}B per Flow; {total_gdpt_gbps}Gbps Total Goodput)\n {title_addendum}")
    plt.legend()
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log')
    if (y_lim): plt.ylim(y_lim)

    Path(PATH_TO_FCT_SLOWDOWN_PLOTS).mkdir(parents=True, exist_ok=True)
    filename = f"{filename_prefix}ssird_vs_xpass_vs_dctcp_{num_flows}flo_{flow_size_B}BperFlo_{total_gdpt_gbps}GbpsGdpt{title_addendum}.png"
    plt.savefig(f"{PATH_TO_FCT_SLOWDOWN_PLOTS}{filename}")
    plt.close()

def plot_fct_diff_ssird_vs_ideal(
    graph_name,
    experiment_type,
    x_vals_list, ssird_fct_s_list, ideal_fct_s_list,
    num_flows, flow_size_B, total_gdpt_gbps,
    percentile,
    title_addendum="",
    is_log_x=False, is_log_y=False, y_lim=None
):
    ssird_fct_diff_s_list = [s - i for s, i in zip(ssird_fct_s_list, ideal_fct_s_list)]
    ssird_fct_diff_us_list = [x * pow(10,6) for x in ssird_fct_diff_s_list]

    # plt.figure(figsize=(10, 6))
    plt.figure(figsize=(8, 4))
    plt.tight_layout()
    plt.plot(x_vals_list, ssird_fct_diff_us_list, label="SSIRD vs Theoretical", linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)

    if experiment_type == VARY_BLOAD_SIZE:
        plt.xlabel('Byteload Size (B)')
        filename_prefix = "FCT_DIFF_VARY_BLOAD_SIZE_"
    elif experiment_type == VARY_INTERVAL:
        plt.xlabel('Inter-Byteload Interval (us)')
        filename_prefix = "FCT_DIFF_VARY_INTERVAL_"
    elif experiment_type == VARY_FLOWRATE:
        plt.xlabel('Flow Rate (Gbps)')
        filename_prefix = "FCT_DIFF_VARY_FLOWRATE_"
    else:
        raise ValueError(f"Unknown experiment type: {experiment_type}")

    print(f"{filename_prefix:} FCT Diff (us): {ssird_fct_diff_us_list}")

    plt.ylabel(f'FCT Delay (us)')
    # plt.ylabel(f'FCT Delay (us) ({percentile}-th percentile)')
    # plt.title(f"FCT Diff: SSIRD vs Ideal (Theoretical): {experiment_type}\n({num_flows} Flows; {flow_size_B}B per Flow; {total_gdpt_gbps}Gbps Total Goodput)\n {title_addendum}")
    plt.title(f"SSIRD Flow Completion Time Delay\n{graph_name}")
    # plt.legend()
    plt.grid(True)

    ax = plt.gca()
    ax.grid(True, which='both')
    if (y_lim): plt.ylim(y_lim)
    if (is_log_y): plt.yscale('log')
    if (is_log_x):
        ax.set_xscale('log')
        # place ticks at the exact datapoints
        xticks = sorted({float(x) for x in x_vals_list})
        ax.xaxis.set_major_locator(mticker.FixedLocator(xticks))
        # show their raw values as labels
        labels = []
        for x in xticks:
            labels.append(f"{int(x)}" if float(x).is_integer() else f"{x:g}")
            ax.xaxis.set_major_formatter(mticker.FixedFormatter(labels))
            # improve readability (optional)
            # plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            plt.setp(ax.get_xticklabels(), rotation=0, ha='center')
            ax.minorticks_off() # keep only your custom ticks

    Path(PATH_TO_FCT_SLOWDOWN_PLOTS).mkdir(parents=True, exist_ok=True)
    filename = f"{filename_prefix}ssird_vs_ideal_{num_flows}flo_{flow_size_B}BperFlo_{total_gdpt_gbps}GbpsGdpt{title_addendum}.png"
    plt.savefig(f"{PATH_TO_FCT_SLOWDOWN_PLOTS}{filename}")
    plt.close()

def plot_fct_slowdown_ssird_xpass_vs_dctcp(experiment_type, x_vals_list, ssird_fct_s_list, xpass_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, title_addendum="", is_log_x=False, is_log_y=False, y_lim=None):
    ssird_fct_slowdown_list = [s/i for s, i in zip(ssird_fct_s_list, ideal_fct_s_list)]
    xpass_fct_slowdown_list = [s/i for s, i in zip(xpass_fct_s_list, ideal_fct_s_list)]
    ideal_fct_slowdown_list = [s/i for s, i in zip(ideal_fct_s_list, ideal_fct_s_list)]

    plt.figure(figsize=(10, 6))

    if experiment_type == VARY_BLOAD_SIZE:
        x_logscale_addendum = "(Log Scale)" if is_log_x else ""
        plt.xlabel(f'Byteload Size (Bytes) {x_logscale_addendum}')
        filename_prefix = "FCT_SLOWDOWN_VARY_BLOAD_SIZE_"
    elif experiment_type == VARY_INTERVAL:
        plt.xlabel('Inter-Byteload Interval (us)')
        filename_prefix = "FCT_SLOWDOWN_VARY_INTERVAL_"
    elif experiment_type == VARY_FLOWRATE:
        plt.xlabel('Flow Rate (Gbps)')
        filename_prefix = "FCT_SLOWDOWN_VARY_FLOWRATE_"
    else:
        raise ValueError(f"Unknown experiment type: {experiment_type}")
    print(f"{filename_prefix:} Slowdown: {ssird_fct_slowdown_list}")

    plt.plot(x_vals_list, ssird_fct_slowdown_list, label="SSIRD vs DCTCP", linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.plot(x_vals_list, xpass_fct_slowdown_list, label="ExpressPass vs DCTCP", linestyle='-', marker='o', color=XPASS_PLOT_COLOUR)
    plt.plot(x_vals_list, ideal_fct_slowdown_list, label="DCTCP", linestyle=':', marker='X', color=IDEAL_PLOT_COLOUR)

    percentile = round((num_flows-1)/num_flows * 100, 2)
    plt.ylabel(f'FCT Slowdown ({percentile}-th percentile)')
    plt.title(f"FCT Slowdown: SSIRD, ExpressPass vs Ideal (DCTCP): {experiment_type}\n({num_flows} Flows; {flow_size_B}B per Flow; {total_gdpt_gbps}Gbps Total Goodput)\n {title_addendum}")
    plt.legend()

    ax = plt.gca()

    ax.grid(True, which='both')
    if (y_lim): plt.ylim(y_lim)
    if (is_log_y): plt.yscale('log')
    if (is_log_x):
        ax.set_xscale('log')
        # place ticks at the exact datapoints
        xticks = sorted({float(x) for x in x_vals_list})
        ax.xaxis.set_major_locator(mticker.FixedLocator(xticks))
        # show their raw values as labels
        labels = []
        for x in xticks:
            labels.append(f"{int(x)}" if float(x).is_integer() else f"{x:g}")
            ax.xaxis.set_major_formatter(mticker.FixedFormatter(labels))
            # improve readability (optional)
            # plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            plt.setp(ax.get_xticklabels(), rotation=0, ha='center')
            ax.minorticks_off() # keep only your custom ticks

    Path(PATH_TO_FCT_SLOWDOWN_PLOTS).mkdir(parents=True, exist_ok=True)
    filename = f"{filename_prefix}ssird_vs_ideal_{num_flows}flo_{flow_size_B}BperFlo_{total_gdpt_gbps}GbpsGdpt{title_addendum}.png"
    plt.savefig(f"{PATH_TO_FCT_SLOWDOWN_PLOTS}{filename}")
    plt.close()

def plot_fct_slowdown_ssird_vs_ideal(
        experiment_type,
        x_vals_list, ssird_fct_s_list, ideal_fct_s_list,
        num_flows, flow_size_B, total_gdpt_gbps,
        percentile,
        title_addendum="",
        is_log_x=False, is_log_y=False, y_lim=None):
    ssird_fct_slowdown_list = [s/i for s, i in zip(ssird_fct_s_list, ideal_fct_s_list)]
    ideal_fct_slowdown_list = [s/i for s, i in zip(ideal_fct_s_list, ideal_fct_s_list)]

    plt.figure(figsize=(10, 6))

    if experiment_type == VARY_BLOAD_SIZE:
        x_logscale_addendum = "(Log Scale)" if is_log_x else ""
        plt.xlabel(f'Byteload Size (Bytes) {x_logscale_addendum}')
        filename_prefix = "FCT_SLOWDOWN_VARY_BLOAD_SIZE_"
    elif experiment_type == VARY_INTERVAL:
        plt.xlabel('Inter-Byteload Interval (us)')
        filename_prefix = "FCT_SLOWDOWN_VARY_INTERVAL_"
    elif experiment_type == VARY_FLOWRATE:
        plt.xlabel('Flow Rate (Gbps)')
        filename_prefix = "FCT_SLOWDOWN_VARY_FLOWRATE_"
    else:
        raise ValueError(f"Unknown experiment type: {experiment_type}")
    print(f"{filename_prefix:} Slowdown: {ssird_fct_slowdown_list}")

    plt.plot(x_vals_list, ssird_fct_slowdown_list, label="SSIRD vs Theoretical", linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.plot(x_vals_list, ideal_fct_slowdown_list, label="Theoretical", linestyle=':', marker='X', color=IDEAL_PLOT_COLOUR)

    # percentile = round((num_flows-1)/num_flows * 100, 2)
    plt.ylabel(f'FCT Slowdown ({percentile}-th percentile)')
    plt.title(f"FCT Slowdown: SSIRD vs Ideal (Theoretical): {experiment_type}\n({num_flows} Flows; {flow_size_B}B per Flow; {total_gdpt_gbps}Gbps Total Goodput)\n {title_addendum}")
    # plt.legend()

    ax = plt.gca()
    ax.grid(True, which='both')
    if (y_lim): plt.ylim(y_lim)
    if (is_log_y): plt.yscale('log')
    if (is_log_x):
        ax.set_xscale('log')
        # place ticks at the exact datapoints
        xticks = sorted({float(x) for x in x_vals_list})
        ax.xaxis.set_major_locator(mticker.FixedLocator(xticks))
        # show their raw values as labels
        labels = []
        for x in xticks:
            labels.append(f"{int(x)}" if float(x).is_integer() else f"{x:g}")
            ax.xaxis.set_major_formatter(mticker.FixedFormatter(labels))
            # improve readability (optional)
            # plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            plt.setp(ax.get_xticklabels(), rotation=0, ha='center')
            ax.minorticks_off() # keep only your custom ticks

    Path(PATH_TO_FCT_SLOWDOWN_PLOTS).mkdir(parents=True, exist_ok=True)
    filename = f"{filename_prefix}ssird_vs_xpass_vs_dctcp_{num_flows}flo_{flow_size_B}BperFlo_{total_gdpt_gbps}GbpsGdpt{title_addendum}.png"
    plt.savefig(f"{PATH_TO_FCT_SLOWDOWN_PLOTS}{filename}")
    plt.close()

def analyse_fct_slowdown_ssird_xpass_vs_dctcp(
        inter_byteload_period_us_list,
        num_byteloads_list,
        byteload_size_B_list,
        ssird_fct_s_list_list,
        xpass_fct_s_list_list,
        dctcp_fct_s_list_list,
        num_flows,
        flow_size_B,
        total_gdpt_gbps,
        rtt_s=RTT_5US_S,
        title_addendum=""
    ):
    # NOTE: max 1 out of 40 flows is 97.5th percentile 
    ssird_fct_s_max_list = [max(l) for l in ssird_fct_s_list_list]
    xpass_fct_s_max_list = [max(l) for l in xpass_fct_s_list_list]
    dctcp_fct_s_max_list = [max(l) for l in dctcp_fct_s_list_list]
    print(f"SSIRD FCT (s) MAX:{ssird_fct_s_max_list}")
    print(f"XPass FCT (s) MAX:{xpass_fct_s_max_list}")
    print(f"DCTCP FCT (s) MAX:{dctcp_fct_s_max_list}")

    theoretical_fct_parallel_flows_s_list = get_theoretical_fct_parallel_flows_s(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rtt_s)
    print(f"THEORETICAL IDEAL Exactly-parallel FCT (s):{theoretical_fct_parallel_flows_s_list}")

    ssird_fct_s_list = ssird_fct_s_max_list
    xpass_fct_s_list = xpass_fct_s_max_list
    # print("*** VS THEORY")
    # ideal_fct_s_list = theoretical_fct_parallel_flows_s_list 
    print("*** VS DCTCP")
    ideal_fct_s_list = dctcp_fct_s_max_list 

    # Plot FCT
    plot_fct_vs_interval_ssird_xpass_vs_dctcp(inter_byteload_period_us_list, ssird_fct_s_list, xpass_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, title_addendum, is_log_x=True, y_lim=None)
    plot_fct_vs_byteload_size_ssird_xpass_vs_dctcp(byteload_size_B_list,ssird_fct_s_list, xpass_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, title_addendum, is_log_x=True, y_lim=None)

    # Plot FCT Diff
    # fct_diff_ylim = (0, 2000)
    fct_diff_ylim = None
    plot_fct_diff_ssird_xpass_vs_dctcp(VARY_INTERVAL, inter_byteload_period_us_list, ssird_fct_s_list, xpass_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, title_addendum, is_log_x=True, y_lim=fct_diff_ylim)
    plot_fct_diff_ssird_xpass_vs_dctcp(VARY_BLOAD_SIZE, byteload_size_B_list, ssird_fct_s_list, xpass_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, title_addendum, is_log_x=True, y_lim=fct_diff_ylim)

    # Plot FCT Slowdown
    # fct_slowdown_ylim = (0, 4)
    fct_slowdown_ylim = None
    plot_fct_slowdown_ssird_xpass_vs_dctcp(VARY_INTERVAL, inter_byteload_period_us_list, ssird_fct_s_list, xpass_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, title_addendum, is_log_x=True, y_lim=fct_slowdown_ylim)
    plot_fct_slowdown_ssird_xpass_vs_dctcp(VARY_BLOAD_SIZE, byteload_size_B_list, ssird_fct_s_list, xpass_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, title_addendum, is_log_x=True, y_lim=fct_slowdown_ylim)

def analyse_fct_slowdown_ssird_vs_ideal(
        inter_byteload_period_us_list,
        num_byteloads_list,
        byteload_size_B_list,
        ssird_fct_s_list_list,
        num_flows,
        flow_size_B,
        total_gdpt_gbps,
        percentile,
        rtt_s=RTT_5US_S,
        title_addendum=""):
    # NOTE: max 1 out of 40 flows is 97.5th percentile 
    ssird_fct_s_p_list = [np.percentile(l, percentile) for l in ssird_fct_s_list_list]
    print(f"SSIRD FCT (s) MAX:{ssird_fct_s_p_list}")

    # theoretical_fct_parallel_flows_s_list = get_theoretical_fct_parallel_flows_s(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rtt_s)
    theoretical_fct_parallel_flows_s_list = []
    for byteload_size_B, p_us in zip(byteload_size_B_list, inter_byteload_period_us_list):
        p_ns = p_us * 1000
        fct_ideal = get_theoretical_fct_single_flow_s_exact(flow_size_B, byteload_size_B, inter_byteload_interval_nanosec=p_ns, rtt_s=rtt_s)
        theoretical_fct_parallel_flows_s_list.append(fct_ideal)
    print(f"THEORETICAL IDEAL Exactly-parallel FCT (s):{theoretical_fct_parallel_flows_s_list}")

    ssird_fct_s_list = ssird_fct_s_p_list
    print("*** VS THEORY")
    ideal_fct_s_list = theoretical_fct_parallel_flows_s_list 

    # Plot FCT Diff
    fct_diff_ylim = (500, 2000)
    # fct_diff_ylim = (0, 2000)
    # fct_diff_ylim = None
    graph_name_vary_interval = "Vary Interval"
    plot_fct_diff_ssird_vs_ideal(graph_name_vary_interval, VARY_INTERVAL, inter_byteload_period_us_list, ssird_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, percentile, title_addendum, is_log_x=True, y_lim=fct_diff_ylim)
    graph_name_vary_bload_size = "Fixed Flow Size & Rate, Vary Byteload Size, RTT = 1ms"
    plot_fct_diff_ssird_vs_ideal(graph_name_vary_bload_size, VARY_BLOAD_SIZE, byteload_size_B_list, ssird_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, percentile, title_addendum, is_log_x=True, y_lim=fct_diff_ylim)

    # # Plot FCT Slowdown
    # fct_slowdown_ylim = (0, 4)
    # # fct_slowdown_ylim = None
    # plot_fct_slowdown_ssird_vs_ideal(VARY_INTERVAL, inter_byteload_period_us_list, ssird_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, percentile, title_addendum, is_log_x=True, y_lim=fct_slowdown_ylim)
    # plot_fct_slowdown_ssird_vs_ideal(VARY_BLOAD_SIZE, byteload_size_B_list, ssird_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, percentile, title_addendum, is_log_x=True, y_lim=fct_slowdown_ylim)

def analyse_fct_slowdown_ssird_vs_ideal_vary_flowrate(
        inter_byteload_period_us_list,
        num_byteloads_list,
        byteload_size_B_list,
        ssird_fct_s_list_list,
        num_flows,
        flow_size_B,
        total_gdpt_gbps,
        percentile,
        rtt_s=RTT_5US_S,
        title_addendum=""):
    # NOTE: max 1 out of 40 flows is 97.5th percentile 
    # ssird_fct_s_max_list = [max(l) for l in ssird_fct_s_list_list]
    ssird_fct_s_p_list = [np.percentile(l, percentile) for l in ssird_fct_s_list_list]

    print(f"SSIRD FCT (s) MAX:{ssird_fct_s_p_list}")

    # theoretical_fct_parallel_flows_s_list = get_theoretical_fct_parallel_flows_s(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rtt_s)
    theoretical_fct_parallel_flows_s_list = []
    for byteload_size_B, p_us in zip(byteload_size_B_list, inter_byteload_period_us_list):
        p_ns = p_us * 1000
        fct_ideal = get_theoretical_fct_single_flow_s(flow_size_B, byteload_size_B, inter_byteload_interval_nanosec=p_ns, rtt_s=rtt_s)
        theoretical_fct_parallel_flows_s_list.append(fct_ideal)
    print(f"THEORETICAL IDEAL Exactly-parallel FCT (s):{theoretical_fct_parallel_flows_s_list}")

    ssird_fct_s_list = ssird_fct_s_p_list

    print("*** VS THEORY")
    ideal_fct_s_list = theoretical_fct_parallel_flows_s_list 

    flow_rate_gbps_list = []
    assert(len(inter_byteload_period_us_list) == len(byteload_size_B_list))
    for i in range(len(inter_byteload_period_us_list)):
        inter_byteload_period_us = inter_byteload_period_us_list[i]
        byteload_size_B = byteload_size_B_list[i]
        flow_rate_gbps = round(byteload_size_B * 8 / (inter_byteload_period_us * pow(10, -6)) * pow(10,-9), 2)
        flow_rate_gbps_list.append(flow_rate_gbps) 

    # Plot FCT Diff
    fct_diff_ylim = (500, 2000)
    # fct_diff_ylim = (0, 2000)
    # fct_diff_ylim = None
    graph_name_vary_flowrate = "Fixed Flow & Byteload Size, Vary Flow Rate, RTT = 1ms"
    plot_fct_diff_ssird_vs_ideal(graph_name_vary_flowrate, VARY_FLOWRATE, flow_rate_gbps_list, ssird_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, percentile, title_addendum, is_log_x=False, y_lim=fct_diff_ylim)

    # # Plot FCT Slowdown
    # fct_slowdown_ylim = (0, 4)
    # # fct_slowdown_ylim = None
    # plot_fct_slowdown_ssird_vs_ideal(VARY_FLOWRATE, flow_rate_gbps_list, ssird_fct_s_list, ideal_fct_s_list, num_flows, flow_size_B, total_gdpt_gbps, percentile, title_addendum, is_log_x=False, y_lim=fct_slowdown_ylim)

''' Analyse Experiment Results: '''

def fe_analyse_ssird_vs_ideal_fct_fullrange_100Bto1MB_6flo_5usRTT():
    title_addendum = "_fullrange_500Bto1MB_6flo"

    rtt_s = RTT_5US_S
    num_flows = 6
    flow_size_B = 1000000
    total_gdpt_gbps = -1
    inter_byteload_period_us_list = [0.5, 1, 5, 10, 50, 100, 500, 10000]
    num_byteloads_list = [2000, 1000, 200, 100, 20, 10, 2, 1]
    byteload_size_B_list = [500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000]
    ssird_fct_s_list_list = [[0.001002143000000899, 0.0010021900000012351, 0.0010022360000014885, 0.0010022819999999655, 0.0010023290000003016, 0.0010073750000003656], [0.0010017330000007263, 0.0010018190000007365, 0.0010019060000008295, 0.0010019920000008398, 0.00100207800000085, 0.0010071450000008753], [0.000998099000000252, 0.0009985660000015883, 0.0009989910000012259, 0.0009994170000009461, 0.0009998420000005837, 0.001005278000000942], [0.0009984720000009162, 0.0009993170000015539, 0.0010001610000003325, 0.0010010060000009702, 0.0010018510000016079, 0.0010030480000011721], [0.0009618970000015992, 0.000966187000001284, 0.000970411000000837, 0.00097463500000039, 0.000978858999999943, 0.0009830830000012725], [0.0009161049999999449, 0.0009245790000012022, 0.0009330210000015882, 0.0009414630000001978, 0.000949904000000501, 0.000958346000000887], [0.000549868000000231, 0.0005920630000009197, 0.0006342589999999149, 0.0006764540000006036, 0.0007186490000012924, 0.0007608440000002048], [9.211300000089295e-05, 0.00017650400000057687, 0.00026089400000017804, 0.00034528499999986195, 0.0004296750000012395, 0.0005140650000008407]]
    dctcp_fct_s_list_list = [[0.001002092000000232, 0.001002139000000568, 0.0010021850000008214, 0.0010022310000010748, 0.0010022770000013281, 0.0010023239999998879], [0.0010016720000010082, 0.0010017590000011012, 0.0010018450000011114, 0.0010019310000011217, 0.001002017000001132, 0.001002104000001225], [0.0009980480000013614, 0.000998473000000999, 0.0009988980000006364, 0.000999323000000274, 0.0009997479999999115, 0.0010001730000013254], [0.0009934670000006918, 0.000994310000001164, 0.0009951539999999426, 0.0009959980000004975, 0.0009968410000009698, 0.0009976850000015247], [0.0009568410000007077, 0.0009610600000016234, 0.00096527800000068, 0.0009694970000015957, 0.0009737150000006523, 0.0009779330000014852], [0.0009516569999998836, 0.0009519670000006641, 0.0009522770000014447, 0.0009525870000004488, 0.0009528960000011466, 0.0009532060000001508], [0.000641472999999948, 0.0007403390000000343, 0.0007564210000001736, 0.000758882000001293, 0.0007366500000003384, 0.000739417000000131], [0.0002897900000000675, 0.0003847760000006417, 0.0005068290000007636, 0.0005073140000000365, 0.000507798000001003, 0.0005085200000003454]]

    print(f"RTT (us): {rtt_s * pow(10,6)}")
    print(f"Byteload Size (B): {byteload_size_B_list}")
    analyse_fct_slowdown_ssird_xpass_vs_dctcp(inter_byteload_period_us_list, num_byteloads_list, byteload_size_B_list, ssird_fct_s_list_list, dctcp_fct_s_list_list, num_flows, flow_size_B, total_gdpt_gbps, rtt_s, title_addendum)

def fe_analyse_ssird_vs_ideal_fct_fullrange_100Bto100KB_40flo_5usRTT():
    title_addendum = "_fullrange_500Bto100KB_40flo"

    rtt_s = RTT_5US_S
    num_flows = 40
    flow_size_B = 1000000
    total_gdpt_gbps = -1
    inter_byteload_period_us_list = [0.5, 1, 5, 10, 50, 100]
    num_byteloads_list = [2000, 1000, 200, 100, 20, 10]
    byteload_size_B_list = [500, 1000, 5000, 10000, 50000, 100000]
    ssird_fct_s_list_list = [[0.010004453000000524, 0.009998893000000564, 0.00999815000000126, 0.009999496000000718, 0.009998475000001505, 0.009997918000001604, 0.009999356999999875, 0.00999898500000107, 0.009997872000001351, 0.009998568000000319, 0.009998104000001007, 0.009998753000001415, 0.00999805700000067, 0.009998799999999974, 0.00999912500000022, 0.009999449000000382, 0.009998429000001252, 0.009999589000001308, 0.009998520999999982, 0.009998382000000916, 0.009998846000000228, 0.009998011000000417, 0.009998939000000817, 0.009999217000000726, 0.009998614000000572, 0.009998197000001596, 0.009999077999999884, 0.009999032000001407, 0.009999635000001561, 0.009998336000000663, 0.009999403000000129, 0.009998243000000073, 0.009998661000000908, 0.009998289000000327, 0.009999310000001316, 0.009999264000001062, 0.009998707000001161, 0.009997965000000164, 0.009999542000000972, 0.009999171000000473], [0.009999268000001393, 0.00999771300000063, 0.009998663000001073, 0.009999872999999937, 0.009999355000001486, 0.009999958999999947, 0.010000910000000474, 0.009999786999999927, 0.01000073700000037, 0.010000305000000154, 0.00999831800000095, 0.00999900900000128, 0.009998750000001166, 0.009999441000001497, 0.009998491000001053, 0.00999970000000161, 0.010000564000000267, 0.00999840400000096, 0.009998577000001063, 0.009998231000000857, 0.00999909500000129, 0.009999527000001507, 0.00999892300000127, 0.009997972000000743, 0.009998059000000836, 0.010000478000000257, 0.009998836000001177, 0.010001083000000577, 0.010000219000000143, 0.01000004600000004, 0.009997886000000733, 0.009999182000001383, 0.009998145000000846, 0.01000013200000005, 0.0099996140000016, 0.01000082300000038, 0.010000996000000484, 0.00999779900000064, 0.010000391000000164, 0.01000065100000036], [0.00996325700000078, 0.009973056000001534, 0.009970926000001157, 0.009970075000000023, 0.00997050100000152, 0.009967947000001587, 0.009966666000000401, 0.009959001000000356, 0.009969224000000665, 0.009961129000000568, 0.009971352000000877, 0.00997433200000053, 0.009965389000001323, 0.009961981000000009, 0.009959853000001573, 0.009958099000000331, 0.009973481000001172, 0.009965814000000961, 0.009972630000000038, 0.009972204000000318, 0.009961555000000288, 0.009962832000001143, 0.009964534000001635, 0.009964960000001355, 0.009967096000000453, 0.009969649000000302, 0.0099636830000005, 0.009973907000000892, 0.009968373000001307, 0.00996027800000121, 0.00996410900000022, 0.00996752100000009, 0.009968798000000945, 0.009966240000000681, 0.009958576000000718, 0.009962406000001423, 0.00997177900000068, 0.00996070400000093, 0.00997475800000025, 0.009959427000000076], [0.009909353000001175, 0.009921214000000234, 0.009938126000001546, 0.009914439000000996, 0.009912749000001497, 0.009922059000000871, 0.009926283000000424, 0.009931368000000163, 0.009915284000001634, 0.009927128000001062, 0.0099322130000008, 0.009913594000000359, 0.009934747000000854, 0.009910215000001443, 0.009922904000001509, 0.009941506000000544, 0.009911905000000942, 0.009925438000001563, 0.00993050800000006, 0.009933902000000217, 0.00992374900000037, 0.009916129000000495, 0.009938971000000407, 0.009940660999999906, 0.009937282000000991, 0.00991868000000018, 0.009929663000001199, 0.009936437000000353, 0.009939816000001045, 0.009927972999999923, 0.009920369000001372, 0.009933058000001438, 0.00991697300000105, 0.009908508000000538, 0.009928818000000561, 0.009917835000001318, 0.009911060000000305, 0.009919525000000817, 0.009924593000000925, 0.009935592000001492], [0.00955842699999998, 0.009642906999999923, 0.009575322999999969, 0.009609114999999946, 0.009651355000000805, 0.009617563000000828, 0.009659802999999911, 0.009524635000000004, 0.009634459000000817, 0.009511897000001213, 0.00956265100000131, 0.009596443000001287, 0.00963868300000037, 0.009613339000001275, 0.009541530999999992, 0.009583771000000851, 0.009587995000000404, 0.009516187000000897, 0.009554203000000427, 0.009528859000001333, 0.009604891000000393, 0.00960066700000084, 0.00952041100000045, 0.009549979000000874, 0.009566875000000863, 0.009592218999999957, 0.00966402700000124, 0.009579547000001298, 0.009655579000000358, 0.009647131000001252, 0.009545755000001321, 0.009621787000000381, 0.009571099000000416, 0.009630235000001264, 0.009537307000000439, 0.009668251000000794, 0.009626010999999934, 0.0096766989999999, 0.009533083000000886, 0.009672475000000347], [0.009201853000000426, 0.009176528000001127, 0.009277828000000099, 0.009303152000001091, 0.009311594000001477, 0.009075229000000462, 0.00913432000000114, 0.009210295000000812, 0.009108996000000147, 0.009066788000000159, 0.009286269000000402, 0.009016105000000607, 0.00905834600000155, 0.009320036000000087, 0.009184970000001513, 0.0092525030000008, 0.009218736000001115, 0.009083671000000848, 0.009336919000000776, 0.009100554000001537, 0.009244061000000414, 0.00932847700000039, 0.009142762000001525, 0.009151204000000135, 0.009049904000001163, 0.009193412000000123, 0.009033021000000474, 0.00926938600000149, 0.009260944000001103, 0.009159645000000438, 0.00934536000000108, 0.009227178000001501, 0.009092112000001151, 0.009168087000000824, 0.009235620000000111, 0.00902458000000017, 0.009125879000000836, 0.00911743700000045, 0.00904146300000086, 0.009294711000000788]]
    dctcp_fct_s_list_list = [[0.009997592000001276, 0.009997639000001612, 0.00999768500000009, 0.009997731000000343, 0.009997777000000596, 0.009997824000000932, 0.009997870000001186, 0.009997916000001439, 0.009997961999999916, 0.009998009000000252, 0.009998055000000505, 0.009998101000000759, 0.009998147000001012, 0.009998194000001348, 0.009998240000001601, 0.009998286000000078, 0.009998332000000332, 0.009998379000000668, 0.009998425000000921, 0.009998471000001175, 0.009998517000001428, 0.009998563999999988, 0.009998610000000241, 0.009998656000000494, 0.009998702000000748, 0.009998748000001001, 0.009998795000001337, 0.00999884100000159, 0.009998887000000067, 0.00999893300000032, 0.009998980000000657, 0.00999902600000091, 0.009999072000001163, 0.009999118000001417, 0.009999164999999977, 0.00999921100000023, 0.009999257000000483, 0.009999303000000737, 0.009999350000001073, 0.009999396000001326], [0.00999267200000098, 0.009992759000001072, 0.009992845000001083, 0.009992931000001093, 0.009993017000001103, 0.009993104000001196, 0.009993190000001206, 0.009993276000001217, 0.009993362000001227, 0.00999344900000132, 0.00999353500000133, 0.00999362100000134, 0.00999370700000135, 0.009993794000001444, 0.009993880000001454, 0.009993966000001464, 0.009994052000001474, 0.009994139000001567, 0.009994225000001578, 0.009994311000001588, 0.009994397000001598, 0.009994483999999915, 0.009994569999999925, 0.009994655999999935, 0.009994741999999945, 0.009994827999999956, 0.009994915000000049, 0.009995001000000059, 0.009995087000000069, 0.00999517300000008, 0.009995260000000172, 0.009995346000000183, 0.009995432000000193, 0.009995518000000203, 0.009995605000000296, 0.009995691000000306, 0.009995777000000317, 0.009995863000000327, 0.00999595000000042, 0.00999603600000043], [0.00995304800000163, 0.009953473000001267, 0.009953898000000905, 0.009954323000000542, 0.00995474800000018, 0.009955173000001594, 0.009955598000001231, 0.009956023000000869, 0.009956448000000506, 0.009956873000000144, 0.009957298000001558, 0.009957723000001195, 0.009958148000000833, 0.009958572000000387, 0.009958997000000025, 0.009959422000001439, 0.009959847000001076, 0.009960272000000714, 0.009960697000000351, 0.009961121999999989, 0.009961547000001403, 0.00996197200000104, 0.009962397000000678, 0.009962822000000315, 0.009963246999999953, 0.009963672000001367, 0.009964097000001004, 0.009964522000000642, 0.00996494700000028, 0.009965371999999917, 0.00996579700000133, 0.009966222000000968, 0.009966647000000606, 0.009967072000000243, 0.00996749699999988, 0.009967922000001295, 0.009968347000000932, 0.00996877200000057, 0.009969196000000125, 0.009969621000001538], [0.009903467000000887, 0.00990431000000136, 0.009905154000000138, 0.009905998000000693, 0.009906841000001165, 0.009907684999999944, 0.009908529000000499, 0.009909372000000971, 0.009910216000001526, 0.009911060000000305, 0.00991190400000086, 0.009912747000001332, 0.00991359100000011, 0.009914435000000665, 0.009915278000001138, 0.009916121999999916, 0.009916966000000471, 0.009917809000000943, 0.009918653000001498, 0.009919497000000277, 0.009920340000000749, 0.009921184000001304, 0.009922028000000083, 0.009922871000000555, 0.00992371500000111, 0.009924558999999888, 0.00992540200000036, 0.009926246000000916, 0.00992709000000147, 0.009927933000000166, 0.009928777000000721, 0.009929621000001276, 0.009930463999999972, 0.009931308000000527, 0.009932152000001082, 0.00993299599999986, 0.009933839000000333, 0.009934683000000888, 0.009935527000001443, 0.009936370000000139], [0.009506841000000321, 0.009511060000001237, 0.009515278000000293, 0.009519497000001209, 0.009523715000000266, 0.009527933000001099, 0.009532152000000238, 0.009536370000001071, 0.00954058900000021, 0.009544807000001043, 0.0095490250000001, 0.009553244000001015, 0.009557462000000072, 0.009561681000000988, 0.009565899000000044, 0.009570117000000877, 0.009574336000000017, 0.00957855400000085, 0.009582772999999989, 0.009586991000000822, 0.009591208999999878, 0.009595428000000794, 0.009599646000001627, 0.009603865000000766, 0.0096080830000016, 0.009612301000000656, 0.009616520000001572, 0.009620738000000628, 0.009624957000001544, 0.0096291750000006, 0.009633393000001433, 0.009637612000000573, 0.009641830000001406, 0.009646049000000545, 0.009650267000001378, 0.009654485000000435, 0.00965870400000135, 0.009662922000000407, 0.009667141000001322, 0.009671359000000379], [0.009327759000001379, 0.0093280680000003, 0.00932837800000108, 0.009328688000000085, 0.009328998000000865, 0.00932930799999987, 0.00932961800000065, 0.00932992800000143, 0.009330238000000435, 0.009330548000001215, 0.00933085800000022, 0.009331168000001, 0.009331478000000004, 0.009331788000000785, 0.009332097000001482, 0.009332407000000487, 0.009332717000001267, 0.009333027000000271, 0.009333337000001052, 0.009333647000000056, 0.009333957000000837, 0.009334267000001617, 0.009334577000000621, 0.009334887000001402, 0.009335197000000406, 0.009335507000001186, 0.009335940000001486, 0.009336371999999926, 0.009336805000000226, 0.009337238000000525, 0.009337671000000825, 0.009338104000001124, 0.009338537000001423, 0.009338969999999946, 0.009339403000000246, 0.009339836000000545, 0.009340269000000845, 0.009340579000001625, 0.00934088900000063, 0.00934119900000141]]

    print(f"RTT (us): {rtt_s * pow(10,6)}")
    print(f"Byteload Size (B): {byteload_size_B_list}")
    analyse_fct_slowdown_ssird_xpass_vs_dctcp(inter_byteload_period_us_list, num_byteloads_list, byteload_size_B_list, ssird_fct_s_list_list, dctcp_fct_s_list_list, num_flows, flow_size_B, total_gdpt_gbps, rtt_s, title_addendum)

def fe_analyse_ssird_xpass_vs_dctcp_fct_fullrange_100Bto100KB_40flo_5usRTT():
    title_addendum = "_fullrange_500Bto100KB_40flo_allproto"

    rtt_s = RTT_5US_S
    num_flows = 40
    flow_size_B = 1000000
    total_gdpt_gbps = -1
    inter_byteload_period_us_list = [0.5, 1, 5, 10, 50, 100]
    num_byteloads_list = [2000, 1000, 200, 100, 20, 10]
    byteload_size_B_list = [500, 1000, 5000, 10000, 50000, 100000]
    ssird_fct_s_list_list = [[0.010004453000000524, 0.009998893000000564, 0.00999815000000126, 0.009999496000000718, 0.009998475000001505, 0.009997918000001604, 0.009999356999999875, 0.00999898500000107, 0.009997872000001351, 0.009998568000000319, 0.009998104000001007, 0.009998753000001415, 0.00999805700000067, 0.009998799999999974, 0.00999912500000022, 0.009999449000000382, 0.009998429000001252, 0.009999589000001308, 0.009998520999999982, 0.009998382000000916, 0.009998846000000228, 0.009998011000000417, 0.009998939000000817, 0.009999217000000726, 0.009998614000000572, 0.009998197000001596, 0.009999077999999884, 0.009999032000001407, 0.009999635000001561, 0.009998336000000663, 0.009999403000000129, 0.009998243000000073, 0.009998661000000908, 0.009998289000000327, 0.009999310000001316, 0.009999264000001062, 0.009998707000001161, 0.009997965000000164, 0.009999542000000972, 0.009999171000000473], [0.009999268000001393, 0.00999771300000063, 0.009998663000001073, 0.009999872999999937, 0.009999355000001486, 0.009999958999999947, 0.010000910000000474, 0.009999786999999927, 0.01000073700000037, 0.010000305000000154, 0.00999831800000095, 0.00999900900000128, 0.009998750000001166, 0.009999441000001497, 0.009998491000001053, 0.00999970000000161, 0.010000564000000267, 0.00999840400000096, 0.009998577000001063, 0.009998231000000857, 0.00999909500000129, 0.009999527000001507, 0.00999892300000127, 0.009997972000000743, 0.009998059000000836, 0.010000478000000257, 0.009998836000001177, 0.010001083000000577, 0.010000219000000143, 0.01000004600000004, 0.009997886000000733, 0.009999182000001383, 0.009998145000000846, 0.01000013200000005, 0.0099996140000016, 0.01000082300000038, 0.010000996000000484, 0.00999779900000064, 0.010000391000000164, 0.01000065100000036], [0.00996325700000078, 0.009973056000001534, 0.009970926000001157, 0.009970075000000023, 0.00997050100000152, 0.009967947000001587, 0.009966666000000401, 0.009959001000000356, 0.009969224000000665, 0.009961129000000568, 0.009971352000000877, 0.00997433200000053, 0.009965389000001323, 0.009961981000000009, 0.009959853000001573, 0.009958099000000331, 0.009973481000001172, 0.009965814000000961, 0.009972630000000038, 0.009972204000000318, 0.009961555000000288, 0.009962832000001143, 0.009964534000001635, 0.009964960000001355, 0.009967096000000453, 0.009969649000000302, 0.0099636830000005, 0.009973907000000892, 0.009968373000001307, 0.00996027800000121, 0.00996410900000022, 0.00996752100000009, 0.009968798000000945, 0.009966240000000681, 0.009958576000000718, 0.009962406000001423, 0.00997177900000068, 0.00996070400000093, 0.00997475800000025, 0.009959427000000076], [0.009909353000001175, 0.009921214000000234, 0.009938126000001546, 0.009914439000000996, 0.009912749000001497, 0.009922059000000871, 0.009926283000000424, 0.009931368000000163, 0.009915284000001634, 0.009927128000001062, 0.0099322130000008, 0.009913594000000359, 0.009934747000000854, 0.009910215000001443, 0.009922904000001509, 0.009941506000000544, 0.009911905000000942, 0.009925438000001563, 0.00993050800000006, 0.009933902000000217, 0.00992374900000037, 0.009916129000000495, 0.009938971000000407, 0.009940660999999906, 0.009937282000000991, 0.00991868000000018, 0.009929663000001199, 0.009936437000000353, 0.009939816000001045, 0.009927972999999923, 0.009920369000001372, 0.009933058000001438, 0.00991697300000105, 0.009908508000000538, 0.009928818000000561, 0.009917835000001318, 0.009911060000000305, 0.009919525000000817, 0.009924593000000925, 0.009935592000001492], [0.00955842699999998, 0.009642906999999923, 0.009575322999999969, 0.009609114999999946, 0.009651355000000805, 0.009617563000000828, 0.009659802999999911, 0.009524635000000004, 0.009634459000000817, 0.009511897000001213, 0.00956265100000131, 0.009596443000001287, 0.00963868300000037, 0.009613339000001275, 0.009541530999999992, 0.009583771000000851, 0.009587995000000404, 0.009516187000000897, 0.009554203000000427, 0.009528859000001333, 0.009604891000000393, 0.00960066700000084, 0.00952041100000045, 0.009549979000000874, 0.009566875000000863, 0.009592218999999957, 0.00966402700000124, 0.009579547000001298, 0.009655579000000358, 0.009647131000001252, 0.009545755000001321, 0.009621787000000381, 0.009571099000000416, 0.009630235000001264, 0.009537307000000439, 0.009668251000000794, 0.009626010999999934, 0.0096766989999999, 0.009533083000000886, 0.009672475000000347], [0.009201853000000426, 0.009176528000001127, 0.009277828000000099, 0.009303152000001091, 0.009311594000001477, 0.009075229000000462, 0.00913432000000114, 0.009210295000000812, 0.009108996000000147, 0.009066788000000159, 0.009286269000000402, 0.009016105000000607, 0.00905834600000155, 0.009320036000000087, 0.009184970000001513, 0.0092525030000008, 0.009218736000001115, 0.009083671000000848, 0.009336919000000776, 0.009100554000001537, 0.009244061000000414, 0.00932847700000039, 0.009142762000001525, 0.009151204000000135, 0.009049904000001163, 0.009193412000000123, 0.009033021000000474, 0.00926938600000149, 0.009260944000001103, 0.009159645000000438, 0.00934536000000108, 0.009227178000001501, 0.009092112000001151, 0.009168087000000824, 0.009235620000000111, 0.00902458000000017, 0.009125879000000836, 0.00911743700000045, 0.00904146300000086, 0.009294711000000788]]
    dctcp_fct_s_list_list = [[0.009997592000001276, 0.009997639000001612, 0.00999768500000009, 0.009997731000000343, 0.009997777000000596, 0.009997824000000932, 0.009997870000001186, 0.009997916000001439, 0.009997961999999916, 0.009998009000000252, 0.009998055000000505, 0.009998101000000759, 0.009998147000001012, 0.009998194000001348, 0.009998240000001601, 0.009998286000000078, 0.009998332000000332, 0.009998379000000668, 0.009998425000000921, 0.009998471000001175, 0.009998517000001428, 0.009998563999999988, 0.009998610000000241, 0.009998656000000494, 0.009998702000000748, 0.009998748000001001, 0.009998795000001337, 0.00999884100000159, 0.009998887000000067, 0.00999893300000032, 0.009998980000000657, 0.00999902600000091, 0.009999072000001163, 0.009999118000001417, 0.009999164999999977, 0.00999921100000023, 0.009999257000000483, 0.009999303000000737, 0.009999350000001073, 0.009999396000001326], [0.00999267200000098, 0.009992759000001072, 0.009992845000001083, 0.009992931000001093, 0.009993017000001103, 0.009993104000001196, 0.009993190000001206, 0.009993276000001217, 0.009993362000001227, 0.00999344900000132, 0.00999353500000133, 0.00999362100000134, 0.00999370700000135, 0.009993794000001444, 0.009993880000001454, 0.009993966000001464, 0.009994052000001474, 0.009994139000001567, 0.009994225000001578, 0.009994311000001588, 0.009994397000001598, 0.009994483999999915, 0.009994569999999925, 0.009994655999999935, 0.009994741999999945, 0.009994827999999956, 0.009994915000000049, 0.009995001000000059, 0.009995087000000069, 0.00999517300000008, 0.009995260000000172, 0.009995346000000183, 0.009995432000000193, 0.009995518000000203, 0.009995605000000296, 0.009995691000000306, 0.009995777000000317, 0.009995863000000327, 0.00999595000000042, 0.00999603600000043], [0.00995304800000163, 0.009953473000001267, 0.009953898000000905, 0.009954323000000542, 0.00995474800000018, 0.009955173000001594, 0.009955598000001231, 0.009956023000000869, 0.009956448000000506, 0.009956873000000144, 0.009957298000001558, 0.009957723000001195, 0.009958148000000833, 0.009958572000000387, 0.009958997000000025, 0.009959422000001439, 0.009959847000001076, 0.009960272000000714, 0.009960697000000351, 0.009961121999999989, 0.009961547000001403, 0.00996197200000104, 0.009962397000000678, 0.009962822000000315, 0.009963246999999953, 0.009963672000001367, 0.009964097000001004, 0.009964522000000642, 0.00996494700000028, 0.009965371999999917, 0.00996579700000133, 0.009966222000000968, 0.009966647000000606, 0.009967072000000243, 0.00996749699999988, 0.009967922000001295, 0.009968347000000932, 0.00996877200000057, 0.009969196000000125, 0.009969621000001538], [0.009903467000000887, 0.00990431000000136, 0.009905154000000138, 0.009905998000000693, 0.009906841000001165, 0.009907684999999944, 0.009908529000000499, 0.009909372000000971, 0.009910216000001526, 0.009911060000000305, 0.00991190400000086, 0.009912747000001332, 0.00991359100000011, 0.009914435000000665, 0.009915278000001138, 0.009916121999999916, 0.009916966000000471, 0.009917809000000943, 0.009918653000001498, 0.009919497000000277, 0.009920340000000749, 0.009921184000001304, 0.009922028000000083, 0.009922871000000555, 0.00992371500000111, 0.009924558999999888, 0.00992540200000036, 0.009926246000000916, 0.00992709000000147, 0.009927933000000166, 0.009928777000000721, 0.009929621000001276, 0.009930463999999972, 0.009931308000000527, 0.009932152000001082, 0.00993299599999986, 0.009933839000000333, 0.009934683000000888, 0.009935527000001443, 0.009936370000000139], [0.009506841000000321, 0.009511060000001237, 0.009515278000000293, 0.009519497000001209, 0.009523715000000266, 0.009527933000001099, 0.009532152000000238, 0.009536370000001071, 0.00954058900000021, 0.009544807000001043, 0.0095490250000001, 0.009553244000001015, 0.009557462000000072, 0.009561681000000988, 0.009565899000000044, 0.009570117000000877, 0.009574336000000017, 0.00957855400000085, 0.009582772999999989, 0.009586991000000822, 0.009591208999999878, 0.009595428000000794, 0.009599646000001627, 0.009603865000000766, 0.0096080830000016, 0.009612301000000656, 0.009616520000001572, 0.009620738000000628, 0.009624957000001544, 0.0096291750000006, 0.009633393000001433, 0.009637612000000573, 0.009641830000001406, 0.009646049000000545, 0.009650267000001378, 0.009654485000000435, 0.00965870400000135, 0.009662922000000407, 0.009667141000001322, 0.009671359000000379], [0.009327759000001379, 0.0093280680000003, 0.00932837800000108, 0.009328688000000085, 0.009328998000000865, 0.00932930799999987, 0.00932961800000065, 0.00932992800000143, 0.009330238000000435, 0.009330548000001215, 0.00933085800000022, 0.009331168000001, 0.009331478000000004, 0.009331788000000785, 0.009332097000001482, 0.009332407000000487, 0.009332717000001267, 0.009333027000000271, 0.009333337000001052, 0.009333647000000056, 0.009333957000000837, 0.009334267000001617, 0.009334577000000621, 0.009334887000001402, 0.009335197000000406, 0.009335507000001186, 0.009335940000001486, 0.009336371999999926, 0.009336805000000226, 0.009337238000000525, 0.009337671000000825, 0.009338104000001124, 0.009338537000001423, 0.009338969999999946, 0.009339403000000246, 0.009339836000000545, 0.009340269000000845, 0.009340579000001625, 0.00934088900000063, 0.00934119900000141]]
    xpass_fct_s_list_list = [[0.009998059000000836, 0.009998152000001426, 0.009998245000000239, 0.009998338000000828, 0.009998390999999884, 0.009998444000000717, 0.00999849700000155, 0.010003124000000696, 0.010003248000000298, 0.010003377000000313, 0.01000371599999994, 0.009998549000000523, 0.010012169000001236, 0.010042287000000982, 0.010067035000000502, 0.010054981000001462, 0.010070716000001312, 0.010028004000000479, 0.010056091000000933, 0.010061856000000091, 0.010007426000001374, 0.010015343000000954, 0.009998602000001355, 0.009998769000000962, 0.01002700500000131, 0.010028674000000848, 0.010016567000000975, 0.009998822000000018, 0.010047029000000762, 0.010075406000000342, 0.010061066000000451, 0.010064016000001175, 0.010044309000001306, 0.01000692600000086, 0.010042215000000354, 0.010000967999999943, 0.01001153400000021, 0.010077346000000986, 0.010083970000000164, 0.01001959600000113], [0.009997699000001248, 0.00999779200000006, 0.00999791899999991, 0.009998046000001537, 0.009998165000000725, 0.009998287000000161, 0.009998412999999928, 0.009998552000000771, 0.010066410000000303, 0.01005591100000025, 0.010070235000000594, 0.010041396000000091, 0.010049802000001051, 0.010066926000000365, 0.010039710000000923, 0.010029009000000144, 0.009998851000000641, 0.010009521000000632, 0.010013578000000578, 0.010045954000000634, 0.010056077000001551, 0.010050151000001506, 0.010052976000000768, 0.010031356000000713, 0.010027843000001369, 0.01008157000000054, 0.009993474999999918, 0.009996307000001536, 0.01005116900000047, 0.01002791099999989, 0.010079986000000929, 0.01004004500000022, 0.010004810999999947, 0.009998990000001484, 0.010027272000000309, 0.010014995000000582, 0.010084552000000357, 0.009993959000000885, 0.010004174000000532, 0.010041306000001526], [0.009996164000000363, 0.00999507400000077, 0.010038928000000169, 0.009996471000000895, 0.009994203000001534, 0.010032657, 0.010045850000000911, 0.009996540000001275, 0.010045738000000526, 0.010041992000001443, 0.009981240000000113, 0.009983272000001264, 0.00999852400000023, 0.009982937000000192, 0.009983346000000282, 0.00998719100000045, 0.01000395100000162, 0.009998996000000204, 0.009997824000000932, 0.009997247000001153, 0.009989589999999993, 0.010052082000001406, 0.009984643000001014, 0.009988784000000805, 0.009995249000001039, 0.009997530000001476, 0.009990340999999958, 0.009989227000000156, 0.00999137000000161, 0.009998229000000691, 0.009987843000001106, 0.010005072000000226, 0.009983945000000105, 0.009991089000001452, 0.009992045000000616, 0.009982869999999977, 0.009982246999999944, 0.009987721999999977, 0.009997184000001269, 0.00996371400000129], [0.009915335000000525, 0.00996039400000015, 0.009987221000001156, 0.009953743000000514, 0.009944639000000421, 0.010018725000000117, 0.009940105000000088, 0.009962085000001508, 0.009969007000000474, 0.009982761000001616, 0.009984045000001274, 0.00994539100000047, 0.009958598000000762, 0.009946734000001456, 0.009962265000000414, 0.010012611000000504, 0.010022951999999918, 0.009937148000000562, 0.010017415000000085, 0.009939363000000867, 0.00991403500000132, 0.010017164000000633, 0.009995635000001002, 0.01002710800000095, 0.009977090000001354, 0.010021392000000517, 0.009953837000001187, 0.009929614000000697, 0.009956657000000035, 0.009999488000000056, 0.009960895000000747, 0.009999190000000269, 0.009938054000000918, 0.010034907000001425, 0.00993025400000036, 0.010011646000000596, 0.009954994000000994, 0.009926021000000063, 0.009937934999999953, 0.010011775000000611], [0.009648729000000245, 0.009732044000001494, 0.009669479000001147, 0.00970475100000101, 0.009693654000001217, 0.009710125000001568, 0.009729276000001619, 0.00972190900000136, 0.009663512000001262, 0.009602558000000982, 0.009707298000000364, 0.009699308000000073, 0.009721000000000757, 0.009601783000000808, 0.009682629000000276, 0.009745768000000155, 0.009684158000000664, 0.009658211000001415, 0.009668319000001091, 0.009686813000000072, 0.009627013000001128, 0.009735184000000174, 0.009758615000000859, 0.009663167000001138, 0.009706258000001355, 0.009743135000000791, 0.009613949000000233, 0.009643830999999992, 0.00968279300000141, 0.009697098000000182, 0.009700987000000438, 0.009710877000001616, 0.00976683500000064, 0.009691478000000586, 0.009677445000001228, 0.009661170000001107, 0.009663547000000605, 0.009707879000000474, 0.009670824000000522, 0.009681898000000189], [0.009309393000000554, 0.009337838000000431, 0.009317002000001295, 0.009398079000000337, 0.009321905000000186, 0.009295005000000245, 0.009308576000000457, 0.009334400000000187, 0.009388375000000337, 0.00930018200000049, 0.00924999800000137, 0.0094144310000015, 0.009436938000000339, 0.009362177999999943, 0.00947522300000081, 0.009379326000001242, 0.00935534300000107, 0.009378382000001295, 0.009248419000000396, 0.00936459300000081, 0.00938103600000062, 0.009301724000000178, 0.009329951999999864, 0.009384114000001276, 0.009347550000001092, 0.009341156000001405, 0.009354670000000453, 0.009408984000000231, 0.009326688000001582, 0.009378058000001133, 0.0094378740000014, 0.009371090000000137, 0.00930275199999997, 0.009303784000000093, 0.009346752000000791, 0.009362053000000259, 0.009304679000001315, 0.009319169000001182, 0.009349614000001338, 0.00933059100000122]]

    print(f"RTT (us): {rtt_s * pow(10,6)}")
    print(f"Byteload Size (B): {byteload_size_B_list}")
    analyse_fct_slowdown_ssird_xpass_vs_dctcp(
        inter_byteload_period_us_list,
        num_byteloads_list,
        byteload_size_B_list,
        ssird_fct_s_list_list,
        xpass_fct_s_list_list,
        dctcp_fct_s_list_list,
        num_flows,
        flow_size_B,
        total_gdpt_gbps,
        rtt_s,
        title_addendum
    )

def fe_analyse_ssird_vs_ideal_fct_fullrange_100Bto100KB_40flo_1msRTT():
    title_addendum = "_10flo_500Bto100KB_0pt8GbpsFlo_1msRTT_allproto"

    rtt_s = RTT_1MS_S
    num_flows_per_host_pair = 4
    # num_host_pairs = 5
    # percentile = round((num_flows_per_host_pair * num_host_pairs - 1) / (num_flows_per_host_pair * num_host_pairs) * 100, 1)
    percentile = 100
    flow_size_B = 1000000
    total_gdpt_gbps = -1
    inter_byteload_period_us_list =  [0.5, 1, 5, 10, 50, 100]
    num_byteloads_list = [2000, 1000, 200, 100, 20, 10]
    byteload_size_B_list = [500, 1000, 5000, 10000, 50000, 100000]
    ssird_fct_s_list_list = [[0.001752821000000182, 0.0020028110000005483, 0.0022528310000016205, 0.0025028210000002105, 0.0017528300000009267, 0.002002820000001293, 0.002252840000000589, 0.002502830000000955, 0.001752838999999895, 0.0020028290000002613, 0.0022528490000013335, 0.0025028389999999234, 0.0017528480000006397, 0.002002838000001006, 0.002252858000000302, 0.002502848000000668, 0.001752858000001467, 0.002002848000000057, 0.002252868000001129, 0.0025028580000014955], [0.0017525270000007254, 0.002002547000000021, 0.0022525370000003875, 0.002502527000000754, 0.0017525440000003556, 0.0020025640000014278, 0.0022525540000000177, 0.002502544000000384, 0.0017525609999999858, 0.002002581000001058, 0.0022525710000014243, 0.0025025610000000142, 0.0017525780000013924, 0.002002598000000688, 0.0022525880000010545, 0.002502578000001421, 0.0017525960000011054, 0.002002616000000401, 0.0022526060000007675, 0.002502596000001134], [0.0017499930000006714, 0.0019999830000010377, 0.0022500030000003335, 0.0024999940000007825, 0.0017500180000009635, 0.00200000800000133, 0.0022500280000006256, 0.002500018000000992, 0.0017500430000012557, 0.002000033000001622, 0.002250053000000918, 0.002500043000001284, 0.001750067000001465, 0.002000057000000055, 0.002250077000001127, 0.0025000670000014935, 0.0017500919999999809, 0.002000082000000347, 0.0022501020000014194, 0.0025000920000000093], [0.0017466110000015078, 0.0019966310000008036, 0.00224662100000117, 0.002496612000001619, 0.0017466360000000236, 0.0019966560000010958, 0.002246646000001462, 0.002496636000000052, 0.0017466610000003158, 0.001996681000001388, 0.002246670999999978, 0.002496661000000344, 0.0017466850000005252, 0.0019967050000015973, 0.0022466950000001873, 0.0024966850000005536, 0.0017467100000008173, 0.001996730000000113, 0.0022467200000004794, 0.0024967100000008458], [0.0017202040000015018, 0.0019701940000000917, 0.002220214000001164, 0.00247020400000153, 0.0017202290000000175, 0.001970219000000384, 0.002220239000001456, 0.002470229000000046, 0.0017202540000003097, 0.001970244000000676, 0.002220263999999972, 0.002470254000000338, 0.0017202780000005191, 0.0019702680000008854, 0.0022202880000001812, 0.0024702780000005475, 0.0017203030000008113, 0.0019702930000011776, 0.0022203130000004734, 0.0024703030000008397], [0.00172014400000009, 0.0019370439999999434, 0.0022201540000015285, 0.002437024000000676, 0.0017201680000002995, 0.0019370680000001528, 0.0022201790000000443, 0.002437049000000968, 0.0017201930000005916, 0.001937093000000445, 0.0022202030000002537, 0.0024370730000011775, 0.0017202180000008838, 0.001937118000000737, 0.002220228000000546, 0.0024370980000014697, 0.0017202420000010932, 0.0019371420000009465, 0.0022202520000007553, 0.0024371219999999028]]

    print(f"RTT (us): {rtt_s * pow(10,6)}")
    print(f"Byteload Size (B): {byteload_size_B_list}")
    analyse_fct_slowdown_ssird_vs_ideal(
        inter_byteload_period_us_list,
        num_byteloads_list,
        byteload_size_B_list,
        ssird_fct_s_list_list,
        num_flows_per_host_pair,
        flow_size_B,
        total_gdpt_gbps,
        percentile,
        rtt_s,
        title_addendum
    )

def fe_analyse_ssird_vs_ideal_fct_flowratesweep_10flo_1458B_2000nsTo150ns_10flo_1msRTT():
    title_addendum = "_10flo_1458B_2000nsTo150ns_1msRTT_allproto_test"

    rtt_s = RTT_1MS_S
    num_flows_per_host_pair = 2
    # num_host_pairs = 5
    # percentile = round((num_flows_per_host_pair * num_host_pairs - 1) / (num_flows_per_host_pair * num_host_pairs) * 100, 1)
    percentile = 90
    flow_size_B = -1
    total_gdpt_gbps = -1
    inter_byteload_period_us_list = [2, 1, 0.8, 0.6, 0.4, 0.3, 0.2, 0.15]
    num_byteloads_list = [500]*8
    byteload_size_B_list = [1458]*8
    ssird_fct_s_list_list = [[0.0020014780000003896, 0.0025014880000000517, 0.0020015030000006817, 0.002501513000000344, 0.002001528000000974, 0.002501538000000636, 0.0020015520000011833, 0.0025015620000008454, 0.0020015770000014754, 0.0025015870000011375], [0.0017524780000002238, 0.002002498000001296, 0.001752503000000516, 0.002002523000001588, 0.001752528000000808, 0.002002548000000104, 0.0017525520000010175, 0.0020025720000003133, 0.0017525770000013097, 0.0020025970000006055], [0.0017026780000009012, 0.0019026880000012625, 0.0017027030000011933, 0.0019027130000015546, 0.0017027280000014855, 0.0019027380000000704, 0.0017027519999999186, 0.0019027620000002798, 0.0017027770000002107, 0.001902787000000572], [0.0016528780000015786, 0.001802878000001229, 0.0016529030000000944, 0.0018029030000015211, 0.0016529280000003865, 0.001802928000000037, 0.001652952000000596, 0.0018029520000002464, 0.001652977000000888, 0.0018029770000005385], [0.0016030780000004796, 0.001703098000000125, 0.0016031030000007718, 0.0017031230000004172, 0.001603128000001064, 0.0017031480000007093, 0.0016031520000012733, 0.0017031720000009187, 0.0016031770000015655, 0.0017031970000012109], [0.0015781780000008183, 0.0016531780000015317, 0.0015782030000011105, 0.0016532030000000475, 0.0015782280000014026, 0.0016532280000003396, 0.001578252000001612, 0.001653252000000549, 0.0015782770000001278, 0.0016532770000008412], [0.0015648120000015808, 0.0016263320000007297, 0.0015648370000000966, 0.001626357000001022, 0.001564861000000306, 0.0016263810000012313, 0.0015648860000005982, 0.0016264060000015235, 0.0015649110000008903, 0.0016264310000000393], [0.0015648120000015808, 0.0016263320000007297, 0.0015648370000000966, 0.001626357000001022, 0.001564861000000306, 0.0016263810000012313, 0.0015648860000005982, 0.0016264060000015235, 0.0015649110000008903, 0.0016264310000000393]]

    print(f"RTT (us): {rtt_s * pow(10,6)}")
    print(f"Byteload Size (B): {byteload_size_B_list}")

    # TODO: make new plots with flow rate as x axis
    analyse_fct_slowdown_ssird_vs_ideal_vary_flowrate(
        inter_byteload_period_us_list,
        num_byteloads_list,
        byteload_size_B_list,
        ssird_fct_s_list_list,
        num_flows_per_host_pair,
        flow_size_B,
        total_gdpt_gbps,
        percentile,
        rtt_s,
        title_addendum
    )

def fe_analyse_ssird_vs_ideal_fct_fullrange_500Bto100KB_1msRTT_NEW():

    title_addendum = "_500Bto100KB_8GbpsFlo_1msRTT_allproto"

    rtt_s = RTT_1MS_S
    num_flows_per_host_pair = 1
    percentile = 90
    flow_size_B = 1000000
    total_gdpt_gbps = -1
    inter_byteload_period_us_list =  [0.5, 1, 5, 10, 50, 100]
    num_byteloads_list = [2000, 1000, 200, 100, 20, 10]
    byteload_size_B_list = [500, 1000, 5000, 10000, 50000, 100000]
    ssird_fct_s_list_list = [[0.0024996530000009898, 0.0024996530000009898, 0.0024996530000009898, 0.0024996530000009898, 0.0024996530000009898, 0.0024996530000009898, 0.0024996530000009898, 0.0024996530000009898, 0.0024996530000009898, 0.0024996530000009898], [0.0024992230000009386, 0.0024992230000009386, 0.0024992230000009386, 0.0024992230000009386, 0.0024992230000009386, 0.0024992230000009386, 0.0024992230000009386, 0.0024992230000009386, 0.0024992230000009386, 0.0024992230000009386], [0.002495609000000343, 0.002495609000000343, 0.002495609000000343, 0.002495609000000343, 0.002495609000000343, 0.002495609000000343, 0.002495609000000343, 0.002495609000000343, 0.002495609000000343, 0.002495609000000343], [0.002491018000000622, 0.002491018000000622, 0.002491018000000622, 0.002491018000000622, 0.002491018000000622, 0.002491018000000622, 0.002491018000000622, 0.002491018000000622, 0.002491018000000622, 0.002491018000000622], [0.002454407000000103, 0.002454407000000103, 0.002454407000000103, 0.002454407000000103, 0.002454407000000103, 0.002454407000000103, 0.002454407000000103, 0.002454407000000103, 0.002454407000000103, 0.002454407000000103], [0.002408615000000225, 0.002408615000000225, 0.002408615000000225, 0.002408615000000225, 0.002408615000000225, 0.002408615000000225, 0.002408615000000225, 0.002408615000000225, 0.002408615000000225, 0.002408615000000225]]

    print(f"RTT (us): {rtt_s * pow(10,6)}")
    print(f"Byteload Size (B): {byteload_size_B_list}")

    # NOTE: use exact ideal fct calc method!
    analyse_fct_slowdown_ssird_vs_ideal(
        inter_byteload_period_us_list,
        num_byteloads_list,
        byteload_size_B_list,
        ssird_fct_s_list_list,
        num_flows_per_host_pair,
        flow_size_B,
        total_gdpt_gbps,
        percentile,
        rtt_s,
        title_addendum
    )

def fe_analyse_ssird_vs_ideal_fct_flowratesweep_1458B_2000nsTo150ns_1msRTT_NEW():

    title_addendum = "_1458B_2000nsTo150ns_1msRTT_allproto_test"

    rtt_s = RTT_1MS_S
    num_flows_per_host_pair = 1
    percentile = 90
    flow_size_B = 1458*500
    total_gdpt_gbps = -1
    inter_byteload_period_us_list = [2, 1, 0.8, 0.6, 0.4, 0.3, 0.2, 0.15]
    num_byteloads_list = [500]*8
    byteload_size_B_list = [1458]*8
    ssird_fct_s_list_list = [[0.002498306000001449, 0.002498306000001449, 0.002498306000001449, 0.002498306000001449, 0.002498306000001449, 0.002498306000001449, 0.002498306000001449, 0.002498306000001449, 0.002498306000001449, 0.002498306000001449], [0.001999316000000917, 0.001999316000000917, 0.001999316000000917, 0.001999316000000917, 0.001999316000000917, 0.001999316000000917, 0.001999316000000917, 0.001999316000000917, 0.001999316000000917, 0.001999316000000917], [0.0018995060000008834, 0.0018995060000008834, 0.0018995060000008834, 0.0018995060000008834, 0.0018995060000008834, 0.0018995060000008834, 0.0018995060000008834, 0.0018995060000008834, 0.0018995060000008834, 0.0018995060000008834], [0.00179969600000085, 0.00179969600000085, 0.00179969600000085, 0.00179969600000085, 0.00179969600000085, 0.00179969600000085, 0.00179969600000085, 0.00179969600000085, 0.00179969600000085, 0.00179969600000085], [0.0016999160000015223, 0.0016999160000015223, 0.0016999160000015223, 0.0016999160000015223, 0.0016999160000015223, 0.0016999160000015223, 0.0016999160000015223, 0.0016999160000015223, 0.0016999160000015223, 0.0016999160000015223], [0.0016499960000011527, 0.0016499960000011527, 0.0016499960000011527, 0.0016499960000011527, 0.0016499960000011527, 0.0016499960000011527, 0.0016499960000011527, 0.0016499960000011527, 0.0016499960000011527, 0.0016499960000011527], [0.0016001060000014888, 0.0016001060000014888, 0.0016001060000014888, 0.0016001060000014888, 0.0016001060000014888, 0.0016001060000014888, 0.0016001060000014888, 0.0016001060000014888, 0.0016001060000014888, 0.0016001060000014888], [0.0015751460000004158, 0.0015751460000004158, 0.0015751460000004158, 0.0015751460000004158, 0.0015751460000004158, 0.0015751460000004158, 0.0015751460000004158, 0.0015751460000004158, 0.0015751460000004158, 0.0015751460000004158]]

    print(f"RTT (us): {rtt_s * pow(10,6)}")
    print(f"Byteload Size (B): {byteload_size_B_list}")

    # NOTE: use exact ideal fct calc method!
    analyse_fct_slowdown_ssird_vs_ideal_vary_flowrate(
        inter_byteload_period_us_list,
        num_byteloads_list,
        byteload_size_B_list,
        ssird_fct_s_list_list,
        num_flows_per_host_pair,
        flow_size_B,
        total_gdpt_gbps,
        percentile,
        rtt_s,
        title_addendum
    )

if __name__ == "__main__":

    pass
    # fe_analyse_ssird_vs_ideal_fct_fullrange_100Bto1MB_6flo_5usRTT()
    # print("=====")
    # fe_analyse_ssird_vs_ideal_fct_fullrange_100Bto100KB_40flo_5usRTT()

    # fe_analyse_ssird_xpass_vs_dctcp_fct_fullrange_100Bto100KB_40flo_5usRTT()
    # fe_analyse_ssird_vs_ideal_fct_fullrange_100Bto100KB_40flo_1msRTT()
    # fe_analyse_ssird_vs_ideal_fct_flowratesweep_10flo_1458B_2000nsTo150ns_10flo_1msRTT()

    fe_analyse_ssird_vs_ideal_fct_fullrange_500Bto100KB_1msRTT_NEW()
    fe_analyse_ssird_vs_ideal_fct_flowratesweep_1458B_2000nsTo150ns_1msRTT_NEW()