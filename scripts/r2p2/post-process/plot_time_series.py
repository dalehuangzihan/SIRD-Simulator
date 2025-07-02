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

def plot_ssird_dctcp_fct_slowdown_vs_ideal(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, byteload_size_B):
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

    # plt.yscale('log')

    filename = f"ssird_dctcp_fct_slowdown_sweep_1gbps_100gbps.png"
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

    # plt.yscale('log')

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
    # INFO:__main__:* IDEAL FCT: [0.000301, 0.001501, 0.003001, 0.015000999999999999, 0.030001]
    # INFO:__main__:* SSIRD FCT: [0.0006190300000010751, 0.003019030000000811, 0.0060190300000009245, 0.030019030000000058, 0.06001903100000128]
    # INFO:__main__:* DCTCP FCT: [0.0006140540000014738, 0.0030140540000012095, 0.006014054000001323, 0.030014054000000456, 0.06001405400000159]
    num_byteloads = 4
    byteload_size_B = 100000
    inter_byteload_period_us_list = [100, 500, 1000, 5000, 10000]
    ideal_fct = [0.000301, 0.001501, 0.003001, 0.015000999999999999, 0.030001]
    ssird_fct = [0.0006190300000010751, 0.003019030000000811, 0.0060190300000009245, 0.030019030000000058, 0.06001903100000128]
    dctcp_fct = [0.0006140540000014738, 0.0030140540000012095, 0.006014054000001323, 0.030014054000000456, 0.06001405400000159]
    plot_ssird_dctcp_fct_compare(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B)
    plot_ssird_dctcp_fct_slowdown_vs_ideal(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, byteload_size_B)
    

def plot_ssird_dctcp_fct_sweep_1gbps_100gbps():
    inter_byteload_period_us = 1000
    num_byteloads = 10
    load_gbps = [1.0, 5.0, 10.0, 50.0, 100.0]
    ideal_fct = [] # TODO
    ssird_fct = [0.015020917000001077, 0.015054869000000082, 0.01509706400000077, 0.015434331000001578, 0.015856482000000227]
    dctcp_fct = [0.015016054000000167, 0.015049763000000382, 0.015091897000001353, 0.015428995000000612, 0.01585036700000053]
    plot_ssird_dctcp_fct_sweep_compare(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us)
    plot_ssird_dctcp_fct_sweep_slowdown_vs_ideal(load_gbps, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, inter_byteload_period_us)

if __name__ == "__main__":
    # plot_ssird_dctcp_fct_1000B()
    # plot_ssird_dctcp_fct_100000B()
    plot_ssird_dctcp_fct_100000B()
    # plot_ssird_dctcp_fct_sweep_1gbps_100gbps()