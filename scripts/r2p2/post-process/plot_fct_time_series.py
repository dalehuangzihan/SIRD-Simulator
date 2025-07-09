import matplotlib.pyplot as plt

SSIRD_PLOT_COLOUR = 'tab:orange'
DCTCP_PLOT_COLOR  = 'tab:green'
IDEAL_PLOT_COLOUR = 'tab:blue'

LINK_SPEED_GBPS = 100 # 100 GBps link speed

def plot_ssird_vs_ideal_fct_compare(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=False, is_log_y=False, title_addendum=""):
    ssird_fct_ms = [t * 1000 for t in ssird_fct]
    dctcp_fct_ms = [t * 1000 for t in dctcp_fct]
    ideal_fct_ms = [t * 1000 for t in ideal_fct]
    plt.figure(figsize=(10, 6))
    plt.plot(inter_byteload_period_us_list, ssird_fct_ms, label="SSIRD", linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    # plt.plot(inter_byteload_period_us_list, dctcp_fct_ms, label="DCTCP", linestyle='-', marker='o', color=DCTCP_PLOT_COLOR)
    plt.plot(inter_byteload_period_us_list, ideal_fct_ms, label="Ideal", linestyle='-', marker='o', color=IDEAL_PLOT_COLOUR)
    plt.xlabel('Inter-byteload Period (us)')
    plt.ylabel('Flow Completion Time (ms)')
    plt.title(f"SSIRD vs Ideal: FCT vs Inter-byteload period ({num_byteloads} byteloads x {byteload_size_B} Bytes) {title_addendum}")
    plt.legend()
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log')
    filename = f"ssird_vs_ideal_fct_{byteload_size_B}B_vary_period{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_fct_sweep_compare(load_gbps, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, inter_byteload_period_us, title_addendum=""):
    ssird_fct_ms = [t * 1000 for t in ssird_fct]
    dctcp_fct_ms = [t * 1000 for t in dctcp_fct]
    ideal_fct_ms = [t * 1000 for t in ideal_fct]
    load_percent = [(l / LINK_SPEED_GBPS) * 100 for l in load_gbps]
    plt.figure(figsize=(10, 6))
    plt.plot(load_percent, ssird_fct_ms, label="SSIRD", linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    # plt.plot(load_percent, dctcp_fct_ms, label="DCTCP", linestyle='-', marker='o', color=DCTCP_PLOT_COLOR)
    plt.plot(load_percent, ideal_fct_ms, label="Ideal", linestyle='-', marker='o', color=IDEAL_PLOT_COLOUR)
    plt.xlabel('Load (Percent of Max Link Capacity)')
    plt.ylabel('Flow Completion Time (ms)')
    plt.title(f"SSIRD vs Ideal: FCT vs Load Sweep ({num_byteloads} x {inter_byteload_period_us/1000}ms) {title_addendum}")
    plt.legend()
    plt.grid(True)
    filename = f"ssird_vs_ideal_fct_sweep_1gbps_100gbps{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_fct_diff(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=False, is_log_y=False, title_addendum=""):
    fct_ssird_minus_ideal_us = [(ssird - ideal) * 1000000 for ssird, ideal in zip(ssird_fct, ideal_fct)]
    fct_dctcp_minus_ideal_us = [(dctcp - ideal) * 1000000 for dctcp, ideal in zip(dctcp_fct, ideal_fct)]
    plt.figure(figsize=(10, 6))
    plt.plot(inter_byteload_period_us_list, fct_ssird_minus_ideal_us, linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR, label='SSIRD')
    # plt.plot(inter_byteload_period_us_list, fct_dctcp_minus_ideal_us, linestyle='-', marker='o', color=DCTCP_PLOT_COLOR, label='DCTCP')
    plt.xlabel('Inter-byteload Period')
    plt.ylabel('FCT SSIRD - Ideal (us)')
    plt.title(f"FCT Difference (SSIRD - Ideal) vs Inter-byteload period ({num_byteloads} byteloads x {byteload_size_B} Bytes) {title_addendum}")
    plt.legend()
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log')
    filename = f"ssird_vs_ideal_fct_{byteload_size_B}B_vary_period_DIFF{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_fct_sweep_diff(load_gbps, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, inter_byteload_period_us, title_addendum=""):
    fct_ssird_minus_ideal_us = [(ssird - ideal) * 1000000 for ssird, ideal in zip(ssird_fct, ideal_fct)]
    fct_dctcp_minus_ideal_us = [(dctcp - ideal) * 1000000 for dctcp, ideal in zip(dctcp_fct, ideal_fct)]
    load_percent = [(l / LINK_SPEED_GBPS) * 100 for l in load_gbps]
    plt.figure(figsize=(10, 6))
    plt.plot(load_percent, fct_ssird_minus_ideal_us, label='SSIRD', linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    # plt.plot(load_percent, fct_dctcp_minus_ideal_us, label='DCTCP', linestyle='-', marker='o', color=DCTCP_PLOT_COLOR)
    plt.xlabel('Load (Percent of Max Link Capacity)')
    plt.ylabel('FCT SSIRD - Ideal (us)')
    plt.title(f"FCT Difference (SSIRD - Ideal) vs Load Sweep ({num_byteloads} byteloads x {inter_byteload_period_us/1000}ms) {title_addendum}")
    plt.legend()
    plt.grid(True)
    filename = f"ssird_vs_ideal_fct_sweep_1gbps_100gbps_DIFF{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_fct_slowdown_vs_ideal(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=False, is_log_y=False, title_addendum=""):
    ssird_slowdown = [ssird/ideal for ssird, ideal in zip(ssird_fct, ideal_fct)] 
    dctcp_slowdown = [dctcp/ideal for dctcp, ideal in zip(dctcp_fct, ideal_fct)]

    plt.figure(figsize=(10, 6))
    plt.plot(inter_byteload_period_us_list, ssird_slowdown, label='SSIRD', linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    # plt.plot(inter_byteload_period_us_list, dctcp_slowdown, label='DCTCP', linestyle='-', marker='o', color=DCTCP_PLOT_COLOR)
    plt.xlabel('Inter-byteload Period (us)')
    plt.ylabel('Slowdown vs Ideal FCT')
    plt.title(f"SSIRD: FCT Slowdown vs Inter-byteload period ({num_byteloads} byteloads x {byteload_size_B} Bytes) {title_addendum}")
    plt.legend()
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log')
    filename = f"ssird_vs_ideal_fct_slowdown_{byteload_size_B}B_vary_period{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_fct_sweep_slowdown_vs_ideal(load_gbps, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, inter_byteload_period_us, title_addendum=""):
    ssird_slowdown = [ssird/ideal for ssird, ideal in zip(ssird_fct, ideal_fct)] 
    dctcp_slowdown = [dctcp/ideal for dctcp, ideal in zip(dctcp_fct, ideal_fct)]

    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps, ssird_slowdown, label='SSIRD', linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    # plt.plot(load_gbps, dctcp_slowdown, label='DCTCP', linestyle='-', marker='o', color=DCTCP_PLOT_COLOR)
    plt.xlabel('Load (Percent of Max Link Capacity)')
    plt.ylabel('Slowdown vs Ideal FCT')
    plt.title(f"SSIRD: FCT Slowdown vs Load Sweep ({num_byteloads} byteloads x {inter_byteload_period_us/1000}ms) {title_addendum}")
    plt.legend()
    plt.grid(True)
    filename = f"ssird_vs_ideal_fct_slowdown_sweep_1gbps_100gbps{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_fct_1000000B_varying_period():
    # INFO:__main__:Time Periods: [10, 50, 100, 500, 1000, 5000]
    # INFO:__main__:Num Byteloads: 5
    # INFO:__main__:Byteload Size: 125000.0 Bytes
    # INFO:__main__:Sim duration (SSIRD): [0.0005, 0.0005, 0.001, 0.0025, 0.005, 0.024999999999999998]
    # INFO:__main__:Sim duration (DCTCP): [0.0005, 0.0005, 0.001, 0.0025, 0.005, 0.024999999999999998]
    # INFO:__main__:Load Measured (Gbps): [99.99999999786458, 19.999999999809766, 9.999999999964094, 1.9999999999999243, 0.9999999999999621, 0.19999999999999243]
    # INFO:__main__:* IDEAL FCT: [4.9999999999999996e-05, 0.00025, 0.0005, 0.0025, 0.005, 0.025]
    # INFO:__main__:* IDEAL FCT (old): [4.125e-05, 0.00020124999999999999, 0.00040124999999999997, 0.00200125, 0.0040012500000000005, 0.02000125]
    # INFO:__main__:* SSIRD FCT: [6.049600000146427e-05, 0.00021822300000096106, 0.00041823300000132235, 0.0020182230000003187, 0.00401823400000012, 0.020018224000001084]
    # INFO:__main__:* DCTCP FCT: [7.587600000036332e-05, 0.00021316000000126678, 0.00041316000000080066, 0.0020131600000006244, 0.004013160000001292, 0.020013160000001307]

    num_byteloads = 5
    byteload_size_B = 125000  # 1000000/8 Bytes
    inter_byteload_period_us_list = [10, 50, 100, 500, 1000, 5000]
    ideal_fct = [4.9999999999999996e-05, 0.00025, 0.0005, 0.0025, 0.005, 0.025]
    ideal_fct_old = [4.125e-05, 0.00020124999999999999, 0.00040124999999999997, 0.00200125, 0.0040012500000000005, 0.02000125] 
    ssird_fct = [6.049600000146427e-05, 0.00021822300000096106, 0.00041823300000132235, 0.0020182230000003187, 0.00401823400000012, 0.020018224000001084]
    dctcp_fct = [7.587600000036332e-05, 0.00021316000000126678, 0.00041316000000080066, 0.0020131600000006244, 0.004013160000001292, 0.020013160000001307] 
    plot_ssird_vs_ideal_fct_compare(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=True)
    plot_ssird_vs_ideal_fct_compare(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct_old, num_byteloads, byteload_size_B, is_log_x=True, title_addendum="_exact")
    
    plot_ssird_vs_ideal_fct_slowdown_vs_ideal(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=True)
    plot_ssird_vs_ideal_fct_slowdown_vs_ideal(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct_old, num_byteloads, byteload_size_B, is_log_x=True, title_addendum="_exact")

    plot_ssird_vs_ideal_fct_diff(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=True)
    plot_ssird_vs_ideal_fct_diff(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct_old, num_byteloads, byteload_size_B, is_log_x=True, title_addendum="_exact")
    
def plot_ssird_vs_ideal_fct_sweep_1gbps_100gbps():
    # INFO:__main__:Time Period: 100
    # INFO:__main__:Num Byteloads: 10
    # INFO:__main__:Byteload Size (Bytes): [12500, 62500, 125000, 625000, 1250000]
    # INFO:__main__:Load Gbps theoretical: [1.0000000000000002, 5.000000000000001, 10.000000000000002, 50.00000000000001, 100.00000000000001]
    # INFO:__main__:Load Gbps measured: [1.0000000000001101, 5.000000000000551, 10.000000000001101, 50.000000000005514, 100.00000000001103]
    # INFO:__main__:Sim duration (SSIRD): [0.002, 0.002, 0.002, 0.006, 0.01]
    # INFO:__main__:Sim duration (DCTCP): [0.002, 0.002, 0.002, 0.006, 0.01]
    # INFO:__main__:* IDEAL FCT: [0.0009999999999999998, 0.001, 0.001, 0.0009999999999999998, 0.0009999999999999998]
    # INFO:__main__:* IDEAL FCT (old): [0.000900125, 0.000900625, 0.0009012499999999999, 0.0009062499999999999, 0.0009125]
    # INFO:__main__:* SSIRD FCT: [0.0009087210000000567, 0.0009129380000008069, 0.0009182130000002786, 0.0009604090000010501, 0.0010626570000003]
    # INFO:__main__:* DCTCP FCT: [0.0009036790000003236, 0.0009078910000006601, 0.0009131600000014117, 0.0009553000000011025, 0.0011023810000008183]

    inter_byteload_period_us = 100
    num_byteloads = 10
    load_gbps = [1.0, 5.0, 10.0, 50.0, 100.0]
    ideal_fct = [0.0009999999999999998, 0.001, 0.001, 0.0009999999999999998, 0.001]
    ideal_fct_old = [0.000900125, 0.000900625, 0.0009012499999999999, 0.0009062499999999999, 0.0009125]
    ssird_fct = [0.0009087210000000567, 0.0009129380000008069, 0.0009182130000002786, 0.0009604090000010501, 0.0010626570000003]
    dctcp_fct = [0.0009036790000003236, 0.0009078910000006601, 0.0009131600000014117, 0.0009553000000011025, 0.0011023810000008183]
    plot_ssird_vs_ideal_fct_sweep_compare(load_gbps, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, inter_byteload_period_us)
    plot_ssird_vs_ideal_fct_sweep_compare(load_gbps, ssird_fct, dctcp_fct, ideal_fct_old, num_byteloads, inter_byteload_period_us, title_addendum="_exact")

    plot_ssird_fct_sweep_slowdown_vs_ideal(load_gbps, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, inter_byteload_period_us)
    plot_ssird_fct_sweep_slowdown_vs_ideal(load_gbps, ssird_fct, dctcp_fct, ideal_fct_old, num_byteloads, inter_byteload_period_us, title_addendum="_exact")

    plot_ssird_vs_ideal_fct_sweep_diff(load_gbps, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, inter_byteload_period_us)
    plot_ssird_vs_ideal_fct_sweep_diff(load_gbps, ssird_fct, dctcp_fct, ideal_fct_old, num_byteloads, inter_byteload_period_us, title_addendum="_exact")

if __name__ == "__main__":
    plot_ssird_vs_ideal_fct_1000000B_varying_period()
    plot_ssird_vs_ideal_fct_sweep_1gbps_100gbps()
