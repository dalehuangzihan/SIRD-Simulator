import sys, subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import csv
import datetime
import logging
import collections
import math
import numpy as np
from scipy.stats import truncexpon
import json

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
DCTCP_PROTO_FAMILY_NAME = "DCTCP"

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
FLOW_SPECS_JSON_PATH = PATH_TO_POST_PROCESS + "flow_specs_json/"
SAVED_FLOW_SPECS_JSON_PATH = PATH_TO_POST_PROCESS + "saved_flow_specs_json/"

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

    def __init__(self, src, dst, flow_id, flow_spec, absolute_start_time_us):
        self.id = flow_id
        self.src = src
        self.dst = dst
        self.flow_spec = flow_spec
        self.absolute_start_time_us = absolute_start_time_us
        self.byteloads_list = []

        # assert(byteload_interval_us >= 1)
        # assert(byteload_interval_us*10%10 == 0)
        assert(min(flow_spec.interval_us_list) >= 0.001) # must be at least 1ns

        self.init_byteloads()

    def init_byteloads(self):
        byteload_size_B_list = self.flow_spec.byteload_size_B_list
        byteload_rel_timestamp_us_list = self.flow_spec.byteload_timestamp_us_list
        assert(len(byteload_size_B_list) == len(byteload_rel_timestamp_us_list)) 
        for i in range(0, len(byteload_size_B_list)):
            rel_timestamp_us = self.RELATIVE_START_TIME_US + byteload_rel_timestamp_us_list[i]
            absolute_timestamp_us = self.absolute_start_time_us + rel_timestamp_us
            self.byteloads_list.append(Byteload(self.src, self.dst, self.id, self.flow_spec.byteload_size_B_list[i], rel_timestamp_us, absolute_timestamp_us))

class MultiFlow:
    '''
    Is a collection of multiple flows that are passed to the simulation
    TODO: currently can only replicate the same flow multiple times
    ''' 

    def __init__(self, src, dst, flow_spec_list, flow_start_times_us_list):
        self.src = src
        self.dst = dst
        self.flow_spec_list = flow_spec_list
        self.flow_start_times_us_list = flow_start_times_us_list # is the start times relative to the overall start timestamp of 0us
        self.num_flows = len(flow_spec_list)
        self.flows_list = []

        # assert(num_byteloads_per_flow > 1) # we want at least 2 byteloads per flow
        self.init_flows()

    def init_flows(self):
        for i in range(0, self.num_flows):
            flow_start_time_us = self.flow_start_times_us_list[i]
            self.flows_list.append(Flow(self.src, self.dst, i, self.flow_spec_list[i], flow_start_time_us))
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

class ExperimentGroupResultsProcessed:
    def __init__(self, processed_results_list):
        self.processed_results_list = processed_results_list

        self.ssird_fct_list = []
        self.dctcp_fct_list = []

        self.total_app_gdpt_gbps_measured_list_ssird = []
        self.total_app_gdpt_gbps_measured_list_dctcp = []
        self.app_gdpt_gbps_measured_per_flow_list_list_ssird = []
        self.app_gdpt_gbps_measured_per_flow_list_list_dctcp = []

        self.total_nw_gdpt_gbps_measured_list_ssird = []
        self.total_nw_gdpt_gbps_measured_list_dctcp = []
        self.nw_gdpt_gbps_measured_per_flow_list_list_ssird = []
        self.nw_gdpt_gbps_measured_per_flow_list_list_dctcp = []

        for results in self.processed_results_list:
            self.ssird_fct_list.append(results.ssird_fct)
            self.dctcp_fct_list.append(results.dctcp_fct)

            self.total_app_gdpt_gbps_measured_list_ssird.append(results.ssird_total_app_gdpt_gbps_measured)
            self.total_app_gdpt_gbps_measured_list_dctcp.append(results.dctcp_total_app_gdpt_gbps_measured)
            self.app_gdpt_gbps_measured_per_flow_list_list_ssird.append(results.ssird_app_gdpt_gbps_measured_per_flow_list)
            self.app_gdpt_gbps_measured_per_flow_list_list_dctcp.append(results.dctcp_app_gdpt_gbps_measured_per_flow_list)

            self.total_nw_gdpt_gbps_measured_list_ssird.append(results.ssird_total_nw_gdpt_gbps_measured)
            self.total_nw_gdpt_gbps_measured_list_dctcp.append(results.dctcp_total_nw_gdpt_gbps_measured )
            self.nw_gdpt_gbps_measured_per_flow_list_list_ssird.append(results.ssird_nw_gdpt_gbps_measured_per_flow_list )
            self.nw_gdpt_gbps_measured_per_flow_list_list_dctcp.append(results.dctcp_nw_gdpt_gbps_measured_per_flow_list )

class ExperimentResultsProcessed:
    def __init__(self, ssird_experiment_metrics=None, dctcp_experiment_metrics=None):
        self.ssird_experiment_metrics = ssird_experiment_metrics
        self.dctcp_experiment_metrics = dctcp_experiment_metrics

        self.ssird_fct = None
        self.dctcp_fct = None

        self.ssird_total_app_gdpt_gbps_measured = None
        self.dctcp_total_app_gdpt_gbps_measured = None

        self.ssird_app_gdpt_gbps_measured_per_flow_list = None
        self.dctcp_app_gdpt_gbps_measured_per_flow_list = None

        self.ssird_total_nw_gdpt_gbps_measured = None
        self.dctcp_total_nw_gdpt_gbps_measured = None

        self.ssird_nw_gdpt_gbps_measured_per_flow_list = None
        self.dctcp_nw_gdpt_gbps_measured_per_flow_list = None

        self.ingest_metrics()

    def ingest_metrics(self):
        if (self.ssird_experiment_metrics):
            assert(SSIRD_PROTO_NAME in self.ssird_experiment_metrics.proto)
            self.ssird_fct = self.ssird_experiment_metrics.fct_list
            self.ssird_total_app_gdpt_gbps_measured = self.ssird_experiment_metrics.total_app_gdpt_gbps_measured
            self.ssird_app_gdpt_gbps_measured_per_flow_list = self.ssird_experiment_metrics.app_gdpt_gbps_measured_per_flow_list
            self.ssird_total_nw_gdpt_gbps_measured = self.ssird_experiment_metrics.total_nw_gdpt_gbps_measured
            self.ssird_nw_gdpt_gbps_measured_per_flow_list = self.ssird_experiment_metrics.nw_gdpt_gbps_measured_per_flow_list

        if (self.dctcp_experiment_metrics):
            assert(DCTCP_PROTO_FAMILY_NAME in self.dctcp_experiment_metrics.proto)
            self.dctcp_fct = self.dctcp_experiment_metrics.fct_list
            self.dctcp_total_app_gdpt_gbps_measured = self.dctcp_experiment_metrics.total_app_gdpt_gbps_measured
            self.dctcp_app_gdpt_gbps_measured_per_flow_list = self.dctcp_experiment_metrics.app_gdpt_gbps_measured_per_flow_list
            self.dctcp_total_nw_gdpt_gbps_measured = self.dctcp_experiment_metrics.total_nw_gdpt_gbps_measured
            self.dctcp_nw_gdpt_gbps_measured_per_flow_list = self.dctcp_experiment_metrics.nw_gdpt_gbps_measured_per_flow_list

class ExperimentMetrics:
    def __init__(self, proto, fct_list, total_app_gdpt_gbps_measured, app_gdpt_gbps_measured_per_flow_list, total_nw_gdpt_gbps_measured, nw_gdpt_gbps_measured_per_flow_list):
        self.proto = proto
        self.fct_list = fct_list

        self.total_app_gdpt_gbps_measured = total_app_gdpt_gbps_measured 
        self.app_gdpt_gbps_measured_per_flow_list = app_gdpt_gbps_measured_per_flow_list 

        self.total_nw_gdpt_gbps_measured = total_nw_gdpt_gbps_measured 
        self.nw_gdpt_gbps_measured_per_flow_list = nw_gdpt_gbps_measured_per_flow_list 

class ExperimentOutputRaw:
    '''
    Is the raw un-processed experiment outputs
    '''
    def __init__(self, exp_id, experiment_family, experiment_name, app_trace_file_path, proto, src_dst_pairs_list, num_flows, flow_spec_list, target_flow_rate_gbps):
        self.exp_id = exp_id
        self.experiment_family = experiment_family
        self.experiment_name = experiment_name
        self.proto = proto
        self.src_dst_pairs_list = src_dst_pairs_list
        self.app_trace_file_path = app_trace_file_path

        self.num_flows = num_flows
        self.flow_spec_list = flow_spec_list
        self.target_flow_rate_gbps = target_flow_rate_gbps

    def process_results_fct(self):
        logger.info(f"Processing results from {self.app_trace_file_path}")
        
        d = {}
        for src, dst in self.src_dst_pairs_list:
            for flow_id in range(0, self.num_flows):
                src_dst_pair = sorted([src,dst]) # each src-dst pair is unique, so both h0->h1 and h1->h0 flows should be treated as under the same src-dst pair
                dict_key = (src_dst_pair[0], src_dst_pair[1], flow_id)
                d[dict_key] = FlowStats(self.proto, src, dst, flow_id, self.flow_spec_list[flow_id].num_byteloads, self.flow_spec_list[flow_id].byteload_size_B_list)
        flow_stats_dict = collections.OrderedDict(sorted(d.items()))
        del d

        total_bytes_sent_B = 0
        total_bytes_sent_until_penultimate_srq_B = 0
        overall_srq_start_time_s = math.inf
        overall_final_srq_timestamp_s = None

        overall_start_time_s = math.inf
        overall_final_rrq_timestamp_s = None
        total_bytes_rcvd_B = 0

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

                    overall_start_time_s = min(flow_trace_event.get_timestamp(), overall_start_time_s)

                    if (flow_trace_event.get_event() == FlowTraceEvent.SRQ_EVENT):
                        overall_srq_start_time_s = min(flow_trace_event.get_timestamp(), overall_srq_start_time_s)
                        overall_final_srq_timestamp_s = flow_trace_event.get_timestamp()
                        total_bytes_sent_until_penultimate_srq_B = total_bytes_sent_B
                        total_bytes_sent_B += flow_trace_event.get_req_size() 

                    elif (flow_trace_event.get_event() == FlowTraceEvent.RRQ_EVENT):
                        overall_final_rrq_timestamp_s = flow_trace_event.get_timestamp()

                    del flow_id
                    del flow_trace_event
        except FileNotFoundError:
            logger.error("The file was not found")
        except IOError:
            logger.error("An error occurred while reading the file")

        # Measure per-flow app & nw gdpt:
        fct_list = []
        measured_app_gdpt_gbps_per_flow_list = []
        measured_nw_gdpt_gbps_per_flow_list = []
        total_data_expected_B = 0
        total_data_rcved_B = 0
        for _, flow_stats_obj in flow_stats_dict.items():
            expected_data_B, rcvd_data_B = flow_stats_obj.check_flow_stats()
            total_data_expected_B += expected_data_B
            total_data_rcved_B += rcvd_data_B
            fct_list.append(flow_stats_obj.get_fct_s())
            measured_app_gdpt_gbps_per_flow_list.append(flow_stats_obj.get_measured_app_gdpt_for_flow_gbps())
            measured_nw_gdpt_gbps_per_flow_list.append(flow_stats_obj.get_measured_nw_gdpt_for_flow_gbps())
            total_bytes_rcvd_B += flow_stats_obj.total_data_bytes_recv_B

        logger.info(f"Total data expected (B): {total_data_expected_B}, total data received (B): {total_data_rcved_B}, diff: {total_data_expected_B - total_data_rcved_B}")

        # TODO: FIX ME! This total-thrpt calc seems a lil iffy... it overestimates gbps by 5%. Why??
        # Measure overal app gdpt:
        if (overall_final_srq_timestamp_s - overall_srq_start_time_s > 0):
            measured_total_app_gdpt_gbps = (total_bytes_sent_until_penultimate_srq_B * 8) / (overall_final_srq_timestamp_s - overall_srq_start_time_s) * pow(10,-9)
        else:
            measured_total_app_gdpt_gbps = -1

        # Measure overall nw gdpt:
        if (overall_final_rrq_timestamp_s is not None and overall_final_rrq_timestamp_s - overall_start_time_s > 0):
            measured_total_nw_gdpt_gbps = (total_bytes_rcvd_B * 8) / (overall_final_rrq_timestamp_s - overall_start_time_s) * pow(10,-9)
        else:
            measured_total_nw_gdpt_gbps = -1 

        return ExperimentMetrics(self.proto, fct_list, measured_total_app_gdpt_gbps, measured_app_gdpt_gbps_per_flow_list, measured_total_nw_gdpt_gbps, measured_nw_gdpt_gbps_per_flow_list)

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
        self.byteload_size_B_list = byteload_size_B
        
        self.num_srq = 0
        self.num_rrq = 0
        self.start_time_s = math.inf
        self.end_time_s = -1
        self.total_data_bytes_sent_B = 0
        self.total_data_bytes_recv_B = 0

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
            self.total_bytes_sent_until_penultimate_srq_B = self.total_data_bytes_sent_B
            self.total_data_bytes_sent_B += flow_trace_event.get_req_size()
            self.final_srq_timestamp = flow_trace_event.get_timestamp()

        elif (trace_event_name == FlowTraceEvent.RRQ_EVENT):
            self.num_rrq += 1
            if (self.proto == SSIRD_PROTO_NAME):
                # each ssird rrq shows cumulative recved-data size that progressively increases as data chunks reach the receiver-side app
                self.total_data_bytes_recv_B = flow_trace_event.get_req_size()
            elif (self.proto == DCTCP_PROTO_NAME):
                self.total_data_bytes_recv_B += flow_trace_event.get_req_size()
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

        expected_flow_size_B = sum(self.byteload_size_B_list)
        logger.debug(f"Flow {self.flow_id}:: first_event_name: {self.first_event_name}, final_event_name: {self.final_event_name}, expected_data_B: {expected_flow_size_B}, recv_data_B: {self.total_data_bytes_recv_B}")
        if (self.total_data_bytes_recv_B != expected_flow_size_B):
            logger.error(f"Missing data! flow_id: {self.flow_id}: total bytes recv: {self.total_data_bytes_recv_B}, expected flow size = {expected_flow_size_B}, diff = {expected_flow_size_B - self.total_data_bytes_recv_B}")

        return expected_flow_size_B, self.total_data_bytes_recv_B

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

    def get_measured_nw_gdpt_for_flow_gbps(self):
        # returns in Gbps
        send_duration_s = self.end_time_s - self.start_time_s
        return self.total_data_bytes_recv_B * 8 / send_duration_s * pow(10,-9)

class Experiment():

    def __init__(self, experiment_family, experiment_name, proto, src_dst_pairs_list, num_flows, target_flow_rate_gbps, flow_start_times_us_list, flow_spec_list, is_full_postproc=False):
        self.experiment_family = experiment_family
        self.proto = proto

        self.src_dst_pairs_list = src_dst_pairs_list
        self.num_flows = num_flows
        self.target_flow_rate_gbps = target_flow_rate_gbps
        self.flow_spec_list = flow_spec_list
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

        self.prep_experiment_input(self.src_dst_pairs_list, self.flow_spec_list, self.flow_start_times_us_list)
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

        experiment_results_raw = ExperimentOutputRaw(
            exp_id,
            self.experiment_family,
            self.experiment_name,
            app_trace_file_path,
            self.proto,
            self.src_dst_pairs_list,
            self.num_flows,
            self.flow_spec_list,
            self.target_flow_rate_gbps
        )

        return experiment_results_raw

    def prep_experiment_input(self, src_dst_pairs_list, flow_spec_list, flow_start_times_list):
        logger.info("-----\nPreparing experiment input MRIs")
        try:
            logger.info("### Creating MRI inputs parent dir: " + self.mri_input_dir)
            Path(self.mri_input_dir).mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            logger.info("File " + self.mri_input_dir + " aready exists.")
        
        mri = ManualReqInterval(self.mri_input_dir, self.experiment_name)
        multiflow_obj_list = []
        for src, dst in src_dst_pairs_list:
            multiflow_obj = MultiFlow(src, dst, flow_spec_list, flow_start_times_list)  
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
    def write_app_trace_paths_to_file(proto, experiment_family, num_flows, target_flow_rate_gbps, experiment_date, app_trace_file_paths_list):
        logger.info("-----\nBacking up app trace file paths")
        parent_dir = f"{APP_TRACE_PATHS_BACKUP_PATH}{experiment_family}/{num_flows}flo_{target_flow_rate_gbps}Gbps_{experiment_date}/"
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
    def get_experiment_name(num_flows, target_flow_rate_gbps):
        return "{}flo-{}Gbps-{}".format(num_flows, target_flow_rate_gbps, Experiment.get_date_now())
    
    @staticmethod
    def get_date_now():
        return datetime.datetime.now().strftime("%Y-%m-%dT_%H-%M-%SZ")

class ExperimentGroup:

    def __init__(self, experiment_family, proto_names_list, src_dst_pairs_list, num_flows, target_flow_rate_gbps, flow_start_times_us_list_list, flow_spec_list_list, ssird_sim_dur_list, dctcp_sim_dur_list, is_full_postproc=False, log_level=LOG_LEVEL_2, title_addendum=""):
        self.experiment_family = experiment_family
        self.proto_names_l = proto_names_list
        self.src_dst_pairs_list = src_dst_pairs_list
        self.num_flows = num_flows
        self.target_flow_rate_gbps = target_flow_rate_gbps
        self.flow_start_times_us_list_list = flow_start_times_us_list_list
        self.flow_spec_list_list = flow_spec_list_list
        self.is_full_postproc = is_full_postproc
        self.ssird_sim_dur_list = ssird_sim_dur_list
        self.dctcp_sim_dur_list = dctcp_sim_dur_list
        self.title_addendum = title_addendum
        self.log_level = log_level

        # check inputs
        assert(len(set([
            len(flow_start_times_us_list_list),
            len(flow_spec_list_list),
            ])) == 1)
        self.num_experiments = len(flow_spec_list_list)
        assert(all(len(flow_spec_list) == num_flows for flow_spec_list in flow_spec_list_list))
        assert(all(len(flow_start_times) == num_flows for flow_start_times in flow_start_times_us_list_list))

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
                experiment_name = Experiment.get_experiment_name(self.num_flows, self.target_flow_rate_gbps) + self.title_addendum
                for proto in self.proto_names_l:
                    experiment = Experiment(self.experiment_family, experiment_name, proto, self.src_dst_pairs_list, self.num_flows, self.target_flow_rate_gbps, self.flow_start_times_us_list_list[exp_id], self.flow_spec_list_list[exp_id], self.is_full_postproc) 

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
        Experiment.write_app_trace_paths_to_file(SSIRD_PROTO_NAME, self.experiment_family, self.num_flows, self.target_flow_rate_gbps, Experiment.get_date_now(), ssird_path_to_app_trace_files_list)
        dctcp_path_to_app_trace_files_list = [r.app_trace_file_path for r in self.dctcp_raw_experiment_results_list if r is not None]
        Experiment.write_app_trace_paths_to_file(DCTCP_PROTO_NAME, self.experiment_family, self.num_flows, self.target_flow_rate_gbps, Experiment.get_date_now(), dctcp_path_to_app_trace_files_list)
        logger.info(f"Simulations ended at: {datetime.datetime.now()}")
    
    def post_process_results(self):
        logger.info("\n##### POST PROCESS RESULTS #####")
        for i in range(0, self.num_experiments):
            logger.info(f"=====\n** Num Flows: {self.num_flows}, Target Flow Rate (Gbps): {self.target_flow_rate_gbps}, ssird_sim_dur (s): {self.ssird_sim_dur_list[i]}, dctcp_sim_dur (s): {self.dctcp_sim_dur_list[i]}")

            ssird_result = self.ssird_raw_experiment_results_list[i]
            if ssird_result == None:
                logger.error("No results for SSIRD")
                ssird_exp_metrics = None
            else:
                logger.info(f"Processing SIRD results exp_id {ssird_result.exp_id}:: {ssird_result.num_flows}flo-{ssird_result.target_flow_rate_gbps}Gbps_target")
                ssird_exp_metrics = ssird_result.process_results_fct()
                logger.info(f"{ssird_exp_metrics.proto} FCT (ms): {ssird_exp_metrics.fct_list}\nApp Gdpt (overall): {ssird_exp_metrics.total_app_gdpt_gbps_measured} Gbps\nApp Gdpt (per flow): {ssird_exp_metrics.app_gdpt_gbps_measured_per_flow_list}\nNetwork Gdpt (overall): {ssird_exp_metrics.total_nw_gdpt_gbps_measured}\nNetwork Gdpt (per flow): {ssird_exp_metrics.nw_gdpt_gbps_measured_per_flow_list}")

            dctcp_result = self.dctcp_raw_experiment_results_list[i]
            if dctcp_result == None:
                logger.error("No results for DCTCP")
                dctcp_exp_metrics = None
            else:
                logger.info(f"Processing DCTCP results exp_id {dctcp_result.exp_id}:: {dctcp_result.num_flows}flo-{dctcp_result.target_flow_rate_gbps}Gbps_target")
                dctcp_exp_metrics = dctcp_result.process_results_fct()
                logger.info(f"{dctcp_exp_metrics.proto} FCT (ms): {dctcp_exp_metrics.fct_list}\nApp Gdpt (overall): {dctcp_exp_metrics.total_app_gdpt_gbps_measured} Gbps\nApp Gdpt (per flow): {dctcp_exp_metrics.app_gdpt_gbps_measured_per_flow_list}\nNetwork Gdpt (overall): {dctcp_exp_metrics.total_nw_gdpt_gbps_measured}\nNetwork Gdpt (per flow): {dctcp_exp_metrics.nw_gdpt_gbps_measured_per_flow_list}")

            processed_result = ExperimentResultsProcessed(ssird_exp_metrics, dctcp_exp_metrics)
            self.processed_results_list.append(processed_result)

    def generate_overall_experiment_metrics(self):
        logger.info("\n##### GENERATE METRICS #####")
        return ExperimentGroupResultsProcessed(self.processed_results_list)

    @staticmethod
    def process_side_loaded_results(proto, src_dst_pairs_list, num_flows, flow_spec_list_list, target_flow_rate_gbps, app_trace_paths_list):
        # NOTE: this mtd can only read results for 1 proto at a time
        assert(len(set( [len(flow_spec_list_list), len(app_trace_paths_list)] )) == 1)
        processed_results_list = []
        for i in range(0, len(app_trace_paths_list)):
            exp_output_raw = ExperimentOutputRaw(exp_id=None,
                                              experiment_family=None,
                                              experiment_name=None,
                                              app_trace_file_path=app_trace_paths_list[i],
                                              proto=proto,
                                              src_dst_pairs_list=src_dst_pairs_list,
                                              num_flows=num_flows,
                                              flow_spec_list=flow_spec_list_list[i],
                                              target_flow_rate_gbps=target_flow_rate_gbps)
            exp_metrics = exp_output_raw.process_results_fct() 
            if (SSIRD_PROTO_NAME in proto):
                processed_result = ExperimentResultsProcessed(ssird_experiment_metrics=exp_metrics)
            elif (DCTCP_PROTO_FAMILY_NAME in proto):
                processed_result = ExperimentResultsProcessed(dctcp_experiment_metrics=exp_metrics)
            processed_results_list.append(processed_result)
        exp_metrics = ExperimentGroupResultsProcessed(processed_results_list)
        
        print(f"Num flows: {num_flows}")
        print(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")

        print(f"APP Gdpt Gbps measured (SSIRD): {exp_metrics.total_app_gdpt_gbps_measured_list_ssird }")
        print(f"APP Gdpt Gbps measured (DCTCP): {exp_metrics.total_app_gdpt_gbps_measured_list_dctcp}")
        print(f"APP Gdpt Gbps measured per flow (SSIRD): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_ssird}")
        print(f"APP Gdpt Gbps measured per flow (DCTCP): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_dctcp}")

        print(f"NW Gdpt Gbps measured (SSIRD): {exp_metrics.total_nw_gdpt_gbps_measured_list_ssird}")
        print(f"NW Gdpt Gbps measured (DCTCP): {exp_metrics.total_nw_gdpt_gbps_measured_list_dctcp}")
        print(f"NW Gdpt Gbps measured per flow (SSIRD): {exp_metrics.nw_gdpt_gbps_measured_per_flow_list_list_ssird}")
        print(f"NW Gdpt Gbps measured per flow (DCTCP): {exp_metrics.nw_gdpt_gbps_measured_per_flow_list_list_dctcp}")

        print(f"* SSIRD FCT: {exp_metrics.ssird_fct_list}")
        print(f"* DCTCP FCT: {exp_metrics.dctcp_fct_list}")

        return exp_metrics

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

''' --- Poisson Process --- '''
# Each flow must have a given flow rate (approximately). Flow can vary.
# For each flow: inter-bload intervals are drawn from poisson process; bload sizes can vary; variable num bloads per flow 
# Bload sizes must > 4

class PoissonFlowGenerator:

    FLOW_GEN_RETRIES = 10

    def __init__(self, flow_rate_bps, min_num_byteloads, max_num_byteloads, min_byteload_size_B, max_byteload_size_B, min_interval_us, max_interval_us, seed_num_byteloads=None):
        self.flow_rate_bps = flow_rate_bps
        self.seed_num_byteloads = seed_num_byteloads
        self.min_num_byteloads = min_num_byteloads
        self.max_num_byteloads = max_num_byteloads
        self.min_byteload_size_B = min_byteload_size_B
        self.max_byteload_size_B = max_byteload_size_B
        self.min_interval_us = min_interval_us  # NOTE: this limit doesn't actually do much, final intervals are still at ns granularity
        self.max_interval_us = max_interval_us

    def _generate_byteload_sizes(self, num_byteloads):
        """Generate random byteload sizes in bits."""
        return np.rint(np.random.uniform(self.min_byteload_size_B, self.max_byteload_size_B, size=num_byteloads))

    def _calculate_required_byteloads(self, flow_size_B):
        """
        Calculate minimum byteloads needed to satisfy:
        1. Total duration = total_bits / flow_rate_bps
        2. Sum of intervals = total_duration
        3. Each interval in [min_interval_us, max_interval_us]
        """
        total_duration_s = flow_size_B * 8 / self.flow_rate_bps
        total_duration_us = total_duration_s * 1e6
        
        # Minimum byteloads needed to fit all intervals within bounds
        min_byteloads_adjusted = max(self.min_num_byteloads, int(np.ceil(total_duration_us / self.max_interval_us)) + 1)
        
        # Maximum allowed byteloads (to prevent too many small packets)
        max_byteloads_adjusted = min(self.max_num_byteloads, int(np.floor(total_duration_us / self.min_interval_us)) + 1)
        
        if min_byteloads_adjusted > self.max_num_byteloads:
            raise ValueError(
                f"Cannot satisfy constraints: need {min_byteloads_adjusted} byteloads "
                f"but max allowed is {self.max_num_byteloads}. Adjust parameters."
            )
        if max_byteloads_adjusted < self.min_num_byteloads:
            raise ValueError(
                f"Cannot satisfy constraints: need {max_byteloads_adjusted} byteloads "
                f"but min allowed is {self.min_num_byteloads}. Adjust parameters."
            )
        
        return np.random.randint(min_byteloads_adjusted, max_byteloads_adjusted + 1)

    def generate_flow(self):
        """Generate flow with dynamically adjusted byteload count."""
        if (self.seed_num_byteloads):
            num_byteloads = self.seed_num_byteloads
        else:
            # Initial random byteload count
            num_byteloads = np.random.randint(self.min_num_byteloads, self.max_num_byteloads + 1)
        
        # Generate byteload sizes and total bits
        byteload_size_B_list = self._generate_byteload_sizes(num_byteloads)
        flow_size_B = byteload_size_B_list.sum()
        
        # Calculate required byteloads based on interval constraints
        num_byteloads = self._calculate_required_byteloads(flow_size_B)
        
        # Regenerate sizes if byteload count changed
        if len(byteload_size_B_list) != num_byteloads:
            byteload_size_B_list = self._generate_byteload_sizes(num_byteloads)
            flow_size_B = byteload_size_B_list.sum()

        total_duration_s = flow_size_B * 8 / self.flow_rate_bps
        total_duration_us = total_duration_s * 1e6
        
        # Generate intervals with truncated exponential distribution
        num_intervals = num_byteloads - 1
        target_sum_us = total_duration_us
        
        # Scale parameter for exponential distribution
        # Choose λ to balance between min/max interval constraints
        scale_us = target_sum_us / num_intervals
        
        # Truncated exponential sampling of interval sizes
        a = self.min_interval_us / scale_us
        b = self.max_interval_us / scale_us
        interval_us_list = truncexpon(b - a, scale=scale_us).rvs(size=num_intervals)
        
        # Rescale to exact total duration
        interval_us_list = interval_us_list * (target_sum_us / interval_us_list.sum())
        interval_us_list = np.round(interval_us_list, 3)
        # Ensure minimum interval is at least 1ns
        interval_us_list = np.array([i + 0.001 if i == 0 else i for i in interval_us_list])
        
        # Calculate timestamps in us, round to nearest ns
        timestamp_us_list = np.round(np.cumsum(np.concatenate([[0], interval_us_list])), 3)
        
        actual_flow_rate_bps = flow_size_B * 8 / (timestamp_us_list[-1] * 1e-6) if timestamp_us_list[-1] > 0 else -1
        return FlowSpec(
            num_byteloads=num_byteloads,
            byteload_size_B_list=byteload_size_B_list.astype(np.int64).tolist(),
            flow_size_B=int(flow_size_B),
            interval_us_list=interval_us_list.tolist(),
            byteload_timestamp_us_list=timestamp_us_list.tolist(),
            total_flow_send_duration_us=float(total_duration_us),
            flow_rate_bps=float(actual_flow_rate_bps)
        )

    def generate_n_flows(self, num_flows):
        flow_spec_list = []

        # first pass
        for _ in range(0, num_flows):
            try:
                flow_spec = self.generate_flow()
                flow_spec_list.append(flow_spec)
            except ValueError as e:
                logger.warning(e)
                continue
        
        if (len(flow_spec_list) == num_flows):
            return flow_spec_list
        else:
            # retries
            to_retry_count = num_flows - len(flow_spec_list)
            for _ in range(0, to_retry_count):
                for _ in range(0, self.FLOW_GEN_RETRIES):
                    try:
                        flow_spec = self.generate_flow()
                        flow_spec_list.append(flow_spec)
                        break
                    except ValueError as e:
                        logger.warning(e)
                        continue
            if (len(flow_spec_list) == num_flows):
                return flow_spec_list
            else:
                raise ValueError(f"Could not generate sufficient flows. Change parameters!")

class FlowSpec:
    def __init__(self, num_byteloads, byteload_size_B_list, flow_size_B, interval_us_list, byteload_timestamp_us_list, total_flow_send_duration_us, flow_rate_bps):
        self.num_byteloads = num_byteloads
        self.byteload_size_B_list = byteload_size_B_list
        self.flow_size_B = flow_size_B
        self.interval_us_list = interval_us_list
        self.byteload_timestamp_us_list = byteload_timestamp_us_list
        self.total_flow_send_duration_us = total_flow_send_duration_us
        self.flow_rate_bps = flow_rate_bps
        self.check_spec()

    def check_spec(self):
        assert(len(set([
            self.num_byteloads,
            len(self.byteload_size_B_list),
            len(self.interval_us_list) + 1,
            len(self.byteload_timestamp_us_list)
        ])) == 1)

    def to_dict(self):
        # Convert the FlowSpec object to a dictionary.
        return {
            'num_byteloads': self.num_byteloads,
            'byteload_size_B_list': self.byteload_size_B_list,
            'flow_size_B': self.flow_size_B,
            'interval_us_list': self.interval_us_list,
            'byteload_timestamp_us_list': self.byteload_timestamp_us_list,
            'total_flow_send_duration_us': self.total_flow_send_duration_us,
            'flow_rate_bps': self.flow_rate_bps
        }

    @staticmethod
    def flow_spec_list_to_dict(flow_spec_list, flow_start_times_us_list):
        assert(len(flow_spec_list) == len(flow_start_times_us_list))
        full_dict = {
            'flow_start_times_us_list': flow_start_times_us_list,
            'flow_spec_dict_dict': {}
        } 
        for i in range(0, len(flow_spec_list)):
            full_dict['flow_spec_dict_dict'][i] = flow_spec_list[i].to_dict()
        return full_dict

    @staticmethod
    def flow_specs_dict_to_file(flow_spec_list_full_dict, parent_dir, file_name):
        Path(parent_dir).mkdir(parents=True, exist_ok=True)
        file_path = parent_dir + file_name
        with open(file_path, 'w') as file:
            json.dump(flow_spec_list_full_dict, file, indent=None)

    @staticmethod
    def parse_flow_specs_json_file(parent_dir, file_name):
        file_path = parent_dir + file_name
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        flow_start_times_us_list = data['flow_start_times_us_list']
        flow_spec_dict_dict = data['flow_spec_dict_dict']
        flow_spec_list = []
        for _, flow_spec_dict in flow_spec_dict_dict.items():
            flow_spec = FlowSpec(
                num_byteloads=flow_spec_dict['num_byteloads'],
                byteload_size_B_list=flow_spec_dict['byteload_size_B_list'],
                flow_size_B=flow_spec_dict['flow_size_B'],
                interval_us_list=flow_spec_dict['interval_us_list'],
                byteload_timestamp_us_list=flow_spec_dict['byteload_timestamp_us_list'],
                total_flow_send_duration_us=flow_spec_dict['total_flow_send_duration_us'],
                flow_rate_bps=flow_spec_dict['flow_rate_bps']
            )
            flow_spec_list.append(flow_spec)
        
        return flow_start_times_us_list, flow_spec_list

if __name__ == "__main__":

    # Example Usage of Possion Flow Generator
    num_flows = 2
    flow_rate_bps = 2 * pow(10,9)
    min_num_byteloads = 100
    max_num_byteloads = 5000
    min_byteload_size_B = 1458
    max_byteload_size_B = 1458
    min_interval_us = 10
    max_interval_us = 100

    poisson_flow_generator = PoissonFlowGenerator(
        flow_rate_bps,
        min_num_byteloads,
        max_num_byteloads,
        min_byteload_size_B,
        max_byteload_size_B,
        min_interval_us,
        max_interval_us
    )
    # Generate multiple flows and verify flow rates
    # flow_start_times_us_list = [0, 0]
    # flows = poisson_flow_generator.generate_n_flows(num_flows)

    flow_start_times_us_list, flows = FlowSpec.parse_flow_specs_json_file(SAVED_FLOW_SPECS_JSON_PATH, "poisson_intervals_experiment_50flo_2GbpsFlo_2025-08-04T_19-03-49Z.log")
    print(flow_start_times_us_list)

    for flow in flows:
        print(
            f"Flow with {flow.num_byteloads} byteloads | "
            f"Flow Size B: {flow.flow_size_B} B | "
            f"Duration: {flow.total_flow_send_duration_us:.4f}us | "
            f"Flow Rate: {flow.flow_rate_bps*pow(10,-9):.6f} Gbps"
            f"\n    Min Byteload Size (B): {min(flow.byteload_size_B_list)}"
            f"\n    Max Byteload Size (B): {max(flow.byteload_size_B_list)}"
            f"\n    Min Interval (us): {min(flow.interval_us_list)}"
            f"\n    Max Interval (us): {max(flow.interval_us_list)}"
            f"\n"
        )

    # flow_spec_dict = FlowSpec.flow_spec_list_to_dict(flows, flow_start_times_us_list)
    # FlowSpec.flow_specs_dict_to_file(flow_spec_dict, FLOW_SPECS_JSON_PATH, "testing.json")

    ''' --- Side-load & analyse existing app trace file ---'''
    # proto = SSIRD_PROTO_NAME
    # src_dst_pairs_list = [(0,1)]
    # num_flows = 9
    # # num_flows = 8
    # num_byteloads_list = [100]
    # byteload_size_B_list = [1560]
    # app_trace_paths_list = ["/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-9flo-100#-1560B-1000ns_1560B_9flo_112Gbps/data/SSIRD/60/applications_trace.str"]
    # # app_trace_paths_list = ["/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-8flo-100#-1560B-1000ns_1560B_8flo_99pt84Gbps/data/SSIRD/60/applications_trace.str"]
    # exp_metrics = ExperimentGroup.process_side_loaded_results(proto, src_dst_pairs_list, num_flows, num_byteloads_list, byteload_size_B_list, app_trace_paths_list)

