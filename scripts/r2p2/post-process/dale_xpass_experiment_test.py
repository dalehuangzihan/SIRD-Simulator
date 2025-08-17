import dale_experiment_rig
import dale_final_eval_experiments

if __name__ == "__main__":
    dale_final_eval_experiments.run_experiment(
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='10-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0)],
        num_flows_list=[1],
        byteload_size_B_list=[1458],
        target_mean_byteload_interval_nanosec_list=[100],
        flow_size_distr_list=[dale_experiment_rig.FixedDistr(10, 1458)]*1,
        target_mean_flow_interarr_ns=2000,
        is_use_poisson_byteload_intervals=False,
        is_use_poisson_flow_interarr=False,
        ssird_sim_dur_list=[0.01],
        dctcp_sim_dur_list=[0.01],
        xpass_sim_dur_list=[0.01],
        is_full_postproc=False,
        title_prefix="xpass_test",
        title_addendum="_1flo",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date="nodate"
    ) 