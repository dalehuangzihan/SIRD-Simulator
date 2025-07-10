import sys
from pathlib import Path
import logging
import fct_experiment

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
        self.flow_start_times_us_list = flow_start_times_us_list
        self.num_flows = len(flow_start_times_us_list)
        self.flows_list = []

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
            assert(len(byteloads_list) > 1)
            print(f"len byteloads list: {len(byteloads_list)}, flow_id: {flow.id}")
            serialised_byteloads_list.extend(byteloads_list) 
        serialised_byteloads_list.sort(key = lambda b : b.absolute_timestamp_us)
        serialised_byteloads_list = self.enforce_min_byteload_interval(serialised_byteloads_list)
        return self.convert_abs_timestamp_to_rel_intervals(serialised_byteloads_list)

    def convert_abs_timestamp_to_rel_intervals(self, serialised_byteloads_list):
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

class MultiFlowManualReqInterval(fct_experiment.ManualReqInterval):
    # TODO: move to separate multiflow experiment file
    
    def __init__(self, parent_dir, experiment_name):
        fct_experiment.ManualReqInterval.__init__(self, parent_dir, experiment_name)

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

class MultiFlowExperiment(fct_experiment.FctExperiment):
    # TODO: move to separate multiflow experiment file

    def __init__(self, experiment_family, experiment_name, proto_names, src, dst, flow_start_times_us_list, num_byteloads, byteload_size_B, inter_byteload_period_us, is_full_postproc=False):
        fct_experiment.FctExperiment.__init__(self, experiment_family, experiment_name, proto_names, src, dst, num_byteloads, byteload_size_B, inter_byteload_period_us, is_full_postproc)
        self.flow_start_times_us_list = flow_start_times_us_list

    def execute(self, ssird_sim_dur, dctcp_sim_dur):
        logger.info("\n=====")
        logger.info("Execute experiment " + self.experiment_name)
        logger.info(f'Flags: {self.run_simulations}, {self.run_post_proc}, {self.create_timeseires}, {self.create_plots}, {self.delete_current}')
        logger.info("ssird_sim_duration={:f}; dctcp_sim_duration={:f}".format(ssird_sim_dur, dctcp_sim_dur))

        self.prep_experiment_input(self.src, self.dst, self.num_byteloads, self.byteload_size_B, self.inter_byteload_period_us, self.flow_start_times_us_list)
        ssird_sim_script_path, dctcp_sim_script_path = self.prep_experiment_spec_scripts(ssird_sim_duration=ssird_sim_dur, dctcp_sim_duration=dctcp_sim_dur, experiment_name=self.experiment_name)
        ssird_fct = -1
        dctcp_fct = -1
        load_gbps_measured = -1
        for proto in self.proto_names:
            app_trace_file_path = f"{fct_experiment.PATH_TO_SIM_RESULTS}{proto}-{self.experiment_name}/data/{proto}/{fct_experiment.CLIENT_INJECTION_RATE_GBPS}/applications_trace.str"
            if proto == fct_experiment.SSIRD_PROTO_NAME:
                self.run_experiment(proto, ssird_sim_script_path, f"{fct_experiment.PATH_TO_SIM_COORD}outputs/ssird_{self.experiment_name}.out")
                ssird_fct, load_gbps_measured = self.process_results_fct(app_trace_file_path, proto)
                logger.info(f"SSIRD FCT: {ssird_fct} ms, Load: {load_gbps_measured} Gbps")

            if proto == fct_experiment.DCTCP_PROTO_NAME:
                self.run_experiment(proto, dctcp_sim_script_path, f"{fct_experiment.PATH_TO_SIM_COORD}outputs/{fct_experiment.DCTCP_PROTO_NAME}-{self.experiment_name}.out")
                dctcp_fct, load_gbps_measured = self.process_results_fct(app_trace_file_path, proto)
                logger.info(f"DCTCP FCT: {dctcp_fct} ms, Load: {load_gbps_measured} Gbps")

        return ssird_fct, dctcp_fct, load_gbps_measured

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

    @staticmethod
    def get_sim_duration(num_byteloads, inter_byteload_period_us, multiplication_factor):
        return multiplication_factor * num_byteloads * inter_byteload_period_us * MultiFlowManualReqInterval.TIME_STEP_S

    @staticmethod
    def get_experiment_name(num_flows, num_byteloads, byteload_size_B, inter_byteload_period_us):
        return "{}flo-{}#-{}B-{}us".format(num_flows, num_byteloads, byteload_size_B, inter_byteload_period_us)

def init_logs(output_path):
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler(output_path, mode='w'),
            logging.StreamHandler()
        ]
    )

def multiflow_fct_load_experiment_vary_byteloadsize(is_full_postproc=True, title_addendum=""):

    experiment_family = f"FCT_Vary_Byteload_Size{title_addendum}"
    proto_names = [fct_experiment.SSIRD_PROTO_NAME, fct_experiment.DCTCP_PROTO_NAME]
    # proto_names = [SSIRD_PROTO_NAME]

    src = 0
    dst = 1
    num_byteloads = 10
    inter_byteload_period_us = 100 # is 0.1ms
    flow_start_times_us_list = [0]
    # flow_start_times_us_list = [0, 1, 10]
    num_flows = len(flow_start_times_us_list)

    KILOBYTE = 1000
    # byteload_size_KB_list = [500/8]
    byteload_size_KB_list = [100/8, 500/8, 1000/8, 5000/8, 10000/8] # 100/8KB to 10/8MB
    byteload_size_B_list = [int(n * KILOBYTE) for n in byteload_size_KB_list] 
    num_of_experiments = len(byteload_size_B_list)

    # sim_dur_list = [MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, 1)]
    sim_dur_list = [MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, 1),   # for 100/8KB
                    MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, 1),   # for 500/8KB
                    MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, 1),   # for 1000/8KB
                    MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, 1),   # for 5000/8KB
                    MultiFlowExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, 1.5)]  # for 10000/8KB

    ssird_sim_dur_list = sim_dur_list
    dctcp_sim_dur_list = sim_dur_list

    init_logs(output_path=f"experiment_output/{MultiFlowExperiment.get_experiment_name(num_flows, num_byteloads, "variable_", inter_byteload_period_us)}{title_addendum}.log")

    load_gbps_theoretical = [(bytes*8)/(inter_byteload_period_us * pow(10, -6) * pow(10, 9)) for bytes in byteload_size_B_list]
    logger.info(f"Num flows: {num_flows}")
    logger.info(f"Time Period: {inter_byteload_period_us}")
    logger.info(f"Num Byteloads: {num_byteloads}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Load GBps theoretical: {load_gbps_theoretical}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")

    # return
    ssird_fct_list = []
    dctcp_fct_list = []

    assert num_of_experiments == len(byteload_size_B_list)
    assert num_of_experiments == len(ssird_sim_dur_list)
    assert num_of_experiments == len(dctcp_sim_dur_list)

    load_gbps_measured_list = []
    for i in range(0, num_of_experiments):
        experiment_name = MultiFlowExperiment.get_experiment_name(num_flows, num_byteloads, byteload_size_B_list[i], inter_byteload_period_us) + title_addendum
        fct_exp1 = MultiFlowExperiment(experiment_family, experiment_name, proto_names, src, dst, flow_start_times_us_list, num_byteloads, byteload_size_B_list[i], inter_byteload_period_us, is_full_postproc) 
        ssird_fct, dctcp_fct, load_gbps_measured = fct_exp1.execute(ssird_sim_dur=ssird_sim_dur_list[i], dctcp_sim_dur=dctcp_sim_dur_list[i]) 
        ssird_fct_list.append(ssird_fct)
        dctcp_fct_list.append(dctcp_fct)
        load_gbps_measured_list.append(load_gbps_measured)

    logger.info(f"Num flows: {num_flows}")
    logger.info(f"Time Period: {inter_byteload_period_us}")
    logger.info(f"Num Byteloads: {num_byteloads}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Load Gbps theoretical: {load_gbps_theoretical}")
    logger.info(f"Load Gbps measured: {load_gbps_measured_list}")
    logger.info(f"Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"Sim duration (DCTCP): {dctcp_sim_dur_list}")
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
    multiflow_fct_load_experiment_vary_byteloadsize(is_full_postproc=False, title_addendum="_multiflow")