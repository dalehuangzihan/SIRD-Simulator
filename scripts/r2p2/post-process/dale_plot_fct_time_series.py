import matplotlib.pyplot as plt

SSIRD_PLOT_COLOUR = 'tab:orange'
DCTCP_PLOT_COLOR  = 'tab:green'
IDEAL_PLOT_COLOUR = 'tab:blue'

LINK_SPEED_GIGABITS_PER_SEC = 100 # 100 GBps link speed

def plot_ssird_vs_ideal_vary_interval_fct_compare(thrpt_gbps, ssird_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=False, is_log_y=False, title_addendum=""):
    ssird_fct_ms = [t * 1000 for t in ssird_fct]
    ideal_fct_ms = [t * 1000 for t in ideal_fct]
    load_gbps_int = [int(l) for l in thrpt_gbps]
    # load_percent = [(l / LINK_SPEED_GIGABITS_PER_SEC) * 100 for l in load_gbps]
    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps_int, ssird_fct_ms, label="SSIRD", linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.plot(load_gbps_int, ideal_fct_ms, label="Ideal (DCTCP conn-pool)", linestyle='-', marker='o', color=IDEAL_PLOT_COLOUR)
    plt.xlabel('Goodput (Gbps)')
    plt.ylabel('Flow Completion Time (ms)')
    plt.ylim(0.0, 4.2)
    plt.title(f"FCT: SSIRD vs Ideal: Varying Intervals ({num_byteloads} byteloads x {byteload_size_B} Bytes x P ms) {title_addendum}\n(Flow Rate Changes!)")
    plt.legend()
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log')
    filename = f"ssird_vs_ideal_vary_interval_{num_byteloads}#_{byteload_size_B}B_fct{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_vary_byteloadsize_fct_compare(thrpt_gbps, ssird_fct, ideal_fct, num_byteloads, inter_byteload_period_us, title_addendum=""):
    ssird_fct_ms = [t * 1000 for t in ssird_fct]
    ideal_fct_ms = [t * 1000 for t in ideal_fct]
    load_gbps_int = [int(l) for l in thrpt_gbps]
    # load_percent = [(l / LINK_SPEED_GIGABITS_PER_SEC) * 100 for l in load_gbps]
    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps_int, ssird_fct_ms, label="SSIRD", linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.plot(load_gbps_int, ideal_fct_ms, label="Ideal (DCTCP conn-pool)", linestyle='-', marker='o', color=IDEAL_PLOT_COLOUR)
    plt.xlabel('Goodput (Gbps)')
    plt.ylabel('Flow Completion Time (ms)')
    plt.ylim(0.0, 4.2)
    plt.title(f"FCT: SSIRD vs Ideal: Varying Byteload Size ({num_byteloads} byteloads x B Bytes x {inter_byteload_period_us/1000}ms) {title_addendum}\n(Flow Size Changes!)")
    plt.legend()
    plt.grid(True)
    filename = f"ssird_vs_ideal_vary_byteloadsize_{num_byteloads}#_{inter_byteload_period_us}us_fct{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_vary_interval_fct_diff(thrpt_gbps, ssird_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=False, is_log_y=False, title_addendum=""):
    fct_ssird_minus_ideal_us = [(ssird - ideal) * 1000000 for ssird, ideal in zip(ssird_fct, ideal_fct)]
    load_gbps_int = [int(l) for l in thrpt_gbps]
    # load_percent = [(l / LINK_SPEED_GIGABITS_PER_SEC) * 100 for l in load_gbps]
    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps_int, fct_ssird_minus_ideal_us, linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR, label='SSIRD')
    plt.xlabel('Goodput (Gbps)')
    plt.ylabel('FCT SSIRD - Ideal (us)')
    plt.ylim(3, 8)
    plt.title(f"FCT Difference (SSIRD - Ideal): Varying Intervals ({num_byteloads} byteloads x {byteload_size_B} Bytes x P ms) {title_addendum}\n(Flow Rate Changes!)")
    plt.legend()
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log')
    filename = f"ssird_vs_ideal_vary_interval_{num_byteloads}#_{byteload_size_B}B_fct_DIFF{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_vary_byteloadsize_fct_diff(thrpt_gbps, ssird_fct, ideal_fct, num_byteloads, inter_byteload_period_us, title_addendum=""):
    fct_ssird_minus_ideal_us = [(ssird - ideal) * 1000000 for ssird, ideal in zip(ssird_fct, ideal_fct)]
    load_gbps_int = [int(l) for l in thrpt_gbps]
    # load_percent = [(l / LINK_SPEED_GIGABITS_PER_SEC) * 100 for l in load_gbps]
    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps_int, fct_ssird_minus_ideal_us, label='SSIRD', linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.xlabel('Goodput (Gbps)')
    plt.ylabel('FCT SSIRD - Ideal (us)')
    plt.ylim(3, 8)
    plt.title(f"FCT Difference (SSIRD - Ideal): Varying Byteload Size ({num_byteloads} byteloads x B Bytes x {inter_byteload_period_us/1000}ms) {title_addendum}\n(Flow Size Changes!)")
    plt.legend()
    plt.grid(True)
    filename = f"ssird_vs_ideal_vary_byteloadsize_{num_byteloads}#_{inter_byteload_period_us}us_fct_DIFF{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_vary_interval_fct_slowdown(thrpt_gbps, ssird_fct, ideal_fct, num_byteloads, byteload_size_B, is_log_x=False, is_log_y=False, title_addendum=""):
    ssird_slowdown = [ssird/ideal for ssird, ideal in zip(ssird_fct, ideal_fct)] 
    load_gbps_int = [int(l) for l in thrpt_gbps]
    # load_percent = [(l / LINK_SPEED_GIGABITS_PER_SEC) * 100 for l in load_gbps]
    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps_int, ssird_slowdown, label='SSIRD', linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.xlabel('Thorughput (Gbps)')
    plt.ylabel('Slowdown vs Ideal FCT')
    plt.ylim(0.98, 1.1)
    plt.title(f"FCT Slowdown: Varying Intervals ({num_byteloads} byteloads x {byteload_size_B} Bytes x P ms) {title_addendum}\n(Flow Rate Changes!)")
    plt.legend()
    plt.grid(True)
    if (is_log_x): plt.xscale('log')
    if (is_log_y): plt.yscale('log')
    filename = f"ssird_vs_ideal_vary_interval_{num_byteloads}#_{byteload_size_B}B_fct_slowdown{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_vary_byteloadsize_fct_slowdown(thrpt_gbps, ssird_fct, ideal_fct, num_byteloads, inter_byteload_period_us, title_addendum=""):
    ssird_slowdown = [ssird/ideal for ssird, ideal in zip(ssird_fct, ideal_fct)] 
    load_gbps_int = [int(l) for l in thrpt_gbps]
    # load_percent = [(l / LINK_SPEED_GIGABITS_PER_SEC) * 100 for l in load_gbps]
    plt.figure(figsize=(10, 6))
    plt.plot(load_gbps_int, ssird_slowdown, label='SSIRD', linestyle='-', marker='o', color=SSIRD_PLOT_COLOUR)
    plt.xlabel('Goodput (Gbps)')
    plt.ylabel('Slowdown vs Ideal FCT')
    plt.ylim(0.98, 1.1)
    plt.title(f"FCT Slowdown: Varying Byteload Size ({num_byteloads} byteloads x B Bytes x {inter_byteload_period_us/1000}ms) {title_addendum}\n(Flow Size Changes!)")
    plt.legend()
    plt.grid(True)
    filename = f"ssird_vs_ideal_vary_byteloadsize_{num_byteloads}#_{inter_byteload_period_us}us_fct_slowdown{title_addendum}.png"
    plt.savefig(f"tmp_plot/{filename}")
    plt.close()

def plot_ssird_vs_ideal_fct_1000000B_varying_period():
    # INFO:__main__:Time Periods: [1000, 500, 100, 50, 10]
    # INFO:__main__:Num Byteloads: 5
    # INFO:__main__:Byteload Size: 125000 Bytes
    # INFO:__main__:Sim duration (SSIRD): [0.005, 0.0025, 0.0005, 0.00025, 7.5e-05]
    # INFO:__main__:Sim duration (DCTCP): [0.005, 0.0025, 0.0005, 0.00025, 7.5e-05]
    # INFO:__main__:Load Measured (Gbps): [0.9999999999999621, 1.9999999999999243, 9.999999999964094, 19.999999999809766, 99.99999999786458]
    # INFO:__main__:* IDEAL FCT: [0.005, 0.0025, 0.0005, 0.00025, 4.9999999999999996e-05]
    # INFO:__main__:* IDEAL FCT (old): [0.0040012500000000005, 0.00200125, 0.00040124999999999997, 0.00020124999999999999, 4.125e-05]
    # INFO:__main__:* SSIRD FCT: [0.00401823400000012, 0.0020182230000003187, 0.00041823300000132235, 0.00021822300000096106, 6.049600000146427e-05]
    # INFO:__main__:* DCTCP FCT: [0.004013160000001292, 0.0020131600000006244, 0.00041316000000080066, 0.00021316000000126678, 5.533100000043589e-05]

    '''
        NOTE: Slowdown increases with rate, because flow size is unchanged, but FCT is reduced as byteload interval size decreases. So the 1RTT delay becomes a biger and bigger proportion of the FCT.
    '''

    num_byteloads = 5
    byteload_size_B = 125000  # 1000000/8 Bytes
    inter_byteload_period_us_list = [1000, 500, 100, 50, 10]
    throughput_measured_gbps_list = list(map(int, [0.9999999999999621, 1.9999999999999243, 9.999999999964094, 19.999999999809766, 99.99999999786458]))
    ssird_fct = [0.00401823400000012, 0.0020182230000003187, 0.00041823300000132235, 0.00021822300000096106, 6.049600000146427e-05]
    dctcp_fct = [0.004013160000001292, 0.0020131600000006244, 0.00041316000000080066, 0.00021316000000126678, 5.533100000043589e-05] 
    plot_ssird_vs_ideal_vary_interval_fct_compare(throughput_measured_gbps_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B)
    plot_ssird_vs_ideal_vary_interval_fct_slowdown(throughput_measured_gbps_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B)
    plot_ssird_vs_ideal_vary_interval_fct_diff(throughput_measured_gbps_list, ssird_fct, dctcp_fct, num_byteloads, byteload_size_B)
    
def plot_ssird_vs_ideal_fct_varying_byteloadsize_100us():
    # INFO:__main__:Time Period: 100
    # INFO:__main__:Num Byteloads: 10
    # INFO:__main__:Byteload Size (Bytes): [12500, 62500, 125000, 625000, 1250000]
    # INFO:__main__:Load Gbps theoretical: [1.0000000000000002, 5.000000000000001, 10.000000000000002, 50.00000000000001, 100.00000000000001]
    # INFO:__main__:Load Gbps measured: [1.0000000000001101, 5.000000000000551, 10.000000000001101, 50.000000000005514, 100.00000000001103]
    # INFO:__main__:Sim duration (SSIRD): [0.001, 0.001, 0.001, 0.001, 0.0015]
    # INFO:__main__:Sim duration (DCTCP): [0.001, 0.001, 0.001, 0.001, 0.0015]
    # INFO:__main__:* IDEAL FCT: [0.0009999999999999998, 0.001, 0.001, 0.0009999999999999998, 0.0009999999999999998]
    # INFO:__main__:* IDEAL FCT (old): [0.000900125, 0.000900625, 0.0009012499999999999, 0.0009062499999999999, 0.0009125]
    # INFO:__main__:* SSIRD FCT: [0.0009087210000000567, 0.0009129380000008069, 0.0009182130000002786, 0.0009604090000010501, 0.0010626570000003]
    # INFO:__main__:* DCTCP FCT: [0.0009036790000003236, 0.0009078910000006601, 0.0009131600000014117, 0.0009553000000011025, 0.001056156000000641]

    '''
        NOTE: FCT time increases because flow size increases; specifically, the final byteload is larger, and so will take longer to transmit.
    '''

    inter_byteload_period_us = 100
    num_byteloads = 10
    byteload_size_B_list = [12500, 62500, 125000, 625000, 1250000]  # 100/8KB to 10/8MB
    throughput_measured_gbps_list = list(map(int, [1.0000000000001101, 5.000000000000551, 10.000000000001101, 50.000000000005514, 100.00000000001103]))
    ssird_fct = [0.0009087210000000567, 0.0009129380000008069, 0.0009182130000002786, 0.0009604090000010501, 0.0010626570000003]
    dctcp_fct = [0.0009036790000003236, 0.0009078910000006601, 0.0009131600000014117, 0.0009553000000011025, 0.001056156000000641]
    plot_ssird_vs_ideal_vary_byteloadsize_fct_compare(throughput_measured_gbps_list, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us)
    plot_ssird_vs_ideal_vary_byteloadsize_fct_slowdown(throughput_measured_gbps_list, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us)
    plot_ssird_vs_ideal_vary_byteloadsize_fct_diff(throughput_measured_gbps_list, ssird_fct, dctcp_fct, num_byteloads, inter_byteload_period_us)

if __name__ == "__main__":
    plot_ssird_vs_ideal_fct_1000000B_varying_period()
    plot_ssird_vs_ideal_fct_varying_byteloadsize_100us()
