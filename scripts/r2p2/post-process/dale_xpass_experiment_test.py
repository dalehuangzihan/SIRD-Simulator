from pathlib import Path
import dale_experiment_rig
import dale_final_eval_experiments

logger = dale_experiment_rig.logging.getLogger(__name__)

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

    saved_json_file_path = Path(dale_experiment_rig.FLOW_SPECS_JSON_PATH + saved_json_file)
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

    logger.debug(f"Flow size distr workload: {[distr.cdf_file_name for distr in flow_size_distr_list]}")

    src_dst_pairs_to_flowspecs_dict_list = [] # list of src_dst_pairs_to_flowspecs_dict objs, one per experiment
    all_flow_specs_list = [] # list of flow_spec objs across all src-dst pairs across all experiments
    src_dst_pairs_to_flow_start_times_us_dict_list = [] # list of src_dst_pairs_to_flow_start_times_us_dict objs, one per experiment

    src_dst_pairs_to_flowspecs_dict_list = dale_experiment_rig.FlowSpec.parse_src_dst_pairs_flowspec_dict_list_from_jsonfile(dale_experiment_rig.FLOW_SPECS_JSON_PATH, saved_json_file)
    for src_dst_pairs_to_flowspecs_dict in src_dst_pairs_to_flowspecs_dict_list: # iterating thru experiments
        # print(src_dst_pairs_to_flowspecs_dict)
        src_dst_pairs_to_flow_start_times_us_dict = {}
        for src_dst_pair in src_dst_pairs_list:
            src_dst_pair_key = (src_dst_pair[0], src_dst_pair[1])
            flow_spec_list, flow_start_times_us_list = src_dst_pairs_to_flowspecs_dict[src_dst_pair_key]
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


if __name__ == "__main__":
    # dale_final_eval_experiments.run_experiment(
    #     proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='4-hosts.yaml',
    #     src_dst_pairs_list=[(1,0)],
    #     num_flows_list=[2],
    #     byteload_size_B_list=[1458],
    #     target_mean_byteload_interval_nanosec_list=[10000],
    #     max_interval_nanosec_list=[10000],
    #     flow_size_distr_list=[dale_experiment_rig.FixedDistr(3, 1458)]*1,
    #     target_mean_flow_interarr_ns=0,
    #     is_use_poisson_byteload_intervals=False,
    #     is_use_poisson_flow_interarr=False,
    #     ssird_sim_dur_list=[0.001],
    #     dctcp_sim_dur_list=[0.001],
    #     xpass_sim_dur_list=[0.001],
    #     is_full_postproc=False,
    #     title_prefix="xpass_test_2",
    #     title_addendum="_1flo",
    #     log_level=dale_experiment_rig.LOG_LEVEL_6,
    #     experiment_date="nodate"
    # ) 

    # dale_final_eval_experiments.run_experiment(
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='4-hosts.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0)],
    #     num_flows_list=[10],
    #     byteload_size_B_list=[1458],
    #     target_mean_byteload_interval_nanosec_list=[1000],
    #     max_interval_nanosec_list=[10000],
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="DCTCP_MsgSizeDist.txt")],
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.01],
    #     dctcp_sim_dur_list=[0.01],
    #     xpass_sim_dur_list=[0.01],
    #     is_full_postproc=True,
    #     title_prefix="xpass_stresstest_",
    #     title_addendum="_4host_DctcpMsgSizeDist_loadtest",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 

    # dale_final_eval_experiments.run_experiment(
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='4-hosts.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0)],
    #     num_flows_list=[10],
    #     byteload_size_B_list=[1458],
    #     target_mean_byteload_interval_nanosec_list=[1000],
    #     max_interval_nanosec_list=[10000],
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")],
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.01],
    #     dctcp_sim_dur_list=[0.01],
    #     xpass_sim_dur_list=[0.01],
    #     is_full_postproc=True,
    #     title_prefix="xpass_stresstest_",
    #     title_addendum="_4host_fbHadoopDist_loadtest",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 

    dale_final_eval_experiments.run_experiment(
        proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='4-hosts.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0)],
        num_flows_list=[20],
        byteload_size_B_list=[1458],
        target_mean_byteload_interval_nanosec_list=[1000],
        max_interval_nanosec_list=[10000],
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Google_AllRPC.txt")],
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.005],
        dctcp_sim_dur_list=[0.005],
        xpass_sim_dur_list=[0.005],
        is_full_postproc=True,
        title_prefix="xpass_stresstest_",
        title_addendum="_4host_GoogleAllRPC_loadtest",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    # run_experiment_from_saved_json(
    #     saved_json_file="xpass_stresstest_3to1_4host_GoogleAllRPC_loadtest_2025-08-18T_14-32-25Z.json",
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='4-hosts.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0)],
    #     num_flows_list=[20],
    #     byteload_size_B_list=[1458],
    #     target_mean_byteload_interval_nanosec_list=[1000],
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Google_AllRPC.txt")],
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.01],
    #     dctcp_sim_dur_list=[0.01],
    #     xpass_sim_dur_list=[0.01],
    #     is_full_postproc=True,
    #     title_prefix="xpass_stresstest_",
    #     title_addendum="_4host_GoogleAllRPC_loadtest",
    #     log_level=dale_experiment_rig.LOG_LEVEL_6,
    #     experiment_date="2025-08-18T_14-32-25Z_redo_no_sub4_bloads"
    # ) 