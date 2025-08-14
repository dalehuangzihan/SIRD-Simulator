import dale_experiment_rig

logger = dale_experiment_rig.logging.getLogger(__name__)

def experiment_incast(
        topo_yaml_file,
        src_dst_pairs_list,
        num_flows,
        byteload_size_B,
        target_mean_byteload_interval_nanosec,
        target_mean_num_byteloads,
        target_mean_flow_interarr_ns,
        is_use_poisson_byteload_intervals,
        is_use_poisson_num_byteloads,
        is_use_poisson_flow_interarr,
        ssird_sim_dur_list,
        dctcp_sim_dur_list,
        is_full_postproc=True,
        title_addendum="",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=None
    ):

    experiment_family = f"FE_Incast_{title_addendum}"
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    target_flow_rate_gbps = (byteload_size_B * 8) / (target_mean_byteload_interval_nanosec * pow(10,-9)) * pow(10, -9)
    logs_file_name = f"fe_incast_{len(src_dst_pairs_list)}to1_{dale_experiment_rig.Experiment.get_experiment_name(num_flows, target_flow_rate_gbps, byteload_size_B, target_mean_byteload_interval_nanosec, experiment_date)}{title_addendum}"
    dale_experiment_rig.init_logs(experiment_family, logs_file_name+".log")

    src_dst_pairs_to_flowspecs_dict = {}
    all_flow_specs_list = []
    src_dst_pairs_to_flow_start_times_us_dict = {}
    for src_dst_pair in src_dst_pairs_list:
        logger.info(f"Generating flow for src_dst_pair={src_dst_pair}\n")
        flow_generator = dale_experiment_rig.FlowSpecGenerator(
            num_flows=num_flows,
            byteload_size_B=byteload_size_B,
            target_mean_byteload_interval_ns=target_mean_byteload_interval_nanosec,
            target_mean_num_byteloads=target_mean_num_byteloads,
            target_mean_flow_interarr_ns=target_mean_flow_interarr_ns,
            is_use_poisson_byteload_intervals=is_use_poisson_byteload_intervals,
            is_use_poisson_num_byteloads=is_use_poisson_num_byteloads,
            is_use_poisson_flow_interarr=is_use_poisson_flow_interarr
        )
        flow_spec_list, flow_start_times_us_list = flow_generator.generate_poisson_flows()
        assert(len(flow_spec_list) == len(flow_start_times_us_list))
        src_dst_pairs_to_flowspecs_dict[src_dst_pair] = (flow_spec_list, flow_start_times_us_list)
        # the following are for debugging purposes
        all_flow_specs_list.extend(flow_spec_list)
        src_dst_pairs_to_flow_start_times_us_dict[src_dst_pair] = flow_start_times_us_list

    src_dst_pairs_to_flowspecs_dict_list = [src_dst_pairs_to_flowspecs_dict]
    num_of_experiments = len(src_dst_pairs_to_flowspecs_dict_list)

    # Back up flow spec list # TODO: make infra to back up flow spec list list
    all_experiment_inputs_json = dale_experiment_rig.FlowSpec.convert_src_dst_pairs_flowspec_dict_list_to_jsondict(src_dst_pairs_to_flowspecs_dict_list)
    print(all_experiment_inputs_json)
    dale_experiment_rig.FlowSpec.write_jsondict_to_jsonfile(all_experiment_inputs_json, dale_experiment_rig.FLOW_SPECS_JSON_PATH, logs_file_name+".json")

    print("----")

    # TESTING: Load in flow spec data to check
    src_dst_pairs_to_flowspecs_dict_list_loaded = dale_experiment_rig.FlowSpec.parse_src_dst_pairs_flowspec_dict_list_from_jsonfile(dale_experiment_rig.FLOW_SPECS_JSON_PATH, logs_file_name+".json")
    all_experiment_inputs_json_loaded = dale_experiment_rig.FlowSpec.convert_src_dst_pairs_flowspec_dict_list_to_jsondict(src_dst_pairs_to_flowspecs_dict_list_loaded)
    print(all_experiment_inputs_json_loaded)

    # return

    flow_rate_gbps_list = [round(f.flow_rate_bps*pow(10,-9),6) for f in all_flow_specs_list]
    flow_size_B_list = [f.flow_size_B for f in all_flow_specs_list]
    flow_num_byteloads_list = [f.num_byteloads for f in all_flow_specs_list]
    flow_send_durations_us_list = [f.total_flow_send_duration_us for f in all_flow_specs_list]
    flow_min_byteload_size_B_list = [min(f.byteload_size_B_list) for f in all_flow_specs_list]
    flow_max_byteload_size_B_list = [max(f.byteload_size_B_list) for f in all_flow_specs_list]
    flow_min_interval_us = [min(f.interval_us_list) for f in all_flow_specs_list]
    flow_max_interval_us = [max(f.interval_us_list) for f in all_flow_specs_list]

    logger.info(f"Protos tested: {proto_names}")
    logger.info(f"Topo Yaml File: {topo_yaml_file}")
    logger.info(f"Src-Dst pairs list: {src_dst_pairs_list}")
    logger.info(f"Num Flows: {num_flows}")
    logger.info(f"Byteload Size (B): {byteload_size_B}")
    logger.info(f"Target Mean Byteload Interval (ns): {target_mean_byteload_interval_nanosec}")
    logger.info(f"  is_use_poisson_byteload_intervals={is_use_poisson_byteload_intervals}")
    logger.info(f"Target Mean Flow Interarrival (ns): {target_mean_flow_interarr_ns}")
    logger.info(f"  is_use_poisson_flow_interarr={is_use_poisson_flow_interarr}")
    logger.info(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    logger.info(f"Num Byteloads: {flow_num_byteloads_list}")
    logger.info(f"  is_use_poisson_num_byteloads={is_use_poisson_num_byteloads}")
    logger.info(f"Flow Start Times (us): {src_dst_pairs_to_flow_start_times_us_dict}")
    logger.info(f"Flow Rate (Gbps): {flow_rate_gbps_list}")
    logger.info(f"Flow Size (B): {flow_size_B_list}")
    logger.info(f"Flow Send Durations (us): {flow_send_durations_us_list}")
    logger.info(f"Flow Min Byteload Size (B): {flow_min_byteload_size_B_list}")
    logger.info(f"Flow Max Byteload Size (B): {flow_max_byteload_size_B_list}")
    logger.info(f"Flow Min Interval (us): {flow_min_interval_us}")
    logger.info(f"Flow Max Interval (us): {flow_max_interval_us}")

    # TODO: modify assertion to work for spec that does specifies multiple experiments
    logger.debug(f"Max flow send durations (us): {max(flow_send_durations_us_list)}")
    assert(max(flow_send_durations_us_list) * pow(10,-6) * 1.5 < ssird_sim_dur_list[0])
    assert(max(flow_send_durations_us_list) * pow(10,-6) * 1.5 < dctcp_sim_dur_list[0])

    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    # return

    byteload_size_B_list = [byteload_size_B]
    target_mean_byteload_interval_nanosec_list = [target_mean_byteload_interval_nanosec]
    exp_grp = dale_experiment_rig.ExperimentGroup(
        experiment_family,
        experiment_date,
        proto_names,
        topo_yaml_file,
        src_dst_pairs_list,
        num_flows,
        byteload_size_B_list,
        target_mean_byteload_interval_nanosec_list,
        target_flow_rate_gbps,
        src_dst_pairs_to_flowspecs_dict_list,
        ssird_sim_dur_list,
        dctcp_sim_dur_list,
        is_full_postproc,
        log_level,
        title_addendum
    )

    exp_metrics = exp_grp.perform_experiment()

    logger.info(f"Protos tested: {proto_names}")
    logger.info(f"Topo Yaml File: {topo_yaml_file}")
    logger.info(f"Src-Dst pairs list: {src_dst_pairs_list}")
    logger.info(f"Num Flows: {num_flows}")
    logger.info(f"Byteload Size (B): {byteload_size_B}")
    logger.info(f"Target Mean Byteload Interval (ns): {target_mean_byteload_interval_nanosec}")
    logger.info(f"  is_use_poisson_byteload_intervals={is_use_poisson_byteload_intervals}")
    logger.info(f"Target Mean Flow Interarrival (ns): {target_mean_flow_interarr_ns}")
    logger.info(f"  is_use_poisson_flow_interarr={is_use_poisson_flow_interarr}")
    logger.info(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    logger.info(f"Num Byteloads: {flow_num_byteloads_list}")
    logger.info(f"  is_use_poisson_num_byteloads={is_use_poisson_num_byteloads}")
    logger.info(f"Flow Start Times (us): {src_dst_pairs_to_flow_start_times_us_dict}")
    logger.info(f"Flow Rate (Gbps): {flow_rate_gbps_list}")
    logger.info(f"Flow Size (B): {flow_size_B_list}")
    logger.info(f"Flow Send Durations (us): {flow_send_durations_us_list}")
    logger.info(f"Flow Min Byteload Size (B): {flow_min_byteload_size_B_list}")
    logger.info(f"Flow Max Byteload Size (B): {flow_max_byteload_size_B_list}")
    logger.info(f"Flow Min Interval (us): {flow_min_interval_us}")
    logger.info(f"Flow Max Interval (us): {flow_max_interval_us}")

    logger.info(f"APP Gdpt Gbps measured (SSIRD): {exp_metrics.total_app_gdpt_gbps_measured_list_ssird }")
    logger.info(f"APP Gdpt Gbps measured (DCTCP): {exp_metrics.total_app_gdpt_gbps_measured_list_dctcp}")
    logger.debug(f"APP Gdpt Gbps measured per flow (SSIRD): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_ssird}")
    logger.debug(f"APP Gdpt Gbps measured per flow (DCTCP): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_dctcp}")

    logger.info(f"NW Gdpt Gbps measured (SSIRD): {exp_metrics.total_nw_gdpt_gbps_measured_list_ssird}")
    logger.info(f"NW Gdpt Gbps measured (DCTCP): {exp_metrics.total_nw_gdpt_gbps_measured_list_dctcp}")
    logger.debug(f"NW Gdpt Gbps measured per flow (SSIRD): {exp_metrics.nw_gdpt_gbps_measured_per_flow_list_list_ssird}")
    logger.debug(f"NW Gdpt Gbps measured per flow (DCTCP): {exp_metrics.nw_gdpt_gbps_measured_per_flow_list_list_dctcp}")

    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    logger.info(f"* SSIRD FCT: {exp_metrics.ssird_fct_list}")
    logger.info(f"* DCTCP FCT: {exp_metrics.dctcp_fct_list}")

    assert num_of_experiments == len(exp_metrics.ssird_fct_list)
    assert num_of_experiments == len(exp_metrics.dctcp_fct_list)

def incast_9to1_1458B_maxload():
    # incurs max load on downlink
    ''' 
        9 to 1 incast experiment
            * 8flo
            * 1458B per bload
            * 1000ns intervals (avg)
            * mean num bloads = 500
            * 93.312Gbps total per sender
    '''
    experiment_incast(
        topo_yaml_file='10-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0)],
        num_flows=8,
        byteload_size_B=1458,
        target_mean_byteload_interval_nanosec=1000,
        target_mean_num_byteloads=500,
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_num_byteloads=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.01],
        dctcp_sim_dur_list=[0.01],
        is_full_postproc=True,
        title_addendum="_incast_poisson_9to1_8flo_1458B_1us_93pt312Gbps",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 

if __name__ == "__main__":
    ''' 
        9 to 1 incast experiment
        * test
    '''
    experiment_incast(
        topo_yaml_file='10-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0)],
        num_flows=2,
        byteload_size_B=1458,
        target_mean_byteload_interval_nanosec=1000,
        target_mean_num_byteloads=50,
        target_mean_flow_interarr_ns=2000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_num_byteloads=False,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.001],
        dctcp_sim_dur_list=[0.001],
        is_full_postproc=True,
        title_addendum="_rig_test",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=None
    ) 