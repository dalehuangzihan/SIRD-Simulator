import matplotlib.pyplot as plt

def plot_ssird_dctcp_fct_compare(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B):
    ssird_fct_ms = [t * 1000 for t in ssird_fct]
    dctcp_fct_ms = [t * 1000 for t in dctcp_fct]
    plt.figure(figsize=(10, 6))
    plt.plot(inter_byteload_period_us_list, ssird_fct_ms, label="SSIRD", linestyle='-', marker='o')
    plt.plot(inter_byteload_period_us_list, dctcp_fct_ms, label="DCTCP", linestyle='-', marker='o')
    plt.xlabel('Inter-byteload Period (us)')
    plt.ylabel('Flow Completion Time (ms)')
    plt.title(f"SSIRD vs DCTCP: FCT vs Inter-byteload period ({num_byteloads} x {byteload_size_B} Bytes)")
    plt.legend()
    plt.grid(True)
    filename = f"ssird_dctcp_fct_{byteload_size_B}B.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_dctcp_fct_sweep_compare(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us):
    ssird_fct_ms = [t * 1000 for t in ssird_fct]
    dctcp_fct_ms = [t * 1000 for t in dctcp_fct]
    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps, ssird_fct_ms, label="SSIRD", linestyle='-', marker='o')
    plt.plot(load_gbps, dctcp_fct_ms, label="DCTCP", linestyle='-', marker='o')
    plt.xlabel('Load (GBps)')
    plt.ylabel('Flow Completion Time (ms)')
    plt.title(f"SSIRD vs DCTCP: FCT vs Load Sweep ({num_byteloads} x {inter_byteload_period_us/1000}ms)")
    plt.legend()
    plt.grid(True)
    filename = f"ssird_dctcp_fct_sweep_1gbps_100gbps.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_dctcp_fct_sweep_diff(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us):
    fct_ssird_minus_dctcp_us = [(ssird - dctcp) * 1000000 for ssird, dctcp in zip(ssird_fct, dctcp_fct)]
    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps, fct_ssird_minus_dctcp_us, linestyle='-', marker='o')
    plt.xlabel('Load (GBps)')
    plt.ylabel('FCT SSIRD - DCTCP (us)')
    plt.title(f"FCT Difference (SSIRD - DCTCP) vs Load Sweep ({num_byteloads} x {inter_byteload_period_us/1000}ms)")
    plt.grid(True)
    filename = f"ssird_dctcp_fct_sweep_1gbps_100gbps_diff.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_dctcp_fct_diff(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B):
    fct_ssird_minus_dctcp_us = [(ssird - dctcp) * 1000000 for ssird, dctcp in zip(ssird_fct, dctcp_fct)]
    plt.figure(figsize=(10, 6))
    plt.plot(inter_byteload_period_us_list, fct_ssird_minus_dctcp_us, linestyle='-', marker='o')
    plt.xlabel('Inter-byteload Period')
    plt.ylabel('FCT SSIRD - DCTCP (ms)')
    plt.title(f"FCT Difference (SSIRD - DCTCP) vs Inter-byteload period ({num_byteloads} x {byteload_size_B} Bytes)")
    plt.grid(True)
    filename = f"ssird_dctcp_fct_diff_{byteload_size_B}B.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_dctcp_fct_slowdown_vs_ideal(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=False, is_log_y=False):
    ssird_slowdown_percent = [((ssird-ideal)/ideal) * 100 for ssird, ideal in zip(ssird_fct, ideal_fct)] 
    dctcp_slowdown_percent = [((dctcp-ideal)/ideal) * 100 for dctcp, ideal in zip(dctcp_fct, ideal_fct)] 
    plt.figure(figsize=(10, 6))
    plt.plot(inter_byteload_period_us_list, ssird_slowdown_percent, label='SSIRD', linestyle='-', marker='o')
    plt.plot(inter_byteload_period_us_list, dctcp_slowdown_percent, label='DCTCP', linestyle='-', marker='o')
    plt.xlabel('Inter-byteload Period (us)')
    plt.ylabel('Slowdown vs Ideal (%)')
    plt.title(f"SSIRD: FCT Slowdown vs Inter-byteload period ({num_byteloads} x {byteload_size_B} Bytes)")
    plt.legend()
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log()')
    filename = f"ssird_dctcp_fct_slowdown_{byteload_size_B}B.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_dctcp_fct_sweep_slowdown_vs_ideal(load_gbps, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, inter_byteload_period_us):
    ssird_slowdown_percent = [((ssird-ideal)/ideal) * 100 for ssird, ideal in zip(ssird_fct, ideal_fct)] 
    dctcp_slowdown_percent = [((dctcp-ideal)/ideal) * 100 for dctcp, ideal in zip(dctcp_fct, ideal_fct)] 
    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps, ssird_slowdown_percent, label='SSIRD', linestyle='-', marker='o')
    plt.plot(load_gbps, dctcp_slowdown_percent, label='DCTCP', linestyle='-', marker='o')
    plt.xlabel('Load (GBps)')
    plt.ylabel('Slowdown vs Ideal (%)')
    plt.title(f"SSIRD: FCT Slowdown vs Load Sweep ({num_byteloads} x {inter_byteload_period_us/1000}ms)")
    plt.legend()
    plt.grid(True)
    filename = f"ssird_dctcp_fct_slowdown_sweep_1gbps_100gbps.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

# def plot_ssird_dctcp_fct_1000B():
#     num_byteloads = 4
#     byteload_size_B = 1000
#     inter_byteload_period_us_list = [100, 500, 1000, 5000, 10000]
#     ssird_fct = [0.0006107130000003735, 0.0030107130000001092, 0.006010713000000223, 0.030010714000001215, 0.060010714000000576]
#     dctcp_fct = [0.0006056720000007232, 0.003005672000000459, 0.0060056720000005726, 0.030005672000001482, 0.06000567200000084]
#     plot_ssird_dctcp_fct_compare(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B)

def plot_ssird_dctcp_fct_100000B():
    # INFO:__main__:Time Periods: [1, 10, 100, 500, 1000, 5000, 10000]
    # INFO:__main__:Num Byteloads: 8
    # INFO:__main__:Byteload Size: 100000 Bytes
    # INFO:__main__:Sim duration (SSIRD): [1.6e-05, 0.00015999999999999999, 0.0015999999999999999, 0.008, 0.016, 0.08, 0.16]
    # INFO:__main__:Sim duration (DCTCP): [1.6e-05, 0.00015999999999999999, 0.0015999999999999999, 0.008, 0.016, 0.08, 0.16]
    # INFO:__main__:* IDEAL FCT: [8e-06, 7.099999999999999e-05, 0.0007009999999999999, 0.003501, 0.007001, 0.035001000000000004, 0.07000100000000001]
    # INFO:__main__:* SSIRD FCT: [4.993200000136255e-05, 0.0001709170000001592, 0.0015209170000005656, 0.007520917000000793, 0.015020917000001077, 0.07502091799999988, 0.1500209200000011]
    # INFO:__main__:* DCTCP FCT: [6.534500000121568e-05, 0.00016605400000102577, 0.0015160540000014322, 0.007516053999999883, 0.015016054000000167, 0.07501605400000066, 0.15001605399999995]
    num_byteloads = 8
    byteload_size_B = 100000
    inter_byteload_period_us_list = [1, 10, 100, 500, 1000, 5000, 10000]
    ideal_fct = [8e-06, 7.099999999999999e-05, 0.0007009999999999999, 0.003501, 0.007001, 0.035001000000000004, 0.07000100000000001]
    ssird_fct = [4.993200000136255e-05, 0.0001709170000001592, 0.0015209170000005656, 0.007520917000000793, 0.015020917000001077, 0.07502091799999988, 0.1500209200000011]
    dctcp_fct = [6.534500000121568e-05, 0.00016605400000102577, 0.0015160540000014322, 0.007516053999999883, 0.015016054000000167, 0.07501605400000066, 0.15001605399999995]
    plot_ssird_dctcp_fct_compare(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B)
    plot_ssird_dctcp_fct_slowdown_vs_ideal(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=True)
    plot_ssird_dctcp_fct_diff(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B)
    

def plot_ssird_dctcp_fct_sweep_1gbps_100gbps():
    # INFO:__main__:Load GBps: [1.0000000000000002, 5.000000000000001, 10.000000000000002, 50.00000000000001, 100.00000000000001]
    # INFO:__main__:Sim duration (SSIRD): [0.015, 0.015, 0.015, 0.015, 0.015]
    # INFO:__main__:Sim duration (DCTCP): [0.015, 0.015, 0.015, 0.015, 0.015]
    # INFO:__main__:* IDEAL FCT: [0.000901, 0.000905, 0.00091, 0.00095, 0.001]
    # INFO:__main__:* SSIRD FCT: [0.004524661000001373, 0.004558858000001109, 0.00460094600000005, 0.004938566999999949, 0.008446747000000698]
    # INFO:__main__:* DCTCP FCT: [0.004520054000000329, 0.004553763000000544, 0.004595897000001514, 0.004932995000000773, 0.008476345000000052]
    inter_byteload_period_us = 1000
    num_byteloads = 10
    load_gbps = [1.0, 5.0, 10.0, 50.0, 100.0]
    ideal_fct = [0.000901, 0.000905, 0.00091, 0.00095, 0.001]
    ssird_fct = [0.004524661000001373, 0.004558858000001109, 0.00460094600000005, 0.004938566999999949, 0.008446747000000698]
    dctcp_fct = [0.004520054000000329, 0.004553763000000544, 0.004595897000001514, 0.004932995000000773, 0.008476345000000052]
    # plot_ssird_dctcp_fct_sweep_compare(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us)
    plot_ssird_dctcp_fct_sweep_slowdown_vs_ideal(load_gbps, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, inter_byteload_period_us)
    plot_ssird_dctcp_fct_sweep_diff(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us)

if __name__ == "__main__":
    # plot_ssird_dctcp_fct_1000B()
    # plot_ssird_dctcp_fct_100000B()
    plot_ssird_dctcp_fct_100000B()
    plot_ssird_dctcp_fct_sweep_1gbps_100gbps()