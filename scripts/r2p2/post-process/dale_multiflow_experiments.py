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

if __name__ == "__main__":
    # multiflow_fct_gdpt_experiment_vary_byteloadsize(is_full_postproc=False, title_addendum="_multiflow")
    multiflow_fct_gdpt_experiment_vary_byteloadsize(is_full_postproc=False, title_addendum="_multiflow_test_16jul")