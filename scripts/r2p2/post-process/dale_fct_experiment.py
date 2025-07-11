import sys
import subprocess
from pathlib import Path
import csv
import logging

# Common experiment param; value is meaningful only when req_interval_distr is not 'manual'
CLIENT_INJECTION_RATE_GBPS = "60"
DCTCP_ECN_MARKING_THRESHOLD = "50"
LINK_SPEED_BITS_PER_SEC = 100 * pow(10,9) * 8 # 100Gbps

SSIRD_PROTO_NAME = "SSIRD"
DCTCP_PROTO_NAME = f"DCTCP-{DCTCP_ECN_MARKING_THRESHOLD}"

PATH_TO_SIRD_SIM = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/"
PATH_TO_SIM_COORD = PATH_TO_SIRD_SIM + "scripts/r2p2/coord/"
PATH_TO_POST_PROCESS = PATH_TO_SIRD_SIM + "post_process/"
PATH_TO_SIM_RESULTS = PATH_TO_SIRD_SIM + "scripts/r2p2/coord/results/"
PATH_TO_EXPERIMENTS = PATH_TO_SIRD_SIM + "scripts/r2p2/coord/config/"
SCRIPTS_RELATIVE_PATH = "dale_experiments/"
PATH_TO_EXPERIMENTS_SCRIPTS = PATH_TO_EXPERIMENTS + SCRIPTS_RELATIVE_PATH
MRI_RELATIVE_PATH = "dale_experiments/"
PATH_TO_EXPERIMENTS_INPUTS = PATH_TO_EXPERIMENTS + "manual-req-intervals/" + MRI_RELATIVE_PATH

logger = logging.getLogger(__name__)

class FlowTraceEvent:
    SRQ_EVENT = "srq"
    RRQ_EVENT = "rrq"

    def __init__(self, timestamp, event, local_addr, remote_addr, thread_id, req_id, app_level_id, req_duration, req_size, resp_size, pending_tasks_size, wildcard):
        self.timestamp = timestamp
        self.event = event
        self.local_addr = local_addr
        self.remote_addr = remote_addr
        self.thread_id = thread_id
        self.req_id = req_id
        self.app_level_id = app_level_id
        self.req_duration = req_duration
        self.req_size = req_size
        self.resp_size = resp_size
        self.pending_tasks_size = pending_tasks_size
        self.wildcard = wildcard

    def get_timestamp(self):
        return float(self.timestamp)
    def get_event(self):
        return self.event
    def get_req_size(self):
        return int(self.req_size)
    def get_app_level_id(self):
        return int(self.app_level_id)

    @staticmethod
    def read_flow_trace_from_str(str_line):
        tokens = str_line.split(" ")
        assert(len(tokens) == 12)
        return FlowTraceEvent(tokens[0], tokens[1], tokens[2], tokens[3], tokens[4], tokens[5], tokens[6], tokens[7], tokens[8], tokens[9], tokens[10], tokens[11])

class ManualReqInterval:
    # is in seconds; is 1us
    TIME_STEP_S = 0.000001
    MRI_START_TIME_S = TIME_STEP_S

    def __init__(self, parent_dir, experiment_name):
        self.parent_dir = parent_dir
        self.experiment_name = experiment_name

    def create_p2p_mri(self, src, dst, num_byteloads, byteload_size_B, inter_byteload_period_us):
        mri_filepath = self.get_mri_filepath(self.parent_dir, self.experiment_name)
        mri_byteloads_spec = []    
        mri_byteloads_spec.append(str(src))
        for i in range(0, num_byteloads):
            time_spec = self.MRI_START_TIME_S if i == 0 else inter_byteload_period_us * self.TIME_STEP_S
            byteload_str = "{:.7f}|{}|{}".format(time_spec, str(dst), byteload_size_B) 
            mri_byteloads_spec.append(byteload_str)
        self.mri_list_to_csv(mri_byteloads_spec, mri_filepath)
        return mri_filepath

    @staticmethod
    def get_mri_filepath(parent_dir, experiment_name):
        return parent_dir + experiment_name + ".csv"

    @staticmethod
    def mri_list_to_csv(mri_list, mri_filepath):
        with open(mri_filepath, 'w') as mri_file:
            wr = csv.writer(mri_file, quoting=csv.QUOTE_NONE)
            wr.writerow(mri_list)

class SimSpecScript:
    PATH_TO_SSIRD_TEMPLATE_NOBURST = PATH_TO_EXPERIMENTS_SCRIPTS + "template-ssird-2host-p2p-noburst.sh"
    PATH_TO_DCTCP_TEMPLATE_NOBURST = PATH_TO_EXPERIMENTS_SCRIPTS + "template-dctcp-2host-p2p-noburst.sh"

    MANUAL_REQ_INTERVAL_FILE_L = "manual_req_interval_file_l"
    DURATION_MODIFIER_L = "duration_modifier_l"
    DCTCP_K_L = "dctcp_k_l"
    SIMULATION_NAME_L = "simulation_name_l"

    def __init__(self, parent_dir, experiment_name):
        self.parent_dir = parent_dir
        self.experiment_name = experiment_name
    
    def create_ssird_noburst_params_script(self, mri_relative_path, sim_duration):
        script_filepath = self.parent_dir + f"{SSIRD_PROTO_NAME}-" + self.experiment_name + ".sh"
        with open(self.PATH_TO_SSIRD_TEMPLATE_NOBURST) as template, open(script_filepath, 'w') as fout:
            lines_in = template.readlines()
            for i in range(len(lines_in)):
                line_out = lines_in[i]
                if self.MANUAL_REQ_INTERVAL_FILE_L in line_out:
                    line_out = "{}='{}'\n".format(self.MANUAL_REQ_INTERVAL_FILE_L, mri_relative_path)
                elif self.DURATION_MODIFIER_L in line_out:
                    line_out = "{}='{:f}'\n".format(self.DURATION_MODIFIER_L, sim_duration)
                fout.write(line_out)
        return script_filepath

    def create_dctcp_noburst_params_script(self, mri_relative_path, sim_duration):
        script_filepath = self.parent_dir + f"{DCTCP_PROTO_NAME}-" + self.experiment_name + ".sh"
        with open(self.PATH_TO_DCTCP_TEMPLATE_NOBURST) as template, open(script_filepath, 'w') as fout:
            lines_in = template.readlines()
            for i in range(len(lines_in)):
                line_out = lines_in[i]
                if self.MANUAL_REQ_INTERVAL_FILE_L in line_out:
                    line_out = "{}='{}'\n".format(self.MANUAL_REQ_INTERVAL_FILE_L, mri_relative_path)
                elif self.DURATION_MODIFIER_L in line_out:
                    line_out = "{}='{:f}'\n".format(self.DURATION_MODIFIER_L, sim_duration)
                elif self.DCTCP_K_L in line_out:
                    line_out = "{}='{}'\n".format(self.DCTCP_K_L, DCTCP_ECN_MARKING_THRESHOLD)
                elif self.SIMULATION_NAME_L in line_out:
                    line_out = "{}='{}'\n".format(self.SIMULATION_NAME_L, DCTCP_PROTO_NAME)
                fout.write(line_out)
        return script_filepath


class FctExperiment:
    def __init__(self, experiment_family, experiment_name, proto_names, src, dst, num_byteloads, byteload_size_B, inter_byteload_period_us, is_full_postproc=False):
        self.experiment_family = experiment_family
        self.proto_names = proto_names

        self.src = src
        self.dst = dst
        self.num_byteloads = num_byteloads
        self.byteload_size_B = byteload_size_B
        self.inter_byteload_period_us = inter_byteload_period_us
        self.experiment_name = experiment_name 

        self.mri_input_dir = PATH_TO_EXPERIMENTS_INPUTS + experiment_family + "/"
        self.param_scripts_dir = PATH_TO_EXPERIMENTS_SCRIPTS + experiment_family + "/"
        self.app_trace_file_path = ""

        self.run_simulations = "1"
        self.run_post_proc = f"{int(is_full_postproc)}" 
        self.create_timeseires = f"{int(is_full_postproc)}" 
        self.create_plots = f"{int(is_full_postproc)}"
        self.delete_current = "0"

    def execute(self, ssird_sim_dur, dctcp_sim_dur):
        logger.info("\n=====")
        logger.info("Execute experiment " + self.experiment_name)
        logger.info(f'Flags: {self.run_simulations}, {self.run_post_proc}, {self.create_timeseires}, {self.create_plots}, {self.delete_current}')
        logger.info("ssird_sim_duration={:f}; dctcp_sim_duration={:f}".format(ssird_sim_dur, dctcp_sim_dur))

        self.prep_experiment_input(self.src, self.dst, self.num_byteloads, self.byteload_size_B, self.inter_byteload_period_us)
        ssird_sim_script_path, dctcp_sim_script_path = self.prep_experiment_spec_scripts(ssird_sim_duration=ssird_sim_dur, dctcp_sim_duration=dctcp_sim_dur, experiment_name=self.experiment_name)
        ssird_fct = -1
        dctcp_fct = -1
        load_gbps_measured = -1
        for proto in self.proto_names:
            app_trace_file_path = f"{PATH_TO_SIM_RESULTS}{proto}-{self.experiment_name}/data/{proto}/{CLIENT_INJECTION_RATE_GBPS}/applications_trace.str"
            if proto == SSIRD_PROTO_NAME:
                self.run_experiment(proto, ssird_sim_script_path, f"{PATH_TO_SIM_COORD}outputs/ssird_{self.experiment_name}.out")
                ssird_fct, load_gbps_measured = self.process_results_fct(app_trace_file_path, proto)
                logger.info(f"SSIRD FCT: {ssird_fct} ms, Load: {load_gbps_measured} Gbps")

            if proto == DCTCP_PROTO_NAME:
                self.run_experiment(proto, dctcp_sim_script_path, f"{PATH_TO_SIM_COORD}outputs/{DCTCP_PROTO_NAME}-{self.experiment_name}.out")
                dctcp_fct, load_gbps_measured = self.process_results_fct(app_trace_file_path, proto)
                logger.info(f"DCTCP FCT: {dctcp_fct} ms, Load: {load_gbps_measured} Gbps")

        return ssird_fct, dctcp_fct, load_gbps_measured
        
    def prep_experiment_input(self, src, dst, num_byteloads, byteload_size_B, inter_byteload_period_us):
        logger.info("-----")
        logger.info("Preparing experiment input MRIs")
        try:
            logger.info("### Creating MRI inputs parent dir: " + self.mri_input_dir)
            Path(self.mri_input_dir).mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            logger.info("File " + self.mri_input_dir + " aready exists.")
        
        mri = ManualReqInterval(self.mri_input_dir, self.experiment_name)
        mri_filepath = mri.create_p2p_mri(src, dst, num_byteloads, byteload_size_B, inter_byteload_period_us)
        return mri_filepath

    def prep_experiment_spec_scripts(self, ssird_sim_duration, dctcp_sim_duration, experiment_name):
        logger.info("-----")
        logger.info("Preparing experiment spec scripts")
        try:
            logger.info("### Creating spec scripts parent dir: " + self.param_scripts_dir)
            Path(self.param_scripts_dir).mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            logger.info("#### WARNING: File " + self.param_scripts_dir + " aready exists.")

        sim_script = SimSpecScript(self.param_scripts_dir, self.experiment_name) 
        mri_relative_path = "{}{}/{}.csv".format(MRI_RELATIVE_PATH, self.experiment_family, experiment_name)
        ssird_sim_script_path = sim_script.create_ssird_noburst_params_script(mri_relative_path, ssird_sim_duration)
        dctcp_sim_script_path = sim_script.create_dctcp_noburst_params_script(mri_relative_path, dctcp_sim_duration)

        return ssird_sim_script_path, dctcp_sim_script_path

    def run_experiment(self, proto_name, sim_script_path, sim_output_path):
        logger.info("-----")
        logger.info("Running experiment for " + proto_name)
        logger.info(f"### Script:{sim_script_path}")
        logger.info(f"### Output:{sim_output_path}")
        try:
            result = subprocess.run(
                [f"{PATH_TO_SIM_COORD}run", sim_script_path, self.run_simulations, self.run_post_proc, self.create_timeseires, self.create_plots, self.delete_current],
                cwd=f"{PATH_TO_SIM_COORD}",
                check=True,
                text=True,
                capture_output=True       
            )
            with open(sim_output_path, "w") as f:
                f.write(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.info(f"Script failed with exit code {e.returncode}")
            logger.info("Error output:", e.stderr)
            sys.exit(1)
        except FileNotFoundError:
            logger.error("The file was not found")
        except IOError:
            logger.error("An error occurred while reading the file")

    def process_results_fct(self, app_trace_file_path, proto):
        logger.info("Processing results")
        logger.info(app_trace_file_path)
        flow_trace_event_queue = self.read_app_trace_file(app_trace_file_path)
        fct = self.get_full_flow_duration(flow_trace_event_queue, proto) 
        measured_load_gbps = self.get_measured_load_gbps(flow_trace_event_queue)
        return fct, measured_load_gbps

    def read_app_trace_file(self, app_trace_file_path):
        flow_trace_event_queue = []
        try:
            with open(app_trace_file_path, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    flow_trace_event = FlowTraceEvent.read_flow_trace_from_str(line)
                    flow_trace_event_queue.append(flow_trace_event)
            return flow_trace_event_queue
        except FileNotFoundError:
            logger.error("The file was not found")
        except IOError:
            logger.error("An error occurred while reading the file")

    def get_full_flow_duration(self, flow_trace_event_queue, proto):
        ''' This mtd calculates FCT using timestamps '''

        srq_events = [e for e in flow_trace_event_queue if (e.get_event() == FlowTraceEvent.SRQ_EVENT)]
        rrq_events = [e for e in flow_trace_event_queue if (e.get_event() == FlowTraceEvent.RRQ_EVENT)]

        logger.info(f"num of byteloads: {self.num_byteloads}, num of srq_events: {len(srq_events)}, num of rrq_events {len(rrq_events)}")

        # # TODO: these assertions only work for fully-intermittent flows
        # assert(len(srq_events) == len(rrq_events))
        # assert(num_of_byteloads == len(srq_events))
        # assert(num_of_byteloads == len(rrq_events))

        # TODO: is testing for now, remove if adaptive batching feature is implemented in the sim.
        logger.debug(f"num of srq events: {len(srq_events)}, num of byteloads: {self.num_byteloads}, diff = {self.num_byteloads - len(srq_events)}")
        assert(len(srq_events) == self.num_byteloads)

        first_trace = flow_trace_event_queue[0]
        assert(first_trace.get_event() == FlowTraceEvent.SRQ_EVENT)
        final_trace = flow_trace_event_queue[len(flow_trace_event_queue) - 1]

        assert(final_trace.get_event() == FlowTraceEvent.RRQ_EVENT)
        expected_total_flow_size_B = self.num_byteloads * self.byteload_size_B
        if proto == SSIRD_PROTO_NAME:
            # mirror treatment of hypersmall byteloads by r2p2-app.cc
            if self.byteload_size_B < 4 : expected_total_flow_size_B = self.num_byteloads * 4
            logger.debug(f"final rrq req_size = {final_trace.get_req_size()}, flow size = {expected_total_flow_size_B}, diff = {expected_total_flow_size_B - final_trace.get_req_size()}")
            assert(final_trace.get_req_size() == expected_total_flow_size_B)
        if proto == DCTCP_PROTO_NAME:
            assert(len(srq_events) == len(rrq_events))
            accumulated_rrq_reqs_size_B = 0
            for e in rrq_events:
                accumulated_rrq_reqs_size_B += e.get_req_size()
            assert(accumulated_rrq_reqs_size_B == expected_total_flow_size_B)

        return final_trace.get_timestamp() - first_trace.get_timestamp()

    def get_measured_load_gbps(self, flow_trace_event_queue):
        # returns in Gbps
        # here we only use n-1 out of n events to calc throughput:
        srq_events = [e for e in flow_trace_event_queue if e.get_event() == FlowTraceEvent.SRQ_EVENT]
        assert(self.num_byteloads == len(srq_events))
        if self.num_byteloads == 1:
            # logging.debug(f"NB: srq event count = {len(srq_events)}, not enough events to measure app throughput")  
            # return -1
            print(self.num_byteloads, self.byteload_size_B, self.inter_byteload_period_us)
            return (self.byteload_size_B * 8 / (self.inter_byteload_period_us * pow(10,-6))) * pow(10,-9)
        total_duration = srq_events[len(srq_events)-2].get_timestamp() - srq_events[0].get_timestamp()
        total_data_B = 0 
        for i in range(0, len(srq_events)-2):
            total_data_B += srq_events[i].get_req_size()
        return (total_data_B * 8 / total_duration) * pow(10,-9)

    @staticmethod
    def get_sim_duration(num_byteloads, inter_byteload_period_us, multiplication_factor):
        return multiplication_factor * num_byteloads * inter_byteload_period_us * ManualReqInterval.TIME_STEP_S

    @staticmethod
    def get_experiment_name(num_byteloads, byteload_size_B, inter_byteload_period_us):
        return "{}#-{}B-{}us".format(num_byteloads, byteload_size_B, inter_byteload_period_us)

'''
Is the ideal fct of 1 byteload without any proto-related delays (no credit req, no conn est)
Returned value is in seconds.
'''
def get_ideal_fct_s_exact(link_speed_bps, byteload_size_B, num_byteload_injections, inter_byteload_interval_s):
    data_rtt_s = (byteload_size_B * 8) / float(link_speed_bps)
    if (inter_byteload_interval_s < data_rtt_s):
        # All SRQs will combine together into a uninterrupted flow.
        logger.debug(f"Ideal Fct Calc: Overlap! Interval={inter_byteload_interval_s}; Data RTT={data_rtt_s}")
        return num_byteload_injections * byteload_size_B * 8 / float(link_speed_bps)
    else:
        # SRQs will be separated by gaps; each SRQ will have its own RTT.
        return (num_byteload_injections - 1) * inter_byteload_interval_s + byteload_size_B * 8 / float(link_speed_bps) 

def get_ideal_fct_s(link_speed_bps, byteload_size_B, num_byteload_injections, inter_byteload_interval_s):
    theoretical_throughput_bps = min((byteload_size_B * 8) / float(inter_byteload_interval_s), link_speed_bps)
    flow_size_b = num_byteload_injections * byteload_size_B * 8
    ideal_fct = flow_size_b / theoretical_throughput_bps
    return ideal_fct    

def init_logs(output_path):
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler(output_path, mode='w'),
            logging.StreamHandler()
        ]
    )

def fct_vs_load_experiment_vary_interval(is_full_postproc=True, title_addendum=""):
    '''
    BUG BUG_01-related: 
    30/06/2025:
        SSIRD seems to not work for 100B, 1500B byteloads (replies not issued correctly), is cuz of a bug in how Server tracks req_pkts_expected & req_pkts_received. The former is not updated properly.
        But SSIRD works for 1000B and 10,000B, so we can overlook this for now.
    '''
    experiment_family = f"FCT_Vary_Time_Interval_Size{title_addendum}"
    proto_names = [SSIRD_PROTO_NAME, DCTCP_PROTO_NAME]
    # proto_names = [SSIRD_PROTO_NAME]

    src = 0
    dst = 1
    num_byteloads = 5
    byteload_size_B = int(1000000/8) # 1/8MB

    init_logs(output_path=f"experiment_output/{FctExperiment.get_experiment_name(num_byteloads, byteload_size_B, "variable_")}{title_addendum}.log")

    # inter_byteload_period_us_list = [10, 50, 100, 500, 1000, 5000] # 10000us causes sim to be killed
    inter_byteload_period_us_list = [1000, 500, 100, 50, 10]
    num_of_experiments = len(inter_byteload_period_us_list)

    sim_dur_list = [FctExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us_list[0], 1),   # for 1000us interval
                    FctExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us_list[1], 1),   # for 500us interval
                    FctExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us_list[2], 1),   # for 100us interval
                    FctExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us_list[3], 1),   # for 50us interval
                    FctExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us_list[4], 1.5)]  # for 10us interval

    ssird_sim_dur_list = sim_dur_list
    dctcp_sim_dur_list = sim_dur_list
    # ssird_sim_dur_list = [FctExperiment.get_sim_duration(num_byteloads, p, 10) for p in inter_byteload_period_us_list]
    # dctcp_sim_dur_list = [FctExperiment.get_sim_duration(num_byteloads, p, 10) for p in inter_byteload_period_us_list]

    logger.info(f"Time Periods: {inter_byteload_period_us_list}")
    logger.info(f"Num Byteloads: {num_byteloads}")
    logger.info(f"Byteload Size: {byteload_size_B} Bytes")
    logger.info(f"Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"Sim duration (DCTCP): {dctcp_sim_dur_list}")

    ideal_fct_list = [get_ideal_fct_s(LINK_SPEED_BITS_PER_SEC, byteload_size_B, num_byteloads, p_us*pow(10,-6)) for p_us in inter_byteload_period_us_list]
    ideal_fct_list_old = [get_ideal_fct_s_exact(LINK_SPEED_BITS_PER_SEC, byteload_size_B, num_byteloads, p_us*pow(10,-6)) for p_us in inter_byteload_period_us_list]
    print(ideal_fct_list)
    print(ideal_fct_list_old)
    # return
    ssird_fct_list = []
    dctcp_fct_list = []
    load_measured_gbps_list = []

    assert num_of_experiments == len(inter_byteload_period_us_list)
    assert num_of_experiments == len(ideal_fct_list)
    assert num_of_experiments == len(ssird_sim_dur_list)
    assert num_of_experiments == len(dctcp_sim_dur_list)

    for i in range (0, num_of_experiments):
        experiment_name = FctExperiment.get_experiment_name(num_byteloads, byteload_size_B, inter_byteload_period_us_list[i]) + title_addendum
        fct_exp1 = FctExperiment(experiment_family, experiment_name, proto_names, src, dst, num_byteloads, byteload_size_B, inter_byteload_period_us_list[i], is_full_postproc) 
        ssird_fct, dctcp_fct, load_measured_gbps = fct_exp1.execute(ssird_sim_dur=ssird_sim_dur_list[i], dctcp_sim_dur=dctcp_sim_dur_list[i]) 
        ssird_fct_list.append(ssird_fct)
        dctcp_fct_list.append(dctcp_fct)
        load_measured_gbps_list.append(load_measured_gbps)

    logger.info(f"Time Periods: {inter_byteload_period_us_list}")
    logger.info(f"Num Byteloads: {num_byteloads}")
    logger.info(f"Byteload Size: {byteload_size_B} Bytes")
    logger.info(f"Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"Sim duration (DCTCP): {dctcp_sim_dur_list}")
    logger.info(f"Load Measured (Gbps): {load_measured_gbps_list}")
    logger.info(f"* IDEAL FCT: {ideal_fct_list}")
    logger.info(f"* IDEAL FCT (old): {ideal_fct_list_old}")
    logger.info(f"* SSIRD FCT: {ssird_fct_list}")
    logger.info(f"* DCTCP FCT: {dctcp_fct_list}")

    assert num_of_experiments == len(ssird_fct_list)
    assert num_of_experiments == len(dctcp_fct_list)

'''
Sweep application pacing rate of byteloads from 1% BW to 100% BW capacity. (i.e. 1GBps to 100GBps)
'''
def fct_vs_load_experiment_vary_byteloadsize(is_full_postproc=True, title_addendum=""):
    experiment_family = f"FCT_Vary_Byteload_Size{title_addendum}"
    proto_names = [SSIRD_PROTO_NAME, DCTCP_PROTO_NAME]
    # proto_names = [SSIRD_PROTO_NAME]

    src = 0
    dst = 1
    num_byteloads = 10
    inter_byteload_period_us = 100 # is 0.1ms

    KILOBYTE = 1000
    # byteload_size_KB_list = [10000/8]
    byteload_size_KB_list = [100/8, 500/8, 1000/8, 5000/8, 10000/8] # 100/8KB to 10/8MB
    byteload_size_B_list = [int(n * KILOBYTE) for n in byteload_size_KB_list] 
    num_of_experiments = len(byteload_size_B_list)

    # sim_dur_list = [FctExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, 1.5)]   # for 5000KB
    sim_dur_list = [FctExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, 1),   # for 100/8KB
                    FctExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, 1),   # for 500/8KB
                    FctExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, 1),   # for 1000/8KB
                    FctExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, 1),   # for 5000/8KB
                    FctExperiment.get_sim_duration(num_byteloads, inter_byteload_period_us, 1.5)]  # for 10000/8KB

    ssird_sim_dur_list = sim_dur_list
    dctcp_sim_dur_list = sim_dur_list

    init_logs(output_path=f"experiment_output/{FctExperiment.get_experiment_name(num_byteloads, "variable_", inter_byteload_period_us)}{title_addendum}.log")

    load_gbps_theoretical = [(bytes*8)/(inter_byteload_period_us * pow(10, -6) * pow(10, 9)) for bytes in byteload_size_B_list]
    logger.info(f"Time Period: {inter_byteload_period_us}")
    logger.info(f"Num Byteloads: {num_byteloads}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Load Gbps theoretical: {load_gbps_theoretical}")
    logger.info(f"* Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"* Sim duration (DCTCP): {dctcp_sim_dur_list}")

    ideal_fct_list = [get_ideal_fct_s(LINK_SPEED_BITS_PER_SEC, byteload_size_B, num_byteloads, inter_byteload_period_us*pow(10,-6)) for byteload_size_B in byteload_size_B_list]
    ideal_fct_list_old = [get_ideal_fct_s_exact(LINK_SPEED_BITS_PER_SEC, byteload_size_B, num_byteloads, inter_byteload_period_us*pow(10,-6)) for byteload_size_B in byteload_size_B_list]
    print(ideal_fct_list)
    print(ideal_fct_list_old)
    # return
    ssird_fct_list = []
    dctcp_fct_list = []

    assert num_of_experiments == len(byteload_size_B_list)
    assert num_of_experiments == len(ideal_fct_list)
    assert num_of_experiments == len(ssird_sim_dur_list)
    assert num_of_experiments == len(dctcp_sim_dur_list)

    load_gbps_measured_list = []
    for i in range(0, num_of_experiments):
        experiment_name = FctExperiment.get_experiment_name(num_byteloads, byteload_size_B_list[i], inter_byteload_period_us) + title_addendum
        fct_exp1 = FctExperiment(experiment_family, experiment_name, proto_names, src, dst, num_byteloads, byteload_size_B_list[i], inter_byteload_period_us, is_full_postproc) 
        ssird_fct, dctcp_fct, load_gbps_measured = fct_exp1.execute(ssird_sim_dur=ssird_sim_dur_list[i], dctcp_sim_dur=dctcp_sim_dur_list[i]) 
        ssird_fct_list.append(ssird_fct)
        dctcp_fct_list.append(dctcp_fct)
        load_gbps_measured_list.append(load_gbps_measured)

    logger.info(f"Time Period: {inter_byteload_period_us}")
    logger.info(f"Num Byteloads: {num_byteloads}")
    logger.info(f"Byteload Size (Bytes): {byteload_size_B_list}")
    logger.info(f"Load Gbps theoretical: {load_gbps_theoretical}")
    logger.info(f"Load Gbps measured: {load_gbps_measured_list}")
    logger.info(f"Sim duration (SSIRD): {ssird_sim_dur_list}")
    logger.info(f"Sim duration (DCTCP): {dctcp_sim_dur_list}")
    logger.info(f"* IDEAL FCT: {ideal_fct_list}")
    logger.info(f"* IDEAL FCT (old): {ideal_fct_list_old}")
    logger.info(f"* SSIRD FCT: {ssird_fct_list}")
    logger.info(f"* DCTCP FCT: {dctcp_fct_list}")

    assert num_of_experiments == len(ssird_fct_list)
    assert num_of_experiments == len(dctcp_fct_list)

if __name__ == "__main__":
    # TODO: update each experiment code to write to their own files
    # fct_vs_load_experiment_vary_interval(is_full_postproc=True)
    fct_vs_load_experiment_vary_byteloadsize(is_full_postproc=False)