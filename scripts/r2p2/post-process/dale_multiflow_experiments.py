import dale_experiment_rig

logger = dale_experiment_rig.logging.getLogger(__name__)

def multiflow_fct_gdpt_experiment_vary_byteloadsize(is_full_postproc=True, title_addendum=""):
    log_level = dale_experiment_rig.LOG_LEVEL_2
    experiment_family = f"FCT_Vary_Byteload_Size{title_addendum}"
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    # proto_names = [SSIRD_PROTO_NAME]

    src = 0
    dst = 1
    num_byteloads_per_flow = 10
    inter_byteload_period_us = 100 # is 0.1ms
    num_flows = 2
    inter_flow_spacing_us = 0 # TODO: testing
    flow_start_times_us_list = [i * inter_flow_spacing_us for i in range(0, num_flows)]

    KILOBYTE = 1000
    # byteload_size_KB_list = [100/8]
    # byteload_size_KB_list = [10/8, 50/8, 100/8, 500/8, 1000/8] # 10/8KB to 1/8MB
    byteload_size_KB_list = [100/8, 500/8, 1000/8, 5000/8, 10000/8] # 100/8KB to 10/8MB
    byteload_size_B_list = [int(n * KILOBYTE) for n in byteload_size_KB_list] 
    num_of_experiments = len(byteload_size_B_list)

    num_byteloads_per_flow_list = [num_byteloads_per_flow] * num_of_experiments 
    inter_byteload_period_us_list = [inter_byteload_period_us] * num_of_experiments

    multiplication_factor = 2
    sim_dur_list = []
    for i in range(0, num_of_experiments):
        sim_dur_s = dale_experiment_rig.Experiment.get_sim_duration(num_flows, inter_flow_spacing_us, num_byteloads_per_flow, byteload_size_B_list[i], inter_byteload_period_us, multiplication_factor)
        sim_dur_list.append(sim_dur_s)
    ssird_sim_dur_list = sim_dur_list
    dctcp_sim_dur_list = sim_dur_list

    dale_experiment_rig.init_logs(experiment_family, f"{dale_experiment_rig.Experiment.get_experiment_name(num_flows, num_byteloads_per_flow, "variable_", inter_byteload_period_us)}{title_addendum}.log")

    gdpt_gbps_theoretical_parallel_flows = [num_flows * (bytes*8)/(inter_byteload_period_us * pow(10, -6) * pow(10, 9)) for bytes in byteload_size_B_list]

    logger.info(f"Num flows: {num_flows}")
    logger.debug(f"Flow start times (us): {flow_start_times_us_list}")
    logger.info(f"Time Period: {inter_byteload_period_us}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Load Gbps theoretical (parallel flows): {gdpt_gbps_theoretical_parallel_flows}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")

    exp_grp = dale_experiment_rig.ExperimentGroup(experiment_family, proto_names, src, dst, flow_start_times_us_list, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, ssird_sim_dur_list, dctcp_sim_dur_list, is_full_postproc, log_level, title_addendum)

    ssird_fct_list, dctcp_fct_list, gdpt_gbps_measured_list_ssird, gdpt_gbps_measured_list_dctcp, gdpt_gbps_measured_per_flow_list_list_ssird, gdpt_gbps_measured_per_flow_list_list_dctcp = exp_grp.perform_experiment()

    logger.info(f"Num flows: {num_flows}")
    logger.debug(f"Flow start times (us): {flow_start_times_us_list}")
    logger.info(f"Time Period: {inter_byteload_period_us}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"Sim duration (DCTCP): {dctcp_sim_dur_list}")
    logger.info(f"Gdpt Gbps theoretical: {gdpt_gbps_theoretical_parallel_flows}")
    logger.info(f"Gdpt Gbps measured (SSIRD): {gdpt_gbps_measured_list_ssird}")
    logger.info(f"Gdpt Gbps measured (DCTCP): {gdpt_gbps_measured_list_dctcp}")
    logger.debug(f"Gdpt Gbps measured per flow (SSIRD): {gdpt_gbps_measured_per_flow_list_list_ssird}")
    logger.debug(f"Gdpt Gbps measured per flow (DCTCP): {gdpt_gbps_measured_per_flow_list_list_dctcp}")
    logger.info(f"* SSIRD FCT: {ssird_fct_list}")
    logger.info(f"* DCTCP FCT: {dctcp_fct_list}")

    assert num_of_experiments == len(ssird_fct_list)
    assert num_of_experiments == len(dctcp_fct_list)

def experiment_vary_byteloadsize_multiflow(is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"FCT_Subpkt_Byteloads{title_addendum}"
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    # proto_names = [dale_fct_experiment.SSIRD_PROTO_NAME]

    src = 0
    dst = 1

    # minimum_interval_us = 1
    minimum_interval_us = 0.01
    total_flow_size_B = 1000000
    # NOTE: smallest byteload size that SSIRD sim is set up to use is 4B => with headers this makes a total of 64B per byteload.
    # NOTE: byteload sizes are multiples of 4 so that the inter-byteload periods are later calculated to be whole numbers in the end

    KILOBYTE = 1000
    # byteload_size_KB_list = [1000]
    byteload_size_KB_list = [10, 50, 100, 500, 1000] # 10KB to 1MB byteloads
    byteload_size_B_list = [int(n * KILOBYTE) for n in byteload_size_KB_list] 
    num_of_experiments = len(byteload_size_B_list)
    # num_flows = 300
    num_flows = 10 # TODO: for testing
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
        # # simulation can't handle sub-1us interval granularity
        # assert((inter_byteload_period_us*10)%10 == 0)
        inter_byteload_period_us_list.append(inter_byteload_period_us)
    logger.debug(f"Inter-Byteload Periods list: {inter_byteload_period_us_list}")
    assert(len(inter_byteload_period_us_list) == num_of_experiments)

    # calculate simulation durations for experiment
    multiplication_factor = 100
    sim_dur_list = []
    for i in range(0, len(num_byteloads_per_flow_list)):
       sim_dur_list.append(dale_experiment_rig.Experiment.get_sim_duration(num_flows, inter_flow_spacing_us, num_byteloads_per_flow_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i], multiplication_factor))
    logger.debug(f"Sim Durations list: {sim_dur_list}")
    assert(len(sim_dur_list) == num_of_experiments)
    ssird_sim_dur_list = sim_dur_list
    dctcp_sim_dur_list = sim_dur_list

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
    return

    exp_grp = dale_experiment_rig.ExperimentGroup(experiment_family, proto_names, src, dst, flow_start_times_us_list, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, ssird_sim_dur_list, dctcp_sim_dur_list, is_full_postproc, log_level, title_addendum)

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

def experiment_vary_byteloadsize_subpkt_multiflow(is_full_postproc=True, title_addendum="", log_level=dale_experiment_rig.LOG_LEVEL_2):
    experiment_family = f"FCT_Subpkt_Byteloads{title_addendum}"
    proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME, dale_experiment_rig.DCTCP_PROTO_NAME]
    # proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME]
    # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME]

    src = 0
    dst = 1

    minimum_interval_us = 0.01
    total_flow_size_B = 40000
    # NOTE: smallest byteload size that SSIRD sim is set up to use is 4B => with headers this makes a total of 64B per byteload.
    # NOTE: byteload sizes are multiples of 4 so that the inter-byteload periods are later calculated to be whole numbers in the end
    byteload_size_B_list = [4]
    # byteload_size_B_list = [4, 40, 400, 4000] 
    num_of_experiments = len(byteload_size_B_list)
    # num_flows = 300
    num_flows = 10 # TODO: for testing
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
        # # simulation can't handle sub-1us interval granularity
        # assert((inter_byteload_period_us*10)%10 == 0)
        inter_byteload_period_us_list.append(inter_byteload_period_us)
    logger.debug(f"Inter-Byteload Periods list: {inter_byteload_period_us_list}")
    assert(len(inter_byteload_period_us_list) == num_of_experiments)

    # calculate simulation durations for experiment
    ssird_sim_dur_multiplication_factor = 5
    ssird_sim_dur_list = []
    for i in range(0, len(num_byteloads_per_flow_list)):
       ssird_sim_dur_list.append(dale_experiment_rig.Experiment.get_sim_duration(num_flows, inter_flow_spacing_us, num_byteloads_per_flow_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i], ssird_sim_dur_multiplication_factor))
    logger.debug(f"Sim Durations list (SSIRD): {ssird_sim_dur_list}")
    assert(len(ssird_sim_dur_list) == num_of_experiments)
    
    # dctcp_sim_dur_multiplication_factor = 200
    # dctcp_sim_dur_list = []
    # for i in range(0, len(num_byteloads_per_flow_list)):
    #    dctcp_sim_dur_list.append(dale_experiment_rig.Experiment.get_sim_duration(num_flows, inter_flow_spacing_us, num_byteloads_per_flow_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i], dctcp_sim_dur_multiplication_factor))
    dctcp_sim_dur_list = [0.0130] * num_of_experiments
    logger.debug(f"Sim Durations list (DCTCP): {dctcp_sim_dur_list}")
    assert(len(dctcp_sim_dur_list) == num_of_experiments)

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

    exp_grp = dale_experiment_rig.ExperimentGroup(experiment_family, proto_names, src, dst, flow_start_times_us_list, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, ssird_sim_dur_list, dctcp_sim_dur_list, is_full_postproc, log_level, title_addendum)

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
    # multiflow_fct_gdpt_experiment_vary_byteloadsize(is_full_postproc=False, title_addendum="_multiflow")
    # multiflow_fct_gdpt_experiment_vary_byteloadsize(is_full_postproc=False, title_addendum="_multiflow_test_16jul")

    experiment_vary_byteloadsize_subpkt_multiflow(is_full_postproc=False, title_addendum="_subpkt_multiflow_17jul_test", log_level=dale_experiment_rig.LOG_LEVEL_2)

