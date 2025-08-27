from pathlib import Path

import dale_experiment_rig
import dale_final_eval_experiments

logger = dale_experiment_rig.logging.getLogger(__name__)


''' 
    ========== INCAST EXPERIMENTS (LOAD TEST): ==========
'''

def incast_10to1_1458B_fbHadoopDist_loadtest():
    # # new fine-grained experiment
    # run_experiment(
    #     proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 15, 20, 24, 26, 28, 30, 25, 40],
    #     byteload_size_B_list=[1458]*11,
    #     target_mean_byteload_interval_nanosec_list=[600]*11,
    #     max_interval_nanosec_list=[10000]*11,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*11,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.01]*11,
    #     dctcp_sim_dur_list=[0.01]*11,
    #     xpass_sim_dur_list=[0.01]*11,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_",
    #     title_addendum="_12host_fbHadoopDist_loadtest_300ns",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # print("12host_fbHadoopDist_loadtest")

    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # FE policy probe:
    # factor = 1
    factor = 3
    dale_final_eval_experiments.run_experiment(
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 15, 20, 24, 26, 28, 30, 25, 40],
        # byteload_size_B_list=[1458]*11,
        byteload_size_B_list=[ 1458 * factor ]*11,
        # target_mean_byteload_interval_nanosec_list=[600]*11,
        target_mean_byteload_interval_nanosec_list=[ 600 * factor ]*11,
        max_interval_nanosec_list=[10000]*11,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*11,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.01]*11,
        dctcp_sim_dur_list=[0.01]*11,
        xpass_sim_dur_list=[0.01]*11,
        is_full_postproc=False,
        title_prefix="FE_policy_PROBE_",
        title_addendum=f"_12host_fbHadoopDist_600x{factor}ns_1458Bx{factor}",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 

    # # FACTOR = 2
    # dale_final_eval_experiments.run_experiment_from_saved_json(
    #     saved_json_file="FE_policy_PROBE_10to1_12host_fbHadoopDist_600ns_1458Bx2_2025-08-27T_18-34-59Z.json",
    #     proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 15, 20, 24, 26, 28, 30, 25, 40],
    #     # byteload_size_B_list=[1458]*11,
    #     byteload_size_B_list=[ 1458 * 2 ]*11,
    #     # target_mean_byteload_interval_nanosec_list=[600]*11,
    #     target_mean_byteload_interval_nanosec_list=[ 600 * 2 ]*11,
    #     # max_interval_nanosec_list=[10000]*11,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*11,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.007]*11,
    #     dctcp_sim_dur_list=[0.007]*11,
    #     xpass_sim_dur_list=[0.007]*11,
    #     is_full_postproc=False,
    #     title_prefix="FE_policy_PROBE_",
    #     title_addendum=f"_12host_fbHadoopDist_600x{2}ns_1458Bx{2}",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    print(f"12host_fbHadoopDist_loadtest, factor={factor}\n\n")

def incast_10to1_1458B_fbCacheFollowerDist_loadtest():
    # # new fine-grained experiment
    # run_experiment(
    #     # proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 14, 17, 20, 25, 30, 40],
    #     byteload_size_B_list=[1458]*9,
    #     target_mean_byteload_interval_nanosec_list=[5000]*9,
    #     max_interval_nanosec_list=[10000]*9,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_CacheFollowerDist_IntraCluster.txt")]*9,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.1]*9,
    #     dctcp_sim_dur_list=[0.1]*9,
    #     xpass_sim_dur_list=[0.1]*9,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_",
    #     title_addendum="_12host_fbCacheFollowerDist_loadtest_5000ns_1to40flo",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 

    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # FE Policy Probe:
    # factor = 1
    factor = 3
    dale_final_eval_experiments.run_experiment(
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 14, 17, 20, 25, 30, 40],
        byteload_size_B_list=[ 1458 * factor ]*9,
        target_mean_byteload_interval_nanosec_list=[ 5000 * factor ]*9,
        max_interval_nanosec_list=[ 30000 ]*9,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_CacheFollowerDist_IntraCluster.txt")]*9,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.1]*9,
        dctcp_sim_dur_list=[0.1]*9,
        xpass_sim_dur_list=[0.1]*9,
        is_full_postproc=False,
        title_prefix="FE_policy_PROBE_",
        title_addendum=f"_12host_fbCacheFollowerDist_loadtest_5000nsx{factor}_1458Bx{factor}_1to40flo",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print(f"12host_fbCacheFollowerDist_loadtest, factor={factor}\n")

def incast_5to1_1458B_dctcpMsgSizeDistActual_loadtest():
    # assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # run_experiment_from_saved_json(
    #     saved_json_file="FE_incast_12host_5to1_6host_DctcpMsgSizeDistActual_loadtest_1Kns_2025-08-25T_20-37-43Z.json",
    #     proto_names = [dale_experiment_rig.DCTCP_PROTO_NAME, dale_experiment_rig.XPASS_PROTO_NAME],
    #     # topo_yaml_file='12-hosts-dumbbell.yaml',
    #     topo_yaml_file='6-hosts-dumbbell.yaml',
    #     # src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
    #     num_flows_list=[1, 5, 10, 15, 20, 25, 30],
    #     byteload_size_B_list=[1458]*7,
    #     target_mean_byteload_interval_nanosec_list=[1000]*7,
    #     flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*7,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.07]*7,
    #     dctcp_sim_dur_list=[0.07]*7,
    #     xpass_sim_dur_list=[0.07]*7,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_",
    #     title_addendum="_6host_DctcpMsgSizeDistActual_loadtest_1Kns_retry",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # FE Policy Probe:
    # factor = 1
    factor = 3
    dale_final_eval_experiments.run_experiment(
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        # topo_yaml_file='12-hosts-dumbbell.yaml',
        topo_yaml_file='6-hosts-dumbbell.yaml',
        # src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
        num_flows_list=[1, 4, 8, 11, 12, 13, 15, 17, 20, 25],
        byteload_size_B_list=[ 1458 * factor ]*10,
        target_mean_byteload_interval_nanosec_list=[ 1000 * factor ]*10,
        flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*10,
        target_mean_flow_interarr_ns=1000,
        max_interval_nanosec_list=[20000]*10,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.07]*10,
        dctcp_sim_dur_list=[0.07]*10,
        xpass_sim_dur_list=[0.07]*10,
        is_full_postproc=False,
        title_prefix="FE_policy_PROBE_",
        title_addendum=f"_6host_DctcpMsgSizeDistActual_loadtest_1Knsx{factor}_1458Bx{factor}",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_policy_PROBE_"+f"_6host_DctcpMsgSizeDistActual_loadtest_1Knsx{factor}_1458Bx{factor}")

def incast_10to1_1458B_dctcpMsgSizeDistActual_loadtest():
    # assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # run_experiment(
    #     proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     # topo_yaml_file='6-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     # src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
    #     num_flows_list=[1, 5, 8, 12, 14, 16, 18, 20, 25, 30],
    #     byteload_size_B_list=[1458]*10,
    #     target_mean_byteload_interval_nanosec_list=[2000]*10,
    #     max_interval_nanosec_list=[20000]*10,
    #     flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*10,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.1]*10,
    #     dctcp_sim_dur_list=[0.1]*10,
    #     xpass_sim_dur_list=[0.1]*10,
    #     is_full_postproc=True,
    #     title_prefix="FE_incast_12host_",
    #     title_addendum="_12host_DctcpMsgSizeDistActual_loadtest_2Kns",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # print("12host_dctcpMsgSizeDistActual_loadtest")
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # FE Policy Probe:
    # factor = 1
    factor = 3
    dale_final_eval_experiments.run_experiment(
        proto_names = [dale_experiment_rig.XPASS_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 8, 12, 14, 16, 18, 20, 25, 30],
        byteload_size_B_list=[ 1458 * factor ]*10,
        target_mean_byteload_interval_nanosec_list=[ 2000 * factor ]*10,
        max_interval_nanosec_list=[20000]*10,
        flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*10,
        target_mean_flow_interarr_ns=1000,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.1]*10,
        dctcp_sim_dur_list=[0.1]*10,
        xpass_sim_dur_list=[0.1]*10,
        is_full_postproc=True,
        title_prefix="FE_policy_PROBE_",
        title_addendum=f"_12host_DctcpMsgSizeDistActual_loadtest_2Knsx{factor}_1458Bx{factor}",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_policy_PROBE_" + f"_12host_DctcpMsgSizeDistActual_loadtest_2Knsx{factor}_1458Bx{factor}")


''' 
    ========== INCAST EXPERIMENTS (FULL LOAD SWEEP): ==========
'''
def incast_10to1_1458B_fbHadoopDist_load_fullsweep():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # # FACTOR = 2
    # dale_final_eval_experiments.run_experiment_from_saved_json(
    #     saved_json_file="FE_policy_PROBE_10to1_12host_fbHadoopDist_600ns_1458Bx2_2025-08-27T_18-34-59Z.json",
    #     proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 15, 20, 24, 26, 28, 30, 25, 40],
    #     byteload_size_B_list=[ 1458 * 2 ]*11,
    #     target_mean_byteload_interval_nanosec_list=[ 600 * 2 ]*11,
    #     # max_interval_nanosec_list=[10000]*11,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*11,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.007]*11,
    #     dctcp_sim_dur_list=[0.007]*11,
    #     xpass_sim_dur_list=[0.007]*11,
    #     is_full_postproc=True,
    #     title_prefix="FE_policy_ssird_bload_",
    #     title_addendum=f"_12host_fbHadoopDist_600x{2}ns_1458Bx{2}_srpt",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # print("FE_policy_ssird_bload_"+f"_12host_fbHadoopDist_600x{2}ns_1458Bx{2}_srpt")
    # FACTOR = 3
    dale_final_eval_experiments.run_experiment_from_saved_json(
        saved_json_file="FE_policy_PROBE_10to1_12host_fbHadoopDist_600x3ns_1458Bx3_2025-08-27T_19-08-50Z.json",
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 15, 20, 24, 26, 28, 30, 25, 40],
        byteload_size_B_list=[ 1458 * 3 ]*11,
        target_mean_byteload_interval_nanosec_list=[ 600 * 3 ]*11,
        # max_interval_nanosec_list=[10000]*11,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*11,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.007]*11,
        dctcp_sim_dur_list=[0.007]*11,
        xpass_sim_dur_list=[0.007]*11,
        is_full_postproc=True,
        title_prefix="FE_policy_ssird_bload_",
        title_addendum=f"_12host_fbHadoopDist_600x{3}ns_1458Bx{3}_srpt",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_policy_ssird_bload_"+f"_12host_fbHadoopDist_600x{3}ns_1458Bx{3}_srpt")

def incast_10to1_1458B_fbCacheFollowerDist_load_fullsweep():
    ''' USE THIS WORKLOAD DISTRIBUTION & FLOWSPEC FILE! '''
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # # FACTOR = 2
    # dale_final_eval_experiments.run_experiment_from_saved_json(
    #     saved_json_file="FE_policy_PROBE_10to1_12host_fbCacheFollowerDist_loadtest_5000nsx2_1458Bx2_1to40flo_2025-08-27T_19-38-32Z.json",
    #     proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 14, 17, 20, 25, 30, 40],
    #     byteload_size_B_list=[ 1458 * 2 ]*9,
    #     target_mean_byteload_interval_nanosec_list=[ 5000 * 2 ]*9,
    #     max_interval_nanosec_list=[ 30000 ]*9,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_CacheFollowerDist_IntraCluster.txt")]*9,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.05]*9,
    #     dctcp_sim_dur_list=[0.05]*9,
    #     xpass_sim_dur_list=[0.05]*9,
    #     is_full_postproc=True,
    #     title_prefix="FE_policy_ssird_",
    #     title_addendum=f"_12host_fbCacheFollowerDist_loadtest_5000nsx{2}_1458Bx{2}_1to40flo_srpt",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # print("FE_policy_ssird_" + f"_12host_fbCacheFollowerDist_loadtest_5000nsx{2}_1458Bx{2}_1to40flo_srpt")

def incast_5to1_1458B_dctcpMsgSizeDistActual_load_fullsweep():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # # FACTOR = 2
    # dale_final_eval_experiments.run_experiment_from_saved_json(
    #     saved_json_file="FE_policy_PROBE_5to1_6host_DctcpMsgSizeDistActual_loadtest_1Knsx2_1458Bx2_2025-08-27T_19-48-33Z.json",
    #     proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
    #     topo_yaml_file='6-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
    #     num_flows_list=[1, 4, 8, 11, 12, 13, 15, 17, 20, 25],
    #     byteload_size_B_list=[ 1458 * 2 ]*10,
    #     target_mean_byteload_interval_nanosec_list=[ 1000 * 2 ]*10,
    #     flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*10,
    #     target_mean_flow_interarr_ns=1000,
    #     # max_interval_nanosec_list=[20000]*10,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.055]*10,
    #     dctcp_sim_dur_list=[0.055]*10,
    #     xpass_sim_dur_list=[0.055]*10,
    #     is_full_postproc=True,
    #     title_prefix="FE_policy_ssird_",
    #     title_addendum=f"_6host_DctcpMsgSizeDistActual_loadtest_1Knsx{2}_1458Bx{2}_srpt",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # print("FE_policy_ssird_"+f"_6host_DctcpMsgSizeDistActual_loadtest_1Knsx{2}_1458Bx{2}_srpt")
    # FACTOR = 3
    dale_final_eval_experiments.run_experiment_from_saved_json(
        saved_json_file="FE_policy_PROBE_5to1_6host_DctcpMsgSizeDistActual_loadtest_1Knsx3_1458Bx3_2025-08-27T_20-22-11Z.json",
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='6-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
        num_flows_list=[1, 4, 8, 11, 12, 13, 15, 17, 20, 25],
        byteload_size_B_list=[ 1458 * 3 ]*10,
        target_mean_byteload_interval_nanosec_list=[ 1000 * 3 ]*10,
        flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*10,
        target_mean_flow_interarr_ns=1000,
        max_interval_nanosec_list=[20000]*10,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.05]*10,
        dctcp_sim_dur_list=[0.05]*10,
        xpass_sim_dur_list=[0.05]*10,
        is_full_postproc=True,
        title_prefix="FE_policy_ssird_",
        title_addendum=f"_6host_DctcpMsgSizeDistActual_loadtest_1Knsx{3}_1458Bx{3}_srpt",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_policy_ssird_" + f"_6host_DctcpMsgSizeDistActual_loadtest_1Knsx{3}_1458Bx{3}_srpt")

def incast_10to1_1458B_dctcpMsgSizeDistActual_load_fullsweep():
    ''' USE THIS WORKLOAD DISTRIBUTION & FLOWSPEC FILE! '''
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.SRPT)
    # # FACTOR = 2
    # dale_final_eval_experiments.run_experiment_from_saved_json(
    #     saved_json_file="FE_policy_PROBE_10to1_12host_DctcpMsgSizeDistActual_loadtest_2Knsx2_1458Bx2_2025-08-27T_19-44-21Z.json",
    #     proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 8, 12, 14, 16, 18, 20, 25, 30],
    #     byteload_size_B_list=[ 1458 * 2 ]*10,
    #     target_mean_byteload_interval_nanosec_list=[ 2000 * 2 ]*10,
    #     max_interval_nanosec_list=[20000]*10,
    #     flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*10,
    #     target_mean_flow_interarr_ns=1000,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.09]*10,
    #     dctcp_sim_dur_list=[0.09]*10,
    #     xpass_sim_dur_list=[0.09]*10,
    #     is_full_postproc=True,
    #     title_prefix="FE_policy_ssird_",
    #     title_addendum=f"_12host_DctcpMsgSizeDistActual_loadtest_2Knsx{2}_1458Bx{2}_srpt",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # print("FE_policy_ssird_"+f"_12host_DctcpMsgSizeDistActual_loadtest_2Knsx{2}_1458Bx{2}_srpt")

''' 
    ========== INCAST SSIRD FAIRSHARE POLICY EXPERIMENTS (FULL LOAD SWEEP): ==========
'''

def incast_10to1_1458B_fbHadoopDist_load_fullsweep_ssird_policy_fairshare():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.FAIRSHARE)
    # # FACTOR = 2
    # dale_final_eval_experiments.run_experiment_from_saved_json(
    #     saved_json_file="FE_policy_PROBE_10to1_12host_fbHadoopDist_600ns_1458Bx2_2025-08-27T_18-34-59Z.json",
    #     proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
    #     topo_yaml_file='12-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
    #     num_flows_list=[1, 5, 10, 15, 20, 24, 26, 28, 30, 25, 40],
    #     byteload_size_B_list=[ 1458 * 2 ]*11,
    #     target_mean_byteload_interval_nanosec_list=[ 600 * 2 ]*11,
    #     # max_interval_nanosec_list=[10000]*11,
    #     flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*11,
    #     target_mean_flow_interarr_ns=500,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.007]*11,
    #     dctcp_sim_dur_list=[0.007]*11,
    #     xpass_sim_dur_list=[0.007]*11,
    #     is_full_postproc=True,
    #     title_prefix="FE_policy_ssird_",
    #     title_addendum=f"_12host_fbHadoopDist_600x{2}ns_1458Bx{2}_fairshare",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # print("FE_policy_srpt_"+f"_12host_fbHadoopDist_600x{2}ns_1458Bx{2}_fairshare")
    # FACTOR = 3
    dale_final_eval_experiments.run_experiment_from_saved_json(
        saved_json_file="FE_policy_PROBE_10to1_12host_fbHadoopDist_600x3ns_1458Bx3_2025-08-27T_19-08-50Z.json",
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='12-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0), (6,0), (7,0), (8,0), (9,0), (10,0)],
        num_flows_list=[1, 5, 10, 15, 20, 24, 26, 28, 30, 25, 40],
        byteload_size_B_list=[ 1458 * 3 ]*11,
        target_mean_byteload_interval_nanosec_list=[ 600 * 3 ]*11,
        # max_interval_nanosec_list=[10000]*11,
        flow_size_distr_list=[dale_experiment_rig.WxDistr(cdf_file_name="Facebook_HadoopDist_All.txt")]*11,
        target_mean_flow_interarr_ns=500,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.007]*11,
        dctcp_sim_dur_list=[0.007]*11,
        xpass_sim_dur_list=[0.007]*11,
        is_full_postproc=True,
        title_prefix="FE_policy_ssird_",
        title_addendum=f"_12host_fbHadoopDist_600x{3}ns_1458Bx{3}_fairshare",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_policy_srpt_"+f"_12host_fbHadoopDist_600x{3}ns_1458Bx{3}_fairshare")

def incast_10to1_1458B_fbCacheFollowerDist_load_fullsweep_ssird_policy_fairshare():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.FAIRSHARE)
    # TODO

def incast_5to1_1458B_dctcpMsgSizeDistActual_load_fullsweep_ssird_policy_fairshare():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.FAIRSHARE)
    # # FACTOR = 2
    # dale_final_eval_experiments.run_experiment_from_saved_json(
    #     saved_json_file="FE_policy_PROBE_5to1_6host_DctcpMsgSizeDistActual_loadtest_1Knsx2_1458Bx2_2025-08-27T_19-48-33Z.json",
    #     proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
    #     topo_yaml_file='6-hosts-dumbbell.yaml',
    #     src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
    #     num_flows_list=[1, 4, 8, 11, 12, 13, 15, 17, 20, 25],
    #     byteload_size_B_list=[ 1458 * 2 ]*10,
    #     target_mean_byteload_interval_nanosec_list=[ 1000 * 2 ]*10,
    #     flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*10,
    #     target_mean_flow_interarr_ns=1000,
    #     # max_interval_nanosec_list=[20000]*10,
    #     is_use_poisson_byteload_intervals=True,
    #     is_use_poisson_flow_interarr=True,
    #     ssird_sim_dur_list=[0.055]*10,
    #     dctcp_sim_dur_list=[0.055]*10,
    #     xpass_sim_dur_list=[0.055]*10,
    #     is_full_postproc=True,
    #     title_prefix="FE_policy_ssird_",
    #     title_addendum=f"_6host_DctcpMsgSizeDistActual_loadtest_1Knsx{2}_1458Bx{2}_fairshare",
    #     log_level=dale_experiment_rig.LOG_LEVEL_2,
    #     experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    # ) 
    # print("FE_policy_ssird_"+f"_6host_DctcpMsgSizeDistActual_loadtest_1Knsx{2}_1458Bx{2}_fairshare")
    # FACTOR = 3
    dale_final_eval_experiments.run_experiment_from_saved_json(
        saved_json_file="FE_policy_PROBE_5to1_6host_DctcpMsgSizeDistActual_loadtest_1Knsx3_1458Bx3_2025-08-27T_20-22-11Z.json",
        proto_names = [dale_experiment_rig.SSIRD_PROTO_NAME],
        topo_yaml_file='6-hosts-dumbbell.yaml',
        src_dst_pairs_list=[(1,0), (2,0), (3,0), (4,0), (5,0)],
        num_flows_list=[1, 4, 8, 11, 12, 13, 15, 17, 20, 25],
        byteload_size_B_list=[ 1458 * 3 ]*10,
        target_mean_byteload_interval_nanosec_list=[ 1000 * 3 ]*10,
        flow_size_distr_list=[dale_experiment_rig.W5Distr_DctcpMsgSizeDistActual()]*10,
        target_mean_flow_interarr_ns=1000,
        max_interval_nanosec_list=[20000]*10,
        is_use_poisson_byteload_intervals=True,
        is_use_poisson_flow_interarr=True,
        ssird_sim_dur_list=[0.05]*10,
        dctcp_sim_dur_list=[0.05]*10,
        xpass_sim_dur_list=[0.05]*10,
        is_full_postproc=True,
        title_prefix="FE_policy_ssird_",
        title_addendum=f"_6host_DctcpMsgSizeDistActual_loadtest_1Knsx{3}_1458Bx{3}_fairshare",
        log_level=dale_experiment_rig.LOG_LEVEL_2,
        experiment_date=dale_experiment_rig.Experiment.get_date_now_formatted()
    ) 
    print("FE_policy_ssird_" + f"_6host_DctcpMsgSizeDistActual_loadtest_1Knsx{3}_1458Bx{3}_fairshare")

def incast_10to1_1458B_dctcpMsgSizeDistActual_load_fullsweep_ssird_policy_fairshare():
    assert(dale_experiment_rig.SSIRD_POLICY == dale_experiment_rig.FAIRSHARE)
    # TODO

if __name__ == "__main__":

    ''' FINAL EXPERIMENTS (LOAD TEST) '''
    # incast_10to1_1458B_fbHadoopDist_loadtest()
    incast_10to1_1458B_fbCacheFollowerDist_loadtest()
    # incast_5to1_1458B_dctcpMsgSizeDistActual_loadtest()
    # incast_10to1_1458B_dctcpMsgSizeDistActual_loadtest()


    ''' FINAL EXPERIMENTS (FULL LOAD SWEEP) '''
    # incast_5to1_1458B_dctcpMsgSizeDistActual_load_fullsweep()

    # assert(False)
    # incast_10to1_1458B_fbHadoopDist_load_fullsweep()
    # incast_10to1_1458B_fbCacheFollowerDist_load_fullsweep()
    # incast_10to1_1458B_dctcpMsgSizeDistActual_load_fullsweep()

    ''' FINAL EXPERIMENTS SSIRD POLICY (FULL LOAD SWEEP) '''
    # incast_5to1_1458B_dctcpMsgSizeDistActual_load_fullsweep_ssird_policy_fairshare()

    # assert(False)
    # incast_10to1_1458B_fbHadoopDist_load_fullsweep_ssird_policy_fairshare()
    # incast_10to1_1458B_fbCacheFollowerDist_load_fullsweep_ssird_policy_fairshare()
    # incast_10to1_1458B_dctcpMsgSizeDistActual_load_fullsweep_ssird_policy_fairshare()
