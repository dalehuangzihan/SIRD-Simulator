from pathlib import Path
import csv

# Common experiment param; value is meaningful only when req_interval_distr is not 'manual'
CLIENT_INJECTION_RATE_GBPS = "60"

PATH_TO_SIRD_SIM = "/home/dalehuang/Documents/ICL/msc_proj/SIRD-Simulator/"
PATH_TO_SIM_RESULTS = PATH_TO_SIRD_SIM + "scripts/r2p2/coord/results/"
PATH_TO_EXPERIMENTS = PATH_TO_SIRD_SIM + "scripts/r2p2/coord/config/"
SCRIPTS_RELATIVE_PATH = "dale_experiments/"
PATH_TO_EXPERIMENTS_SCRIPTS = PATH_TO_EXPERIMENTS + SCRIPTS_RELATIVE_PATH
MRI_RELATIVE_PATH = "dale_experiments/"
PATH_TO_EXPERIMENTS_INPUTS = PATH_TO_EXPERIMENTS + "manual-req-intervals/" + MRI_RELATIVE_PATH

class FlowTraceEvent:
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

    @staticmethod
    def read_flow_trace_from_str(str_line):
        tokens = str_line.split(" ")
        assert(len(tokens) == 12)
        return FlowTraceEvent(tokens[0], tokens[1], tokens[2], tokens[3], tokens[4], tokens[5], tokens[6], tokens[7], tokens[8], tokens[9], tokens[10], tokens[11])

class ManualReqInterval:
    # is in seconds; is 1us
    TIME_STEP_S = 0.000001

    def __init__(self, parent_dir):
        self.parent_dir = parent_dir

    def create_p2p_intermittent_mri(self, src, dst, num_byteloads, byteload_size_B, inter_byteload_period_us):
        mri_filepath = self.get_mri_filepath(self.parent_dir, num_byteloads, byteload_size_B, inter_byteload_period_us)
        mri_byteloads_spec = []    
        mri_byteloads_spec.append(str(src))
        time_start = self.TIME_STEP_S
        for i in range(0, num_byteloads):
           byteload_str = "{:f}|{}|{}".format(time_start + i * inter_byteload_period_us * self.TIME_STEP_S, str(dst), byteload_size_B) 
           mri_byteloads_spec.append(byteload_str)
        self.mri_list_to_csv(mri_byteloads_spec, mri_filepath)
        return mri_filepath

    @staticmethod
    def get_mri_filepath(parent_dir, num_byteloads, byteload_size_B, inter_byteload_period_us):
        return parent_dir + ManualReqInterval.get_mri_filename(num_byteloads, byteload_size_B, inter_byteload_period_us) 

    @staticmethod
    def get_mri_filename(num_byteloads, byteload_size_B, inter_byteload_period_us):
        return "{}#-{}B-{}us.csv".format(num_byteloads, byteload_size_B, inter_byteload_period_us)

    @staticmethod
    def mri_list_to_csv(mri_list, mri_filepath):
        with open(mri_filepath, 'w') as mri_file:
            wr = csv.writer(mri_file, quoting=csv.QUOTE_NONE)
            print(mri_list)
            wr.writerow(mri_list)

class SimSpecScript:
    PATH_TO_SSIRD_TEMPLATE_NOBURST = PATH_TO_EXPERIMENTS_SCRIPTS + "template-ssird-2host-p2p-noburst.sh"
    PATH_TO_DCTCP_TEMPLATE_NOBURST = PATH_TO_EXPERIMENTS_SCRIPTS + "template-dctcp-2host-p2p-noburst.sh"

    MANUAL_REQ_INTERVAL_FILE_L = "manual_req_interval_file_l"
    DURATION_MODIFIER_L = "duration_modifier_l"

    def __init__(self, parent_dir):
        self.parent_dir = parent_dir
    
    def create_ssird_noburst_params_script(self, mri_relative_path, num_byteloads, byteload_size_B, inter_byteload_period_us, sim_duration):
        script_filepath = self.parent_dir + self.get_param_script_filename(num_byteloads, byteload_size_B, inter_byteload_period_us)

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

    @staticmethod
    def get_param_script_filename(num_byteloads, byteload_size_B, inter_byteload_period_us):
        return "{}#-{}B-{}us.sh".format(num_byteloads, byteload_size_B, inter_byteload_period_us)


class FctExperiment:
    def __init__(self, experiment_name, sim_name):
        self.experiment_name = experiment_name
        self.proto_name = sim_name
        self.results_file_path = PATH_TO_SIM_RESULTS + experiment_name + "/data/" + sim_name + "/" + CLIENT_INJECTION_RATE_GBPS + "/applications_trace.str" 
        self.flow_trace_event_queue = []
        self.fct = -1

        self.mri_input_dir = PATH_TO_EXPERIMENTS_INPUTS + experiment_name + "/"
        self.param_scripts_dir = PATH_TO_EXPERIMENTS_SCRIPTS + experiment_name + "/"

    def execute(self):
        print("# Execute experiment " + self.experiment_name)

        src = 0
        dst = 1
        num_byteloads = 4
        byteload_size_B = 1000
        inter_byteload_period_us = 100
        # is a heuristic
        sim_duration = 2 * num_byteloads * inter_byteload_period_us * ManualReqInterval.TIME_STEP_S

        print("sim_duration={:f}".format(sim_duration))

        self.prep_experiment_input(src, dst, num_byteloads, byteload_size_B, inter_byteload_period_us)
        self.prep_experiment_spec_scripts(num_byteloads, byteload_size_B, inter_byteload_period_us, sim_duration)
        # self.run_experiment()
        # self.process_results_fct()

        return self.fct
        
    def prep_experiment_input(self, src, dst, num_byteloads, byteload_size_B, inter_byteload_period_us):
        print("## Preparing experiment input MRIs")
        try:
            print("### Creating MRI inputs parent dir: " + self.mri_input_dir)
            Path(self.mri_input_dir).mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            print("File " + self.mri_input_dir + " aready exists.")
        
        mri = ManualReqInterval(self.mri_input_dir)
        mri_filepath = mri.create_p2p_intermittent_mri(src, dst, num_byteloads, byteload_size_B, inter_byteload_period_us)
        return mri_filepath

    def prep_experiment_spec_scripts(self, num_byteloads, byteload_size_B, inter_byteload_period_us, sim_duration):
        print("## Preparing experiment spec scripts")
        try:
            print("### Creating spec scripts parent dir: " + self.param_scripts_dir)
            Path(self.param_scripts_dir).mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            print("File " + self.param_scripts_dir + " aready exists.")

        sim_script = SimSpecScript(self.param_scripts_dir)        
        mri_relative_path = "{}{}/{}".format(MRI_RELATIVE_PATH, self.experiment_name, ManualReqInterval.get_mri_filename(num_byteloads, byteload_size_B, inter_byteload_period_us))
        sim_script.create_ssird_noburst_params_script(mri_relative_path, num_byteloads, byteload_size_B, inter_byteload_period_us, sim_duration)
        return sim_script

    def run_experiment(self):
        print("## Running experiment")
        ''' TODO '''
        pass

    def process_results_fct(self):
        print("## Processing results")
        self.read_app_trace_file()
        self.fct = self.get_full_flow_duration() 
        return self.fct

    def read_app_trace_file(self):
        try:
            with open(self.results_file_path, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    flow_trace_event = FlowTraceEvent.read_flow_trace_from_str(line)
                    self.flow_trace_event_queue.append(flow_trace_event)
        except FileNotFoundError:
            print("The file was not found")
        except IOError:
            print("An error occurred while reading the file")

    '''
    TODO: support filtering by app_level_id
    '''
    def get_full_flow_duration(self):
        final_trace = self.flow_trace_event_queue[len(self.flow_trace_event_queue) - 1]
        assert(final_trace.event == "rrq")
        assert(final_trace.app_level_id == "0")
        return final_trace.req_duration

if __name__ == "__main__":
    experiment_name = "TEST"
    proto_name = "SIRD-dale-2host"
    fct_exp1 = FctExperiment(experiment_name, proto_name) 
    fct = fct_exp1.execute() 
    print(fct)