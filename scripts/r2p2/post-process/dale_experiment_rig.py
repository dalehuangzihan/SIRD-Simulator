import sys, subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import csv
import datetime
import logging
import collections
import math

# for thread pool
# MAX_WORKERS = 4 
MAX_WORKERS = 12 # NOTE: use this for batch1 server

MIN_BYTELOAD_INTERVAL_US = 0.001 # is 1ns

# Common experiment param; value is meaningful only when req_interval_distr is not 'manual'
CLIENT_INJECTION_RATE_GBPS = "60"
DCTCP_ECN_MARKING_THRESHOLD = "50"
LINK_SPEED_BITS_PER_SEC = 100 * pow(10,9) * 8 # 100Gbps

SSIRD_PROTO_NAME = "SSIRD"
DCTCP_PROTO_NAME = f"DCTCP-{DCTCP_ECN_MARKING_THRESHOLD}"

# PATH_TO_SIRD_SIM = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/"
PATH_TO_SIRD_SIM = "/data/dh1723/SIRD-Simulator/" # NOTE: use this for batch1 server
PATH_TO_SIM_COORD = PATH_TO_SIRD_SIM + "scripts/r2p2/coord/"
PATH_TO_POST_PROCESS = PATH_TO_SIRD_SIM + "scripts/r2p2/post-process/"
PATH_TO_SIM_RESULTS = PATH_TO_SIM_COORD + "results/"
PATH_TO_EXPERIMENTS = PATH_TO_SIM_COORD + "config/"
PATH_TO_EXPERIMENTS_SCRIPTS = PATH_TO_EXPERIMENTS + "dale_experiments/"
PATH_TO_EXPERIMENT_SCRIPT_TEMPLATES = PATH_TO_EXPERIMENTS + "dale_experiment_script_templates/"
MRI_RELATIVE_PATH = "dale_experiments/"
PATH_TO_EXPERIMENTS_INPUTS = PATH_TO_EXPERIMENTS + "manual-req-intervals/" + MRI_RELATIVE_PATH
APP_TRACE_PATHS_BACKUP_PATH = PATH_TO_POST_PROCESS + "experiment_app_trace_paths/"
LOGS_REL_PATH = "experiment_output/" # is relative to post-process/ dir

LOG_LEVEL_1 = 1
LOG_LEVEL_2 = 2
LOG_LEVEL_6 = 6

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

        # assert(byteload_interval_us >= 1)
        # assert(byteload_interval_us*10%10 == 0)
        assert(byteload_interval_us >= 0.001) # must be at least 1ns

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

        # assert(num_byteloads_per_flow > 1) # we want at least 2 byteloads per flow
        self.init_flows()

    def init_flows(self):
        for i in range(0, self.num_flows):
            flow_start_time_us = self.flow_start_times_us_list[i]
            self.flows_list.append(Flow(self.src, self.dst, i, self.num_byteloads_per_flow, self.byteload_size_B, self.byteload_interval_us, flow_start_time_us))
        logger.debug(f"num flows: {len(self.flows_list)}")
    
    def serialise_flows_to_byteloads(self):
        if len(self.flows_list) < 1:
            logging.error(f"Flows list is empty (size={len(self.flows_list)})!")
            return
        serialised_byteloads_list = [] 
        for flow in self.flows_list:
            byteloads_list = flow.byteloads_list
            assert(len(byteloads_list) > 0)
            serialised_byteloads_list.extend(byteloads_list) 
        serialised_byteloads_list.sort(key = lambda b : b.absolute_timestamp_us)
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

class ManualReqInterval():
    # is in seconds; is 1us
    MICROSECOND_S = 0.000001
    MRI_START_TIME_S = MICROSECOND_S
    
    def __init__(self, parent_dir, experiment_name):
        self.parent_dir = parent_dir
        self.experiment_name = experiment_name

    def create_p2p_mri(self, multiflow_obj_list):
        # NOTE: each multiflow obj is for a unique sender-recvr pair
        '''
        Creates MRI csv file of multiple flows of the same kind between a single src, dst pair.
        '''
        mri_filepath = self.get_mri_filepath(self.parent_dir, self.experiment_name)
        mri_byteloads_spec_list = []

        for multiflow_obj in multiflow_obj_list:
            src = multiflow_obj.src
            dst = multiflow_obj.dst

            mri_byteloads_spec = []    
            mri_byteloads_spec.append(str(src))

            serialised_byteloads_list = multiflow_obj.serialise_flows_to_byteloads()
            for i in range(0, len(serialised_byteloads_list)):
                bl = serialised_byteloads_list[i]
                time_spec = bl.relative_interval_us * self.MICROSECOND_S
                if i == 0: time_spec += self.MRI_START_TIME_S 
                byteload_str = "{:.10f}|{}|{}|{}".format(time_spec, str(dst), bl.size_B, bl.flow_id)
                mri_byteloads_spec.append(byteload_str)
            mri_byteloads_spec_list.append(mri_byteloads_spec)

        self.mri_list_to_csv(mri_byteloads_spec_list, mri_filepath)
        return mri_filepath

    @staticmethod
    def get_mri_filepath(parent_dir, experiment_name):
        return parent_dir + experiment_name + ".csv"

    @staticmethod
    def mri_list_to_csv(mri_byteloads_spec_list, mri_filepath):
        with open(mri_filepath, 'w') as mri_file:
            wr = csv.writer(mri_file, quoting=csv.QUOTE_NONE)
            for mri_byteloads_spec in mri_byteloads_spec_list:
                wr.writerow(mri_byteloads_spec)

class SimSpecScript:
    PATH_TO_SSIRD_TEMPLATE_NOBURST = PATH_TO_EXPERIMENT_SCRIPT_TEMPLATES + "template-ssird-2host-p2p-noburst.sh"
    PATH_TO_DCTCP_TEMPLATE_NOBURST = PATH_TO_EXPERIMENT_SCRIPT_TEMPLATES + "template-dctcp-2host-p2p-noburst.sh"

    MANUAL_REQ_INTERVAL_FILE_L = "manual_req_interval_file_l"
    DURATION_MODIFIER_L = "duration_modifier_l"
    GLOBAL_DEBUG = "global_debug"
    DCTCP_K_L = "dctcp_k_l"
    SIMULATION_NAME_L = "simulation_name_l"

    def __init__(self, parent_dir, experiment_name):
        self.parent_dir = parent_dir
        self.experiment_name = experiment_name
    
    def create_ssird_noburst_params_script(self, mri_relative_path, sim_duration, log_level):
        script_filepath = self.parent_dir + f"{SSIRD_PROTO_NAME}-" + self.experiment_name + ".sh"
        with open(self.PATH_TO_SSIRD_TEMPLATE_NOBURST) as template, open(script_filepath, 'w') as fout:
            lines_in = template.readlines()
            for i in range(len(lines_in)):
                line_out = lines_in[i]
                if self.MANUAL_REQ_INTERVAL_FILE_L in line_out:
                    line_out = "{}='{}'\n".format(self.MANUAL_REQ_INTERVAL_FILE_L, mri_relative_path)
                elif self.DURATION_MODIFIER_L in line_out:
                    line_out = "{}='{:f}'\n".format(self.DURATION_MODIFIER_L, sim_duration)
                elif self.GLOBAL_DEBUG in line_out:
                    line_out = "{}='{}'\n".format(self.GLOBAL_DEBUG, log_level)
                fout.write(line_out)
        return script_filepath

    def create_dctcp_noburst_params_script(self, mri_relative_path, sim_duration, log_level):
        script_filepath = self.parent_dir + f"{DCTCP_PROTO_NAME}-" + self.experiment_name + ".sh"
        with open(self.PATH_TO_DCTCP_TEMPLATE_NOBURST) as template, open(script_filepath, 'w') as fout:
            lines_in = template.readlines()
            for i in range(len(lines_in)):
                line_out = lines_in[i]
                if self.MANUAL_REQ_INTERVAL_FILE_L in line_out:
                    line_out = "{}='{}'\n".format(self.MANUAL_REQ_INTERVAL_FILE_L, mri_relative_path)
                elif self.DURATION_MODIFIER_L in line_out:
                    line_out = "{}='{:f}'\n".format(self.DURATION_MODIFIER_L, sim_duration)
                elif self.GLOBAL_DEBUG in line_out:
                    line_out = "{}='{}'\n".format(self.GLOBAL_DEBUG, log_level)
                elif self.DCTCP_K_L in line_out:
                    line_out = "{}='{}'\n".format(self.DCTCP_K_L, DCTCP_ECN_MARKING_THRESHOLD)
                elif self.SIMULATION_NAME_L in line_out:
                    line_out = "{}='{}'\n".format(self.SIMULATION_NAME_L, DCTCP_PROTO_NAME)
                fout.write(line_out)
        return script_filepath

class ExperimentResults:
    def __init__(self, ssird_fct=None, dctcp_fct=None, gdpt_gbps_measured_ssird=None, gdpt_gbps_measured_dctcp=None, gdnpt_gbps_measured_per_flow_list_ssird=None, gdpt_gbps_measured_per_flow_list_dctcp=None):
        self.ssird_fct = ssird_fct
        self.dctcp_fct = dctcp_fct

        self.gdpt_gbps_measured_ssird = gdpt_gbps_measured_ssird
        self.gdpt_gbps_measured_dctcp = gdpt_gbps_measured_dctcp

        self.gdpt_gbps_measured_per_flow_list_ssird = gdnpt_gbps_measured_per_flow_list_ssird
        self.gdpt_gbps_measured_per_flow_list_dctcp = gdpt_gbps_measured_per_flow_list_dctcp

class ExperimentOutputRaw:
    '''
    Is the raw un-processed experiment outputs
    '''
    def __init__(self, exp_id, experiment_family, experiment_name, app_trace_file_path, proto, src_dst_pairs_list, num_flows, num_byteloads, byteload_size_B):
        self.exp_id = exp_id
        self.experiment_family = experiment_family
        self.experiment_name = experiment_name
        self.proto = proto
        self.src_dst_pairs_list = src_dst_pairs_list
        self.app_trace_file_path = app_trace_file_path

        self.num_flows = num_flows
        self.num_byteloads = num_byteloads
        self.byteload_size_B = byteload_size_B

    def process_results_fct(self):
        logger.info(f"Processing results from {self.app_trace_file_path}")
        
        d = {}
        for src, dst in self.src_dst_pairs_list:
            for flow_id in range(0, self.num_flows):
                src_dst_pair = sorted([src,dst]) # each src-dst pair is unique, so both h0->h1 and h1->h0 flows should be treated as under the same src-dst pair
                dict_key = (src_dst_pair[0], src_dst_pair[1], flow_id)
                d[dict_key] = FlowStats(self.proto, src, dst, flow_id, self.num_byteloads, self.byteload_size_B)
        flow_stats_dict = collections.OrderedDict(sorted(d.items()))
        del d

        total_bytes_sent_B = 0
        total_bytes_sent_until_penultimate_srq_B = 0
        overall_srq_start_time_s = math.inf
        overall_final_srq_timestamp_s = None

        try:
            with open(self.app_trace_file_path, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    flow_trace_event = FlowTraceEvent.read_flow_trace_from_str(line)
                    flow_id = flow_trace_event.get_app_level_id()
                    src = flow_trace_event.get_local_addr()
                    dst = flow_trace_event.get_remote_addr()
                    src_dst_pair = sorted([src,dst]) # each src-dst pair is unique, so both h0->h1 and h1->h0 flows should be treated as under the same src-dst pair
                    dict_key = (src_dst_pair[0], src_dst_pair[1], flow_id)
                    flow_stats_dict.get(dict_key).update_flow_stats(flow_trace_event)

                    if (flow_trace_event.get_event() == FlowTraceEvent.SRQ_EVENT):
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
        if (overall_final_srq_timestamp_s - overall_srq_start_time_s > 0):
            measured_total_gdpt_gbps = (total_bytes_sent_until_penultimate_srq_B * 8) / (overall_final_srq_timestamp_s - overall_srq_start_time_s) * pow(10,-9)
        else:
            measured_total_gdpt_gbps = -1

        fct_list = []
        measured_app_gdpt_gbps_per_flow_list = []
        for _, flow_stats_obj in flow_stats_dict.items():
            flow_stats_obj.check_flow_stats()
            fct_list.append(flow_stats_obj.get_fct_s())
            measured_app_gdpt_gbps_per_flow_list.append(flow_stats_obj.get_measured_app_gdpt_for_flow_gbps())

        return fct_list, measured_total_gdpt_gbps, measured_app_gdpt_gbps_per_flow_list

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
    def get_local_addr(self):
        return int(self.local_addr)
    def get_remote_addr(self):
        return int(self.remote_addr)

    @staticmethod
    def read_flow_trace_from_str(str_line):
        tokens = str_line.split(" ")
        assert(len(tokens) == 12)
        return FlowTraceEvent(tokens[0], tokens[1], tokens[2], tokens[3], tokens[4], tokens[5], tokens[6], tokens[7], tokens[8], tokens[9], tokens[10], tokens[11])

class FlowStats:
    def __init__(self, proto, src, dst, flow_id, num_byteloads, byteload_size_B):
        self.proto = proto
        self.src = src
        self.dst = dst
        self.flow_id = flow_id
        self.num_byteloads = num_byteloads
        self.byteload_size_B = byteload_size_B if byteload_size_B > 4 else 4 # is the actual byteload size as per ssird sim
        
        self.num_srq = 0
        self.num_rrq = 0
        self.start_time_s = math.inf
        self.end_time_s = -1
        self.total_bytes_sent_B = 0
        self.total_bytes_recv_B = 0

		# store the stats accumulated up until the (n-1)th srq.
        self.final_srq_timestamp = None
        self.total_bytes_sent_until_penultimate_srq_B = None
        
        self.first_event_name = None 
        self.final_event_name = None

    def update_flow_stats(self, flow_trace_event):
        assert(self.flow_id == flow_trace_event.get_app_level_id())

        self.start_time_s = min(self.start_time_s, flow_trace_event.get_timestamp())
        self.end_time_s = max(self.end_time_s, flow_trace_event.get_timestamp())

        trace_event_name = flow_trace_event.get_event()
        if (self.num_srq == 0 and self.num_rrq == 0): self.first_event_name = trace_event_name
        self.final_event_name = trace_event_name

        if (trace_event_name == FlowTraceEvent.SRQ_EVENT):
            self.num_srq += 1
            self.total_bytes_sent_until_penultimate_srq_B = self.total_bytes_sent_B
            self.total_bytes_sent_B += flow_trace_event.get_req_size()
            self.final_srq_timestamp = flow_trace_event.get_timestamp()

        elif (trace_event_name == FlowTraceEvent.RRQ_EVENT):
            self.num_rrq += 1
            if (self.proto == SSIRD_PROTO_NAME):
                # each ssird rrq shows cumulative recved-data size that progressively increases as data chunks reach the receiver-side app
                self.total_bytes_recv_B = flow_trace_event.get_req_size()
            elif (self.proto == DCTCP_PROTO_NAME):
                self.total_bytes_recv_B += flow_trace_event.get_req_size()
            else:
                logger.error(f"Unrecognised proto name {self.proto}")

        else:
            logger.error(f"Unrecognised flow trace event {trace_event_name}")

    def check_flow_stats(self):
        logger.info(f"Flow {self.flow_id}:: num of byteloads: {self.num_byteloads}, num srq events: {self.num_srq}, num rrq events: {self.num_rrq}")

        assert(self.num_srq == self.num_byteloads) # TODO: remove assertion if adaptive batching feature is implemented
        assert(self.first_event_name == FlowTraceEvent.SRQ_EVENT)
        
        if (self.final_event_name != FlowTraceEvent.RRQ_EVENT):
            logger.error(f"Flow {self.flow_id}: Final event was {self.final_event_name} instead of {FlowTraceEvent.RRQ_EVENT}!")        

        if (self.proto == DCTCP_PROTO_NAME and self.num_srq != self.num_rrq):
            logger.error(f"DCTCP: Missing rrq event(s)! diff: {self.num_srq - self.num_rrq}")

        expected_flow_size_B = self.num_byteloads * self.byteload_size_B 
        logger.debug(f"Flow {self.flow_id}:: first_event_name: {self.first_event_name}, final_event_name: {self.final_event_name}, expected_data_B: {expected_flow_size_B}, recv_data_B: {self.total_bytes_recv_B}")
        if (self.total_bytes_recv_B != expected_flow_size_B):
            logger.error(f"Missing data! flow_id: {self.flow_id}: total bytes recv: {self.total_bytes_recv_B}, expected flow size = {expected_flow_size_B}, diff = {expected_flow_size_B - self.total_bytes_recv_B}")

    def get_fct_s(self):
        return self.end_time_s - self.start_time_s
    
    def get_measured_app_gdpt_for_flow_gbps(self):
        # returns in Gbps
        # here we use the n-1 gaps between the n srq events to calc throughput:
        if self.num_byteloads == 1: return None 
        send_duration_s = self.final_srq_timestamp - self.start_time_s 
        if (send_duration_s > 0):
            return (self.total_bytes_sent_until_penultimate_srq_B * 8) / send_duration_s * pow(10,-9)
        else:
            return -1 

class Experiment():

    def __init__(self, experiment_family, experiment_name, proto, src_dst_pairs_list, flow_start_times_us_list, num_byteloads, byteload_size_B, inter_byteload_period_us, is_full_postproc=False):
        self.experiment_family = experiment_family
        self.proto = proto

        self.src_dst_pairs_list = src_dst_pairs_list
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

        self.flow_start_times_us_list = flow_start_times_us_list
        self.num_flows = len(flow_start_times_us_list)

    def run(self, exp_id, ssird_sim_dur_l, dctcp_sim_dur_l, log_level):
        logger.info("\n=====\nExecute experiment " + self.experiment_name)
        logger.info(f'Flags: {self.run_simulations}, {self.run_post_proc}, {self.create_timeseires}, {self.create_plots}, {self.delete_current}')
        logger.info("ssird_sim_duration={:f}; dctcp_sim_duration={:f}".format(ssird_sim_dur_l, dctcp_sim_dur_l))

        self.prep_experiment_input(self.src_dst_pairs_list, self.num_byteloads, self.byteload_size_B, self.inter_byteload_period_us, self.flow_start_times_us_list)
        ssird_sim_script_path, dctcp_sim_script_path = self.prep_experiment_spec_scripts(ssird_sim_duration=ssird_sim_dur_l, dctcp_sim_duration=dctcp_sim_dur_l, experiment_name=self.experiment_name, log_level=log_level)

        outputs_dir = f"{PATH_TO_SIM_COORD}outputs/{self.experiment_family}/"
        Path(outputs_dir).mkdir(parents=True, exist_ok=True)

        app_trace_file_path = f"{PATH_TO_SIM_RESULTS}{self.proto}-{self.experiment_name}/data/{self.proto}/{CLIENT_INJECTION_RATE_GBPS}/applications_trace.str"
        if self.proto == SSIRD_PROTO_NAME:
            self.execute(self.proto, ssird_sim_script_path, f"{outputs_dir}ssird_{self.experiment_name}")
        elif self.proto == DCTCP_PROTO_NAME:
            self.execute(self.proto, dctcp_sim_script_path, f"{outputs_dir}{DCTCP_PROTO_NAME}_{self.experiment_name}")
        else:
            logger.error(f"Unrecognised protocol name '{self.proto}'")

        experiment_results_raw = ExperimentOutputRaw(exp_id, self.experiment_family, self.experiment_name, app_trace_file_path, self.proto, self.src_dst_pairs_list, self.num_flows, self.num_byteloads, self.byteload_size_B)

        return experiment_results_raw

    def prep_experiment_input(self, src_dst_pairs_list, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, flow_start_times_list):
        logger.info("-----\nPreparing experiment input MRIs")
        try:
            logger.info("### Creating MRI inputs parent dir: " + self.mri_input_dir)
            Path(self.mri_input_dir).mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            logger.info("File " + self.mri_input_dir + " aready exists.")
        
        mri = ManualReqInterval(self.mri_input_dir, self.experiment_name)
        multiflow_obj_list = []
        for src, dst in src_dst_pairs_list:
            multiflow_obj = MultiFlow(src, dst, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, flow_start_times_list)  
            multiflow_obj_list.append(multiflow_obj)
        mri_filepath = mri.create_p2p_mri(multiflow_obj_list)
        return mri_filepath

    def prep_experiment_spec_scripts(self, ssird_sim_duration, dctcp_sim_duration, experiment_name, log_level):
        logger.info("-----\nPreparing experiment spec scripts")
        try:
            logger.info("### Creating spec scripts parent dir: " + self.param_scripts_dir)
            Path(self.param_scripts_dir).mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            logger.info("#### WARNING: File " + self.param_scripts_dir + " aready exists.")

        sim_script = SimSpecScript(self.param_scripts_dir, self.experiment_name) 
        mri_relative_path = "{}{}/{}.csv".format(MRI_RELATIVE_PATH, self.experiment_family, experiment_name)
        ssird_sim_script_path = sim_script.create_ssird_noburst_params_script(mri_relative_path, ssird_sim_duration, log_level)
        dctcp_sim_script_path = sim_script.create_dctcp_noburst_params_script(mri_relative_path, dctcp_sim_duration, log_level)

        return ssird_sim_script_path, dctcp_sim_script_path

    def execute(self, proto_name, sim_script_path, sim_output_path):
        logger.info("-----\nRunning experiment for " + proto_name)
        logger.info(f"### Script:{sim_script_path}")
        params_list = [f"{PATH_TO_SIM_COORD}run", sim_script_path, self.run_simulations, self.run_post_proc, self.create_timeseires, self.create_plots, self.delete_current] 
        output_file_path_stdout = f"{sim_output_path}_stdout.out" 
        output_file_path_stderr = f"{sim_output_path}_stderr.out" 
        logger.info(f"### Output path (stdout): {output_file_path_stdout}")
        logger.info(f"### Output path (stderr): {output_file_path_stderr}")
        output_file_stdout = open(output_file_path_stdout, "w")
        output_file_stderr = open(output_file_path_stderr, "w")
        try:
            subprocess.run(
                params_list,
                cwd=f"{PATH_TO_SIM_COORD}",
                check=True,
                text=True,
                stderr=output_file_stderr,
                stdout=output_file_stdout
            )
        except subprocess.CalledProcessError as e:
            logger.info(f"Script failed with exit code {e.returncode}")
            logger.info("Error output:", e.stderr)
            sys.exit(1)
        except FileNotFoundError:
            logger.error("The file was not found")
        except IOError:
            logger.error("An error occurred while reading the file")

    @staticmethod
    def write_app_trace_paths_to_file(proto, experiment_family, num_flows, app_trace_file_paths_list):
        logger.info("-----\nBacking up app trace file paths")
        parent_dir = f"{APP_TRACE_PATHS_BACKUP_PATH}{experiment_family}/{num_flows}flo/"
        Path(parent_dir).mkdir(parents=True, exist_ok=True)
        backup_filepath = parent_dir + f"{proto}_app_traces.txt"
        logger.debug(backup_filepath)
        with open(backup_filepath, 'w') as fout:
            for path_to_app_trace in app_trace_file_paths_list:
                fout.write(f"{path_to_app_trace}\n")

    '''
    TODO: double-check this calculation! if it works, use it instead of the prev sim_dur calculator.
    '''
    @staticmethod
    def get_sim_duration(num_flows, inter_flow_spacing_us, num_byteloads_per_flow, byteload_size_B, inter_byteload_period_us, multiplication_factor=2):
        total_data_B = num_flows * num_byteloads_per_flow * byteload_size_B
        data_send_duration_s = total_data_B * 8 / LINK_SPEED_BITS_PER_SEC
        inter_byteload_spacing_delays_per_flow_s = num_byteloads_per_flow * inter_byteload_period_us * pow(10,-6)
        inter_flow_spacing_delays_s = num_flows * inter_flow_spacing_us * pow(10, -6)
        overall_duration_s = data_send_duration_s + inter_byteload_spacing_delays_per_flow_s + inter_flow_spacing_delays_s
        return overall_duration_s * multiplication_factor

    @staticmethod
    def get_experiment_name(num_flows, num_byteloads, byteload_size_B, inter_byteload_period_us):
        return "{}flo-{}#-{}B-{}ns".format(num_flows, num_byteloads, byteload_size_B, int(inter_byteload_period_us * 1000))

class ExperimentGroup:

    def __init__(self, experiment_family, proto_names_list, src_dst_pairs_list, flow_start_times_us_list, num_byteloads_per_flow_list, byteload_size_B_list, inter_byteload_period_us_list, ssird_sim_dur_list, dctcp_sim_dur_list, is_full_postproc=False, log_level=LOG_LEVEL_2, title_addendum=""):
        self.experiment_family = experiment_family
        self.proto_names_l = proto_names_list
        self.src_dst_pairs_list = src_dst_pairs_list
        self.num_flows = len(flow_start_times_us_list)
        self.flow_start_times_us_list = flow_start_times_us_list
        self.num_byteloads_per_flow_list = num_byteloads_per_flow_list
        self.byteload_size_B_list = byteload_size_B_list
        self.inter_byteload_period_us_list = inter_byteload_period_us_list
        self.is_full_postproc = is_full_postproc
        self.ssird_sim_dur_list = ssird_sim_dur_list
        self.dctcp_sim_dur_list = dctcp_sim_dur_list
        self.title_addendum = title_addendum
        self.log_level = log_level

        # check that all per-flow specification lists have same length
        assert(len(set([
            len(num_byteloads_per_flow_list),
            len(byteload_size_B_list),
            len(inter_byteload_period_us_list)
            ])) == 1)
        self.num_experiments = len(num_byteloads_per_flow_list)

        self.ssird_raw_experiment_results_list = [None] * self.num_experiments
        self.dctcp_raw_experiment_results_list = [None] * self.num_experiments
        self.processed_results_list = []

    def perform_experiment(self):
        self.run_group()
        self.post_process_results()
        return self.generate_overall_experiment_metrics()
    
    def run_group(self):
        logger.info(f"Experiment started at: {datetime.datetime.now()}")
        logger.info("\n##### RUN GROUP #####")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures_list = []

            for exp_id in range(0, self.num_experiments):
                experiment_name = Experiment.get_experiment_name(self.num_flows, self.num_byteloads_per_flow_list[exp_id], self.byteload_size_B_list[exp_id], self.inter_byteload_period_us_list[exp_id]) + self.title_addendum
                for proto in self.proto_names_l:
                    experiment = Experiment(self.experiment_family, experiment_name, proto, self.src_dst_pairs_list, self.flow_start_times_us_list, self.num_byteloads_per_flow_list[exp_id], self.byteload_size_B_list[exp_id], self.inter_byteload_period_us_list[exp_id], self.is_full_postproc) 

                    # submit experiment to thread pool
                    future = executor.submit(
                        experiment.run,
                        exp_id,
                        ssird_sim_dur_l=self.ssird_sim_dur_list[exp_id],
                        dctcp_sim_dur_l=self.dctcp_sim_dur_list[exp_id],
                        log_level=self.log_level
                    ) 
                    futures_list.append((exp_id, future, experiment_name, proto))

            # wait for all experiments to complete and collect results
            for exp_id, future, experiment_name, proto in futures_list:
                try:
                    raw_result = future.result()
                    if raw_result.proto == SSIRD_PROTO_NAME:
                        self.ssird_raw_experiment_results_list[exp_id] = raw_result
                    elif raw_result.proto == DCTCP_PROTO_NAME:
                        self.dctcp_raw_experiment_results_list[exp_id] = raw_result
                    else:
                        logger.error(f"Unrecognised protocol name '{raw_result.proto}' in experiment result! (experiment_name={experiment_name})")
                except Exception as e:
                    logger.error(f"Experiment {experiment_name} failed: {str(e)}")

        if (SSIRD_PROTO_NAME in self.proto_names_l):
            assert(all(r.exp_id == i for r, i in zip(self.ssird_raw_experiment_results_list, range(0, self.num_experiments))))
        if (DCTCP_PROTO_NAME in self.proto_names_l):
            assert(all(r.exp_id == i for r, i in zip(self.dctcp_raw_experiment_results_list, range(0, self.num_experiments))))

        ssird_path_to_app_trace_files_list = [r.app_trace_file_path for r in self.ssird_raw_experiment_results_list if r is not None]
        Experiment.write_app_trace_paths_to_file(SSIRD_PROTO_NAME, self.experiment_family, self.num_flows, ssird_path_to_app_trace_files_list)
        dctcp_path_to_app_trace_files_list = [r.app_trace_file_path for r in self.dctcp_raw_experiment_results_list if r is not None]
        Experiment.write_app_trace_paths_to_file(DCTCP_PROTO_NAME, self.experiment_family, self.num_flows, dctcp_path_to_app_trace_files_list)
        logger.info(f"Simulations ended at: {datetime.datetime.now()}")
    
    def post_process_results(self):
        logger.info("\n##### POST PROCESS RESULTS #####")
        for i in range(0, self.num_experiments):
            logger.info(f"=====\n** Num Byteloads Per Flow: {self.num_byteloads_per_flow_list[i]}, Byteload Size (B): {self.byteload_size_B_list[i]}, Inter-Byteload Interval (us): {self.inter_byteload_period_us_list[i]}, ssird_sim_dur (s): {self.ssird_sim_dur_list[i]}, dctcp_sim_dur (s): {self.dctcp_sim_dur_list[i]}")

            ssird_result = self.ssird_raw_experiment_results_list[i]
            if ssird_result == None:
                logger.error("No results for SSIRD")
                ssird_fct = None
                app_gdpt_gbps_measured_ssird = None
                app_gdpt_gbps_measured_per_flow_list_ssird = None
            else:
                logger.info(f"Processing SIRD results exp_id {ssird_result.exp_id}:: {ssird_result.num_flows}flo-{ssird_result.num_byteloads}#-{ssird_result.byteload_size_B}B")
                ssird_fct, app_gdpt_gbps_measured_ssird, app_gdpt_gbps_measured_per_flow_list_ssird = ssird_result.process_results_fct()
            logger.info(f"SSIRD FCT: {ssird_fct} ms, App Gdpt (overall): {app_gdpt_gbps_measured_ssird} Gbps, App Gdpt (per flow): {app_gdpt_gbps_measured_per_flow_list_ssird}")

            dctcp_result = self.dctcp_raw_experiment_results_list[i]
            if dctcp_result == None:
                logger.error("No results for DCTCP")
                dctcp_fct = None
                gdpt_gbps_measured_dctcp = None
                gdpt_gbps_measured_per_flow_list_dctcp = None
            else:
                logger.info(f"Processing DCTCP results exp_id {dctcp_result.exp_id}:: {dctcp_result.num_flows}flo-{dctcp_result.num_byteloads}#-{dctcp_result.byteload_size_B}B")
                dctcp_fct, gdpt_gbps_measured_dctcp, gdpt_gbps_measured_per_flow_list_dctcp = dctcp_result.process_results_fct()
            logger.info(f"DCTCP FCT: {dctcp_fct} ms, App Gtpt (overall): {gdpt_gbps_measured_dctcp} Gbps, App Gdpt (per flow): {gdpt_gbps_measured_per_flow_list_dctcp}")

            processed_result = ExperimentResults(ssird_fct, dctcp_fct, app_gdpt_gbps_measured_ssird, gdpt_gbps_measured_dctcp, app_gdpt_gbps_measured_per_flow_list_ssird, gdpt_gbps_measured_per_flow_list_dctcp)
            self.processed_results_list.append(processed_result)

    def generate_overall_experiment_metrics(self):
        logger.info("\n##### GENERATE METRICS #####")
        logger.info(f"Experiment family: {self.experiment_family}")
        ssird_fct_list = []
        dctcp_fct_list = []
        gdpt_gbps_measured_list_ssird = []
        gdpt_gbps_measured_list_dctcp = []
        gdpt_gbps_measured_per_flow_list_list_ssird = []
        gdpt_gbps_measured_per_flow_list_list_dctcp = []

        for results in self.processed_results_list:
            ssird_fct_list.append(results.ssird_fct)
            dctcp_fct_list.append(results.dctcp_fct)
            gdpt_gbps_measured_list_ssird.append(results.gdpt_gbps_measured_ssird)
            gdpt_gbps_measured_list_dctcp.append(results.gdpt_gbps_measured_dctcp)
            gdpt_gbps_measured_per_flow_list_list_ssird.append(results.gdpt_gbps_measured_per_flow_list_ssird)
            gdpt_gbps_measured_per_flow_list_list_dctcp.append(results.gdpt_gbps_measured_per_flow_list_dctcp)

        return ssird_fct_list, dctcp_fct_list, gdpt_gbps_measured_list_ssird, gdpt_gbps_measured_list_dctcp, gdpt_gbps_measured_per_flow_list_list_ssird, gdpt_gbps_measured_per_flow_list_list_dctcp


def init_logs(experiment_family, logs_file_name, log_level=logging.DEBUG):
    full_rel_path = f"{LOGS_REL_PATH}{experiment_family}/"
    Path(full_rel_path).mkdir(parents=True, exist_ok=True) 
    logs_file_path = full_rel_path + logs_file_name
    logging.basicConfig(
        level=log_level,
        handlers=[
            logging.FileHandler(logs_file_path, mode='w'),
            logging.StreamHandler()
        ]
    )
