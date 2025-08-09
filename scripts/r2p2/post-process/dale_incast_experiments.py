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
    dctcp_sim_dur_list = [0.04] * num_of_experiments # TODO: tweak

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

    exp_metrics = exp_grp.perform_experiment()

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows per Sendr/Recvr Pair: {num_flows_per_sr_pair}")
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

    exp_metrics = exp_grp.perform_experiment()

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_per_flow_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows per Sendr/Recvr Pair: {num_flows_per_sr_pair}")
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

if __name__ == "__main__":
    # experiment_incast_3_to_1_test(is_full_postproc=True, title_addendum="_3to1_incast_test_2flo_1conn", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_incast_3_to_1_test(is_full_postproc=True, title_addendum="_3to1_incast_31flo_1pt6GbpsFlo_25conn", log_level=dale_experiment_rig.LOG_LEVEL_2)
    experiment_incast_3_to_1_test(is_full_postproc=True, title_addendum="_3to1_incast_31flo_1pt6GbpsFlo_40conn", log_level=dale_experiment_rig.LOG_LEVEL_2)
    # experiment_incast_3to1_16GbpsFlo(is_full_postproc=True, title_addendum="_incast_3to1_5flo_16GbpsFlo_200KBflo_3conn", log_level=dale_experiment_rig.LOG_LEVEL_2)