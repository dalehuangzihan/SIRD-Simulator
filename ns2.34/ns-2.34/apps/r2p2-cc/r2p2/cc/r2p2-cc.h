#ifndef ns_r2p2_cc_h
#define ns_r2p2_cc_h

#include <queue>
#include <vector>
#include <map>
#include "r2p2-generic.h"
#include "r2p2.h"
#include "r2p2-hdr.h"
#include "r2p2-udp.h"
#include "traced-class.h"
#include "msg-tracer.h"

class R2p2CCFifo;

/** Dale:
 * This is <client_addr, thread_id, req_id, is_persist_msg_state, is_ignore_persist, msg_id>
 * 12/06/2025 is_ignore_persist is for overriding the persist decision; currently for allowing GRANT_REQ for REPLY msgs to be treated separately from GRANT_REQ for data.
 * 20/06/2025 Each app (sender/receiver pair) can simul use diff extensible-msgs for diff app-lvl req (diff app lvl id). Currently use req_id field to carry app lvl id.
 */
typedef std::tuple<int32_t, int, request_id, bool, bool> uniq_req_id_t; 
/* Dale: helper functions */
namespace ReqIdTuple
{
    static bool is_persist_msg_state(uniq_req_id_t &req_id)
    {
        return std::get<3>(req_id);
    }

    static bool is_ignore_persistence(uniq_req_id_t &req_id)
    {
        return std::get<4>(req_id);
    }

    static void set_ignore_persistence(uniq_req_id_t &req_id)
    {
        std::get<4>(req_id) = true;
    }
}
typedef std::tuple<hdr_r2p2, int, int32_t> packet_info_t;

class DownlinkTimer : public TimerHandler
{
public:
    DownlinkTimer(R2p2CCFifo *r2p2_cc) : r2p2_cc_(r2p2_cc) {}

protected:
    void expire(Event *);
    R2p2CCFifo *r2p2_cc_;
};

class UplinkTimer : public TimerHandler
{
public:
    UplinkTimer(R2p2CCFifo *r2p2_cc) : r2p2_cc_(r2p2_cc) {}

protected:
    void expire(Event *);
    R2p2CCFifo *r2p2_cc_;
};

class R2p2CCGeneric : public R2p2Transport, public SimpleTracedClass
{
    friend class R2p2UplinkQueue;

public:
    R2p2CCGeneric();
    virtual ~R2p2CCGeneric();

    virtual void recv(Packet *pkt, Handler *h);
    virtual void send_to_transport(hdr_r2p2 &, int nbytes, int32_t daddr);

    virtual void attach_r2p2_layer(R2p2 *r2p2_layer);
    inline int get_debug()
    {
        return debug_;
    }

protected:
    virtual void forward_to_transport(packet_info_t, MsgTracerLogs &&logs);

    virtual void attach_r2p2_router_agent(R2p2Agent *r2p2_router_agent);
    virtual int command(int argc, const char *const *argv);

    int32_t r2p2_router_addr_;
    R2p2 *r2p2_layer_;
};

class R2p2CCNoop : public R2p2CCGeneric
{
public:
    R2p2CCNoop();
    virtual ~R2p2CCNoop();
};

#endif