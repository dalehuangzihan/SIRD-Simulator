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

if __name__ == "__main__":
    plot_ssird_dctcp_fct_1000B()
    plot_ssird_dctcp_fct_100000B()