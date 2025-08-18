import dale_experiment_rig
import dale_final_eval_experiments

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

    dale_final_eval_experiments.run_experiment(
        proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='4-hosts.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0)],
        num_flows_list=[10],
        byteload_size_B_list=[1458],
        target_mean_byteload_interval_nanosec_list=[1000],
        max_interval_nanosec_list=[10000],
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="DCTCP_MsgSizeDist.txt")],
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.01],
        dctcp_sim_dur_list=[0.01],
        xpass_sim_dur_list=[0.01],
        is_full_postproc=True,
        title_prefix="xpass_stresstest_",
        title_addendum="_4host_DctcpMsgSizeDist_loadtest",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 