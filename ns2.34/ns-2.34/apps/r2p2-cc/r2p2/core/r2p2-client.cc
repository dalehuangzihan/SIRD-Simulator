#include <iostream>
#include "r2p2-client.h"
#include "r2p2-hdr.h"
#include "simple-log.h"

struct ClientRequestState
{
    ClientRequestState() : req_bytes_left_(0), reply_pkts_to_rec_(0),
                           reply_pkts_recvd_(0), reply_bytes_recvd_(0),
                           msg_creation_time_(-1.0), is_update_msg_timestamp(false) {}
    int req_bytes_left_;
    int reply_pkts_to_rec_;
    int reply_pkts_recvd_;
    int reply_bytes_recvd_;
    double msg_creation_time_;
    /* Dale: track whether reply for this request has been received */
    bool is_update_msg_timestamp;
};

R2p2Client::R2p2Client(R2p2 *r2p2_layer) : r2p2_layer_(r2p2_layer) {}

R2p2Client::~R2p2Client()
{
    delete r2p2_layer_;
    for (auto it_map = thrd_id_to_pending_reqs_map_.begin();
         it_map != thrd_id_to_pending_reqs_map_.end(); it_map++)
    {
        for (auto it = it_map->second->begin();
             it != it_map->second->end(); it++)
        {
            delete it->second;
        }
        delete it_map->second;
    }
}

void R2p2Client::send_req(int payload, const RequestIdTuple &request_id_tuple)
{
    if (payload < 1)
    {
        throw std::invalid_argument("nbytes must be > 0");
    }
    // TODO: define constants somewhere
    int bytes_in_req0 = REQ0_MSG_SIZE;
    int num_pkts = payload / MAX_R2P2_PAYLOAD;
    if (payload % MAX_R2P2_PAYLOAD > 0)
        num_pkts++;
    bool single_pkt_rpc = num_pkts == 1;
    // TODO: This should not be happening -req0 should be just control
    int reqn_payload = payload - bytes_in_req0;

    if (!single_pkt_rpc)
    {
        num_pkts = reqn_payload / MAX_R2P2_PAYLOAD;
        if (reqn_payload % MAX_R2P2_PAYLOAD > 0)
            num_pkts++;
    }
    else
    {
        num_pkts = 0;
    }
    /** Dale:
     * Use app_level_id as client request id (rewrote whole control block below).
     * Allows 1 thread to service multiple app-level requests. 
     */
    request_id current_rid = request_id_tuple.app_level_id_;
    // check if this thread has sent before
    int thread_id = request_id_tuple.cl_thread_id_;
    auto srch_thread = thrd_id_to_req_id_.find(thread_id);
    if (srch_thread != thrd_id_to_req_id_.end())
    {
        // thread has sent before
        // check if thread has sent on this rid before
        rid_set_t *rid_set = srch_thread->second;
        auto srch_rid = rid_set->find(current_rid);
        if (srch_rid != rid_set->end())
        {
            // thread has sent on this rid before 
            (*thrd_id_app_lvl_id_to_req_count_.at(thread_id))[current_rid] += 1;
        }
        else
        {
            rid_set->insert(current_rid);
            (*thrd_id_app_lvl_id_to_req_count_.at(thread_id))[current_rid] = 0;
        }
    }
    else
    {
        thrd_id_to_req_id_[thread_id] = new rid_set_t(); 
        (*thrd_id_to_req_id_.at(thread_id)).insert(current_rid);
        thrd_id_app_lvl_id_to_req_count_[thread_id] = new req_id_to_req_count_t();
        (*thrd_id_app_lvl_id_to_req_count_.at(thread_id))[current_rid] = 0;
        thrd_id_to_pending_reqs_map_[thread_id] = new req_id_to_req_state_t();
    }
    /* Dale: calc if msg extension based on whether current thread has sent mutiple req from this app lvl id */
    bool is_msg_extension = (*thrd_id_app_lvl_id_to_req_count_.at(thread_id))[current_rid] > 0;

    /** Dale: TODO:
     * Maintain the same client request state until connection teardown.
     * TODO: clear client request state during connection teardown.
     */

    /** Dale:
     * 20/06/2025 Each new app_level_id gets and uses its own client request state.
     */
    ClientRequestState *client_request_state = (*thrd_id_to_pending_reqs_map_.at(thread_id))[current_rid];
    bool is_new_client_request_state = false;
    if (client_request_state == nullptr)
    {
        slog::log6(r2p2_layer_->get_debug(), r2p2_layer_->get_local_addr(), "creating new client request state for thread=", thread_id, "rid=", current_rid);
        client_request_state = new ClientRequestState();
        is_new_client_request_state = true;
    }
    hdr_r2p2 r2p2_hdr;
    r2p2_hdr.first() = true;
    r2p2_hdr.last() = single_pkt_rpc;
    r2p2_hdr.msg_type() = hdr_r2p2::REQUEST;
    r2p2_hdr.policy() = hdr_r2p2::UNRESTRICTED;
    r2p2_hdr.req_id() = current_rid;
    r2p2_hdr.pkt_id() = num_pkts;
    // will be interpreted as: send to r2p2-router
    r2p2_hdr.cl_addr() = request_id_tuple.cl_addr_;
    r2p2_hdr.cl_thread_id() = thread_id;
    r2p2_hdr.app_level_id() = request_id_tuple.app_level_id_;
    r2p2_hdr.sr_addr() = request_id_tuple.sr_addr_;
    r2p2_hdr.sr_thread_id() = request_id_tuple.sr_thread_id_;
    // r2p2_hdr.msg_size_bytes() = reqn_payload;
    /** Dale: override msg creation time only if is new client request state, or if reply
     * for existing client req state has been received immediately prior */
    if (is_new_client_request_state || client_request_state->is_update_msg_timestamp)
    {
        r2p2_hdr.msg_creation_time() = request_id_tuple.ts_;
    }
    else
    {
        r2p2_hdr.msg_creation_time() = client_request_state->msg_creation_time_;
    }
    /* Dale: carry is_msg_extension_ within hdr */
    r2p2_hdr.is_msg_extension() = is_msg_extension;
    /* Dale: init is_ignore_persistence to default value (only cuz R2p2Client::send_req() is called only by the app layer) */
    r2p2_hdr.is_ignore_msg_state_persist() = false;

    slog::log4(r2p2_layer_->get_debug(), r2p2_layer_->get_local_addr(),
               "R2p2Client::send_req(). app lvl id:", r2p2_hdr.app_level_id(), "req id:", r2p2_hdr.req_id(), "single pkt?", single_pkt_rpc, "from:", r2p2_hdr.cl_addr(),
               "thread:", r2p2_hdr.cl_thread_id(), ">to:",
               r2p2_hdr.sr_addr(), "thread:", r2p2_hdr.sr_thread_id(), "req count:", (*thrd_id_app_lvl_id_to_req_count_.at(thread_id))[current_rid],
               "is_msg_extension:", r2p2_hdr.is_msg_extension(), "pkt_id:", r2p2_hdr.pkt_id());
    // if the RPC does not fit in a single packet, the protocol sends a 64 byte packet -
    // given 50 bytes of headers, that leaves 14 bytes of data.
    /** Dale: TODO:
     * 17/06/2025 (?) Don't cumulate req_bytes_left_ here as it will interfere with lower-level pkt processing.
     *                SSIRD transport will do payload cumulation. (impl unchanged from vanilla SIRD)
     */
    client_request_state->req_bytes_left_ = single_pkt_rpc ? 0 : reqn_payload;
    /* Dale: update msg timestamp only during brand new client request, or after reply received for existing request */
    if (is_new_client_request_state || client_request_state->is_update_msg_timestamp)
    {
        client_request_state->msg_creation_time_ = request_id_tuple.ts_;
        client_request_state->is_update_msg_timestamp = false;
        if (is_new_client_request_state) (*thrd_id_to_pending_reqs_map_.at(thread_id))[current_rid] = client_request_state;
    } 
    slog::log6(r2p2_layer_->get_debug(), r2p2_layer_->get_local_addr(), "### msg_creation_time=", r2p2_hdr.msg_creation_time(), "req_id_tuple.ts_=", request_id_tuple.ts_, "client_request_state->msg_creation_time_=", client_request_state->msg_creation_time_);

    int32_t daddr = -2; // -1 used to be destination: r2p2 router
    daddr = r2p2_hdr.sr_addr();
    // add the size of all headers here (eth, ip, udp, r2p2)
    r2p2_layer_->send_to_transport(r2p2_hdr, single_pkt_rpc ? payload : bytes_in_req0, daddr);
}

void R2p2Client::handle_req_rdy(hdr_r2p2 &r2p2_hdr, int payload)
{
    slog::log5(r2p2_layer_->get_debug(), r2p2_layer_->get_local_addr(),
               "handle_req_rdy", r2p2_hdr.req_id(),
               "with pkt_id", r2p2_hdr.pkt_id(), "(first",
               r2p2_hdr.first(), ") from server", r2p2_hdr.sr_addr());
    r2p2_hdr.msg_type() = hdr_r2p2::REQUEST;
    // CAREFULL -> pkt_id will carry the prio level.
    // pkt_id == 1 will be assigned to the first REQN packet
    r2p2_hdr.pkt_id() = 1;
    // unecessary
    r2p2_hdr.first() = false;
    ClientRequestState *client_request_state = thrd_id_to_pending_reqs_map_.at(r2p2_hdr.cl_thread_id())->at(r2p2_hdr.req_id());
    int bytes_left = client_request_state->req_bytes_left_;
    r2p2_hdr.msg_creation_time() = client_request_state->msg_creation_time_;
    r2p2_layer_->send_to_transport(r2p2_hdr, bytes_left, r2p2_hdr.sr_addr());
}

void R2p2Client::handle_reply_pkt(hdr_r2p2 &r2p2_hdr, int payload)
{
    bool is_ooo = false;
    slog::log5(r2p2_layer_->get_debug(), r2p2_layer_->get_local_addr(),
               "Handling reply packet with req id", r2p2_hdr.req_id(),
               "with pkt_id", r2p2_hdr.pkt_id(), "(first",
               r2p2_hdr.first(), ") from server", r2p2_hdr.sr_addr());
    ClientRequestState *client_request_state = NULL;
    try
    {
        client_request_state = thrd_id_to_pending_reqs_map_.at(
                                                               r2p2_hdr.cl_thread_id())
                                   ->at(r2p2_hdr.req_id());
    }
    catch (const std::out_of_range &e)
    {
        std::cerr << e.what() << "\n (likely) Unable to retrieve the request that this reply "
                  << "responds to. Received a reply for a request that was never sent?"
                  << std::endl;
        throw;
    }
    client_request_state->reply_pkts_recvd_++;
    if (r2p2_hdr.first())
    {
        /* Dale: cumultae reply_pkts_to_rec_ */
        client_request_state->reply_pkts_to_rec_ += r2p2_hdr.pkt_id();
    }
    if (!r2p2_hdr.first() && client_request_state->reply_pkts_to_rec_ == 0)
    {
        // TODO: can it be that there is a first() packet that legitimately carries 0?
        // Some packet from the reply has been received before the first() packet
        // of the reply. Ignore for now - but don't judge wheteher the whole reply
        // has been received at this point.
        // This is either due to re-ordering or due to loss.
        // On 13/04/2021 there is no retransmission. So the whole RPC will fail.
        // Also, no reordering between the first packet and any other packet of the same uRPC is possible
        // as each uRPC (or RPC) follows the same path.
        // 31/07/2021: From what I understand, this code will work with OOO pkts
        // That is, as long as no packet is not dropped, the reply will be successfully forwarded to app layer.
        std::cerr << "Some packet (" << r2p2_hdr.pkt_id() << ") from reply has been received before the first() packet "
                  << "of the reply." << std::endl;
        slog::log2(r2p2_layer_->get_debug(), r2p2_layer_->get_local_addr(),
                   "Info:",
                   "\nmsg_type", r2p2_hdr.msg_type(),
                   "\nreq_id",
                   r2p2_hdr.req_id(),
                   "\npkt_id",
                   r2p2_hdr.pkt_id(),
                   "\nfirst",
                   r2p2_hdr.first(),
                   "\ncl_addr",
                   r2p2_hdr.cl_addr(),
                   "\nsr_addr",
                   r2p2_hdr.sr_addr(),
                   "\napp_level_id",
                   r2p2_hdr.app_level_id(),
                   "\nmsg_bytes",
                   r2p2_hdr.msg_bytes(),
                   "\nfirst_urpc",
                   r2p2_hdr.first_urpc(),
                   "\numsg_id",
                   r2p2_hdr.umsg_id());
        is_ooo = true;
    }
    client_request_state->reply_bytes_recvd_ += payload;

    slog::log6(r2p2_layer_->get_debug(), r2p2_layer_->get_local_addr(),
            "CLIENT reply_pkts_recvd_:", client_request_state->reply_pkts_recvd_,
            "reply_pkts_to_rec_:", client_request_state->reply_pkts_to_rec_);

    if (!is_ooo && client_request_state->reply_pkts_recvd_ == client_request_state->reply_pkts_to_rec_)
    {
        slog::log5(r2p2_layer_->get_debug(), r2p2_layer_->get_local_addr(),
                   "Passing complete reply to application. Req ID:", r2p2_hdr.req_id(),
                   "from server", r2p2_hdr.sr_addr());
        r2p2_layer_->send_to_application(r2p2_hdr, client_request_state->reply_bytes_recvd_);
        // TODO: erase entry too (Although it will eventually wrap at 65k)
        /** Dale: TODO: IMPORTANT
         * 10/05/2025
         * Cannot delete client_requeset_state here, cuz message
         * extension might still happen after this in intermittent flows.
         * TODO: use explicit teardown sequence btw client and server to clean up
         * flow state.
         */
        // delete client_request_state;

        /** Dale: set is_reply_received to true so that next client request can update msg
         * creation time (used for FCT measurement; is for msg extensions in intermittent flows)*/
        slog::log6(r2p2_layer_->get_debug(), r2p2_layer_->get_local_addr(), "### reply recv, set is_update_timestamp = true");
        client_request_state->is_update_msg_timestamp = true;
    }
    // TODO: Add check -> have more bytes than expected been received?
}