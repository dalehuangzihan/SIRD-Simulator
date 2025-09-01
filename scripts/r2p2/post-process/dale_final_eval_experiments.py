from pathlib import Path

import dale_experiment_rig

logger = dale_experiment_rig.logging.getLogger(__name__)

''' Function to generate flows and run experiment '''
def run_experiment(
        proto_names,
        topo_yaml_file,
        src_dst_pairs_list,
        num_flows_list,
        byteload_size_B_list,
        target_mean_byteload_interval_nanosec_list,
        max_interval_nanosec_list,
        flow_size_distr_list,
        target_mean_flow_interarr_ns,
        is_use_poisson_byteload_intervals,
        is_use_poisson_flow_interarr,
        ssird_sim_dur_list,
        dctcp_sim_dur_list,
        xpass_sim_dur_list,
        is_full_postproc=True,
        title_prefix="",
        title_addendum="",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date="nodate",
        is_all_same_flowrate=True
    ):

    experiment_family = f"{title_prefix}"

    assert(len(set([
            len(num_flows_list),
            len(byteload_size_B_list),
            len(target_mean_byteload_interval_nanosec_list),
            len(flow_size_distr_list),
            len(ssird_sim_dur_list),
            len(dctcp_sim_dur_list),
            len(xpass_sim_dur_list)
        ])) == 1)
    num_of_experiments = len(byteload_size_B_list)
    target_flow_rate_gbps = (byteload_size_B_list[0] * 8) / (target_mean_byteload_interval_nanosec_list[0] * pow(10,-9)) * pow(10, -9)

    logs_file_name = f"{experiment_family}{len(src_dst_pairs_list)}to1{title_addendum}_{experiment_date}"
    dale_experiment_rig.init_logs(f"{experiment_family}{title_addendum}", logs_file_name+".log")

    logger.debug(f"Flow size distr workload: {[distr.cdf_file_name for distr in flow_size_distr_list]}")

    src_dst_pairs_to_flowspecs_dict_list = [] # list of src_dst_pairs_to_flowspecs_dict objs, one per experiment
    all_flow_specs_list = [] # list of flow_spec objs across all src-dst pairs across all experiments
    src_dst_pairs_to_flow_start_times_us_dict_list = [] # list of src_dst_pairs_to_flow_start_times_us_dict objs, one per experiment

    for i in range(0, num_of_experiments):
        logger.info(f"\n* Generating flows for experiment {i} ---")
        num_flows = num_flows_list[i]
        byteload_size_B = byteload_size_B_list[i]
        flow_size_distr = flow_size_distr_list[i]
        target_mean_byteload_interval_nanosec = target_mean_byteload_interval_nanosec_list[i]
        max_interval_nanosec = max_interval_nanosec_list[i]
        exp_target_flow_rate_gbps = (byteload_size_B_list[i] * 8) / (target_mean_byteload_interval_nanosec_list[i] * pow(10,-9)) * pow(10, -9)
        if (is_all_same_flowrate):
            assert(round(exp_target_flow_rate_gbps, 9) == round(target_flow_rate_gbps, 9))

        src_dst_pairs_to_flowspecs_dict = {}
        src_dst_pairs_to_flow_start_times_us_dict = {}
        for src_dst_pair in src_dst_pairs_list:
            logger.info(f"\nGenerating flow for src_dst_pair={src_dst_pair}")
            flow_generator = dale_experiment_rig.FlowSpecGenerator(
                num_flows=num_flows,
                byteload_size_B=byteload_size_B,
                target_mean_byteload_interval_ns=target_mean_byteload_interval_nanosec,
                flow_size_distr=flow_size_distr,
                target_mean_flow_interarr_ns=target_mean_flow_interarr_ns,
                max_interval_ns=max_interval_nanosec,
                is_use_poisson_byteload_intervals=is_use_poisson_byteload_intervals,
                is_use_poisson_flow_interarr=is_use_poisson_flow_interarr
            )
            flow_spec_list, flow_start_times_us_list = flow_generator.generate_poisson_flows()
            assert(len(flow_spec_list) == len(flow_start_times_us_list))
            src_dst_pairs_to_flowspecs_dict[src_dst_pair] = (flow_spec_list, flow_start_times_us_list)
            # the following are for debugging purposes
            all_flow_specs_list.extend(flow_spec_list)
            src_dst_pairs_to_flow_start_times_us_dict[src_dst_pair] = flow_start_times_us_list

        src_dst_pairs_to_flowspecs_dict_list.append(src_dst_pairs_to_flowspecs_dict)
        # the following are for debugging purposes
        src_dst_pairs_to_flow_start_times_us_dict_list.append(src_dst_pairs_to_flow_start_times_us_dict)

    assert(num_of_experiments == len(src_dst_pairs_to_flowspecs_dict_list))

    # return

    # Back up flow spec list # TODO: make infra to back up flow spec list list
    all_experiment_inputs_json = dale_experiment_rig.FlowSpec.convert_src_dst_pairs_flowspec_dict_list_to_jsondict(src_dst_pairs_to_flowspecs_dict_list)
    # logger.debug(all_experiment_inputs_json)
    dale_experiment_rig.FlowSpec.write_jsondict_to_jsonfile(all_experiment_inputs_json, dale_experiment_rig.FLOW_SPECS_JSON_PATH, logs_file_name+".json")

    print("----")

    # # TESTING: Load in flow spec data to check
    # src_dst_pairs_to_flowspecs_dict_list_loaded = dale_experiment_rig.FlowSpec.parse_src_dst_pairs_flowspec_dict_list_from_jsonfile(dale_experiment_rig.FLOW_SPECS_JSON_PATH, logs_file_name+".json")
    # all_experiment_inputs_json_loaded = dale_experiment_rig.FlowSpec.convert_src_dst_pairs_flowspec_dict_list_to_jsondict(src_dst_pairs_to_flowspecs_dict_list_loaded)
    # # logger.debug(all_experiment_inputs_json_loaded)

    # return

    flow_rate_gbps_list = [round(f.flow_rate_bps*pow(10,-9),6) for f in all_flow_specs_list]
    flow_size_B_list = [f.flow_size_B for f in all_flow_specs_list]
    flow_num_byteloads_list = [f.num_byteloads for f in all_flow_specs_list]
    flow_send_durations_us_list = [f.total_flow_send_duration_us for f in all_flow_specs_list]
    flow_min_byteload_size_B_list = [min(f.byteload_size_B_list) for f in all_flow_specs_list]
    flow_max_byteload_size_B_list = [max(f.byteload_size_B_list) for f in all_flow_specs_list]
    flow_min_interval_us = [min(f.interval_us_list) if len(f.interval_us_list) > 0 else f.interval_us_list for f in all_flow_specs_list]
    flow_max_interval_us = [max(f.interval_us_list) if len(f.interval_us_list) > 0 else f.interval_us_list for f in all_flow_specs_list]

    logger.info(f"Protos tested: {proto_names}")
    logger.info(f"Topo Yaml File: {topo_yaml_file}")
    logger.info(f"Src-Dst pairs list: {src_dst_pairs_list}")
    logger.info(f"Num Flows: {num_flows_list}")
    logger.info(f"Byteload Size (B): {byteload_size_B_list}")
    logger.info(f"Flow size distr workload: {[distr.cdf_file_name for distr in flow_size_distr_list]}")
    logger.info(f"Target Mean Byteload Interval (ns): {target_mean_byteload_interval_nanosec_list}")
    logger.info(f"  is_use_poisson_byteload_intervals={is_use_poisson_byteload_intervals}")
    logger.info(f"Target Mean Flow Interarrival (ns): {target_mean_flow_interarr_ns}")
    logger.info(f"  is_use_poisson_flow_interarr={is_use_poisson_flow_interarr}")
    logger.info(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    logger.info(f"Num Byteloads: {flow_num_byteloads_list}")
    logger.info(f"Flow Start Times (us): {src_dst_pairs_to_flow_start_times_us_dict_list}")
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
    assert(max(flow_send_durations_us_list) * pow(10,-6) * 1.5 < xpass_sim_dur_list[0])

    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    logger.info(f"* Sim duration (XPass): {xpass_sim_dur_list}")
    # return

    exp_grp = dale_experiment_rig.ExperimentGroup(
        experiment_family,
        experiment_date,
        proto_names,
        topo_yaml_file,
        src_dst_pairs_list,
        num_flows_list,
        byteload_size_B_list,
        target_mean_byteload_interval_nanosec_list,
        target_flow_rate_gbps,
        src_dst_pairs_to_flowspecs_dict_list,
        ssird_sim_dur_list,
        dctcp_sim_dur_list,
        xpass_sim_dur_list,
        is_full_postproc,
        log_level,
        title_addendum
    )

    exp_metrics = exp_grp.perform_experiment()

    logger.info(f"Protos tested: {proto_names}")
    logger.info(f"Topo Yaml File: {topo_yaml_file}")
    logger.info(f"Src-Dst pairs list: {src_dst_pairs_list}")
    logger.info(f"Num Flows: {num_flows_list}")
    logger.info(f"Byteload Size (B): {byteload_size_B_list}")
    logger.info(f"Flow size distr workload: {[distr.cdf_file_name for distr in flow_size_distr_list]}")
    logger.info(f"Target Mean Byteload Interval (ns): {target_mean_byteload_interval_nanosec_list}")
    logger.info(f"  is_use_poisson_byteload_intervals={is_use_poisson_byteload_intervals}")
    logger.info(f"Target Mean Flow Interarrival (ns): {target_mean_flow_interarr_ns}")
    logger.info(f"  is_use_poisson_flow_interarr={is_use_poisson_flow_interarr}")
    logger.info(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    logger.info(f"Num Byteloads: {flow_num_byteloads_list}")
    logger.info(f"Flow Start Times (us): {src_dst_pairs_to_flow_start_times_us_dict_list}")
    logger.info(f"Flow Rate (Gbps): {flow_rate_gbps_list}")
    logger.info(f"Flow Size (B): {flow_size_B_list}")
    logger.info(f"Flow Send Durations (us): {flow_send_durations_us_list}")
    logger.info(f"Flow Min Byteload Size (B): {flow_min_byteload_size_B_list}")
    logger.info(f"Flow Max Byteload Size (B): {flow_max_byteload_size_B_list}")
    logger.info(f"Flow Min Interval (us): {flow_min_interval_us}")
    logger.info(f"Flow Max Interval (us): {flow_max_interval_us}")

    logger.info(f"- APP Gdpt Gbps measured (SSIRD): {exp_metrics.total_app_gdpt_gbps_measured_list_ssird }")
    logger.info(f"+ APP Gdpt Gbps union (SSIRD):    {exp_metrics.total_app_gdpt_gbps_measured_list_union_ssird }")
    logger.info(f"- APP Gdpt Gbps measured (DCTCP): {exp_metrics.total_app_gdpt_gbps_measured_list_dctcp}")
    logger.info(f"+ APP Gdpt Gbps union (DCTCP):    {exp_metrics.total_app_gdpt_gbps_measured_list_union_dctcp}")
    logger.info(f"- APP Gdpt Gbps measured (XPass): {exp_metrics.total_app_gdpt_gbps_measured_list_xpass}")
    logger.info(f"+ APP Gdpt Gbps union (XPass):    {exp_metrics.total_app_gdpt_gbps_measured_list_union_xpass}")
    logger.debug(f"APP Gdpt Gbps measured per flow (SSIRD): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_ssird}")
    logger.debug(f"APP Gdpt Gbps measured per flow (DCTCP): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_dctcp}")
    logger.debug(f"APP Gdpt Gbps measured per flow (XPass): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_xpass}")

    logger.info(f"- NW Gdpt Gbps measured (SSIRD): {exp_metrics.total_nw_gdpt_gbps_measured_list_ssird}")
    logger.info(f"+ NW Gdpt Gbps union (SSIRD):    {exp_metrics.total_nw_gdpt_gbps_measured_list_union_ssird}")
    logger.info(f"- NW Gdpt Gbps measured (DCTCP): {exp_metrics.total_nw_gdpt_gbps_measured_list_dctcp}")
    logger.info(f"+ NW Gdpt Gbps union (DCTCP):    {exp_metrics.total_nw_gdpt_gbps_measured_list_union_dctcp}")
    logger.info(f"- NW Gdpt Gbps measured (Xpass): {exp_metrics.total_nw_gdpt_gbps_measured_list_xpass}")
    logger.info(f"+ NW Gdpt Gbps union (Xpass):    {exp_metrics.total_nw_gdpt_gbps_measured_list_union_xpass}")
    logger.debug(f"NW Gdpt Gbps measured per flow (SSIRD): {exp_metrics.nw_gdpt_gbps_measured_per_flow_list_list_ssird}")
    logger.debug(f"NW Gdpt Gbps measured per flow (DCTCP): {exp_metrics.nw_gdpt_gbps_measured_per_flow_list_list_dctcp}")
    logger.debug(f"NW Gdpt Gbps measured per flow (XPass): {exp_metrics.nw_gdpt_gbps_measured_per_flow_list_list_xpass}")

    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    logger.info(f"* Sim duration (XPass): {xpass_sim_dur_list}")
    logger.info(f"* SSIRD FCT: {exp_metrics.ssird_fct_list}")
    logger.info(f"* DCTCP FCT: {exp_metrics.dctcp_fct_list}")
    logger.info(f"* XPass FCT: {exp_metrics.xpass_fct_list}")

    logger.info(f"** SSIRD FCT sorted: {exp_metrics.sorted_flowsize_fct_list_list_ssird}")
    logger.info(f"** DCTCP FCT sorted: {exp_metrics.sorted_flowsize_fct_list_list_dctcp}")
    logger.info(f"** XPass FCT sorted: {exp_metrics.sorted_flowsize_fct_list_list_xpass}")

    assert num_of_experiments == len(exp_metrics.ssird_fct_list)
    assert num_of_experiments == len(exp_metrics.dctcp_fct_list)
    assert num_of_experiments == len(exp_metrics.xpass_fct_list)

''' Function to load flows from saved json and run experiments '''
def run_experiment_from_saved_json(
        saved_json_file,
        proto_names,
        topo_yaml_file,
        src_dst_pairs_list,
        num_flows_list,
        byteload_size_B_list,
        target_mean_byteload_interval_nanosec_list,
        flow_size_distr_list,
        target_mean_flow_interarr_ns,
        is_use_poisson_byteload_intervals,
        is_use_poisson_flow_interarr,
        ssird_sim_dur_list,
        dctcp_sim_dur_list,
        xpass_sim_dur_list,
        is_full_postproc=True,
        title_prefix="",
        title_addendum="",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date="nodate"
    ):

    saved_json_file_path = Path(dale_experiment_rig.SAVED_FLOW_SPECS_JSON_PATH + saved_json_file)
    assert(saved_json_file_path.exists())

    experiment_family = f"{title_prefix}"

    assert(len(set([
            len(num_flows_list),
            len(byteload_size_B_list),
            len(target_mean_byteload_interval_nanosec_list),
            len(flow_size_distr_list),
            len(ssird_sim_dur_list),
            len(dctcp_sim_dur_list),
            len(xpass_sim_dur_list)
        ])) == 1)
    num_of_experiments = len(byteload_size_B_list)
    target_flow_rate_gbps = (byteload_size_B_list[0] * 8) / (target_mean_byteload_interval_nanosec_list[0] * pow(10,-9)) * pow(10, -9)

    logs_file_name = f"{experiment_family}{len(src_dst_pairs_list)}to1{title_addendum}_{experiment_date}"
    dale_experiment_rig.init_logs(f"{experiment_family}{title_addendum}", logs_file_name+".log")

    logger.debug(f"## LOADING FROM SAVED JSON FILE: {saved_json_file_path}")
    logger.debug(f"Flow size distr workload: {[distr.cdf_file_name for distr in flow_size_distr_list]}")

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

    assert(num_of_experiments == len(src_dst_pairs_to_flowspecs_dict_list))

    flow_rate_gbps_list = [round(f.flow_rate_bps*pow(10,-9),6) for f in all_flow_specs_list]
    flow_size_B_list = [f.flow_size_B for f in all_flow_specs_list]
    flow_num_byteloads_list = [f.num_byteloads for f in all_flow_specs_list]
    flow_send_durations_us_list = [f.total_flow_send_duration_us for f in all_flow_specs_list]
    flow_min_byteload_size_B_list = [min(f.byteload_size_B_list) for f in all_flow_specs_list]
    flow_max_byteload_size_B_list = [max(f.byteload_size_B_list) for f in all_flow_specs_list]
    flow_min_interval_us = [min(f.interval_us_list) if len(f.interval_us_list) > 0 else f.interval_us_list for f in all_flow_specs_list]
    flow_max_interval_us = [max(f.interval_us_list) if len(f.interval_us_list) > 0 else f.interval_us_list for f in all_flow_specs_list]

    logger.info(f"Protos tested: {proto_names}")
    logger.info(f"Topo Yaml File: {topo_yaml_file}")
    logger.info(f"Src-Dst pairs list: {src_dst_pairs_list}")
    logger.info(f"Num Flows: {num_flows_list}")
    logger.info(f"Byteload Size (B): {byteload_size_B_list}")
    logger.info(f"Flow size distr workload: {[distr.cdf_file_name for distr in flow_size_distr_list]}")
    logger.info(f"Target Mean Byteload Interval (ns): {target_mean_byteload_interval_nanosec_list}")
    logger.info(f"  is_use_poisson_byteload_intervals={is_use_poisson_byteload_intervals}")
    logger.info(f"Target Mean Flow Interarrival (ns): {target_mean_flow_interarr_ns}")
    logger.info(f"  is_use_poisson_flow_interarr={is_use_poisson_flow_interarr}")
    logger.info(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    logger.info(f"Num Byteloads: {flow_num_byteloads_list}")
    logger.info(f"Flow Start Times (us): {src_dst_pairs_to_flow_start_times_us_dict_list}")
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
    assert(max(flow_send_durations_us_list) * pow(10,-6) * 1.5 < xpass_sim_dur_list[0])

    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    logger.info(f"* Sim duration (XPass): {xpass_sim_dur_list}")
    # return

    exp_grp = dale_experiment_rig.ExperimentGroup(
        experiment_family,
        experiment_date,
        proto_names,
        topo_yaml_file,
        src_dst_pairs_list,
        num_flows_list,
        byteload_size_B_list,
        target_mean_byteload_interval_nanosec_list,
        target_flow_rate_gbps,
        src_dst_pairs_to_flowspecs_dict_list,
        ssird_sim_dur_list,
        dctcp_sim_dur_list,
        xpass_sim_dur_list,
        is_full_postproc,
        log_level,
        title_addendum
    )

    exp_metrics = exp_grp.perform_experiment()

    logger.info(f"Protos tested: {proto_names}")
    logger.info(f"Topo Yaml File: {topo_yaml_file}")
    logger.info(f"Src-Dst pairs list: {src_dst_pairs_list}")
    logger.info(f"Num Flows: {num_flows_list}")
    logger.info(f"Byteload Size (B): {byteload_size_B_list}")
    logger.info(f"Flow size distr workload: {[distr.cdf_file_name for distr in flow_size_distr_list]}")
    logger.info(f"Target Mean Byteload Interval (ns): {target_mean_byteload_interval_nanosec_list}")
    logger.info(f"  is_use_poisson_byteload_intervals={is_use_poisson_byteload_intervals}")
    logger.info(f"Target Mean Flow Interarrival (ns): {target_mean_flow_interarr_ns}")
    logger.info(f"  is_use_poisson_flow_interarr={is_use_poisson_flow_interarr}")
    logger.info(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    logger.info(f"Num Byteloads: {flow_num_byteloads_list}")
    logger.info(f"Flow Start Times (us): {src_dst_pairs_to_flow_start_times_us_dict_list}")
    logger.info(f"Flow Rate (Gbps): {flow_rate_gbps_list}")
    logger.info(f"Flow Size (B): {flow_size_B_list}")
    logger.info(f"Flow Send Durations (us): {flow_send_durations_us_list}")
    logger.info(f"Flow Min Byteload Size (B): {flow_min_byteload_size_B_list}")
    logger.info(f"Flow Max Byteload Size (B): {flow_max_byteload_size_B_list}")
    logger.info(f"Flow Min Interval (us): {flow_min_interval_us}")
    logger.info(f"Flow Max Interval (us): {flow_max_interval_us}")

    logger.info(f"- APP Gdpt Gbps measured (SSIRD): {exp_metrics.total_app_gdpt_gbps_measured_list_ssird }")
    logger.info(f"+ APP Gdpt Gbps union (SSIRD):    {exp_metrics.total_app_gdpt_gbps_measured_list_union_ssird }")
    logger.info(f"- APP Gdpt Gbps measured (DCTCP): {exp_metrics.total_app_gdpt_gbps_measured_list_dctcp}")
    logger.info(f"+ APP Gdpt Gbps union (DCTCP):    {exp_metrics.total_app_gdpt_gbps_measured_list_union_dctcp}")
    logger.info(f"- APP Gdpt Gbps measured (XPass): {exp_metrics.total_app_gdpt_gbps_measured_list_xpass}")
    logger.info(f"+ APP Gdpt Gbps union (XPass):    {exp_metrics.total_app_gdpt_gbps_measured_list_union_xpass}")
    logger.debug(f"APP Gdpt Gbps measured per flow (SSIRD): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_ssird}")
    logger.debug(f"APP Gdpt Gbps measured per flow (DCTCP): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_dctcp}")
    logger.debug(f"APP Gdpt Gbps measured per flow (XPass): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_xpass}")

    logger.info(f"- NW Gdpt Gbps measured (SSIRD): {exp_metrics.total_nw_gdpt_gbps_measured_list_ssird}")
    logger.info(f"+ NW Gdpt Gbps union (SSIRD):    {exp_metrics.total_nw_gdpt_gbps_measured_list_union_ssird}")
    logger.info(f"- NW Gdpt Gbps measured (DCTCP): {exp_metrics.total_nw_gdpt_gbps_measured_list_dctcp}")
    logger.info(f"+ NW Gdpt Gbps union (DCTCP):    {exp_metrics.total_nw_gdpt_gbps_measured_list_union_dctcp}")
    logger.info(f"- NW Gdpt Gbps measured (Xpass): {exp_metrics.total_nw_gdpt_gbps_measured_list_xpass}")
    logger.info(f"+ NW Gdpt Gbps union (Xpass):    {exp_metrics.total_nw_gdpt_gbps_measured_list_union_xpass}")
    logger.debug(f"NW Gdpt Gbps measured per flow (SSIRD): {exp_metrics.nw_gdpt_gbps_measured_per_flow_list_list_ssird}")
    logger.debug(f"NW Gdpt Gbps measured per flow (DCTCP): {exp_metrics.nw_gdpt_gbps_measured_per_flow_list_list_dctcp}")
    logger.debug(f"NW Gdpt Gbps measured per flow (XPass): {exp_metrics.nw_gdpt_gbps_measured_per_flow_list_list_xpass}")

    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    logger.info(f"* Sim duration (XPass): {xpass_sim_dur_list}")
    logger.info(f"* SSIRD FCT: {exp_metrics.ssird_fct_list}")
    logger.info(f"* DCTCP FCT: {exp_metrics.dctcp_fct_list}")
    logger.info(f"* XPass FCT: {exp_metrics.xpass_fct_list}")

    logger.info(f"** SSIRD FCT sorted: {exp_metrics.sorted_flowsize_fct_list_list_ssird}")
    logger.info(f"** DCTCP FCT sorted: {exp_metrics.sorted_flowsize_fct_list_list_dctcp}")
    logger.info(f"** XPass FCT sorted: {exp_metrics.sorted_flowsize_fct_list_list_xpass}")

    assert num_of_experiments == len(exp_metrics.ssird_fct_list)
    assert num_of_experiments == len(exp_metrics.dctcp_fct_list)
    assert num_of_experiments == len(exp_metrics.xpass_fct_list)

''' 
    ========== 1RTT EXPERIMENTS: ==========
'''

# def onertt_delay_p2p_lowload():
#     ''' 1 to 1 point-to-point experiment '''
#     run_experiment(
#         proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME],
#         topo_yaml_file='10-hosts-dumbbell.yaml',
#         src_dst_pairs_list=[(0,1)],
#         num_flows_list=[6]*8,
#         byteload_size_B_list=[500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000],
#         target_mean_byteload_interval_nanosec_list=[500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000], 
#         max_interval_nanosec_list=[500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000],
#         flow_size_distr_list=[
#             dale_experiment_rig.FixedDistr(num_byteloads=2000, byteload_size_B=500),
#             dale_experiment_rig.FixedDistr(num_byteloads=1000, byteload_size_B=1000),
#             dale_experiment_rig.FixedDistr(num_byteloads=200, byteload_size_B=5000),
#             dale_experiment_rig.FixedDistr(num_byteloads=100, byteload_size_B=10000),
#             dale_experiment_rig.FixedDistr(num_byteloads=20, byteload_size_B=50000),
#             dale_experiment_rig.FixedDistr(num_byteloads=10, byteload_size_B=100000),
#             dale_experiment_rig.FixedDistr(num_byteloads=2, byteload_size_B=500000),
#             dale_experiment_rig.FixedDistr(num_byteloads=1, byteload_size_B=1000000),
#             ],
#         target_mean_flow_interarr_ns=0,
#         is_use_poisson_byteload_intervals=False,
#         is_use_poisson_flow_interarr=False,
#         ssird_sim_dur_list=[0.01]*8,
#         dctcp_sim_dur_list=[0.01]*8,
#         xpass_sim_dur_list=[0.01]*8,
#         is_full_postproc=True,
#         title_prefix="FE_1rtt_delay_",
#         title_addendum="_500Bto1MB_5usRTT",
#         log_level=dale_experiment_rig.LOG_LEVEL_2,
#         experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
#     ) 

def onertt_delay_p2p_lowload():
    ''' 1 to 1 point-to-point experiment '''
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # run_experiment(
    #     proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='6-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(0,1)],
    #     num_flows_list=[40]*6,
    #     byteload_size_B_list=[500, 1000, 5000, 10000, 50000, 100000],
    #     target_mean_byteload_interval_nanosec_list=[5000, 10000, 50000, 100000, 500000, 1000000], 
    #     max_interval_nanosec_list=[5000, 10000, 50000, 100000, 500000, 1000000],
    #     flow_size_distr_list=[
    #         dale_experiment_rig.FixedDistr(num_byteloads=2000, byteload_size_B=500),
    #         dale_experiment_rig.FixedDistr(num_byteloads=1000, byteload_size_B=1000),
    #         dale_experiment_rig.FixedDistr(num_byteloads=200, byteload_size_B=5000),
    #         dale_experiment_rig.FixedDistr(num_byteloads=100, byteload_size_B=10000),
    #         dale_experiment_rig.FixedDistr(num_byteloads=20, byteload_size_B=50000),
    #         dale_experiment_rig.FixedDistr(num_byteloads=10, byteload_size_B=100000)
    #         ],
    #     target_mean_flow_interarr_ns=0,
    #     is_use_poisson_byteload_intervals=False,
    #     is_use_poisson_flow_interarr=False,
    #     ssird_sim_dur_list=[0.02]*6,
    #     dctcp_sim_dur_list=[0.02]*6,
    #     xpass_sim_dur_list=[0.02]*6,
    #     is_full_postproc=True,
    #     title_prefix="FE_1rtt_delay_",
    #     title_addendum="_500Bto100KB_0pt8GbpsFlo_5usRTT_allproto",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    run_experiment(
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='20-hosts-1msRTT.yaml',
        src_dst_pairs_list=[(0,10), (1,11), (2,12), (3,13), (4,14), (5,15), (6,16), (7,17), (8,18), (9,19)],
        num_flows_list=[1]*6,
        byteload_size_B_list=[500, 1000, 5000, 10000, 50000, 100000],
        target_mean_byteload_interval_nanosec_list=[500, 1000, 5000, 10000, 50000, 100000], 
        max_interval_nanosec_list=[500, 1000, 5000, 10000, 50000, 100000],
        flow_size_distr_list=[
            dale_experiment_rig.FixedDistr(num_byteloads=2000, byteload_size_B=500),
            dale_experiment_rig.FixedDistr(num_byteloads=1000, byteload_size_B=1000),
            dale_experiment_rig.FixedDistr(num_byteloads=200, byteload_size_B=5000),
            dale_experiment_rig.FixedDistr(num_byteloads=100, byteload_size_B=10000),
            dale_experiment_rig.FixedDistr(num_byteloads=20, byteload_size_B=50000),
            dale_experiment_rig.FixedDistr(num_byteloads=10, byteload_size_B=100000)
            ],
        target_mean_flow_interarr_ns=0,
        is_use_poisson_byteload_intervals=False,
        is_use_poisson_flow_interarr=False,
        ssird_sim_dur_list=[0.015]*6,
        dctcp_sim_dur_list=[0.015]*6,
        xpass_sim_dur_list=[0.015]*6,
        is_full_postproc=True,
        title_prefix="FE_NEW_1rtt_delay_1msRTT_",
        title_addendum="_20host_500Bto100KB_8GbpsFlo_1msRTT_allproto_1flo",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_NEW_1rtt_delay_1msRTT_" + "_20host_500Bto100KB_8GbpsFlo_1msRTT_allproto")

def onertt_delay_p2p_flowrate_sweep():
    ''' 1 to 1 point-to-point experiment '''
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # run_experiment(
    #     proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='10-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(0,5), (1,6), (2,7), (3,8), (4,9)],
    #     num_flows_list=[2]*8,
    #     byteload_size_B_list=[1458]*8,
    #     target_mean_byteload_interval_nanosec_list=[2000, 1000, 800, 600, 400, 300, 200, 150], 
    #     max_interval_nanosec_list=[2000, 1000, 800, 600, 400, 300, 200, 150],
    #     flow_size_distr_list=[dale_experiment_rig.FixedDistr(num_byteloads=500, byteload_size_B=1458)]*8,
    #     target_mean_flow_interarr_ns=0,
    #     is_use_poisson_byteload_intervals=False,
    #     is_use_poisson_flow_interarr=False,
    #     ssird_sim_dur_list=[0.02]*8,
    #     dctcp_sim_dur_list=[0.02]*8,
    #     xpass_sim_dur_list=[0.02]*8,
    #     is_full_postproc=True,
    #     title_prefix="FE_1rtt_delay_flowrate_sweep_",
    #     title_addendum="_10flo_1458B_2000nsTo150ns_5usRTT_allproto_test",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted(),
    #     is_all_same_flowrate=False
    # ) 
    run_experiment(
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='20-hosts-1msRTT.yaml',
        src_dst_pairs_list=[(0,10), (1,11), (2,12), (3,13), (4,14), (5,15), (6,16), (7,17), (8,18), (9,19)],
        num_flows_list=[1]*8,
        byteload_size_B_list=[1458]*8,
        target_mean_byteload_interval_nanosec_list=[2000, 1000, 800, 600, 400, 300, 200, 150], 
        max_interval_nanosec_list=[2000, 1000, 800, 600, 400, 300, 200, 150],
        flow_size_distr_list=[dale_experiment_rig.FixedDistr(num_byteloads=500, byteload_size_B=1458)]*8,
        target_mean_flow_interarr_ns=0,
        is_use_poisson_byteload_intervals=False,
        is_use_poisson_flow_interarr=False,
        ssird_sim_dur_list=[0.015]*8,
        dctcp_sim_dur_list=[0.015]*8,
        xpass_sim_dur_list=[0.015]*8,
        is_full_postproc=True,
        title_prefix="FE_NEW_1rtt_delay_flowrate_sweep_1msRTT_",
        title_addendum="_20host_1458B_2000nsTo150ns_1msRTT_allproto_test",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted(),
        is_all_same_flowrate=False
    ) 
    print("FE_NEW_1rtt_delay_flowrate_sweep_1msRTT_"+"_20host_1458B_2000nsTo150ns_1msRTT_allproto_test")

''' 
    ========== INCAST EXPERIMENTS (LOAD TEST): ==========
'''

def incast_5to1_1458B_fabricated_heavy_middle_loadtest():
    run_experiment(
        proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='6-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
        num_flows_list=[5, 10, 20, 30, 40],
        byteload_size_B_list=[1458]*5,
        target_mean_byteload_interval_nanosec_list=[70]*5,
        max_interval_nanosec_list=[10000]*5,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Fabricated_Heavy_Middle.txt")]*5,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.001]*5,
        dctcp_sim_dur_list=[0.001]*5,
        xpass_sim_dur_list=[0.001]*5,
        is_full_postproc=True,
        title_prefix="FE_incast_6host_",
        title_addendum="_6host_topo_fabHvyMid_loadtest_70ns",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 

def incast_10to1_1458B_fabricated_heavy_middle_loadtest():
    # run_experiment(
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 20, 30, 40],
    #     byteload_size_B_list=[1458]*6,
    #     target_mean_byteload_interval_nanosec_list=[200]*6,
    #     max_interval_nanosec_list=[10000]*6,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Fabricated_Heavy_Middle.txt")]*6,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.005]*6,
    #     dctcp_sim_dur_list=[0.005]*6,
    #     xpass_sim_dur_list=[0.005]*6,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_",
    #     title_addendum="_12host_fabHvyMid_loadtest_200ns",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_10to1_12host_fabHvyMid_loadtest_200ns_2025-08-20T_10-08-04Z.json",
        proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 20, 30, 40],
        byteload_size_B_list=[1458]*6,
        target_mean_byteload_interval_nanosec_list=[200]*6,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Fabricated_Heavy_Middle.txt")]*6,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.005]*6,
        dctcp_sim_dur_list=[0.005]*6,
        xpass_sim_dur_list=[0.005]*6,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_",
        title_addendum="_12host_fabHvyMid_loadtest_200ns_fromjson",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("12host_favHvyMid_loadtest")

def incast_3to1_1458B_fbHadoopDist_loadtest():
    run_experiment(
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME],
        topo_yaml_file='4-hosts.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0)],
        num_flows_list=[5, 10],
        byteload_size_B_list=[1458, 1458],
        target_mean_byteload_interval_nanosec_list=[1000, 1000],
        max_interval_nanosec_list=[10000, 10000],
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*2,
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.01]*2,
        dctcp_sim_dur_list=[0.01]*2,
        xpass_sim_dur_list=[0.01]*2,
        is_full_postproc=True,
        title_prefix="FE_incast_",
        title_addendum="_4host_fbHadoopDist_loadtest",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 

def incast_5to1_1458B_fbHadoopDist_loadtest():
    run_experiment(
        proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='6-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
        num_flows_list=[5, 10, 20, 30, 40],
        byteload_size_B_list=[1458]*5,
        target_mean_byteload_interval_nanosec_list=[500]*5,
        max_interval_nanosec_list=[10000]*5,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*5,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.01]*5,
        dctcp_sim_dur_list=[0.01]*5,
        xpass_sim_dur_list=[0.01]*5,
        is_full_postproc=True,
        title_prefix="FE_incast_6host_",
        title_addendum="_6host_fbHadoopDist_loadtest_500ns",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 

def incast_10to1_1458B_fbHadoopDist_loadtest():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # run_experiment(
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 20, 30, 40],
    #     byteload_size_B_list=[1458]*6,
    #     target_mean_byteload_interval_nanosec_list=[300]*6,
    #     max_interval_nanosec_list=[10000]*6,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*6,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.02]*6,
    #     dctcp_sim_dur_list=[0.02]*6,
    #     xpass_sim_dur_list=[0.02]*6,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_",
    #     title_addendum="_12host_fbHadoopDist_loadtest_300ns",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # run_experiment_from_saved_json(
    #     saved_json_file="FE_incast_12host_10to1_12host_fbHadoopDist_loadtest_300ns_2025-08-22T_18-10-46Z.json",
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 20, 30, 40],
    #     byteload_size_B_list=[1458]*6,
    #     target_mean_byteload_interval_nanosec_list=[300]*6,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*6,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.005]*6,
    #     dctcp_sim_dur_list=[0.005]*6,
    #     xpass_sim_dur_list=[0.005]*6,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_",
    #     title_addendum="_12host_fbHadoopDist_loadtest_300ns_retry",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    run_experiment(
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 15, 20, 24, 26, 28, 30, 25, 40],
        byteload_size_B_list=[1458]*11,
        target_mean_byteload_interval_nanosec_list=[600]*11,
        max_interval_nanosec_list=[10000]*11,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*11,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.01]*11,
        dctcp_sim_dur_list=[0.01]*11,
        xpass_sim_dur_list=[0.01]*11,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_",
        title_addendum="_12host_fbHadoopDist_loadtest_300ns",   # NOTE: this shdve been 600ns
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("12host_fbHadoopDist_loadtest")

def incast_10to1_1458B_fbHadoopDist_loadtest_NEW():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    run_experiment(
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 15, 20, 25, 30, 35, 40, 44, 48],
        byteload_size_B_list=[1458]*11,
        target_mean_byteload_interval_nanosec_list=[800]*11,
        max_interval_nanosec_list=[20000]*11,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*11,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.1]*11,
        dctcp_sim_dur_list=[0.1]*11,
        xpass_sim_dur_list=[0.1]*11,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_NEW_PROBE2_",
        title_addendum="_12host_fbHadoopDist_loadtest_800ns",   # NOTE: this shdve been 600ns
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("12host_fbHadoopDist_loadtest")

def incast_20to1_1458B_fbHadoopDist_loadtest_NEW():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    run_experiment(
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='21-hosts.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0), (11,0), (12,0), (13,0), (14,0), (15,0), (16,0), (17,0), (18,0), (19,0), (20,0)],
        num_flows_list=[1, 5, 10, 15, 20, 25],
        byteload_size_B_list=[1458]*6,
        target_mean_byteload_interval_nanosec_list=[1000]*6,
        max_interval_nanosec_list=[10000]*6,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*6,
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.1]*6,
        dctcp_sim_dur_list=[0.1]*6,
        xpass_sim_dur_list=[0.1]*6,
        is_full_postproc=True,
        title_prefix="FE_incast_21host_NEW_PROBE_",
        title_addendum="_21host_fbHadoopDist_loadtest_1000ns",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("21host_fbHadoopDist_loadtest")

def incast_3to1_1458B_dctcpMsgSizeDist_loadtest():
    run_experiment(
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME],
        topo_yaml_file='4-hosts.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0)],
        num_flows_list=[5, 10],
        byteload_size_B_list=[1458, 1458],
        target_mean_byteload_interval_nanosec_list=[1000, 1000],
        max_interval_nanosec_list=[10000, 10000],
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="DCTCP_MsgSizeDist.txt")]*2,
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.01]*2,
        dctcp_sim_dur_list=[0.01]*2,
        xpass_sim_dur_list=[0.01]*2,
        is_full_postproc=True,
        title_prefix="FE_incast_",
        title_addendum="_4host_DctcpMsgSizeDist_loadtest",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 

def incast_5to1_1458B_dctcpMsgSizeDist_loadtest():
    run_experiment(
        proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='6-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
        num_flows_list=[5, 10, 20, 30, 40],
        byteload_size_B_list=[1458]*5,
        target_mean_byteload_interval_nanosec_list=[500]*5,
        max_interval_nanosec_list=[10000]*5,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="DCTCP_MsgSizeDist.txt")]*5,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.003]*5,
        dctcp_sim_dur_list=[0.003]*5,
        xpass_sim_dur_list=[0.003]*5,
        is_full_postproc=True,
        title_prefix="FE_incast_6host_",
        title_addendum="_6host_DctcpMsgSizeDist_loadtest_500ns",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 

def incast_10to1_1458B_dctcpMsgSizeDist_loadtest():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    run_experiment(
        proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 15, 20, 30, 40],
        byteload_size_B_list=[1458]*7,
        target_mean_byteload_interval_nanosec_list=[800]*7,
        max_interval_nanosec_list=[10000]*7,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="DCTCP_MsgSizeDist.txt")]*7,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.003]*7,
        dctcp_sim_dur_list=[0.003]*7,
        xpass_sim_dur_list=[0.003]*7,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_v2_",
        title_addendum="_12host_DctcpMsgSizeDist_loadtest_800ns_v2",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    # run_experiment_from_saved_json(
    #     saved_json_file="FE_incast_12host_10to1_12host_DctcpMsgSizeDist_loadtest_800ns_2025-08-20T_10-12-29Z.json",
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 20, 30, 40],
    #     byteload_size_B_list=[1458]*6,
    #     target_mean_byteload_interval_nanosec_list=[800]*6,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="DCTCP_MsgSizeDist.txt")]*6,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.01]*6,
    #     dctcp_sim_dur_list=[0.01]*6,
    #     xpass_sim_dur_list=[0.01]*6,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_",
    #     title_addendum="_12host_DctcpMsgSizeDist_loadtest_800ns_fromjson",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    print("12host_dctcpMsgSizeDist_loadtest")

def incast_10to1_1458B_fbCacheFollowerDist_loadtest():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # run_experiment(
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 20, 30, 40],
    #     byteload_size_B_list=[1458]*6,
    #     target_mean_byteload_interval_nanosec_list=[5000]*6,
    #     max_interval_nanosec_list=[10000]*6,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_CacheFollowerDist_IntraCluster.txt")]*6,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.08]*6,
    #     dctcp_sim_dur_list=[0.08]*6,
    #     xpass_sim_dur_list=[0.08]*6,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_",
    #     title_addendum="_12host_fbCacheFollowerDist_loadtest_5000ns_1to40flo",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # run_experiment_from_saved_json(
    #     saved_json_file="FE_incast_12host_10to1_12host_fbCacheFollowerDist_loadtest_5000ns_1to40flo_2025-08-20T_22-41-02Z.json",
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 20, 30, 40],
    #     byteload_size_B_list=[1458]*6,
    #     target_mean_byteload_interval_nanosec_list=[5000]*6,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_CacheFollowerDist_IntraCluster.txt")]*6,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.08]*6,
    #     dctcp_sim_dur_list=[0.08]*6,
    #     xpass_sim_dur_list=[0.08]*6,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_",
    #     title_addendum="_12host_fbCacheFollowerDist_loadtest_5000ns_1to40flo_retry",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    run_experiment(
        # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 14, 17, 20, 25, 30, 40],
        byteload_size_B_list=[1458]*9,
        target_mean_byteload_interval_nanosec_list=[5000]*9,
        max_interval_nanosec_list=[10000]*9,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_CacheFollowerDist_IntraCluster.txt")]*9,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.1]*9,
        dctcp_sim_dur_list=[0.1]*9,
        xpass_sim_dur_list=[0.1]*9,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_",
        title_addendum="_12host_fbCacheFollowerDist_loadtest_5000ns_1to40flo",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("12host_fbCacheFollowerDist_loadtest")

def incast_10to1_1458B_fbCacheFollowerDist_loadtest_NEW():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    run_experiment(
        # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        byteload_size_B_list=[1458]*10,
        target_mean_byteload_interval_nanosec_list=[5000]*10,
        max_interval_nanosec_list=[10000]*10,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_CacheFollowerDist_IntraCluster.txt")]*10,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.1]*10,
        dctcp_sim_dur_list=[0.1]*10,
        xpass_sim_dur_list=[0.1]*10,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_NEW_PROBE2_",
        title_addendum="_12host_fbCacheFollowerDist_loadtest_5Kns",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("12host_fbCacheFollowerDist_loadtest")

def incast_20to1_1458B_fbCacheFollowerDist_loadtest_NEW():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    run_experiment(
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='21-hosts.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0), (11,0), (12,0), (13,0), (14,0), (15,0), (16,0), (17,0), (18,0), (19,0), (20,0)],
        num_flows_list=[1, 5, 10, 15, 20, 25],
        byteload_size_B_list=[1458]*6,
        target_mean_byteload_interval_nanosec_list=[6000]*6,
        max_interval_nanosec_list=[30000]*6,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_CacheFollowerDist_IntraCluster.txt")]*6,
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.1]*6,
        dctcp_sim_dur_list=[0.1]*6,
        xpass_sim_dur_list=[0.1]*6,
        is_full_postproc=True,
        title_prefix="FE_incast_21host_NEW_PROBE_",
        title_addendum="_21host_fbCacheFollowerDist_loadtest_5000ns",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("21host_fbCacheFollowerDist_loadtest")

def incast_3to1_1458B_googleAllRpc_loadtest():
    run_experiment(
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME],
        topo_yaml_file='4-hosts.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0)],
        num_flows_list=[5, 10, 20],
        byteload_size_B_list=[1458]*3,
        target_mean_byteload_interval_nanosec_list=[1000]*3,
        max_interval_nanosec_list=[10000]*3,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Google_AllRPC.txt")]*3,
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.01]*3,
        dctcp_sim_dur_list=[0.01]*3,
        xpass_sim_dur_list=[0.01]*3,
        is_full_postproc=True,
        title_prefix="FE_incast_",
        title_addendum="_4host_GoogleAllRPC_loadtest",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 

def incast_5to1_1458B_googleAllRpc_loadtest():
    run_experiment(
        proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='6-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
        num_flows_list=[5, 10, 20, 30, 40],
        byteload_size_B_list=[1458]*5,
        target_mean_byteload_interval_nanosec_list=[500]*5,
        max_interval_nanosec_list=[10000]*5,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Google_AllRPC.txt")]*5,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.003]*5,
        dctcp_sim_dur_list=[0.003]*5,
        xpass_sim_dur_list=[0.003]*5,
        is_full_postproc=True,
        title_prefix="FE_incast_6host_",
        title_addendum="_6host_GoogleAllRPC_loadtest_500ns",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 

def incast_10to1_1458B_googleAllRpc_loadtest():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # run_experiment(
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[5, 10, 20, 30, 40, 50],
    #     byteload_size_B_list=[1458]*6,
    #     target_mean_byteload_interval_nanosec_list=[300]*6,
    #     max_interval_nanosec_list=[10000]*6,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Google_AllRPC.txt")]*6,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.005]*6,
    #     dctcp_sim_dur_list=[0.005]*6,
    #     xpass_sim_dur_list=[0.005]*6,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_",
    #     title_addendum="_12host_GoogleAllRPC_loadtest_300ns",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_10to1_12host_GoogleAllRPC_loadtest_300ns_2025-08-25T_19-31-25Z.json",
        proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[5, 10, 20, 30, 40, 50],
        byteload_size_B_list=[1458]*6,
        target_mean_byteload_interval_nanosec_list=[300]*6,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Google_AllRPC.txt")]*6,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.002]*6,
        dctcp_sim_dur_list=[0.002]*6,
        xpass_sim_dur_list=[0.002]*6,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_",
        title_addendum="_12host_GoogleAllRPC_loadtest_300ns_retry",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("12host_googleAllRpc_loadtest")

def incast_10to1_1458B_expDistr_loadtest():
    run_experiment(
        proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 2, 3, 5, 10, 15, 20, 25],
        byteload_size_B_list=[1458]*8,
        target_mean_byteload_interval_nanosec_list=[10000]*8,
        max_interval_nanosec_list=[100000]*8,
        flow_size_distr_list=[dale_experiment_rig.ExpDistr(
            byteload_size_B=1458,
            avg_num_byteloads=500,
            min_num_byteloads=10,
            max_num_byteloads=2000
        )]*8,
        target_mean_flow_interarr_ns=10000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.03]*8,
        dctcp_sim_dur_list=[0.03]*8,
        xpass_sim_dur_list=[0.03]*8,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_",
        title_addendum="_12host_ExpDistr_loadtest_10000ns",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("12host_ExpDistr_loadtest")

def incast_10to1_1458B_dctcpMsgSizeDistActual_loadtest():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # run_experiment(
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     # topo_yaml_file='12-hosts-dumbbell.yaml',
    #     topo_yaml_file='6-hosts-dumbbell.yaml',
    #     # src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
    #     num_flows_list=[1, 5, 10, 15, 20, 25, 30],
    #     byteload_size_B_list=[1458]*7,
    #     target_mean_byteload_interval_nanosec_list=[1000]*7,
    #     max_interval_nanosec_list=[20000]*7,
    #     flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*7,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.1]*7,
    #     dctcp_sim_dur_list=[0.1]*7,
    #     xpass_sim_dur_list=[0.1]*7,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_",
    #     title_addendum="_6host_DctcpMsgSizeDistActual_loadtest_1Kns",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # run_experiment_from_saved_json(
    #     saved_json_file="FE_incast_12host_5to1_6host_DctcpMsgSizeDistActual_loadtest_1Kns_2025-08-25T_20-37-43Z.json",
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     # topo_yaml_file='12-hosts-dumbbell.yaml',
    #     topo_yaml_file='6-hosts-dumbbell.yaml',
    #     # src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
    #     num_flows_list=[1, 5, 10, 15, 20, 25, 30],
    #     byteload_size_B_list=[1458]*7,
    #     target_mean_byteload_interval_nanosec_list=[1000]*7,
    #     flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*7,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.07]*7,
    #     dctcp_sim_dur_list=[0.07]*7,
    #     xpass_sim_dur_list=[0.07]*7,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_",
    #     title_addendum="_6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # run_experiment(
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     # topo_yaml_file='6-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     # src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
    #     num_flows_list=[1, 5, 10, 15, 20, 25, 30],
    #     byteload_size_B_list=[1458]*7,
    #     target_mean_byteload_interval_nanosec_list=[2000]*7,
    #     max_interval_nanosec_list=[20000]*7,
    #     flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*7,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.1]*7,
    #     dctcp_sim_dur_list=[0.1]*7,
    #     xpass_sim_dur_list=[0.1]*7,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_",
    #     title_addendum="_12host_DctcpMsgSizeDistActual_loadtest_2Kns",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # run_experiment_from_saved_json(
    #     saved_json_file="FE_incast_12host_10to1_12host_DctcpMsgSizeDistActual_loadtest_2Kns_2025-08-26T_10-36-29Z.json",
    #     # saved_json_file="FE_incast_12host_10to1_12host_DctcpMsgSizeDistActual_loadtest_2Kns_2025-08-26T_12-17-15Z.json",
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     # topo_yaml_file='6-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     # src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
    #     num_flows_list=[1, 5, 10, 15, 20, 25, 30],
    #     byteload_size_B_list=[1458]*7,
    #     target_mean_byteload_interval_nanosec_list=[2000]*7,
    #     flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*7,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.083]*7,
    #     dctcp_sim_dur_list=[0.083]*7,
    #     xpass_sim_dur_list=[0.083]*7,
    #     # ssird_sim_dur_list=[0.15]*7,
    #     # dctcp_sim_dur_list=[0.15]*7,
    #     # xpass_sim_dur_list=[0.15]*7,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_",
    #     title_addendum="_12host_DctcpMsgSizeDistActual_loadtest_2Kns_retry",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    run_experiment(
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        # topo_yaml_file='6-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        # src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
        num_flows_list=[1, 5, 8, 12, 14, 16, 18, 20, 25, 30],
        byteload_size_B_list=[1458]*10,
        target_mean_byteload_interval_nanosec_list=[2000]*10,
        max_interval_nanosec_list=[20000]*10,
        flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*10,
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.1]*10,
        dctcp_sim_dur_list=[0.1]*10,
        xpass_sim_dur_list=[0.1]*10,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_",
        title_addendum="_12host_DctcpMsgSizeDistActual_loadtest_2Kns",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("12host_dctcpMsgSizeDistActual_loadtest")

def incast_10to1_1458B_dctcpMsgSizeDistActual_loadtest_NEW():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    run_experiment(
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 4, 6, 8, 10, 12, 13, 14, 15, 16],
        byteload_size_B_list=[1458]*10,
        target_mean_byteload_interval_nanosec_list=[2000]*10,
        max_interval_nanosec_list=[20000]*10,
        flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*10,
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.1]*10,
        dctcp_sim_dur_list=[0.1]*10,
        xpass_sim_dur_list=[0.1]*10,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_NEW_PROBE2_",
        title_addendum="_12host_DctcpMsgSizeDistActual_loadtest_2Kns",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("12host_dctcpMsgSizeDistActual_loadtest")

''' 
    ========== INCAST EXPERIMENTS (FULL LOAD SWEEP): ==========
'''

def incast_10to1_1458B_fabHvyMid_load_fullsweep():
    # run_experiment(
    #     proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 2, 3, 4, 5, 7, 10, 20, 30, 40],
    #     byteload_size_B_list=[1458]*10,
    #     target_mean_byteload_interval_nanosec_list=[100]*10,
    #     max_interval_nanosec_list=[10000]*10,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Fabricated_Heavy_Middle.txt")]*10,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.003]*10,
    #     dctcp_sim_dur_list=[0.003]*10,
    #     xpass_sim_dur_list=[0.003]*10,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_fullsweep_",
    #     title_addendum="_10host_fabHvyMid_load_fullsweep",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_10to1_12host_fabHvyMid_loadtest_200ns_2025-08-20T_10-08-04Z.json",
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 20, 30, 40],
        byteload_size_B_list=[1458]*6,
        target_mean_byteload_interval_nanosec_list=[200]*6,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Fabricated_Heavy_Middle.txt")]*6,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.002]*6,
        dctcp_sim_dur_list=[0.002]*6,
        xpass_sim_dur_list=[0.002]*6,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_fullsweep_",
        title_addendum="_12host_fabHvyMid_load_fullsweep_200ns_fromjson",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_incast_fullsweep_"+"_12host_fabHvyMid_load_fullsweep")

def incast_10to1_1458B_fbHadoopDist_load_fullsweep():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    assert(dale_experiment_rig.DCTCP_ECN_MARKING_THRESHOLD == "61")
    ''' USE THIS WORKLOAD DISTRIBUTION & FLOWSPEC FILE! '''
    # run_experiment_from_saved_json(
    #     saved_json_file="FE_incast_12host_10to1_12host_fbHadoopDist_loadtest_300ns_2025-08-22T_18-10-46Z.json",
    #     # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 20, 30, 40],
    #     byteload_size_B_list=[1458]*6,
    #     target_mean_byteload_interval_nanosec_list=[300]*6,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*6,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.005]*6,
    #     dctcp_sim_dur_list=[0.005]*6,
    #     xpass_sim_dur_list=[0.005]*6,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_fullsweep_",
    #     # title_addendum="_12host_fbHadoopDist_load_fullsweep_300ns_fromjson",
    #     title_addendum="_12host_fbHadoopDist_load_fullsweep_300ns_fromjson_dctcp61-49",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # # print("FE_incast_12host_fullsweep_"+"_12host_fbHadoopDist_load_fullsweep_300ns_fromjson")
    # print("FE_incast_12host_fullsweep_"+"_12host_fbHadoopDist_load_fullsweep_300ns_fromjson_dctcp61-49")
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_10to1_12host_fbHadoopDist_loadtest_300ns_2025-08-27T_15-45-48Z.json",
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME],
        # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 15, 20, 24, 26, 28, 30, 25, 40],
        byteload_size_B_list=[1458]*11,
        target_mean_byteload_interval_nanosec_list=[600]*11,
        # max_interval_nanosec_list=[10000]*11,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*11,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.009]*11,
        dctcp_sim_dur_list=[0.009]*11,
        xpass_sim_dur_list=[0.009]*11,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_fullsweep_v3_",
        # title_addendum="_12host_fbHadoopDist_loadtest_300ns_retry_dctcp",   # NOTE: this shdve been 600ns
        title_addendum="_12host_fbHadoopDist_loadtest_300ns_retry_xpass",   # NOTE: this shdve been 300ns
        # title_addendum="_12host_fbHadoopDist_load_fullsweep_300ns_fromjson_ssird",  # NOTE: this should've been 600ns
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_incast_12host_fullsweep_v3_"+"_12host_fbHadoopDist_load_fullsweep_300ns_fromjson")

def incast_10to1_1458B_fbHadoopDist_800ns_load_fullsweep_v5():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    assert(dale_experiment_rig.DCTCP_ECN_MARKING_THRESHOLD == "61")
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_NEW_PROBE2_10to1_12host_fbHadoopDist_loadtest_800ns_2025-08-31T_16-46-59Z.json",
        # proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME],
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 15, 20, 25, 30, 35, 40, 44, 48],
        byteload_size_B_list=[1458]*11,
        target_mean_byteload_interval_nanosec_list=[800]*11,
        # max_interval_nanosec_list=[20000]*11,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*11,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.009]*11,
        dctcp_sim_dur_list=[0.009]*11,
        xpass_sim_dur_list=[0.009]*11,
        is_full_postproc=True,
        title_prefix="FE_NEW_incast_12host_fullsweep_v5_",
        # title_addendum="_12host_fbHadoopDist_loadtest_800ns_fromjson_xpass",
        # title_addendum="_12host_fbHadoopDist_loadtest_800ns_fromjson_dctcp",
        title_addendum="_12host_fbHadoopDist_loadtest_800ns_fromjson_ssird",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_NEW_incast_12host_fullsweep_v5_" + "_12host_fbHadoopDist_loadtest_800ns_fromjson_xpass")

def incast_10to1_1458B_dctcpMsgSizeDist_load_fullsweep():
    # run_experiment(
    #     proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 15, 20, 30, 40],
    #     byteload_size_B_list=[1458]*7,
    #     target_mean_byteload_interval_nanosec_list=[800]*7,
    #     max_interval_nanosec_list=[10000]*7,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="DCTCP_MsgSizeDist.txt")]*7,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.002]*7,
    #     dctcp_sim_dur_list=[0.002]*7,
    #     xpass_sim_dur_list=[0.002]*7,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_fullsweep_v2_",
    #     title_addendum="_12host_DctcpMsgSizeDist_load_fullsweep_800ns_v2",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    ''' USE THIS WORKLOAD DISTRIBUTION & FLOWSPEC FILE! '''
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_10to1_12host_DctcpMsgSizeDist_loadtest_800ns_2025-08-20T_10-12-29Z.json",
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 20, 30, 40],
        byteload_size_B_list=[1458]*6,
        target_mean_byteload_interval_nanosec_list=[800]*6,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="DCTCP_MsgSizeDist.txt")]*6,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.002]*6,
        dctcp_sim_dur_list=[0.002]*6,
        xpass_sim_dur_list=[0.002]*6,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_fullsweep_",
        title_addendum="_12host_DctcpMsgSizeDist_load_fullsweep_800ns_fromjson",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_incast_fullsweep_"+"_12host_DctcpMsgSizeDist_load_fullsweep")

def incast_10to1_1458B_fbCacheFollowerDist_load_fullsweep():
    ''' USE THIS WORKLOAD DISTRIBUTION & FLOWSPEC FILE! '''
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    assert(dale_experiment_rig.DCTCP_ECN_MARKING_THRESHOLD == "61")
    # run_experiment_from_saved_json(
    #     saved_json_file="FE_incast_12host_10to1_12host_fbCacheFollowerDist_loadtest_5000ns_1to40flo_2025-08-20T_22-41-02Z.json",
    #     proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 20, 30, 40],
    #     byteload_size_B_list=[1458]*6,
    #     target_mean_byteload_interval_nanosec_list=[5000]*6,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_CacheFollowerDist_IntraCluster.txt")]*6,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.032]*6,
    #     dctcp_sim_dur_list=[0.05]*6,
    #     xpass_sim_dur_list=[0.05]*6,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_fullsweep_",
    #     title_addendum="_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # run_experiment_from_saved_json(
    #     saved_json_file="FE_incast_12host_10to1_12host_fbCacheFollowerDist_loadtest_5000ns_1to40flo_2025-08-20T_22-41-02Z.json",
    #     # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 20, 30, 40],
    #     byteload_size_B_list=[1458]*6,
    #     target_mean_byteload_interval_nanosec_list=[5000]*6,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_CacheFollowerDist_IntraCluster.txt")]*6,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.032]*6,
    #     dctcp_sim_dur_list=[0.05]*6,
    #     xpass_sim_dur_list=[0.05]*6,
    #     is_full_postproc=True,
    #     # title_prefix="FE_incast_12host_fullsweep_dctcp_xpass_",
    #     title_prefix="FE_incast_12host_fullsweep_",
    #     # title_addendum="_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp_xpass",
    #     title_addendum="_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_dctcp61-49",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # print("FE_incast_fullsweep_"+"_12host_fbCacheFollowerDist_load_fullsweep_dctcp61-49")
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_10to1_12host_fbCacheFollowerDist_loadtest_5000ns_1to40flo_2025-08-27T_13-42-30Z.json",
        # proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME],
        # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 14, 17, 20, 25, 30, 40],
        byteload_size_B_list=[1458]*9,
        target_mean_byteload_interval_nanosec_list=[5000]*9,
        # max_interval_nanosec_list=[10000]*9,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_CacheFollowerDist_IntraCluster.txt")]*9,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.035]*9,
        dctcp_sim_dur_list=[0.035]*9,
        xpass_sim_dur_list=[0.035]*9,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_fullsweep_v3_",
        title_addendum="_12host_fbCacheFollowerDist_loadtest_5000ns_1to40flo_retry_dctcp",
        # title_addendum="_12host_fbCacheFollowerDist_loadtest_5000ns_1to40flo_retry_xpass",
        # title_addendum="_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_ssird",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_incast_fullsweep_"+"_12host_fbCacheFollowerDist_load_fullsweep_fromjson")

def incast_10to1_1458B_fbCacheFollowerDist_load_fullsweep_v5():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    assert(dale_experiment_rig.DCTCP_ECN_MARKING_THRESHOLD == "61")
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_NEW_PROBE2_10to1_12host_fbCacheFollowerDist_loadtest_5Kns_2025-08-31T_14-17-55Z.json",
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME],
        # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        byteload_size_B_list=[1458]*10,
        target_mean_byteload_interval_nanosec_list=[5000]*10,
        # max_interval_nanosec_list=[10000]*10,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_CacheFollowerDist_IntraCluster.txt")]*10,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.035]*10,
        dctcp_sim_dur_list=[0.035]*10,
        xpass_sim_dur_list=[0.035]*10,
        is_full_postproc=True,
        title_prefix="FE_NEW_incast_12host_fullsweep_v5_",
        title_addendum="_12host_fbCacheFollowerDist_loadtest_5Kns_fromjson_xpass",
        # title_addendum="_12host_fbCacheFollowerDist_loadtest_5Kns_fromjson_dctcp",
        # title_addendum="_12host_fbCacheFollowerDist_loadtest_5Kns_fromjson_ssird",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 

def incast_10to1_1458B_googleAllRpc_load_fullsweep():
    ''' USE THIS WORKLOAD DISTRIBUTION & FLOWSPEC FILE! '''
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_10to1_12host_GoogleAllRPC_loadtest_300ns_2025-08-25T_19-31-25Z.json",
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[5, 10, 20, 30, 40, 50],
        byteload_size_B_list=[1458]*6,
        target_mean_byteload_interval_nanosec_list=[300]*6,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Google_AllRPC.txt")]*6,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.0006]*6,
        dctcp_sim_dur_list=[0.0006]*6,
        xpass_sim_dur_list=[0.0006]*6,
        # ssird_sim_dur_list=[0.001]*6,
        # dctcp_sim_dur_list=[0.001]*6,
        # xpass_sim_dur_list=[0.001]*6,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_fullsweep_",
        title_addendum="_12host_GoogleAllRPC_load_fullsweep_300ns_fromjson",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_incast_12host_fullsweep_"+"_12host_GoogleAllRPC_loadtest_300ns_fromjson")

def incast_5to1_1458B_dctcpMsgSizeDistActual_load_fullsweep():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    assert(dale_experiment_rig.DCTCP_ECN_MARKING_THRESHOLD == "61")
    # assert(dale_experiment_rig.DCTCP_ECN_MARKING_THRESHOLD == "82")
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_5to1_6host_DctcpMsgSizeDistActual_loadtest_1Kns_2025-08-25T_20-37-43Z.json",
        # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME],
        topo_yaml_file='6-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
        num_flows_list=[1, 5, 10, 15, 20, 25, 30],
        byteload_size_B_list=[1458]*7,
        target_mean_byteload_interval_nanosec_list=[1000]*7,
        flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*7,
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.055]*7,
        dctcp_sim_dur_list=[0.055]*7,
        xpass_sim_dur_list=[0.055]*7,
        # ssird_sim_dur_list=[0.07]*7,
        # dctcp_sim_dur_list=[0.07]*7,
        # xpass_sim_dur_list=[0.07]*7,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_fullsweep_",
        # title_addendum="_6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson",
        title_addendum="_6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson_dctcp61-49",
        # title_addendum="_6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson_dctcp82-49",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_incast_12host_fullsweep_"+"_6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson_dctcp61-49")
    # print("FE_incast_12host_fullsweep_"+"_6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson_dctcp82-49")

def incast_10to1_1458B_dctcpMsgSizeDistActual_load_fullsweep():
    ''' USE THIS WORKLOAD DISTRIBUTION & FLOWSPEC FILE! '''
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    assert(dale_experiment_rig.DCTCP_ECN_MARKING_THRESHOLD == "61")

    # run_experiment_from_saved_json(
    #     saved_json_file="FE_incast_12host_10to1_12host_DctcpMsgSizeDistActual_loadtest_2Kns_2025-08-26T_10-36-29Z.json",
    #     # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 15, 20, 25, 30],
    #     byteload_size_B_list=[1458]*7,
    #     target_mean_byteload_interval_nanosec_list=[2000]*7,
    #     flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*7,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.085]*7,
    #     dctcp_sim_dur_list=[0.085]*7,
    #     xpass_sim_dur_list=[0.085]*7,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_fullsweep_",
    #     # title_addendum="_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson",
    #     title_addendum="_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson_dctcp61-49",
    #     # title_addendum="_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson_dctcp82-49",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # # print("FE_incast_12host_fullsweep_"+"_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson")
    # print("FE_incast_12host_fullsweep_"+"_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson_dctcp61-49")
    # print("FE_incast_12host_fullsweep_"+"_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson_dctcp82-49")

    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_10to1_12host_DctcpMsgSizeDistActual_loadtest_2Kns_2025-08-27T_14-43-35Z.json",
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME],
        # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 8, 12, 14, 16, 18, 20, 25, 30],
        byteload_size_B_list=[1458]*10,
        target_mean_byteload_interval_nanosec_list=[2000]*10,
        # max_interval_nanosec_list=[20000]*10,
        flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*10,
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.09]*10,
        dctcp_sim_dur_list=[0.09]*10,
        xpass_sim_dur_list=[0.09]*10,
        is_full_postproc=True,
        title_prefix="FE_NEW_incast_12host_fullsweep_",
        # title_addendum="_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson_dctcp61-49",
        title_addendum="_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson_xpass",
        # title_addendum="_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson_ssird",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_NEW_incast_12host_fullsweep_"+"_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson")

def incast_10to1_1458B_dctcpMsgSizeDistActual_load_fullsweep_v5():
    ''' USE THIS WORKLOAD DISTRIBUTION & FLOWSPEC FILE! '''
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    assert(dale_experiment_rig.DCTCP_ECN_MARKING_THRESHOLD == "61")
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_NEW_PROBE2_10to1_12host_DctcpMsgSizeDistActual_loadtest_2Kns_2025-08-31T_12-38-03Z.json",
        # proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME],
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 4, 6, 8, 10, 12, 13, 14, 15, 16],
        byteload_size_B_list=[1458]*10,
        target_mean_byteload_interval_nanosec_list=[2000]*10,
        # max_interval_nanosec_list=[20000]*10,
        flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*10,
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.065]*10,
        dctcp_sim_dur_list=[0.06]*10,
        xpass_sim_dur_list=[0.06]*10,
        is_full_postproc=True,
        title_prefix="FE_NEW_incast_12host_fullsweep_v5_",
        # title_addendum="_12host_DctcpMsgSizeDistActual_loadtest_2Kns_fromjson_xpass",
        # title_addendum="_12host_DctcpMsgSizeDistActual_loadtest_2Kns_fromjson_dctcp",
        title_addendum="_12host_DctcpMsgSizeDistActual_loadtest_2Kns_fromjson_ssird",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_NEW_incast_12host_fullsweep_v5_"+"_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson")

''' 
    ========== INCAST SSIRD FAIRSHARE POLICY EXPERIMENTS (FULL LOAD SWEEP): ==========
'''

def incast_10to1_1458B_googleAllRpc_load_fullsweep_ssird_policy_fairshare():
    ''' USE THIS WORKLOAD DISTRIBUTION & FLOWSPEC FILE! '''
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.FAIRSHARE)
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_10to1_12host_GoogleAllRPC_loadtest_300ns_2025-08-25T_19-31-25Z.json",
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[5, 10, 20, 30, 40, 50],
        byteload_size_B_list=[1458]*6,
        target_mean_byteload_interval_nanosec_list=[300]*6,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Google_AllRPC.txt")]*6,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.0002]*6,
        dctcp_sim_dur_list=[0.0006]*6,
        xpass_sim_dur_list=[0.0006]*6,
        # ssird_sim_dur_list=[0.001]*6,
        # dctcp_sim_dur_list=[0.001]*6,
        # xpass_sim_dur_list=[0.001]*6,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_fullsweep_ssird_policy_",
        title_addendum="_12host_GoogleAllRPC_load_fullsweep_300ns_fromjson_ssird_fairshare",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_incast_12host_fullsweep_ssird_policy_"+"_12host_GoogleAllRPC_loadtest_300ns_fromjson_fairshare")

def incast_10to1_1458B_fbHadoopDist_load_fullsweep_ssird_policy_fairshare():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.FAIRSHARE)
    ''' USE THIS WORKLOAD DISTRIBUTION & FLOWSPEC FILE! '''
    # run_experiment_from_saved_json(
    #     saved_json_file="FE_incast_12host_10to1_12host_fbHadoopDist_loadtest_300ns_2025-08-22T_18-10-46Z.json",
    #     proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 20, 30, 40],
    #     byteload_size_B_list=[1458]*6,
    #     target_mean_byteload_interval_nanosec_list=[300]*6,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*6,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.005]*6,
    #     dctcp_sim_dur_list=[0.005]*6,
    #     xpass_sim_dur_list=[0.005]*6,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_fullsweep_ssird_policy_",
    #     title_addendum="_12host_fbHadoopDist_load_fullsweep_300ns_fromjson_ssird_fairshare",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # print("FE_incast_12host_fullsweep_ssird_policy_"+"_12host_fbHadoopDist_load_fullsweep_300ns_fromjson_fairshare")
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_10to1_12host_fbHadoopDist_loadtest_300ns_2025-08-27T_15-45-48Z.json",
        # proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME],
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 15, 20, 24, 26, 28, 30, 25, 40],
        byteload_size_B_list=[1458]*11,
        target_mean_byteload_interval_nanosec_list=[600]*11,
        # max_interval_nanosec_list=[10000]*11,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*11,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.009]*11,
        dctcp_sim_dur_list=[0.009]*11,
        xpass_sim_dur_list=[0.009]*11,
        is_full_postproc=True,
        # title_prefix="FE_incast_12host_",
        # title_addendum="_12host_fbHadoopDist_loadtest_300ns_retry_dctcp",
        # title_addendum="_12host_fbHadoopDist_loadtest_300ns_retry_xpass",
        # title_prefix="FE_incast_12host_fullsweep_v3_",
        title_prefix="FE_incast_12host_fullsweep_ssird_policy_v3_",
        title_addendum="_12host_fbHadoopDist_load_fullsweep_300ns_fromjson_ssird_fairshare",    # NOTE: this shdve been 600ns
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_incast_12host_fullsweep_ssird_policy_v3_"+"_12host_fbHadoopDist_load_fullsweep_300ns_fromjson_ssird_fairshare")

def incast_10to1_1458B_fbHadoopDist_800ns_load_fullsweep_ssird_policy_fairshare_v5():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.FAIRSHARE)
    assert(dale_experiment_rig.DCTCP_ECN_MARKING_THRESHOLD == "61")
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_NEW_PROBE2_10to1_12host_fbHadoopDist_loadtest_800ns_2025-08-31T_16-46-59Z.json",
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 15, 20, 25, 30, 35, 40, 44, 48],
        byteload_size_B_list=[1458]*11,
        target_mean_byteload_interval_nanosec_list=[800]*11,
        # max_interval_nanosec_list=[20000]*11,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*11,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.009]*11,
        dctcp_sim_dur_list=[0.009]*11,
        xpass_sim_dur_list=[0.009]*11,
        is_full_postproc=True,
        title_prefix="FE_NEW_incast_12host_fullsweep_v5_policy_",
        title_addendum="_12host_fbHadoopDist_loadtest_800ns_fromjson_ssird_fairshare",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_NEW_incast_12host_fullsweep_v5_" + "_12host_fbHadoopDist_loadtest_800ns_fromjson_xpass")

def incast_10to1_1458B_dctcpMsgSizeDist_load_fullsweep_ssird_policy_fairshare():
    ''' USE THIS WORKLOAD DISTRIBUTION & FLOWSPEC FILE! '''
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.FAIRSHARE)
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_10to1_12host_DctcpMsgSizeDist_loadtest_800ns_2025-08-20T_10-12-29Z.json",
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 20, 30, 40],
        byteload_size_B_list=[1458]*6,
        target_mean_byteload_interval_nanosec_list=[800]*6,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="DCTCP_MsgSizeDist.txt")]*6,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.002]*6,
        dctcp_sim_dur_list=[0.002]*6,
        xpass_sim_dur_list=[0.002]*6,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_fullsweep_ssird_policy_",
        title_addendum="_12host_DctcpMsgSizeDist_load_fullsweep_800ns_fromjson_ssird_fairshare",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_incast_fullsweep_ssird_policy_"+"_12host_DctcpMsgSizeDist_load_fullsweep_ssird_fairshare")

def incast_10to1_1458B_fbCacheFollowerDist_load_fullsweep_ssird_policy_fairshare():
    ''' USE THIS WORKLOAD DISTRIBUTION & FLOWSPEC FILE! '''
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.FAIRSHARE)
    # run_experiment_from_saved_json(
    #     saved_json_file="FE_incast_12host_10to1_12host_fbCacheFollowerDist_loadtest_5000ns_1to40flo_2025-08-20T_22-41-02Z.json",
    #     proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 20, 30, 40],
    #     byteload_size_B_list=[1458]*6,
    #     target_mean_byteload_interval_nanosec_list=[5000]*6,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_CacheFollowerDist_IntraCluster.txt")]*6,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.035]*6,
    #     dctcp_sim_dur_list=[0.035]*6,
    #     xpass_sim_dur_list=[0.035]*6,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_fullsweep_ssird_policy_",
    #     title_addendum="_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_ssird_fairshare",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # print("FE_incast_12host_fullsweep_ssird_policy_"+"_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_ssird_fairshare")
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_10to1_12host_fbCacheFollowerDist_loadtest_5000ns_1to40flo_2025-08-27T_13-42-30Z.json",
        # proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME],
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 14, 17, 20, 25, 30, 40],
        byteload_size_B_list=[1458]*9,
        target_mean_byteload_interval_nanosec_list=[5000]*9,
        # max_interval_nanosec_list=[10000]*9,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_CacheFollowerDist_IntraCluster.txt")]*9,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.035]*9,
        dctcp_sim_dur_list=[0.035]*9,
        xpass_sim_dur_list=[0.035]*9,
        is_full_postproc=True,
        # title_prefix="FE_incast_12host_",
        # title_addendum="_12host_fbCacheFollowerDist_loadtest_5000ns_1to40flo_retry_dctcp",
        # title_addendum="_12host_fbCacheFollowerDist_loadtest_5000ns_1to40flo_retry_xpass",
        # title_prefix="FE_incast_12host_fullsweep_v3_",
        title_prefix="FE_incast_12host_fullsweep_ssird_policy_v3_",
        title_addendum="_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_ssird_fairshare",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_incast_12host_fullsweep_ssird_policy_v3_"+"_12host_fbCacheFollowerDist_load_fullsweep_5000ns_1to40flo_fromjson_ssird_fairshare")

def incast_10to1_1458B_fbCacheFollowerDist_load_fullsweep_ssird_policy_fairshare_v5():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.FAIRSHARE)
    assert(dale_experiment_rig.DCTCP_ECN_MARKING_THRESHOLD == "61")
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_NEW_PROBE2_10to1_12host_fbCacheFollowerDist_loadtest_5Kns_2025-08-31T_14-17-55Z.json",
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        byteload_size_B_list=[1458]*10,
        target_mean_byteload_interval_nanosec_list=[5000]*10,
        # max_interval_nanosec_list=[10000]*10,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_CacheFollowerDist_IntraCluster.txt")]*10,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.035]*10,
        dctcp_sim_dur_list=[0.035]*10,
        xpass_sim_dur_list=[0.035]*10,
        is_full_postproc=True,
        title_prefix="FE_NEW_incast_12host_fullsweep_v5_policy_",
        title_addendum="_12host_fbCacheFollowerDist_loadtest_5Kns_fromjson_ssird_fairshare",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_NEW_incast_12host_fullsweep_v5_policy_" + "_12host_fbCacheFollowerDist_loadtest_5Kns_fromjson_ssird_fairshare")

def incast_5to1_1458B_dctcpMsgSizeDistActual_load_fullsweep_ssird_policy_fairshare():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.FAIRSHARE)
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_5to1_6host_DctcpMsgSizeDistActual_loadtest_1Kns_2025-08-25T_20-37-43Z.json",
        # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='6-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
        num_flows_list=[1, 5, 10, 15, 20, 25, 30],
        byteload_size_B_list=[1458]*7,
        target_mean_byteload_interval_nanosec_list=[1000]*7,
        flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*7,
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.055]*7,
        dctcp_sim_dur_list=[0.055]*7,
        xpass_sim_dur_list=[0.055]*7,
        # ssird_sim_dur_list=[0.07]*7,
        # dctcp_sim_dur_list=[0.07]*7,
        # xpass_sim_dur_list=[0.07]*7,
        is_full_postproc=True,
        title_prefix="FE_incast_12host_fullsweep_ssird_policy_",
        title_addendum="_6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson_ssird_fairshare",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_incast_12host_fullsweep_ssird_policy_"+"_6host_DctcpMsgSizeDistActual_load_fullsweep_1Kns_fromjson_ssird_fairshare")

def incast_10to1_1458B_dctcpMsgSizeDistActual_load_fullsweep_ssird_policy_fairshare():
    ''' USE THIS WORKLOAD DISTRIBUTION & FLOWSPEC FILE! '''
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.FAIRSHARE)
    # run_experiment_from_saved_json(
    #     saved_json_file="FE_incast_12host_10to1_12host_DctcpMsgSizeDistActual_loadtest_2Kns_2025-08-26T_10-36-29Z.json",
    #     proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 15, 20, 25, 30],
    #     byteload_size_B_list=[1458]*7,
    #     target_mean_byteload_interval_nanosec_list=[2000]*7,
    #     flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*7,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.085]*7,
    #     dctcp_sim_dur_list=[0.085]*7,
    #     xpass_sim_dur_list=[0.085]*7,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_fullsweep_ssird_policy_",
    #     title_addendum="_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson_ssird_fairshare",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # print("FE_incast_12host_fullsweep_ssird_policy_"+"_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson")
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_10to1_12host_DctcpMsgSizeDistActual_loadtest_2Kns_2025-08-27T_14-43-35Z.json",
        # proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME],
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 8, 12, 14, 16, 18, 20, 25, 30],
        byteload_size_B_list=[1458]*10,
        target_mean_byteload_interval_nanosec_list=[2000]*10,
        # max_interval_nanosec_list=[20000]*10,
        flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*10,
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.09]*10,
        dctcp_sim_dur_list=[0.09]*10,
        xpass_sim_dur_list=[0.09]*10,
        is_full_postproc=True,
        title_prefix="FE_NEW_incast_12host_fullsweep_ssird_policy_",
        title_addendum="_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson_ssird_fairshare",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_NEW_incast_12host_fullsweep_ssird_policy_"+"_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson_ssird_fairshare")

def incast_10to1_1458B_dctcpMsgSizeDistActual_load_fullsweep_ssird_policy_fairshare_v5():
    ''' USE THIS WORKLOAD DISTRIBUTION & FLOWSPEC FILE! '''
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.FAIRSHARE)
    assert(dale_experiment_rig.DCTCP_ECN_MARKING_THRESHOLD == "61")
    run_experiment_from_saved_json(
        saved_json_file="FE_incast_12host_NEW_PROBE2_10to1_12host_DctcpMsgSizeDistActual_loadtest_2Kns_2025-08-31T_12-38-03Z.json",
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 4, 6, 8, 10, 12, 13, 14, 15, 16],
        byteload_size_B_list=[1458]*10,
        target_mean_byteload_interval_nanosec_list=[2000]*10,
        # max_interval_nanosec_list=[20000]*10,
        flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*10,
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.065]*10,
        dctcp_sim_dur_list=[0.06]*10,
        xpass_sim_dur_list=[0.06]*10,
        is_full_postproc=True,
        title_prefix="FE_NEW_incast_12host_fullsweep_v5_policy_",
        title_addendum="_12host_DctcpMsgSizeDistActual_loadtest_2Kns_fromjson_ssird_fairshare",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_NEW_incast_12host_fullsweep_v5_policy_"+"_12host_DctcpMsgSizeDistActual_load_fullsweep_2Kns_fromjson_fairshare")

if __name__ == "__main__":

    ''' FINAL EXPERIMENTS (1RTT DELAY TEST) '''
    onertt_delay_p2p_lowload()
    # onertt_delay_p2p_flowrate_sweep()

    ''' FINAL EXPERIMENTS (LOAD TEST) '''
    # incast_3to1_1458B_fbHadoopDist()
    # incast_3to1_1458B_dctcpMsgSizeDist()
    # incast_3to1_1458B_googleAllRpc()

    # incast_5to1_1458B_fabricated_heavy_middle_loadtest()
    # incast_5to1_1458B_fbHadoopDist_loadtest()
    # incast_5to1_1458B_dctcpMsgSizeDist_loadtest()
    # incast_5to1_1458B_googleAllRpc_loadtest()

    # incast_10to1_1458B_googleAllRpc_loadtest()
    # incast_10to1_1458B_fabricated_heavy_middle_loadtest()
    # incast_10to1_1458B_fbHadoopDist_loadtest()
    # incast_10to1_1458B_fbCacheFollowerDist_loadtest()
    # incast_10to1_1458B_dctcpMsgSizeDist_loadtest()

    # incast_10to1_1458B_dctcpMsgSizeDistActual_loadtest()

    # incast_10to1_1458B_fbHadoopDist_loadtest_NEW()
    # incast_10to1_1458B_fbCacheFollowerDist_loadtest_NEW()
    # incast_10to1_1458B_dctcpMsgSizeDistActual_loadtest_NEW()

    # incast_20to1_1458B_fbHadoopDist_loadtest_NEW()
    # incast_20to1_1458B_fbCacheFollowerDist_loadtest_NEW()

    ''' FINAL EXPERIMENTS (FULL LOAD SWEEP) '''
    # incast_10to1_1458B_googleAllRpc_load_fullsweep()
    # incast_10to1_1458B_fabHvyMid_load_fullsweep()
    # incast_10to1_1458B_dctcpMsgSizeDist_load_fullsweep()

    # incast_5to1_1458B_dctcpMsgSizeDistActual_load_fullsweep()

    # assert(False)
    # incast_10to1_1458B_fbHadoopDist_load_fullsweep()
    # incast_10to1_1458B_fbCacheFollowerDist_load_fullsweep()
    # incast_10to1_1458B_dctcpMsgSizeDistActual_load_fullsweep()
    # incast_10to1_1458B_dctcpMsgSizeDistActual_load_fullsweep_v5()
    # incast_10to1_1458B_fbHadoopDist_800ns_load_fullsweep_v5()

    ''' FINAL EXPERIMENTS SSIRD POLICY (FULL LOAD SWEEP) '''
    # incast_10to1_1458B_googleAllRpc_load_fullsweep_ssird_policy_fairshare()
    # incast_10to1_1458B_dctcpMsgSizeDist_load_fullsweep_ssird_policy_fairshare()
    # incast_5to1_1458B_dctcpMsgSizeDistActual_load_fullsweep_ssird_policy_fairshare()

    # assert(False)
    # incast_10to1_1458B_fbHadoopDist_load_fullsweep_ssird_policy_fairshare()
    # incast_10to1_1458B_fbCacheFollowerDist_load_fullsweep_ssird_policy_fairshare()
    # incast_10to1_1458B_dctcpMsgSizeDistActual_load_fullsweep_ssird_policy_fairshare()
    # incast_10to1_1458B_dctcpMsgSizeDistActual_load_fullsweep_ssird_policy_fairshare_v5()
    # incast_10to1_1458B_fbHadoopDist_800ns_load_fullsweep_ssird_policy_fairshare_v5()