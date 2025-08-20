#include "pfabric-app.h"
#include "simple-log.h"
#include "xpass.h"
#include <iostream>
#include <math.h>
#include <iomanip>
#include <sstream>

struct MsgState
{
    int total_size_B_;
    int bytes_recvd_;
};

static class PfabricAppClass : public TclClass
{
public:
    PfabricAppClass() : TclClass("Generic_app/PFABRIC") {}
    TclObject *create(int, const char *const *)
    {
        return (new PfabricApplication<FullTcpAgent>);
    }
} class_pfabric_app;

static class PfabricAppXpassClass : public TclClass
{
public:
    PfabricAppXpassClass() : TclClass("Generic_app/PFABRICXPASS") {}
    TclObject *create(int, const char *const *)
    {
        return (new PfabricApplication<XPassAgent>);
    }
} class_pfabricxpass_app;

template <typename T>
PfabricApplication<T>::PfabricApplication() : GenericApp(this), warmup_timer_(this),
                                              warmup_pool_counter_(0), queued_requests_(0)
{
    bind("warmup_phase_", &warmup_phase_);
}

template <typename T>
PfabricApplication<T>::~PfabricApplication() {}

template <typename T>
void PfabricApplication<T>::start_app()
{
    slog::log2(debug_, local_addr_, "================== PfabricApplication::start_app() ==================");
    slog::log2(debug_, local_addr_, "msg_tracing:", MsgTracer::do_trace_,
               enable_incast_, incast_interval_sec_, num_clients_,
               num_servers_, incast_size_, incast_request_size_);
    if (request_interval_sec_ > 0.0)
    {
        double first = send_interval_->get_next();
        send_req_timer_.resched(first);
    }

    assert(dst_ids_->size() == num_servers_ - 1);

    bool manual_mode = false;
    if (request_interval_sec_ > 0.0 && dynamic_cast<ManualDistr *>(send_interval_)) // not perfect check
        manual_mode = true;

    if (manual_mode)
    {
        if (enable_incast_ == 1)
        {
            throw std::invalid_argument("Incast not available with manual mode");
        }
    }

    if (enable_incast_)
    {
        IncastGenerator::init(num_clients_, num_servers_, incast_request_size_, incast_size_); // must get total number of clients and incast size.
        send_incast_timer_.resched(incast_interval_sec_);
    }
}

template <typename T>
void PfabricApplication<T>::stop_app()
{
    slog::log2(debug_, local_addr_, "PfabricApplication::stop_app()");
    if (send_req_timer_.status() == TIMER_PENDING)
        send_req_timer_.cancel();
    if (send_incast_timer_.status() == TIMER_PENDING)
        send_incast_timer_.cancel();
}

template <typename T>
void PfabricApplication<T>::attach_agent(int argc, const char *const *argv)
{
    T *agent = (T *)TclObject::lookup(argv[2]);
    if (agent == 0)
    {
        throw std::invalid_argument("No such agent");
    }
    // destination thread id
    // int thread_id = atoi(argv[3]);
    slog::log4(debug_, local_addr_, "PfabricApplication::attach_agent() attach agent with daddr",
               agent->daddr());
    if (dstid_to_free_agent_pool_.count(agent->daddr()) == 0)
    {
        slog::log3(debug_, local_addr_, "PfabricApplication::attach_agent() creating pool for daddr:", agent->daddr());
        dstid_to_free_agent_pool_[agent->daddr()] = new free_connections_pool_t();
    }
    try
    {
        /** Dale: Intermittent Connections FCT Experiment: restrict pool size to 1 */
        if (dstid_to_free_agent_pool_.at(agent->daddr())->size() < MAX_POOL_SIZE)
        {
            slog::log4(debug_, local_addr_, "Adding new agent to pool for daddr=", agent->daddr(), ", dport=", agent->dport());
            dstid_to_free_agent_pool_.at(agent->daddr())->push_back(agent);
        }
    }
    catch (const std::out_of_range &e)
    {
        slog::error(debug_, local_addr_, "Did not find agent with address", agent->daddr(), "in dstid_to_free_agent_pool_");
        throw;
    }

    bool is_unique = true;
    for (int32_t item : *dst_ids_)
    {
        if (item == agent->daddr())
        {
            is_unique = false;
            break;
        }
    }
    if (is_unique)
        dst_ids_->push_back(agent->daddr());
    agent->attachApp(this);
    local_addr_ = agent->addr();
}

template <typename T>
void PfabricApplication<T>::send_request(RequestIdTuple *arg_req, size_t arg_size)
{
    bool is_incast = false;
    int next_req_size = 0;
    if (arg_req)
    {
        is_incast = true;
        next_req_size = static_cast<int>(arg_size);
    }
    else
    {
        next_req_size = static_cast<int>(req_size_->get_next());
    }

    // 2 because if 1 tcp seems unwilling to forward to the app..
    if (next_req_size < 4)
        next_req_size = 4;

    /* Dale: store flow-id information in req_id */
    long flow_id = (long) req_flow_id_->get_next();
    /* Dale: get flag stating if this is the final byteload of the flow */
    bool is_final_byteload = (bool) req_is_final_byteload_->get_next();

    RequestIdTuple req_id;
    int32_t srvr_addr;
    if (is_incast)
    {
        req_id = *arg_req;
        srvr_addr = req_id.sr_addr_;
    }
    else
    {
        srvr_addr = dst_thread_gen_->get_next();
        req_id = RequestIdTuple();
        /* Dale: set app_level_id_ to flow_id instead of num of reqs_sent_ */
        req_id.app_level_id_ = flow_id;
        req_id.msg_bytes_ = next_req_size;
        /* Dale: init total msg data size field */
        req_id.total_msg_data_ = next_req_size;
        req_id.is_request_ = true;
        req_id.cl_thread_id_ = thread_id_;
        req_id.sr_thread_id_ = SERVER_THREAD_BASE;
        req_id.ts_ = Scheduler::instance().clock();
    }
    req_id.flow_id_ = flow_id; /* Dale: we don't use this field in DCTCP this anymore, cuz app_level_id is now flow_id */
    /* Dale: store is_final_byteload flag in req_id */
    req_id.is_final_req_of_conn_ = is_final_byteload;

    // take the first available connection for the randomly selected target and send the request

    // update load factor
    if (!is_incast)
    {
        send_interval_->set_mean(request_interval_sec_ * (1 / load_pattern_->get_load_multiplier()));
        send_req_timer_.resched(send_interval_->get_next());
    }

    free_connections_pool_t *pool = nullptr;
    try
    {
        pool = dstid_to_free_agent_pool_.at(srvr_addr);
        /** Dale: restrict conn pool size to 1 */
        assert(pool->size() <= MAX_POOL_SIZE);
    }
    catch (const std::out_of_range &e)
    {
        slog::error(debug_, local_addr_, "Did not find pool for server address:", srvr_addr);
        throw;
    }

    if (do_trace_)
        trace_state("srq", srvr_addr, -1, req_id.app_level_id_, -1, next_req_size, -1, pool->size());
    reqs_sent_++;

    /* Dale: retrieve queued requests for the current flow */
    flow_id_to_queued_requests_t *flow_id_to_req_queue = nullptr;
    queued_requests_t *flow_req_queue = nullptr;
    if (dstid_to_flow_queued_requests_.find(srvr_addr) != dstid_to_flow_queued_requests_.end())
    {
        flow_id_to_req_queue = dstid_to_flow_queued_requests_.at(srvr_addr);
        // check if there is already a queue for this flow_id
        auto it = flow_id_to_req_queue->find(req_id.app_level_id_);
        if (it != flow_id_to_req_queue->end())
        {
            flow_req_queue = it->second;
        }
        else
        {
            flow_req_queue = new queued_requests_t();
            (*flow_id_to_req_queue)[req_id.app_level_id_] = flow_req_queue;
        }
    }
    else
    {
        flow_id_to_req_queue = new flow_id_to_queued_requests_t();
        dstid_to_flow_queued_requests_[srvr_addr] = flow_id_to_req_queue;
        flow_req_queue = new queued_requests_t();
        (*flow_id_to_req_queue)[req_id.app_level_id_] = flow_req_queue;
    }

    // if (dstid_to_queued_requests_.find(srvr_addr) != dstid_to_queued_requests_.end())
    // {

    //     req_queue = dstid_to_queued_requests_.at(srvr_addr);
    // }
    // else
    // {
    //     req_queue = new queued_requests_t();
    //     dstid_to_queued_requests_[srvr_addr] = req_queue;
    // }

    /* Dale: check if there is already a conn assigned to this flow_id */
    T *agent = nullptr;
    auto it = flow_id_to_agent_map_.find(req_id.app_level_id_);
    if (it != flow_id_to_agent_map_.end())
    {
        agent = it->second;
        slog::log1(debug_, local_addr_, "PfabricApplication::send_request() for flow_id:", req_id.app_level_id_, "using EXISTING agent (daddr=", agent->daddr(), "dport=", agent->dport(), ") pool size:", pool->size());
    }
    else
    {
        if (pool->empty())
        {
            // see if for this connection pool, there is a queue of queued messages
            /* Dale: push req_id into request queue corresponding to this flow_id */
            flow_req_queue->push_back(req_id);
            bool is_flow_already_waiting = std::find(waiting_flows_.begin(), waiting_flows_.end(), req_id.app_level_id_) != waiting_flows_.end();
            if (!is_flow_already_waiting)
            {
                waiting_flows_.push_back(req_id.app_level_id_);
            }
            queued_requests_++;
            slog::log1(debug_, local_addr_, "PfabricApplication::send_request(): Pool empty. Flow_id:", req_id.app_level_id_, "new flow_req_queue size:", flow_req_queue->size(), "is flow already waiting:", is_flow_already_waiting, "new waiting_flows_ size:", waiting_flows_.size());
            return;
        }

        /* Dale: get new agent from pool and assign it to this flow_id */
        agent = pool->front();
        pool->pop_front();
        flow_id_to_agent_map_[req_id.app_level_id_] = agent;

        slog::log1(debug_, local_addr_, "PfabricApplication::send_request() for flow_id:", req_id.app_level_id_, "using NEW agent (daddr=", agent->daddr(), ", dport=", agent->dport(), ") pool size:", pool->size());

        /* Dale: Since each flow hogs a connection until it finishes sending, a flow that gets a new conn the moment it tries to send should never have any existing queued requests */
        assert(flow_req_queue->empty());
        // if (!flow_req_queue->empty())
        // {
        //     slog::log6(debug_, local_addr_, "WARN: PfabricApplication::send_request(): there are ", flow_req_queue->size(), "queued requests for flow_id:", req_id.app_level_id_);
        //     flow_req_queue->push_back(req_id);
        //     req_id = flow_req_queue->front();
        //     flow_req_queue->pop_front();
        // }
    }

    // slog::log4(debug_, local_addr_, "PfabricApplication::send_request(). Pool size:", pool->size(), "| is incast:", is_incast);

    forward_request(req_id, agent, srvr_addr);
}

template <typename T>
void PfabricApplication<T>::send_incast()
{
    slog::log4(debug_, local_addr_, "PfabricApplication::send_incast()");
    IncastGenerator::BurstInfo binfo = IncastGenerator::should_send(local_addr_);

    if (binfo.should_send_)
    {
        if (do_trace_)
        {
            trace_state("sin", binfo.incast_target_, -1, reqs_sent_, -1, binfo.req_size_, -1, 0);
        }
        RequestIdTuple req = RequestIdTuple(reqs_sent_, local_addr_,
                                            binfo.incast_target_,
                                            thread_id_,
                                            SERVER_THREAD_BASE,
                                            Scheduler::instance().clock());
        req.msg_bytes_ = binfo.req_size_;
        req.is_request_ = true;
        slog::log5(debug_, local_addr_, "PfabricApplication::send_incast(). Req size:", req.msg_bytes_);
        send_request(&req, binfo.req_size_);
    }

    send_incast_timer_.resched(incast_interval_sec_);
}

/* Dale: forward request to specific agent assigned to this flow, instead of to the general pool */
template <typename T>
void PfabricApplication<T>::forward_request(RequestIdTuple &req_id, T *agent, int32_t srvr_addr)
{
    // // remove agent from free pool
    // T *agent = pool->back();
    // pool->pop_back();

    // also pass this client's address
    req_id.cl_addr_ = local_addr_;

    /* Dale: update info in sender-side flow request state, and in req_id of pkt to be sent out */
    auto it = flow_id_to_req_state_map_.find(req_id.app_level_id_);
    if (it != flow_id_to_req_state_map_.end())
    {
        RequestIdTuple &flow_request_state = it->second;

        flow_request_state.total_msg_data_ += req_id.msg_bytes_;
        req_id.total_msg_data_ = flow_request_state.total_msg_data_;

        double msg_creation_time = min(flow_request_state.ts_, req_id.ts_);
        flow_request_state.ts_ = msg_creation_time;
        req_id.ts_ = msg_creation_time;
        
        slog::log2(debug_, local_addr_, "* PfabricApplication::forward_request(): updating request state for flow_id:", req_id.app_level_id_, "total_msg_data_:", req_id.total_msg_data_, "ts:", req_id.ts_);
    }
    else
    {
        flow_id_to_req_state_map_[req_id.app_level_id_] = req_id;
    }

    // add agent to busy agents
    req_id_to_busy_agent_[req_id.app_level_id_] = std::make_tuple(srvr_addr, 0, agent);

    /* Dale: elevate from log5 to log2 */
    slog::log2(debug_, local_addr_, "PfabricApplication::forward_request() of size", req_id.msg_bytes_, req_id.is_request_, "total_msg_data_:", req_id.total_msg_data_, "flow_id_:", req_id.app_level_id_, "is_final_req_of_conn_:", req_id.is_final_req_of_conn_);
    // send msg
    assert(agent != nullptr);
    assert(req_id.is_request_);
    /* Dale: do partial reset (nop==0) for xpass: resets state and timers, not counters */
    agent->reset(0); 
    agent->advance_bytes(req_id.msg_bytes_, std::move(req_id));
}

/**
 * Receives TCP data whenever TCP decides to send them. It keeps track of when all the bytes of
 * a message are received.
 */
template <typename T>
void PfabricApplication<T>::recv_msg(int payload, RequestIdTuple &&req_id_tup)
{
    slog::log2(debug_, local_addr_, "PfabricApplication::recv_msg() received bytes:", payload, "total_msg_data_", req_id_tup.total_msg_data_ ,"app_level_id_:", req_id_tup.app_level_id_, "ts_:", req_id_tup.ts_, "is_final_req_of_conn_:", req_id_tup.is_final_req_of_conn_);
    if (warmup_phase_ == 1)
        return;
    else
        assert(req_id_tup.ts_ > 0);
    long app_lvl_req_id = req_id_tup.app_level_id_;
    int total_msg_sz = req_id_tup.msg_bytes_;
    slog::log6(debug_, local_addr_, "&& src_:", req_id_tup.cl_addr_, req_id_tup.cl_thread_id_, "flow_id_:", req_id_tup.flow_id_);
    // is this msg (part of) a request?
    if (req_id_tup.is_request_)
    {
        // Register the state of an incoming request to know when it has been fully received.
        cl_addr_thread_t cl_tup = std::make_tuple(req_id_tup.cl_addr_, req_id_tup.cl_thread_id_);
        auto search_res = cl_tup_to_pending_requests_.find(cl_tup);
        req_id_to_req_state_t *req_id_to_req_state;
        // has the (remote) client thread sent before?
        if (search_res != cl_tup_to_pending_requests_.end())
        {
            req_id_to_req_state = search_res->second;
        }
        else
        {
            req_id_to_req_state = new req_id_to_req_state_t();
            cl_tup_to_pending_requests_[cl_tup] = req_id_to_req_state;
        }
        // is this the first packet of this request?
        MsgState *req_state;
        if (req_id_to_req_state->find(app_lvl_req_id) == req_id_to_req_state->end())
        {
            slog::log5(debug_, local_addr_, "Register incoming request with sz:", total_msg_sz);
            req_state = new MsgState();
            req_state->total_size_B_ = max(total_msg_sz, req_id_tup.total_msg_data_);
            req_state->bytes_recvd_ = payload;
            (*req_id_to_req_state)[app_lvl_req_id] = req_state;
        }
        else
        {
            req_state = req_id_to_req_state->at(app_lvl_req_id);
            /* Dale: update expected total size of msg */
            req_state->total_size_B_ = max(req_id_tup.total_msg_data_, req_state->total_size_B_);
            req_state->bytes_recvd_ += payload;
        }
        // Has the whole request been received
        slog::log5(debug_, local_addr_, "req_state->bytes_recvd_:", req_state->bytes_recvd_, "req_state->total_size_B_", req_state->total_size_B_, "is_xpass_app_msg_", req_id_tup.is_xpass_app_msg_);
        /* Dale: try: hack for xpass */
        if (req_state->bytes_recvd_ == req_state->total_size_B_
            || (req_id_tup.is_xpass_app_msg_ && (req_id_tup.is_final_req_of_conn_ || req_state->bytes_recvd_ >= req_state->total_size_B_))
        )
        {
            /* Dale: only do rrq and after we've receieved the final byteload of the flow */
            if (req_id_tup.is_final_req_of_conn_)
            {
                double msg_created_at = req_id_tup.ts_;
                /* Dale: elevate from lo4 to log2 */
                slog::log1(debug_, local_addr_, "PfabricApplication - whole request received for flow ", app_lvl_req_id, ". size", req_state->bytes_recvd_,
                        "From:", req_id_tup.cl_addr_, "that was created on:", msg_created_at);
                assert(msg_created_at > 9.9); // assumes sim starts at 10.0
                if (do_trace_)
                {
                    slog::log6(debug_, local_addr_, "rrq");
                    /* Dale: change rrq to trace flow-id instead of app-level-id */
                    trace_state("rrq", req_id_tup.cl_addr_, -1, req_id_tup.app_level_id_, Scheduler::instance().clock() - msg_created_at, req_state->total_size_B_, -1, -1);
                }
                // no replies
                if (pending_tasks_.empty())
                {
                    send_resp_timer_.sched(proc_time_->get_next());
                }
                pending_tasks_.push(req_id_tup);
                delete req_state;
                try
                {
                    cl_tup_to_pending_requests_.at(cl_tup)->erase(app_lvl_req_id);
                }
                catch (const std::out_of_range &e)
                {
                    slog::error(debug_, local_addr_, "Failed to erase req_state.");
                    throw;
                }
            }
            else
            {
                slog::log1(debug_, local_addr_, "++ PfabricApplication - received all outstanding bytes for flow_id ", app_lvl_req_id, ", but is not final request of connection. bytes_recvd_:", req_state->bytes_recvd_, "total_size_B_:", req_state->total_size_B_);
            }
        }
        else if (req_state->bytes_recvd_ > req_state->total_size_B_)
        {
            slog::error(debug_, local_addr_, "Error, Pfab-app: Received more request bytes than expected.");
            slog::error(debug_, "expected:", req_state->total_size_B_, "received:", req_state->bytes_recvd_);
            exit(EXIT_FAILURE);
        }
    }
    else
    {
        // is this the first packet of this reply?
        MsgState *reply_state;
        if (req_id_to_reply_state_.find(app_lvl_req_id) == req_id_to_reply_state_.end())
        {
            reply_state = new MsgState();
            reply_state->total_size_B_ = total_msg_sz;
            reply_state->bytes_recvd_ = payload;
            req_id_to_reply_state_[app_lvl_req_id] = reply_state;
        }
        else
        {
            reply_state = req_id_to_reply_state_.at(app_lvl_req_id);
            /* Dale: update expected total size of msg */
            reply_state->total_size_B_ = max(total_msg_sz, reply_state->total_size_B_);
            reply_state->bytes_recvd_ += payload;
        }
        // has the whole reply been received?
        if (reply_state->bytes_recvd_ == reply_state->total_size_B_)
        {
            // double req_dur = Scheduler::instance().clock() - app_req_id_to_req_info_.at(app_lvl_req_id)->time_sent_;
            // int req_sz = app_req_id_to_req_info_.at(app_lvl_req_id)->request_size_;
            // free the connection
            std::tuple<int32_t, int, T *> srvr_info;
            try
            {
                srvr_info = req_id_to_busy_agent_.at(app_lvl_req_id);
            }
            catch (const std::out_of_range &e)
            {
                slog::error(debug_, local_addr_, "Failed to find busy agent.");
                throw;
            }

            int32_t srvr_addr = std::get<0>(srvr_info);
            int srvr_thrd = std::get<1>(srvr_info);
            T *agent = std::get<2>(srvr_info);

            slog::log1(debug_, local_addr_, "PfabricApplication - whole reply received from srvr_addr", srvr_addr, ". Pool size:", dstid_to_free_agent_pool_.at(srvr_addr)->size(), "| flow_id:", app_lvl_req_id, "waiting_flows_ size:", waiting_flows_.size());

            req_id_to_busy_agent_.erase(app_lvl_req_id);
            delete reply_state;
            req_id_to_reply_state_.erase(app_lvl_req_id);

            int pool_size;
            try
            {
                /* Dale: flow has finished sending, un-assign agent from flow */
                slog::log3(debug_, local_addr_, "$$ pt1");
                assert(std::find(waiting_flows_.begin(), waiting_flows_.end(), app_lvl_req_id) == waiting_flows_.end());
                flow_id_to_agent_map_.erase(app_lvl_req_id);
                /* Dale: fully reset agent when we release agent/conn back to pool (for xpass) */
                agent->reset(-1);
                dstid_to_free_agent_pool_.at(srvr_addr)->push_back(agent);
                pool_size = dstid_to_free_agent_pool_.at(srvr_addr)->size();
                /** Dale: restrict conn pool size to 1 */
                assert(pool_size <= MAX_POOL_SIZE);

                slog::log3(debug_, local_addr_, "$$ pt2");
                // check for queued requests waiting for connections in this pool
                /* Dale: check if there are other waiting flows with queued requests */
                flow_id_to_queued_requests_t *flow_id_to_req_queue = nullptr;
                queued_requests_t *flow_req_queue = nullptr;
                /* Dale: choose next flow to service (FCFS) */
                if (waiting_flows_.empty())
                {
                    return;
                }
                slog::log3(debug_, local_addr_, "$$ pt3");
                long next_flow_id = waiting_flows_.front(); 
                waiting_flows_.pop_front();
                if (dstid_to_flow_queued_requests_.find(srvr_addr) != dstid_to_flow_queued_requests_.end())
                {
                    flow_id_to_req_queue = dstid_to_flow_queued_requests_.at(srvr_addr);
                    if (flow_id_to_req_queue->find(next_flow_id) != flow_id_to_req_queue->end())
                    {
                        flow_req_queue = flow_id_to_req_queue->at(next_flow_id);
                    }
                }
                slog::log3(debug_, local_addr_, "$$ pt4");
                if (flow_req_queue && !flow_req_queue->empty())
                {
                    /* Dale: Retrieve an agent from the pool to forward_requests through */
                    free_connections_pool_t *pool = dstid_to_free_agent_pool_.at(srvr_addr);
                    T* agent = pool->front();
                    pool->pop_front();
                    flow_id_to_agent_map_[next_flow_id] = agent; // update the agent for this flow_id
                    slog::log3(debug_, local_addr_, "$$ pt5");

                    // there are queued requests and a connection has just been freed. Use it
                    slog::log3(debug_, local_addr_, "PfabricApplication::recv_msg() servicing queued requests for flow_id:", next_flow_id, "using agent (daddr=", agent->daddr(), ", dport=", agent->dport(), "), flow_req_queue size:", flow_req_queue->size(), "waiting_flows_ size:", waiting_flows_.size());
                    slog::log2(debug_, local_addr_, "$$ pt6");
                    while (!flow_req_queue->empty())
                    {
                        slog::log3(debug_, local_addr_, "$$ pt7");
                        /* Dale: process all queued requests for this flow_id */
                        RequestIdTuple req_id = flow_req_queue->front();
                        flow_req_queue->pop_front();
                        queued_requests_--;
                        forward_request(req_id, agent, srvr_addr);
                        if (req_id.is_final_req_of_conn_)
                        {
                            assert(flow_req_queue->empty());
                        }
                        slog::log3(debug_, local_addr_, "$$ pt8");
                    } 
                }
                
            }
            catch (const std::out_of_range &e)
            {
                slog::error(debug_, local_addr_, "Did not find pool for server addr:", srvr_addr, "while inserting agent");
                throw;
            }

        }
        else if (reply_state->bytes_recvd_ > reply_state->total_size_B_)
        {
            slog::error(debug_, local_addr_, "Error, Pfab-app: Received more reply bytes than expected.");
            slog::error(debug_, "expected:", reply_state->total_size_B_, "received:", reply_state->bytes_recvd_);
            exit(EXIT_FAILURE);
        }
    }
}

template <typename T>
void PfabricApplication<T>::send_response()
{
    slog::log4(debug_, local_addr_, "PfabricApplication::send_response()");
    // find the agent that was used to send the request in the first place
    RequestIdTuple req_id = pending_tasks_.front();
    pending_tasks_.pop();
    // schedule next response if one is pending
    if (!pending_tasks_.empty())
    {
        send_resp_timer_.resched(proc_time_->get_next());
    }
    free_connections_pool_t *pool = dstid_to_free_agent_pool_.at(req_id.cl_addr_);
    /** Dale: restrict conn pool size to 1 */
    assert(pool->size() <= MAX_POOL_SIZE);

    // now to find the connection that the client used...
    // the addr and port must match the client's daddr and dport
    T *agent;

    for (auto it = pool->begin(); it != pool->end(); it++)
    {
        if (req_id.cl_addr_ == (*it)->daddr() && req_id.client_port_ == (*it)->dport())
        {
            agent = (*it);
            slog::log6(debug_, local_addr_, "Found agent for client addr:", req_id.cl_addr_, "port:", req_id.client_port_);
            break;
        }
    }
    if (!agent)
    {
        slog::error(debug_, "Could not find the agent that is connected to the agent the client used");
        exit(EXIT_FAILURE);
    }
    slog::log6(debug_, local_addr_, "@ Agent: daddr():", agent->daddr(), "dport:", agent->dport());
    // Will not remove from free pool at the server side for now...
    // int next_resp_size = (int)(resp_size_->get_next());
    int next_resp_size = 4;
    if (next_resp_size < 2)
        next_resp_size = 2;
    req_id.is_request_ = false;
    req_id.msg_bytes_ = next_resp_size;
    // req_id.msg_bytes_ = next_resp_size;
    req_id.sr_addr_ = local_addr_;
    // if (do_trace_)
    //     trace_state("srs", req_id.cl_addr_, -1, req_id.app_level_id_, -1, -1, -1, -1);
    agent->reset(-1);
    agent->advance_bytes(next_resp_size, std::move(req_id));
}

/**
 * Warmup TCP connections - mostly to establish the connection (handshake)
 */
template <typename T>
void PfabricApplication<T>::warmup()
{
    slog::log3(debug_, local_addr_, "PfabricApplication::warmup()");
    slog::log3(debug_, local_addr_, "Warmup pool:", warmup_pool_counter_);
    int pool_cnt = 0;
    for (auto pool_it = dstid_to_free_agent_pool_.begin(); pool_it != dstid_to_free_agent_pool_.end(); pool_it++)
    {
        if (pool_cnt == warmup_pool_counter_)
        {
            // std::cout << "pool_cnt: " << pool_cnt << "warmup_pool_cnt: " << warmup_pool_counter_ << std::endl;
            free_connections_pool_t *pool = pool_it->second;
            for (auto it = pool->begin(); it != pool->end(); it++)
            {
                (*it)->advance_bytes(2);
            }
            warmup_timer_.resched(100.0 / 1000.0 / 1000.0);
            break;
        }
        else
        {
            pool_cnt++;
        }
    }
    warmup_pool_counter_++;
}

template <typename T>
int PfabricApplication<T>::command(int argc, const char *const *argv)
{
    slog::log5(debug_, local_addr_, "PfabricApplication::command()");
    if (argc == 2)
    {
        if (strcmp(argv[1], "warmup") == 0)
        {
            slog::log5(debug_, local_addr_, "Establishing connections..");
            warmup();
            return (TCL_OK);
        }
        else if (strcmp(argv[1], "stop-warmup") == 0)
        {
            warmup_phase_ = 0;
            return (TCL_OK);
        }
    }
    return (GenericApp::command(argc, argv));
}

template <typename T>
void PfabricApplication<T>::trace_state(std::string &&event,
                                        int32_t remote_addr,
                                        int req_id,
                                        long app_level_id,
                                        double req_dur,
                                        int req_size,
                                        int resp_size,
                                        int pool_size)
{
    std::vector<std::string> vars;
    vars.push_back(event);
    vars.push_back(std::to_string(local_addr_));
    vars.push_back(std::to_string(remote_addr));
    vars.push_back(std::to_string(thread_id_));
    vars.push_back(std::to_string(req_id));
    vars.push_back(std::to_string(app_level_id));
    std::stringstream stream;
    stream << std::fixed << std::setprecision(9) << req_dur;
    vars.push_back(stream.str());
    vars.push_back(std::to_string(req_size));
    vars.push_back(std::to_string(resp_size));
    vars.push_back(std::to_string(queued_requests_));
    vars.push_back(std::to_string(pool_size));
    tracer_->trace(vars);
}

template <typename T>
void WarmupGapTimer<T>::expire(Event *)
{
    pfab_app_->warmup();
}