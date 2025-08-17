
import datetime
import dale_experiment_rig

logger = dale_experiment_rig.logging.getLogger(__name__)

def experiment_p2p_poisson_const_flow_rate_vary_byteload_size_and_interval(
        topo_yaml_file,
        src_dst_pairs_list,
        num_flows,
        byteload_size_B_list,
        target_mean_byteload_interval_nanosec_list,
        target_mean_num_byteloads_list,
        target_mean_flow_interarr_ns,
        is_use_poisson_byteload_intervals,
        is_use_poisson_num_byteloads,
        is_use_poisson_flow_interarr,
        ssird_sim_dur_list,
        dctcp_sim_dur_list,
        is_full_postproc=True,
        title_addendum="",
        log_level=dale_experiment_rig.LOG_LEVEL_2
    ):

    experiment_family = f"Poisson{title_addendum}"
    experiment_date = dale_experiment_rig.Experiment.get_date_now_formatted()
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(0,1)]

    assert(len(byteload_size_B_list) == len(target_mean_byteload_interval_nanosec_list))
    num_of_experiments = len(byteload_size_B_list)
    target_flow_rate_gbps = (byteload_size_B_list[0] * 8) / (target_mean_byteload_interval_nanosec_list[0] * pow(10,-9)) * pow(10, -9)

    logs_file_name = f"poisson_p2p_{num_flows}flo_{round(target_flow_rate_gbps)}Gbps_{experiment_date}{title_addendum}"
    dale_experiment_rig.init_logs(experiment_family, logs_file_name+".log")

    # Generate flow specs for each experiment
    flow_spec_list_list = []
    flow_start_times_us_list_list = []
    for i in range(0, num_of_experiments):
        logger.info(f"Generating flows for experiment {i} ---")
        byteload_size_B = byteload_size_B_list[i]
        target_mean_byteload_interval_nanosec = target_mean_byteload_interval_nanosec_list[i]
        target_mean_num_byteloads = target_mean_num_byteloads_list[i]
        exp_target_flow_rate_gbps = (byteload_size_B_list[i] * 8) / (target_mean_byteload_interval_nanosec_list[i] * pow(10,-9)) * pow(10, -9)
        assert(round(exp_target_flow_rate_gbps, 9) == round(target_flow_rate_gbps, 9))

        flow_generator = dale_experiment_rig.FlowSpecGenerator(
            num_flows=num_flows,
            byteload_size_B=byteload_size_B,
            target_mean_byteload_interval_ns=target_mean_byteload_interval_nanosec,
            max_interval_ns=target_mean_byteload_interval_nanosec*100, # NOTE: we override default here cuz we have 10000ns interval in one of experiments
            flow_size_distr=target_mean_num_byteloads,
            target_mean_flow_interarr_ns=target_mean_flow_interarr_ns,
            is_use_poisson_byteload_intervals=is_use_poisson_byteload_intervals,
            is_use_poisson_num_byteloads=is_use_poisson_num_byteloads,
            is_use_poisson_flow_interarr=is_use_poisson_flow_interarr
        )
        flow_spec_list, flow_start_times_us_list = flow_generator.generate_poisson_flows()
        flow_spec_list_list.append(flow_spec_list)
        flow_start_times_us_list_list.append(flow_start_times_us_list)
    assert(len(flow_spec_list_list) == num_of_experiments)
    assert(len(flow_start_times_us_list_list) == num_of_experiments)

    # # Load flow spec for each experiment from saved json: 
    # flow_start_times_us_list_list, flow_spec_list_list = dale_experiment_rig.FlowSpec.parse_multi_exp_flow_specs_json_file(dale_experiment_rig.SAVED_FLOW_SPECS_JSON_PATH, "multi_exp_poisson_p2p_2flo-16Gbps-2025-08-11T_16-36-33Z.log")
    # assert(len(flow_spec_list_list) == num_of_experiments)
    # assert(len(flow_start_times_us_list_list) == num_of_experiments)
    # for i in range(0, num_of_experiments):
    #     assert(len(flow_start_times_us_list_list[i]) == len(flow_spec_list_list[i]) and len(flow_spec_list_list[i]) == num_flows)

    # Back up flow spec list list # TODO: make infra to back up flow spec list list
    exp_flows_dict_dict = dale_experiment_rig.FlowSpec.flow_spec_list_list_to_dict(flow_spec_list_list, flow_start_times_us_list_list)
    dale_experiment_rig.FlowSpec.write_jsondict_to_jsonfile(exp_flows_dict_dict, dale_experiment_rig.FLOW_SPECS_JSON_PATH, f"multi_exp_{logs_file_name}.json")

    flow_rate_gbps_list = [round(f.flow_rate_bps*pow(10,-9),6) for f in flow_spec_list]
    flow_size_B_list = [f.flow_size_B for f in flow_spec_list]
    flow_num_byteloads_list = [f.num_byteloads for f in flow_spec_list]
    flow_send_durations_us_list = [f.total_flow_send_duration_us for f in flow_spec_list]
    flow_min_byteload_size_B_list = [min(f.byteload_size_B_list) for f in flow_spec_list]
    flow_max_byteload_size_B_list = [max(f.byteload_size_B_list) for f in flow_spec_list]
    flow_min_interval_us = [min(f.interval_us_list) for f in flow_spec_list]
    flow_max_interval_us = [max(f.interval_us_list) for f in flow_spec_list]

    logger.info(f"Protos tested: {proto_names}")
    logger.info(f"Topo Yaml File: {topo_yaml_file}")
    logger.info(f"Src-Dst pairs list: {src_dst_pairs_list}")
    logger.info(f"Num Flows: {num_flows}")
    logger.info(f"Byteload Size (B): {byteload_size_B}")
    logger.info(f"Target Mean Byteload Interval (ns): {target_mean_byteload_interval_nanosec_list}")
    logger.info(f"  is_use_poisson_byteload_intervals={is_use_poisson_byteload_intervals}")
    logger.info(f"Target Mean Flow Interarrival (ns): {target_mean_flow_interarr_ns}")
    logger.info(f"  is_use_poisson_flow_interarr={is_use_poisson_flow_interarr}")
    logger.info(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    logger.info(f"Num Byteloads: {flow_num_byteloads_list}")
    logger.info(f"  is_use_poisson_num_byteloads={is_use_poisson_num_byteloads}")
    logger.info(f"Flow Start Times (us): {flow_start_times_us_list}")
    logger.info(f"Flow Rate (Gbps): {flow_rate_gbps_list}")
    logger.info(f"Flow Size (B): {flow_size_B_list}")
    logger.info(f"Flow Send Durations (us): {flow_send_durations_us_list}")
    logger.info(f"Flow Min Byteload Size (B): {flow_min_byteload_size_B_list}")
    logger.info(f"Flow Max Byteload Size (B): {flow_max_byteload_size_B_list}")
    logger.info(f"Flow Min Interval (us): {flow_min_interval_us}")
    logger.info(f"Flow Max Interval (us): {flow_max_interval_us}")

    # # For RTT = 5us
    # ssird_sim_dur_list = [0.08, 0.05, 0.03, 0.02, 0.01] 
    # dctcp_sim_dur_list = [0.08, 0.05, 0.03, 0.02, 0.01]

    # TODO: modify assertion to work for spec that does specifies multiple experiments
    logger.debug(f"Max flow send durations (us): {max(flow_send_durations_us_list)}")
    assert(max(flow_send_durations_us_list) * pow(10,-6) * 1.5 < ssird_sim_dur_list[0])
    assert(max(flow_send_durations_us_list) * pow(10,-6) * 1.5 < dctcp_sim_dur_list[0])

    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    # return

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
        flow_start_times_us_list_list,
        flow_spec_list_list,
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
    logger.info(f"Flow Start Times (us): {flow_start_times_us_list}")
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

if __name__ == "__main__":

    # ''' 
    #   Experiment Rig Test
    # '''
    # experiment_p2p_poisson_const_flow_rate_vary_byteload_size_and_interval(
    #     num_flows=2,
    #     byteload_size_B_list=[2000, 4000],
    #     target_mean_byteload_interval_nanosec_list=[1000, 2000],
    #     target_mean_num_byteloads=1000,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_num_byteloads=False,
    #     is_use_poisson_flow_interarr=True,
    #     is_full_postproc=False,
    #     title_addendum="_p2p_poisson_fullrange_test",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2
    # )

    ''' 
        100% Gdpt p2p goodput experiment
            * 31flo
            * varying byteload size B: [20, 200, 2000, 20000]
            * varying byteload intervals (avg) ns: [100, 1000, 10000, 100000]
            * varying num byteloads: [10000, 1000, 100, 10]
            * 49.6Gbps total
    '''
    experiment_p2p_poisson_const_flow_rate_vary_byteload_size_and_interval(
        num_flows=31,
        byteload_size_B_list=[20, 200, 2000, 20000],
        target_mean_byteload_interval_nanosec_list=[100, 1000, 10000, 100000],
        target_mean_num_byteloads_list=[10000, 1000, 100, 10],
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=False,
        is_use_poisson_num_byteloads=False,
        is_use_poisson_flow_interarr=True,
        is_full_postproc=False,
        title_addendum="_p2p_poisson_fullrange_31flo_fixed_intervals",
        log_level=dale_experiment_rig.LOG_LEVEL_2
    )