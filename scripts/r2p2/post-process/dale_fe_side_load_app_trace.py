import dale_experiment_rig

def side_load_and_process_results(
    experiment_logs_list,
    proto_list,
    topo_yaml_file,
    dist_workload_name,
    src_dst_pairs_list,
    num_flows_list,
    byteload_size_B_list,
    target_mean_byteload_interval_nanosec_list,
    ssird_app_trace_paths_list,
    dctcp_app_trace_paths_list,
    xpass_app_trace_paths_list,
    saved_json_file
):

    assert(len(set([
        len(num_flows_list),
        len(byteload_size_B_list),
        len(target_mean_byteload_interval_nanosec_list)
    ])) == 1)

    assert(len(set([
        len(num_flows_list),
        len(ssird_app_trace_paths_list),
        len(dctcp_app_trace_paths_list),
        len(xpass_app_trace_paths_list)
    ])) == 1)

    for log in experiment_logs_list:
        print(log)
    print("----------")
    print(saved_json_file)
    print("==========")

    target_flow_rate_gbps = (byteload_size_B_list[0] * 8) / (target_mean_byteload_interval_nanosec_list[0] * pow(10,-9)) * pow(10, -9)

    print(f"Flowspecs loaded from saved json file: {saved_json_file}")
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
            # print(len(flow_spec_list))
            # print(num_flows_list[exp_id])
            assert(len(flow_spec_list) == num_flows_list[exp_id])
            all_flow_specs_list.extend(flow_spec_list)
            src_dst_pairs_to_flow_start_times_us_dict[src_dst_pair] = flow_start_times_us_list
        src_dst_pairs_to_flow_start_times_us_dict_list.append(src_dst_pairs_to_flow_start_times_us_dict)

    flow_rate_gbps_list = [round(f.flow_rate_bps*pow(10,-9),6) for f in all_flow_specs_list]
    flow_size_B_list = [f.flow_size_B for f in all_flow_specs_list]
    flow_num_byteloads_list = [f.num_byteloads for f in all_flow_specs_list]
    flow_send_durations_us_list = [f.total_flow_send_duration_us for f in all_flow_specs_list]
    flow_min_byteload_size_B_list = [min(f.byteload_size_B_list) for f in all_flow_specs_list]
    flow_max_byteload_size_B_list = [max(f.byteload_size_B_list) for f in all_flow_specs_list]
    flow_min_interval_us = [min(f.interval_us_list) if len(f.interval_us_list) > 0 else f.interval_us_list for f in all_flow_specs_list]
    flow_max_interval_us = [max(f.interval_us_list) if len(f.interval_us_list) > 0 else f.interval_us_list for f in all_flow_specs_list]

    print(f"Workload name: {dist_workload_name}")
    print(f"Protos tested: {proto_list}")
    print(f"Topo Yaml File: {topo_yaml_file}")
    print(f"Src-Dst pairs list: {src_dst_pairs_list}")
    print(f"Num Flows: {num_flows_list}")
    print(f"Byteload Size (B): {byteload_size_B_list}")
    print(f"Flow size distr workload: {dist_workload_name}")
    print(f"Target Mean Byteload Interval (ns): {target_mean_byteload_interval_nanosec_list}")
    print(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    print(f"Num Byteloads: {flow_num_byteloads_list}")
    print(f"Flow Start Times (us): {src_dst_pairs_to_flow_start_times_us_dict_list}")
    print(f"Flow Rate (Gbps): {flow_rate_gbps_list}")
    print(f"Flow Size (B): {flow_size_B_list}")
    print(f"Flow Send Durations (us): {flow_send_durations_us_list}")
    print(f"Flow Min Byteload Size (B): {flow_min_byteload_size_B_list}")
    print(f"Flow Max Byteload Size (B): {flow_max_byteload_size_B_list}")
    print(f"Flow Min Interval (us): {flow_min_interval_us}")
    print(f"Flow Max Interval (us): {flow_max_interval_us}")

    exp_metrics = dale_experiment_rig.ExperimentGroup.process_side_loaded_results(
        proto_list,
        src_dst_pairs_list,
        num_flows_list,
        src_dst_pairs_to_flowspecs_dict_list,
        target_flow_rate_gbps,
        ssird_app_trace_paths_list,
        dctcp_app_trace_paths_list,
        xpass_app_trace_paths_list
    )

    print("==========")
    for log in experiment_logs_list:
        print(log)
    print("----------")
    print(saved_json_file)

def side_load_incast_fbHadoopDist_load_fullsweep_10to1_1458B_300ns_coarsegrained():
    # scripts/r2p2/post-process/saved_experiment_outputs/FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson/FE_incast_12host_fullsweep_10to1_12host_fbHadoopDist_load_fullsweep_300ns_fromjson_2025-08-22T_18-46-14Z.log

    experiment_logs_list = [
        "scripts/r2p2/post-process/saved_experiment_outputs/FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson/FE_incast_12host_fullsweep_10to1_12host_fbHadoopDist_load_fullsweep_300ns_fromjson_2025-08-22T_18-46-14Z.log"
    ]

    proto_list = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME]
    topo_yaml_file = "12-hosts-dumbbell.yaml"
    dist_workload_name = 'Facebook_HadoopDist_All.txt'
    src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)]
    num_flows_list = [1, 5, 10, 20, 30, 40]
    byteload_size_B_list = [1458, 1458, 1458, 1458, 1458, 1458]
    target_mean_byteload_interval_nanosec_list = [300, 300, 300, 300, 300, 300]

    # scripts/r2p2/post-process/experiment_app_trace_paths/FE_incast_12host_fullsweep_/_12host_fbHadoopDist_load_fullsweep_300ns_fromjson_1+5+10+20+30+40flo_39Gbps_2025-08-22T_18-46-14Z/SSIRD_app_traces.txt
    ssird_app_trace_paths_list = [
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__1flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/SSIRD/60/applications_trace.str", 
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__5flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/SSIRD/60/applications_trace.str", 
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__10flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/SSIRD/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__20flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/SSIRD/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__30flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/SSIRD/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__40flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/SSIRD/60/applications_trace.str"
    ]
    # scripts/r2p2/post-process/experiment_app_trace_paths/FE_incast_12host_fullsweep_/_12host_fbHadoopDist_load_fullsweep_300ns_fromjson_1+5+10+20+30+40flo_39Gbps_2025-08-22T_18-46-14Z/DCTCP-50_app_traces.txt
    dctcp_app_trace_paths_list = [
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__1flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__5flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__10flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__20flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__30flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__40flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/DCTCP-50/60/applications_trace.str",
    ]
    # scripts/r2p2/post-process/experiment_app_trace_paths/FE_incast_12host_fullsweep_/_12host_fbHadoopDist_load_fullsweep_300ns_fromjson_1+5+10+20+30+40flo_39Gbps_2025-08-22T_18-46-14Z/ExpressPass_app_traces.txt
    xpass_app_trace_paths_list = [
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__1flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__5flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__10flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__20flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__30flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host_fullsweep__12host_fbHadoopDist_load_fullsweep_300ns_fromjson__40flo-39Gbps-1458B-300ns-2025-08-22T_18-46-14Z/data/ExpressPass/60/applications_trace.str"
    ]

    saved_json_file = "FE_incast_12host_10to1_12host_fbHadoopDist_loadtest_300ns_2025-08-22T_18-10-46Z.json"

    side_load_and_process_results(
        experiment_logs_list=experiment_logs_list,
        proto_list=proto_list,
        topo_yaml_file=topo_yaml_file,
        dist_workload_name=dist_workload_name,
        src_dst_pairs_list=src_dst_pairs_list,
        num_flows_list=num_flows_list,
        byteload_size_B_list=byteload_size_B_list,
        target_mean_byteload_interval_nanosec_list=target_mean_byteload_interval_nanosec_list,
        ssird_app_trace_paths_list=ssird_app_trace_paths_list,
        dctcp_app_trace_paths_list=dctcp_app_trace_paths_list,
        xpass_app_trace_paths_list=xpass_app_trace_paths_list,
        saved_json_file=saved_json_file
    )

def side_load_incast_fbCacheFollowerDist_load_fullsweep_10to1_1458B_5000ns_coarsegrained():

    experiment_logs_list = [
        "scripts/r2p2/post-process/saved_experiment_outputs/FE_incast_12host_10to1_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_sideloaded/FE_incast_12host_fullsweep_10to1_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_2025-08-22T_18-30-29Z.log",
        "scripts/r2p2/post-process/saved_experiment_outputs/FE_incast_12host_10to1_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_sideloaded/FE_incast_12host_fullsweep_dctcp_xpass_10to1_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass_2025-08-24T_11-16-52Z.log",
        "scripts/r2p2/post-process/saved_experiment_outputs/FE_incast_12host_10to1_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_sideloaded/ssird_FE_incast_10to1_12host_fbCacheFollowerDist_load_fullsweep_5000ns_fromjson_sideloaded_2025-08-22T_18-30-29Z.txt"
    ]

    proto_list = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME]
    topo_yaml_file = "12-hosts-dumbbell.yaml"
    dist_workload_name = "Facebook_CacheFollowerDist_IntraCluster.txt"
    src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)]
    num_flows_list = [1, 5, 10, 20, 30, 40]
    byteload_size_B_list = [1458, 1458, 1458, 1458, 1458, 1458]
    target_mean_byteload_interval_nanosec_list = [5000, 5000, 5000, 5000, 5000, 5000]

    # scripts/r2p2/post-process/experiment_app_trace_paths/FE_incast_12host_fullsweep_/_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_1+5+10+20+30+40flo_2Gbps_2025-08-22T_18-30-29Z/SSIRD_app_traces.txt
    ssird_app_trace_paths_list = [
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson__1flo-2Gbps-1458B-5000ns-2025-08-22T_18-30-29Z/data/SSIRD/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson__5flo-2Gbps-1458B-5000ns-2025-08-22T_18-30-29Z/data/SSIRD/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson__10flo-2Gbps-1458B-5000ns-2025-08-22T_18-30-29Z/data/SSIRD/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson__20flo-2Gbps-1458B-5000ns-2025-08-22T_18-30-29Z/data/SSIRD/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson__30flo-2Gbps-1458B-5000ns-2025-08-22T_18-30-29Z/data/SSIRD/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson__40flo-2Gbps-1458B-5000ns-2025-08-22T_18-30-29Z/data/SSIRD/60/applications_trace.str"
    ]
    # scripts/r2p2/post-process/experiment_app_trace_paths/FE_incast_12host_fullsweep_dctcp_xpass_/_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass_1+5+10+20+30+40flo_2Gbps_2025-08-24T_11-16-52Z/DCTCP-50_app_traces.txt
    dctcp_app_trace_paths_list = [
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep_dctcp_xpass__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass__1flo-2Gbps-1458B-5000ns-2025-08-24T_11-16-52Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep_dctcp_xpass__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass__5flo-2Gbps-1458B-5000ns-2025-08-24T_11-16-52Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep_dctcp_xpass__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass__10flo-2Gbps-1458B-5000ns-2025-08-24T_11-16-52Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep_dctcp_xpass__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass__20flo-2Gbps-1458B-5000ns-2025-08-24T_11-16-52Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep_dctcp_xpass__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass__30flo-2Gbps-1458B-5000ns-2025-08-24T_11-16-52Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host_fullsweep_dctcp_xpass__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass__40flo-2Gbps-1458B-5000ns-2025-08-24T_11-16-52Z/data/DCTCP-50/60/applications_trace.str"
    ]
    # scripts/r2p2/post-process/experiment_app_trace_paths/FE_incast_12host_fullsweep_dctcp_xpass_/_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass_1+5+10+20+30+40flo_2Gbps_2025-08-24T_11-16-52Z/ExpressPass_app_traces.txt
    xpass_app_trace_paths_list = [
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host_fullsweep_dctcp_xpass__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass__1flo-2Gbps-1458B-5000ns-2025-08-24T_11-16-52Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host_fullsweep_dctcp_xpass__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass__5flo-2Gbps-1458B-5000ns-2025-08-24T_11-16-52Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host_fullsweep_dctcp_xpass__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass__10flo-2Gbps-1458B-5000ns-2025-08-24T_11-16-52Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host_fullsweep_dctcp_xpass__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass__20flo-2Gbps-1458B-5000ns-2025-08-24T_11-16-52Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host_fullsweep_dctcp_xpass__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass__30flo-2Gbps-1458B-5000ns-2025-08-24T_11-16-52Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host_fullsweep_dctcp_xpass__12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass__40flo-2Gbps-1458B-5000ns-2025-08-24T_11-16-52Z/data/ExpressPass/60/applications_trace.str"
    ]

    saved_json_file = "FE_incast_12host_10to1_12host_fbCacheFollowerDist_loadtest_5000ns_1to40flo_2025-08-20T_22-41-02Z.json"

    side_load_and_process_results(
        experiment_logs_list=experiment_logs_list,
        proto_list=proto_list,
        topo_yaml_file=topo_yaml_file,
        dist_workload_name=dist_workload_name,
        src_dst_pairs_list=src_dst_pairs_list,
        num_flows_list=num_flows_list,
        byteload_size_B_list=byteload_size_B_list,
        target_mean_byteload_interval_nanosec_list=target_mean_byteload_interval_nanosec_list,
        ssird_app_trace_paths_list=ssird_app_trace_paths_list,
        dctcp_app_trace_paths_list=dctcp_app_trace_paths_list,
        xpass_app_trace_paths_list=xpass_app_trace_paths_list,
        saved_json_file=saved_json_file
    )

def side_load_incast_dctcpMsgSizeDistActual_load_fullsweep_5to1_1458B_1Kns_coarsegrained():

    experiment_logs_list = [
        "scripts/r2p2/post-process/saved_experiment_outputs/FE_incast_12host_fullsweep__6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson/FE_incast_12host_fullsweep_5to1_6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson_2025-08-25T_21-36-46Z.log",
        "scripts/r2p2/post-process/saved_experiment_outputs/FE_incast_12host__6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry/FE_incast_12host_5to1_6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry_2025-08-25T_21-17-11Z.log"
    ]

    proto_list = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME]
    topo_yaml_file = "6-hosts-dumbbell.yaml"
    dist_workload_name = "DCTCP_MsgSizeDist.txt"
    src_dst_pairs_list=[(1, 0), (2, 0), (3, 0), (4, 0), (5, 0)]
    num_flows_list = [1, 5, 10, 15, 20, 25, 30]
    byteload_size_B_list = [1458, 1458, 1458, 1458, 1458, 1458, 1458]
    target_mean_byteload_interval_nanosec_list = [1000, 1000, 1000, 1000, 1000, 1000, 1000]

    # scripts/r2p2/post-process/experiment_app_trace_paths/FE_incast_12host_fullsweep_/_6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson_1+5+10+15+20+25+30flo_12Gbps_2025-08-25T_21-36-46Z/SSIRD_app_traces.txt
    ssird_app_trace_paths_list = [
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson__1flo-12Gbps-1458B-1000ns-2025-08-25T_21-36-46Z/data/SSIRD/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson__5flo-12Gbps-1458B-1000ns-2025-08-25T_21-36-46Z/data/SSIRD/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson__10flo-12Gbps-1458B-1000ns-2025-08-25T_21-36-46Z/data/SSIRD/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson__15flo-12Gbps-1458B-1000ns-2025-08-25T_21-36-46Z/data/SSIRD/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson__20flo-12Gbps-1458B-1000ns-2025-08-25T_21-36-46Z/data/SSIRD/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson__25flo-12Gbps-1458B-1000ns-2025-08-25T_21-36-46Z/data/SSIRD/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-FE_incast_12host_fullsweep__6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson__30flo-12Gbps-1458B-1000ns-2025-08-25T_21-36-46Z/data/SSIRD/60/applications_trace.str"
    ]
    # scripts/r2p2/post-process/experiment_app_trace_paths/FE_incast_12host_/_6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry_1+5+10+15+20+25+30flo_12Gbps_2025-08-25T_21-17-11Z/DCTCP-50_app_traces.txt
    dctcp_app_trace_paths_list = [
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry__1flo-12Gbps-1458B-1000ns-2025-08-25T_21-17-11Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry__5flo-12Gbps-1458B-1000ns-2025-08-25T_21-17-11Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry__10flo-12Gbps-1458B-1000ns-2025-08-25T_21-17-11Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry__15flo-12Gbps-1458B-1000ns-2025-08-25T_21-17-11Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry__20flo-12Gbps-1458B-1000ns-2025-08-25T_21-17-11Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry__25flo-12Gbps-1458B-1000ns-2025-08-25T_21-17-11Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry__30flo-12Gbps-1458B-1000ns-2025-08-25T_21-17-11Z/data/DCTCP-50/60/applications_trace.str"
    ]
    # scripts/r2p2/post-process/experiment_app_trace_paths/FE_incast_12host_/_6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry_1+5+10+15+20+25+30flo_12Gbps_2025-08-25T_21-17-11Z/ExpressPass_app_traces.txt
    xpass_app_trace_paths_list = [
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host__6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry__1flo-12Gbps-1458B-1000ns-2025-08-25T_21-17-11Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host__6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry__5flo-12Gbps-1458B-1000ns-2025-08-25T_21-17-11Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host__6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry__10flo-12Gbps-1458B-1000ns-2025-08-25T_21-17-11Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host__6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry__15flo-12Gbps-1458B-1000ns-2025-08-25T_21-17-11Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host__6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry__20flo-12Gbps-1458B-1000ns-2025-08-25T_21-17-11Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host__6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry__25flo-12Gbps-1458B-1000ns-2025-08-25T_21-17-11Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host__6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry__30flo-12Gbps-1458B-1000ns-2025-08-25T_21-17-11Z/data/ExpressPass/60/applications_trace.str"
    ]

    saved_json_file = "FE_incast_12host_5to1_6host_DctcpMsgSizeDistActual_loadtest_1Kns_2025-08-25T_20-37-43Z.json"

    side_load_and_process_results(
        experiment_logs_list=experiment_logs_list,
        proto_list=proto_list,
        topo_yaml_file=topo_yaml_file,
        dist_workload_name=dist_workload_name,
        src_dst_pairs_list=src_dst_pairs_list,
        num_flows_list=num_flows_list,
        byteload_size_B_list=byteload_size_B_list,
        target_mean_byteload_interval_nanosec_list=target_mean_byteload_interval_nanosec_list,
        ssird_app_trace_paths_list=ssird_app_trace_paths_list,
        dctcp_app_trace_paths_list=dctcp_app_trace_paths_list,
        xpass_app_trace_paths_list=xpass_app_trace_paths_list,
        saved_json_file=saved_json_file
    )

def side_load_incast_dctcpMsgSizeDistActual_load_fullsweep_10to1_1458B_2Kns_coarsegrained():

    experiment_logs_list = [
        "scripts/r2p2/post-process/experiment_output/FE_incast_12host_fullsweep__12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson/FE_incast_12host_fullsweep_10to1_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson_2025-08-26T_15-19-45Z.log",
        "scripts/r2p2/post-process/saved_experiment_outputs/FE_incast_12host__12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry/FE_incast_12host_10to1_12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry_2025-08-26T_13-13-34Z.log"
    ]

    proto_list = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME]
    topo_yaml_file = "12-hosts-dumbbell.yaml"
    dist_workload_name = "DCTCP_MsgSizeDist.txt"
    src_dst_pairs_list=[(1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0), (8, 0), (9, 0), (10, 0)]
    num_flows_list = [1, 5, 10, 15, 20, 25, 30]
    byteload_size_B_list = [1458, 1458, 1458, 1458, 1458, 1458, 1458]
    target_mean_byteload_interval_nanosec_list = [2000, 2000, 2000, 2000, 2000, 2000, 2000]

    ssird_app_trace_paths_list = [
        # TODO
    ]
    # scripts/r2p2/post-process/experiment_app_trace_paths/FE_incast_12host_/_12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry_1+5+10+15+20+25+30flo_6Gbps_2025-08-26T_13-13-34Z/DCTCP-50_app_traces.txt
    dctcp_app_trace_paths_list = [
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry__1flo-6Gbps-1458B-2000ns-2025-08-26T_13-13-34Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry__5flo-6Gbps-1458B-2000ns-2025-08-26T_13-13-34Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry__10flo-6Gbps-1458B-2000ns-2025-08-26T_13-13-34Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry__15flo-6Gbps-1458B-2000ns-2025-08-26T_13-13-34Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry__20flo-6Gbps-1458B-2000ns-2025-08-26T_13-13-34Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry__25flo-6Gbps-1458B-2000ns-2025-08-26T_13-13-34Z/data/DCTCP-50/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/DCTCP-50-FE_incast_12host__12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry__30flo-6Gbps-1458B-2000ns-2025-08-26T_13-13-34Z/data/DCTCP-50/60/applications_trace.str"
    ]
    # scripts/r2p2/post-process/experiment_app_trace_paths/FE_incast_12host_/_12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry_1+5+10+15+20+25+30flo_6Gbps_2025-08-26T_13-13-34Z/DCTCP-50_app_traces.txt
    xpass_app_trace_paths_list = [
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host__12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry__1flo-6Gbps-1458B-2000ns-2025-08-26T_13-13-34Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host__12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry__5flo-6Gbps-1458B-2000ns-2025-08-26T_13-13-34Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host__12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry__10flo-6Gbps-1458B-2000ns-2025-08-26T_13-13-34Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host__12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry__15flo-6Gbps-1458B-2000ns-2025-08-26T_13-13-34Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host__12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry__20flo-6Gbps-1458B-2000ns-2025-08-26T_13-13-34Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host__12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry__25flo-6Gbps-1458B-2000ns-2025-08-26T_13-13-34Z/data/ExpressPass/60/applications_trace.str",
        "/home/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/ExpressPass-FE_incast_12host__12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry__30flo-6Gbps-1458B-2000ns-2025-08-26T_13-13-34Z/data/ExpressPass/60/applications_trace.str"
    ]

    saved_json_file = "FE_incast_12host_10to1_12host_DctcpMsgSizeDistActual_loadtest_2Kns_2025-08-26T_10-36-29Z.json"

    side_load_and_process_results(
        experiment_logs_list=experiment_logs_list,
        proto_list=proto_list,
        topo_yaml_file=topo_yaml_file,
        dist_workload_name=dist_workload_name,
        src_dst_pairs_list=src_dst_pairs_list,
        num_flows_list=num_flows_list,
        byteload_size_B_list=byteload_size_B_list,
        target_mean_byteload_interval_nanosec_list=target_mean_byteload_interval_nanosec_list,
        ssird_app_trace_paths_list=ssird_app_trace_paths_list,
        dctcp_app_trace_paths_list=dctcp_app_trace_paths_list,
        xpass_app_trace_paths_list=xpass_app_trace_paths_list,
        saved_json_file=saved_json_file
    )

if __name__ == "__main__":
    
    # side_load_incast_fbHadoopDist_load_fullsweep_10to1_1458B_300ns_coarsegrained()
    # side_load_incast_fbCacheFollowerDist_load_fullsweep_10to1_1458B_5000ns_coarsegrained()
    side_load_incast_dctcpMsgSizeDistActual_load_fullsweep_5to1_1458B_1Kns_coarsegrained()

    # side_load_incast_dctcpMsgSizeDistActual_load_fullsweep_10to1_1458B_2Kns_coarsegrained()
