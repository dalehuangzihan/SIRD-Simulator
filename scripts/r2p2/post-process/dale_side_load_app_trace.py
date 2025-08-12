import dale_experiment_rig

def side_load_incast_3to1_8flo_1560B_1000ns_exp():
    ''' --- Side-load & analyse existing app trace file ---'''
    proto = dale_experiment_rig.SSIRD_PROTO_NAME

    num_of_experiments = 1

    src_dst_pairs_list = [(1,0), (2,0), (3,0)]
    num_flows = 8
    num_byteloads_list = [1000]
    byteload_size_B_list = [1560]
    target_mean_byteload_interval_nanosec_list = [1000]

    target_flow_rate_gbps = (byteload_size_B_list[0] * 8) / (target_mean_byteload_interval_nanosec_list[0] * pow(10,-9)) * pow(10, -9)

    app_trace_paths_list = [
        "/data/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-8flo-12Gbps-1560B-1000ns-2025-08-12T_10-09-35Z_incast_poisson_3to1_8flo_1560B_1us_99pt84Gbps/data/SSIRD/60/applications_trace.str",
    ]

    # Load flow spec for each experiment from saved json: 
    flow_start_times_us_list, flow_spec_list = dale_experiment_rig.FlowSpec.parse_flow_specs_json_file(dale_experiment_rig.SAVED_FLOW_SPECS_JSON_PATH, "poisson_flow_incast_experiment_3to1_8flo-12Gbps-1560B-1000ns-2025-08-12T_10-08-57Z.log")
    assert(len(flow_start_times_us_list) == len(flow_spec_list) and len(flow_spec_list) == num_flows)
    flow_spec_list_list = [flow_spec_list]
    flow_start_times_us_list_list = [flow_start_times_us_list]

    exp_metrics, flow_stats_dict = dale_experiment_rig.ExperimentGroup.process_side_loaded_results(proto, src_dst_pairs_list, num_flows, flow_spec_list_list, target_flow_rate_gbps, app_trace_paths_list)

    srcdst_to_flowstatslist_dict = {}

    for key, flow_stat in flow_stats_dict.items():
        # initialise vals (empty lists) in srcdst_to_flowstatslist_dict
        src_or_dst_1, src_or_dst_2, flow_id = key
        srcdst_to_flowstatslist_dict[(src_or_dst_1, src_or_dst_2)] = []

    for key, flow_stat in flow_stats_dict.items():
        # append to vals (lists) in scrdst_to_flowstatslist_dict
        src_or_dst_1, src_or_dst_2, flow_id = key
        srcdst_to_flowstatslist_dict[(src_or_dst_1, src_or_dst_2)].append(flow_stat)

    print("======")
    for srcdst, flow_stat_list in srcdst_to_flowstatslist_dict.items():
        print(f"srcdst={srcdst}")
        for flow_stat in flow_stat_list:
            print(f"flow_id={flow_stat.flow_id}, flow_size_B={flow_stat.total_data_bytes_recv_B}, FCT(s)={flow_stat.end_time_s - flow_stat.start_time_s}")

def side_load_incast_3to1_8flo_1560B_1000ns_same_flow_interarr():
    ''' --- Side-load & analyse existing app trace file ---'''
    proto = dale_experiment_rig.SSIRD_PROTO_NAME

    num_of_experiments = 1

    src_dst_pairs_list = [(1,0), (2,0), (3,0)]
    num_flows = 8
    num_byteloads_list = [1000]
    byteload_size_B_list = [1560]
    target_mean_byteload_interval_nanosec_list = [1000]

    target_flow_rate_gbps = (byteload_size_B_list[0] * 8) / (target_mean_byteload_interval_nanosec_list[0] * pow(10,-9)) * pow(10, -9)

    app_trace_paths_list = [
        "/data/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-8flo-12Gbps-1560B-1000ns-2025-08-12T_16-38-55Z_incast_poisson_3to1_8flo_1560B_1us_99pt84Gbps_same_flo_interarr/data/SSIRD/60/applications_trace.str",
    ]

    # Load flow spec for each experiment from saved json: 
    flow_start_times_us_list, flow_spec_list = dale_experiment_rig.FlowSpec.parse_flow_specs_json_file(dale_experiment_rig.SAVED_FLOW_SPECS_JSON_PATH, "poisson_flow_incast_experiment_3to1_8flo-12Gbps-1560B-1000ns-2025-08-12T_16-38-20Z_incast_poisson_3to1_8flo_1560B_1us_99pt84Gbps_same_flo_interarr.log")
    assert(len(flow_start_times_us_list) == len(flow_spec_list) and len(flow_spec_list) == num_flows)
    flow_spec_list_list = [flow_spec_list]
    flow_start_times_us_list_list = [flow_start_times_us_list]

    exp_metrics, flow_stats_dict = dale_experiment_rig.ExperimentGroup.process_side_loaded_results(proto, src_dst_pairs_list, num_flows, flow_spec_list_list, target_flow_rate_gbps, app_trace_paths_list)

    srcdst_to_flowstatslist_dict = {}

    for key, flow_stat in flow_stats_dict.items():
        # initialise vals (empty lists) in srcdst_to_flowstatslist_dict
        src_or_dst_1, src_or_dst_2, flow_id = key
        srcdst_to_flowstatslist_dict[(src_or_dst_1, src_or_dst_2)] = []

    for key, flow_stat in flow_stats_dict.items():
        # append to vals (lists) in scrdst_to_flowstatslist_dict
        src_or_dst_1, src_or_dst_2, flow_id = key
        srcdst_to_flowstatslist_dict[(src_or_dst_1, src_or_dst_2)].append(flow_stat)

    print("======")
    flow_size_fct_list = []
    for srcdst, flow_stat_list in srcdst_to_flowstatslist_dict.items():
        print(f"srcdst={srcdst}")
        for flow_stat in flow_stat_list:
            fct = flow_stat.end_time_s - flow_stat.start_time_s
            # print(f"flow_id={flow_stat.flow_id}, flow_size_B={flow_stat.total_data_bytes_recv_B}, FCT(s)={flow_stat.end_time_s - flow_stat.start_time_s}")
            flow_size_fct_list.append((flow_stat.total_data_bytes_recv_B, fct))
        flow_size_fct_list.sort()
        print(f"{flow_size_fct_list}")

if __name__ == "__main__":

    side_load_incast_3to1_8flo_1560B_1000ns_same_flow_interarr()
    
