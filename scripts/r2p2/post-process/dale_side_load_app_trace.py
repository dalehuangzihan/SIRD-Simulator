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

def side_load_incast_fbCacheFollowerDist_loadtest_10to1_30flo_1458B_5000ns():
    ''' --- Side-load & analyse existing app trace file ---'''
    proto = dale_experiment_rig.SSIRD_PROTO_NAME

    src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)]
    num_flows_list = [1, 3, 5, 10, 20, 30]
    byteload_size_B_list = [1458]
    target_mean_byteload_interval_nanosec_list = [5000]

    target_flow_rate_gbps = (byteload_size_B_list[0] * 8) / (target_mean_byteload_interval_nanosec_list[0] * pow(10,-9)) * pow(10, -9)

    app_trace_paths_list = [
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__12host_fbCacheFollowerDist_loadtest_5000ns__1flo-2Gbps-1458B-5000ns-2025-08-20T_19-00-08Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__12host_fbCacheFollowerDist_loadtest_5000ns__3flo-2Gbps-1458B-5000ns-2025-08-20T_19-00-08Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__12host_fbCacheFollowerDist_loadtest_5000ns__5flo-2Gbps-1458B-5000ns-2025-08-20T_19-00-08Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__12host_fbCacheFollowerDist_loadtest_5000ns__10flo-2Gbps-1458B-5000ns-2025-08-20T_19-00-08Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__12host_fbCacheFollowerDist_loadtest_5000ns__20flo-2Gbps-1458B-5000ns-2025-08-20T_19-00-08Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__12host_fbCacheFollowerDist_loadtest_5000ns__30flo-2Gbps-1458B-5000ns-2025-08-20T_19-00-08Z/data/DCTCP-50/60/applications_trace.str"
    ]

    saved_json_file = "FE_incast_12host_10to1_12host_fbCacheFollowerDist_loadtest_5000ns_2025-08-20T_19-00-08Z.json"
    src_dst_pairs_to_flowspecs_dict_list = dale_experiment_rig.FlowSpec.parse_src_dst_pairs_flowspec_dict_list_from_jsonfile(dale_experiment_rig.SAVED_FLOW_SPECS_JSON_PATH, saved_json_file)


    src_dst_pairs_to_flowspecs_dict_list = [] # list of src_dst_pairs_to_flowspecs_dict objs, one per experiment
    all_flow_specs_list = [] # list of flow_spec objs across all src-dst pairs across all experiments
    src_dst_pairs_to_flow_start_times_us_dict_list = [] # list of src_dst_pairs_to_flow_start_times_us_dict objs, one per experiment

    src_dst_pairs_to_flowspecs_dict_list = dale_experiment_rig.FlowSpec.parse_src_dst_pairs_flowspec_dict_list_from_jsonfile(dale_experiment_rig.SAVED_FLOW_SPECS_JSON_PATH, saved_json_file)
    for exp_id in range(len(src_dst_pairs_to_flowspecs_dict_list)): # iterating thru experiments
        src_dst_pairs_to_flowspecs_dict = src_dst_pairs_to_flowspecs_dict_list[exp_id]
        # print(src_dst_pairs_to_flowspecs_dict)
        src_dst_pairs_to_flow_start_times_us_dict = {}
        for src_dst_pair in src_dst_pairs_list:
            src_dst_pair_key = (src_dst_pair[0], src_dst_pair[1])
            flow_spec_list, flow_start_times_us_list = src_dst_pairs_to_flowspecs_dict[src_dst_pair_key]
            assert(len(flow_spec_list) == len(flow_start_times_us_list))
            assert(len(flow_spec_list) == num_flows_list[exp_id])
            all_flow_specs_list.extend(flow_spec_list)
            src_dst_pairs_to_flow_start_times_us_dict[src_dst_pair] = flow_start_times_us_list
        src_dst_pairs_to_flow_start_times_us_dict_list.append(src_dst_pairs_to_flow_start_times_us_dict)

    exp_metrics, flow_stats_dict = dale_experiment_rig.ExperimentGroup.process_side_loaded_results(proto, src_dst_pairs_list, num_flows_list, src_dst_pairs_to_flowspecs_dict_list, target_flow_rate_gbps, app_trace_paths_list)

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


def side_load_incast_DctcpMsgsizeDist_load_fullsweep_v2_10to1_1458B_800ns():
    ''' --- Side-load & analyse existing app trace file ---'''
    proto = dale_experiment_rig.DCTCP_PROTO_NAME

    src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)]
    num_flows_list = [1, 5, 10, 15, 20, 30, 40]
    byteload_size_B_list = [1458]
    target_mean_byteload_interval_nanosec_list = [5000]

    target_flow_rate_gbps = (byteload_size_B_list[0] * 8) / (target_mean_byteload_interval_nanosec_list[0] * pow(10,-9)) * pow(10, -9)

    app_trace_paths_list = [
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep_v2__12host_DctcpMsgSizeDist_load_fullsweep_800ns_v2__1flo-15Gbps-1458B-800ns-2025-08-21T_08-44-37Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep_v2__12host_DctcpMsgSizeDist_load_fullsweep_800ns_v2__5flo-15Gbps-1458B-800ns-2025-08-21T_08-44-37Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep_v2__12host_DctcpMsgSizeDist_load_fullsweep_800ns_v2__10flo-15Gbps-1458B-800ns-2025-08-21T_08-44-37Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep_v2__12host_DctcpMsgSizeDist_load_fullsweep_800ns_v2__15flo-15Gbps-1458B-800ns-2025-08-21T_08-44-37Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep_v2__12host_DctcpMsgSizeDist_load_fullsweep_800ns_v2__20flo-15Gbps-1458B-800ns-2025-08-21T_08-44-37Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep_v2__12host_DctcpMsgSizeDist_load_fullsweep_800ns_v2__30flo-15Gbps-1458B-800ns-2025-08-21T_08-44-37Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep_v2__12host_DctcpMsgSizeDist_load_fullsweep_800ns_v2__40flo-15Gbps-1458B-800ns-2025-08-21T_08-44-37Z/data/DCTCP-50/60/applications_trace.str",
    ]

    saved_json_file = "FE_incast_12host_fullsweep_v2_10to1_12host_DctcpMsgSizeDist_load_fullsweep_800ns_v2_2025-08-21T_08-44-37Z.json"
    src_dst_pairs_to_flowspecs_dict_list = dale_experiment_rig.FlowSpec.parse_src_dst_pairs_flowspec_dict_list_from_jsonfile(dale_experiment_rig.SAVED_FLOW_SPECS_JSON_PATH, saved_json_file)


    src_dst_pairs_to_flowspecs_dict_list = [] # list of src_dst_pairs_to_flowspecs_dict objs, one per experiment
    all_flow_specs_list = [] # list of flow_spec objs across all src-dst pairs across all experiments
    src_dst_pairs_to_flow_start_times_us_dict_list = [] # list of src_dst_pairs_to_flow_start_times_us_dict objs, one per experiment

    src_dst_pairs_to_flowspecs_dict_list = dale_experiment_rig.FlowSpec.parse_src_dst_pairs_flowspec_dict_list_from_jsonfile(dale_experiment_rig.SAVED_FLOW_SPECS_JSON_PATH, saved_json_file)
    for exp_id in range(len(src_dst_pairs_to_flowspecs_dict_list)): # iterating thru experiments
        src_dst_pairs_to_flowspecs_dict = src_dst_pairs_to_flowspecs_dict_list[exp_id]
        # print(src_dst_pairs_to_flowspecs_dict)
        src_dst_pairs_to_flow_start_times_us_dict = {}
        for src_dst_pair in src_dst_pairs_list:
            src_dst_pair_key = (src_dst_pair[0], src_dst_pair[1])
            flow_spec_list, flow_start_times_us_list = src_dst_pairs_to_flowspecs_dict[src_dst_pair_key]
            assert(len(flow_spec_list) == len(flow_start_times_us_list))
            assert(len(flow_spec_list) == num_flows_list[exp_id])
            all_flow_specs_list.extend(flow_spec_list)
            src_dst_pairs_to_flow_start_times_us_dict[src_dst_pair] = flow_start_times_us_list
        src_dst_pairs_to_flow_start_times_us_dict_list.append(src_dst_pairs_to_flow_start_times_us_dict)

    exp_metrics, flow_stats_dict = dale_experiment_rig.ExperimentGroup.process_side_loaded_results(proto, src_dst_pairs_list, num_flows_list, src_dst_pairs_to_flowspecs_dict_list, target_flow_rate_gbps, app_trace_paths_list)

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

    # side_load_incast_3to1_8flo_1560B_1000ns_same_flow_interarr()
    # side_load_incast_fbCacheFollowerDist_loadtest_10to1_30flo_1458B_5000ns()
    
    side_load_incast_DctcpMsgsizeDist_load_fullsweep_v2_10to1_1458B_800ns()