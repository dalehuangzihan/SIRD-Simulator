import datetime
import dale_experiment_rig

logger = dale_experiment_rig.logging.getLogger(__name__)

def experiment_1458B_bloads_8flo_93pt312Gbps_gdpt(is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"Normal_Byteloads{title_addendum}"
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(0,1)]

    minimum_interval_us = 1
    total_flow_size_B = 1458 * 10000 # 10000 bloads

    byteload_size_B_list = [1458] 
    num_of_experiments = len(byteload_size_B_list)
    num_flows = 8 # for 93.312Gbps total app goodput
    inter_flow_spacing_us = 0 # TODO: for testing
    flow_start_times_us_list = [i * inter_flow_spacing_us for i in range(0, num_flows)]

    dale_experiment_rig.init_logs(experiment_family, f"subpkt_experiment_{num_flows}flo_{total_flow_size_B}B_total_{min(byteload_size_B_list)}B_to_{max(byteload_size_B_list)}B.log")

    logger.debug(f"Protos tested: {proto_names}")
    logger.debug(f"Total_flow_size_B: {total_flow_size_B}")
    logger.debug(f"Byteload sizes list: {byteload_size_B_list}")
    logger.debug(f"Num Flows: {num_flows}")
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

    ssird_sim_dur_list = [0.02, 0.02, 0.02, 0.02, 0.02] # for RTT = 5us
    dctcp_sim_dur_list = [0.001, 0.001, 0.001, 0.001, 0.001] # for RTT = 5us

    # TODO: currently only calculates theoretical gbps for in-parallel flows
    gdpt_gbps_theoretical_list = []
    for i in range(0, num_of_experiments):
        gdpt_gbps_theoretical = num_flows * (byteload_size_B_list[i]*8)/(inter_byteload_period_us_list[i]) * pow(10,-3)
        if byteload_size_B_list[i] < 4: gdpt_gbps_theoretical *= 4  # mirror treatment of hypersmall byteloads by r2p2-app.cc
        gdpt_gbps_theoretical_list.append(gdpt_gbps_theoretical)
    assert(len(gdpt_gbps_theoretical_list) == num_of_experiments)

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
    logger.info(f"Gdpt GBps theoretical: {gdpt_gbps_theoretical_list}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    # return

    exp_grp = dale_experiment_rig.ExperimentGroup(experiment_family, proto_names, src_dst_pairs_list, flow_start_times_us_list, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, ssird_sim_dur_list, dctcp_sim_dur_list, is_full_postproc, log_level, title_addendum)

    exp_metrics = exp_grp.perform_experiment()

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
    logger.debug(f"Flow start times (us): {flow_start_times_us_list}")
    logger.info(f"Gdpt Gbps theoretical: {gdpt_gbps_theoretical_list}")

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

def experiment_1560B_bloads_8flo_99pt84Gbps_gdpt(is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"Normal_Byteloads{title_addendum}"
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(0,1)]

    minimum_interval_us = 1
    total_flow_size_B = 1560 * 10000 # 10000 bloads

    byteload_size_B_list = [1560] 
    num_of_experiments = len(byteload_size_B_list)
    num_flows = 8 # for 99.84Gbps total app goodput
    inter_flow_spacing_us = 0 # TODO: for testing
    flow_start_times_us_list = [i * inter_flow_spacing_us for i in range(0, num_flows)]

    dale_experiment_rig.init_logs(experiment_family, f"subpkt_experiment_{num_flows}flo_{total_flow_size_B}B_total_{min(byteload_size_B_list)}B_to_{max(byteload_size_B_list)}B.log")

    logger.debug(f"Protos tested: {proto_names}")
    logger.debug(f"Total_flow_size_B: {total_flow_size_B}")
    logger.debug(f"Byteload sizes list: {byteload_size_B_list}")
    logger.debug(f"Num Flows: {num_flows}")
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

    ssird_sim_dur_list = [0.02, 0.02, 0.02, 0.02, 0.02] # for RTT = 5us
    # ssird_sim_dur_list = [0.01, 0.01, 0.01, 0.01, 0.01] # RTT = 1ms
    dctcp_sim_dur_list = [0.3, 0.3, 0.3, 0.3, 0.3] # for RTT = 1ms

    # TODO: currently only calculates theoretical gbps for in-parallel flows
    gdpt_gbps_theoretical_list = []
    for i in range(0, num_of_experiments):
        gdpt_gbps_theoretical = num_flows * (byteload_size_B_list[i]*8)/(inter_byteload_period_us_list[i]) * pow(10,-3)
        if byteload_size_B_list[i] < 4: gdpt_gbps_theoretical *= 4  # mirror treatment of hypersmall byteloads by r2p2-app.cc
        gdpt_gbps_theoretical_list.append(gdpt_gbps_theoretical)
    assert(len(gdpt_gbps_theoretical_list) == num_of_experiments)

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
    logger.info(f"Gdpt GBps theoretical: {gdpt_gbps_theoretical_list}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    # return

    exp_grp = dale_experiment_rig.ExperimentGroup(experiment_family, proto_names, src_dst_pairs_list, flow_start_times_us_list, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, ssird_sim_dur_list, dctcp_sim_dur_list, is_full_postproc, log_level, title_addendum)

    exp_metrics = exp_grp.perform_experiment()

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
    logger.debug(f"Flow start times (us): {flow_start_times_us_list}")
    logger.info(f"Gdpt Gbps theoretical: {gdpt_gbps_theoretical_list}")

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

def experiment_1458B_bloads_85flo_99pt144Gbps_gdpt(is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"Normal_Byteloads{title_addendum}"
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(0,1)]

    minimum_interval_us = 10
    total_flow_size_B = 1458 * 10000 # 10000 bloads

    byteload_size_B_list = [1458] 
    num_of_experiments = len(byteload_size_B_list)
    num_flows = 85 # for 99.144Gbps total app goodput
    inter_flow_spacing_us = 0 # TODO: for testing
    flow_start_times_us_list = [i * inter_flow_spacing_us for i in range(0, num_flows)]

    dale_experiment_rig.init_logs(experiment_family, f"subpkt_experiment_{num_flows}flo_{total_flow_size_B}B_total_{min(byteload_size_B_list)}B_to_{max(byteload_size_B_list)}B.log")

    logger.debug(f"Protos tested: {proto_names}")
    logger.debug(f"Total_flow_size_B: {total_flow_size_B}")
    logger.debug(f"Byteload sizes list: {byteload_size_B_list}")
    logger.debug(f"Num Flows: {num_flows}")
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

    ssird_sim_dur_list = [0.012, 0.012, 0.012, 0.012, 0.012]
    # dctcp_sim_dur_list = [0.03, 0.03, 0.03, 0.03, 0.03] # for RTT = 5us
    dctcp_sim_dur_list = [0.3, 0.3, 0.3, 0.3, 0.3] # for RTT = 1ms

    # TODO: currently only calculates theoretical gbps for in-parallel flows
    gdpt_gbps_theoretical_list = []
    for i in range(0, num_of_experiments):
        gdpt_gbps_theoretical = num_flows * (byteload_size_B_list[i]*8)/(inter_byteload_period_us_list[i]) * pow(10,-3)
        if byteload_size_B_list[i] < 4: gdpt_gbps_theoretical *= 4  # mirror treatment of hypersmall byteloads by r2p2-app.cc
        gdpt_gbps_theoretical_list.append(gdpt_gbps_theoretical)
    assert(len(gdpt_gbps_theoretical_list) == num_of_experiments)

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
    logger.info(f"Gdpt GBps theoretical: {gdpt_gbps_theoretical_list}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    # return

    exp_grp = dale_experiment_rig.ExperimentGroup(experiment_family, proto_names, src_dst_pairs_list, flow_start_times_us_list, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, ssird_sim_dur_list, dctcp_sim_dur_list, is_full_postproc, log_level, title_addendum)

    exp_metrics = exp_grp.perform_experiment()

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
    logger.debug(f"Flow start times (us): {flow_start_times_us_list}")
    logger.info(f"Gdpt Gbps theoretical: {gdpt_gbps_theoretical_list}")

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

def experiment_poissoninterval_1458B_bloads_10flo_10GbpsFlo(is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"Poisson_Intervals{title_addendum}"
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(0,1)]

    # TODO: for now generate flow spec by hand to debug experiment rig
    # num_flows = 2
    # target_flow_rate_gbps = 69 # TODO: is just placeholder
    # manual_flow_spec = dale_experiment_rig.FlowSpec(
    #     num_byteloads=5,
    #     byteload_size_B_list=[1458]*5,
    #     flow_size_B=1458*5,
    #     interval_us_list=[1]*(5-1),
    #     byteload_timestamp_us_list=[0, 1, 2, 3, 4],
    #     total_flow_send_duration_us=4,
    #     flow_rate_bps=11.664*pow(10,9)
    # )
    # flow_spec_list = [manual_flow_spec] * num_flows

    # NOTE: here we only do 1 experiment, but in the future we could do multiple experiments, each with their own set of flow constraints from which flows are generated
    num_flows = 10
    target_flow_rate_gbps = 10
    target_flow_rate_bps = target_flow_rate_gbps * pow(10,9)
    min_num_byteloads = 100
    max_num_byteloads = 5000
    min_byteload_size_B = 1458
    max_byteload_size_B = 1458
    min_interval_us = 10
    max_interval_us = 100
    poisson_flow_generator = dale_experiment_rig.PoissonFlowGenerator(target_flow_rate_bps, min_num_byteloads, max_num_byteloads, min_byteload_size_B, max_byteload_size_B, min_interval_us, max_interval_us)
    flow_spec_list = poisson_flow_generator.generate_n_flows(num_flows)

    inter_flow_spacing_us = 0 # TODO: for testing
    flow_start_times_us_list = [i * inter_flow_spacing_us for i in range(0, num_flows)]

    flow_spec_list_list = [flow_spec_list]
    flow_start_times_us_list_list = [flow_start_times_us_list]

    num_of_experiments = len(flow_spec_list_list)
    assert(len(flow_start_times_us_list_list) == num_of_experiments)

    logs_file_name = f"poisson_intervals_experiment_{num_flows}flo_{target_flow_rate_gbps}GbpsFlo_{dale_experiment_rig.Experiment.get_date_now()}.log"
    dale_experiment_rig.init_logs(experiment_family, logs_file_name)

    # Back up flow spec list # TODO: make infra to back up flow spec list list
    flow_spec_dict = dale_experiment_rig.FlowSpec.flow_spec_list_to_dict(flow_spec_list, flow_start_times_us_list)
    dale_experiment_rig.FlowSpec.flow_specs_dict_to_file(flow_spec_dict, dale_experiment_rig.FLOW_SPECS_JSON_PATH, logs_file_name)

    flow_rate_gbps_list = [round(f.flow_rate_bps*pow(10,-9),6) for f in flow_spec_list]
    flow_size_B_list = [f.flow_size_B for f in flow_spec_list]
    flow_num_byteloads_list = [f.num_byteloads for f in flow_spec_list]
    flow_send_durations_us_list = [f.total_flow_send_duration_us for f in flow_spec_list]
    flow_min_byteload_size_B_list = [min(f.byteload_size_B_list) for f in flow_spec_list]
    flow_max_byteload_size_B_list = [max(f.byteload_size_B_list) for f in flow_spec_list]
    flow_min_interval_us = [min(f.interval_us_list) for f in flow_spec_list]
    flow_max_interval_us = [max(f.interval_us_list) for f in flow_spec_list]

    logger.info(f"Protos tested: {proto_names}")
    logger.info(f"Num Flows: {num_flows}")
    logger.info(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    logger.info(f"Flow Start Times (us): {flow_start_times_us_list}")
    logger.info(f"Flow Rate (Gbps): {flow_rate_gbps_list}")
    logger.info(f"Flow Size (B): {flow_size_B_list}")
    logger.info(f"Num Byteloads: {flow_num_byteloads_list}")
    logger.info(f"Flow Send Durations (us): {flow_send_durations_us_list}")
    logger.info(f"Flow Min Byteload Size (B): {flow_min_byteload_size_B_list}")
    logger.info(f"Flow Max Byteload Size (B): {flow_max_byteload_size_B_list}")
    logger.info(f"Flow Min Interval (us): {flow_min_interval_us}")
    logger.info(f"Flow Max Interval (us): {flow_max_interval_us}")

    # ssird_sim_dur_list = [0.0001] * num_flows
    # dctcp_sim_dur_list = [0.0001] * num_flows
    ssird_sim_dur_list = [0.001, 0.001, 0.001, 0.001, 0.001]
    dctcp_sim_dur_list = [0.001, 0.001, 0.001, 0.001, 0.001] # for RTT = 5us
    # TODO: modify assertion to work for spec that does specifies multiple experiments
    logger.debug(f"Max flow send durations (us): {max(flow_send_durations_us_list)}")
    assert(max(flow_send_durations_us_list) * pow(10,-6) * 1.5 < ssird_sim_dur_list[0])
    assert(max(flow_send_durations_us_list) * pow(10,-6) * 1.5 < dctcp_sim_dur_list[0])

    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    # return

    exp_grp = dale_experiment_rig.ExperimentGroup(
        experiment_family,
        proto_names,
        src_dst_pairs_list,
        num_flows,
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
    logger.info(f"Num Flows: {num_flows}")
    logger.info(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    logger.info(f"Flow Start Times (us): {flow_start_times_us_list}")
    logger.info(f"Flow Rate (Gbps): {flow_rate_gbps_list}")
    logger.info(f"Flow Size (B): {flow_size_B_list}")
    logger.info(f"Num Byteloads: {flow_num_byteloads_list}")
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

def experiment_poissoninterval_1458B_bloads_50flo_1GbpsFlo(is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"Poisson_Intervals{title_addendum}"
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(0,1)]

    # NOTE: here we only do 1 experiment, but in the future we could do multiple experiments, each with their own set of flow constraints from which flows are generated
    num_flows = 50
    target_flow_rate_gbps = 1
    target_flow_rate_bps = target_flow_rate_gbps * pow(10,9)
    min_num_byteloads = 1000
    max_num_byteloads = 5000
    min_byteload_size_B = 1458
    max_byteload_size_B = 1458
    min_interval_us = 10
    max_interval_us = 100
    poisson_flow_generator = dale_experiment_rig.PoissonFlowGenerator(target_flow_rate_bps, min_num_byteloads, max_num_byteloads, min_byteload_size_B, max_byteload_size_B, min_interval_us, max_interval_us)
    flow_spec_list = poisson_flow_generator.generate_n_flows(num_flows)

    inter_flow_spacing_us = 0 # TODO: for testing
    flow_start_times_us_list = [i * inter_flow_spacing_us for i in range(0, num_flows)]

    flow_spec_list_list = [flow_spec_list]
    flow_start_times_us_list_list = [flow_start_times_us_list]

    num_of_experiments = len(flow_spec_list_list)
    assert(len(flow_start_times_us_list_list) == num_of_experiments)

    logs_file_name = f"poisson_intervals_experiment_{num_flows}flo_{target_flow_rate_gbps}GbpsFlo_{dale_experiment_rig.Experiment.get_date_now()}.log"
    dale_experiment_rig.init_logs(experiment_family, logs_file_name)

    # Back up flow spec list # TODO: make infra to back up flow spec list list
    flow_spec_dict = dale_experiment_rig.FlowSpec.flow_spec_list_to_dict(flow_spec_list, flow_start_times_us_list)
    dale_experiment_rig.FlowSpec.flow_specs_dict_to_file(flow_spec_dict, dale_experiment_rig.FLOW_SPECS_JSON_PATH, logs_file_name)

    flow_rate_gbps_list = [round(f.flow_rate_bps*pow(10,-9),6) for f in flow_spec_list]
    flow_size_B_list = [f.flow_size_B for f in flow_spec_list]
    flow_num_byteloads_list = [f.num_byteloads for f in flow_spec_list]
    flow_send_durations_us_list = [f.total_flow_send_duration_us for f in flow_spec_list]
    flow_min_byteload_size_B_list = [min(f.byteload_size_B_list) for f in flow_spec_list]
    flow_max_byteload_size_B_list = [max(f.byteload_size_B_list) for f in flow_spec_list]
    flow_min_interval_us = [min(f.interval_us_list) for f in flow_spec_list]
    flow_max_interval_us = [max(f.interval_us_list) for f in flow_spec_list]

    logger.info(f"Protos tested: {proto_names}")
    logger.info(f"Num Flows: {num_flows}")
    logger.info(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    logger.info(f"Flow Start Times (us): {flow_start_times_us_list}")
    logger.info(f"Flow Rate (Gbps): {flow_rate_gbps_list}")
    logger.info(f"Flow Size (B): {flow_size_B_list}")
    logger.info(f"Num Byteloads: {flow_num_byteloads_list}")
    logger.info(f"Flow Send Durations (us): {flow_send_durations_us_list}")
    logger.info(f"Flow Min Byteload Size (B): {flow_min_byteload_size_B_list}")
    logger.info(f"Flow Max Byteload Size (B): {flow_max_byteload_size_B_list}")
    logger.info(f"Flow Min Interval (us): {flow_min_interval_us}")
    logger.info(f"Flow Max Interval (us): {flow_max_interval_us}")

    # ssird_sim_dur_list = [0.0001] * num_flows
    # dctcp_sim_dur_list = [0.0001] * num_flows
    ssird_sim_dur_list = [0.1, 0.1, 0.1, 0.1, 0.1]
    dctcp_sim_dur_list = [0.1, 0.1, 0.1, 0.1, 0.1] # for RTT = 5us
    # TODO: modify assertion to work for spec that does specifies multiple experiments
    logger.debug(f"Max flow send durations (us): {max(flow_send_durations_us_list)}")
    assert(max(flow_send_durations_us_list) * pow(10,-6) * 1.5 < ssird_sim_dur_list[0])
    assert(max(flow_send_durations_us_list) * pow(10,-6) * 1.5 < dctcp_sim_dur_list[0])

    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    # return

    exp_grp = dale_experiment_rig.ExperimentGroup(
        experiment_family,
        proto_names,
        src_dst_pairs_list,
        num_flows,
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
    logger.info(f"Num Flows: {num_flows}")
    logger.info(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    logger.info(f"Flow Start Times (us): {flow_start_times_us_list}")
    logger.info(f"Flow Rate (Gbps): {flow_rate_gbps_list}")
    logger.info(f"Flow Size (B): {flow_size_B_list}")
    logger.info(f"Num Byteloads: {flow_num_byteloads_list}")
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

def experiment_poissoninterval_1458B_bloads_50flo_2GbpsFlo(is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"Poisson_Intervals{title_addendum}"
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(0,1)]

    # NOTE: here we only do 1 experiment, but in the future we could do multiple experiments, each with their own set of flow constraints from which flows are generated
    num_flows = 50
    target_flow_rate_gbps = 2
    # target_flow_rate_bps = target_flow_rate_gbps * pow(10,9)
    # min_num_byteloads = 1000
    # max_num_byteloads = 5000
    # min_byteload_size_B = 1458
    # max_byteload_size_B = 1458
    # min_interval_us = 10
    # max_interval_us = 100
    # poisson_flow_generator = dale_experiment_rig.PoissonFlowGenerator(target_flow_rate_bps, min_num_byteloads, max_num_byteloads, min_byteload_size_B, max_byteload_size_B, min_interval_us, max_interval_us)
    # flow_spec_list = poisson_flow_generator.generate_n_flows(num_flows)
    # inter_flow_spacing_us = 0 # TODO: for testing
    # flow_start_times_us_list = [i * inter_flow_spacing_us for i in range(0, num_flows)]

    flow_start_times_us_list, flow_spec_list = dale_experiment_rig.FlowSpec.parse_flow_specs_json_file(dale_experiment_rig.SAVED_FLOW_SPECS_JSON_PATH, "poisson_intervals_experiment_50flo_2GbpsFlo_2025-08-04T_19-03-49Z.log")
    assert(len(flow_start_times_us_list) == len(flow_spec_list) and len(flow_spec_list) == num_flows)

    flow_spec_list_list = [flow_spec_list]
    flow_start_times_us_list_list = [flow_start_times_us_list]

    num_of_experiments = len(flow_spec_list_list)
    assert(len(flow_start_times_us_list_list) == num_of_experiments)

    logs_file_name = f"poisson_intervals_experiment_{num_flows}flo_{target_flow_rate_gbps}GbpsFlo_{dale_experiment_rig.Experiment.get_date_now()}.log"
    dale_experiment_rig.init_logs(experiment_family, logs_file_name)

    # # Back up flow spec list # TODO: make infra to back up flow spec list list
    # flow_spec_dict = dale_experiment_rig.FlowSpec.flow_spec_list_to_dict(flow_spec_list, flow_start_times_us_list)
    # dale_experiment_rig.FlowSpec.flow_specs_dict_to_file(flow_spec_dict, dale_experiment_rig.FLOW_SPECS_JSON_PATH, logs_file_name)

    flow_rate_gbps_list = [round(f.flow_rate_bps*pow(10,-9),6) for f in flow_spec_list]
    flow_size_B_list = [f.flow_size_B for f in flow_spec_list]
    flow_num_byteloads_list = [f.num_byteloads for f in flow_spec_list]
    flow_send_durations_us_list = [f.total_flow_send_duration_us for f in flow_spec_list]
    flow_min_byteload_size_B_list = [min(f.byteload_size_B_list) for f in flow_spec_list]
    flow_max_byteload_size_B_list = [max(f.byteload_size_B_list) for f in flow_spec_list]
    flow_min_interval_us = [min(f.interval_us_list) for f in flow_spec_list]
    flow_max_interval_us = [max(f.interval_us_list) for f in flow_spec_list]

    logger.info(f"Protos tested: {proto_names}")
    logger.info(f"Num Flows: {num_flows}")
    logger.info(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    logger.info(f"Flow Start Times (us): {flow_start_times_us_list}")
    logger.info(f"Flow Rate (Gbps): {flow_rate_gbps_list}")
    logger.info(f"Flow Size (B): {flow_size_B_list}")
    logger.info(f"Num Byteloads: {flow_num_byteloads_list}")
    logger.info(f"Flow Send Durations (us): {flow_send_durations_us_list}")
    logger.info(f"Flow Min Byteload Size (B): {flow_min_byteload_size_B_list}")
    logger.info(f"Flow Max Byteload Size (B): {flow_max_byteload_size_B_list}")
    logger.info(f"Flow Min Interval (us): {flow_min_interval_us}")
    logger.info(f"Flow Max Interval (us): {flow_max_interval_us}")

    ssird_sim_dur_list = [1]
    dctcp_sim_dur_list = [0.04] # NOTE: for dctcp test
    # ssird_sim_dur_list = [0.1, 0.1, 0.1, 0.1, 0.1]
    # dctcp_sim_dur_list = [0.1, 0.1, 0.1, 0.1, 0.1] # for RTT = 5us
    # TODO: modify assertion to work for spec that does specifies multiple experiments
    logger.debug(f"Max flow send durations (us): {max(flow_send_durations_us_list)}")
    assert(max(flow_send_durations_us_list) * pow(10,-6) * 1.5 < ssird_sim_dur_list[0])
    assert(max(flow_send_durations_us_list) * pow(10,-6) * 1.5 < dctcp_sim_dur_list[0])

    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    # return

    exp_grp = dale_experiment_rig.ExperimentGroup(
        experiment_family,
        proto_names,
        src_dst_pairs_list,
        num_flows,
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
    logger.info(f"Num Flows: {num_flows}")
    logger.info(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    logger.info(f"Flow Start Times (us): {flow_start_times_us_list}")
    logger.info(f"Flow Rate (Gbps): {flow_rate_gbps_list}")
    logger.info(f"Flow Size (B): {flow_size_B_list}")
    logger.info(f"Num Byteloads: {flow_num_byteloads_list}")
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

def simple_experiment(is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):

    experiment_family = f"DCTCP_CONN_POOL{title_addendum}"
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(0,1)]

    # TODO: for now generate flow spec by hand to debug experiment rig
    num_flows = 5
    target_flow_rate_gbps = -1 # TODO: is just placeholder
    manual_flow_spec = dale_experiment_rig.FlowSpec(
        num_byteloads=5,
        byteload_size_B_list=[1458]*5,
        flow_size_B=1458*5,
        interval_us_list=[1]*(5-1),
        byteload_timestamp_us_list=[0, 1, 2, 3, 4],
        total_flow_send_duration_us=4,
        flow_rate_bps=11.664*pow(10,9)
    )
    flow_spec_list = [manual_flow_spec] * num_flows

    inter_flow_spacing_us = 0 # TODO: for testing
    flow_start_times_us_list = [i * inter_flow_spacing_us for i in range(0, num_flows)]

    flow_spec_list_list = [flow_spec_list]
    flow_start_times_us_list_list = [flow_start_times_us_list]

    num_of_experiments = len(flow_spec_list_list)
    assert(len(flow_start_times_us_list_list) == num_of_experiments)

    logs_file_name = f"dctcp_conn_pool_{num_flows}flo_{target_flow_rate_gbps}GbpsFlo.log"
    dale_experiment_rig.init_logs(experiment_family, logs_file_name)

    # Back up flow spec list # TODO: make infra to back up flow spec list list
    flow_spec_dict = dale_experiment_rig.FlowSpec.flow_spec_list_to_dict(flow_spec_list, flow_start_times_us_list)
    dale_experiment_rig.FlowSpec.flow_specs_dict_to_file(flow_spec_dict, dale_experiment_rig.FLOW_SPECS_JSON_PATH, logs_file_name)

    flow_rate_gbps_list = [round(f.flow_rate_bps*pow(10,-9),6) for f in flow_spec_list]
    flow_size_B_list = [f.flow_size_B for f in flow_spec_list]
    flow_num_byteloads_list = [f.num_byteloads for f in flow_spec_list]
    flow_send_durations_us_list = [f.total_flow_send_duration_us for f in flow_spec_list]
    flow_min_byteload_size_B_list = [min(f.byteload_size_B_list) for f in flow_spec_list]
    flow_max_byteload_size_B_list = [max(f.byteload_size_B_list) for f in flow_spec_list]
    flow_min_interval_us = [min(f.interval_us_list) for f in flow_spec_list]
    flow_max_interval_us = [max(f.interval_us_list) for f in flow_spec_list]

    logger.info(f"Protos tested: {proto_names}")
    logger.info(f"Num Flows: {num_flows}")
    logger.info(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    logger.info(f"Flow Start Times (us): {flow_start_times_us_list}")
    logger.info(f"Flow Rate (Gbps): {flow_rate_gbps_list}")
    logger.info(f"Flow Size (B): {flow_size_B_list}")
    logger.info(f"Num Byteloads: {flow_num_byteloads_list}")
    logger.info(f"Flow Send Durations (us): {flow_send_durations_us_list}")
    logger.info(f"Flow Min Byteload Size (B): {flow_min_byteload_size_B_list}")
    logger.info(f"Flow Max Byteload Size (B): {flow_max_byteload_size_B_list}")
    logger.info(f"Flow Min Interval (us): {flow_min_interval_us}")
    logger.info(f"Flow Max Interval (us): {flow_max_interval_us}")

    ssird_sim_dur_list = [0.0001] * num_flows
    dctcp_sim_dur_list = [0.0001] * num_flows
    # TODO: modify assertion to work for spec that does specifies multiple experiments
    logger.debug(f"Max flow send durations (us): {max(flow_send_durations_us_list)}")
    assert(max(flow_send_durations_us_list) * pow(10,-6) * 1.5 < ssird_sim_dur_list[0])
    assert(max(flow_send_durations_us_list) * pow(10,-6) * 1.5 < dctcp_sim_dur_list[0])

    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    # return

    exp_grp = dale_experiment_rig.ExperimentGroup(
        experiment_family,
        proto_names,
        src_dst_pairs_list,
        num_flows,
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
    logger.info(f"Num Flows: {num_flows}")
    logger.info(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")
    logger.info(f"Flow Start Times (us): {flow_start_times_us_list}")
    logger.info(f"Flow Rate (Gbps): {flow_rate_gbps_list}")
    logger.info(f"Flow Size (B): {flow_size_B_list}")
    logger.info(f"Num Byteloads: {flow_num_byteloads_list}")
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

    ''' --- RTT = 5us ---- '''
    # experiment_1458B_bloads_8flo_93pt312Gbps_gdpt(is_full_postproc=True, title_addendum="_1458B_8flo_93pt312Gbps", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_1560B_bloads_8flo_99pt84Gbps_gdpt(is_full_postproc=True, title_addendum="_1560B_8flo_99pt84Gbps", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_1458B_bloads_85flo_99pt144Gbps_gdpt(is_full_postproc=True, title_addendum="_1458B_85flo_99pt144Gbps", log_level=dale_experiment_rig.LOG_LEVEL_2)

    # # RTT = 1ms ----
    # # experiment_1458B_bloads_8flo_93pt312Gbps_gdpt(is_full_postproc=True, title_addendum="_1458B_8flo_93pt312Gbps_1msRTT", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # # experiment_1560B_bloads_8flo_99pt84Gbps_gdpt(is_full_postproc=True, title_addendum="_1560B_8flo_99pt84Gbps_1msRTT", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # # experiment_1458B_bloads_85flo_99pt144Gbps_gdpt(is_full_postproc=True, title_addendum="_1458B_85flo_99pt144Gbps_1msRTT", log_level=dale_experiment_rig.LOG_LEVEL_2)


    ''' --- Poisson Process Intervals, RTT = 5us --- '''
    # experiment_poissoninterval_1458B_bloads_10flo_10GbpsFlo(is_full_postproc=False, title_addendum="_poisson_10flo_10GbpsFlo", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_poissoninterval_1458B_bloads_50flo_1GbpsFlo(is_full_postproc=False, title_addendum="_poisson_50flo_1GbpsFlo", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_poissoninterval_1458B_bloads_50flo_2GbpsFlo(is_full_postproc=False, title_addendum="_poisson_50flo_2GbpsFlo", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_poissoninterval_1458B_bloads_50flo_2GbpsFlo(is_full_postproc=True, title_addendum="_poisson_50flo_2GbpsFlo_dctcp_test", log_level=dale_experiment_rig.LOG_LEVEL_6)

    ''' --- DCTCP Connection Pool Experiment, RTT = 5us --- '''
    simple_experiment(is_full_postproc=True, title_addendum="_dctcp_conn_pool", log_level=dale_experiment_rig.LOG_LEVEL_2)