import matplotlib.pyplot as plt

SSIRD_PLOT_COLOUR = 'tab:blue'
IDEAL_PLOT_COLOUR = 'tab:orange'

LINK_SPEED_GBPS = 100 # 100 GBps link speed

def plot_ssird_vs_ideal_fct_compare(inter_byteload_period_us_list, ssird_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=False, is_log_y=False, title_addendum=""):
    ssird_fct_ms = [t * 1000 for t in ssird_fct]
    ideal_fct_ms = [t * 1000 for t in ideal_fct]
    plt.figure(figsize=(10, 6))
    plt.plot(inter_byteload_period_us_list, ssird_fct_ms, label="SSIRD", linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.plot(inter_byteload_period_us_list, ideal_fct_ms, label="Ideal", linestyle='-', marker='o', color=IDEAL_PLOT_COLOUR)
    plt.xlabel('Inter-byteload Period (us)')
    plt.ylabel('Flow Completion Time (ms)')
    plt.title(f"SSIRD vs Ideal: FCT vs Inter-byteload period ({num_byteloads} x {byteload_size_B} Bytes) {title_addendum}")
    plt.legend()
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log')
    filename = f"ssird_vs_ideal_fct_{byteload_size_B}B_vary_period{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_fct_sweep_compare(load_gbps, ssird_fct, ideal_fct, num_byteloads, inter_byteload_period_us, title_addendum=""):
    ssird_fct_ms = [t * 1000 for t in ssird_fct]
    ideal_fct_ms = [t * 1000 for t in ideal_fct]
    load_percent = [(l / LINK_SPEED_GBPS) * 100 for l in load_gbps]
    plt.figure(figsize=(10, 6))
    plt.plot(load_percent, ssird_fct_ms, label="SSIRD", linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.plot(load_percent, ideal_fct_ms, label="Ideal", linestyle='-', marker='o', color=IDEAL_PLOT_COLOUR)
    plt.xlabel('Load (Percent of Max Link Speed)')
    plt.ylabel('Flow Completion Time (ms)')
    plt.title(f"SSIRD vs Ideal: FCT vs Load Sweep ({num_byteloads} x {inter_byteload_period_us/1000}ms) {title_addendum}")
    plt.legend()
    plt.grid(True)
    filename = f"ssird_vs_ideal_fct_sweep_1gbps_100gbps{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_fct_diff(inter_byteload_period_us_list, ssird_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=False, is_log_y=False, title_addendum=""):
    fct_ssird_minus_ideal_us = [(ssird - ideal) * 1000000 for ssird, ideal in zip(ssird_fct, ideal_fct)]
    plt.figure(figsize=(10, 6))
    plt.plot(inter_byteload_period_us_list, fct_ssird_minus_ideal_us, linestyle='-', marker='o')
    plt.xlabel('Inter-byteload Period')
    plt.ylabel('FCT SSIRD - Ideal (us)')
    plt.title(f"FCT Difference (SSIRD - Ideal) vs Inter-byteload period ({num_byteloads} x {byteload_size_B} Bytes) {title_addendum}")
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log')
    filename = f"ssird_vs_ideal_fct_{byteload_size_B}B_vary_period_DIFF{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_fct_sweep_diff(load_gbps, ssird_fct, ideal_fct, num_byteloads, inter_byteload_period_us, title_addendum=""):
    fct_ssird_minus_ideal_us = [(ssird - ideal) * 1000000 for ssird, ideal in zip(ssird_fct, ideal_fct)]
    load_percent = [(l / LINK_SPEED_GBPS) * 100 for l in load_gbps]
    plt.figure(figsize=(10, 6))
    plt.plot(load_percent, fct_ssird_minus_ideal_us, linestyle='-', marker='o')
    plt.xlabel('Load (Percent of Max Link Speed)')
    plt.ylabel('FCT SSIRD - Ideal (us)')
    plt.title(f"FCT Difference (SSIRD - Ideal) vs Load Sweep ({num_byteloads} x {inter_byteload_period_us/1000}ms) {title_addendum}")
    plt.grid(True)
    filename = f"ssird_vs_ideal_fct_sweep_1gbps_100gbps_DIFF{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_fct_slowdown_vs_ideal(inter_byteload_period_us_list, ssird_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=False, is_log_y=False, title_addendum=""):
    ssird_slowdown = [ssird/ideal for ssird, ideal in zip(ssird_fct, ideal_fct)] 

    plt.figure(figsize=(10, 6))
    plt.plot(inter_byteload_period_us_list, ssird_slowdown, label='SSIRD', linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.xlabel('Inter-byteload Period (us)')
    plt.ylabel('Slowdown vs Ideal FCT')
    plt.title(f"SSIRD: FCT Slowdown vs Inter-byteload period ({num_byteloads} x {byteload_size_B} Bytes) {title_addendum}")
    plt.legend()
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log')
    filename = f"ssird_vs_ideal_fct_slowdown_{byteload_size_B}B_vary_period{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_fct_sweep_slowdown_vs_ideal(load_gbps, ssird_fct, ideal_fct, num_byteloads, inter_byteload_period_us, title_addendum=""):
    ssird_slowdown = [ssird/ideal for ssird, ideal in zip(ssird_fct, ideal_fct)] 

    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps, ssird_slowdown, label='SSIRD', linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.xlabel('Load (Percent of Max Link Speed)')
    plt.ylabel('Slowdown vs Ideal FCT')
    plt.title(f"SSIRD: FCT Slowdown vs Load Sweep ({num_byteloads} x {inter_byteload_period_us/1000}ms) {title_addendum}")
    plt.legend()
    plt.grid(True)
    filename = f"ssird_vs_ideal_fct_slowdown_sweep_1gbps_100gbps{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_fct_1000000B_varying_period():
    # INFO:__main__:SSIRD FCT: 0.020092063999999965 ms, Load: 0.19999999999999243 Gbps
    # INFO:__main__:Time Periods: [10, 50, 100, 500, 1000, 5000]
    # INFO:__main__:Num Byteloads: 5
    # INFO:__main__:Byteload Size: 1000000 Bytes
    # INFO:__main__:Sim duration (SSIRD): [0.0005, 0.0005, 0.001, 0.0025, 0.005, 0.024999999999999998]
    # INFO:__main__:Sim duration (DCTCP): [0.0005, 0.0005, 0.001, 0.0025, 0.005, 0.024999999999999998]
    # INFO:__main__:* IDEAL FCT: [5e-05, 0.00025, 0.0005, 0.0025, 0.005, 0.025]
    # INFO:__main__:* SSIRD FCT: [0.00042970199999992076, 0.00042970199999992076, 0.0004920730000002038, 0.0020920630000009766, 0.004092074000000778, 0.020092063999999965]
    # INFO:__main__:* DCTCP FCT: [-1, -1, -1, -1, -1, -1]
    num_byteloads = 5
    byteload_size_B = 1000000
    inter_byteload_period_us_list = [10, 50, 100, 500, 1000, 5000]
    ideal_fct = [5e-05, 0.00025, 0.0005, 0.0025, 0.005, 0.025]
    ideal_fct_old = [5e-05, 0.00020999999999999998, 0.00041, 0.00201, 0.00401, 0.02001] 
    ssird_fct = [0.00042970199999992076, 0.00042970199999992076, 0.0004920730000002038, 0.0020920630000009766, 0.004092074000000778, 0.020092063999999965]
    plot_ssird_vs_ideal_fct_compare(inter_byteload_period_us_list, ssird_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=True)
    plot_ssird_vs_ideal_fct_compare(inter_byteload_period_us_list, ssird_fct, ideal_fct_old, num_byteloads, byteload_size_B, is_log_x=True, title_addendum="_old")
    
    plot_ssird_vs_ideal_fct_slowdown_vs_ideal(inter_byteload_period_us_list, ssird_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=True)
    plot_ssird_vs_ideal_fct_slowdown_vs_ideal(inter_byteload_period_us_list, ssird_fct, ideal_fct_old, num_byteloads, byteload_size_B, is_log_x=True, title_addendum="_old")

    plot_ssird_vs_ideal_fct_diff(inter_byteload_period_us_list, ssird_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=True)
    plot_ssird_vs_ideal_fct_diff(inter_byteload_period_us_list, ssird_fct, ideal_fct_old, num_byteloads, byteload_size_B, is_log_x=True, title_addendum="_old")
    
def plot_ssird_vs_ideal_fct_sweep_1gbps_100gbps():
    # INFO:__main__:Time Period: 100
    # INFO:__main__:Num Byteloads: 10
    # INFO:__main__:Byteload Size (Bytes): [100000, 500000, 1000000, 5000000, 10000000]
    # INFO:__main__:Load GBps theoretical: [1.0000000000000002, 5.000000000000001, 10.000000000000002, 50.00000000000001, 100.00000000000001]
    # INFO:__main__:Load GBps measured: [1.0000000000001101, 5.000000000000551, 10.000000000001101, 50.000000000005514, 100.00000000001103]
    # INFO:__main__:Sim duration (SSIRD): [0.002, 0.002, 0.002, 0.006, 0.01]
    # INFO:__main__:Sim duration (DCTCP): [0.002, 0.002, 0.002, 0.006, 0.01]
    # INFO:__main__:* IDEAL FCT: [0.0009999999999999998, 0.001, 0.001, 0.0009999999999999998, 0.001]
    # INFO:__main__:* SSIRD FCT: [0.0009161049999999449, 0.0009498580000002477, 0.0009920530000009364, 0.004227265000000813, 0.008446747000000698]
    # INFO:__main__:* DCTCP FCT: [-1, -1, -1, -1, -1]
    inter_byteload_period_us = 100
    num_byteloads = 10
    load_gbps = [1.0, 5.0, 10.0, 50.0, 100.0]
    ideal_fct = [0.0009999999999999998, 0.001, 0.001, 0.0009999999999999998, 0.001]
    ideal_fct_old = [0.000901, 0.000905, 0.00091, 0.00095, 0.001]
    ssird_fct = [0.0009161049999999449, 0.0009498580000002477, 0.0009920530000009364, 0.004227265000000813, 0.008446747000000698]
    plot_ssird_vs_ideal_fct_sweep_compare(load_gbps, ssird_fct, ideal_fct, num_byteloads, inter_byteload_period_us)
    plot_ssird_vs_ideal_fct_sweep_compare(load_gbps, ssird_fct, ideal_fct, num_byteloads, inter_byteload_period_us, title_addendum="_old")

    plot_ssird_fct_sweep_slowdown_vs_ideal(load_gbps, ssird_fct, ideal_fct, num_byteloads, inter_byteload_period_us)
    plot_ssird_fct_sweep_slowdown_vs_ideal(load_gbps, ssird_fct, ideal_fct_old, num_byteloads, inter_byteload_period_us, title_addendum="_old")

    plot_ssird_vs_ideal_fct_sweep_diff(load_gbps, ssird_fct, ideal_fct, num_byteloads, inter_byteload_period_us)
    plot_ssird_vs_ideal_fct_sweep_diff(load_gbps, ssird_fct, ideal_fct_old, num_byteloads, inter_byteload_period_us, title_addendum="_old")

if __name__ == "__main__":
    plot_ssird_vs_ideal_fct_1000000B_varying_period()
    plot_ssird_vs_ideal_fct_sweep_1gbps_100gbps()
