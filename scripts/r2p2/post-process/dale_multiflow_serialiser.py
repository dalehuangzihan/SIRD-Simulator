import sys
from pathlib import Path
import logging
import collections
import math
import dale_fct_experiment

MIN_BYTELOAD_INTERVAL_US = 1
  
logger = logging.getLogger(__name__)

class Byteload:
    '''
    relative_timestamp_us is the timestamp since the start of the flow, measured in us; flow always starts at a relative timestamp of 0us 
    relative_interval_us is the time gap between this byteload and the previous one in the serialised multiflow
    '''
    def __init__(self, src, dst, flow_id, size_B, relative_timestamp_us, absolute_timestamp_us):
        self.src = src
        self.dst = dst
        self.flow_id = flow_id
        self.size_B = size_B
        self.relative_timestamp_us = relative_timestamp_us
        self.absolute_timestamp_us = absolute_timestamp_us
        self.relative_interval_us = None
    
    # custom comparators
    def __lt__(self, other):
        return self.absolute_timestamp_us < other.absolute_timestamp_us 
    def __le__(self, other):
        return self.absolute_timestamp_us <= other.absolute_timestamp_us 
    def __gt__(self, other):
        return self.absolute_timestamp_us > other.absolute_timestamp_us
    def __ge__(self, other):
        return self.absolute_timestamp_us >= other.absolute_timestamp_us
    def __eq__(self, other):
        return self.absolute_timestamp_us == other.absolute_timestamp_us
    def __ne__(self, other):
        return self.absolute_timestamp_us != other.absolute_timestamp_us

class Flow:
    '''
    Each flow is a unique connection, and is uniquely identified by its flow-id
    '''
    RELATIVE_START_TIME_US = 0

    def __init__(self, src, dst, flow_id, num_byteloads, byteload_size_B, byteload_interval_us, absolute_start_time_us):
        self.id = flow_id
        self.src = src
        self.dst = dst
        self.num_byteloads = num_byteloads
        self.byteload_size_B = byteload_size_B
        self.byteload_interval_us = byteload_interval_us
        self.absolute_start_time_us = absolute_start_time_us
        self.byteloads_list = []

        assert(byteload_interval_us >= 1)
        assert(byteload_interval_us*10%10 == 0)

        self.init_byteloads()

    def init_byteloads(self):
        for i in range(0, self.num_byteloads):
            rel_timestamp_us = self.RELATIVE_START_TIME_US + i * self.byteload_interval_us
            absolute_timestamp_us = self.absolute_start_time_us + rel_timestamp_us
            self.byteloads_list.append(Byteload(self.src, self.dst, self.id, self.byteload_size_B, rel_timestamp_us, absolute_timestamp_us))

class MultiFlow:
    '''
    Is a collection of multiple flows that are passed to the simulation
    TODO: currently can only replicate the same flow multiple times
    ''' 

    def __init__(self, src, dst, num_byteloads_per_flow, byteload_size_B, byteload_interval_us, flow_start_times_us_list):
        self.src = src
        self.dst = dst
        self.num_byteloads_per_flow = num_byteloads_per_flow
        self.byteload_size_B = byteload_size_B
        self.byteload_interval_us = byteload_interval_us
        self.flow_start_times_us_list = flow_start_times_us_list # is the start times relative to the overall start timestamp of 0us
        self.num_flows = len(flow_start_times_us_list)
        self.flows_list = []

        assert(num_byteloads_per_flow > 1) # we want at least 2 byteloads per flow
        self.init_flows()

    def init_flows(self):
        for i in range(0, self.num_flows):
            flow_start_time_us = self.flow_start_times_us_list[i]
            self.flows_list.append(Flow(self.src, self.dst, i, self.num_byteloads_per_flow, self.byteload_size_B, self.byteload_interval_us, flow_start_time_us))
        print(f"num flows: {len(self.flows_list)}")
    
    def serialise_flows_to_byteloads(self):
        if len(self.flows_list) < 1:
            print(f"Flows list is empty (size={len(self.flows_list)})!", file=sys.stderr)
            return
        serialised_byteloads_list = [] 
        for flow in self.flows_list:
            byteloads_list = flow.byteloads_list
            assert(len(byteloads_list) > 0)
            # print(f"len byteloads list: {len(byteloads_list)}, flow_id: {flow.id}")
            serialised_byteloads_list.extend(byteloads_list) 
        serialised_byteloads_list.sort(key = lambda b : b.absolute_timestamp_us)
        # serialised_byteloads_list = self.enforce_min_byteload_interval(serialised_byteloads_list)
        return self.convert_abs_timestamp_to_rel_intervals(serialised_byteloads_list)

    def convert_abs_timestamp_to_rel_intervals(self, serialised_byteloads_list):
        if len(serialised_byteloads_list) == 1:
            only = serialised_byteloads_list[0]
            only.relative_interval_us = only.absolute_timestamp_us
        else:
            for i in range(0, len(serialised_byteloads_list) - 1):
                first = serialised_byteloads_list[i]
                second = serialised_byteloads_list[i+1] 
                if i == 0: first.relative_interval_us = first.absolute_timestamp_us
                second.relative_interval_us = second.absolute_timestamp_us - first.absolute_timestamp_us
        return serialised_byteloads_list

    # def enforce_min_byteload_interval(self, serialised_byteloads_list):
    #     ''' Two byteloads cannot have the same timestamp, so we add a spacing between them of size MIN_BYTELOAD_INTERVAL_US '''
    #     for i in range(0, len(serialised_byteloads_list) - 1):
    #         first = serialised_byteloads_list[i]
    #         second = serialised_byteloads_list[i+1] 
    #         if second.absolute_timestamp_us <= first.absolute_timestamp_us:
    #             second.absolute_timestamp_us = first.absolute_timestamp_us + MIN_BYTELOAD_INTERVAL_US
    #     return serialised_byteloads_list

    @staticmethod
    def pretty_print_byteloads_abs_timestamp(serialised_byteloads_list):
        abs_timestamp_list = []
        for byteload in serialised_byteloads_list:
            abs_timestamp_list.append((byteload.flow_id, byteload.absolute_timestamp_us, byteload.relative_interval_us))
        print(abs_timestamp_list)

    @staticmethod
    def enforce_min_flow_interval(flow_start_times_us_list):
        # check that flows do not start less than 1us from each other
        flow_start_times_us_list.sort()
        start_times_pair_us = zip(flow_start_times_us_list, flow_start_times_us_list[1:])
        for a, b in start_times_pair_us: assert(b - a >= MIN_BYTELOAD_INTERVAL_US)

class MultiFlowManualReqInterval(dale_fct_experiment.ManualReqInterval):
    # TODO: move to separate multiflow experiment file
    
    def __init__(self, parent_dir, experiment_name):
        dale_fct_experiment.ManualReqInterval.__init__(self, parent_dir, experiment_name)

    def create_p2p_mri(self, multiflow_obj):
        '''
        Creates MRI csv file of multiple flows of the same kind between a single src, dst pair.
        '''
        src = multiflow_obj.src
        dst = multiflow_obj.dst
        
        mri_filepath = self.get_mri_filepath(self.parent_dir, self.experiment_name)
        mri_byteloads_spec = []    
        mri_byteloads_spec.append(str(src))

        serialised_byteloads_list = multiflow_obj.serialise_flows_to_byteloads()
        for i in range(0, len(serialised_byteloads_list)):
            bl = serialised_byteloads_list[i]
            time_spec = bl.relative_interval_us * self.MICROSECOND_S
            if i == 0: time_spec += self.MRI_START_TIME_S 
            byteload_str = "{:.7f}|{}|{}|{}".format(time_spec, str(dst), bl.size_B, bl.flow_id)
            mri_byteloads_spec.append(byteload_str)

        self.mri_list_to_csv(mri_byteloads_spec, mri_filepath)
        return mri_filepath

    @staticmethod
    def get_mri_filepath(parent_dir, experiment_name):
        return parent_dir + experiment_name + ".csv"

class MultiFlowExperiment(dale_fct_experiment.FctExperiment):
    # TODO: move to separate multiflow experiment file

    def __init__(self, experiment_family, experiment_name, proto_names, src, dst, flow_start_times_us_list, num_byteloads, byteload_size_B, inter_byteload_period_us, is_full_postproc=False):
        dale_fct_experiment.FctExperiment.__init__(self, experiment_family, experiment_name, proto_names, src, dst, num_byteloads, byteload_size_B, inter_byteload_period_us, is_full_postproc)
        self.flow_start_times_us_list = flow_start_times_us_list
        self.num_flows = len(flow_start_times_us_list)

    def execute(self, ssird_sim_dur, dctcp_sim_dur):
        logger.info("\n=====")
        logger.info("Execute experiment " + self.experiment_name)
        logger.info(f'Flags: {self.run_simulations}, {self.run_post_proc}, {self.create_timeseires}, {self.create_plots}, {self.delete_current}')
        logger.info("ssird_sim_duration={:f}; dctcp_sim_duration={:f}".format(ssird_sim_dur, dctcp_sim_dur))

        self.prep_experiment_input(self.src, self.dst, self.num_byteloads, self.byteload_size_B, self.inter_byteload_period_us, self.flow_start_times_us_list)
        ssird_sim_script_path, dctcp_sim_script_path = self.prep_experiment_spec_scripts(ssird_sim_duration=ssird_sim_dur, dctcp_sim_duration=dctcp_sim_dur, experiment_name=self.experiment_name)
        ssird_fct = -1
        dctcp_fct = -1
        gdpt_gbps_measured_ssird = -1
        gdpt_gbps_measured_per_flow_list_ssird = []
        gdpt_gbps_measured_dctcp = -1
        gdpt_gbps_measured_per_flow_list_dctcp = []
        app_trace_file_paths_ssird = []
        app_trace_file_paths_dctcp = []
        for proto in self.proto_names:
            app_trace_file_path = f"{dale_fct_experiment.PATH_TO_SIM_RESULTS}{proto}-{self.experiment_name}/data/{proto}/{dale_fct_experiment.CLIENT_INJECTION_RATE_GBPS}/applications_trace.str"
            if proto == dale_fct_experiment.SSIRD_PROTO_NAME:
                app_trace_file_paths_ssird.append(app_trace_file_path)
                outputs_dir = f"{dale_fct_experiment.PATH_TO_SIM_COORD}outputs/{self.experiment_family}/"
                Path(outputs_dir).mkdir(parents=True, exist_ok=True)

                self.run_experiment(proto, ssird_sim_script_path, f"{outputs_dir}ssird_{self.experiment_name}")
                ssird_fct, gdpt_gbps_measured_ssird, gdpt_gbps_measured_per_flow_list_ssird = self.process_results_fct(app_trace_file_path, proto)
                logger.info(f"SSIRD FCT: {ssird_fct} ms, Gdpt (overall): {gdpt_gbps_measured_ssird} Gbps, Gdpt (per flow): {gdpt_gbps_measured_per_flow_list_ssird}")

            if proto == dale_fct_experiment.DCTCP_PROTO_NAME:
                app_trace_file_paths_dctcp.append(app_trace_file_path)
                self.run_experiment(proto, dctcp_sim_script_path, f"{outputs_dir}{dale_fct_experiment.DCTCP_PROTO_NAME}-{self.experiment_name}")
                dctcp_fct, gdpt_gbps_measured_dctcp, gdpt_gbps_measured_per_flow_list_dctcp = self.process_results_fct(app_trace_file_path, proto)
                logger.info(f"DCTCP FCT: {dctcp_fct} ms, Gtpt (overall): {gdpt_gbps_measured_dctcp} Gbps, Gdpt (per flow): {gdpt_gbps_measured_per_flow_list_dctcp}")
        
        self.write_app_trace_paths_to_file(app_trace_file_paths_ssird, app_trace_file_paths_dctcp)

        return dale_fct_experiment.ExperimentResults(ssird_fct, dctcp_fct, gdpt_gbps_measured_ssird, gdpt_gbps_measured_dctcp, gdpt_gbps_measured_per_flow_list_ssird, gdpt_gbps_measured_per_flow_list_dctcp)

    def prep_experiment_input(self, src, dst, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, flow_start_times_list):
        logger.info("-----")
        logger.info("Preparing experiment input MRIs")
        try:
            logger.info("### Creating MRI inputs parent dir: " + self.mri_input_dir)
            Path(self.mri_input_dir).mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            logger.info("File " + self.mri_input_dir + " aready exists.")
        
        mri = MultiFlowManualReqInterval(self.mri_input_dir, self.experiment_name)
        multiflow_obj = MultiFlow(src, dst, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, flow_start_times_list)  
        mri_filepath = mri.create_p2p_mri(multiflow_obj)
        return mri_filepath

    def process_results_fct(self, app_trace_file_path, proto):
        logger.info("Processing results")
        logger.info(app_trace_file_path)
        
        d = {}
        for i in range(0, self.num_flows):
            d[i] = dale_fct_experiment.FlowStats(proto, i, self.num_byteloads, self.byteload_size_B)
        flow_stats_dict = collections.OrderedDict(sorted(d.items()))
        del d

        total_bytes_sent_B = 0
        total_bytes_sent_until_penultimate_srq_B = 0
        overall_srq_start_time_s = math.inf
        overall_final_srq_timestamp_s = None

        try:
            with open(app_trace_file_path, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    flow_trace_event = dale_fct_experiment.FlowTraceEvent.read_flow_trace_from_str(line)
                    flow_id = flow_trace_event.get_app_level_id()
                    flow_stats_dict.get(flow_id).update_flow_stats(flow_trace_event)

                    if (flow_trace_event.get_event() == dale_fct_experiment.FlowTraceEvent.SRQ_EVENT):
                        overall_srq_start_time_s = min(flow_trace_event.get_timestamp(), overall_srq_start_time_s)
                        overall_final_srq_timestamp_s = flow_trace_event.get_timestamp()
                        total_bytes_sent_until_penultimate_srq_B = total_bytes_sent_B
                        total_bytes_sent_B += flow_trace_event.get_req_size() 

                    del flow_id
                    del flow_trace_event
        except FileNotFoundError:
            logger.error("The file was not found")
        except IOError:
            logger.error("An error occurred while reading the file")
    
        # TODO: FIX ME! This total-thrpt calc seems a lil iffy... it overestimates gbps by 5%. Why??
        measured_total_gdpt_gbps = (total_bytes_sent_until_penultimate_srq_B * 8) / (overall_final_srq_timestamp_s - overall_srq_start_time_s) * pow(10,-9)
        # measured_total_gdpt_gbps = sum(measured_gdpt_gbps_per_flow_list)

        fct_list = []
        measured_gdpt_gbps_per_flow_list = []
        for _, flow_stats_obj in flow_stats_dict.items():
            flow_stats_obj.check_flow_stats()
            fct_list.append(flow_stats_obj.get_fct_s())
            measured_gdpt_gbps_per_flow_list.append(flow_stats_obj.get_measured_gdpt_for_flow_gbps())

        return fct_list, measured_total_gdpt_gbps, measured_gdpt_gbps_per_flow_list

    def write_app_trace_paths_to_file(self, app_trace_file_paths_ssird, app_trace_file_paths_dctcp):
        logger.info("-----")
        logger.info("Backing up app trace file paths")
        parent_dir = f"{dale_fct_experiment.APP_TRACE_PATHS_BACKUP_PATH}{self.experiment_family}/"
        Path(parent_dir).mkdir(parents=True, exist_ok=True)
        backup_filepath = parent_dir + self.experiment_name + "_traces.txt"
        logger.debug(backup_filepath)
        with open(backup_filepath, 'w') as fout:
            for ssird_trace_path in app_trace_file_paths_ssird:
                fout.write(f"{ssird_trace_path}\n")
            for dctcp_trace_path in app_trace_file_paths_dctcp:
                fout.write(f"{dctcp_trace_path}\n")

    @staticmethod
    def get_sim_duration(num_byteloads, inter_byteload_period_us, multiplication_factor):
        return multiplication_factor * num_byteloads * inter_byteload_period_us * MultiFlowManualReqInterval.MICROSECOND_S

    '''
    TODO: double-check this calculation! if it works, use it instead of the prev sim_dur calculator.
    '''
    @staticmethod
    def get_sim_duration_new(num_flows, inter_flow_spacing_us, num_byteloads, byteload_size_B, inter_byteload_period_us, multiplication_factor=1):
        send_duration_per_flow_s = num_byteloads * inter_byteload_period_us * MultiFlowManualReqInterval.MICROSECOND_S
        overall_send_duration_s = (num_flows-1) * inter_flow_spacing_us * MultiFlowManualReqInterval.MICROSECOND_S + send_duration_per_flow_s
        overall_data_send_B = num_flows * num_byteloads * byteload_size_B 
        theoretical_gdpt_bps = overall_data_send_B * 8 / overall_send_duration_s
        multiples_of_link_speed = theoretical_gdpt_bps / dale_fct_experiment.LINK_SPEED_BITS_PER_SEC
        k = multiples_of_link_speed if multiples_of_link_speed > 1 else 1
        sim_dur_s = k * overall_data_send_B * 8 / dale_fct_experiment.LINK_SPEED_BITS_PER_SEC
        return sim_dur_s * multiplication_factor

    @staticmethod
    def get_experiment_name(num_flows, num_byteloads, byteload_size_B, inter_byteload_period_us):
        return "{}flo-{}#-{}B-{}us".format(num_flows, num_byteloads, byteload_size_B, inter_byteload_period_us)

def multiflow_fct_gdpt_experiment_vary_byteloadsize(is_full_postproc=True, title_addendum=""):

    experiment_family = f"FCT_Vary_Byteload_Size{title_addendum}"
    proto_names = [dale_fct_experiment.SSIRD_PROTO_NAME, dale_fct_experiment.DCTCP_PROTO_NAME]
    # proto_names = [SSIRD_PROTO_NAME]

    src = 0
    dst = 1
    num_byteloads = 10
    inter_byteload_period_us = 100 # is 0.1ms
    num_flows = 2
    inter_flow_spacing_us = 1
    flow_start_times_us_list = [i * inter_flow_spacing_us for i in range(0, num_flows)]

    KILOBYTE = 1000
    # byteload_size_KB_list = [10/8]
    # byteload_size_KB_list = [10/8, 50/8, 100/8, 500/8, 1000/8] # 10/8KB to 1/8MB
    byteload_size_KB_list = [100/8, 500/8, 1000/8, 5000/8, 10000/8] # 100/8KB to 10/8MB
    byteload_size_B_list = [int(n * KILOBYTE) for n in byteload_size_KB_list] 
    num_of_experiments = len(byteload_size_B_list)

    # sim_dur_list = [MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, num_flows * 1.1)]
    sim_dur_list = [MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, num_flows * 1),   # for 100/8KB
                    MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, num_flows * 1),   # for 500/8KB
                    MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, num_flows * 1),   # for 1000/8KB
                    MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, num_flows * 1),   # for 5000/8KB
                    MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, num_flows * 1.5)]  # for 10000/8KB

    ssird_sim_dur_list = sim_dur_list
    dctcp_sim_dur_list = sim_dur_list

    dale_fct_experiment.init_logs(experiment_family, f"{MultiFlowExperiment.get_experiment_name(num_flows, num_byteloads, "variable_", inter_byteload_period_us)}{title_addendum}.log")

    gdpt_gbps_theoretical_parallel_flows = [num_flows * (bytes*8)/(inter_byteload_period_us * pow(10, -6) * pow(10, 9)) for bytes in byteload_size_B_list]

    logger.info(f"Num flows: {num_flows}")
    logger.info(f"Time Period: {inter_byteload_period_us}")
    logger.info(f"Num Byteloads: {num_byteloads}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Load Gbps theoretical (parallel flows): {gdpt_gbps_theoretical_parallel_flows}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")

    # return
    ssird_fct_list = []
    dctcp_fct_list = []

    assert num_of_experiments == len(byteload_size_B_list)
    assert num_of_experiments == len(ssird_sim_dur_list)
    assert num_of_experiments == len(dctcp_sim_dur_list)

    gdpt_gbps_measured_list_ssird = []
    gdpt_gbps_measured_list_dctcp = []
    gdpt_gbps_measured_per_flow_list_list_ssird = []
    gdpt_gbps_measured_per_flow_list_list_dctcp = []
    for i in range(0, num_of_experiments):
        experiment_name = MultiFlowExperiment.get_experiment_name(num_flows, num_byteloads, byteload_size_B_list[i], inter_byteload_period_us) + title_addendum
        fct_exp1 = MultiFlowExperiment(experiment_family, experiment_name, proto_names, src, dst, flow_start_times_us_list, num_byteloads, byteload_size_B_list[i], inter_byteload_period_us, is_full_postproc) 
        results = fct_exp1.execute(ssird_sim_dur=ssird_sim_dur_list[i], dctcp_sim_dur=dctcp_sim_dur_list[i]) 
        ssird_fct_list.append(results.ssird_fct)
        dctcp_fct_list.append(results.dctcp_fct)
        gdpt_gbps_measured_list_ssird.append(results.gdpt_gbps_measured_ssird)
        gdpt_gbps_measured_list_dctcp.append(results.gdpt_gbps_measured_dctcp)
        gdpt_gbps_measured_per_flow_list_list_ssird.append(results.gdpt_gbps_measured_per_flow_list_ssird)
        gdpt_gbps_measured_per_flow_list_list_dctcp.append(results.gdpt_gbps_measured_per_flow_list_dctcp)

    logger.info(f"Num flows: {num_flows}")
    logger.debug(f"Flow start times (us): {flow_start_times_us_list}")
    logger.info(f"Time Period: {inter_byteload_period_us}")
    logger.info(f"Num Byteloads: {num_byteloads}")
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

def testing():
    # TODO: remove
    flow_start_times_us_list = [0, 1, 10]
    multiflow_obj = MultiFlow(src=0, dst=1, num_byteloads_per_flow=3, byteload_size_B=1000, byteload_interval_us=1, flow_start_times_us_list=flow_start_times_us_list)
    serialised_byteloads_list = multiflow_obj.serialise_flows_to_byteloads()    
    MultiFlow.pretty_print_byteloads_abs_timestamp(serialised_byteloads_list)

if __name__ == "__main__":
    # testing()
    multiflow_fct_gdpt_experiment_vary_byteloadsize(is_full_postproc=False, title_addendum="_multiflow")