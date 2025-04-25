import numpy as np
import csv

# Local files
import helper as hlp
import qmon_hlp
import cc_hlp
import app_hlp
import omnet_helper as ohlp
import dcpim_helper as dchlp
import cfg
from pprint import pprint
import multiprocessing
import worker_manager as workm
import time
import os

###############################################################################################################
###############################################################################################################
###############################################################################################################
############################################# Slowdown ########################################################
###############################################################################################################
###############################################################################################################
###############################################################################################################


def aggr_app_data_ts(directory, prot, load, is_omnet=False, create_plots=False):
    """
    Output a csv that reports slowdown percentiles for different message sizes.
    """

    def write_slowdown_data(this_out_dir, p1, p50, p95, p99, p999):
        """
        p* args are dictionaries: bin value (msg size) -> slowdown
        The bin values should be the same across p* arguments.
        """
        size_col = np.array(list(p1.keys())).reshape((len(p1.keys()), 1))
        p1col = np.array(list(p1.values())).reshape((len(p1.keys()), 1))
        p50col = np.array(list(p50.values())).reshape((len(p1.keys()), 1))
        p95col = np.array(list(p95.values())).reshape((len(p1.keys()), 1))
        p99col = np.array(list(p99.values())).reshape((len(p1.keys()), 1))
        p999col = np.array(list(p999.values())).reshape((len(p1.keys()), 1))

        data = np.concatenate(
            (size_col, p1col, p50col, p95col, p99col, p999col), axis=1
        )
        hlp.make_dir(this_out_dir)
        file_name = f"{this_out_dir}/slowdown.csv"
        header = "size,p1,p50,p95,p99,p999"
        np.savetxt(file_name, data, delimiter=",", fmt=[
                   "%.2f", "%.2f", "%.2f", "%.2f", "%.2f", "%.2f"], header=header, comments="")

    def process_load_lvl(ldir, out_dir, prot, load, param_file):
        params = hlp.import_param_file(param_file)
        app_file = f"{ldir}/{cfg.APP_FILE}"
        data = app_hlp.load_app_data(app_file)
        if data.shape[0] == 0:
            return
        # The loaded timestamps start at 0s (and not 10s)
        start = 0
        trace_end = float(params["sim_dur"][0])
        data = hlp.trim_by_timestamp(
            data, start, trace_end, app_hlp.app_cols["timestamp"])
        sldwn_view = data[data[:, app_hlp.app_cols["event"]]
                          == app_hlp.app_events["rrq"]]
        sldwn_view = sldwn_view[:, (app_hlp.app_cols["timestamp"],
                                    app_hlp.app_cols["req_size"],
                                    app_hlp.app_cols["remote_addr"],
                                    app_hlp.app_cols["local_addr"],
                                    app_hlp.app_cols["req_dur"])]

        # Returns columns (ts, req_size, slowdown)
        slowdown = app_hlp.calculate_slowdown(params, sldwn_view, param_file,
                                              # with this "is_intra_rack" funtion, the next 3 arguments don't matter
                                              0, 1, 2, 3, 4, app_hlp.is_intra_rack,
                                              0, 0, 0,
                                              sortBySize=True)

        bin_count = min(int(slowdown.shape[0] / 500), 50)
        if bin_count == 0:
            print("Not enough datapoints to produce slowdown vs msg_size plot. Returning")
            return
        median, tail99, tail999, tail95, tail1, mean = app_hlp.get_slowdown_vs_size(slowdown, 1, 2, bin_count)
        if create_plots:
            app_hlp.plot_slowdown_vs_size(tail1, "1th% Slowdown", prot, load, out_dir)
            app_hlp.plot_slowdown_vs_size(median, "50th% Slowdown", prot, load, out_dir)
            app_hlp.plot_slowdown_vs_size(tail95, "95th% Slowdown", prot, load, out_dir)
            app_hlp.plot_slowdown_vs_size(tail99, "99th% Slowdown", prot, load, out_dir)
            app_hlp.plot_slowdown_vs_size(tail999, "99.9th% Slowdown", prot, load, out_dir)

        # Write to csv
        write_slowdown_data(out_dir, tail1, median, tail95, tail99, tail999)

    out_dir = f"{directory}/{cfg.OUT_DIR_NAME}/app"
    hlp.make_dir(out_dir)
    param_file = f"{directory}/parameters"
    if is_omnet:
        data_dir = f"{directory}/extracted_results"
        raise Exception("aggr_app_data_ts() not implemented for OMNET")
        # process_load_lvl_omnet(data_dir, out_dir, prot, load, param_file)
    else:
        process_load_lvl(directory, out_dir, prot, load, param_file)


###############################################################################################################
###############################################################################################################
###############################################################################################################
######################################## Queuing and Throughput ###############################################
###############################################################################################################
###############################################################################################################
###############################################################################################################


def plot_qts_data(this_out_dir, data, origin_area, origin, end_area, end, prot):
    out_dir_q = f"{this_out_dir}/plots/qing"
    out_dir_t = f"{this_out_dir}/plots/throughput"
    name = f"{origin_area}_{origin}_{end_area}_{end}"
    hlp.make_dir(out_dir_q)
    hlp.make_dir(out_dir_t)
    # Plot Qing
    hlp.plot_time_series(data[:, (0, 2)], out_dir_q, f"{name}", prot, "Queuing (KB)")

    # Plot Thrpt
    hlp.plot_time_series(
        data[:, (0, 1)], out_dir_t, f"{name}", prot, "Throughput (Gbps)"
    )


def write_qts_data(this_out_dir, data, origin_area, origin, end_area, end):
    hlp.make_dir(this_out_dir)
    file_name = f"{this_out_dir}/qts_{origin_area}_{origin}_{end_area}_{end}.csv"
    header = "timestamp,throughput_gbps,queueing_KB"
    np.savetxt(file_name, data, delimiter=",", fmt=[
               "%.12f", "%.2f", "%.2f"], header=header, comments="")

def aggr_q_data_ts_task(file_name, adir, params, out_dir, origin_area, end_area, create_plots, prot):
    file_path = f"{adir}/{file_name}"
    origin = file_name.split("_")[0]
    end = file_name.split("_")[1].split(".")[0]
    stop = float(params["sim_dur"][0])
    data = qmon_hlp.load_and_trim_qmon_data(file_path, stop)
    thrpt_data = data[:,
                        (qmon_hlp.qmon_cols["timestamp"],
                        qmon_hlp.qmon_cols["byte_departures"])]

    thrpt_data = ohlp.calc_thrpt(thrpt_data)

    q_data = data[:,
                    (qmon_hlp.qmon_cols["timestamp"],
                    qmon_hlp.qmon_cols["q_sz_bytes"])]
    q_data = q_data[1:, :]
    q_data[:, 1] = q_data[:, 1] / 1000.0

    # Write one file per link
    this_out_dir = f"{out_dir}/{origin_area}"
    data = thrpt_data
    data = np.append(data, q_data[:, 1].reshape(
        q_data.shape[0], 1), axis=1)
    write_qts_data(this_out_dir, data,
                    origin_area, origin, end_area, end)
    if create_plots:
        plot_qts_data(this_out_dir, data,
                        origin_area, origin, end_area, end, prot)

def aggr_q_data_ts(directory, prot, load, simulator, create_plots=False):
    def process_load_lvl(ldir, out_dir, prot, load, param_file):
        print(f"Qts Processing {ldir}")
        data_dir = f"{ldir}/qmon"
        params = hlp.import_param_file(param_file)
        area_subdirs = hlp.get_subdirs(data_dir)

        pool = []

        for adir in area_subdirs:
            area = adir.split("/")[-1]
            origin_area = area.split("_")[0]
            end_area = area.split("_")[1]

            files = hlp.get_files(adir)

            for file_name in files:
                pool.append(workm.Task(aggr_q_data_ts_task, (file_name, adir, params, out_dir, origin_area, end_area, create_plots, prot)))

        if len(pool) > 0:
            workm.add_tasks(pool, task_family="Qts subpool", suggested_batch_size=5)


    def process_load_lvl_omnet(data_dir, out_dir, prot, load, param_file):
        print(f"Qts omnet Processing {data_dir}")
        params = hlp.import_param_file(param_file)
        byte_dir = f"{data_dir}/{ohlp.OMNET_BYTE_SAMPLE}"
        q_dir = f"{data_dir}/{ohlp.OMNET_Q_SAMPLE}"

        ifaces, q_data, byte_data, num_aggr, num_tor, num_host_per_tor = ohlp.get_qlen_and_byte_data(
            byte_dir, q_dir)

        # Each two columns map to one interface. So for each iface, calculate thrpt and queueing
        for i, iface in enumerate(ifaces):
            idx = 2 * i

            origin, origin_area, end, end_area, throughput, qing = ohlp.get_qlen_and_throughput_single_origin(
                byte_data, q_data, idx, params, iface, num_aggr, num_tor, num_host_per_tor)
            if throughput is None:
                continue
            this_out_dir = f"{out_dir}/{origin_area}"
            qing[:, 1] = qing[:, 1] / 1000.0
            data = throughput
            data = np.append(data, qing[:, 1].reshape(qing.shape[0], 1), axis=1)

            # this only writes aggr and tor data (no host)
            write_qts_data(this_out_dir, data, origin_area, origin, end_area, end)
    
    def process_load_lvl_dcpim(data_dir, out_dir, prot, param_file):
        print(f"Qts dcpim Processing {data_dir}")
        params = hlp.import_param_file(param_file)
        q_file = f"{data_dir}/{cfg.DCPIM_Q_FILE}"
        data = dchlp.get_queue_data(q_file)

        _, sim_start, sim_end = dchlp.get_app_data(f"{data_dir}/{cfg.DCPIM_APP_FILE}")
        trace_start, trace_end = dchlp.get_trace_interval(params, sim_start, sim_end)
        data = hlp.trim_by_timestamp(data, trace_start, trace_end, dchlp.qCols.TS.value)
        print(f"DELETEME: trace_start {trace_start} trace_end {trace_end}")

        # Group data by link
        orig_to_data = {} # origin -> link -> timeseries (ts,qlen,departures)
        orig_to_data = dchlp.group_by_origin(data)

        # Plot qing timeseries
        for origin in orig_to_data:
            origin_area = origin.split("_")[0]
            for link in orig_to_data[origin]:
                out_dir_q = f"{out_dir}/{origin_area}/plots/qing"
                hlp.make_dir(out_dir_q)
                name = f"{origin}_{link}"
                hlp.plot_time_series(orig_to_data[origin][link][:, (0, 1)], out_dir_q, f"{name}", prot, "Queuing (KB)", x_axis_title="Time (s)")



    out_dir = f"{directory}/{cfg.OUT_DIR_NAME}/qts"
    hlp.make_dir(out_dir)
    param_file = f"{directory}/parameters"
    if simulator == cfg.OMNET_SIMULATOR:
        data_dir = f"{directory}/extracted_results"
        process_load_lvl_omnet(data_dir, out_dir, prot, load, param_file)
    elif simulator == cfg.NS2_SIMULATOR:
        process_load_lvl(directory, out_dir, prot, load, param_file)
    elif simulator == cfg.DCPIM_SIMULATOR:
        process_load_lvl_dcpim(directory, out_dir, prot, param_file)
    else:
        raise ValueError(f"Unknown simulator {simulator}")


###############################################################################################################
###############################################################################################################
###############################################################################################################
#################################### Transport Layer data #####################################################
###############################################################################################################
###############################################################################################################
###############################################################################################################


def aggr_cc_data_ts(directory, prot, load, is_omnet=False, create_plots=False):
    """
    extract the timeseries of every column of cc_trace.str
    So for every protocol, load combination, there are num_col timeseries.
    Only keep "pol" events
    """

    def process_load_lvl(ldir, out_dir, prot, load, param_file):
        print(f"CC Processing {ldir}")
        data_dir = f"{ldir}/cc_trace.str"
        params = hlp.import_param_file(param_file)
        cc_scheme = "micro-hybrid"

        # start_time = {}
        # proc_time = {}
        # start_time["proc"] = time.process_time()
        # Each row corresponds to a specific event type and a specific host. Filter and separate.
        proc_fun = cc_hlp.get_proc_fun(cc_scheme)
        params_to_proc = cc_hlp.get_proc_params(cc_scheme)
        if proc_fun is None:
            # There is no function to process cc data for $cc_scheme
            return
        data = cc_hlp.load_cc_data(ldir, "micro-hybrid", 1.0, param_file)
        results = proc_fun(data, params, prot, load, params_to_proc)
        print("Results processed. Writing out")
        # proc_time["proc"] = time.process_time() - start_time["proc"]
        # start_time["out"] = time.process_time()

        cc_hlp.output_results(results, out_dir, prot, load, create_plots)
        # proc_time["out"] = time.process_time() - start_time["out"]

        # for key in proc_time:
        #     print(f"Processing stage {key} took {proc_time[key]} seconds")

    out_dir = f"{directory}/{cfg.OUT_DIR_NAME}/cc"
    hlp.make_dir(out_dir)
    param_file = f"{directory}/parameters"
    if is_omnet:
        raise Exception("aggr_cc_data_ts() not supported for omnet simulations")
    else:
        process_load_lvl(directory, out_dir, prot, load, param_file)
