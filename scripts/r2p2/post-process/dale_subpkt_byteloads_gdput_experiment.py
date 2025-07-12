import dale_fct_experiment
import dale_multiflow_serialiser
import logging

logger = logging.getLogger(__name__)

def init_logs(output_path):
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler(output_path, mode='w'),
            logging.StreamHandler()
        ]
    )

# def fct_vs_load_experiment_vary_byteloadsize_subpkt_test(is_full_postproc=True, title_addendum="_subpkt"):
#     experiment_name = f"FCT_Subpkt_Byteloads{title_addendum}"
#     proto_names = [dale_fct_experiment.SSIRD_PROTO_NAME, dale_fct_experiment.DCTCP_PROTO_NAME]
#     # proto_names = [dale_fct_experiment.SSIRD_PROTO_NAME]

#     src = 0
#     dst = 1

#     minimum_interval_us = 1
#     total_flow_size_B = 40000
#     # smallest byteload size that SSIRD sim is set up to use is 4B => with headers this makes a total of 64B per byteload.
#     # byteload_size_B_list = [4, 40000]
#     byteload_size_B_list = [4, 40, 400, 4000, 40000] # multiples of 4 so that the inter-byteload periods are later calculated to be whole numbers in the end
#     num_of_experiments = len(byteload_size_B_list)

#     dale_fct_experiment.init_logs(output_path=f"experiment_output/subpkt_experiment_{total_flow_size_B}B_total_{min(byteload_size_B_list)}B_to_{max(byteload_size_B_list)}B.log")

#     logging.debug(f"Total_flow_size_B: {total_flow_size_B}")
#     logging.debug(f"Byteload sizes list: {byteload_size_B_list}")

#     # calculate num of byteloads for experiment
#     num_byteloads_list = []
#     for size in byteload_size_B_list:
#         num_byteloads = None
#         if size < 4:
#             num_byteloads = total_flow_size_B // (4 * size)  # mirror treatment of hypersmall byteloads by r2p2-app.cc
#         else:
#             num_byteloads = total_flow_size_B // size
#         num_byteloads_list.append(num_byteloads)
#     logger.debug(f"Num Byteloads list: {num_byteloads_list}")
#     assert(len(num_byteloads_list) == num_of_experiments)

#     # calculate inter-byteload periods for experiment
#     total_injection_period_us = max(num_byteloads_list) * minimum_interval_us
#     logger.debug(f"Total injection period (us): {total_injection_period_us}")
#     inter_byteload_period_us_list = [] 
#     for num_byteloads in num_byteloads_list:
#         inter_byteload_period_us = total_injection_period_us / num_byteloads
#         # simulation can't handle sub-1us interval granularity
#         assert((inter_byteload_period_us*10)%10 == 0)
#         inter_byteload_period_us_list.append(int(inter_byteload_period_us))
#     logger.debug(f"Inter-Byteload Periods list: {inter_byteload_period_us_list}")
#     assert(len(inter_byteload_period_us_list) == num_of_experiments)

#     # calculate simulation durations for experiment
#     sim_dur_list = []
#     for i in range(0, len(num_byteloads_list)):
#         # TODO: change multiplier factor if sim duration not long enough
#        sim_dur_list.append(dale_fct_experiment.FctExperiment.get_sim_duration(num_byteloads_list[i], inter_byteload_period_us_list[i], 2))
#     logger.debug(f"Sim Durations list: {sim_dur_list}")
#     assert(len(sim_dur_list) == num_of_experiments)
#     ssird_sim_dur_list = sim_dur_list
#     dctcp_sim_dur_list = sim_dur_list

#     load_gbps_theoretical_list = []
#     for i in range(0, num_of_experiments):
#         load_gbps_theoretical = (byteload_size_B_list[i]*8)/(inter_byteload_period_us_list[i]*pow(10,-6)) * pow(10,-9)
#         if byteload_size_B_list[i] < 4: load_gbps_theoretical *= 4  # mirror treatment of hypersmall byteloads by r2p2-app.cc
#         load_gbps_theoretical_list.append(load_gbps_theoretical)
#     assert(len(load_gbps_theoretical_list) == num_of_experiments)

#     logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
#     logger.info(f"Total Injection Period (us): {total_injection_period_us}")
#     logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
#     logger.info(f"Num Byteloads: {num_byteloads}")
#     logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
#     logger.info(f"Load GBps theoretical: {load_gbps_theoretical_list}")
#     logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
#     logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")

#     ssird_fct_list = []
#     dctcp_fct_list = []
#     assert num_of_experiments == len(ssird_sim_dur_list)
#     assert num_of_experiments == len(dctcp_sim_dur_list)
#     # return

#     load_gbps_measured_list = []
#     for i in range(0, num_of_experiments):
#         fct_exp1 = dale_fct_experiment.FctExperiment(experiment_name, proto_names, src, dst, num_byteloads_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i], is_full_postproc, title_addendum=title_addendum) 
#         ssird_fct, dctcp_fct, load_gbps_measured = fct_exp1.execute(ssird_sim_dur=ssird_sim_dur_list[i], dctcp_sim_dur=dctcp_sim_dur_list[i]) 
#         ssird_fct_list.append(ssird_fct)
#         dctcp_fct_list.append(dctcp_fct)
#         load_gbps_measured_list.append(load_gbps_measured)

#     logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
#     logger.info(f"Total Injection Period (us): {total_injection_period_us}")
#     logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
#     logger.info(f"Num Byteloads: {num_byteloads}")
#     logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
#     logger.info(f"Load GBps theoretical: {load_gbps_theoretical_list}")
#     logger.info(f"Load Gbps measured: {load_gbps_measured_list}")
#     logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
#     logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
#     logger.info(f"* SSIRD FCT: {ssird_fct_list}")
#     logger.info(f"* DCTCP FCT: {dctcp_fct_list}")

#     assert num_of_experiments == len(ssird_fct_list)
#     assert num_of_experiments == len(dctcp_fct_list)

def fct_vs_thrpt_experiment_vary_byteloadsize_subpkt_multiflow(is_capture_output=True, is_full_postproc=True, title_addendum="_subpkt_multiflow"):
    experiment_family = f"FCT_Subpkt_Byteloads{title_addendum}"
    proto_names = [dale_fct_experiment.SSIRD_PROTO_NAME, dale_fct_experiment.DCTCP_PROTO_NAME]
    # proto_names = [dale_fct_experiment.SSIRD_PROTO_NAME]

    src = 0
    dst = 1

    minimum_interval_us = 1
    total_flow_size_B = 40000
    # NOTE: smallest byteload size that SSIRD sim is set up to use is 4B => with headers this makes a total of 64B per byteload.
    # NOTE: byteload sizes are multiples of 4 so that the inter-byteload periods are later calculated to be whole numbers in the end
    # byteload_size_B_list = [4]
    byteload_size_B_list = [4, 40, 400, 4000] 
    num_of_experiments = len(byteload_size_B_list)
    # num_flows = 300
    num_flows = 5 # currently 5 flows causes thinkpad to run out of ram (32GB)
    inter_flow_spacing_us = 1
    flow_start_times_us_list = [i * inter_flow_spacing_us for i in range(0, num_flows)]
    # flow_start_times_us_list = [0, 1]

    dale_multiflow_serialiser.init_logs(output_path=f"experiment_output/subpkt_experiment_{num_flows}flo_{total_flow_size_B}B_total_{min(byteload_size_B_list)}B_to_{max(byteload_size_B_list)}B.log")

    logging.debug(f"Total_flow_size_B: {total_flow_size_B}")
    logging.debug(f"Byteload sizes list: {byteload_size_B_list}")
    logging.debug(f"Num Flows: {num_flows}")
    logging.debug(f"Inter-flow spacing (us): {inter_flow_spacing_us}")
    logging.debug(f"Flow start times (us): {flow_start_times_us_list}")

    # calculate num of byteloads for experiment
    num_byteloads_list = []
    for size in byteload_size_B_list:
        num_byteloads = None
        if size < 4:
            num_byteloads = total_flow_size_B // (4 * size)  # mirror treatment of hypersmall byteloads by r2p2-app.cc
        else:
            num_byteloads = total_flow_size_B // size
        num_byteloads_list.append(num_byteloads)
    logger.debug(f"Num Byteloads list: {num_byteloads_list}")
    assert(len(num_byteloads_list) == num_of_experiments)

    # calculate inter-byteload periods for experiment
    total_injection_period_us = max(num_byteloads_list) * minimum_interval_us
    logger.debug(f"Total injection period (us): {total_injection_period_us}")
    inter_byteload_period_us_list = [] 
    for num_byteloads in num_byteloads_list:
        inter_byteload_period_us = total_injection_period_us / num_byteloads
        # simulation can't handle sub-1us interval granularity
        assert((inter_byteload_period_us*10)%10 == 0)
        inter_byteload_period_us_list.append(int(inter_byteload_period_us))
    logger.debug(f"Inter-Byteload Periods list: {inter_byteload_period_us_list}")
    assert(len(inter_byteload_period_us_list) == num_of_experiments)

    # calculate simulation durations for experiment
    sim_dur_list = []
    for i in range(0, len(num_byteloads_list)):
        # TODO: change multiplier factor if sim duration not long enough
       sim_dur_list.append(dale_multiflow_serialiser.MultiFlowExperiment.get_sim_duration(num_byteloads_list[i], inter_byteload_period_us_list[i], num_flows * 2))
    logger.debug(f"Sim Durations list: {sim_dur_list}")
    assert(len(sim_dur_list) == num_of_experiments)
    ssird_sim_dur_list = sim_dur_list
    dctcp_sim_dur_list = sim_dur_list

    # TODO: currently only calculates theoretical gbps for in-parallel flows
    thrpt_gbps_theoretical_list = []
    for i in range(0, num_of_experiments):
        thrpt_gbps_theoretical = num_flows * (byteload_size_B_list[i]*8)/(inter_byteload_period_us_list[i]*pow(10,-6)) * pow(10,-9)
        if byteload_size_B_list[i] < 4: thrpt_gbps_theoretical *= 4  # mirror treatment of hypersmall byteloads by r2p2-app.cc
        thrpt_gbps_theoretical_list.append(thrpt_gbps_theoretical)
    assert(len(thrpt_gbps_theoretical_list) == num_of_experiments)

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads_list}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
    logger.info(f"Thrpt GBps theoretical: {thrpt_gbps_theoretical_list}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")

    ssird_fct_list = []
    dctcp_fct_list = []
    assert num_of_experiments == len(ssird_sim_dur_list)
    assert num_of_experiments == len(dctcp_sim_dur_list)
    # return

    thrpt_gbps_measured_list_ssird = []
    thrpt_gbps_measured_list_dctcp = []
    thrpt_gbps_measured_per_flow_list_list_ssird = []
    thrpt_gbps_measured_per_flow_list_list_dctcp = []
    for i in range(0, num_of_experiments):
        experiment_name = dale_multiflow_serialiser.MultiFlowExperiment.get_experiment_name(num_flows, num_byteloads, byteload_size_B_list[i], inter_byteload_period_us_list[i]) + title_addendum
        fct_exp1 = dale_multiflow_serialiser.MultiFlowExperiment(experiment_family, experiment_name, proto_names, src, dst, flow_start_times_us_list, num_byteloads_list[i], byteload_size_B_list[i], inter_byteload_period_us_list[i], is_full_postproc) 
        results = fct_exp1.execute(ssird_sim_dur=ssird_sim_dur_list[i], dctcp_sim_dur=dctcp_sim_dur_list[i], is_capture_output=is_capture_output) 
        ssird_fct_list.append(results.ssird_fct)
        dctcp_fct_list.append(results.dctcp_fct)
        thrpt_gbps_measured_list_ssird.append(results.thrpt_gbps_measured_ssird)
        thrpt_gbps_measured_list_dctcp.append(results.thrpt_gbps_measured_dctcp)
        thrpt_gbps_measured_per_flow_list_list_ssird.append(results.thrpt_gbps_measured_per_flow_list_ssird)
        thrpt_gbps_measured_per_flow_list_list_dctcp.append(results.thrpt_gbps_measured_per_flow_list_dctcp)

    logger.info(f"Total Flow Size (Bytes): {total_flow_size_B}")
    logger.info(f"Total Injection Period (us): {total_injection_period_us}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Num Byteloads: {num_byteloads}")
    logger.info(f"Intervals (us): {inter_byteload_period_us_list}")
    logger.info(f"Num flows: {num_flows}")
    logger.debug(f"Flow start times (us): {flow_start_times_us_list}")
    logger.info(f"Thrpt Gbps theoretical: {thrpt_gbps_theoretical_list}")
    logger.info(f"Thrpt Gbps measured (SSIRD): {thrpt_gbps_measured_list_ssird}")
    logger.info(f"Thrpt Gbps measured (DCTCP): {thrpt_gbps_measured_list_dctcp}")
    logger.debug(f"Thrpt Gbps measured per flow (SSIRD): {thrpt_gbps_measured_per_flow_list_list_ssird}")
    logger.debug(f"Thrpt Gbps measured per flow (DCTCP): {thrpt_gbps_measured_per_flow_list_list_dctcp}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")
    logger.info(f"* SSIRD FCT: {ssird_fct_list}")
    logger.info(f"* DCTCP FCT: {dctcp_fct_list}")

    assert num_of_experiments == len(ssird_fct_list)
    assert num_of_experiments == len(dctcp_fct_list)

if __name__ == "__main__":
    # fct_vs_load_experiment_vary_byteloadsize_subpkt_test(is_full_postproc=True)
    fct_vs_thrpt_experiment_vary_byteloadsize_subpkt_multiflow(is_capture_output=True, is_full_postproc=False)

    # INFO:__main__:Total Flow Size (Bytes): 40000
    # INFO:__main__:Total Injection Period (us): 10000
    # INFO:__main__:Byteload Size (Bytes): [4, 40, 400, 4000, 40000]
    # INFO:__main__:Num Byteloads: 1
    # INFO:__main__:Intervals (us): [1, 10, 100, 1000, 10000]
    # INFO:__main__:Load GBps theoretical: [0.032, 0.03200000000000001, 0.03200000000000001, 0.032, 0.032]
    # INFO:__main__:Load Gbps measured: [0.03199999999999589, 0.03199999999999826, 0.031999999999999175, 0.03199999999999642, 0.032]
    # INFO:__main__:* Sim duration (SSIRD): [0.02, 0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* Sim duration (DCTCP): [0.02, 0.02, 0.02, 0.02, 0.02]
    # INFO:__main__:* SSIRD FCT: [0.010001574000000346, 0.009997559000000322, 0.009907617000001423, 0.009008002000001625, 1.1102000000207113e-05]
    # INFO:__main__:* DCTCP FCT: [0.010001513000000628, 0.009992519000000755, 0.009902575999999996, 0.00900296200000028, 5.998000000673187e-06]
    # NOTE: FCT decreases as byteload size increases because of the "final byteload transmission race" effect, where whichever setup transfers the last byteload fastest has the shortest FCT. Of course, the flow with only 1 byteload (albeit large) wins. 