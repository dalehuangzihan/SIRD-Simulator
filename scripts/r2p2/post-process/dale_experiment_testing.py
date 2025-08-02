import dale_experiment_rig

logger = dale_experiment_rig.logging.getLogger(__name__)

def experiment_vary_byteload_number_200KBflo_5flo(is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"FCT_VARY_NUM_BLOAD{title_addendum}"
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(0,1)]

    minimum_interval_us = 0.1 # 0.1us
    total_flow_size_B = 200000 # 200KB
    # NOTE: smallest byteload size that SSIRD sim is set up to use is 4B => with headers this makes a total of 64B per byteload.
    # NOTE: byteload sizes are multiples of 4 so that the inter-byteload periods are later calculated to be whole numbers in the end

    byteload_size_B_list = [20, 200, 2000] 
    num_of_experiments = len(byteload_size_B_list)
    num_flows = 5
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
    # total_injection_period_us = max(num_byteloads_per_flow_list) * minimum_interval_us
    # logger.debug(f"Total injection period (us): {total_injection_period_us}")
    # inter_byteload_period_us_list = [] 
    # for num_byteloads in num_byteloads_per_flow_list:
    #     inter_byteload_period_us = total_injection_period_us / num_byteloads
    #     inter_byteload_period_us_list.append(inter_byteload_period_us)
    inter_byteload_period_us_list = [10.0, 10.0, 10.0]
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

    ssird_sim_dur_list = [0.12, 0.12, 0.12]
    dctcp_sim_dur_list = [0.2, 0.2, 0.2]
    assert(len(ssird_sim_dur_list) == num_of_experiments)
    assert(len(dctcp_sim_dur_list) == num_of_experiments)

    # TODO: currently only calculates theoretical gbps for in-parallel flows
    gdpt_gbps_theoretical_list = []
    for i in range(0, num_of_experiments):
        gdpt_gbps_theoretical = num_flows * (byteload_size_B_list[i]*8)/(inter_byteload_period_us_list[i]) * pow(10,-3)
        if byteload_size_B_list[i] < 4: gdpt_gbps_theoretical *= 4  # mirror treatment of hypersmall byteloads by r2p2-app.cc
        gdpt_gbps_theoretical_list.append(gdpt_gbps_theoretical)
    assert(len(gdpt_gbps_theoretical_list) == num_of_experiments)

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    # logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
    logger.info(f"Gdpt GBps theoretical: {gdpt_gbps_theoretical_list}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    # return

    exp_grp = dale_experiment_rig.ExperimentGroup(experiment_family, proto_names, src_dst_pairs_list, flow_start_times_us_list, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, ssird_sim_dur_list, dctcp_sim_dur_list, is_full_postproc, log_level, title_addendum)

    ssird_fct_list, dctcp_fct_list, gdpt_gbps_measured_list_ssird, gdpt_gbps_measured_list_dctcp, gdpt_gbps_measured_per_flow_list_list_ssird, gdpt_gbps_measured_per_flow_list_list_dctcp = exp_grp.perform_experiment()

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    # logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
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

def experiment_vary_byteload_size_5flo(is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"FCT_VARY_BLOAD_SIZE{title_addendum}"
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(0,1)]

    minimum_interval_us = 0.1 # 0.1us
    # total_flow_size_B = 200000 # 200KB
    # NOTE: smallest byteload size that SSIRD sim is set up to use is 4B => with headers this makes a total of 64B per byteload.
    # NOTE: byteload sizes are multiples of 4 so that the inter-byteload periods are later calculated to be whole numbers in the end

    byteload_size_B_list = [20, 200, 2000] 
    num_of_experiments = len(byteload_size_B_list)
    num_flows = 5
    inter_flow_spacing_us = 0 # TODO: for testing
    flow_start_times_us_list = [i * inter_flow_spacing_us for i in range(0, num_flows)]

    dale_experiment_rig.init_logs(experiment_family, f"subpkt_experiment_{num_flows}flo_xB_total_{min(byteload_size_B_list)}B_to_{max(byteload_size_B_list)}B.log")

    logger.debug(f"Protos tested: {proto_names}")
    # logger.debug(f"Total_flow_size_B: {total_flow_size_B}")
    logger.debug(f"Byteload sizes list: {byteload_size_B_list}")
    logger.debug(f"Num Flows: {num_flows}")
    logger.debug(f"Inter-flow spacing (us): {inter_flow_spacing_us}")
    logger.debug(f"Flow start times (us): {flow_start_times_us_list}")

    # calculate num of byteloads for experiment
    # num_byteloads_per_flow_list = []
    # for size in byteload_size_B_list:
    #     num_byteloads = None
    #     if size < 4:
    #         num_byteloads = total_flow_size_B // (4 * size)  # mirror treatment of hypersmall byteloads by r2p2-app.cc
    #     else:
    #         num_byteloads = total_flow_size_B // size
    #     num_byteloads_per_flow_list.append(num_byteloads)
    # logger.debug(f"Num Byteloads list: {num_byteloads_per_flow_list}")
    num_byteloads_per_flow_list = [100, 100, 100]
    assert(len(num_byteloads_per_flow_list) == num_of_experiments)

    # calculate inter-byteload periods for experiment
    # total_injection_period_us = max(num_byteloads_per_flow_list) * minimum_interval_us
    # logger.debug(f"Total injection period (us): {total_injection_period_us}")
    # inter_byteload_period_us_list = [] 
    # for num_byteloads in num_byteloads_per_flow_list:
    #     inter_byteload_period_us = total_injection_period_us / num_byteloads
    #     inter_byteload_period_us_list.append(inter_byteload_period_us)
    inter_byteload_period_us_list = [10.0, 10.0, 10.0]
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

    ssird_sim_dur_list = [0.01, 0.01, 0.01]
    dctcp_sim_dur_list = [0.1, 0.1, 0.1]
    assert(len(ssird_sim_dur_list) == num_of_experiments)
    assert(len(dctcp_sim_dur_list) == num_of_experiments)

    # TODO: currently only calculates theoretical gbps for in-parallel flows
    gdpt_gbps_theoretical_list = []
    for i in range(0, num_of_experiments):
        gdpt_gbps_theoretical = num_flows * (byteload_size_B_list[i]*8)/(inter_byteload_period_us_list[i]) * pow(10,-3)
        if byteload_size_B_list[i] < 4: gdpt_gbps_theoretical *= 4  # mirror treatment of hypersmall byteloads by r2p2-app.cc
        gdpt_gbps_theoretical_list.append(gdpt_gbps_theoretical)
    assert(len(gdpt_gbps_theoretical_list) == num_of_experiments)

    # logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    # logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
    logger.info(f"Gdpt GBps theoretical: {gdpt_gbps_theoretical_list}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    # return

    exp_grp = dale_experiment_rig.ExperimentGroup(experiment_family, proto_names, src_dst_pairs_list, flow_start_times_us_list, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, ssird_sim_dur_list, dctcp_sim_dur_list, is_full_postproc, log_level, title_addendum)

    ssird_fct_list, dctcp_fct_list, gdpt_gbps_measured_list_ssird, gdpt_gbps_measured_list_dctcp, gdpt_gbps_measured_per_flow_list_list_ssird, gdpt_gbps_measured_per_flow_list_list_dctcp = exp_grp.perform_experiment()

    # logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    # logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
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

def experiment_vary_interval_5flo(is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"FCT_VARY_INTERVAL{title_addendum}"
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(0,1)]

    minimum_interval_us = 0.1 # 0.1us
    total_flow_size_B = 200000 # 200KB
    # NOTE: smallest byteload size that SSIRD sim is set up to use is 4B => with headers this makes a total of 64B per byteload.
    # NOTE: byteload sizes are multiples of 4 so that the inter-byteload periods are later calculated to be whole numbers in the end

    byteload_size_B_list = [20, 20, 20, 20] 
    num_of_experiments = len(byteload_size_B_list)
    num_flows = 5
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
    # total_injection_period_us = max(num_byteloads_per_flow_list) * minimum_interval_us
    # logger.debug(f"Total injection period (us): {total_injection_period_us}")
    # inter_byteload_period_us_list = [] 
    # for num_byteloads in num_byteloads_per_flow_list:
    #     inter_byteload_period_us = total_injection_period_us / num_byteloads
    #     inter_byteload_period_us_list.append(inter_byteload_period_us)
    inter_byteload_period_us_list = [0.01, 0.1, 1, 10]
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

    ssird_sim_dur_list = [0.0015, 0.002, 0.02, 0.12]
    dctcp_sim_dur_list = [0.02, 0.02, 0.2, 0.3]
    assert(len(ssird_sim_dur_list) == num_of_experiments)
    assert(len(dctcp_sim_dur_list) == num_of_experiments)

    # TODO: currently only calculates theoretical gbps for in-parallel flows
    gdpt_gbps_theoretical_list = []
    for i in range(0, num_of_experiments):
        gdpt_gbps_theoretical = num_flows * (byteload_size_B_list[i]*8)/(inter_byteload_period_us_list[i]) * pow(10,-3)
        if byteload_size_B_list[i] < 4: gdpt_gbps_theoretical *= 4  # mirror treatment of hypersmall byteloads by r2p2-app.cc
        gdpt_gbps_theoretical_list.append(gdpt_gbps_theoretical)
    assert(len(gdpt_gbps_theoretical_list) == num_of_experiments)

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    # logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
    logger.info(f"Gdpt GBps theoretical: {gdpt_gbps_theoretical_list}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    # return

    exp_grp = dale_experiment_rig.ExperimentGroup(experiment_family, proto_names, src_dst_pairs_list, flow_start_times_us_list, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, ssird_sim_dur_list, dctcp_sim_dur_list, is_full_postproc, log_level, title_addendum)

    ssird_fct_list, dctcp_fct_list, gdpt_gbps_measured_list_ssird, gdpt_gbps_measured_list_dctcp, gdpt_gbps_measured_per_flow_list_list_ssird, gdpt_gbps_measured_per_flow_list_list_dctcp = exp_grp.perform_experiment()

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    # logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
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

def experiment_1458B_10us_1flo(is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"Normal_Byteloads{title_addendum}"
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(0,1)]

    minimum_interval_us = 10
    total_flow_size_B = 1458*5 # 5 bloads

    byteload_size_B_list = [1458] 
    num_of_experiments = len(byteload_size_B_list)
    num_flows = 1 
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

    ssird_sim_dur_list = [0.01] # for 1ms RTT
    dctcp_sim_dur_list = [0.0] 

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

    ssird_fct_list, dctcp_fct_list, gdpt_gbps_measured_list_ssird, gdpt_gbps_measured_list_dctcp, gdpt_gbps_measured_per_flow_list_list_ssird, gdpt_gbps_measured_per_flow_list_list_dctcp = exp_grp.perform_experiment()

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
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

def experiment_1462B_10us_xflo(num_flows=1, is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"Normal_Byteloads{title_addendum}"
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(0,1)]

    minimum_interval_us = 10
    total_flow_size_B = 1462 * 3 # 5 bloads

    byteload_size_B_list = [1462] 
    num_of_experiments = len(byteload_size_B_list)
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

    ssird_sim_dur_list = [0.01] # for 1ms RTT
    dctcp_sim_dur_list = [0.0]

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

    ssird_fct_list, dctcp_fct_list, gdpt_gbps_measured_list_ssird, gdpt_gbps_measured_list_dctcp, gdpt_gbps_measured_per_flow_list_list_ssird, gdpt_gbps_measured_per_flow_list_list_dctcp = exp_grp.perform_experiment()

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
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

def experiment_1462B_10us_xflo(num_flows=1, is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"Normal_Byteloads{title_addendum}"
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src_dst_pairs_list = [(0,1)]

    minimum_interval_us = 10
    total_flow_size_B = 1462 * 3 # 5 bloads

    byteload_size_B_list = [1462] 
    num_of_experiments = len(byteload_size_B_list)
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

    ssird_sim_dur_list = [0.01] # for 1ms RTT
    dctcp_sim_dur_list = [0.0]

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

    ssird_fct_list, dctcp_fct_list, gdpt_gbps_measured_list_ssird, gdpt_gbps_measured_list_dctcp, gdpt_gbps_measured_per_flow_list_list_ssird, gdpt_gbps_measured_per_flow_list_list_dctcp = exp_grp.perform_experiment()

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
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

if __name__ == "__main__":
    ### 1ms RTT experiments:
    experiment_vary_byteload_number_200KBflo_5flo(is_full_postproc=True, title_addendum="_vary_num_bload_5flo_1msRTT", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_vary_byteload_size_5flo(is_full_postproc=True, title_addendum="_vary_bload_size_5flo_1msRTT", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_vary_interval_5flo(is_full_postproc=True, title_addendum="_vary_interval_5flo_1msRTT", log_level=dale_experiment_rig.LOG_LEVEL_2)


    ''' Credit Leak Tests: '''
    # 5us RTT ---
    # experiment_1458B_10us_1flo(is_full_postproc=True, title_addendum="_1458B_1flo_credit_leak", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_1462B_10us_xflo(num_flows=1, is_full_postproc=False, title_addendum="_1462B_1flo_3bload_credit_leak_test", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_1462B_10us_xflo(num_flows=2, is_full_postproc=False, title_addendum="_1462B_2flo_3bload_credit_leak_test", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_1462B_10us_xflo(num_flows=5, is_full_postproc=False, title_addendum="_1462B_5flo_3bload_credit_leak_test", log_level=dale_experiment_rig.LOG_LEVEL_2)

    # 1ms RTT ---
    # experiment_1458B_10us_1flo(is_full_postproc=True, title_addendum="_1458B_1flo_credit_leak_1msRTT", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_1462B_10us_xflo(num_flows=1, is_full_postproc=True, title_addendum="_1462B_1flo_3bload_credit_leak_1msRTT_test", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_1462B_10us_xflo(num_flows=5, is_full_postproc=True, title_addendum="_1462B_5flo_3bload_credit_leak_1msRTT_test", log_level=dale_experiment_rig.LOG_LEVEL_2)
