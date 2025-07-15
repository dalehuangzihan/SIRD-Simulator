
CR_0_to_1_SUBSTRING = "0 Forwarded standalone grant_request asking for"
C_1_to_0_SUBSTRING = "1 >>>>Sending credit to: 0"
D_0_to_1_SUBSTRING = "0 Sending pkt of msg"

SUBSTR_LIST = [CR_0_to_1_SUBSTRING, C_1_to_0_SUBSTRING, D_0_to_1_SUBSTRING]

class SimOutputStats:
    def __init__(self, num_creditreq_pkts_0_to_1, num_credit_pkts_1_to_0, num_data_pkts_0_to_1):
        self.num_creditreq_pkts_0_to_1 = num_creditreq_pkts_0_to_1
        self.num_credit_pkts_1_to_0 = num_credit_pkts_1_to_0
        self.num_data_pkts_0_to_1 = num_data_pkts_0_to_1

    def pretty_print(self):
        print(f"Num Credit Req Pkts: {self.num_creditreq_pkts_0_to_1}")
        print(f"Num Credit Pkts: {self.num_credit_pkts_1_to_0}")
        print(f"Num Data Pkts: {self.num_data_pkts_0_to_1}")

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
    
            
if __name__ == "__main__":

    PATH_TO_SIM_OUTPUTS = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/scripts/r2p2/coord/outputs/"
    REL_PATH_TO_EXP_FAMILY = "FCT_Subpkt_Byteloads_subpkt_multiflow/"

    sim_output_4B_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY + "ssird_1flo-10000#-4B-1us_subpkt_multiflow_stdout.out"
    sim_output_4KB_byteloads_path = PATH_TO_SIM_OUTPUTS + REL_PATH_TO_EXP_FAMILY + "ssird_1flo-10#-4000B-1000us_subpkt_multiflow_stdout.out"

    sim_4B_bload_stats = look_through_sim_stdout(sim_output_4B_byteloads_path)
    sim_4KB_bload_stats = look_through_sim_stdout(sim_output_4KB_byteloads_path)

    print("4B per byteload:")
    sim_4B_bload_stats.pretty_print()

    print("---")

    print("4KB per byteload")
    sim_4KB_bload_stats.pretty_print()

    # output:
    # 4B per byteload:
    # Num Credit Req Pkts: 10000
    # Num Credit Pkts: 10000
    # Num Data Pkts: 9994
    # ---
    # 4KB per byteload
    # Num Credit Req Pkts: 10
    # Num Credit Pkts: 30
    # Num Data Pkts: 30





