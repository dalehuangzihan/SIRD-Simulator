import dale_experiment_rig

logger = dale_experiment_rig.logging.getLogger(__name__)

def experiment_incast_3_to_1_test(is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"FCT_Incast{title_addendum}"
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(1,0), (2,0), (3,0)]

    # minimum_interval_us = 1
    minimum_interval_us = 10 # 10us
    # total_flow_size_B = 200000 # 200KB
    total_flow_size_B = 20000 # 20KB (FOR TESTING)
    # NOTE: here we maintain a 1.6Gbps goodput per flow.

    KILOBYTE = 1000
    byteload_size_KB_list = [2] # 2KB bload
    byteload_size_B_list = [int(n * KILOBYTE) for n in byteload_size_KB_list] 
    num_of_experiments = len(byteload_size_B_list)
    num_flows_per_sr_pair = 31 
    # num_flows_per_sr_pair = 2
    inter_flow_spacing_us = 0 # TODO: for testing
    flow_start_times_us_list = [i * inter_flow_spacing_us for i in range(0, num_flows_per_sr_pair)]

    dale_experiment_rig.init_logs(experiment_family, f"subpkt_experiment_{num_flows_per_sr_pair}flo_{total_flow_size_B}B_total_{min(byteload_size_B_list)}B_to_{max(byteload_size_B_list)}B.log")

    logger.debug(f"Protos tested: {proto_names}")
    logger.debug(f"Src-Dst Pairs: {src_dst_pairs_list}")
    logger.debug(f"Total_flow_size_B: {total_flow_size_B}")
    logger.debug(f"Byteload sizes list: {byteload_size_B_list}")
    logger.debug(f"Num Flows Per Sendr/Recvr Pair: {num_flows_per_sr_pair}")
    logger.debug(f"Inter-flow spacing (us): {inter_flow_spacing_us}")
    logger.debug(f"Flow start times (us): {flow_start_times_us_list}")

    # calculate num of byteloads for experiment
    num_byteloads_per_flow_list = []
    for size in byteload_size_B_list:
        num_byteloads = None
        if size < 4:
            num_byteloads = total_flow_size_B // (4 * size)  # mirror treatment of hypersmall byteloads by r2p2-app.cc
        else:
            num_byteloads = total_flow_size_B // size
        num_byteloads_per_flow_list.append(num_byteloads)
    logger.debug(f"Num Byteloads list: {num_byteloads_per_flow_list}")
    assert(len(num_byteloads_per_flow_list) == num_of_experiments)

    # calculate inter-byteload periods for experiment
    total_injection_period_us = max(num_byteloads_per_flow_list) * minimum_interval_us
    logger.debug(f"Total injection period (us): {total_injection_period_us}")
    inter_byteload_period_us_list = [] 
    for num_byteloads in num_byteloads_per_flow_list:
        inter_byteload_period_us = total_injection_period_us / num_byteloads
        inter_byteload_period_us_list.append(inter_byteload_period_us)
    logger.debug(f"Inter-Byteload Periods list: {inter_byteload_period_us_list}")
    assert(len(inter_byteload_period_us_list) == num_of_experiments)

    # calculate simulation durations for experiment
    # multiplication_factor = 100
    # sim_dur_list = []
    # for i in range(0, len(num_byteloads_per_flow_list)):
    #    sim_dur_list.append(dale_experiment_rig.Experiment.get_sim_duration(num_flows, inter_flow_spacing_us, num_byteloads_per_flow_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i], multiplication_factor))
    # logger.debug(f"Sim Durations list: {sim_dur_list}")
    # assert(len(sim_dur_list) == num_of_experiments)
    # ssird_sim_dur_list = sim_dur_list
    # dctcp_sim_dur_list = sim_dur_list

    ssird_sim_dur_list = [0.02] * num_of_experiments # TODO: tweak
    dctcp_sim_dur_list = [0.02] * num_of_experiments # TODO: tweak

    # TODO: currently only calculates theoretical gbps for in-parallel flows
    gdpt_gbps_theoretical_list = []
    for i in range(0, num_of_experiments):
        gdpt_gbps_theoretical = len(src_dst_pairs_list) * num_flows_per_sr_pair * (byteload_size_B_list[i]*8)/(inter_byteload_period_us_list[i]) * pow(10,-3)
        if byteload_size_B_list[i] < 4: gdpt_gbps_theoretical *= 4  # mirror treatment of hypersmall byteloads by r2p2-app.cc
        gdpt_gbps_theoretical_list.append(gdpt_gbps_theoretical)
    assert(len(gdpt_gbps_theoretical_list) == num_of_experiments)

    logger.info(f"Src-Dst Pairs: {src_dst_pairs_list}")
    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows per Sendr/Recvr Pair: {num_flows_per_sr_pair}")
    logger.info(f"Gdpt GBps theoretical: {gdpt_gbps_theoretical_list}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    # return

    exp_grp = dale_experiment_rig.ExperimentGroup(experiment_family, proto_names, src_dst_pairs_list, flow_start_times_us_list, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, ssird_sim_dur_list, dctcp_sim_dur_list, is_full_postproc, log_level, title_addendum)

    ssird_fct_list, dctcp_fct_list, gdpt_gbps_measured_list_ssird, gdpt_gbps_measured_list_dctcp, gdpt_gbps_measured_per_flow_list_list_ssird, gdpt_gbps_measured_per_flow_list_list_dctcp = exp_grp.perform_experiment()

    logger.info(f"Src-Dst Pairs: {src_dst_pairs_list}")
    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows per Sendr/Recvr Pair: {num_flows_per_sr_pair}")
    logger.debug(f"Flow start times (us): {flow_start_times_us_list}")
    logger.info(f"Gdpt Gbps theoretical: {gdpt_gbps_theoretical_list}")
    logger.info(f"Gdpt Gbps measured (SSIRD): {gdpt_gbps_measured_list_ssird}")
    logger.info(f"Gdpt Gbps measured (DCTCP): {gdpt_gbps_measured_list_dctcp}")
    logger.debug(f"Gdpt Gbps measured per flow (SSIRD): {gdpt_gbps_measured_per_flow_list_list_ssird}")
    logger.debug(f"Gdpt Gbps measured per flow (DCTCP): {gdpt_gbps_measured_per_flow_list_list_dctcp}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    logger.info(f"* SSIRD FCT: {ssird_fct_list}")
    logger.info(f"* DCTCP FCT: {dctcp_fct_list}")

    assert num_of_experiments == len(ssird_fct_list)
    assert num_of_experiments == len(dctcp_fct_list)

def experiment_incast_3to1_16GbpsFlo(is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"FCT_Incast{title_addendum}"
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(1,0), (2,0), (3,0)]

    minimum_interval_us = 1
    total_flow_size_B = 200000 # 200KB (FOR TESTING)
    # NOTE: here we maintain a 16Gbps goodput per flow.

    KILOBYTE = 1000
    byteload_size_KB_list = [2] # 2KB bload
    byteload_size_B_list = [int(n * KILOBYTE) for n in byteload_size_KB_list] 
    num_of_experiments = len(byteload_size_B_list)
    num_flows_per_sr_pair = 5 # 3-incast * 5flo * 16Gbps/flo = 240Gpbs towards recvr
    inter_flow_spacing_us = 0 # TODO: for testing
    flow_start_times_us_list = [i * inter_flow_spacing_us for i in range(0, num_flows_per_sr_pair)]

    dale_experiment_rig.init_logs(experiment_family, f"subpkt_experiment_{num_flows_per_sr_pair}flo_{total_flow_size_B}B_total_{min(byteload_size_B_list)}B_to_{max(byteload_size_B_list)}B.log")

    logger.debug(f"Protos tested: {proto_names}")
    logger.debug(f"Src-Dst Pairs: {src_dst_pairs_list}")
    logger.debug(f"Total_flow_size_B: {total_flow_size_B}")
    logger.debug(f"Byteload sizes list: {byteload_size_B_list}")
    logger.debug(f"Num Flows Per Sendr/Recvr Pair: {num_flows_per_sr_pair}")
    logger.debug(f"Inter-flow spacing (us): {inter_flow_spacing_us}")
    logger.debug(f"Flow start times (us): {flow_start_times_us_list}")

    # calculate num of byteloads for experiment
    num_byteloads_per_flow_list = []
    for size in byteload_size_B_list:
        num_byteloads = None
        if size < 4:
            num_byteloads = total_flow_size_B // (4 * size)  # mirror treatment of hypersmall byteloads by r2p2-app.cc
        else:
            num_byteloads = total_flow_size_B // size
        num_byteloads_per_flow_list.append(num_byteloads)
    logger.debug(f"Num Byteloads list: {num_byteloads_per_flow_list}")
    assert(len(num_byteloads_per_flow_list) == num_of_experiments)

    # calculate inter-byteload periods for experiment
    total_injection_period_us = max(num_byteloads_per_flow_list) * minimum_interval_us
    logger.debug(f"Total injection period (us): {total_injection_period_us}")
    inter_byteload_period_us_list = [] 
    for num_byteloads in num_byteloads_per_flow_list:
        inter_byteload_period_us = total_injection_period_us / num_byteloads
        inter_byteload_period_us_list.append(inter_byteload_period_us)
    logger.debug(f"Inter-Byteload Periods list: {inter_byteload_period_us_list}")
    assert(len(inter_byteload_period_us_list) == num_of_experiments)

    # calculate simulation durations for experiment
    # multiplication_factor = 100
    # sim_dur_list = []
    # for i in range(0, len(num_byteloads_per_flow_list)):
    #    sim_dur_list.append(dale_experiment_rig.Experiment.get_sim_duration(num_flows, inter_flow_spacing_us, num_byteloads_per_flow_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i], multiplication_factor))
    # logger.debug(f"Sim Durations list: {sim_dur_list}")
    # assert(len(sim_dur_list) == num_of_experiments)
    # ssird_sim_dur_list = sim_dur_list
    # dctcp_sim_dur_list = sim_dur_list

    ssird_sim_dur_list = [0.02] * num_of_experiments # TODO: tweak
    dctcp_sim_dur_list = [0.05] * num_of_experiments # TODO: tweak

    # TODO: currently only calculates theoretical gbps for in-parallel flows
    gdpt_gbps_theoretical_list = []
    for i in range(0, num_of_experiments):
        gdpt_gbps_theoretical = len(src_dst_pairs_list) * num_flows_per_sr_pair * (byteload_size_B_list[i]*8)/(inter_byteload_period_us_list[i]) * pow(10,-3)
        if byteload_size_B_list[i] < 4: gdpt_gbps_theoretical *= 4  # mirror treatment of hypersmall byteloads by r2p2-app.cc
        gdpt_gbps_theoretical_list.append(gdpt_gbps_theoretical)
    assert(len(gdpt_gbps_theoretical_list) == num_of_experiments)

    logger.info(f"Src-Dst Pairs: {src_dst_pairs_list}")
    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows per Sendr/Recvr Pair: {num_flows_per_sr_pair}")
    logger.info(f"Gdpt GBps theoretical: {gdpt_gbps_theoretical_list}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    # return

    exp_grp = dale_experiment_rig.ExperimentGroup(experiment_family, proto_names, src_dst_pairs_list, flow_start_times_us_list, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, ssird_sim_dur_list, dctcp_sim_dur_list, is_full_postproc, log_level, title_addendum)

    ssird_fct_list, dctcp_fct_list, gdpt_gbps_measured_list_ssird, gdpt_gbps_measured_list_dctcp, gdpt_gbps_measured_per_flow_list_list_ssird, gdpt_gbps_measured_per_flow_list_list_dctcp = exp_grp.perform_experiment()

    logger.info(f"Src-Dst Pairs: {src_dst_pairs_list}")
    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows per Sendr/Recvr Pair: {num_flows_per_sr_pair}")
    logger.debug(f"Flow start times (us): {flow_start_times_us_list}")
    logger.info(f"Gdpt Gbps theoretical: {gdpt_gbps_theoretical_list}")
    logger.info(f"Gdpt Gbps measured (SSIRD): {gdpt_gbps_measured_list_ssird}")
    logger.info(f"Gdpt Gbps measured (DCTCP): {gdpt_gbps_measured_list_dctcp}")
    logger.debug(f"Gdpt Gbps measured per flow (SSIRD): {gdpt_gbps_measured_per_flow_list_list_ssird}")
    logger.debug(f"Gdpt Gbps measured per flow (DCTCP): {gdpt_gbps_measured_per_flow_list_list_dctcp}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    logger.info(f"* SSIRD FCT: {ssird_fct_list}")
    logger.info(f"* DCTCP FCT: {dctcp_fct_list}")

    assert num_of_experiments == len(ssird_fct_list)
    assert num_of_experiments == len(dctcp_fct_list)

def experiment_incast_poisson_flows(
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
        log_level=dale_experiment_rig.LOG_LEVEL_2
    ):

    experiment_family = f"Poisson_Flows{title_addendum}"
    experiment_date = dale_experiment_rig.Experiment.get_date_now_formatted()
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    # src_dst_pairs_list = [(1,0), (2,0), (3,0)]

    target_flow_rate_gbps = (byteload_size_B * 8) / (target_mean_byteload_interval_nanosec * pow(10,-9)) * pow(10, -9)
    logs_file_name = f"poisson_incast_{len(src_dst_pairs_list)}to1_{dale_experiment_rig.Experiment.get_experiment_name(num_flows, target_flow_rate_gbps, byteload_size_B, target_mean_byteload_interval_nanosec, experiment_date)}{title_addendum}"
    dale_experiment_rig.init_logs(experiment_family, logs_file_name+".log")

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

    flow_spec_list_list = [flow_spec_list]
    flow_start_times_us_list_list = [flow_start_times_us_list]

    num_of_experiments = len(flow_spec_list_list)
    assert(len(flow_start_times_us_list_list) == num_of_experiments)

    # Back up flow spec list # TODO: make infra to back up flow spec list list
    flow_spec_dict = dale_experiment_rig.FlowSpec.flow_spec_list_to_dict(flow_spec_list, flow_start_times_us_list)
    dale_experiment_rig.FlowSpec.write_jsondict_to_jsonfile(flow_spec_dict, dale_experiment_rig.FLOW_SPECS_JSON_PATH, logs_file_name+".json")

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

    # For RTT = 5us
    # ssird_sim_dur_list = [0.06]
    # dctcp_sim_dur_list = [0.06]

    # # For RTT = 1ms
    # ssird_sim_dur_list = [0.1]
    # dctcp_sim_dur_list = [0.1]

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
    # experiment_incast_3_to_1_test(is_full_postproc=True, title_addendum="_3to1_incast_test_2flo", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_incast_3_to_1_test(is_full_postproc=True, title_addendum="_3to1_incast_test_31flo", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_incast_3to1_16GbpsFlo(is_full_postproc=True, title_addendum="_incast_3to1_5flo_16GbpsFlo_200KBflo", log_level=dale_experiment_rig.LOG_LEVEL_2) 


    ''' === 1458B, RTT = 5us === '''

    # ''' 
    #     3 to 1 incast experiment
    #         * 8flo
    #         * 1458B per bload
    #         * 1000ns intervals (avg)
    #         * mean num bloads = 500
    #         * 93.312Gbps total per sender
    # '''
    # experiment_incast_poisson_flows(
    #     topo_yaml_file="4-hosts.yaml",
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0)],
    #     num_flows=8,
    #     byteload_size_B=1458,
    #     target_mean_byteload_interval_nanosec=1000,
    #     target_mean_num_byteloads=500,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_num_byteloads=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.01],
    #     dctcp_sim_dur_list=[0.01],
    #     is_full_postproc=True,
    #     title_addendum="_incast_poisson_3to1_8flo_1458B_1us_93pt312Gbps",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2
    # )

    ''' 
        3 to 1 incast experiment (low load)
            * 2flo
            * 1458B per bload
            * 1000ns intervals (avg)
            * mean num bloads = 500
            * 23.33Gbps total per sender
            * 69.984Gbps total at downlink
    '''
    experiment_incast_poisson_flows(
        topo_yaml_file="4-hosts.yaml",
        src_dst_pairs_list=[(1,0), (2,0), (3,0)],
        num_flows=2,
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
        title_addendum="_incast_poisson_3to1_2flo_1458B_1us_23pt33Gbps",
        log_level=dale_experiment_rig.LOG_LEVEL_2
    )

    # ''' 
    #     3 to 1 incast experiment
    #         * 8flo
    #         * 1458B per bload
    #         * 1000ns intervals (avg)
    #         * fix num bloads = 500
    #         * 93.312Gbps total per sender
    # '''
    # experiment_incast_poisson_flows(
    #     topo_yaml_file="4-hosts.yaml",
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0)],
    #     num_flows=8,
    #     byteload_size_B=1458,
    #     target_mean_byteload_interval_nanosec=1000,
    #     target_mean_num_byteloads=500,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_num_byteloads=False,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.01],
    #     dctcp_sim_dur_list=[0.01],
    #     is_full_postproc=True,
    #     title_addendum="_incast_poisson_3to1_8flo_1458B_1us_93pt312Gbps_fixed_bload",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2
    # )

    # ''' 
    #     3 to 1 incast experiment
    #         * 8flo
    #         * 1458B per bload
    #         * 1000ns intervals (avg)
    #         * mean num bloads = 500
    #         * 93.312Gbps total per sender
    # '''
    # experiment_incast_poisson_flows(
    #     topo_yaml_file="4-hosts.yaml",
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0)],
    #     num_flows=8,
    #     byteload_size_B=1458,
    #     target_mean_byteload_interval_nanosec=1000,
    #     target_mean_num_byteloads=500,
    #     target_mean_flow_interarr_ns=0,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_num_byteloads=True,
    #     is_use_poisson_flow_interarr=False,
    #     ssird_sim_dur_list=[0.01],
    #     dctcp_sim_dur_list=[0.01],
    #     is_full_postproc=True,
    #     title_addendum="_incast_poisson_3to1_8flo_1458B_1us_93pt312Gbps_same_flo_interarr",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2
    # )

    # ''' 
    #     3 to 1 incast experiment
    #         * 8flo
    #         * 1458B per bload
    #         * 1000ns intervals (avg)
    #         * mean num bloads = 500
    #         * 93.312Gbps total per sender
    # '''
    # experiment_incast_poisson_flows(
    #     topo_yaml_file="4-hosts.yaml",
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0)],
    #     num_flows=8,
    #     byteload_size_B=1458,
    #     target_mean_byteload_interval_nanosec=1000,
    #     target_mean_num_byteloads=500,
    #     target_mean_flow_interarr_ns=0,
    #     is_use_poisson_byteload_intervals=False,
    #     is_use_poisson_num_byteloads=True,
    #     is_use_poisson_flow_interarr=False,
    #     ssird_sim_dur_list=[0.01],
    #     dctcp_sim_dur_list=[0.01],
    #     is_full_postproc=True,
    #     title_addendum="_incast_poisson_3to1_8flo_1458B_1us_93pt312Gbps_same_flo_interarr_same_interval",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2
    # )

    # ''' 
    #     3 to 1 incast experiment
    #         * 8flo
    #         * 1458B per bload
    #         * 1000ns intervals (avg)
    #         * mean num bloads = 500
    #         * 93.312Gbps total per sender
    # '''
    # experiment_incast_poisson_flows(
    #     topo_yaml_file="4-hosts.yaml",
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0)],
    #     num_flows=8,
    #     byteload_size_B=1458,
    #     target_mean_byteload_interval_nanosec=1000,
    #     target_mean_num_byteloads=500,
    #     target_mean_flow_interarr_ns=0,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_num_byteloads=False,
    #     is_use_poisson_flow_interarr=False,
    #     ssird_sim_dur_list=[0.01],
    #     dctcp_sim_dur_list=[0.01],
    #     is_full_postproc=True,
    #     title_addendum="_incast_poisson_3to1_8flo_1458B_1us_93pt312Gbps_same_flo_interarr_fixed_num_bload",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2
    # )

    # ''' 
    #     9 to 1 incast experiment
    #         * 8flo
    #         * 1458B per bload
    #         * 1000ns intervals (avg)
    #         * mean num bloads = 500
    #         * 93.312Gbps total per sender
    # '''
    # experiment_incast_poisson_flows(
    #     topo_yaml_file='10-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0)],
    #     num_flows=8,
    #     byteload_size_B=1458,
    #     target_mean_byteload_interval_nanosec=1000,
    #     target_mean_num_byteloads=500,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_num_byteloads=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.01],
    #     dctcp_sim_dur_list=[0.01],
    #     is_full_postproc=True,
    #     title_addendum="_incast_poisson_9to1_8flo_1458B_1us_93pt312Gbps",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2
    # ) 

    ''' === 1560B, RTT = 5us === '''

    # ''' 
    #     3 to 1 incast experiment
    #         * 8flo
    #         * 1560B per bload
    #         * 1000ns intervals (avg)
    #         * mean num bloads = 500
    #         * 99.84Gbps total per sender
    # '''
    # experiment_incast_poisson_flows(
    #     src_dst_pair_list=[(1,0), (2,0), (3,0)],
    #     num_flows=8,
    #     byteload_size_B=1560,
    #     target_mean_byteload_interval_nanosec=1000,
    #     target_mean_num_byteloads=500,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_num_byteloads=True,
    #     is_use_poisson_flow_interarr=True,
    #     is_full_postproc=True,
    #     title_addendum="_incast_poisson_3to1_8flo_1560B_1us_99pt84Gbps",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2
    # )

    # ''' 
    #     3 to 1 incast experiment
    #         * 8flo
    #         * 1560B per bload
    #         * 1000ns intervals (avg)
    #         * fix num bloads = 500
    #         * 99.84Gbps total per sender
    # '''
    # experiment_incast_poisson_flows(
    #     # topo_yaml_file="4-hosts.yaml",
    #     src_dst_pair_list=[(1,0), (2,0), (3,0)],
    #     num_flows=8,
    #     byteload_size_B=1560,
    #     target_mean_byteload_interval_nanosec=1000,
    #     target_mean_num_byteloads=500,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_num_byteloads=False,
    #     is_use_poisson_flow_interarr=True,
    #     is_full_postproc=True,
    #     title_addendum="_incast_poisson_3to1_8flo_1560B_1us_99pt84Gbps_fixed_bload",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2
    # )

    # ''' 
    #     3 to 1 incast experiment
    #         * 8flo
    #         * 1560B per bload
    #         * 1000ns intervals (avg)
    #         * mean num bloads = 500
    #         * 99.84Gbps total per sender
    # '''
    # experiment_incast_poisson_flows(
    #     topo_yaml_file="4-hosts.yaml",
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0)],
    #     num_flows=8,
    #     byteload_size_B=1560,
    #     target_mean_byteload_interval_nanosec=1000,
    #     target_mean_num_byteloads=500,
    #     target_mean_flow_interarr_ns=0,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_num_byteloads=True,
    #     is_use_poisson_flow_interarr=False,
    #     ssird_sim_dur_list=[0.01],
    #     dctcp_sim_dur_list=[0.01],
    #     is_full_postproc=True,
    #     title_addendum="_incast_poisson_3to1_8flo_1560B_1us_99pt84Gbps_same_flo_interarr",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2
    # )

    # ''' 
    #     3 to 1 incast experiment
    #         * 8flo
    #         * 1560B per bload
    #         * 1000ns intervals (avg)
    #         * mean num bloads = 500
    #         * 99.84Gbps total per sender
    # '''
    # experiment_incast_poisson_flows(
    #     topo_yaml_file="4-hosts.yaml",
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0)],
    #     num_flows=8,
    #     byteload_size_B=1560,
    #     target_mean_byteload_interval_nanosec=1000,
    #     target_mean_num_byteloads=500,
    #     target_mean_flow_interarr_ns=0,
    #     is_use_poisson_byteload_intervals=False,
    #     is_use_poisson_num_byteloads=True,
    #     is_use_poisson_flow_interarr=False,
    #     ssird_sim_dur_list=[0.01],
    #     dctcp_sim_dur_list=[0.01],
    #     is_full_postproc=True,
    #     title_addendum="_incast_poisson_3to1_8flo_1560B_1us_99pt84Gbps_same_flo_interarr_same_interval",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2
    # )

    # ''' 
    #     3 to 1 incast experiment
    #         * 8flo
    #         * 1560B per bload
    #         * 1000ns intervals (avg)
    #         * mean num bloads = 500
    #         * 99.84Gbps total per sender
    # '''
    # experiment_incast_poisson_flows(
    #     topo_yaml_file="4-hosts.yaml",
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0)],
    #     num_flows=8,
    #     byteload_size_B=1560,
    #     target_mean_byteload_interval_nanosec=1000,
    #     target_mean_num_byteloads=500,
    #     target_mean_flow_interarr_ns=0,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_num_byteloads=False,
    #     is_use_poisson_flow_interarr=False,
    #     ssird_sim_dur_list=[0.01],
    #     dctcp_sim_dur_list=[0.01],
    #     is_full_postproc=True,
    #     title_addendum="_incast_poisson_3to1_8flo_1560B_1us_99pt84Gbps_same_flo_interarr_fixed_num_bload",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2
    # )

    # ''' 
    #     9 to 1 incast experiment
    #         * 8flo
    #         * 1560B per bload
    #         * 1000ns intervals (avg)
    #         * mean num bloads = 500
    #         * 99.84Gbps total per sender
    # '''
    # experiment_incast_poisson_flows(
    #     topo_yaml_file='10-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0)],
    #     num_flows=8,
    #     byteload_size_B=1560,
    #     target_mean_byteload_interval_nanosec=1000,
    #     target_mean_num_byteloads=500,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_num_byteloads=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.01],
    #     dctcp_sim_dur_list=[0.01],
    #     is_full_postproc=True,
    #     title_addendum="_incast_poisson_9to1_8flo_1560B_1us_99pt84Gbps",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2
    # )   

    # ''' === RTT = 1ms === '''

    # ''' 
    #     3 to 1 incast experiment (RTT = 1ms)
    #         * 8flo
    #         * 1560B per bload
    #         * 1000ns intervals (avg)
    #         * mean num bloads = 500
    #         * 99.84Gbps total per sender
    # '''
    # experiment_incast_poisson_flows(
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0)],
    #     num_flows=8,
    #     byteload_size_B=1560,
    #     target_mean_byteload_interval_nanosec=1000,
    #     target_mean_num_byteloads=500,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_num_byteloads=True,
    #     is_use_poisson_flow_interarr=True,
    #     is_full_postproc=True,
    #     title_addendum="_incast_poisson_3to1_8flo_1560B_1us_99pt84Gbps_1msRTT",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2
    # )

    # ''' 
    #     3 to 1 incast experiment (RTT = 1ms)
    #         * 8flo
    #         * 1560B per bload
    #         * 1000ns intervals (avg)
    #         * fix num bloads = 500
    #         * 99.84Gbps total per sender
    # '''
    # experiment_incast_poisson_flows(
    #     # topo_yaml_file="4-hosts.yaml",
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0)],
    #     num_flows=8,
    #     byteload_size_B=1560,
    #     target_mean_byteload_interval_nanosec=1000,
    #     target_mean_num_byteloads=500,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_num_byteloads=False,
    #     is_use_poisson_flow_interarr=True,
    #     is_full_postproc=True,
    #     title_addendum="_incast_poisson_3to1_8flo_1560B_1us_99pt84Gbps_fixed_bload_1msRTT",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2
    # )