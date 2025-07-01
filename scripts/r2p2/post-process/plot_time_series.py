import matplotlib.pyplot as plt

def plot_ssird_dctcp_fct_compare(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B):
    plt.figure(figsize=(10, 6))
    plt.plot(inter_byteload_period_us_list, ssird_fct, label="SSIRD", linestyle='-', marker='o')
    plt.plot(inter_byteload_period_us_list, dctcp_fct, label="DCTCP", linestyle='-', marker='o')

    plt.xlabel('Inter-byteload Period (us)')
    plt.ylabel('Flow Completion Time (s)')
    plt.title(f"SSIRD vs DCTCP: FCT vs Inter-byteload period ({num_byteloads} x {byteload_size_B} Bytes)")
    plt.legend()
    plt.grid(True)

    # plt.yscale('log')

    filename = f"ssird_dctcp_fct_{byteload_size_B}B.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_dctcp_fct_diff(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B):
    fct_ssird_minus_dctcp_us = [(ssird - dctcp) * 1000 for ssird, dctcp in zip(ssird_fct, dctcp_fct)]

    plt.figure(figsize=(10, 6))
    plt.plot(inter_byteload_period_us_list, fct_ssird_minus_dctcp_us, linestyle='-', marker='o')

    plt.xlabel('Inter-byteload Period')
    plt.ylabel('FCT SSIRD - DCTCP (ms)')
    plt.title(f"FCT Difference (SSIRD - DCTCP) vs Inter-byteload period ({num_byteloads} x {byteload_size_B} Bytes)")
    plt.grid(True)
    # plt.yscale('log')

    filename = f"ssird_dctcp_fct_diff_{byteload_size_B}B.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_dctcp_fct_sweep_compare(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us):

    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps, ssird_fct, label="SSIRD", linestyle='-', marker='o')
    plt.plot(load_gbps, dctcp_fct, label="DCTCP", linestyle='-', marker='o')

    plt.xlabel('Load (GBps)')
    plt.ylabel('Flow Completion Time (s)')
    plt.title(f"SSIRD vs DCTCP: FCT vs Load Sweep ({num_byteloads} x {inter_byteload_period_us/1000}ms)")
    plt.legend()
    plt.grid(True)

    # plt.yscale('log')

    filename = f"ssird_dctcp_fct_sweep_1gbps_100gbps.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_dctcp_fct_sweep_diff(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us):
    fct_ssird_minus_dctcp_us = [(ssird - dctcp) * 1000 for ssird, dctcp in zip(ssird_fct, dctcp_fct)]

    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps, fct_ssird_minus_dctcp_us, linestyle='-', marker='o')

    plt.xlabel('Load (GBps)')
    plt.ylabel('FCT SSIRD - DCTCP (ms)')
    plt.title(f"FCT Difference (SSIRD - DCTCP) vs Load Sweep ({num_byteloads} x {inter_byteload_period_us/1000}ms)")
    plt.grid(True)
    # plt.yscale('log')

    filename = f"ssird_dctcp_fct_sweep_1gbps_100gbps_diff.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_dctcp_fct_1000B():
    num_byteloads = 4
    byteload_size_B = 1000
    inter_byteload_period_us_list = [100, 500, 1000, 5000, 10000]
    ssird_fct = [0.0006107130000003735, 0.0030107130000001092, 0.006010713000000223, 0.030010714000001215, 0.060010714000000576]
    dctcp_fct = [0.0006056720000007232, 0.003005672000000459, 0.0060056720000005726, 0.030005672000001482, 0.06000567200000084]
    plot_ssird_dctcp_fct_compare(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B)
    plot_ssird_dctcp_fct_diff(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B)

def plot_ssird_dctcp_fct_100000B():
    num_byteloads = 4
    byteload_size_B = 100000
    inter_byteload_period_us_list = [100, 500, 1000, 5000, 10000]
    ssird_fct = [0.0006190300000010751, 0.003019030000000811, 0.0060190300000009245, 0.030019030000000058, 0.06001903100000128]
    dctcp_fct = [0.0006140540000014738, 0.0030140540000012095, 0.006014054000001323, 0.030014054000000456, 0.06001405400000159]
    plot_ssird_dctcp_fct_compare(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B)
    plot_ssird_dctcp_fct_diff(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B)

def plot_ssird_dctcp_fct_sweep_1gbps_100gbps():
    inter_byteload_period_us = 1000
    num_byteloads = 10
    byteload_size_B_list = [100000, 500000, 1000000, 5000000, 10000000]
    load_gbps = [1.0, 5.0, 10.0, 50.0, 100.0]
    ssird_fct = [0.015020917000001077, 0.015054869000000082, 0.01509706400000077, 0.015434331000001578, 0.015856482000000227]
    dctcp_fct = [0.015016054000000167, 0.015049763000000382, 0.015091897000001353, 0.015428995000000612, 0.01585036700000053]
    plot_ssird_dctcp_fct_sweep_compare(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us)
    plot_ssird_dctcp_fct_sweep_diff(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us)

if __name__ == "__main__":
    # plot_ssird_dctcp_fct_1000B()
    # plot_ssird_dctcp_fct_100000B()
    plot_ssird_dctcp_fct_sweep_1gbps_100gbps()