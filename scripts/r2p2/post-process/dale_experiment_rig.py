import sys, subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from abc import ABC, abstractmethod
import csv
import datetime
import logging
import collections
import math, random
import numpy as np
import json

# for thread pool
# MAX_WORKERS = 4 
# MAX_WORKERS = 12 # NOTE: use this for batch1 server
MAX_WORKERS = 12 # NOTE: use this for octopus4 server

MIN_BYTELOAD_INTERVAL_US = 0.001 # is 1ns

# Common experiment param; value is meaningful only when req_interval_distr is not 'manual'
CLIENT_INJECTION_RATE_GBPS = "60"
DCTCP_ECN_MARKING_THRESHOLD = "50"
LINK_SPEED_BITS_PER_SEC = 100 * pow(10,9) * 8 # 100Gbps

SSIRD_PROTO_NAME = "SSIRD"
DCTCP_PROTO_NAME = f"DCTCP-{DCTCP_ECN_MARKING_THRESHOLD}"
DCTCP_PROTO_FAMILY_NAME = "DCTCP"
XPASS_PROTO_NAME = "ExpressPass"

# PATH_TO_SIRD_SIM = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/"
# PATH_TO_SIRD_SIM = "/data/dh1723/SIRD-Simulator/" # NOTE: use this for batch1 server
PATH_TO_SIRD_SIM = "/home/dh1723/SIRD-Simulator/" # NOTE: use this for octopus4 server
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
PATH_TO_WORKOAD_DISTR_CDF = PATH_TO_POST_PROCESS + "sizeDistributions/"

LOG_LEVEL_1 = 1
LOG_LEVEL_2 = 2
LOG_LEVEL_6 = 6

SRPT = "srpt"
FAIRSHARE = "fairshare"
''' ------ TODO: Manually set which SSIRD template you want to use! ------ '''
SSIRD_POLICY = SRPT
# SSIRD_POLICY = FAIRSHARE
''' ------------ '''


logger = logging.getLogger(__name__)

class Byteload:
    '''
    relative_timestamp_us is the timestamp since the start of the flow, measured in us; flow always starts at a relative timestamp of 0us 
    relative_interval_us is the time gap between this byteload and the previous one in the serialised multiflow
    '''
    def __init__(self, src, dst, flow_id, size_B, relative_timestamp_us, absolute_timestamp_us, is_final_byteload):
        self.src = src
        self.dst = dst
        self.flow_id = flow_id
        self.size_B = size_B
        self.relative_timestamp_us = relative_timestamp_us
        self.absolute_timestamp_us = absolute_timestamp_us
        self.relative_interval_us = None
        self.is_final_byteload = is_final_byteload
    
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
        if (len(flow_spec.interval_us_list) > 0):
            assert(min(flow_spec.interval_us_list) >= 0.001) # must be at least 1ns

        self.init_byteloads()

    def init_byteloads(self):
        byteload_size_B_list = self.flow_spec.byteload_size_B_list
        byteload_rel_timestamp_us_list = self.flow_spec.byteload_rel_timestamp_us_list
        assert(len(byteload_size_B_list) == len(byteload_rel_timestamp_us_list)) 
        for i in range(0, len(byteload_size_B_list)):
            rel_timestamp_us = self.RELATIVE_START_TIME_US + byteload_rel_timestamp_us_list[i]
            absolute_timestamp_us = self.absolute_start_time_us + rel_timestamp_us
            is_final_byteload = (i == len(byteload_size_B_list)-1) # is the last byteload in the flow
            self.byteloads_list.append(Byteload(self.src, self.dst, self.id, self.flow_spec.byteload_size_B_list[i], rel_timestamp_us, absolute_timestamp_us, is_final_byteload))

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
            logger.error(f"Flows list is empty (size={len(self.flows_list)})!")
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
                byteload_str = "{:.10f}|{}|{}|{}|{}".format(time_spec, str(dst), bl.size_B, bl.flow_id, int(bl.is_final_byteload))
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

    SSIRD_TEMPLATE_NOBURST_SRPT = "template-ssird-noburst_srpt.sh"
    SSIRD_TEMPLATE_NOBURST_FAIRSHARE = "template-ssird-noburst_fairshare.sh"

    if (SSIRD_POLICY == SRPT):
        PATH_TO_SSIRD_TEMPLATE_NOBURST = PATH_TO_EXPERIMENT_SCRIPT_TEMPLATES + SSIRD_TEMPLATE_NOBURST_SRPT
    elif (SSIRD_POLICY == FAIRSHARE):
        PATH_TO_SSIRD_TEMPLATE_NOBURST = PATH_TO_EXPERIMENT_SCRIPT_TEMPLATES + SSIRD_TEMPLATE_NOBURST_FAIRSHARE
    else:
        logger.error("Unrecognised SSIRD POLICY: {SSIRD_POLICY}")

    # PATH_TO_SSIRD_TEMPLATE_NOBURST = PATH_TO_EXPERIMENT_SCRIPT_TEMPLATES + "template-ssird-noburst.sh"
    PATH_TO_DCTCP_TEMPLATE_NOBURST = PATH_TO_EXPERIMENT_SCRIPT_TEMPLATES + "template-dctcp.sh"
    PATH_TO_XPASS_TEMPLATE_NOBURST = PATH_TO_EXPERIMENT_SCRIPT_TEMPLATES + "template-xpass.sh"

    MANUAL_REQ_INTERVAL_FILE_L = "manual_req_interval_file_l"
    DURATION_MODIFIER_L = "duration_modifier_l"
    GLOBAL_DEBUG = "global_debug"
    DCTCP_K_L = "dctcp_k_l"
    SIMULATION_NAME_L = "simulation_name_l"
    TOPOLOGY_FILE_L = "topology_file_l"

    def __init__(self, parent_dir, experiment_name):
        self.parent_dir = parent_dir
        self.experiment_name = experiment_name
    
    def create_ssird_noburst_params_script(self, mri_relative_path, sim_duration, topo_yaml_file, log_level):
        script_filepath = self.parent_dir + f"{SSIRD_PROTO_NAME}-" + self.experiment_name + ".sh"
        with open(self.PATH_TO_SSIRD_TEMPLATE_NOBURST) as template, open(script_filepath, 'w') as fout:
            lines_in = template.readlines()
            for i in range(len(lines_in)):
                line_out = lines_in[i]
                if self.TOPOLOGY_FILE_L in line_out:
                    line_out = "{}='{}'\n".format(self.TOPOLOGY_FILE_L, topo_yaml_file)
                elif self.MANUAL_REQ_INTERVAL_FILE_L in line_out:
                    line_out = "{}='{}'\n".format(self.MANUAL_REQ_INTERVAL_FILE_L, mri_relative_path)
                elif self.DURATION_MODIFIER_L in line_out:
                    line_out = "{}='{:f}'\n".format(self.DURATION_MODIFIER_L, sim_duration)
                elif self.GLOBAL_DEBUG in line_out:
                    line_out = "{}='{}'\n".format(self.GLOBAL_DEBUG, log_level)
                fout.write(line_out)
        return script_filepath

    def create_dctcp_noburst_params_script(self, mri_relative_path, sim_duration, topo_yaml_file, log_level):
        script_filepath = self.parent_dir + f"{DCTCP_PROTO_NAME}-" + self.experiment_name + ".sh"
        with open(self.PATH_TO_DCTCP_TEMPLATE_NOBURST) as template, open(script_filepath, 'w') as fout:
            lines_in = template.readlines()
            for i in range(len(lines_in)):
                line_out = lines_in[i]
                if self.TOPOLOGY_FILE_L in line_out:
                    line_out = "{}='{}'\n".format(self.TOPOLOGY_FILE_L, topo_yaml_file)
                elif self.MANUAL_REQ_INTERVAL_FILE_L in line_out:
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

    def create_xpass_noburst_params_script(self, mri_relative_path, sim_duration, topo_yaml_file, log_level):
        script_filepath = self.parent_dir + f"{XPASS_PROTO_NAME}-" + self.experiment_name + ".sh"
        with open(self.PATH_TO_XPASS_TEMPLATE_NOBURST) as template, open(script_filepath, 'w') as fout:
            lines_in = template.readlines()
            for i in range(len(lines_in)):
                line_out = lines_in[i]
                if self.TOPOLOGY_FILE_L in line_out:
                    line_out = "{}='{}'\n".format(self.TOPOLOGY_FILE_L, topo_yaml_file)
                elif self.MANUAL_REQ_INTERVAL_FILE_L in line_out:
                    line_out = "{}='{}'\n".format(self.MANUAL_REQ_INTERVAL_FILE_L, mri_relative_path)
                elif self.DURATION_MODIFIER_L in line_out:
                    line_out = "{}='{:f}'\n".format(self.DURATION_MODIFIER_L, sim_duration)
                elif self.GLOBAL_DEBUG in line_out:
                    line_out = "{}='{}'\n".format(self.GLOBAL_DEBUG, log_level)
                fout.write(line_out)
        return script_filepath

class ExperimentGroupResultsProcessed:
    def __init__(self, processed_results_list):
        self.processed_results_list = processed_results_list

        self.ssird_fct_list = []
        self.dctcp_fct_list = []
        self.xpass_fct_list = []

        self.total_app_gdpt_gbps_measured_list_ssird = []
        self.total_app_gdpt_gbps_measured_list_dctcp = []
        self.total_app_gdpt_gbps_measured_list_xpass = []
        self.app_gdpt_gbps_measured_per_flow_list_list_ssird = []
        self.app_gdpt_gbps_measured_per_flow_list_list_dctcp = []
        self.app_gdpt_gbps_measured_per_flow_list_list_xpass = []

        self.total_nw_gdpt_gbps_measured_list_ssird = []
        self.total_nw_gdpt_gbps_measured_list_dctcp = []
        self.total_nw_gdpt_gbps_measured_list_xpass = []
        self.nw_gdpt_gbps_measured_per_flow_list_list_ssird = []
        self.nw_gdpt_gbps_measured_per_flow_list_list_dctcp = []
        self.nw_gdpt_gbps_measured_per_flow_list_list_xpass = []

        self.sorted_flowsize_fct_list_list_ssird = []
        self.sorted_flowsize_fct_list_list_dctcp = []
        self.sorted_flowsize_fct_list_list_xpass = []

        for results in self.processed_results_list:
            self.ssird_fct_list.append(results.ssird_fct)
            self.dctcp_fct_list.append(results.dctcp_fct)
            self.xpass_fct_list.append(results.xpass_fct)

            self.total_app_gdpt_gbps_measured_list_ssird.append(results.ssird_total_app_gdpt_gbps_measured)
            self.total_app_gdpt_gbps_measured_list_dctcp.append(results.dctcp_total_app_gdpt_gbps_measured)
            self.total_app_gdpt_gbps_measured_list_xpass.append(results.xpass_total_app_gdpt_gbps_measured)
            self.app_gdpt_gbps_measured_per_flow_list_list_ssird.append(results.ssird_app_gdpt_gbps_measured_per_flow_list)
            self.app_gdpt_gbps_measured_per_flow_list_list_dctcp.append(results.dctcp_app_gdpt_gbps_measured_per_flow_list)
            self.app_gdpt_gbps_measured_per_flow_list_list_xpass.append(results.xpass_app_gdpt_gbps_measured_per_flow_list)

            self.total_nw_gdpt_gbps_measured_list_ssird.append(results.ssird_total_nw_gdpt_gbps_measured)
            self.total_nw_gdpt_gbps_measured_list_dctcp.append(results.dctcp_total_nw_gdpt_gbps_measured )
            self.total_nw_gdpt_gbps_measured_list_xpass.append(results.xpass_total_nw_gdpt_gbps_measured )
            self.nw_gdpt_gbps_measured_per_flow_list_list_ssird.append(results.ssird_nw_gdpt_gbps_measured_per_flow_list )
            self.nw_gdpt_gbps_measured_per_flow_list_list_dctcp.append(results.dctcp_nw_gdpt_gbps_measured_per_flow_list )
            self.nw_gdpt_gbps_measured_per_flow_list_list_xpass.append(results.xpass_nw_gdpt_gbps_measured_per_flow_list )

            self.sorted_flowsize_fct_list_list_ssird.append(results.ssird_sorted_flowsize_fct_list)
            self.sorted_flowsize_fct_list_list_dctcp.append(results.dctcp_sorted_flowsize_fct_list)
            self.sorted_flowsize_fct_list_list_xpass.append(results.xpass_sorted_flowsize_fct_list)

class ExperimentResultsProcessed:
    def __init__(self, ssird_experiment_metrics=None, dctcp_experiment_metrics=None, xpass_experiment_metrics=None, ssird_sorted_flowsize_fct_list=None, dctcp_sorted_flowsize_fct_list=None, xpass_sorted_flowsize_fct_list=None):
        self.ssird_experiment_metrics = ssird_experiment_metrics
        self.dctcp_experiment_metrics = dctcp_experiment_metrics
        self.xpass_experiment_metrics = xpass_experiment_metrics
        self.ssird_sorted_flowsize_fct_list = ssird_sorted_flowsize_fct_list
        self.dctcp_sorted_flowsize_fct_list = dctcp_sorted_flowsize_fct_list
        self.xpass_sorted_flowsize_fct_list = xpass_sorted_flowsize_fct_list

        self.ssird_fct = None
        self.dctcp_fct = None
        self.xpass_fct = None

        self.ssird_total_app_gdpt_gbps_measured = None
        self.dctcp_total_app_gdpt_gbps_measured = None
        self.xpass_total_app_gdpt_gbps_measured = None

        self.ssird_app_gdpt_gbps_measured_per_flow_list = None
        self.dctcp_app_gdpt_gbps_measured_per_flow_list = None
        self.xpass_app_gdpt_gbps_measured_per_flow_list = None

        self.ssird_total_nw_gdpt_gbps_measured = None
        self.dctcp_total_nw_gdpt_gbps_measured = None
        self.xpass_total_nw_gdpt_gbps_measured = None

        self.ssird_nw_gdpt_gbps_measured_per_flow_list = None
        self.dctcp_nw_gdpt_gbps_measured_per_flow_list = None
        self.xpass_nw_gdpt_gbps_measured_per_flow_list = None

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

        if (self.xpass_experiment_metrics):
            assert(XPASS_PROTO_NAME in self.xpass_experiment_metrics.proto)
            self.xpass_fct = self.xpass_experiment_metrics.fct_list
            self.xpass_total_app_gdpt_gbps_measured = self.xpass_experiment_metrics.total_app_gdpt_gbps_measured
            self.xpass_app_gdpt_gbps_measured_per_flow_list = self.xpass_experiment_metrics.app_gdpt_gbps_measured_per_flow_list
            self.xpass_total_nw_gdpt_gbps_measured = self.xpass_experiment_metrics.total_nw_gdpt_gbps_measured
            self.xpass_nw_gdpt_gbps_measured_per_flow_list = self.xpass_experiment_metrics.nw_gdpt_gbps_measured_per_flow_list

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
    def __init__(self, exp_id, experiment_family, experiment_name, app_trace_file_path, proto, src_dst_pairs_list, src_dst_pairs_to_flowspecs_dict, num_flows, target_flow_rate_gbps):
        self.exp_id = exp_id
        self.experiment_family = experiment_family
        self.experiment_name = experiment_name
        self.proto = proto
        self.src_dst_pairs_list = src_dst_pairs_list
        self.app_trace_file_path = app_trace_file_path

        self.num_flows = num_flows
        self.src_dst_pairs_to_flowspecs_dict = src_dst_pairs_to_flowspecs_dict
        self.target_flow_rate_gbps = target_flow_rate_gbps

    def process_results_fct(self):
        logger.info(f"Processing results from {self.app_trace_file_path}")
        
        d = {}
        for src, dst in self.src_dst_pairs_list:
            flow_spec_list, _ = self.src_dst_pairs_to_flowspecs_dict[(src,dst)]
            for flow_id in range(0, self.num_flows):
                src_dst_pair = sorted([src,dst]) # each src-dst pair is unique, so both h0->h1 and h1->h0 flows should be treated as under the same src-dst pair
                dict_key = (src_dst_pair[0], src_dst_pair[1], flow_id)
                # print(dict_key)
                d[dict_key] = FlowStats(self.proto, src, dst, flow_id, flow_spec_list[flow_id].num_byteloads, flow_spec_list[flow_id].byteload_size_B_list)
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
                    # print(dict_key)
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
        for _, flow_stats_obj in flow_stats_dict.items():
            flow_stats_obj.check_flow_stats()
            fct_list.append(flow_stats_obj.get_fct_s())
            measured_app_gdpt_gbps_per_flow_list.append(flow_stats_obj.get_measured_app_gdpt_for_flow_gbps())
            measured_nw_gdpt_gbps_per_flow_list.append(flow_stats_obj.get_measured_nw_gdpt_for_flow_gbps())
            total_bytes_rcvd_B += flow_stats_obj.total_data_bytes_recv_B

        # TODO: FIX ME! This total-thrpt calc seems a lil iffy... it overestimates gbps by 5%. Why??
        # NOTE: this calculation of overall app gdpt assumes that all flows are being directed to a SINGLE sender!
        # Measure overal app gdpt:
        if (overall_final_srq_timestamp_s - overall_srq_start_time_s > 0):
            measured_total_app_gdpt_gbps = (total_bytes_sent_until_penultimate_srq_B * 8) / (overall_final_srq_timestamp_s - overall_srq_start_time_s) * pow(10,-9)
        else:
            measured_total_app_gdpt_gbps = -1

        # NOTE: this calculation of overall nw gdpt assumes that all flows are being directed to a SINGLE sender!
        # Measure overall nw gdpt:
        if (overall_final_rrq_timestamp_s is not None and overall_final_rrq_timestamp_s - overall_start_time_s > 0):
            measured_total_nw_gdpt_gbps = (total_bytes_rcvd_B * 8) / (overall_final_rrq_timestamp_s - overall_start_time_s) * pow(10,-9)
        else:
            measured_total_nw_gdpt_gbps = -1 

        return ExperimentMetrics(self.proto, fct_list, measured_total_app_gdpt_gbps, measured_app_gdpt_gbps_per_flow_list, measured_total_nw_gdpt_gbps, measured_nw_gdpt_gbps_per_flow_list), flow_stats_dict

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
                self.total_data_bytes_recv_B = flow_trace_event.get_req_size()
            elif (self.proto == XPASS_PROTO_NAME):
                self.total_data_bytes_recv_B = flow_trace_event.get_req_size()
            else:
                logger.error(f"Unrecognised proto name {self.proto}")

        else:
            logger.error(f"Unrecognised flow trace event {trace_event_name}")

    def check_flow_stats(self):
        logger.info(f"srcdst:{(self.src, self.dst)} Flow {self.flow_id}:: num of byteloads: {self.num_byteloads}, num srq events: {self.num_srq}, num rrq events: {self.num_rrq}")

        assert(self.num_srq == self.num_byteloads) # TODO: remove assertion if adaptive batching feature is implemented
        assert(self.first_event_name == FlowTraceEvent.SRQ_EVENT)
        
        if (self.final_event_name != FlowTraceEvent.RRQ_EVENT):
            logger.error(f"Flow {self.flow_id}: Final event was {self.final_event_name} instead of {FlowTraceEvent.RRQ_EVENT}!")        

        expected_flow_size_B = sum(self.byteload_size_B_list)
        logger.debug(f"Flow {self.flow_id}:: first_event_name: {self.first_event_name}, final_event_name: {self.final_event_name}, expected_data_B: {expected_flow_size_B}, recv_data_B: {self.total_data_bytes_recv_B}")
        if(self.total_data_bytes_sent_B != expected_flow_size_B and expected_flow_size_B >= 4):
            logger.error(f"total_data_bytes_sent_B={self.total_data_bytes_sent_B}, expected_flow_size_B={expected_flow_size_B}, diff={self.total_data_bytes_sent_B - expected_flow_size_B}")
        if (self.total_data_bytes_recv_B != expected_flow_size_B and expected_flow_size_B >= 4):
            logger.error(f"Missing data! flow_id: {self.flow_id}: total bytes recv: {self.total_data_bytes_recv_B}, expected flow size = {expected_flow_size_B}, diff = {expected_flow_size_B - self.total_data_bytes_recv_B}")

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

    def __init__(self, experiment_family, experiment_name, proto, topo_yaml_file, src_dst_pairs_list, num_flows, target_flow_rate_gbps, src_dst_pairs_to_flowspecs_dict, is_full_postproc=False):
        self.experiment_family = experiment_family
        self.proto = proto
        self.topo_yaml_file = topo_yaml_file

        self.src_dst_pairs_list = src_dst_pairs_list
        self.num_flows = num_flows
        self.target_flow_rate_gbps = target_flow_rate_gbps
        self.src_dst_pairs_to_flowspecs_dict = src_dst_pairs_to_flowspecs_dict
        self.experiment_name = experiment_name 

        self.mri_input_dir = PATH_TO_EXPERIMENTS_INPUTS + experiment_family + "/"
        self.param_scripts_dir = PATH_TO_EXPERIMENTS_SCRIPTS + experiment_family + "/"
        self.app_trace_file_path = ""

        self.run_simulations = "1"
        self.run_post_proc = f"{int(is_full_postproc)}" 
        self.create_timeseires = f"{int(is_full_postproc)}" 
        self.create_plots = f"{int(is_full_postproc)}"
        self.delete_current = "0"

    def run(self, exp_id, ssird_sim_dur_l, dctcp_sim_dur_l, xpass_sim_dur_l, log_level):
        logger.info("\n=====\nExecute experiment " + self.experiment_name)
        logger.info(f'Flags: {self.run_simulations}, {self.run_post_proc}, {self.create_timeseires}, {self.create_plots}, {self.delete_current}')
        logger.info("ssird_sim_duration={:f}; dctcp_sim_duration={:f}".format(ssird_sim_dur_l, dctcp_sim_dur_l))

        self.prep_experiment_input(self.src_dst_pairs_list, self.src_dst_pairs_to_flowspecs_dict)
        ssird_sim_script_path, dctcp_sim_script_path, xpass_sim_script_path = self.prep_experiment_spec_scripts(
            ssird_sim_duration=ssird_sim_dur_l,
            dctcp_sim_duration=dctcp_sim_dur_l,
            xpass_sim_duration=xpass_sim_dur_l,
            experiment_name=self.experiment_name,
            topo_yaml_file=self.topo_yaml_file,
            log_level=log_level)

        outputs_dir = f"{PATH_TO_SIM_COORD}outputs/{self.experiment_family}/"
        Path(outputs_dir).mkdir(parents=True, exist_ok=True)

        app_trace_file_path = f"{PATH_TO_SIM_RESULTS}{self.proto}-{self.experiment_name}/data/{self.proto}/{CLIENT_INJECTION_RATE_GBPS}/applications_trace.str"
        if self.proto == SSIRD_PROTO_NAME:
            self.execute(self.proto, ssird_sim_script_path, f"{outputs_dir}ssird_{self.experiment_name}")
        elif self.proto == DCTCP_PROTO_NAME:
            self.execute(self.proto, dctcp_sim_script_path, f"{outputs_dir}{DCTCP_PROTO_NAME}_{self.experiment_name}")
        elif self.proto == XPASS_PROTO_NAME:
            self.execute(self.proto, xpass_sim_script_path, f"{outputs_dir}{XPASS_PROTO_NAME}_{self.experiment_name}")
        else:
            logger.error(f"Unrecognised protocol name '{self.proto}'")

        experiment_results_raw = ExperimentOutputRaw(
            exp_id,
            self.experiment_family,
            self.experiment_name,
            app_trace_file_path,
            self.proto,
            self.src_dst_pairs_list,
            self.src_dst_pairs_to_flowspecs_dict,
            self.num_flows,
            self.target_flow_rate_gbps
        )

        return experiment_results_raw

    def prep_experiment_input(self, src_dst_pairs_list, src_dst_pairs_to_flowspecs_dict):
        logger.info("-----\nPreparing experiment input MRIs")
        try:
            logger.info("### Creating MRI inputs parent dir: " + self.mri_input_dir)
            Path(self.mri_input_dir).mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            logger.info("File " + self.mri_input_dir + " aready exists.")
        
        mri = ManualReqInterval(self.mri_input_dir, self.experiment_name)
        multiflow_obj_list = []
        for src, dst in src_dst_pairs_list:
            flow_spec_list, flow_start_times_us_list = src_dst_pairs_to_flowspecs_dict[(src,dst)]
            multiflow_obj = MultiFlow(src, dst, flow_spec_list, flow_start_times_us_list)  
            multiflow_obj_list.append(multiflow_obj)
        mri_filepath = mri.create_p2p_mri(multiflow_obj_list)
        return mri_filepath

    def prep_experiment_spec_scripts(self, ssird_sim_duration, dctcp_sim_duration, xpass_sim_duration, experiment_name, topo_yaml_file, log_level):
        logger.info("-----\nPreparing experiment spec scripts")
        try:
            logger.info("### Creating spec scripts parent dir: " + self.param_scripts_dir)
            Path(self.param_scripts_dir).mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            logger.info("#### WARNING: File " + self.param_scripts_dir + " aready exists.")

        sim_script = SimSpecScript(self.param_scripts_dir, self.experiment_name) 
        mri_relative_path = "{}{}/{}.csv".format(MRI_RELATIVE_PATH, self.experiment_family, experiment_name)
        ssird_sim_script_path = sim_script.create_ssird_noburst_params_script(mri_relative_path, ssird_sim_duration, topo_yaml_file, log_level)
        dctcp_sim_script_path = sim_script.create_dctcp_noburst_params_script(mri_relative_path, dctcp_sim_duration, topo_yaml_file, log_level)
        xpass_sim_script_path = sim_script.create_xpass_noburst_params_script(mri_relative_path, xpass_sim_duration, topo_yaml_file, log_level)

        return ssird_sim_script_path, dctcp_sim_script_path, xpass_sim_script_path

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
    def write_app_trace_paths_to_file(proto, experiment_family, title_addendum, num_flows_list, target_flow_rate_gbps, experiment_date, app_trace_file_paths_list):
        logger.info("-----\nBacking up app trace file paths")
        num_flow_list_str = "+".join(str(num_flow) for num_flow in num_flows_list)
        parent_dir = f"{APP_TRACE_PATHS_BACKUP_PATH}{experiment_family}/{title_addendum}_{num_flow_list_str}flo_{round(target_flow_rate_gbps)}Gbps_{experiment_date}/"
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
    def get_experiment_name(num_flows, target_flow_rate_gbps, byteload_size_B, byteload_interval_ns, experiment_date="nodate"):
        # if experiment_date is None:
            # experiment_date = Experiment.get_date_now_formatted()
        return "{}flo-{}Gbps-{}B-{}ns-{}".format(num_flows, round(target_flow_rate_gbps), byteload_size_B, byteload_interval_ns, experiment_date)
    
    @staticmethod
    def get_date_now_formatted():
        return datetime.datetime.now().strftime("%Y-%m-%dT_%H-%M-%SZ")

class ExperimentGroup:

    def __init__(self,
                    experiment_family,
                    experiment_date,
                    proto_names_list,
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
                    is_full_postproc=False,
                    log_level=LOG_LEVEL_2,
                    title_addendum=""
                ):

        self.experiment_family = experiment_family
        self.experiment_date = experiment_date
        self.proto_names_l = proto_names_list
        self.topo_yaml_file = topo_yaml_file
        self.src_dst_pairs_list = src_dst_pairs_list
        self.num_flows_list = num_flows_list
        self.byteload_size_B_list = byteload_size_B_list
        self.target_mean_byteload_interval_nanosec_list = target_mean_byteload_interval_nanosec_list
        self.target_flow_rate_gbps = target_flow_rate_gbps
        self.src_dst_pairs_to_flowspecs_dict_list = src_dst_pairs_to_flowspecs_dict_list
        self.is_full_postproc = is_full_postproc
        self.ssird_sim_dur_list = ssird_sim_dur_list
        self.dctcp_sim_dur_list = dctcp_sim_dur_list
        self.xpass_sim_dur_list = xpass_sim_dur_list
        self.title_addendum = title_addendum
        self.log_level = log_level

        self.check_inputs()

        self.ssird_raw_experiment_results_list = [None] * self.num_experiments
        self.dctcp_raw_experiment_results_list = [None] * self.num_experiments
        self.xpass_raw_experiment_results_list = [None] * self.num_experiments
        self.processed_results_list = []

    def check_inputs(self):

        # print(len(self.byteload_size_B_list), len(self.target_mean_byteload_interval_nanosec_list), len(self.src_dst_pairs_to_flowspecs_dict_list))
        assert(len(set([
            len(self.byteload_size_B_list),
            len(self.target_mean_byteload_interval_nanosec_list),
            len(self.src_dst_pairs_to_flowspecs_dict_list),
            ])) == 1)
        self.num_experiments = len(self.src_dst_pairs_to_flowspecs_dict_list)

        for exp_id in range(len(self.src_dst_pairs_to_flowspecs_dict_list)):
            src_dst_pairs_to_flowspecs_dict = self.src_dst_pairs_to_flowspecs_dict_list[exp_id]
            assert(len(self.src_dst_pairs_list) == len(src_dst_pairs_to_flowspecs_dict))
            for src, dst in self.src_dst_pairs_list:
                assert((src,dst) in src_dst_pairs_to_flowspecs_dict)
                flow_spec_list, flow_start_times_us_list = src_dst_pairs_to_flowspecs_dict[(src,dst)]
                assert(len(flow_spec_list) == self.num_flows_list[exp_id])
                assert(len(flow_start_times_us_list) == self.num_flows_list[exp_id])

    def perform_experiment(self):
        self.run_group()
        self.post_process_results()
        return self.generate_overall_experiment_metrics()
    
    def run_group(self):
        logger.info("\n##### RUN GROUP #####")
        logger.info(f"SSIRD POLICY: {SSIRD_POLICY}")
        logger.info(f"Experiment started at: {datetime.datetime.now()}")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures_list = []

            for exp_id in range(0, self.num_experiments):
                for proto in self.proto_names_l:
                    num_flows = self.num_flows_list[exp_id]
                    # NOTE: 11/08/2025: currently all byteloads have the same size.
                    byteload_size_B = self.byteload_size_B_list[exp_id]
                    byteload_interval_ns = self.target_mean_byteload_interval_nanosec_list[exp_id]
                    # experiment_name = Experiment.get_experiment_name(num_flows, self.target_flow_rate_gbps, byteload_size_B, byteload_interval_ns, self.experiment_date) + self.title_addendum
                    experiment_name = "{}{}__{}".format(self.experiment_family, self.title_addendum, Experiment.get_experiment_name(num_flows, self.target_flow_rate_gbps, byteload_size_B, byteload_interval_ns, self.experiment_date))
                    experiment = Experiment(
                        self.experiment_family,
                        experiment_name,
                        proto,
                        self.topo_yaml_file,
                        self.src_dst_pairs_list,
                        num_flows,
                        self.target_flow_rate_gbps,
                        self.src_dst_pairs_to_flowspecs_dict_list[exp_id],
                        self.is_full_postproc
                    ) 

                    # submit experiment to thread pool
                    future = executor.submit(
                        experiment.run,
                        exp_id,
                        ssird_sim_dur_l=self.ssird_sim_dur_list[exp_id],
                        dctcp_sim_dur_l=self.dctcp_sim_dur_list[exp_id],
                        xpass_sim_dur_l=self.xpass_sim_dur_list[exp_id],
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
                    elif raw_result.proto == XPASS_PROTO_NAME:
                        self.xpass_raw_experiment_results_list[exp_id] = raw_result
                    else:
                        logger.error(f"Unrecognised protocol name '{raw_result.proto}' in experiment result! (experiment_name={experiment_name})")
                except Exception as e:
                    logger.error(f"Experiment {experiment_name} failed: {str(e)}")

        if (SSIRD_PROTO_NAME in self.proto_names_l):
            assert(all(r.exp_id == i for r, i in zip(self.ssird_raw_experiment_results_list, range(0, self.num_experiments))))
        if (DCTCP_PROTO_NAME in self.proto_names_l):
            assert(all(r.exp_id == i for r, i in zip(self.dctcp_raw_experiment_results_list, range(0, self.num_experiments))))
        if (XPASS_PROTO_NAME in self.proto_names_l):
            assert(all(r.exp_id == i for r, i in zip(self.xpass_raw_experiment_results_list, range(0, self.num_experiments))))

        ssird_path_to_app_trace_files_list = [r.app_trace_file_path for r in self.ssird_raw_experiment_results_list if r is not None]
        Experiment.write_app_trace_paths_to_file(SSIRD_PROTO_NAME, self.experiment_family, self.title_addendum, self.num_flows_list, self.target_flow_rate_gbps, self.experiment_date, ssird_path_to_app_trace_files_list)
        dctcp_path_to_app_trace_files_list = [r.app_trace_file_path for r in self.dctcp_raw_experiment_results_list if r is not None]
        Experiment.write_app_trace_paths_to_file(DCTCP_PROTO_NAME, self.experiment_family, self.title_addendum, self.num_flows_list, self.target_flow_rate_gbps, self.experiment_date, dctcp_path_to_app_trace_files_list)
        xpass_path_to_app_trace_files_list = [r.app_trace_file_path for r in self.xpass_raw_experiment_results_list if r is not None]
        Experiment.write_app_trace_paths_to_file(XPASS_PROTO_NAME, self.experiment_family, self.title_addendum, self.num_flows_list, self.target_flow_rate_gbps, self.experiment_date, xpass_path_to_app_trace_files_list)
        logger.info(f"Simulations ended at: {datetime.datetime.now()}")
    
    def post_process_results(self):
        logger.info("\n##### POST PROCESS RESULTS #####")
        for exp_id in range(0, self.num_experiments):
            logger.info(f"=====\n** Num Flows: {self.num_flows_list[exp_id]}, Target Flow Rate (Gbps): {self.target_flow_rate_gbps}, ssird_sim_dur (s): {self.ssird_sim_dur_list[exp_id]}, dctcp_sim_dur (s): {self.dctcp_sim_dur_list[exp_id]}")

            ssird_result = self.ssird_raw_experiment_results_list[exp_id]
            if ssird_result == None:
                logger.error("No results for SSIRD")
                ssird_exp_metrics = None
                ssird_sorted_flowsize_fct_list = None
            else:
                logger.info(f"Processing SIRD results exp_id {ssird_result.exp_id}:: {ssird_result.num_flows}flo-{ssird_result.target_flow_rate_gbps}Gbps_target")
                ssird_exp_metrics, ssird_flow_stats_dict = ssird_result.process_results_fct()
                ssird_sorted_flowsize_fct_list = ExperimentGroup.get_sorted_flowsize_fct(ssird_flow_stats_dict)
                logger.info(f"{ssird_exp_metrics.proto} FCT (ms): {ssird_exp_metrics.fct_list}\nApp Gdpt (overall): {ssird_exp_metrics.total_app_gdpt_gbps_measured} Gbps\nApp Gdpt (per flow): {ssird_exp_metrics.app_gdpt_gbps_measured_per_flow_list}\nNetwork Gdpt (overall): {ssird_exp_metrics.total_nw_gdpt_gbps_measured}\nNetwork Gdpt (per flow): {ssird_exp_metrics.nw_gdpt_gbps_measured_per_flow_list}")

            dctcp_result = self.dctcp_raw_experiment_results_list[exp_id]
            if dctcp_result == None:
                logger.error("No results for DCTCP")
                dctcp_exp_metrics = None
                dctcp_sorted_flowsize_fct_list = None
            else:
                logger.info(f"Processing DCTCP results exp_id {dctcp_result.exp_id}:: {dctcp_result.num_flows}flo-{dctcp_result.target_flow_rate_gbps}Gbps_target")
                dctcp_exp_metrics, dctcp_flow_stats_dict = dctcp_result.process_results_fct()
                dctcp_sorted_flowsize_fct_list = ExperimentGroup.get_sorted_flowsize_fct(dctcp_flow_stats_dict)
                logger.info(f"{dctcp_exp_metrics.proto} FCT (ms): {dctcp_exp_metrics.fct_list}\nApp Gdpt (overall): {dctcp_exp_metrics.total_app_gdpt_gbps_measured} Gbps\nApp Gdpt (per flow): {dctcp_exp_metrics.app_gdpt_gbps_measured_per_flow_list}\nNetwork Gdpt (overall): {dctcp_exp_metrics.total_nw_gdpt_gbps_measured}\nNetwork Gdpt (per flow): {dctcp_exp_metrics.nw_gdpt_gbps_measured_per_flow_list}")

            xpass_result = self.xpass_raw_experiment_results_list[exp_id]
            if xpass_result == None:
                logger.error("No results for ExpressPass")
                xpass_exp_metrics = None
                xpass_sorted_flowsize_fct_list = None
            else:
                logger.info(f"Processing ExpressPass results exp_id {xpass_result.exp_id}:: {xpass_result.num_flows}flo-{xpass_result.target_flow_rate_gbps}Gbps_target")
                xpass_exp_metrics, xpass_flow_stats_dict = xpass_result.process_results_fct()
                xpass_sorted_flowsize_fct_list = ExperimentGroup.get_sorted_flowsize_fct(xpass_flow_stats_dict)
                logger.info(f"{xpass_exp_metrics.proto} FCT (ms): {xpass_exp_metrics.fct_list}\nApp Gdpt (overall): {xpass_exp_metrics.total_app_gdpt_gbps_measured} Gbps\nApp Gdpt (per flow): {xpass_exp_metrics.app_gdpt_gbps_measured_per_flow_list}\nNetwork Gdpt (overall): {xpass_exp_metrics.total_nw_gdpt_gbps_measured}\nNetwork Gdpt (per flow): {xpass_exp_metrics.nw_gdpt_gbps_measured_per_flow_list}")
            
            processed_result = ExperimentResultsProcessed(ssird_exp_metrics, dctcp_exp_metrics, xpass_exp_metrics, ssird_sorted_flowsize_fct_list, dctcp_sorted_flowsize_fct_list, xpass_sorted_flowsize_fct_list)
            self.processed_results_list.append(processed_result)

    def generate_overall_experiment_metrics(self):
        logger.info("\n##### GENERATE METRICS #####")
        logger.info(f"SSIRD POLICY: {SSIRD_POLICY}")
        logger.info(f"{self.experiment_family}{self.title_addendum}")
        return ExperimentGroupResultsProcessed(self.processed_results_list)

    @staticmethod
    def get_sorted_flowsize_fct(flow_stats_dict):
        srcdst_to_flowstatslist_dict = {}

        for key, flow_stat in flow_stats_dict.items():
            # initialise vals (empty lists) in srcdst_to_flowstatslist_dict
            src_or_dst_1, src_or_dst_2, flow_id = key
            srcdst_to_flowstatslist_dict[(src_or_dst_1, src_or_dst_2)] = []

        for key, flow_stat in flow_stats_dict.items():
            # append to vals (lists) in scrdst_to_flowstatslist_dict
            src_or_dst_1, src_or_dst_2, flow_id = key
            srcdst_to_flowstatslist_dict[(src_or_dst_1, src_or_dst_2)].append(flow_stat)

        # print("======")
        flow_size_fct_list = [] # contains flows across all sender rcvr pairs in this experiment
        for srcdst, flow_stat_list in srcdst_to_flowstatslist_dict.items():
            # print(f"srcdst={srcdst}")
            for flow_stat in flow_stat_list:
                fct = flow_stat.end_time_s - flow_stat.start_time_s
                # print(f"flow_id={flow_stat.flow_id}, flow_size_B={flow_stat.total_data_bytes_recv_B}, FCT(s)={flow_stat.end_time_s - flow_stat.start_time_s}")
                flow_size_fct_list.append((flow_stat.total_data_bytes_recv_B, fct))
        flow_size_fct_list.sort(key=lambda x: x[0]) # sort by flow size
        # print(f"{flow_size_fct_list}")
        
        return flow_size_fct_list


    @staticmethod
    def process_side_loaded_results(proto, src_dst_pairs_list, num_flows_list, src_dst_pairs_to_flowspecs_dict_list, target_flow_rate_gbps, app_trace_paths_list):
        # TODO: update to use src_dst_pairs_to_flowspecs_dict
        # NOTE: this mtd can only read results for 1 proto at a time
        assert(len(set( [len(src_dst_pairs_to_flowspecs_dict_list), len(app_trace_paths_list)] )) == 1)
        processed_results_list = []
        for i in range(0, len(app_trace_paths_list)):
            exp_output_raw = ExperimentOutputRaw(exp_id=None,
                                              experiment_family=None,
                                              experiment_name=None,
                                              app_trace_file_path=app_trace_paths_list[i],
                                              proto=proto,
                                              src_dst_pairs_list=src_dst_pairs_list,
                                              src_dst_pairs_to_flowspecs_dict=src_dst_pairs_to_flowspecs_dict_list[i],
                                              num_flows=num_flows_list[i],
                                              target_flow_rate_gbps=target_flow_rate_gbps)
            exp_metrics, flow_stats_dict = exp_output_raw.process_results_fct() 
            sorted_flowsize_fct_list = ExperimentGroup.get_sorted_flowsize_fct(flow_stats_dict)
            if (SSIRD_PROTO_NAME in proto):
                processed_result = ExperimentResultsProcessed(ssird_experiment_metrics=exp_metrics, ssird_sorted_flowsize_fct_list=sorted_flowsize_fct_list)
            elif (DCTCP_PROTO_FAMILY_NAME in proto):
                processed_result = ExperimentResultsProcessed(dctcp_experiment_metrics=exp_metrics, dctcp_sorted_flowsize_fct_list=sorted_flowsize_fct_list)
            elif (XPASS_PROTO_NAME in proto):
                processed_result = ExperimentResultsProcessed(xpass_experiment_metrics=exp_metrics, xpass_sorted_flowsize_fct_list=sorted_flowsize_fct_list)
            else:
                raise ValueError(f"Unrecognised protocol name: {proto}")
            processed_results_list.append(processed_result)
        exp_metrics = ExperimentGroupResultsProcessed(processed_results_list)
        
        print(f"Src-Dst pairs list: {src_dst_pairs_list}")
        print(f"Num Flows: {num_flows_list}")
        print(f"Target Flow Rate (Gbps): {target_flow_rate_gbps}")

        print(f"APP Gdpt Gbps measured (SSIRD): {exp_metrics.total_app_gdpt_gbps_measured_list_ssird }")
        print(f"APP Gdpt Gbps measured (DCTCP): {exp_metrics.total_app_gdpt_gbps_measured_list_dctcp}")
        print(f"APP Gdpt Gbps measured (XPass): {exp_metrics.total_app_gdpt_gbps_measured_list_xpass}")
        print(f"APP Gdpt Gbps measured per flow (SSIRD): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_ssird}")
        print(f"APP Gdpt Gbps measured per flow (DCTCP): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_dctcp}")
        print(f"APP Gdpt Gbps measured per flow (XPass): {exp_metrics.app_gdpt_gbps_measured_per_flow_list_list_xpass}")

        print(f"NW Gdpt Gbps measured (SSIRD): {exp_metrics.total_nw_gdpt_gbps_measured_list_ssird}")
        print(f"NW Gdpt Gbps measured (DCTCP): {exp_metrics.total_nw_gdpt_gbps_measured_list_dctcp}")
        print(f"NW Gdpt Gbps measured (Xpass): {exp_metrics.total_nw_gdpt_gbps_measured_list_xpass}")
        print(f"NW Gdpt Gbps measured per flow (SSIRD): {exp_metrics.nw_gdpt_gbps_measured_per_flow_list_list_ssird}")
        print(f"NW Gdpt Gbps measured per flow (DCTCP): {exp_metrics.nw_gdpt_gbps_measured_per_flow_list_list_dctcp}")
        print(f"NW Gdpt Gbps measured per flow (XPass): {exp_metrics.nw_gdpt_gbps_measured_per_flow_list_list_xpass}")

        print(f"* SSIRD FCT: {exp_metrics.ssird_fct_list}")
        print(f"* DCTCP FCT: {exp_metrics.dctcp_fct_list}")
        print(f"* XPass FCT: {exp_metrics.xpass_fct_list}")

        print(f"** SSIRD FCT sorted: {exp_metrics.sorted_flowsize_fct_list_list_ssird}")
        print(f"** DCTCP FCT sorted: {exp_metrics.sorted_flowsize_fct_list_list_dctcp}")
        print(f"** XPass FCT sorted: {exp_metrics.sorted_flowsize_fct_list_list_xpass}")

        return exp_metrics, flow_stats_dict


class FlowSpec:
    def __init__(self, num_byteloads, byteload_size_B_list, flow_size_B, interval_us_list, byteload_rel_timestamp_us_list, total_flow_send_duration_us, flow_rate_bps):
        self.num_byteloads = num_byteloads
        # NOTE: 11/08/2025: currently all byteloads in each FlowSpec list have the same size.
        self.byteload_size_B_list = byteload_size_B_list 
        self.flow_size_B = flow_size_B
        self.interval_us_list = interval_us_list
        self.byteload_rel_timestamp_us_list = byteload_rel_timestamp_us_list
        self.total_flow_send_duration_us = total_flow_send_duration_us
        self.flow_rate_bps = flow_rate_bps
        self.check_spec()

    def check_spec(self):
        if (self.num_byteloads > 1):
            assert(len(set([
                self.num_byteloads,
                len(self.byteload_size_B_list),
                len(self.interval_us_list) + 1,
                len(self.byteload_rel_timestamp_us_list)
            ])) == 1)
        else:
            assert(self.num_byteloads > 0)
            assert(len(set([
                self.num_byteloads,
                len(self.byteload_size_B_list),
                len(self.byteload_rel_timestamp_us_list)
            ])) == 1)
            assert(len(self.interval_us_list) == 0)

    def to_dict(self):
        # Convert the FlowSpec object to a dictionary.
        return {
            'num_byteloads': self.num_byteloads,
            'byteload_size_B_list': self.byteload_size_B_list,
            'flow_size_B': self.flow_size_B,
            'interval_us_list': self.interval_us_list,
            'byteload_timestamp_us_list': self.byteload_rel_timestamp_us_list,
            'total_flow_send_duration_us': self.total_flow_send_duration_us,
            'flow_rate_bps': self.flow_rate_bps
        }

    @staticmethod
    def convert_src_dst_pairs_flowspec_dict_list_to_jsondict(src_dst_pairs_to_flowspecs_dict_list):
        all_experiment_inputs_json = {}
        for i in range(len(src_dst_pairs_to_flowspecs_dict_list)):
            src_dst_pairs_to_flowspecs_dict = src_dst_pairs_to_flowspecs_dict_list[i]
            src_dst_pairs_to_flowspecs_json = {}
            for src, dst in src_dst_pairs_to_flowspecs_dict:
                key = f"{src},{dst}"
                flow_spec_list, flow_start_times_us_list = src_dst_pairs_to_flowspecs_dict[(src,dst)]
                val = FlowSpec.flow_spec_list_to_dict(flow_spec_list, flow_start_times_us_list)
                src_dst_pairs_to_flowspecs_json[key] = val

            all_experiment_inputs_json[i] = src_dst_pairs_to_flowspecs_json
        return all_experiment_inputs_json


    @staticmethod
    def parse_src_dst_pairs_flowspec_dict_list_from_jsonfile(parent_dir, file_name):
        file_path = parent_dir + file_name
        with open(file_path, 'r') as f:
            all_experiment_inputs_json = json.load(f)

        src_dst_pairs_to_flowspecs_dict_list = []
        for exp_id in range(len(all_experiment_inputs_json)):
            exp_input_json = all_experiment_inputs_json[str(exp_id)]
            src_dst_pairs_to_flowspecs_dict = {}
            for src_dst_str, flow_spec_list_dict in exp_input_json.items():
                src_dst_list = src_dst_str.split(",")
                assert(len(src_dst_list) == 2)
                src = int(src_dst_list[0])
                dst = int(src_dst_list[1])
                flow_spec_list, flow_start_times_us_list = FlowSpec.dict_to_flow_spec_list_info(flow_spec_list_dict)
                src_dst_pairs_to_flowspecs_dict[(src,dst)] = (flow_spec_list, flow_start_times_us_list)
            src_dst_pairs_to_flowspecs_dict_list.append(src_dst_pairs_to_flowspecs_dict)

        return src_dst_pairs_to_flowspecs_dict_list

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
    def dict_to_flow_spec_list_info(dict):
        flow_start_times_us_list = dict['flow_start_times_us_list']
        flow_spec_dict_dict = dict['flow_spec_dict_dict']
        flow_spec_list = []
        for _, flow_spec_dict in flow_spec_dict_dict.items():
            flow_spec = FlowSpec(
                num_byteloads=flow_spec_dict['num_byteloads'],
                byteload_size_B_list=flow_spec_dict['byteload_size_B_list'],
                flow_size_B=flow_spec_dict['flow_size_B'],
                interval_us_list=flow_spec_dict['interval_us_list'],
                byteload_rel_timestamp_us_list=flow_spec_dict['byteload_timestamp_us_list'],
                total_flow_send_duration_us=flow_spec_dict['total_flow_send_duration_us'],
                flow_rate_bps=flow_spec_dict['flow_rate_bps']
            )
            flow_spec_list.append(flow_spec)
        
        return flow_spec_list, flow_start_times_us_list

    @staticmethod
    def flow_spec_list_list_to_dict(flow_spec_list_list, flow_start_times_us_list_list):
        assert(len(flow_spec_list_list) == len(flow_start_times_us_list_list))
        num_experiments = len(flow_spec_list_list)
        exp_flows_dict_dict = {}
        for i in range(0, num_experiments):
            flow_spec_list = flow_spec_list_list[i]
            flow_start_times_us_list = flow_start_times_us_list_list[i]
            exp_flows_dict = FlowSpec.flow_spec_list_to_dict(flow_spec_list, flow_start_times_us_list)
            exp_flows_dict_dict[i] = exp_flows_dict
        return exp_flows_dict_dict

    @staticmethod
    def write_jsondict_to_jsonfile(dict, parent_dir, file_name):
        Path(parent_dir).mkdir(parents=True, exist_ok=True)
        file_path = parent_dir + file_name
        with open(file_path, 'w') as file:
            json.dump(dict, file, indent=None)
            # json.dump(dict, file, indent=4)

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
                byteload_rel_timestamp_us_list=flow_spec_dict['byteload_timestamp_us_list'],
                total_flow_send_duration_us=flow_spec_dict['total_flow_send_duration_us'],
                flow_rate_bps=flow_spec_dict['flow_rate_bps']
            )
            flow_spec_list.append(flow_spec)
        
        return flow_start_times_us_list, flow_spec_list

    @staticmethod
    def parse_multi_exp_flow_specs_json_file(parent_dir, file_name):
        file_path = parent_dir + file_name
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        flow_spec_list_list = []
        flow_start_times_us_list_list = []
        for _, exp_flows_dict_dict in data.items():
            flow_start_times_us_list = exp_flows_dict_dict['flow_start_times_us_list']
            flow_spec_dict_dict = exp_flows_dict_dict['flow_spec_dict_dict']
            flow_spec_list = []

            for _, flow_spec_dict in flow_spec_dict_dict.items():
                flow_spec = FlowSpec(
                    num_byteloads=flow_spec_dict['num_byteloads'],
                    byteload_size_B_list=flow_spec_dict['byteload_size_B_list'],
                    flow_size_B=flow_spec_dict['flow_size_B'],
                    interval_us_list=flow_spec_dict['interval_us_list'],
                    byteload_rel_timestamp_us_list=flow_spec_dict['byteload_timestamp_us_list'],
                    total_flow_send_duration_us=flow_spec_dict['total_flow_send_duration_us'],
                    flow_rate_bps=flow_spec_dict['flow_rate_bps']
                )
                flow_spec_list.append(flow_spec)

            flow_spec_list_list.append(flow_spec_list)
            flow_start_times_us_list_list.append(flow_start_times_us_list)
        
        return flow_start_times_us_list_list, flow_spec_list_list 

class PoissonIntervalGenerator:
    ''' Generate byteload intervals (in NANO-SEC) where for each sample, '''

    def __init__(self, target_mean_interval_ns, max_interval_ns, min_interval_ns, num_intervals, num_samples_needed):
        self.target_mean_interval_ns = target_mean_interval_ns
        self.max_interval_ns = max_interval_ns
        self.min_interval_ns = min_interval_ns
        self.num_intervals = num_intervals
        self.num_samples_needed = num_samples_needed

        self.solve_lambda_max_iter=200
        self.solve_lambda_tolerance=1e-12

        # number of samples generated = (mcmc_iters - burn_in) / mcmc_thinning
        # => num_mcmc_iters = burn_in + num_samples * mcmc_thinning
        self.mcmc_thinning=10
        self.mcmc_burn_in=self.mcmc_thinning*500 #5000
        self.num_mcmc_iters=(self.num_samples_needed*self.mcmc_thinning)+self.mcmc_burn_in #80000
        self.mcmc_random_state=42 # can also be None (?)

        self.check_generator_params()

    def generate_interval_samples_ns_list(self):
        logger.info(f"PoissonIntervalGenerator: Generate Byteload Intervals: (target_mean_ns={self.target_mean_interval_ns}, min_interval_ns={self.min_interval_ns}, max_interval_ns={self.max_interval_ns}, num_intervals={self.num_intervals}, num_samples_needed={self.num_samples_needed})")
        # print(f"PoissonIntervalGenerator: Generate Byteload Intervals:\ntarget_mean_ns={self.target_mean_interval_ns}\nmin_interval_ns={self.min_interval_ns}\nmax_interval_ns={self.max_interval_ns}\nnum_intervals={self.num_intervals}\nnum_samples_needed={self.num_samples_needed}")

        lam = self.solve_lambda_for_mean_discrete(mu=self.target_mean_interval_ns, L=self.min_interval_ns, U=self.max_interval_ns)

        logger.debug(f"Step 1) λ solving for mean={self.target_mean_interval_ns} is {lam:.6f}")
        # print(f"Step 1) λ solving for mean={self.target_mean_interval_ns} is {lam:.6f}")
    
        if (self.num_intervals > 1):
            samples = self.mcmc_trunc_exp_cond_mean_discrete(lam, L=self.min_interval_ns, U=self.max_interval_ns, n=self.num_intervals, mu_target=self.target_mean_interval_ns)

            logger.debug(f"Generated samples: shape={samples.shape}")
            # print(f"Generated samples: shape={samples.shape}")

            num_samples_generated, num_intervals_per_sample = samples.shape
            assert(num_samples_generated >= self.num_samples_needed)
            assert(num_intervals_per_sample == self.num_intervals)

            unique_means = np.unique(np.array(samples).mean(axis=1))

            logger.debug(f"sample unique means (ns): {unique_means}")
            # print(f"sample unique means (ns): {unique_means}")

            assert(len(unique_means == 1))
            assert(unique_means == float(self.target_mean_interval_ns))

        elif (self.num_intervals == 1):
            samples = np.array([[self.target_mean_interval_ns]])
            num_samples_generated = 1
            logger.debug(f"WARN: num_intervals={self.num_intervals}, returning target_mean_interval as single sample.")
            # print(f"WARN: num_intervals={self.num_intervals}, returning target_mean_interval as single sample.")
        
        else:
            samples = np.array([[]])
            num_samples_generated = 0
            logger.debug(f"WARN: num_intervals={self.num_intervals}, returning empty sample list.")
            # print(f"WARN: num_intervals={self.num_intervals}, returning empty sample list.")

        # print(f"\nsamples={samples.tolist()}\n")
        

        logger.debug(f"Step 2) Generated {num_samples_generated} samples, taking first {self.num_samples_needed} samples needed"); 
        # print(f"Step 2) Generated {num_samples_generated} samples, taking first {self.num_samples_needed} samples needed"); 

        return samples[:self.num_samples_needed]

    def check_generator_params(self):
        assert(isinstance(self.max_interval_ns, int))
        assert(isinstance(self.min_interval_ns, int))
        assert(isinstance(self.target_mean_interval_ns, int))
        assert(self.min_interval_ns <= self.target_mean_interval_ns)
        assert(self.target_mean_interval_ns <= self.max_interval_ns)
        assert(self.num_samples_needed * 100 <= self.num_mcmc_iters)

    def solve_lambda_for_mean_discrete(self, mu, L, U):
        """Solve for λ so that the mean of discrete truncated exponential = mu."""
        if not (L <= mu <= U):
            raise ValueError("mu must be between L and U")
        def mean_given_lambda(lam):
            vals = np.arange(L, U+1)
            probs = np.exp(-lam * (vals - L))
            probs /= probs.sum()
            return np.sum(vals * probs)
        # bracket λ
        low, high = -10.0, 10.0  # allow negative λ if mu > mid
        for _ in range(self.solve_lambda_max_iter):
            mid = 0.5*(low + high)
            m_mid = mean_given_lambda(mid)
            if abs(m_mid - mu) < self.solve_lambda_tolerance:
                return mid
            if m_mid > mu:
                low = mid
            else:
                high = mid
        return 0.5*(low + high)

    def discrete_trunc_exp_pmf(self, x, lam, L, U):
        """PMF value for integer x in [L,U]."""
        vals = np.arange(L, U+1)
        probs = np.exp(-lam * (vals - L))
        probs /= probs.sum()
        return probs[int(x - L)]

    def make_feasible_initial_int(self, n, L, U, S):
        """Construct an integer vector with sum S."""
        if not (n * L <= S <= n * U):
            raise ValueError("Target sum outside feasible range.")
        x = np.full(n, S // n, dtype=int)
        total = x.sum()
        diff = S - total
        # Adjust elements to match sum exactly
        idx = 0
        while diff != 0:
            if diff > 0 and x[idx] < U:
                x[idx] += 1
                diff -= 1
            elif diff < 0 and x[idx] > L:
                x[idx] -= 1
                diff += 1
            idx = (idx + 1) % n
        return x

    def mcmc_trunc_exp_cond_mean_discrete(self, lam, L, U, n, mu_target):
        """MCMC sampler for integer truncated exponential conditional on exact mean."""
        rng = np.random.default_rng(self.mcmc_random_state)
        S = int(round(n * mu_target))
        x = self.make_feasible_initial_int(n, L, U, S)
        samples = []

        for step in range(self.num_mcmc_iters):
            i, j = rng.choice(n, size=2, replace=False)
            s_pair = x[i] + x[j]
            # feasible integer range for x[i]
            lower = max(L, s_pair - U)
            upper = min(U, s_pair - L)
            if lower > upper:
                continue
            # propose uniformly among feasible integers
            x_i_new = rng.integers(lower, upper+1)
            x_j_new = s_pair - x_i_new
            
            # MH acceptance ratio
            old_p = self.discrete_trunc_exp_pmf(x[i], lam, L, U) * self.discrete_trunc_exp_pmf(x[j], lam, L, U)
            new_p = self.discrete_trunc_exp_pmf(x_i_new, lam, L, U) * self.discrete_trunc_exp_pmf(x_j_new, lam, L, U)
            accept_ratio = new_p / old_p
            
            if rng.random() < accept_ratio:
                x[i], x[j] = x_i_new, x_j_new
            
            if step >= self.mcmc_burn_in and (step - self.mcmc_burn_in) % self.mcmc_thinning == 0:
                samples.append(x.copy())
        
        return np.array(samples)

class DiscTuncExpDistr:
    ''' A discrete truncated exponential distribution '''

    @staticmethod
    def sample_discrete_trunc_exp(num_samples, lam, lower_bound, upper_bound):
        support = np.arange(lower_bound, upper_bound+1)
        weights = np.exp(-lam * support)
        pmf = weights / weights.sum()
        samples = np.random.choice(support, size=num_samples, p=pmf)
        return samples

class FlowSpecGenerator:

    '''
    Generates a specified number of flows.
        - Flow Inter-arrival times are drawn from an exponential distr.
        - For each flow:
            - Flow rate is fixed to a pre-specified value.
            - Inter-byteload intervals are drawn from an exponential distr.
            - Num of byteloads is drawn from an exponential distr.
            - Each byteload is the same size.
    '''

    RETRY_LIMIT=5

    def __init__(self,
                    num_flows,
                    byteload_size_B,
                    target_mean_byteload_interval_ns=1000,
                    min_interval_ns=1,
                    max_interval_ns=10000,
                    flow_size_distr=None,
                    target_mean_flow_interarr_ns=1000,
                    min_flow_interarr_ns=0,
                    max_flow_interarr_ns=100000,
                    is_use_poisson_byteload_intervals=True,
                    is_use_poisson_flow_interarr=True
                ):
        self.num_flows = num_flows

        self.byteload_size_B = byteload_size_B

        self.target_mean_byteload_interval_ns = target_mean_byteload_interval_ns
        self.min_interval_ns = min_interval_ns
        self.max_interval_ns = max_interval_ns
        self.is_use_poisson_byteload_intervals = is_use_poisson_byteload_intervals

        self.flow_size_distr = flow_size_distr
        assert(self.flow_size_distr is not None)

        self.target_mean_flow_interarr_ns = target_mean_flow_interarr_ns
        self.min_flow_interarr_ns = min_flow_interarr_ns
        self.max_flow_interarr_ns = max_flow_interarr_ns
        self.is_use_poisson_flow_interarr = is_use_poisson_flow_interarr

        self.flow_rate_bps = (byteload_size_B * 8) / (self.target_mean_byteload_interval_ns * pow(10,-9))

    def generate_poisson_flows(self):

        if (self.is_use_poisson_flow_interarr):
            flow_start_times_ns_list = self.generate_flow_start_times_ns_for_all_flows()
        else:
            flow_start_times_ns_list = np.concatenate([[0], np.cumsum([self.target_mean_flow_interarr_ns]*(self.num_flows-1))]).tolist()
        flow_start_times_us_list = [start_ns/1000 for start_ns in flow_start_times_ns_list]
        assert(len(set([
            self.num_flows,
            len(flow_start_times_us_list)
            ])) == 1)

        num_byteloads_list = []
        byteload_size_B_list_list = []
        byteload_intervals_us_list_list = []
        for i in range(0, self.num_flows):

            logger.info(f"\n  Generating flow size for flow={i}")
            # print(f"\n  Generating flow size for flow={i}")
            flow_size_generated_B = self.flow_size_distr.get_flow_size_B()
            byteload_size_B_list = []
            if (flow_size_generated_B < self.byteload_size_B):
                if (flow_size_generated_B < 4):
                    # ensure byteload size is at least 4B
                    flow_size_generated_B = 4
                byteload_size_B_list.append(flow_size_generated_B)
            else:
                remaining_bytes_in_flow = flow_size_generated_B
                while(remaining_bytes_in_flow >= self.byteload_size_B):
                    byteload_size_B_list.append(self.byteload_size_B)
                    remaining_bytes_in_flow -= self.byteload_size_B
                if (remaining_bytes_in_flow > 0):
                    if (remaining_bytes_in_flow < 4):
                        # ensure byteload size is at least 4B
                        remaining_bytes_in_flow = 4
                    byteload_size_B_list.append(remaining_bytes_in_flow)

            num_byteloads = len(byteload_size_B_list)
            num_byteloads_list.append(num_byteloads)
            byteload_size_B_list_list.append(byteload_size_B_list)
            # logger.debug(f"    Flow={i}, flow_size_B={flow_size_B}, num_byteloads={num_byteloads}, byteload_size_B_list={byteload_size_B_list}")
            logger.debug(f"    Flow={i}, flow_size_B={sum(byteload_size_B_list)}, num_byteloads={num_byteloads}, len(byteload_size_B_list)={len(byteload_size_B_list)}")

            logger.info(f"\n  Generating intervals for flow={i}")
            # print(f"\n  Generating intervals for flow={i}")
            num_intervals = num_byteloads - 1
            pig = PoissonIntervalGenerator(self.target_mean_byteload_interval_ns, self.max_interval_ns, self.min_interval_ns, num_intervals, num_samples_needed=1)

            retries_remaining = self.RETRY_LIMIT
            while(retries_remaining > 0):
                try:
                    if (self.is_use_poisson_byteload_intervals):
                        flow_byteload_interval_ns_list = pig.generate_interval_samples_ns_list()[0].tolist()
                    else:
                        flow_byteload_interval_ns_list = [self.target_mean_byteload_interval_ns] * num_intervals
                    break
                except Exception as e:
                    logger.warning(e)
                    retries_remaining -= 1
                    logger.warning(f"retries remaining:{retries_remaining}")
                    # print(f"retries remaining:{retries_remaining}")
                    if (retries_remaining == 0):
                        raise e
            if (num_intervals > 0):
                assert(len(flow_byteload_interval_ns_list) == num_intervals)
                flow_byteload_interval_us_list = [float(intv_ns/1000) for intv_ns in flow_byteload_interval_ns_list]
                byteload_intervals_us_list_list.append(flow_byteload_interval_us_list)
            else:
                assert(len(flow_byteload_interval_ns_list) == 0)
                byteload_intervals_us_list_list.append(flow_byteload_interval_ns_list)
                

        flow_spec_list = []
        for j in range(0, self.num_flows):
            num_byteloads = num_byteloads_list[j]
            byteload_size_B_list = byteload_size_B_list_list[j]
            flow_size_B = sum(byteload_size_B_list)
            interval_us_list = byteload_intervals_us_list_list[j]
            byteload_rel_timestamp_us_list = np.round(np.cumsum(np.concatenate([[0], interval_us_list])), 3).tolist() 
            total_flow_send_duration_us = round(byteload_rel_timestamp_us_list[-1] + flow_start_times_us_list[j], 3)
            # print(f">DEBUG: Flow={j} Final byteload_rel_timestamp_us={byteload_rel_timestamp_us_list[-1]} flow_start_time_us={flow_start_times_us_list[j]} total_flow_send_duration_us={total_flow_send_duration_us}")    

            flow_spec = FlowSpec(
                num_byteloads=num_byteloads,
                byteload_size_B_list=byteload_size_B_list,
                flow_size_B=flow_size_B,
                interval_us_list=interval_us_list,
                byteload_rel_timestamp_us_list=byteload_rel_timestamp_us_list,
                total_flow_send_duration_us=total_flow_send_duration_us,
                flow_rate_bps = self.flow_rate_bps
            )

            flow_spec_list.append(flow_spec)
        
        return flow_spec_list, flow_start_times_us_list

    def generate_flow_start_times_ns_for_all_flows(self):
        lam_flow_interarr = 1/self.target_mean_flow_interarr_ns
        sampled_flow_interarr_ns = DiscTuncExpDistr.sample_discrete_trunc_exp(
            num_samples=self.num_flows,
            lam=lam_flow_interarr,
            lower_bound=self.min_flow_interarr_ns, 
            upper_bound=self.max_flow_interarr_ns
        )
        flow_start_times_ns = np.cumsum(sampled_flow_interarr_ns)
        return flow_start_times_ns.tolist()

class EmpiricalDistr(ABC):
    ''' Is Abstract class for workload flow size distributions '''
    @abstractmethod
    def get_flow_size_B(self):
        pass

    @staticmethod
    def normalize_cdf(cdf):
        """Ensure we store CDF as sorted list of (flow_size, cumulative_prob)."""
        if(isinstance(cdf, dict)):
            cdf = list(cdf.items())
        assert(all(prob >= 0 and prob <= 1 for size, prob in cdf))
        cdf.sort(key=lambda x: x[1])  # sort by probability
        return cdf

    @staticmethod
    def load_cdf_from_file(filename):
        """
        Loads CDF from file like Google_SearchRPC.txt.
        First line might be ignored if its avg size or metadata.
        """
        filepath = Path(filename)
        if (not filepath.exists()):
            raise FileNotFoundError(f"Filepath {filepath} does not exist!")

        cdf = []
        with open(filename, 'r') as f:
            first_line = f.readline().strip()
            try:
                # first line might be a mean or scaling value; ignore it, continue reading actual CDF entries
                float(first_line)  
            except ValueError:
                # first line is be part of CDF
                parts = first_line.split()
                if len(parts) == 2:
                    # parts[0] is flow size; parts[1] is cumulative prob
                    cdf.append((float(parts[0]), float(parts[1])))

            # read rest of lines
            for line in f:
                parts = line.strip().split()
                if len(parts) != 2:
                    continue
                size, prob = float(parts[0]), float(parts[1])
                cdf.append((size, prob))
        
        if (len(cdf) == 0):
            raise ValueError(f"No CDF data found in {filename}")

        return EmpiricalDistr.normalize_cdf(cdf)

    @staticmethod
    def sample_flow_size_from_distr_B(cdf_pairs_list, seed):
        # cdf_pairs_list is in format (<flow_size>, <cumulative_prob>)
        random.seed(seed)
        u = random.random()
        for flow_size, cum_prob in cdf_pairs_list:
            if cum_prob >= u:
                return math.ceil(flow_size)
        return math.ceil(cdf_pairs_list[-1][0])  # fallback to max size

    @staticmethod
    def sample_flow_size_from_distr_numpkt_distr_B(cdf_pairs_list, pktsize_B, seed):
        # cdf_pairs_list is in format (<num_pkts>, <cumulative_prob>)
        random.seed(seed)
        u = random.random()
        for num_pkts, cum_prob in cdf_pairs_list:
            if cum_prob >= u:
                return math.ceil(num_pkts * pktsize_B)
        return math.ceil(cdf_pairs_list[-1][0] * pktsize_B)  # fallback to max size

class FixedDistr(EmpiricalDistr):
    ''' Is workload where each sampled flow has the same fixed flow size '''
    def __init__(self, num_byteloads, byteload_size_B):
        self.cdf_file_name = "NA"
        self.num_byteloads = num_byteloads
        self.byteload_size_B = byteload_size_B

    def get_flow_size_B(self):
        return self.byteload_size_B * self.num_byteloads

class ExpDistr(EmpiricalDistr):
    ''' Is workload where each sampled flow has num_byteloads sampled from an exponential distribution '''
    def __init__(self, byteload_size_B, avg_num_byteloads, min_num_byteloads=10, max_num_byteloads=3000):
        self.cdf_file_name = "NA_ExponentialDistr"
        self.byteload_size_B = byteload_size_B
        self.avg_num_byteloads = avg_num_byteloads
        self.min_num_byteloads = min_num_byteloads
        self.max_num_byteloads = max_num_byteloads

    def generate_num_byteloads(self):
        lam_num_byteloads = 1/self.avg_num_byteloads
        sampled_num_byteloads = DiscTuncExpDistr.sample_discrete_trunc_exp(
            num_samples=1,
            lam=lam_num_byteloads,
            lower_bound=self.min_num_byteloads,
            upper_bound=self.max_num_byteloads
        )
        return sampled_num_byteloads.tolist()[0]

    def get_flow_size_B(self):
        return self.byteload_size_B * self.generate_num_byteloads()

class W1Distr(EmpiricalDistr):
    ''' Is workload where each sampled flow has flow size drawn from analytically-derived manual CDF (rounded to next-highest int) '''
    def __init__(self, seed=None):
        self.seed = seed
        self.cdf = {
            1.0: 0.0,
            3.1623: 0.27,
            10.0: 0.35,
            31.623: 0.5,
            100.0: 0.63,
            316.23: 0.83,
            1000.0: 0.96,
            3162.3: 0.99453,
            10000.0: 0.99971856,
            31623.0: 0.99998841,
            100000.0: 0.99999956,
            316230.0: 0.9999999837,
            1000000.0: 1.0 
        }
        self.cdf = EmpiricalDistr.normalize_cdf(self.cdf)

    def get_flow_size_B(self):
        return EmpiricalDistr.sample_flow_size_from_distr_B(self.cdf, self.seed)

class WxDistr(EmpiricalDistr):
    ''' Is workload where each sampled flow has flow size drawn from a cdf specified in a text file (from sird, homa paper)'''
    def __init__(self, cdf_file_name, seed=None):
        self.cdf_file_name = cdf_file_name
        self.cdf_file_path = PATH_TO_WORKOAD_DISTR_CDF + self.cdf_file_name
        self.seed = seed
        self.cdf = EmpiricalDistr.load_cdf_from_file(self.cdf_file_path)
        assert(self.cdf_file_name != "DCTCP_MsgSizeDist.txt")
    
    def get_flow_size_B(self):
        return EmpiricalDistr.sample_flow_size_from_distr_B(self.cdf, self.seed)

class W5Distr_DctcpMsgSizeDistActual(EmpiricalDistr):
    def __init__(self, seed=None):
        self.cdf_file_name = "DCTCP_MsgSizeDist.txt"
        self.cdf_file_path = PATH_TO_WORKOAD_DISTR_CDF + self.cdf_file_name
        self.seed = seed
        self.pktsize_B = 1442
        self.cdf = EmpiricalDistr.load_cdf_from_file(self.cdf_file_path)
    
    def get_flow_size_B(self):
        return EmpiricalDistr.sample_flow_size_from_distr_numpkt_distr_B(self.cdf, self.pktsize_B, self.seed)

def init_logs(logs_subdir, logs_file_name, log_level=logging.DEBUG):
    full_rel_path = f"{LOGS_REL_PATH}{logs_subdir}/"
    Path(full_rel_path).mkdir(parents=True, exist_ok=True) 
    logs_file_path = full_rel_path + logs_file_name
    logging.basicConfig(
        level=log_level,
        handlers=[
            logging.FileHandler(logs_file_path, mode='w'),
            logging.StreamHandler()
        ]
    )

if __name__ == "__main__":

    num_flows = 5
    byteload_size_B = 1458
    target_mean_byteload_interval_ns = 3000
    # flow_size_distr = FixedDistr(num_byteloads=10, byteload_size_B=1458)
    flow_size_distr = WxDistr("Google_SearchRPC.txt") 
    # flow_size_distr = WxDistr("Google_AllRPC.txt") 
    # flow_size_distr = WxDistr("Facebook_HadoopDist_All.txt") 
    # flow_size_distr = WxDistr("DCTCP_MsgSizeDist.txt") 
    # flow_size_distr = WxDistr("Fabricated_Heavy_Middle.txt") 
    target_mean_flow_interarr_ns = 2000
    is_use_poisson_byteload_intervals = True
    is_use_poisson_flow_interarr = False
    flow_generator = FlowSpecGenerator(
        num_flows=num_flows,
        byteload_size_B=byteload_size_B,
        target_mean_byteload_interval_ns=target_mean_byteload_interval_ns,
        flow_size_distr=flow_size_distr,
        target_mean_flow_interarr_ns=target_mean_flow_interarr_ns,
        is_use_poisson_byteload_intervals=is_use_poisson_byteload_intervals,
        is_use_poisson_flow_interarr=is_use_poisson_flow_interarr
    )

    flow_spec_list, flow_start_times_us_list = flow_generator.generate_poisson_flows()

    print(flow_start_times_us_list)

    for flow in flow_spec_list:
        print(
            f"Flow with {flow.num_byteloads} byteloads | "
            f"Flow Size B: {flow.flow_size_B} B | "
            f"Duration: {flow.total_flow_send_duration_us:.4f}us | "
            f"Flow Rate: {flow.flow_rate_bps*pow(10,-9):.6f} Gbps"
            f"\n    Min Byteload Size (B): {min(flow.byteload_size_B_list)}"
            f"\n    Max Byteload Size (B): {max(flow.byteload_size_B_list)}"
            f"\n    Min Interval (us): {min(flow.interval_us_list) if len(flow.interval_us_list) > 0 else flow.interval_us_list}"
            f"\n    Max Interval (us): {max(flow.interval_us_list) if len(flow.interval_us_list) > 0 else flow.interval_us_list}"
            f"\n"
        )


# if __name__ == "__main__":

#     ''' --- Side-load & analyse existing app trace file ---'''
#     proto = SSIRD_PROTO_NAME

#     num_of_experiments = 2

#     src_dst_pairs_list = [(0,1)]
#     num_flows = 2
#     num_byteloads_list = [1000]
#     byteload_size_B_list = [4000]
#     target_mean_byteload_interval_nanosec_list = [2000]

#     target_flow_rate_gbps = (byteload_size_B_list[0] * 8) / (target_mean_byteload_interval_nanosec_list[0] * pow(10,-9)) * pow(10, -9)

#     app_trace_paths_list = [
#         "/data/dh1723/SIRD-Simulator/scripts/r2p2/coord/results/SSIRD-2flo-16Gbps-2025-08-11T_16-36-33Z_p2p_poisson_fullrange_test/data/SSIRD/60/applications_trace.str",
#     ]

#     # Load flow spec for each experiment from saved json: 
#     flow_start_times_us_list_list, flow_spec_list_list = FlowSpec.parse_multi_exp_flow_specs_json_file(SAVED_FLOW_SPECS_JSON_PATH, "multi_exp_poisson_p2p_2flo-16Gbps-2025-08-11T_16-36-33Z.log")
#     assert(len(flow_spec_list_list) == num_of_experiments)
#     assert(len(flow_start_times_us_list_list) == num_of_experiments)
#     for i in range(0, num_of_experiments):
#         assert(len(flow_start_times_us_list_list[i]) == len(flow_spec_list_list[i]) and len(flow_spec_list_list[i]) == num_flows)

#     flow_spec_list_list_2 = [flow_spec_list_list[-1]]
#     exp_metrics = ExperimentGroup.process_side_loaded_results(proto, src_dst_pairs_list, num_flows, flow_spec_list_list_2, target_flow_rate_gbps, app_trace_paths_list)

