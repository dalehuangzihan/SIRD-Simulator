import dale_experiment_rig

CR_0_to_1_SUBSTRING = "Forwarded standalone grant_request asking for"
C_1_to_0_SUBSTRING = ">>>>Sending credit to:"
D_0_to_1_SUBSTRING = "Sending pkt of msg"
SUBSTR_LIST = [CR_0_to_1_SUBSTRING, C_1_to_0_SUBSTRING, D_0_to_1_SUBSTRING]
CREDITREQ_PKT_OVERHEAD_B = 84
CREDIT_PKT_OVERHEAD_B = 84
DATA_PKT_OVERHEAD_B = 80

# PATH_TO_SIM_OUTPUTS = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/scripts/r2p2/coord/outputs/"
PATH_TO_SIM_OUTPUTS = "/data/dh1723/SIRD-Simulator/scripts/r2p2/coord/outputs/" # NOTE: use this for batch1 server
REL_PATH_TO_EXP_FAMILY = "FCT_Subpkt_Byteloads_subpkt_multiflow/"
REL_PATH_TO_EXP_FAMILY_FASTPACE = "FCT_Subpkt_Byteloads_subpkt_multiflow_fastpace/"

class SimOutputStats:
    def __init__(self, num_creditreq_pkts_0_to_1, num_credit_pkts_1_to_0, num_data_pkts_0_to_1):
        self.num_creditreq_pkts_0_to_1 = num_creditreq_pkts_0_to_1
        self.num_credit_pkts_1_to_0 = num_credit_pkts_1_to_0
        self.num_data_pkts_0_to_1 = num_data_pkts_0_to_1
        self.total_overheads_B = self.num_creditreq_pkts_0_to_1 * CREDITREQ_PKT_OVERHEAD_B + self.num_credit_pkts_1_to_0 * CREDIT_PKT_OVERHEAD_B + self.num_data_pkts_0_to_1 * DATA_PKT_OVERHEAD_B

    def pretty_print(self):
        print(f"Num Credit Req Pkts: {self.num_creditreq_pkts_0_to_1}")
        print(f"Num Credit Pkts: {self.num_credit_pkts_1_to_0}")
        print(f"Num Data Pkts: {self.num_data_pkts_0_to_1}")
        print(f"Total Overheads (B): {self.total_overheads_B}")
    

def look_through_sim_stdout(filepath):
    num_creditreq_pkts_0_to_1 = 0
    num_credit_pkts_1_to_0 = 0
    num_data_pkts_0_to_1 = 0

    with open(filepath, 'r') as file:
        for line in file:
            if CR_0_to_1_SUBSTRING in line:
                num_creditreq_pkts_0_to_1 += 1
            elif C_1_to_0_SUBSTRING in line:
                num_credit_pkts_1_to_0 += 1
            elif D_0_to_1_SUBSTRING in line:
                num_data_pkts_0_to_1 += 1
            else:
                pass

            num_matching_substrings = sum(substr in line for substr in SUBSTR_LIST)
            if num_matching_substrings > 1:
                print(line)
                assert(False)
    
    return SimOutputStats(num_creditreq_pkts_0_to_1, num_credit_pkts_1_to_0, num_data_pkts_0_to_1) 


'''
======== 1 FLO SUBPKT EXPERIMENTS ========
'''
def proc_1flo_4B_per_bload_sim_outputs(): 
    sim_output_4B_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY + "ssird_1flo-10000#-4B-1us_subpkt_multiflow_stdout.out"
    sim_4B_bload_stats = look_through_sim_stdout(sim_output_4B_byteloads_path)
    print("4B per byteload:")
    sim_4B_bload_stats.pretty_print()

def proc_1flo_4KB_per_bload_sim_outputs():
    sim_output_4KB_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY + "ssird_1flo-10#-4000B-1000us_subpkt_multiflow_stdout.out"
    sim_4KB_bload_stats = look_through_sim_stdout(sim_output_4KB_byteloads_path)
    print("4KB per byteload")
    sim_4KB_bload_stats.pretty_print()

def proc_1flo_subpkt_exp_sim_outputs():
    # 4B per byteload:
    # Num Credit Req Pkts: 10000
    # Num Credit Pkts: 10000
    # Num Data Pkts: 9994
    # Total Overheads (B): 2479520
    # -----
    # 4KB per byteload
    # Num Credit Req Pkts: 10
    # Num Credit Pkts: 30
    # Num Data Pkts: 30
    # Total Overheads (B): 5760

    proc_1flo_4B_per_bload_sim_outputs()
    print("-----")
    proc_1flo_4KB_per_bload_sim_outputs()

'''
======== 10 FLO SUBPKT EXPERIMENTS ========
'''
def proc_10flo_4B_per_bload_sim_outputs(): 
    sim_output_4B_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY + "ssird_10flo-10000#-4B-1us_subpkt_multiflow_stdout.out"
    sim_4B_bload_stats = look_through_sim_stdout(sim_output_4B_byteloads_path)
    print("4B per byteload:")
    sim_4B_bload_stats.pretty_print()

def proc_10flo_4KB_per_bload_sim_outputs():
    sim_output_4KB_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY + "ssird_10flo-10#-4000B-1000us_subpkt_multiflow_stdout.out"
    sim_4KB_bload_stats = look_through_sim_stdout(sim_output_4KB_byteloads_path)
    print("4KB per byteload")
    sim_4KB_bload_stats.pretty_print()

def proc_10flo_subpkt_exp_sim_outputs():
    # output:
    # 4B per byteload:
    # Num Credit Req Pkts: 100000
    # Num Credit Pkts: 100000
    # Num Data Pkts: 99947
    # Total Overheads (B): 24795760
    # -----
    # 4KB per byteload
    # Num Credit Req Pkts: 100
    # Num Credit Pkts: 300
    # Num Data Pkts: 300
    # Total Overheads (B): 57600

    proc_10flo_4B_per_bload_sim_outputs()
    print("-----")
    proc_10flo_4KB_per_bload_sim_outputs()


'''
======== 15 FLO SUBPKT FASTPACE EXPERIMENTS ========
'''

def process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, title_addendum=""):
    assert(len(set([
        len(num_byteloads_list),
        len(byteload_size_B_list),
        len(inter_byteload_period_us_list)
    ])) == 1)
    num_experiments = len(num_byteloads_list)

    nw_overheads_B_list = [] 
    for i in range(0, num_experiments):
        experiment_name = dale_experiment_rig.Experiment.get_experiment_name(num_flows, num_byteloads_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i]) + title_addendum
        sim_output_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY_FASTPACE + f"ssird_{experiment_name}_stdout.out" 
        sim_stats = look_through_sim_stdout(sim_output_path)
        nw_overheads_B_list.append(sim_stats.total_overheads_B)
        print(f"{byteload_size_B_list[i]}B per byteload:")
        sim_stats.pretty_print()
        print("---")

    return nw_overheads_B_list

def proc_15flo_4B_per_bload_sim_outputs(): 
    experiment_name = dale_experiment_rig.Experiment.get_experiment_name(num_flows=15, num_byteloads=10000, byteload_size_B=4, inter_byteload_period_us=0.01)
    sim_output_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY_FASTPACE + f"ssird_{experiment_name}_subpkt_multiflow_fastpace_stdout.out" #"ssird_15flo-10000#-4B-10ns_subpkt_multiflow_fastpace_stdout.out"
    sim_stats = look_through_sim_stdout(sim_output_path)
    print("4B per byteload:")
    sim_stats.pretty_print()

def proc_15flo_4KB_per_bload_sim_outputs():
    sim_output_4KB_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY_FASTPACE + "ssird_15flo-10#-4000B-10000ns_subpkt_multiflow_fastpace_stdout.out"
    sim_4KB_bload_stats = look_through_sim_stdout(sim_output_4KB_byteloads_path)
    print("4KB per byteload")
    sim_4KB_bload_stats.pretty_print()

def proc_15flo_subpkt_exp_sim_outputs():
    # proc_15flo_4B_per_bload_sim_outputs()
    # print("-----")
    # proc_15flo_4KB_per_bload_sim_outputs()
    
    title_addendum = "_subpkt_multiflow_fastpace"
    num_byteloads_list = [10000, 1000, 100, 10]
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [0.01, 0.1, 1.0, 10.0]
    nw_overheads_theoretical_15flo_B_list = process_ssird_sim_outputs(15, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, title_addendum)
    nw_overheads_measured_15flo_B_list = [4337187.5, 1379893.75, 600348.75, 121467.5]
    measured_vs_theoretical_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_15flo_B_list, nw_overheads_theoretical_15flo_B_list)]
    print(measured_vs_theoretical_ratio)

if __name__ == "__main__":
    # proc_1flo_subpkt_exp_sim_outputs()
    # proc_10flo_subpkt_exp_sim_outputs()

    # analysing 15 flow subpkt experiment (fastpace)
    proc_15flo_subpkt_exp_sim_outputs()




