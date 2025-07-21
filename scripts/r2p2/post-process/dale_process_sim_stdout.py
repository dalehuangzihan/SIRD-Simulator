import dale_experiment_rig

CR_PKT_SUBSTRING = "Forwarded standalone grant_request asking for"
C_PKT_SUBSTRING = ">>>>Sending credit to:"
D_PKT_SUBSTRING = "Sending pkt of msg"
SUBSTR_LIST = [CR_PKT_SUBSTRING, C_PKT_SUBSTRING, D_PKT_SUBSTRING]
CREDITREQ_PKT_OVERHEAD_B = 84
CREDIT_PKT_OVERHEAD_B = 84
DATA_PKT_OVERHEAD_B = 80

# PATH_TO_SIM_OUTPUTS = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/scripts/r2p2/coord/outputs/"
PATH_TO_SIM_OUTPUTS = "/data/dh1723/SIRD-Simulator/scripts/r2p2/coord/outputs/" # NOTE: use this for batch1 server
REL_PATH_TO_EXP_FAMILY = "FCT_Subpkt_Byteloads_subpkt_multiflow/"
REL_PATH_TO_EXP_FAMILY_FASTPACE = "FCT_Subpkt_Byteloads_subpkt_multiflow_fastpace/"
REL_PATH_TO_EXP_FAMILY_FASTPACE_EXTENDED = "FCT_Subpkt_Byteloads_subpkt_multiflow_fastpace_extended/"
REL_PATH_TO_EXP_FAMILY_SLOWPACE = "FCT_Subpkt_Byteloads_subpkt_multiflow_slowpace/"

class SimOutputStats:
    def __init__(self, num_creditreq_pkts, num_credit_pkts, num_data_pkts):
        self.num_creditreq_pkts_0_to_1 = num_creditreq_pkts
        self.num_credit_pkts_1_to_0 = num_credit_pkts
        self.num_data_pkts_0_to_1 = num_data_pkts
        self.total_overheads_B = self.num_creditreq_pkts_0_to_1 * CREDITREQ_PKT_OVERHEAD_B + self.num_credit_pkts_1_to_0 * CREDIT_PKT_OVERHEAD_B + self.num_data_pkts_0_to_1 * DATA_PKT_OVERHEAD_B

    def pretty_print(self):
        print(f"Num Credit Req Pkts: {self.num_creditreq_pkts_0_to_1}")
        print(f"Num Credit Pkts: {self.num_credit_pkts_1_to_0}")
        print(f"Num Data Pkts: {self.num_data_pkts_0_to_1}")
        print(f"Total Overheads (B): {self.total_overheads_B}")
    

def look_through_sim_stdout(filepath):
    num_creditreq_pkts = 0
    num_creditreq_pkts_0_to_1 = 0
    num_credit_pkts = 0
    num_credit_pkts_1_to_0 = 0
    num_data_pkts = 0
    num_data_pkts_0_to_1 = 0

    with open(filepath, 'r') as file:
        for line in file:
            if CR_PKT_SUBSTRING in line:
                num_creditreq_pkts += 1
                if f"0 {CR_PKT_SUBSTRING}" in line: num_creditreq_pkts_0_to_1 += 1

            elif C_PKT_SUBSTRING in line:
                num_credit_pkts += 1
                if f"1 {C_PKT_SUBSTRING}" in line: num_credit_pkts_1_to_0 += 1

            elif D_PKT_SUBSTRING in line:
                num_data_pkts += 1
                if f"0 {D_PKT_SUBSTRING}" in line: num_data_pkts_0_to_1 += 1

            else:
                pass

            num_matching_substrings = sum(substr in line for substr in SUBSTR_LIST)
            if num_matching_substrings > 1:
                print(line)
                assert(False)

    sim_output_stats_overall_nw = SimOutputStats(num_creditreq_pkts, num_credit_pkts, num_data_pkts) 
    sim_output_stats_p2p_data_transf_only = SimOutputStats(num_creditreq_pkts_0_to_1, num_credit_pkts_1_to_0, num_data_pkts_0_to_1)
    return sim_output_stats_overall_nw, sim_output_stats_p2p_data_transf_only


'''
======== 1 FLO SUBPKT EXPERIMENTS ========
'''
def proc_1flo_4B_per_bload_sim_outputs(): 
    sim_output_4B_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY + "ssird_1flo-10000#-4B-1us_subpkt_multiflow_stdout.out"
    sim_4B_bload_stats, _ = look_through_sim_stdout(sim_output_4B_byteloads_path)
    print("4B per byteload:")
    sim_4B_bload_stats.pretty_print()

def proc_1flo_4KB_per_bload_sim_outputs():
    sim_output_4KB_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY + "ssird_1flo-10#-4000B-1000us_subpkt_multiflow_stdout.out"
    sim_4KB_bload_stats, _ = look_through_sim_stdout(sim_output_4KB_byteloads_path)
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
    sim_4B_bload_stats, _= look_through_sim_stdout(sim_output_4B_byteloads_path)
    print("4B per byteload:")
    sim_4B_bload_stats.pretty_print()

def proc_10flo_4KB_per_bload_sim_outputs():
    sim_output_4KB_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY + "ssird_10flo-10#-4000B-1000us_subpkt_multiflow_stdout.out"
    sim_4KB_bload_stats, _ = look_through_sim_stdout(sim_output_4KB_byteloads_path)
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

def proc_10flo_subpkt_exp_sim_outputs_slowpace():
    print("\n--- 10 FLO SLOWPACE: ---") 
    title_addendum = "_subpkt_multiflow_slowpace"
    num_byteloads_list = [10000, 1000, 100, 10]
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [1, 10, 100, 1000]
    nw_overheads_theoretical_15flo_B_list = process_ssird_sim_outputs(10, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, REL_PATH_TO_EXP_FAMILY_SLOWPACE, title_addendum)
    nw_overheads_measured_15flo_B_list = [33335286.23, 3463891.25, 475893.74, 82826.25]
    measured_vs_theoretical_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_15flo_B_list, nw_overheads_theoretical_15flo_B_list)]
    print(measured_vs_theoretical_ratio)


'''
======== 15 FLO SUBPKT FASTPACE EXPERIMENTS ========
'''

def process_ssird_sim_outputs(num_flows, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, rel_path_to_exp_family, title_addendum=""):
    assert(len(set([
        len(num_byteloads_list),
        len(byteload_size_B_list),
        len(inter_byteload_period_us_list)
    ])) == 1)
    num_experiments = len(num_byteloads_list)

    nw_overheads_B_list = [] 
    for i in range(0, num_experiments):
        experiment_name = dale_experiment_rig.Experiment.get_experiment_name(num_flows, num_byteloads_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i]) + title_addendum
        sim_output_path = PATH_TO_SIM_OUTPUTS + rel_path_to_exp_family + f"ssird_{experiment_name}_stdout.out" 
        sim_stats_nw_overall, sim_stats_p2p_only = look_through_sim_stdout(sim_output_path)
        nw_overheads_B_list.append(sim_stats_nw_overall.total_overheads_B)
        print(f"{byteload_size_B_list[i]}B per byteload:")
        print(f"* NW Overall:")
        sim_stats_nw_overall.pretty_print()
        print(f"* P2P Only:")
        sim_stats_p2p_only.pretty_print()
        print("---")

    return nw_overheads_B_list

def proc_15flo_4B_per_bload_sim_outputs(): 
    experiment_name = dale_experiment_rig.Experiment.get_experiment_name(num_flows=15, num_byteloads=10000, byteload_size_B=4, inter_byteload_period_us=0.01)
    sim_output_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY_FASTPACE + f"ssird_{experiment_name}_subpkt_multiflow_fastpace_stdout.out" #"ssird_15flo-10000#-4B-10ns_subpkt_multiflow_fastpace_stdout.out"
    sim_stats, _ = look_through_sim_stdout(sim_output_path)
    print("4B per byteload:")
    sim_stats.pretty_print()

def proc_15flo_4KB_per_bload_sim_outputs():
    sim_output_4KB_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY_FASTPACE + "ssird_15flo-10#-4000B-10000ns_subpkt_multiflow_fastpace_stdout.out"
    sim_4KB_bload_stats, _ = look_through_sim_stdout(sim_output_4KB_byteloads_path)
    print("4KB per byteload")
    sim_4KB_bload_stats.pretty_print()

def proc_15flo_subpkt_exp_sim_outputs_fastpace():
    print("\n--- 15 FLO FASTPACE: ---")
    title_addendum = "_subpkt_multiflow_fastpace"
    num_byteloads_list = [10000, 1000, 100, 10]
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [0.01, 0.1, 1.0, 10.0]
    nw_overheads_theoretical_15flo_B_list = process_ssird_sim_outputs(15, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, REL_PATH_TO_EXP_FAMILY_FASTPACE, title_addendum)
    nw_overheads_measured_15flo_B_list = [4337187.5, 1379893.75, 600348.75, 121467.5]
    measured_vs_theoretical_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_15flo_B_list, nw_overheads_theoretical_15flo_B_list)]
    print(measured_vs_theoretical_ratio)

def proc_15flo_subpkt_exp_sim_outputs_slowpace():
    print("\n--- 15 FLO SLOWPACE: ---") 
    title_addendum = "_subpkt_multiflow_slowpace"
    num_byteloads_list = [10000, 1000, 100, 10]
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [1, 10, 100, 1000]
    nw_overheads_theoretical_15flo_B_list = process_ssird_sim_outputs(15, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, REL_PATH_TO_EXP_FAMILY_SLOWPACE, title_addendum)
    nw_overheads_measured_15flo_B_list = [49931017.46, 5123891.25, 641893.75, 124286.25]
    measured_vs_theoretical_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_15flo_B_list, nw_overheads_theoretical_15flo_B_list)]
    print(measured_vs_theoretical_ratio)


def proc_15flow_subpkt_exp_sim_outputs_fastpace_extended():
    # INFO:__main__:Total Flow Size (Bytes): 40000
    # INFO:__main__:Total Injection Period (us): 100.0
    # INFO:__main__:Byteload Size (Bytes): [4, 40, 400, 4000, 40000]
    # INFO:__main__:Num Byteloads: [10000, 1000, 100, 10, 1]
    # INFO:__main__:Intervals (us): [0.01, 0.1, 1.0, 10.0, 100.0]
    # INFO:__main__:Num flows: 15
    # DEBUG:__main__:Flow start times (us): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    # INFO:__main__:Gdpt Gbps theoretical: [48.0, 48.0, 48.0, 48.0, 48.0]
    # INFO:__main__:Gdpt Gbps measured (SSIRD): [48.00448044770111, 48.044844844664645, 48.452525252273034, 52.97777777769212, -1]
    # INFO:__main__:Gdpt Gbps measured (DCTCP): [48.00448044770111, 48.044844844664645, 48.452525252273034, 52.97777777769212, -1]
    # DEBUG:__main__:Gdpt Gbps measured per flow (SSIRD): [[3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089], [3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982], [3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343], [3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826], [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]]
    # DEBUG:__main__:Gdpt Gbps measured per flow (DCTCP): [[3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089, 3.199999999977089], [3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982, 3.1999999999879982], [3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343, 3.199999999983343], [3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826, 3.199999999994826], [None, None, None, None, None, None, None, None, None, None, None, None, None, None, None]]
    # INFO:__main__:* Sim duration (SSIRD): [0.02, 0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* Sim duration (DCTCP): [0.02, 0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* SSIRD FCT: [[0.0003420990000009283, 0.00034547899999992637, 0.00034886500000119725, 0.00035225100000069176, 0.00035563600000010354, 0.0003590220000013744, 0.0003624080000008689, 0.00036579400000036344, 0.0003691800000016343, 0.00037256600000112883, 0.00037595200000062334, 0.00037933800000011786, 0.00038272400000138873, 0.00038611000000088325, 0.00038949600000037776], [0.00010683200000016768, 0.00011021100000085937, 0.00011359700000035389, 0.00011698300000162476, 0.00012036900000111928, 0.0001237550000006138, 0.0001271410000001083, 0.00013052700000137918, 0.0001339130000008737, 0.0001372990000003682, 0.00014068499999986273, 0.0001440710000011336, 0.0001474570000006281, 0.0001508420000000399, 0.00015422800000131076], [0.00010167800000004945, 0.00010171600000141723, 0.00010175400000100865, 0.00010179300000068281, 0.00010183100000027423, 0.00010186999999994839, 0.00010190800000131617, 0.00010194600000090759, 0.00010198500000058175, 0.00010202300000017317, 0.00010206200000162369, 0.00010210000000121511, 0.00010213800000080653, 0.00010217700000048069, 0.00010513900000042042], [9.307800000080135e-05, 9.815200000140578e-05, 9.849800000161224e-05, 9.883700000123952e-05, 9.917700000094953e-05, 9.951600000057681e-05, 9.985500000020409e-05, 0.00010019400000160772, 0.000100533000001235, 0.00010087300000094501, 0.00010121200000057229, 0.00010155100000019956, 0.0001018900000016032, 0.00010222900000123047, 0.00010294900000040741], [1.1102000000207113e-05, 1.4481000000898803e-05, 1.7867000000393318e-05, 2.1252999999887834e-05, 2.4639000001158706e-05, 2.8025000000653222e-05, 3.141100000014774e-05, 3.479700000141861e-05, 3.8183000000913125e-05, 4.156900000040764e-05, 4.4954999999902157e-05, 4.834100000117303e-05, 5.1727000000667545e-05, 5.511200000007932e-05, 5.849800000135019e-05]]
    # INFO:__main__:* DCTCP FCT: [[0.018869601000000458, 0.01886961300000145, 0.01886962600000075, 0.01886963900000005, 0.018869652000001125, 0.018869665000000424, 0.018869677000001417, 0.018869690000000716, 0.018869703000000015, 0.01886971600000109, 0.01886972900000039, 0.018869741000001383, 0.018869754000000682, 0.018869766999999982, 0.018869780000001057], [0.0018871410000009803, 0.0018871530000001968, 0.0018871660000012724, 0.0018871790000005717, 0.001887191999999871, 0.0018872050000009466, 0.0018872170000001631, 0.0018872300000012387, 0.001887243000000538, 0.0018872560000016136, 0.001887269000000913, 0.0018872810000001294, 0.001887294000001205, 0.0018873070000005043, 0.00188732000000158], [0.00019131400000027554, 0.00019135199999986696, 0.00019139000000123474, 0.00019142800000082616, 0.00019146700000050032, 0.00019150500000009174, 0.00019154300000145952, 0.00019158100000105094, 0.0001916200000007251, 0.00019165800000031652, 0.0001921230000014873, 0.00019216100000107872, 0.00019219900000067014, 0.00019223700000026156, 0.00019227599999993572], [9.296200000008525e-05, 9.330000000140615e-05, 9.363900000103342e-05, 9.39780000006607e-05, 9.431700000028798e-05, 9.465500000160887e-05, 9.499400000123615e-05, 9.533300000086342e-05, 9.56720000004907e-05, 9.601000000003523e-05, 9.634900000143887e-05, 9.668800000106614e-05, 9.702600000061068e-05, 9.736500000023796e-05, 9.770399999986523e-05], [5.998000000673187e-06, 9.372000000951175e-06, 1.2747000001311903e-05, 1.6121999999896275e-05, 1.9497000000257003e-05, 2.287100000053499e-05, 2.624600000089572e-05, 2.9621000001256448e-05, 3.2996000001617176e-05, 3.637000000011881e-05, 3.9745000000479536e-05, 4.3120000000840264e-05, 4.649400000111825e-05, 4.986900000147898e-05, 5.324400000006335e-05]]

    print("\n--- 15 FLO SUBPKT FASTPACE (EXTENDED): ---") 
    title_addendum = "_subpkt_multiflow_fastpace_extended"
    num_byteloads_list = [10000, 1000, 100, 10, 1]
    byteload_size_B_list = [4, 40, 400, 4000, 40000]
    inter_byteload_period_us_list = [0.01, 0.1, 1.0, 10.0, 100.0]
    nw_overheads_theoretical_15flo_B_list = process_ssird_sim_outputs(15, num_byteloads_list, byteload_size_B_list, inter_byteload_period_us_list, REL_PATH_TO_EXP_FAMILY_FASTPACE_EXTENDED, title_addendum)
    nw_overheads_measured_15flo_B_list = [4337187.5, 1379893.75, 600348.75, 121467.5, 73920.0]
    measured_vs_theoretical_ratio = [round(m/t, 4) for m, t in zip(nw_overheads_measured_15flo_B_list, nw_overheads_theoretical_15flo_B_list)]
    print(measured_vs_theoretical_ratio)

if __name__ == "__main__":
    # proc_1flo_subpkt_exp_sim_outputs()
    # proc_10flo_subpkt_exp_sim_outputs()

    # analysing 10 flow subpkt experiment (slowpace)
    proc_10flo_subpkt_exp_sim_outputs_slowpace()

    # analysing 15 flow subpkt experiment (fastpace)
    proc_15flo_subpkt_exp_sim_outputs_slowpace()
    proc_15flo_subpkt_exp_sim_outputs_fastpace()
    proc_15flow_subpkt_exp_sim_outputs_fastpace_extended()



