import matplotlib.pyplot as plt

SSIRD_PLOT_COLOUR = 'tab:blue'
DCTCP_PLOT_COLOUR = 'tab:orange'

def plot_ssird_dctcp_fct_compare(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B, is_log_x=False, is_log_y=False, title_addendum=""):
    ssird_fct_ms = [t * 1000 for t in ssird_fct]
    dctcp_fct_ms = [t * 1000 for t in dctcp_fct]
    plt.figure(figsize=(10, 6))
    plt.plot(inter_byteload_period_us_list, ssird_fct_ms, label="SSIRD", linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.plot(inter_byteload_period_us_list, dctcp_fct_ms, label="DCTCP", linestyle='-', marker='o', color=DCTCP_PLOT_COLOUR)
    plt.xlabel('Inter-byteload Period (us)')
    plt.ylabel('Flow Completion Time (ms)')
    plt.title(f"SSIRD vs DCTCP: FCT vs Inter-byteload period ({num_byteloads} x {byteload_size_B} Bytes) {title_addendum}")
    plt.legend()
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log')
    filename = f"ssird_dctcp_fct_{byteload_size_B}B_vary_period{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_dctcp_fct_sweep_compare(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us, title_addendum=""):
    ssird_fct_ms = [t * 1000 for t in ssird_fct]
    dctcp_fct_ms = [t * 1000 for t in dctcp_fct]
    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps, ssird_fct_ms, label="SSIRD", linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.plot(load_gbps, dctcp_fct_ms, label="DCTCP", linestyle='-', marker='o', color=DCTCP_PLOT_COLOUR)
    plt.xlabel('Load (GBps)')
    plt.ylabel('Flow Completion Time (ms)')
    plt.title(f"SSIRD vs DCTCP: FCT vs Load Sweep ({num_byteloads} x {inter_byteload_period_us/1000}ms) {title_addendum}")
    plt.legend()
    plt.grid(True)
    filename = f"ssird_dctcp_fct_sweep_1gbps_100gbps{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_dctcp_fct_diff(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B, is_log_x=False, is_log_y=False, title_addendum=""):
    fct_ssird_minus_dctcp_us = [(ssird - dctcp) * 1000000 for ssird, dctcp in zip(ssird_fct, dctcp_fct)]
    plt.figure(figsize=(10, 6))
    plt.plot(inter_byteload_period_us_list, fct_ssird_minus_dctcp_us, linestyle='-', marker='o')
    plt.xlabel('Inter-byteload Period')
    plt.ylabel('FCT SSIRD - DCTCP (ms)')
    plt.title(f"FCT Difference (SSIRD - DCTCP) vs Inter-byteload period ({num_byteloads} x {byteload_size_B} Bytes) {title_addendum}")
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log')
    filename = f"ssird_dctcp_fct_{byteload_size_B}B_vary_period_DIFF{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_dctcp_fct_sweep_diff(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us, title_addendum=""):
    fct_ssird_minus_dctcp_us = [(ssird - dctcp) * 1000000 for ssird, dctcp in zip(ssird_fct, dctcp_fct)]
    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps, fct_ssird_minus_dctcp_us, linestyle='-', marker='o')
    plt.xlabel('Load (GBps)')
    plt.ylabel('FCT SSIRD - DCTCP (us)')
    plt.title(f"FCT Difference (SSIRD - DCTCP) vs Load Sweep ({num_byteloads} x {inter_byteload_period_us/1000}ms) {title_addendum}")
    plt.grid(True)
    filename = f"ssird_dctcp_fct_sweep_1gbps_100gbps_DIFF{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_dctcp_fct_slowdown_vs_ideal(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=False, is_log_y=False, title_addendum=""):
    ssird_slowdown_percent = [((ssird-ideal)/ideal) * 100 for ssird, ideal in zip(ssird_fct, ideal_fct)] 
    dctcp_slowdown_percent = [((dctcp-ideal)/ideal) * 100 for dctcp, ideal in zip(dctcp_fct, ideal_fct)] 
    plt.figure(figsize=(10, 6))
    plt.plot(inter_byteload_period_us_list, ssird_slowdown_percent, label='SSIRD', linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.plot(inter_byteload_period_us_list, dctcp_slowdown_percent, label='DCTCP', linestyle='-', marker='o', color=DCTCP_PLOT_COLOUR)
    plt.xlabel('Inter-byteload Period (us)')
    plt.ylabel('Slowdown vs Ideal (%)')
    plt.title(f"SSIRD: FCT Slowdown vs Inter-byteload period ({num_byteloads} x {byteload_size_B} Bytes) {title_addendum}")
    plt.legend()
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log')
    filename = f"ssird_dctcp_fct_slowdown_{byteload_size_B}B_vary_period{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_dctcp_fct_sweep_slowdown_vs_ideal(load_gbps, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, inter_byteload_period_us, title_addendum=""):
    ssird_slowdown_percent = [((ssird-ideal)/ideal) * 100 for ssird, ideal in zip(ssird_fct, ideal_fct)] 
    dctcp_slowdown_percent = [((dctcp-ideal)/ideal) * 100 for dctcp, ideal in zip(dctcp_fct, ideal_fct)] 
    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps, ssird_slowdown_percent, label='SSIRD', linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.plot(load_gbps, dctcp_slowdown_percent, label='DCTCP', linestyle='-', marker='o', color=DCTCP_PLOT_COLOUR)
    plt.xlabel('Load (GBps)')
    plt.ylabel('Slowdown vs Ideal (%)')
    plt.title(f"SSIRD: FCT Slowdown vs Load Sweep ({num_byteloads} x {inter_byteload_period_us/1000}ms) {title_addendum}")
    plt.legend()
    plt.grid(True)
    filename = f"ssird_dctcp_fct_slowdown_sweep_1gbps_100gbps{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

# def plot_ssird_dctcp_fct_1000B():
#     num_byteloads = 4
#     byteload_size_B = 1000
#     inter_byteload_period_us_list = [100, 500, 1000, 5000, 10000]
#     ssird_fct = [0.0006107130000003735, 0.0030107130000001092, 0.006010713000000223, 0.030010714000001215, 0.060010714000000576]
#     dctcp_fct = [0.0006056720000007232, 0.003005672000000459, 0.0060056720000005726, 0.030005672000001482, 0.06000567200000084]
#     plot_ssird_dctcp_fct_compare(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B)

def plot_ssird_dctcp_fct_1000000B_varying_period():
    # INFO:__main__:Time Periods: [10, 50, 100, 500, 1000, 5000]
    # INFO:__main__:Num Byteloads: 5
    # INFO:__main__:Byteload Size: 1000000 Bytes
    # INFO:__main__:Sim duration (SSIRD): [0.0005, 0.0005, 0.001, 0.0025, 0.005, 0.024999999999999998]
    # INFO:__main__:Sim duration (DCTCP): [0.0005, 0.0005, 0.001, 0.0025, 0.005, 0.024999999999999998]
    # INFO:__main__:* IDEAL FCT: [5e-05, 0.00020999999999999998, 0.00041, 0.00201, 0.00401, 0.02001]
    # INFO:__main__:* SSIRD FCT: [0.00042970199999992076, 0.00042970199999992076, 0.0004920730000002038, 0.0020920630000009766, 0.004092074000000778, 0.020092063999999965]
    # INFO:__main__:* DCTCP FCT: [0.00044456500000045196, 0.00044456500000045196, 0.00048689700000004166, 0.0020868969999998654, 0.004086897000000533, 0.020086897000000548]

    num_byteloads = 5
    byteload_size_B = 1000000
    inter_byteload_period_us_list = [10, 50, 100, 500, 1000, 5000]
    ideal_fct = [4.9999999999999996e-05, 0.00020999999999999998, 0.00041, 0.00201, 0.00401, 0.02001]
    ssird_fct = [0.00042970199999992076, 0.00042970199999992076, 0.0004920730000002038, 0.0020920630000009766, 0.004092074000000778, 0.020092063999999965]
    dctcp_fct = [0.00044456500000045196, 0.00044456500000045196, 0.00048689700000004166, 0.0020868969999998654, 0.004086897000000533, 0.020086897000000548]
    plot_ssird_dctcp_fct_compare(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B, is_log_x=True)
    plot_ssird_dctcp_fct_slowdown_vs_ideal(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=True)
    plot_ssird_dctcp_fct_diff(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B, is_log_x=True)
    
def plot_ssird_dctcp_manyconn_fct_1000000B_varying_period():
    # INFO:__main__:num of byteloads: 5, num of srq_events: 5, num of rrq_events 5
    # INFO:__main__:DCTCP FCT: 0.020086897000000548 ms, Load: 0.19999999999999243 Gbps
    # INFO:__main__:Time Periods: [10, 50, 100, 500, 1000, 5000]
    # INFO:__main__:Num Byteloads: 5
    # INFO:__main__:Byteload Size: 1000000 Bytes
    # INFO:__main__:Sim duration (SSIRD): [0.0005, 0.0005, 0.001, 0.0025, 0.005, 0.024999999999999998]
    # INFO:__main__:Sim duration (DCTCP): [0.0005, 0.0005, 0.001, 0.0025, 0.005, 0.024999999999999998]
    # INFO:__main__:* IDEAL FCT: [5e-05, 0.00020999999999999998, 0.00041, 0.00201, 0.00401, 0.02001]
    # INFO:__main__:* SSIRD FCT: [0.00042970199999992076, 0.00042970199999992076, 0.0004920730000002038, 0.0020920630000009766, 0.004092074000000778, 0.020092063999999965]
    # INFO:__main__:* DCTCP FCT: [0.00042801800000091816, 0.00043185100000009413, 0.00048689700000004166, 0.0020868969999998654, 0.004086897000000533, 0.020086897000000548]

    title_addendum = "_DCTCP_many_conns"
    num_byteloads = 5
    byteload_size_B = 1000000
    inter_byteload_period_us_list = [10, 50, 100, 500, 1000, 5000]
    ideal_fct = [5e-05, 0.00020999999999999998, 0.00041, 0.00201, 0.00401, 0.02001]
    ssird_fct = [0.00042970199999992076, 0.00042970199999992076, 0.0004920730000002038, 0.0020920630000009766, 0.004092074000000778, 0.020092063999999965]
    dctcp_fct = [0.00042801800000091816, 0.00043185100000009413, 0.00048689700000004166, 0.0020868969999998654, 0.004086897000000533, 0.020086897000000548]
    plot_ssird_dctcp_fct_compare(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B, is_log_x=True, title_addendum=title_addendum)
    plot_ssird_dctcp_fct_slowdown_vs_ideal(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=True, title_addendum=title_addendum)
    plot_ssird_dctcp_fct_diff(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B, is_log_x=True, title_addendum=title_addendum)

def plot_ssird_dctcp_fct_sweep_1gbps_100gbps():
    # INFO:__main__:Time Period: 100
    # INFO:__main__:Num Byteloads: 10
    # INFO:__main__:Byteload Size (Bytes): [100000, 500000, 1000000, 5000000, 10000000]
    # INFO:__main__:Load GBps theoretical: [1.0000000000000002, 5.000000000000001, 10.000000000000002, 50.00000000000001, 100.00000000000001]
    # INFO:__main__:Load GBps measured: [1.0000000000001101, 5.000000000000551, 10.000000000001101, 50.000000000005514, 100.00000000001103]
    # INFO:__main__:Sim duration (SSIRD): [0.002, 0.002, 0.002, 0.006, 0.01]
    # INFO:__main__:Sim duration (DCTCP): [0.002, 0.002, 0.002, 0.006, 0.01]
    # INFO:__main__:* IDEAL FCT: [0.000901, 0.000905, 0.00091, 0.00095, 0.001]
    # INFO:__main__:* SSIRD FCT: [0.0009161049999999449, 0.0009498580000002477, 0.0009920530000009364, 0.004227265000000813, 0.008446747000000698]
    # INFO:__main__:* DCTCP FCT: [0.0009110540000012435, 0.0009447630000014584, 0.0009868970000006527, 0.0042626250000008525, 0.008476345000000052]

    inter_byteload_period_us = 100
    num_byteloads = 10
    load_gbps = [1.0, 5.0, 10.0, 50.0, 100.0]
    ideal_fct = [0.000901, 0.000905, 0.00091, 0.00095, 0.001]
    ssird_fct = [0.0009161049999999449, 0.0009498580000002477, 0.0009920530000009364, 0.004227265000000813, 0.008446747000000698]
    dctcp_fct = [0.0009110540000012435, 0.0009447630000014584, 0.0009868970000006527, 0.0042626250000008525, 0.008476345000000052]
    plot_ssird_dctcp_fct_sweep_compare(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us)
    plot_ssird_dctcp_fct_sweep_slowdown_vs_ideal(load_gbps, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, inter_byteload_period_us)
    plot_ssird_dctcp_fct_sweep_diff(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us)

def plot_ssird_dctcp_manyconn_fct_sweep_1gbps_100gbps():
    # INFO:__main__:Time Period: 100
    # INFO:__main__:Num Byteloads: 10
    # INFO:__main__:Byteload Size (Bytes): [100000, 500000, 1000000, 5000000, 10000000]
    # INFO:__main__:Load GBps theoretical: [1.0000000000000002, 5.000000000000001, 10.000000000000002, 50.00000000000001, 100.00000000000001]
    # INFO:__main__:Load GBps measured: [1.0000000000001101, 5.000000000000551, 10.000000000001101, 50.000000000005514, 100.00000000001103]
    # INFO:__main__:Sim duration (SSIRD): [0.002, 0.002, 0.002, 0.006, 0.01]
    # INFO:__main__:Sim duration (DCTCP): [0.002, 0.002, 0.002, 0.006, 0.01]
    # INFO:__main__:* IDEAL FCT: [0.000901, 0.000905, 0.00091, 0.00095, 0.001]
    # INFO:__main__:* SSIRD FCT: [0.0009161049999999449, 0.0009498580000002477, 0.0009920530000009364, 0.004227265000000813, 0.008446747000000698]
    # INFO:__main__:* DCTCP FCT: [0.0009110540000012435, 0.0009447630000014584, 0.0009868970000006527, 0.004218168000001299, 0.008432386000000847]

    title_addendum = "_DCTCP_many_conns"
    inter_byteload_period_us = 100
    num_byteloads = 10
    load_gbps = [1.0, 5.0, 10.0, 50.0, 100.0]
    ideal_fct = [0.000901, 0.000905, 0.00091, 0.00095, 0.001]
    ssird_fct = [0.0009161049999999449, 0.0009498580000002477, 0.0009920530000009364, 0.004227265000000813, 0.008446747000000698]
    dctcp_fct = [0.0009110540000012435, 0.0009447630000014584, 0.0009868970000006527, 0.004218168000001299, 0.008432386000000847]
    plot_ssird_dctcp_fct_sweep_compare(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us, title_addendum=title_addendum)
    plot_ssird_dctcp_fct_sweep_slowdown_vs_ideal(load_gbps, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, inter_byteload_period_us, title_addendum=title_addendum)
    plot_ssird_dctcp_fct_sweep_diff(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us, title_addendum=title_addendum)

def plot_ssird_dctcp_2conn_each_fct_1000000B_varying_period():
    # INFO:__main__:Time Periods: [10, 50, 100, 500, 1000, 5000]
    # INFO:__main__:Num Byteloads: 5
    # INFO:__main__:Byteload Size: 1000000 Bytes
    # INFO:__main__:Sim duration (SSIRD): [0.001, 0.001, 0.002, 0.005, 0.01, 0.049999999999999996]
    # INFO:__main__:Sim duration (DCTCP): [0.001, 0.001, 0.002, 0.005, 0.01, 0.049999999999999996]
    # INFO:__main__:* IDEAL FCT: [0.0001, 0.00021999999999999998, 0.00041999999999999996, 0.00202, 0.00402, 0.02002]
    # INFO:__main__:* SSIRD FCT: [0.0008516880000009053, 0.0008516880000009053, 0.0008517140000012802, 0.002176851000001534, 0.004176861000001253, 0.02017685100000044]
    # INFO:__main__:* DCTCP FCT: [0.0008453730000006487, 0.0008453730000006487, 0.0008453730000006487, 0.0021715780000004514, 0.004171578000001119, 0.020171578000001134]

    title_addendum = "_2conns_each"
    num_byteloads = 5
    byteload_size_B = 1000000
    inter_byteload_period_us_list = [10, 50, 100, 500, 1000, 5000]
    ideal_fct = [0.0001, 0.00021999999999999998, 0.00041999999999999996, 0.00202, 0.00402, 0.02002]
    ssird_fct = [0.0008516880000009053, 0.0008516880000009053, 0.0008517140000012802, 0.002176851000001534, 0.004176861000001253, 0.02017685100000044]
    dctcp_fct = [0.0008453730000006487, 0.0008453730000006487, 0.0008453730000006487, 0.0021715780000004514, 0.004171578000001119, 0.020171578000001134]
    plot_ssird_dctcp_fct_compare(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B, is_log_x=True, title_addendum=title_addendum)
    plot_ssird_dctcp_fct_slowdown_vs_ideal(inter_byteload_period_us_list, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=True, title_addendum=title_addendum)
    plot_ssird_dctcp_fct_diff(inter_byteload_period_us_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B, is_log_x=True, title_addendum=title_addendum)

def plot_ssird_dctcp_2conn_each_fct_sweep_1gbps_100gbps():
    # INFO:__main__:Time Period: 100
    # INFO:__main__:Num Byteloads: 10
    # INFO:__main__:Byteload Size (Bytes): [100000, 500000, 1000000, 5000000, 10000000]
    # INFO:__main__:Load GBps theoretical: [2.0000000000000004, 10.0, 20.0, 100.00000000000001, 200.00000000000003]
    # INFO:__main__:Load GBps measured: [1.9801980198018743, 9.900990099009372, 19.801980198018743, 99.00990099009371, 198.01980198018742]
    # INFO:__main__:Sim duration (SSIRD): [0.004, 0.004, 0.004, 0.012, 0.02]
    # INFO:__main__:Sim duration (DCTCP): [0.004, 0.004, 0.004, 0.012, 0.02]
    # INFO:__main__:* IDEAL FCT: [0.000902, 0.00091, 0.00092, 0.001, 0.002]
    # INFO:__main__:* SSIRD FCT: [0.0009335860000003748, 0.001001060000000109, 0.0016957060000013513, 0.008446814000000913, 0.0168857770000006]
    # INFO:__main__:* DCTCP FCT: [0.0009284840000010064, 0.0009959040000016017, 0.0016881170000004886, 0.008430069000000984, 0.01685750900000116]

    title_addendum = "_2conns_each"
    inter_byteload_period_us = 100
    num_byteloads = 10
    load_gbps = [1.0, 5.0, 10.0, 50.0, 100.0]
    ideal_fct = [0.000902, 0.00091, 0.00092, 0.001, 0.002]
    ssird_fct = [0.0009335860000003748, 0.001001060000000109, 0.0016957060000013513, 0.008446814000000913, 0.0168857770000006]
    dctcp_fct = [0.0009284840000010064, 0.0009959040000016017, 0.0016881170000004886, 0.008430069000000984, 0.01685750900000116]
    plot_ssird_dctcp_fct_sweep_compare(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us, title_addendum=title_addendum)
    plot_ssird_dctcp_fct_sweep_slowdown_vs_ideal(load_gbps, ssird_fct, dctcp_fct, ideal_fct, num_byteloads, inter_byteload_period_us, title_addendum=title_addendum)
    plot_ssird_dctcp_fct_sweep_diff(load_gbps, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us, title_addendum=title_addendum)

if __name__ == "__main__":
    # plot_ssird_dctcp_fct_1000000B_varying_period()
    # plot_ssird_dctcp_fct_sweep_1gbps_100gbps()

    plot_ssird_dctcp_2conn_each_fct_1000000B_varying_period()
    plot_ssird_dctcp_2conn_each_fct_sweep_1gbps_100gbps()

