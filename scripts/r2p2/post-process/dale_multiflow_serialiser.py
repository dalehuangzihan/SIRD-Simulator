import sys
from pathlib import Path
import logging
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
        serialised_byteloads_list = self.enforce_min_byteload_interval(serialised_byteloads_list)
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

    def enforce_min_byteload_interval(self, serialised_byteloads_list):
        ''' Two byteloads cannot have the same timestamp, so we add a spacing between them of size MIN_BYTELOAD_INTERVAL_US '''
        for i in range(0, len(serialised_byteloads_list) - 1):
            first = serialised_byteloads_list[i]
            second = serialised_byteloads_list[i+1] 
            if second.absolute_timestamp_us <= first.absolute_timestamp_us:
                second.absolute_timestamp_us = first.absolute_timestamp_us + MIN_BYTELOAD_INTERVAL_US
        return serialised_byteloads_list

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
            time_spec = bl.relative_interval_us * self.TIME_STEP_S
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

    def execute(self, ssird_sim_dur, dctcp_sim_dur, is_capture_output):
        logger.info("\n=====")
        logger.info("Execute experiment " + self.experiment_name)
        logger.info(f'Flags: {self.run_simulations}, {self.run_post_proc}, {self.create_timeseires}, {self.create_plots}, {self.delete_current}')
        logger.info("ssird_sim_duration={:f}; dctcp_sim_duration={:f}".format(ssird_sim_dur, dctcp_sim_dur))

        self.prep_experiment_input(self.src, self.dst, self.num_byteloads, self.byteload_size_B, self.inter_byteload_period_us, self.flow_start_times_us_list)
        ssird_sim_script_path, dctcp_sim_script_path = self.prep_experiment_spec_scripts(ssird_sim_duration=ssird_sim_dur, dctcp_sim_duration=dctcp_sim_dur, experiment_name=self.experiment_name)
        ssird_fct = -1
        dctcp_fct = -1
        thrpt_gbps_measured_ssird = -1
        thrpt_gbps_measured_per_flow_list_ssird = []
        thrpt_gbps_measured_dctcp = -1
        thrpt_gbps_measured_per_flow_list_dctcp = []
        for proto in self.proto_names:
            app_trace_file_path = f"{dale_fct_experiment.PATH_TO_SIM_RESULTS}{proto}-{self.experiment_name}/data/{proto}/{dale_fct_experiment.CLIENT_INJECTION_RATE_GBPS}/applications_trace.str"
            if proto == dale_fct_experiment.SSIRD_PROTO_NAME:
                self.run_experiment(proto, ssird_sim_script_path, f"{dale_fct_experiment.PATH_TO_SIM_COORD}outputs/ssird_{self.experiment_name}", is_capture_output)
                ssird_fct, thrpt_gbps_measured_ssird, thrpt_gbps_measured_per_flow_list_ssird = self.process_results_fct(app_trace_file_path, proto)
                logger.info(f"SSIRD FCT: {ssird_fct} ms, Throughput: {thrpt_gbps_measured_ssird} Gbps")

            if proto == dale_fct_experiment.DCTCP_PROTO_NAME:
                self.run_experiment(proto, dctcp_sim_script_path, f"{dale_fct_experiment.PATH_TO_SIM_COORD}outputs/{dale_fct_experiment.DCTCP_PROTO_NAME}-{self.experiment_name}", is_capture_output)
                dctcp_fct, thrpt_gbps_measured_dctcp, thrpt_gbps_measured_per_flow_list_dctcp = self.process_results_fct(app_trace_file_path, proto)
                logger.info(f"DCTCP FCT: {dctcp_fct} ms, Throughput: {thrpt_gbps_measured_ssird} Gbps")

        return dale_fct_experiment.ExperimentResults(ssird_fct, dctcp_fct, thrpt_gbps_measured_ssird, thrpt_gbps_measured_dctcp, thrpt_gbps_measured_per_flow_list_ssird, thrpt_gbps_measured_per_flow_list_dctcp)

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

    def get_full_flow_duration(self, flow_trace_event_queue, proto):
        ''' This mtd calculates FCT using timestamps; ALSO checks trace to verify expected behaviour '''
        fct_list = []
        srq_events_all_flows = [e for e in flow_trace_event_queue if (e.get_event() == dale_fct_experiment.FlowTraceEvent.SRQ_EVENT)]
        rrq_events_all_flows = [e for e in flow_trace_event_queue if (e.get_event() == dale_fct_experiment.FlowTraceEvent.RRQ_EVENT)]

        for i in range(0, self.num_flows):
            srq_events_flow_i = [e for e in srq_events_all_flows if e.get_app_level_id() == i]
            rrq_events_flow_i = [e for e in rrq_events_all_flows if e.get_app_level_id() == i]

            logger.info(f"flow_id: {i}, num of byteloads: {self.num_byteloads}, num of srq_events_flow_{i}: {len(srq_events_flow_i)}, num of rrq_events_flow_{i}: {len(rrq_events_flow_i)}")

            # TODO: is testing for now, remove if adaptive batching feature is implemented in the sim.
            logger.debug(f"flow_id: {i}, num of srq_events_flow_{i}: {len(srq_events_flow_i)}, num of byteloads: {self.num_byteloads}, diff = {self.num_byteloads - len(srq_events_flow_i)}")
            assert(len(srq_events_flow_i) == self.num_byteloads)

            flow_trace_event_queue_flow_i = [e for e in flow_trace_event_queue if e.get_app_level_id() == i]
            first_trace_flow_i = flow_trace_event_queue_flow_i[0]
            assert(first_trace_flow_i.get_event() == dale_fct_experiment.FlowTraceEvent.SRQ_EVENT)
            final_trace_flow_i = flow_trace_event_queue_flow_i[len(flow_trace_event_queue_flow_i) - 1]
            assert(final_trace_flow_i.get_event() == dale_fct_experiment.FlowTraceEvent.RRQ_EVENT)

            expected_total_flow_i_size_B = self.num_byteloads * self.byteload_size_B
            if proto == dale_fct_experiment.SSIRD_PROTO_NAME:
                # mirror treatment of hypersmall byteloads by r2p2-app.cc
                if self.byteload_size_B < 4 : expected_total_flow_i_size_B = self.num_byteloads * 4
                logger.debug(f"flow {i}: final rrq req_size = {final_trace_flow_i.get_req_size()}, flow size = {expected_total_flow_i_size_B}, diff = {expected_total_flow_i_size_B - final_trace_flow_i.get_req_size()}")
                assert(final_trace_flow_i.get_req_size() == expected_total_flow_i_size_B)
            if proto == dale_fct_experiment.DCTCP_PROTO_NAME:
                assert(len(srq_events_flow_i) == len(rrq_events_flow_i))
                accumulated_rrq_reqs_size_B = 0
                for e in rrq_events_flow_i:
                    accumulated_rrq_reqs_size_B += e.get_req_size()
                assert(accumulated_rrq_reqs_size_B == expected_total_flow_i_size_B)

            fct = final_trace_flow_i.get_timestamp()- first_trace_flow_i.get_timestamp()
            fct_list.append(fct)

        return fct_list

    def get_measured_thrpt_gbps(self, flow_trace_event_queue):
        # returns in Gbps
        # here we use the n-1 gaps between the n srq events to calc throughput:
        srq_events_all_flows = [e for e in flow_trace_event_queue if e.get_event() == dale_fct_experiment.FlowTraceEvent.SRQ_EVENT]

        # calculate overall throughput
        overall_first_srq_timestamp = srq_events_all_flows[0].get_timestamp()
        overall_final_srq_timestamp = srq_events_all_flows[len(srq_events_all_flows)-1].get_timestamp()
        total_duration_s = overall_final_srq_timestamp - overall_first_srq_timestamp
        total_data_B_all_flows = 0
        for i in range(0, len(srq_events_all_flows)-2):
            total_data_B_all_flows += srq_events_all_flows[i].get_req_size()
        total_throughput_gbps = (total_data_B_all_flows * 8) / (total_duration_s) * pow(10,-9)

        # calculate throuhgput per flow
        throughput_gbps_per_flow_list = []
        for i in range(0, self.num_flows):
            throughput_gbps_flow_i = 0
            srq_events_flow_i = [e for e in srq_events_all_flows if e.get_app_level_id() == i]
            assert(self.num_byteloads == len (srq_events_flow_i))
            if self.num_byteloads == 1:
                # logging.debug(f"NB: srq event count = {len(srq_events)}, not enough events to measure app throughput")  
                # return -1
                print(self.num_byteloads, self.byteload_size_B, self.inter_byteload_period_us)
                throughput_gbps_flow_i = (self.byteload_size_B * 8 / (self.inter_byteload_period_us * pow(10,-6))) * pow(10,-9)
            else:
                total_duration_i_s = srq_events_flow_i[len(srq_events_flow_i)-1].get_timestamp() - srq_events_flow_i[0].get_timestamp()
                total_data_B = 0 
                for i in range(0, len(srq_events_flow_i)-2):
                    total_data_B += srq_events_flow_i[i].get_req_size()
                throughput_gbps_flow_i = (total_data_B * 8 / total_duration_i_s) * pow(10,-9)
            throughput_gbps_per_flow_list.append(throughput_gbps_flow_i)

        return total_throughput_gbps, throughput_gbps_per_flow_list

    @staticmethod
    def get_sim_duration(num_byteloads, inter_byteload_period_us, multiplication_factor):
        return multiplication_factor * num_byteloads * inter_byteload_period_us * MultiFlowManualReqInterval.TIME_STEP_S

    @staticmethod
    def get_experiment_name(num_flows, num_byteloads, byteload_size_B, inter_byteload_period_us):
        return "{}flo-{}#-{}B-{}us".format(num_flows, num_byteloads, byteload_size_B, inter_byteload_period_us)

def init_logs(output_path):
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler(output_path, mode='w'),
            logging.StreamHandler()
        ]
    )

def multiflow_fct_thrpt_experiment_vary_byteloadsize(is_capture_output=True, is_full_postproc=True, title_addendum=""):

    experiment_family = f"FCT_Vary_Byteload_Size{title_addendum}"
    proto_names = [dale_fct_experiment.SSIRD_PROTO_NAME, dale_fct_experiment.DCTCP_PROTO_NAME]
    # proto_names = [SSIRD_PROTO_NAME]

    src = 0
    dst = 1
    num_byteloads = 10
    inter_byteload_period_us = 100 # is 0.1ms
    flow_start_times_us_list = [0, 1]
    # flow_start_times_us_list = [0, 1, 10]
    num_flows = len(flow_start_times_us_list)

    KILOBYTE = 1000
    # byteload_size_KB_list = [10000/8]
    byteload_size_KB_list = [100/8, 500/8, 1000/8, 5000/8, 10000/8] # 100/8KB to 10/8MB
    byteload_size_B_list = [int(n * KILOBYTE) for n in byteload_size_KB_list] 
    num_of_experiments = len(byteload_size_B_list)

    # sim_dur_list = [MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, num_flows * 1.5)] # for 10000/8KB
    sim_dur_list = [MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, num_flows * 1),   # for 100/8KB
                    MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, num_flows * 1),   # for 500/8KB
                    MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, num_flows * 1),   # for 1000/8KB
                    MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, num_flows * 1),   # for 5000/8KB
                    MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, num_flows * 1.5)]  # for 10000/8KB

    ssird_sim_dur_list = sim_dur_list
    dctcp_sim_dur_list = sim_dur_list

    init_logs(output_path=f"experiment_output/{MultiFlowExperiment.get_experiment_name(num_flows, num_byteloads, "variable_", inter_byteload_period_us)}{title_addendum}.log")

    thrpt_gbps_theoretical_parallel_flows = [num_flows * (bytes*8)/(inter_byteload_period_us * pow(10, -6) * pow(10, 9)) for bytes in byteload_size_B_list]

    logger.info(f"Num flows: {num_flows}")
    logger.info(f"Time Period: {inter_byteload_period_us}")
    logger.info(f"Num Byteloads: {num_byteloads}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Load Gbps theoretical (parallel flows): {thrpt_gbps_theoretical_parallel_flows}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")

    # return
    ssird_fct_list = []
    dctcp_fct_list = []

    assert num_of_experiments == len(byteload_size_B_list)
    assert num_of_experiments == len(ssird_sim_dur_list)
    assert num_of_experiments == len(dctcp_sim_dur_list)

    thrpt_gbps_measured_list_ssird = []
    thrpt_gbps_measured_list_dctcp = []
    thrpt_gbps_measured_per_flow_list_list_ssird = []
    thrpt_gbps_measured_per_flow_list_list_dctcp = []
    for i in range(0, num_of_experiments):
        experiment_name = MultiFlowExperiment.get_experiment_name(num_flows, num_byteloads, byteload_size_B_list[i], inter_byteload_period_us) + title_addendum
        fct_exp1 = MultiFlowExperiment(experiment_family, experiment_name, proto_names, src, dst, flow_start_times_us_list, num_byteloads, byteload_size_B_list[i], inter_byteload_period_us, is_full_postproc) 
        results = fct_exp1.execute(ssird_sim_dur=ssird_sim_dur_list[i], dctcp_sim_dur=dctcp_sim_dur_list[i], is_capture_output=is_capture_output) 
        ssird_fct_list.append(results.ssird_fct)
        dctcp_fct_list.append(results.dctcp_fct)
        thrpt_gbps_measured_list_ssird.append(results.thrpt_gbps_measured_ssird)
        thrpt_gbps_measured_list_dctcp.append(results.thrpt_gbps_measured_dctcp)
        thrpt_gbps_measured_per_flow_list_list_ssird.append(results.thrpt_gbps_measured_per_flow_list_ssird)
        thrpt_gbps_measured_per_flow_list_list_dctcp.append(results.thrpt_gbps_measured_per_flow_list_dctcp)

    logger.info(f"Num flows: {num_flows}")
    logger.debug(f"Flow start times (us): {flow_start_times_us_list}")
    logger.info(f"Time Period: {inter_byteload_period_us}")
    logger.info(f"Num Byteloads: {num_byteloads}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"Sim duration (DCTCP): {dctcp_sim_dur_list}")
    logger.info(f"Thrpt Gbps theoretical: {thrpt_gbps_theoretical_parallel_flows}")
    logger.info(f"Thrpt Gbps measured (SSIRD): {thrpt_gbps_measured_list_ssird}")
    logger.info(f"Thrpt Gbps measured (DCTCP): {thrpt_gbps_measured_list_dctcp}")
    logger.debug(f"Thrpt Gbps measured per flow (SSIRD): {thrpt_gbps_measured_per_flow_list_list_ssird}")
    logger.debug(f"Thrpt Gbps measured per flow (DCTCP): {thrpt_gbps_measured_per_flow_list_list_dctcp}")
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
    multiflow_fct_thrpt_experiment_vary_byteloadsize(is_capture_output=False, is_full_postproc=False, title_addendum="_multiflow")