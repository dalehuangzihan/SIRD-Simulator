from pathlib import Path

import dale_experiment_rig
import dale_final_eval_experiments

logger = dale_experiment_rig.logging.getLogger(__name__)

''' Function to load flows from saved json and run experiments '''
def run_experiment_from_saved_json_custom_numflows(
        saved_json_file,
        proto_names,
        topo_yaml_file,
        src_dst_pairs_list,
        num_flows,
        byteload_size_B,
        target_mean_byteload_interval_nanosec,
        flow_size_distr,
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

    num_of_experiments = 1
    target_flow_rate_gbps = (byteload_size_B * 8) / (target_mean_byteload_interval_nanosec * pow(10,-9)) * pow(10, -9)

    logs_file_name = f"{experiment_family}{len(src_dst_pairs_list)}to1{title_addendum}_{experiment_date}"
    dale_experiment_rig.init_logs(f"{experiment_family}{title_addendum}", logs_file_name+".log")

    logger.debug(f"## LOADING FROM SAVED JSON FILE: {saved_json_file_path}")
    logger.debug(f"Flow size distr workload: {flow_size_distr.cdf_file_name}")

    src_dst_pairs_to_flowspecs_dict_list_original = [] # list of src_dst_pairs_to_flowspecs_dict objs, one per experiment
    all_flow_specs_list = [] # list of flow_spec objs across all src-dst pairs across all experiments
    src_dst_pairs_to_flow_start_times_us_dict_list = [] # list of src_dst_pairs_to_flow_start_times_us_dict objs, one per experiment
    src_dst_pairs_to_flowspecs_dict_list_truncated = []

    src_dst_pairs_to_flowspecs_dict_list_original = dale_experiment_rig.FlowSpec.parse_src_dst_pairs_flowspec_dict_list_from_jsonfile(dale_experiment_rig.SAVED_FLOW_SPECS_JSON_PATH, saved_json_file)
    for exp_id in range(len(src_dst_pairs_to_flowspecs_dict_list_original)): # iterating thru experiments

        ''' only load up experiments for this particular num_flow '''
        src_dst_pairs_to_flowspecs_dict = src_dst_pairs_to_flowspecs_dict_list_original[exp_id]
        # print(src_dst_pairs_to_flowspecs_dict)
        src_dst_pairs_to_flow_start_times_us_dict = {}

        src_dst_pair_test = src_dst_pairs_list[0]
        src_dst_pair_key_test = (src_dst_pair_test[0], src_dst_pair_test[1])
        flow_spec_list_test, flow_start_times_us_list_test = src_dst_pairs_to_flowspecs_dict[src_dst_pair_key_test]
        assert(len(flow_spec_list_test) == len(flow_start_times_us_list_test))
        if (num_flows != len(flow_start_times_us_list_test)):
            # not the num_flows we're looking for, skip to the next flowspec dict list entry
            continue

        for src_dst_pair in src_dst_pairs_list:
            src_dst_pair_key = (src_dst_pair[0], src_dst_pair[1])
            flow_spec_list, flow_start_times_us_list = src_dst_pairs_to_flowspecs_dict[src_dst_pair_key]
            assert(len(flow_spec_list) == len(flow_start_times_us_list))
            assert(len(flow_spec_list) == num_flows)
            all_flow_specs_list.extend(flow_spec_list)
            src_dst_pairs_to_flow_start_times_us_dict[src_dst_pair] = flow_start_times_us_list
        src_dst_pairs_to_flow_start_times_us_dict_list.append(src_dst_pairs_to_flow_start_times_us_dict)
        src_dst_pairs_to_flowspecs_dict_list_truncated.append(src_dst_pairs_to_flowspecs_dict)

    assert(num_of_experiments == 1)

    flow_rate_gbps_list = [round(f.flow_rate_bps*pow(10,-9),6) for f in all_flow_specs_list]
    flow_size_B_list = [f.flow_size_B for f in all_flow_specs_list]
    flow_num_byteloads_list = [f.num_byteloads for f in all_flow_specs_list]
    flow_send_durations_us_list = [f.total_flow_send_duration_us for f in all_flow_specs_list]
    flow_min_byteload_size_B_list = [min(f.byteload_size_B_list) for f in all_flow_specs_list]
    flow_max_byteload_size_B_list = [max(f.byteload_size_B_list) for f in all_flow_specs_list]
    flow_min_interval_us = [min(f.interval_us_list) if len(f.interval_us_list) > 0 else f.interval_us_list for f in all_flow_specs_list]
    flow_max_interval_us = [max(f.interval_us_list) if len(f.interval_us_list) > 0 else f.interval_us_list for f in all_flow_specs_list]


    num_flows_list = [num_flows]
    byteload_size_B_list = [byteload_size_B]
    target_mean_byteload_interval_nanosec_list = [target_mean_byteload_interval_nanosec]

    logger.info(f"Protos tested: {proto_names}")
    logger.info(f"Topo Yaml File: {topo_yaml_file}")
    logger.info(f"Src-Dst pairs list: {src_dst_pairs_list}")
    logger.info(f"Num Flows: {num_flows}")
    logger.info(f"Byteload Size (B): {byteload_size_B_list}")
    logger.info(f"Flow size distr workload: {flow_size_distr.cdf_file_name}")
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
        src_dst_pairs_to_flowspecs_dict_list_truncated,
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
    logger.info(f"Flow size distr workload: {flow_size_distr.cdf_file_name}")
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

    logger.info(f"APP Gdpt Gbps measured (SSIRD): {exp_metrics.total_app_gdpt_gbps_measured_list_ssird }")
    logger.info(f"APP Gdpt Gbps measured (DCTCP): {exp_metrics.total_app_gdpt_gbps_measured_list_dctcp}")
    logger.info(f"APP Gdpt Gbps measured (XPass): {exp_metrics.total_app_gdpt_gbps_measured_list_xpass}")
    logger.debug(f"APP Gdpt Gbps measured per flow (SSIRD): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_ssird}")
    logger.debug(f"APP Gdpt Gbps measured per flow (DCTCP): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_dctcp}")
    logger.debug(f"APP Gdpt Gbps measured per flow (XPass): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_xpass}")

    logger.info(f"NW Gdpt Gbps measured (SSIRD): {exp_metrics.total_nw_gdpt_gbps_measured_list_ssird}")
    logger.info(f"NW Gdpt Gbps measured (DCTCP): {exp_metrics.total_nw_gdpt_gbps_measured_list_dctcp}")
    logger.info(f"NW Gdpt Gbps measured (Xpass): {exp_metrics.total_nw_gdpt_gbps_measured_list_xpass}")
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
Function to load flows from saved json and run experiments;
Optionally combines all byteloads of each flow into a single byteload.
'''
def run_experiment_from_saved_json_custom_combine_byteloads(
        is_combine_byteloads,
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
    logger.info(f">>is_combine_byteloads={is_combine_byteloads}")

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

            for i in range(len(flow_spec_list)):
                flow_spec = flow_spec_list[i]

                # print("ORIGINAL FLOWSPEC:")
                # print(f"num_byteloads: {flow_spec.num_byteloads}")
                # print(f"byteoad_size_B_list: {flow_spec.byteload_size_B_list}")
                # print(f"flow_size_B: {flow_spec.flow_size_B}")
                # print(f"interval_us_list: {flow_spec.interval_us_list}")
                # print(f"byteload_rel_timestamp_us_list: {flow_spec.byteload_rel_timestamp_us_list}")
                # print(f"total_flow_send_duration_us: {flow_spec.total_flow_send_duration_us}")
                # print("---")

                if (is_combine_byteloads):
                    # combine byteloads

                    flow_spec.num_byteloads = 1        
                    flow_spec.byteload_size_B_list = [sum(flow_spec.byteload_size_B_list)]
                    flow_spec.flow_size_B = sum(flow_spec.byteload_size_B_list)
                    flow_spec.interval_us_list = []
                    flow_spec.byteload_rel_timestamp_us_list = [0]
                    flow_spec.total_flow_send_duration_us = 0 + flow_start_times_us_list[i]

                    # print("NEW FLOWSPEC:")
                    # print(f"num_byteloads: {flow_spec.num_byteloads}")
                    # print(f"byteoad_size_B_list: {flow_spec.byteload_size_B_list}")
                    # print(f"flow_size_B: {flow_spec.flow_size_B}")
                    # print(f"interval_us_list: {flow_spec.interval_us_list}")
                    # print(f"byteload_rel_timestamp_us_list: {flow_spec.byteload_rel_timestamp_us_list}")
                    # print(f"total_flow_send_duration_us: {flow_spec.total_flow_send_duration_us}")
                    # print("===\n")

            # return # TODO: remove


            all_flow_specs_list.extend(flow_spec_list)
            src_dst_pairs_to_flow_start_times_us_dict[src_dst_pair] = flow_start_times_us_list
        src_dst_pairs_to_flow_start_times_us_dict_list.append(src_dst_pairs_to_flow_start_times_us_dict)

    assert(num_of_experiments == len(src_dst_pairs_to_flowspecs_dict_list))

    # return  # TODO: remove

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

    logger.info(f"APP Gdpt Gbps measured (SSIRD): {exp_metrics.total_app_gdpt_gbps_measured_list_ssird }")
    logger.info(f"APP Gdpt Gbps measured (DCTCP): {exp_metrics.total_app_gdpt_gbps_measured_list_dctcp}")
    logger.info(f"APP Gdpt Gbps measured (XPass): {exp_metrics.total_app_gdpt_gbps_measured_list_xpass}")
    logger.debug(f"APP Gdpt Gbps measured per flow (SSIRD): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_ssird}")
    logger.debug(f"APP Gdpt Gbps measured per flow (DCTCP): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_dctcp}")
    logger.debug(f"APP Gdpt Gbps measured per flow (XPass): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_xpass}")

    logger.info(f"NW Gdpt Gbps measured (SSIRD): {exp_metrics.total_nw_gdpt_gbps_measured_list_ssird}")
    logger.info(f"NW Gdpt Gbps measured (DCTCP): {exp_metrics.total_nw_gdpt_gbps_measured_list_dctcp}")
    logger.info(f"NW Gdpt Gbps measured (Xpass): {exp_metrics.total_nw_gdpt_gbps_measured_list_xpass}")
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

def simple_ssird_incast_DctcpMsgSizeDist_same_flow_interarr():
    # is experiment where all flows start at the same time, to see SRPT
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # dale_final_eval_experiments.run_experiment(
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[40],
    #     byteload_size_B_list=[1458],
    #     target_mean_byteload_interval_nanosec_list=[800],
    #     max_interval_nanosec_list=[10000],
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="DCTCP_MsgSizeDist.txt")],
    #     target_mean_flow_interarr_ns=0,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=False,
    #     ssird_sim_dur_list=[0.002],
    #     dctcp_sim_dur_list=[0.002],
    #     xpass_sim_dur_list=[0.002],
    #     is_full_postproc=True,
    #     title_prefix="FE_p2p_srpt_exp_",
    #     title_addendum="_12host_10to1_DctcpMsgSizeDist_srpttest_800ns_same_flow_interarr",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    dale_final_eval_experiments.run_experiment_from_saved_json(
        saved_json_file="FE_p2p_srpt_exp_10to1_12host_10to1_DctcpMsgSizeDist_srpttest_800ns_same_flow_interarr_2025-08-22T_07-58-29Z.json",
        # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[40],
        byteload_size_B_list=[1458],
        target_mean_byteload_interval_nanosec_list=[800],
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="DCTCP_MsgSizeDist.txt")],
        target_mean_flow_interarr_ns=0,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=False,
        ssird_sim_dur_list=[0.001],
        dctcp_sim_dur_list=[0.001],
        xpass_sim_dur_list=[0.001],
        is_full_postproc=True,
        title_prefix="FE_incast_ssird_srpt_exp_",
        title_addendum="_12host_10to1_DctcpMsgSizeDist_srpttest_800ns_same_flow_interarr_fromjson",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_incast_ssird_srpt_exp_" + "_12host_10to1_DctcpMsgSizeDist_srpttest_800ns_same_flow_interarr_fromjson"+"\n")

def simple_ssird_incast_DctcpMsgSizeDist_same_flow_interarr_combine_byteloads():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    run_experiment_from_saved_json_custom_combine_byteloads(
        is_combine_byteloads=True,
        saved_json_file="FE_p2p_srpt_exp_10to1_12host_10to1_DctcpMsgSizeDist_srpttest_800ns_same_flow_interarr_2025-08-22T_07-58-29Z.json",
        # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[40],
        byteload_size_B_list=[1458],
        target_mean_byteload_interval_nanosec_list=[800],
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="DCTCP_MsgSizeDist.txt")],
        target_mean_flow_interarr_ns=0,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=False,
        ssird_sim_dur_list=[0.001],
        dctcp_sim_dur_list=[0.001],
        xpass_sim_dur_list=[0.001],
        is_full_postproc=True,
        title_prefix="FE_incast_ssird_srpt_exp_",
        title_addendum="_12host_10to1_DctcpMsgSizeDist_srpttest_800ns_same_flow_interarr_fromjson_combine_bloads",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_incast_ssird_srpt_exp_" + "_12host_10to1_DctcpMsgSizeDist_srpttest_800ns_same_flow_interarr_fromjson_combine_bloads"+"\n")

def incast_10to1_1458B_dctcpMsgSizeDist_load_fullsweep_combine_byteloads():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    run_experiment_from_saved_json_custom_combine_byteloads(
        is_combine_byteloads=True,
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
        title_prefix="FE_incast_12host_fullsweep_ssird_srpt_exp_",
        title_addendum="_12host_DctcpMsgSizeDist_load_fullsweep_800ns_fromjson_combine_byteloads",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_incast_12host_fullsweep_ssird_srpt_exp_"+"_12host_DctcpMsgSizeDist_load_fullsweep_800ns_fromjson_combine_byteloads")

if __name__ == "__main__":

    # simple_ssird_incast_DctcpMsgSizeDist_same_flow_interarr()
    # simple_ssird_incast_DctcpMsgSizeDist_same_flow_interarr_combine_byteloads()

    incast_10to1_1458B_dctcpMsgSizeDist_load_fullsweep_combine_byteloads()

    # run_experiment_from_saved_json_custom_combine_byteloads(
    #     is_combine_byteloads=True,
    #     saved_json_file="FE_p2p_srpt_exp_10to1_12host_10to1_DctcpMsgSizeDist_srpttest_800ns_same_flow_interarr_2025-08-22T_07-58-29Z.json",
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[40],
    #     byteload_size_B_list=[1458],
    #     target_mean_byteload_interval_nanosec_list=[800],
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="DCTCP_MsgSizeDist.txt")],
    #     target_mean_flow_interarr_ns=0,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=False,
    #     ssird_sim_dur_list=[0.001],
    #     dctcp_sim_dur_list=[0.001],
    #     xpass_sim_dur_list=[0.001],
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_ssird_srpt_exp_",
    #     title_addendum="_12host_10to1_DctcpMsgSizeDist_srpttest_800ns_same_flow_interarr_fromjson",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 

    # run_experiment_from_saved_json_custom_numflows(
    #     saved_json_file="FE_incast_12host_10to1_12host_DctcpMsgSizeDist_loadtest_800ns_2025-08-20T_10-12-29Z.json",
    #     proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     # num_flows_list=[1, 5, 10, 20, 30, 40],
    #     num_flows=20,
    #     byteload_size_B=1458,
    #     target_mean_byteload_interval_nanosec=800,
    #     flow_size_distr=dale_experiment_rig.WxDistr(cdf_file_name="DCTCP_MsgSizeDist.txt"),
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.002],
    #     dctcp_sim_dur_list=[0.002],
    #     xpass_sim_dur_list=[0.002],
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_policy_TEST_",
    #     title_addendum="_12host_DctcpMsgSizeDist_800ns_fromjson_policy_TEST_FAIRSHARE",
    #     # title_addendum="_12host_DctcpMsgSizeDist_800ns_fromjson_policy_TEST_SRPT",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date="nodate"
    #     # experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
