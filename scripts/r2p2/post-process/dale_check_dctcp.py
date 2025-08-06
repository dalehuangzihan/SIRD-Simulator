

def check_amt_data_sent_per_flowid(filepath):

    dict = {}
    with open(filepath, 'r') as file:
        for line in file:
            if f"0 B: FullTcpAgent::send_much():" in line:
                tokens_list = line.split(" ")
                idx_of_flow_id = tokens_list.index("flow_id=") + 1
                flow_id = int(tokens_list[idx_of_flow_id])
                idx_of_sent_amt_data = tokens_list.index("sent_amt_data=") + 1
                sent_amt_data = int(tokens_list[idx_of_sent_amt_data])
                if flow_id not in dict:
                    dict[flow_id] = sent_amt_data
                else:
                    dict[flow_id] += sent_amt_data
    return dict


if __name__ == "__main__":
    parent_dir = "/data/dh1723/SIRD-Simulator/scripts/r2p2/coord/outputs/Poisson_Intervals_poisson_50flo_2GbpsFlo_dctcp_test/"
    file_name = "DCTCP-50_50flo-2Gbps-2025-08-06T_14-58-27Z_poisson_50flo_2GbpsFlo_dctcp_test_stdout.out"
                 
    dict = check_amt_data_sent_per_flowid(parent_dir + file_name) 
    print(dict)
