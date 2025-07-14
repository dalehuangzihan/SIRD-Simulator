import sys
import csv
import statistics

PATH_TO_SCRIPTS_R2P2 = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/scripts/r2p2/"
PATH_TO_POSTPROC = f"{PATH_TO_SCRIPTS_R2P2}post-process/"
PATH_TO_SIM_RESULTS = f"{PATH_TO_SCRIPTS_R2P2}coord/results/"

# Common experiment param; value is meaningful only when req_interval_distr is not 'manual'
CLIENT_INJECTION_RATE_GBPS = "60"
DCTCP_ECN_THRESH = 50

SSIRD_PROTO_NAME = 'SSIRD'
DCTCP_PROTO_NAME = 'DCTCP'

AGGR = "aggr"
HOST = "host"
TOR = "tor"

class QmonResults:
    def __init__(self, nw_elem, src, dst, timestamps_list, throughput_gbps_list, queueing_KB_list):
        self.nw_elem = nw_elem
        self.src = src
        self.dst = dst
        self.timestamps_list = timestamps_list
        self.throughput_gbps_list = throughput_gbps_list
        self.queueing_KB_list = queueing_KB_list
    
    def get_avg_thrpt_gbps(self,):
        return statistics.mean(self.throughput_gbps_list)

    def get_avg_qing_KB(self):
        # TODO
        pass

def get_qts_results_from_csv(nw_elem, src, dst, path_to_qts_csv, timestamp_cutoff_s=None):
    with open(path_to_qts_csv, newline='') as file:
        reader = csv.reader(file, delimiter=',')
        headings = next(reader)

        timestamps_list = []
        throughput_gbps_list = []
        queueing_KB_list = []
        for row in reader:
            if timestamp_cutoff_s and float(row[0]) > timestamp_cutoff_s:
                break
            timestamps_list.append(float(row[0]))
            throughput_gbps_list.append(float(row[1]))
            queueing_KB_list.append(float(row[2]))

        return QmonResults(nw_elem, src, dst, timestamps_list, throughput_gbps_list, queueing_KB_list) 

def get_qts_result(proto, nw_elem, src, dst, num_flows, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, timestamp_cutoff_s=None, title_addendum=""):
    if proto.upper() == SSIRD_PROTO_NAME: 
        path_to_qts_results = f"{PATH_TO_SIM_RESULTS}{SSIRD_PROTO_NAME}-{num_flows}flo-{num_byteloads_per_flow}#-{byteload_size_B}B-{inter_byteload_period_us}us{title_addendum}/data/{SSIRD_PROTO_NAME}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

    elif proto.upper() == DCTCP_PROTO_NAME:
        path_to_qts_results = f"{PATH_TO_SIM_RESULTS}{DCTCP_PROTO_NAME}-{DCTCP_ECN_THRESH}-{num_flows}flo-{num_byteloads_per_flow}#-{byteload_size_B}B-{inter_byteload_period_us}us{title_addendum}/data/{DCTCP_PROTO_NAME}-{DCTCP_ECN_THRESH}/{CLIENT_INJECTION_RATE_GBPS}/output/qts/{nw_elem}/qts_{src}_{dst}.csv"

    else:
        print(f"ERROR: proto name '{proto}' unrecognised!")

    return get_qts_results_from_csv(nw_elem, src, dst, path_to_qts_results, timestamp_cutoff_s)


if __name__ == "__main__":
   
    num_flows = 2
    num_byteloads_per_flow_list = [10, 10, 10, 10] # should be [10000, 1000, 100, 10] but there was a naming bug in the experiment
    byteload_size_B_list = [4, 40, 400, 4000]
    inter_byteload_period_us_list = [1, 10, 100, 1000]
    timestamp_cutoff_us_list = [0.020006, 0.009998, 0.009913, 0.009008]

    num_experiments = len(num_byteloads_per_flow_list)
    assert(len(byteload_size_B_list) == num_experiments)
    assert(len(inter_byteload_period_us_list) == num_experiments)

    ssird_qts_results_list = []
    dctcp_qts_results_list = []
    for i in range(0, num_experiments):
        ssird_subpkt_result = get_qts_result(SSIRD_PROTO_NAME, HOST, "host_0", "tor_4", num_flows, num_byteloads_per_flow_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i], timestamp_cutoff_us_list[i], title_addendum="_subpkt_multiflow") 
        dctcp_subpkt_result = get_qts_result(DCTCP_PROTO_NAME, HOST, "host_0", "tor_4", num_flows, num_byteloads_per_flow_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i], timestamp_cutoff_us_list[i], title_addendum="_subpkt_multiflow") 
        ssird_qts_results_list.append(ssird_subpkt_result)
        dctcp_qts_results_list.append(dctcp_subpkt_result)

    ssird_thrpt_gbps_list = [x.get_avg_thrpt_gbps() for x in ssird_qts_results_list]
    dctcp_thrpt_gbps_list = [x.get_avg_thrpt_gbps() for x in dctcp_qts_results_list]
    diff_thrpt_gbps_list = [s - d for s, d in zip(ssird_thrpt_gbps_list, dctcp_thrpt_gbps_list)]
    print(ssird_thrpt_gbps_list)
    print(dctcp_thrpt_gbps_list)
    print(diff_thrpt_gbps_list)

    # ---
    # ssird_subpkt_result = get_qts_result(SSIRD_PROTO_NAME, HOST, "host_0", "tor_4", 2, 10, 4, 1, 0.020006, title_addendum="_subpkt_multiflow") 
    # dctcp_subpkt_result = get_qts_result(DCTCP_PROTO_NAME, HOST, "host_0", "tor_4", 2, 10, 4, 1, 0.020006, title_addendum="_subpkt_multiflow") 
    # print(ssird_subpkt_result.get_avg_thrpt_gbps())
    # print(dctcp_subpkt_result.get_avg_thrpt_gbps())

    # ---
    # ssird_subpkt_2flo_10bload_4B_1us_qmon_path = f"{PATH_TO_SIM_RESULTS}SSIRD-2flo-10#-4B-1us_subpkt_multiflow/data/SSIRD/60/output/qts/host/qts_host_0_tor_4.csv"
    # ssird_subpkt_2flo_10bload_4B_1us_qmon_result = get_qmon_results_from_csv(HOST, "host_0", "tor_4", ssird_subpkt_2flo_10bload_4B_1us_qmon_path, 0.020006)
    # print(ssird_subpkt_2flo_10bload_4B_1us_qmon_result.get_avg_thrpt_gbps())
    # dctcp_subpkt_2flo_10bload_4B_1us_qmon_path = f"{PATH_TO_SIM_RESULTS}DCTCP-50-2flo-10#-4B-1us_subpkt_multiflow/data/DCTCP-50/60/output/qts/host/qts_host_0_tor_4.csv"
    # dctcp_subpkt_2flo_10bload_4B_1us_qmon_result = get_qmon_results_from_csv(HOST, "host_0", "tor_4", dctcp_subpkt_2flo_10bload_4B_1us_qmon_path, 0.020006)
    # print(dctcp_subpkt_2flo_10bload_4B_1us_qmon_result.get_avg_thrpt_gbps())