#ifndef ns_r2p2_client_h
#define ns_r2p2_client_h

#include <unordered_map>
#include <unordered_set>
#include "r2p2-hdr.h"
#include "packet.h"
#include "r2p2.h"

class R2p2;
struct ClientRequestState;
struct RequestIdTuple;

class R2p2Client
{
public:
    R2p2Client(R2p2 *r2p2_layer);
    virtual ~R2p2Client();
    void send_req(int payload, const RequestIdTuple &request_id_tuple);
    void handle_req_rdy(hdr_r2p2 &r2p2_hdr, int nbytes);
    void handle_reply_pkt(hdr_r2p2 &r2p2_hdr, int nbytes);

    // void set_max_payload(int);

protected:
    // req_id will be local to the client thread id (as it is for port in the impl)
    typedef std::unordered_map<request_id, ClientRequestState *> req_id_to_req_state_t;
    std::unordered_map<int, req_id_to_req_state_t *> thrd_id_to_pending_reqs_map_;
    // To keep track of the current reqid per thread
    /* Dale: assume each thread can multiplex several different requests */
    typedef std::unordered_set<request_id> rid_set_t;
    std::unordered_map<int, rid_set_t *> thrd_id_to_req_id_;
    /* Dale: keep track of how many requests each app_level_id in each thread has made */
    typedef std::unordered_map<request_id, int> req_id_to_req_count_t;
    std::unordered_map<int, req_id_to_req_count_t *> thrd_id_app_lvl_id_to_req_count_;
    // int max_payload_;
    R2p2 *r2p2_layer_;
};
#endif