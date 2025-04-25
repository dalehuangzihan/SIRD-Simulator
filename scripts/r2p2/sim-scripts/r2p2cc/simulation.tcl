set script_path [ file dirname [ file normalize [ info script ] ] ]

# Utilities
source "$script_path/../util.tcl"
# Common variables
source "$script_path/../common.tcl"
# Needed for dict support in tcl 8.4
source "$script_path/dict.tcl" 


# ------------------- Source parameters -------------------
set script_params_file [lindex $argv 0]
set do_run [lindex $argv 1]

if {[file exists $script_params_file]} {
    source $script_params_file
} else {
    puts "A generated parameters file must exist before staring the simulation."
    exit 1
}

if {$do_run == "1"} {

# --------------------- Debug -----------------
# Indicative debug levels for code using this (value of debug_):
#   0: Errors etc - always displayed
#   1: Only important information that does not cause clutter
#   2: Debug info that will not cause output regularly (eg for every request/pkt)
#   3: Secondary debug info that will not cause output regularly (eg for every request/pkt)
#   4: Debug info that will cause frequent output (eg for every request)
#   5: Debug info that will cause very frequent output (eg for every packet)
#   6: Debug info that will cause deterministcally very frequent output (eg polling/timers)
#   7: Secondary debug info that will cause deterministcally very frequent output (eg polling/timers)
     
# Set the debug_ flag of individual classes to make use of the logging tool in
# ns2.34/ns-2.34/apps/r2p2-cc/common/util.h
if {$global_debug > 0} {
    Generic_app set debug_ $global_debug
    Agent/TCP/FullTcp set debug_ $global_debug
    Agent/XPass set debug_ $global_debug
    Agent/UDP/R2P2 set debug_ $global_debug
    Agent/UDP/HOMA set debug_ $global_debug
    R2P2 set debug_ $global_debug
    R2P2_Router set debug_ $global_debug
    R2P2_CC_MICRO set debug_ $global_debug
    HOMA set debug_ $global_debug
} else {
    Generic_app set debug_ $app_debug
    Agent/TCP/FullTcp set debug_ $full_tcp_debug
    Agent/XPass set debug_ $full_tcp_debug
    Agent/UDP/R2P2 set debug_ $r2p2_udp_debug
    Agent/UDP/HOMA set debug_ $homa_transport_debug
    R2P2 set debug_ $r2p2_tranport_debug
    HOMA set debug_ $homa_transport_debug
    R2P2_Router set debug_ $r2p2_router_debug
    R2P2_CC_MICRO set debug_ $r2p2_cc_debug
}

# ---------------------------------------------------------

puts "Num hosts/clients/servers $num_hosts/$num_client_apps/$num_server_apps"

if {$transport_protocol == "r2p2" || $transport_protocol == "homa"} {
    set queue_size $general_queue_size
} elseif {$transport_protocol == "pfabric"} {
    set queue_size $queue_size_pfab
} elseif {$transport_protocol == "dctcp"} {
    set queue_size $general_queue_size
} elseif {$transport_protocol == "xpass"} {
    # Apply the same treatment: Infinite buffers. Express pass does not depend on shallow queues like NDP
    set queue_size $general_queue_size
} else {
    puts "Unknown protocol $transport_protocol"
    exit 1
}
set tcp_max_payload_size [expr $packet_size_bytes - $tcp_common_headers_size - $inter_pkt_and_preamble]


puts "Interval between requests per client: $mean_per_client_req_interval_us us"
puts "Reqs per sec per client: $per_client_req_send_rate_rps rps"
puts "Capacity per sec per server: $per_server_capacity_rps rps"
puts "Reqs per sec: $global_req_send_rate_rps rps"
puts "Server Capacity per sec: $total_server_capacity_rps rps"

puts "Estimated sending rate per client: $estim_send_rate_per_client_gbps_bgrnd Gbps"
puts "Total req rate: $total_cl_send_rate_gbps Gbps"
puts "core_link_speed_gbps: $core_link_speed_gbps Gbps"
puts "---------"
puts "Approx app load = $approx_app_load %"
puts "approx_leaves_load = $approx_leaves_load %"
puts "Approx req nwrk load at leaves = $approx_req_nwrk_load_leaves %"
puts "Approx reply nwrk load at leaves = $approx_reply_nwrk_load_leaves %"
puts "Approx max req nwrk load at core = $approx_max_req_nwrk_load_core %"
puts "Approx max reply nwrk load at core = $approx_max_reply_nwrk_load_core %"
puts "Simulation Duration = $simul_dur seconds"
puts "<<^^>>\n"

set tf [open "${results_path}/packet_trace.tr" w]
if {$capture_pkt_trace != 0} {
    $ns trace-all $tf
}

if {$capture_msg_trace != 0} {
    Generic_app set capture_msg_trace_ 1
}

# --------------------- NODES ---------------------
set parmtr_file [open "${results_path}/parameters" w]
# For shared buffer switches
Node set shared_queue_len_pkts_ $queue_size 

puts -nonewline $parmtr_file "client_addr "
foreach host [dict keys $hosts] {
    set attributes [dict get $hosts $host]
    set host_node($host) [$ns node]
    $host_node($host) set nodetype_ 1
    if {[dict get $attributes client]} {
        puts -nonewline $parmtr_file "[$host_node($host) node-addr] "
    }
}
puts $parmtr_file " "

puts -nonewline $parmtr_file "server_addr "
foreach host [dict keys $hosts] {
    set attributes [dict get $hosts $host]
    if {[dict get $attributes server]} {
        puts -nonewline $parmtr_file "[$host_node($host) node-addr] "
    }
}
puts $parmtr_file " "

puts -nonewline $parmtr_file "host_addr "
foreach host [dict keys $hosts] {
    puts -nonewline $parmtr_file "[$host_node($host) node-addr] "
}
puts $parmtr_file " "

puts -nonewline $parmtr_file "tor_addr "
for {set i 0} {$i < $num_tors} {incr i} {
    set tor_node($i) [$ns node]
    $tor_node($i) set nodetype_ 2
    puts -nonewline $parmtr_file "[$tor_node($i) node-addr] "
}
puts $parmtr_file " "

puts -nonewline $parmtr_file "aggr_addr "
for {set i 0} {$i < $num_aggr} {incr i} {
    set aggr_node($i) [$ns node]
    $aggr_node($i) set nodetype_ 3
    puts -nonewline $parmtr_file "[$aggr_node($i) node-addr] "
}
puts $parmtr_file ""
close $parmtr_file


# --------------------- LINKS ---------------------
# xpass
# 10 * 125,000,000 * 84 / (84+1538) = 65M
# 100 * 125,000,000 * 84 / (84+1538) = 647M -> bytes / second = 5.178792GBps
set xpass_creditBW_leaves [expr $leaf_link_speed_gbps*125000000*$xpass_avgCreditSize/($xpass_avgCreditSize+$xpass_maxEthernetSize)]
set xpass_creditBW_leaves [expr int($xpass_creditBW_leaves)]
set xpass_creditBW_core [expr $core_link_speed_gbps*125000000*$xpass_avgCreditSize/($xpass_avgCreditSize+$xpass_maxEthernetSize)]
set xpass_creditBW_core [expr int($xpass_creditBW_core)]

# Q size in packets (for all links)
Queue set limit_ $queue_size
Queue/DropTail set queue_in_bytes_ true
Queue/DropTail set bw_gbps_ $leaf_link_speed_gbps
Queue/DropTail set num_prios_ $drop_tail_num_prios
Queue/RED set num_prios_ $drop_tail_num_prios
Queue/RED set queue_in_bytes_ true
if {$switch_queue_type == "per-port"} {
    Queue set switch_shared_buffer_ 0
} elseif {$switch_queue_type == "shared"} {
    Queue set switch_shared_buffer_ 1
}

set uplink_q_sz_pkts 1000000000
# only red and droptail support shared buffer
set leaf_sw_q_type DropTail 
set core_sw_q_type DropTail
if {$transport_protocol == "r2p2"} {
    # the +50 is hardwired in r2p2-udp.cc
    # mean_pktsize_ defines the size of the q. From drop-tail.c
    Queue/DropTail set mean_pktsize_ [expr $mean_packet_size]
    Queue/DropTail set drop_prio_ false
    Queue/RED set drop_prio_ false
    
    if {$r2p2_ecn_at_core == 1} {
        Queue/RED set bytes_ true
        Queue/RED set mean_pktsize_ [expr $mean_packet_size]
        Queue/RED set gentle_ false
        Queue/RED set q_weight_ 1.0
        Queue/RED set mark_p_ 1.0
        # In packets
        Queue/RED set thresh_ $r2p2_ecn_threshold_min
        Queue/RED set maxthresh_ $r2p2_ecn_threshold_max
        
        Queue/RED set setbit_ true
        set core_sw_q_type RED
    }

    if {$r2p2_hybrid_in_network_prios == 1} {
        Queue/DropTail set deque_prio_ true
        Queue/DropTail set keep_order_ true
        Queue/RED set deque_prio_ true
    } else {
        Queue/DropTail set deque_prio_ false
        Queue/DropTail set keep_order_ true
        Queue/RED set deque_prio_ false
    }
# TODO: CHECK
} elseif {$transport_protocol == "homa"} { 
    # this is meant to be approximate
    Queue/DropTail set mean_pktsize_ [expr $mean_packet_size]
    if {$homa_in_network_prios == 1} {
        Queue/DropTail set drop_prio_ false 
        # MUST disable priorities on the uplink, else Homa breaks (bad tail latency because of starvation at the uplink for low prio pkts). Homa keeps this buffer empty anyway
        Queue/DropTail set deque_prio_ true
        Queue/DropTail set keep_order_ false
    } else {
        Queue/DropTail set drop_prio_ false 
        Queue/DropTail set deque_prio_ false
        Queue/DropTail set keep_order_ false
    }
} elseif {$transport_protocol == "pfabric"} {
    Queue/DropTail set mean_pktsize_ [expr $mean_packet_size]
    Queue/DropTail set drop_prio_ true
    Queue/DropTail set deque_prio_ true
    Queue/DropTail set keep_order_ true
} elseif {$transport_protocol == "dctcp"} {
    # TODO: it is likely that DCTCP should be configured differently for the core
    Queue/RED set bytes_ true
    Queue/RED set mean_pktsize_ [expr $mean_packet_size]
    Queue/RED set gentle_ false
    Queue/RED set q_weight_ 1.0
    Queue/RED set mark_p_ 1.0
    # In packets
    Queue/RED set thresh_ $dctcp_K
    Queue/RED set maxthresh_ $dctcp_K
    Queue/RED set drop_prio_ false
    Queue/RED set deque_prio_ false
    Queue/RED set setbit_ true
    set leaf_sw_q_type RED
    set core_sw_q_type RED
} elseif {$transport_protocol == "xpass"} {
    # 8 packets. # TODO: check that credit packets are indeed of size 84
    # WHAT ABOUT HOST UPLINKS? They must also be XPassDropTail. Ok correct.
    Queue/XPassDropTail set credit_limit_ [expr 84*8] 
    Queue/XPassDropTail set max_tokens_ [expr 84*2]
    # Explicitly overwritting core credit rates later
    Queue/XPassDropTail set token_refresh_rate_ $xpass_creditBW_leaves 
    Queue/XPassDropTail set data_limit_ [expr $queue_size * 1538]

    DelayLink set avoidReordering_ true
    Classifier/MultiPath set symmetric_ true
    Classifier/MultiPath set nodetype_ 0

    set leaf_sw_q_type XPassDropTail
    set core_sw_q_type XPassDropTail
} else {
    puts "Unknown protocol $transport_protocol"
    exit 1
}


foreach host [dict keys $hosts] {
    set attributes [dict get $hosts $host]
    set tor [dict get $attributes tor]
    # puts "Creating $leaf_link_speed_gbps gbps links between tor $tor and host $host"
    $ns simplex-link $tor_node($tor) $host_node($host) ${leaf_link_speed_gbps}Gb ${leaf_link_latency_ms}ms $leaf_sw_q_type
    $ns simplex-link $host_node($host) $tor_node($tor) ${leaf_link_speed_gbps}Gb ${leaf_link_latency_ms}ms $leaf_sw_q_type

    # Attach tor->host link to node for shared switch buffer mode
    $tor_node($tor) attach-egress-queue [[$ns link $tor_node($tor) $host_node($host)] queue]
    # Do the same for the single link/queue of each host uplink for consistency
    $host_node($host) attach-egress-queue [[$ns link $host_node($host) $tor_node($tor)] queue]

    # Set the size of the shared uplink buffer (if cuffer is set to shared - doesn't matter since there is one link)
    $host_node($host) set shared_queue_len_pkts_ $uplink_q_sz_pkts
    if {$transport_protocol == "r2p2" || $transport_protocol == "homa"} {
        # pFabric is meant to have small queues at host-to-ToR
        # What should happen with DCTCP (q size at host? Mark at host? See https://docs.google.com/presentation/d/1_PfsE151sgVl2FDAuCY1nRKgffvljCHXKudpqwbVUrs/edit?usp=sharing)
        $ns queue-limit $host_node($host) $tor_node($tor) $uplink_q_sz_pkts
        if {$r2p2_host_uplink_prio == 1 && $transport_protocol == "r2p2"} {
            # host uplinks do prio forwarding
            set q [[$ns link $host_node($host) $tor_node($tor)] queue]
            $q set deque_prio_ true
            $q set keep_order_ true
        }
        if {$transport_protocol == "homa"} {
            set q [[$ns link $host_node($host) $tor_node($tor)] queue]
            # MUST disable priorities on the uplink, else Homa breaks (bad tail latency because of starvation at the uplink for low prio pkts). Homa keeps this buffer empty anyway
            $q set drop_prio_ false
            $q set deque_prio_ false
            $q set keep_order_ false
        }
    }
}


set parmtr_file [open "${results_path}/parameters" a+]
# Write tor->node in parameter file
for {set tor 0} {$tor < $num_tors} {incr tor} {
    puts -nonewline $parmtr_file "tor_[$tor_node($tor) node-addr]"
    foreach {host} [set "tor_${tor}_hosts"] {
        puts -nonewline $parmtr_file " [$host_node($host) node-addr]"
    }
    puts $parmtr_file ""
}

# Aggr to tor
for {set i 0} {$i < $num_aggr} {incr i} {
    puts -nonewline $parmtr_file "aggr_[$aggr_node($i) node-addr] "
    for {set j 0} {$j < $num_tors} {incr j} {
        $ns duplex-link $aggr_node($i) $tor_node($j) ${core_link_speed_gbps}Gb ${core_link_latency_ms}ms $core_sw_q_type
        puts -nonewline $parmtr_file "[$tor_node($j) node-addr] "
        # puts "Creating links between aggr $i and tor $j"
        # Attach aggr->tor link to node for shared switch buffer mode
        $aggr_node($i) attach-egress-queue [[$ns link $aggr_node($i) $tor_node($j)] queue]
        # Attach tor->aggr link to node for shared switch buffer mode
        $tor_node($j) attach-egress-queue [[$ns link $tor_node($j) $aggr_node($i)] queue]

        if { $transport_protocol == "xpass" } {
            set q_up [[$ns link $tor_node($j) $aggr_node($i)] queue]
            set q_down [[$ns link $aggr_node($i) $tor_node($j)] queue]
            $q_up set token_refresh_rate_ $xpass_creditBW_core
            $q_down set token_refresh_rate_ $xpass_creditBW_core
        }
    }
    puts $parmtr_file ""
}

close $parmtr_file

# --------------------- TRANSPORT ---------------------

# One transport agent per node (for r2p2)
if {$transport_protocol == "r2p2" || $transport_protocol == "homa"} {
    # This is the payload size. This + headers is what will be transmitted over the link (and queued)

    # packetSize_ is used by the agent as the max_payload size
    # (application payload) -> corresponds to size_ in the Agent udp classes
    if {$transport_protocol == "r2p2"} {
        # Agent/UDP/R2P2 set packetSize_ $max_payload_size
        set agent_type Agent/UDP/R2P2
    } elseif {$transport_protocol == "homa"} {
        # TODO: CHECK
        # Agent/UDP/HOMA set packetSize_ $max_payload_size
        set agent_type Agent/UDP/HOMA
    }

    # Create and attach agents to clients and servers.
    set agent_host_host [dict create]
    foreach host [dict keys $hosts] {
        set attributes [dict get $hosts $host]
        set is_client [dict get $attributes client]
        set is_server [dict get $attributes server]
        foreach host_in [dict keys $hosts] {
            set attributes_in [dict get $hosts $host_in]
            set is_client_in [dict get $attributes_in client]
            set is_server_in [dict get $attributes_in server]
            if {$host != $host_in} {
                # Only create agents to connect clients with servers (and not servers to servers or clients to clients)
                if {($is_client && $is_server_in) || ($is_server && $is_client_in)} {
                    dict set agent_host_host "${host}_$host_in" [new $agent_type]
                    puts "Attaching agent pointing to $host_in to host $host"
                    $ns attach-agent $host_node($host) [dict get $agent_host_host "${host}_$host_in"]
                }
            }
        }
    }

    # Connect clients and servers
    foreach index [dict keys $agent_host_host] {
        set from_to [split $index "_"]
        set from [lindex $from_to 0]
        set to [lindex $from_to 1]
        $ns connect [dict get $agent_host_host "${from}_${to}"] [dict get $agent_host_host "${to}_${from}"]
        # puts "Connecting (connect) hosts: $from and $to"
    }

    # Create router agents (one for each node (all nodes, not just of the router's rack))
    # Therefore the router's JBSQ mode does not work
    # Connect each router with all agents (not good for jbsq - in this case we would only connect 
    # the servers of the tor to the router on the tor and then redirect msgs for other tors to the 
    # router  of that tor)
    # 2021: so each router has a connection to all nodes (machines) in the topology.
    # So when it receives a REQ0, the router picks a uniformly random destination (except source)
    # set agent_router_host [dict create]
    # for {set i 0} {$i < $num_tors} {incr i} {
    #     for {set j 0} {$j < $num_hosts} {incr j} {
    #         dict set agent_router_host "${i}_${j}" [new Agent/UDP/R2P2]
    #         $ns attach-agent $tor_node($i) [dict get $agent_router_host "${i}_${j}"]
    #         puts "Attaching agent to host $j to tor (r2p2 router) $i"
    #     }
    # }

    # # Also create the respective agents at nodes
    # set agent_host_router [dict create]
    # for {set i 0} {$i < $num_tors} {incr i} {
    #     for {set j 0} {$j < $num_hosts} {incr j} {
    #         dict set agent_host_router "${j}_${i}" [new Agent/UDP/R2P2]
    #         $ns attach-agent $host_node($j) [dict get $agent_host_router "${j}_${i}"]
    #         puts "Attaching agent to tor (r2p2 router) $i to host $j"
    #     }
    # }

    # # connect nodes and router
    # for {set i 0} {$i < $num_tors} {incr i} {
    #     for {set j 0} {$j < $num_hosts} {incr j} {
    #         $ns connect [dict get $agent_host_router "${j}_${i}"] [dict get $agent_router_host "${i}_${j}"]
    #         puts "Connecting (connect) router<->host: $i and $j"
    #     }
    # }
} elseif {$transport_protocol == "pfabric"} {
    if {$per_flow_mp == 0} {  
        # Not sure abt this, in QJump the do this and then unconditionally also disable it. test
        Agent/TCP/FullTcp set dynamic_dupack_ 0.75
    }
    Agent/TCP set ecn_ 1
    Agent/TCP set old_ecn_ 1
    Agent/TCP set packetSize_ $tcp_max_payload_size
    Agent/TCP/FullTcp set segsize_ $tcp_max_payload_size
    Agent/TCP/FullTcp set spa_thresh_ 0
    Agent/TCP set slow_start_restart_ true
    Agent/TCP set windowOption_ 0
    Agent/TCP set tcpTick_ 0.000001
    Agent/TCP set minrto_ $pfab_min_rto
    Agent/TCP set maxrto_ 2

    Agent/TCP/FullTcp set nodelay_ true; # disable Nagle
    Agent/TCP/FullTcp set segsperack_ $tcp_ack_ratio
    Agent/TCP/FullTcp set interval_ 0.000006

    Agent/TCP set ecnhat_ true
    Agent/TCPSink set ecnhat_ true
    Agent/TCP set ecnhat_g_ $pfab_g;

    #Shuang
    Agent/TCP/FullTcp set prio_scheme_ $prio_scheme;
    Agent/TCP/FullTcp set dynamic_dupack_ 1000000; #disable dupack
    Agent/TCP set window_ 1000000
    Agent/TCP set windowInit_ 12
    Agent/TCP set rtxcur_init_ $pfab_min_rto;
    Agent/TCP/FullTcp/Sack set clear_on_timeout_ false
    #Agent/TCP/FullTcp set pipectrl_ true
    Agent/TCP/FullTcp/Sack set sack_rtx_threshmode_ 2
    if {$queue_size > 12} {
        echo "This looks like a missconfiguration for pFabric. Exiting"
        exit 1
        Agent/TCP set maxcwnd_ [expr $queue_size - 1]
    } else {
        echo "This looks like a missconfiguration for pFabric. Exiting"
        exit 1
        Agent/TCP set maxcwnd_ 12
    }
    Agent/TCP/FullTcp set prob_cap_ $prob_cap
    # hack
    Agent/TCP/FullTcp/Sack/MinTCP set conctd_to_pfabric_app_ 1
} elseif {$transport_protocol == "dctcp"} {
    Agent/TCP set window_ 1256
    Agent/TCP set windowInit_ $dctcp_init_cwnd
    Agent/TCP set max_ssthresh_ 111200
    Agent/TCP set minrto_ $dctcp_min_rto
    # boolean: re-init cwnd after connection goes idle.  On by default. 
    # used true from reproduc until 18/11. Setting to false bcs of example
    Agent/TCP set slow_start_restart_ false
    # def is 1. Not clear what it is. dctcp example has it at 0
    Agent/TCP set windowOption_ 0
    # probly smthing to do with simulation sampling. extreme (0.000001 <- dctcp
    # reproductions study (was using until 19/11)) - 0.01 is default and also used in example. 
    Agent/TCP set tcpTick_ 0.00000001
    # retransmission time out. default values are fine.
    #Agent/TCP set minrto_ $min_rto
    #Agent/TCP set maxrto_ 2

    # Don't know what this is. default is 0
    # "below do 1 seg per ack [0:disable]"
    Agent/TCP/FullTcp set spa_thresh_ 0
    # disable sender-side Nagle? def: false
    # https://www.lifewire.com/nagle-algorithm-for-tcp-network-communication-817932
    Agent/TCP/FullTcp set nodelay_ true; # disable Nagle
    # def is 1. "ACK frequency". (there is a segs_per_ack_ in .h)
    Agent/TCP/FullTcp set segsperack_ 1;
    # delayed ack (repr has it at 0.000006, ex has it at 0.04, def is 0.1)
    Agent/TCP/FullTcp set interval_ 0.000006
    Agent/TCP/FullTcp set segsize_ $tcp_max_payload_size
    Agent/TCP set packetSize_ $tcp_max_payload_size
    Agent/TCP set maxcwnd_ [expr $queue_size - 1]

    # def is 0
    Agent/TCP set ecn_ 1
    # def is 0
    Agent/TCP set old_ecn_ 1
    Agent/TCP set ecnhat_ true
    Agent/TCPSink set ecnhat_ true
    Agent/TCP set ecnhat_g_ $dctcp_g;

    # hack
    Agent/TCP/FullTcp set conctd_to_pfabric_app_ 1
} elseif {$transport_protocol == "xpass"} {
    Agent/XPass set min_credit_size_ $xpass_minCreditSize
    Agent/XPass set max_credit_size_ $xpass_maxCreditSize
    Agent/XPass set min_ethernet_size_ $xpass_minEthernetSize
    Agent/XPass set max_ethernet_size_ $xpass_maxEthernetSize
    Agent/XPass set max_credit_rate_ $xpass_creditBW_leaves
    Agent/XPass set alpha_ $xpass_alpha
    Agent/XPass set target_loss_scaling_ 0.125
    # TODO: is this correct or is it that 0.0625 just happens to be one packet at 10gig & RTT
    Agent/XPass set w_init_ $xpass_w_init
    Agent/XPass set min_w_ 0.01
    Agent/XPass set retransmit_timeout_ 0.0001
    Agent/XPass set min_jitter_ $xpass_minJitter
    Agent/XPass set max_jitter_ $xpass_maxJitter
} else {
    puts "Cannot configure agents of unknown protocol $transport_protocol"
    exit 1
}

# ----------------- CONFIGURE R2P2 -----------------
if {$transport_protocol == "r2p2"} {
    # R2P2 set max_payload_ $max_payload_size

    # R2P2 MicroRPCs
    R2P2_CC_MICRO set urpc_sz_bytes_ $urpc_sz_bytes
    R2P2_CC_MICRO set single_path_per_msg_ $single_path_per_msg
    R2P2_CC_MICRO set pace_uplink_ $r2p2_pace_uplink
    R2P2_CC_MICRO set uplink_deque_policy_ $r2p2_uplink_deque_policy
    R2P2_CC_MICRO set ecn_capable_ $r2p2_ecn_at_core
    R2P2_CC_MICRO set link_speed_gbps_ $leaf_link_speed_gbps
    R2P2_CC_MICRO set ce_new_weight_ $r2p2_ce_new_weight
    R2P2_CC_MICRO set ecn_mechanism_influence_ $r2p2_ecn_mechanism_influence
    R2P2_CC_MICRO set ecn_init_slash_mul_ $r2p2_ecn_init_slash_mul
    R2P2_CC_MICRO set ecn_min_mul_ $r2p2_ecn_min_mul
    R2P2_CC_MICRO/HYBRID set ecn_min_mul_nw_ $r2p2_ecn_min_mul_nw
    R2P2_CC_MICRO/HYBRID set state_polling_ival_s_ $state_polling_ival_s
    R2P2_CC_MICRO/HYBRID set budget_bytes_ $r2p2_budgets_intra_max_bytes
    R2P2_CC_MICRO/HYBRID set unsolicited_thresh_bytes_ $r2p2_unsolicited_thresh_bytes
    R2P2_CC_MICRO/HYBRID set unsolicited_limit_senders_ $r2p2_unsolicited_limit_senders
    R2P2_CC_MICRO/HYBRID set unsolicited_burst_when_idle_ $r2p2_unsolicited_burst_when_idle
    R2P2_CC_MICRO/HYBRID set priority_flow_ $r2p2_priority_flow
    R2P2_CC_MICRO/HYBRID set data_prio_ $r2p2_data_prio
    R2P2_CC_MICRO/HYBRID set sender_policy_ratio_ $r2p2_sender_policy_ratio
    R2P2_CC_MICRO/HYBRID set receiver_policy_ $r2p2_elet_receiver_policy
    R2P2_CC_MICRO/HYBRID set account_unsched_ $r2p2_elet_account_unsched
    R2P2_CC_MICRO/HYBRID set max_srpb_ $r2p2_elet_srpb
    R2P2_CC_MICRO/HYBRID set ecn_thresh_pkts_ $r2p2_sender_ecn_threshold
    R2P2_CC_MICRO/HYBRID set reset_after_x_rtt_ $r2p2_hybrid_reset_after_x_rtt
    R2P2_CC_MICRO/HYBRID set pace_grants_ $r2p2_hybrid_pace_grants
    R2P2_CC_MICRO/HYBRID set additive_incr_mul_ $r2p2_hybrid_additive_incr_mul
    R2P2_CC_MICRO/HYBRID set sender_policy_ $r2p2_hybrid_sender_policy
    R2P2_CC_MICRO/HYBRID set sender_algo_ $r2p2_hybrid_sender_algo
    R2P2_CC_MICRO/HYBRID set eta_ $r2p2_hybrid_eta
    R2P2_CC_MICRO/HYBRID set wai_ $r2p2_hybrid_wai
    R2P2_CC_MICRO/HYBRID set max_stage_ $r2p2_hybrid_max_stage

    # ~~ NODES
    # FIX: non-convention-respecting class names
    for {set j 0} {$j < $num_hosts} {incr j} {
        if {$r2p2_cc_scheme == "noop"} {
            set r2p2CC($j) [new R2P2_CC_NOOP]
        } elseif {$r2p2_cc_scheme == "micro"} {
            set r2p2CC($j) [new R2P2_CC_MICRO]
        } elseif {$r2p2_cc_scheme == "micro-hybrid"} {
            set r2p2CC($j) [new R2P2_CC_MICRO/HYBRID]
        } else {
            puts "Error, unknown r2p2_cc_scheme: $r2p2_cc_scheme"
            exit 1
        }
        # Receiver driven transport layer (r2p2 and homa)
        set rdTransportLayer($j) [new R2P2]
    }

    # making the r2p2 cc module at each node aware of all its agents that connect to other nodes
    # R2P2 - must have connected agents before attaching them to r2p2
    foreach index [dict keys $agent_host_host] {
        set from_to [split $index "_"]
        set from [lindex $from_to 0]
        set to [lindex $from_to 1]
        $r2p2CC($from) attach-agent [dict get $agent_host_host "${from}_${to}"]
        # puts "Attaching agent ($from -> $to) to r2p2-cc module of $from"
    }

    # # using a special command for the router agent (for feedback)
    # for {set tor 0} {$tor < $num_tors} {incr tor} {
    #     foreach {host} [set "tor_${tor}_hosts"] {
    #         $r2p2CC($host) attach-router-agent [dict get $agent_host_router "${host}_${tor}"]
    #         puts "Attaching host router agent ($host -> $tor) to r2p2-cc module of $host"
    #         for {set other_tor 0} {$other_tor < $num_tors} {incr other_tor} {
    #             if {$other_tor != $tor} {
    #                 # puts "attach agent $other_tor of $host"
    #                 # Mess (want to have one router per node but still need to register the cc layer for
    #                 # the other routers so the node can receive from them (that connection))
    #                 puts "Attaching host router agent ($host -> $other_tor) to r2p2-cc module of $host"
    #                 $r2p2CC($host) attach-agent [dict get $agent_host_router "${host}_${other_tor}"]
    #             }
    #         }
    #     }
    # }

    # attaching the r2p2 cc module with the r2p2 layer
    for {set j 0} {$j < $num_hosts} {incr j} {
        $rdTransportLayer($j) attach-cc-module $r2p2CC($j)
        # puts "Attaching cc-module $j to r2p2 layer $j"
    }

    # # ~~ ROUTER
    # R2P2_Router set router_latency_s_ [expr $router_latency_us /1000.0/1000.0]
    # R2P2_Router set pooled_sender_credit_bytes_ $r2p2_pooled_sender_credit_bytes
    # for {set i 0} {$i < $num_tors} {incr i} {
    #     set r2p2LayerRouter($i) [new R2P2_Router]
    #     $r2p2LayerRouter($i) op-mode $router_op_mode
    #     # This will not work properly with jbsq
    #     # puts "Creating r2p2 router with [expr $num_hosts*$threads_per_host] workers"
    #     $r2p2LayerRouter($i) num-workers [expr $num_server_apps]
    #     puts "Set the number of workers of r2p2 router $i to $num_server_apps" 
    # }

    # # making the router's r2p2 layer aware of its agents
    # # Not using threads
    # # Attach all _server_ agents to all routers
    # for {set tor 0} {$tor < $num_tors} {incr tor} {
    #     foreach host $server_apps {
    #         $r2p2LayerRouter($tor) attach-server-agent [dict get $agent_router_host "${tor}_${host}"] 1
    #         puts "Attaching worker server $host to router $tor"
    #     }
    # }

    # # Also attach all _client_ agents to routers so that routers can receive requests from clients
    # for {set tor 0} {$tor < $num_tors} {incr tor} {
    #     foreach host $client_apps {
    #         $r2p2LayerRouter($tor) attach-client-agent [dict get $agent_router_host "${tor}_${host}"]
    #         puts "Attaching client $host to router $tor"
    #     }
    # }

    # # hack that gives r2p2cc instances access to their TOR's router instance.
    # for {set tor 0} {$tor < $num_tors} {incr tor} {
    #     foreach {host} [set "tor_${tor}_hosts"] {
    #         $r2p2CC($host) attach-router $r2p2LayerRouter($tor)
    #     }
    # }
} elseif {$transport_protocol == "homa"} {
    HOMA set nicLinkSpeed $leaf_link_speed_gbps
    HOMA set rttBytes $homa_rtt_bytes
    # Always seems to be set to this
    HOMA set maxOutstandingRecvBytes $homa_rtt_bytes
    HOMA set grantMaxBytes $homa_grant_max_bytes
    HOMA set allPrio $homa_all_prio
    HOMA set adaptiveSchedPrioLevels $homa_adaptive_sched_prio_levels
    HOMA set numSendersToKeepGranted $homa_adaptive_sched_prio_levels
    HOMA set accountForGrantTraffic $homa_account_for_grant_traffic
    if {[expr $homa_all_prio - $homa_adaptive_sched_prio_levels] < 1} {
        puts "homa_all_prio must be higher than homa_adaptive_sched_prio_levels"
        exit 1
    }
    HOMA set prioResolverPrioLevels [expr $homa_all_prio - $homa_adaptive_sched_prio_levels]
    HOMA set unschedPrioUsageWeight $homa_unsched_prio_usage_weight
    HOMA set isRoundRobinScheduler $homa_is_round_robin_scheduler
    HOMA set linkCheckBytes $homa_link_check_bytes
    HOMA set cbfCapMsgSize $homa_rtt_bytes
    HOMA set boostTailBytesPrio $homa_boost_tail_bytes_prio
    HOMA set defaultReqBytes $homa_default_req_bytes
    HOMA set defaultUnschedBytes $homa_default_unsched_bytes
    HOMA set useUnschRateInScheduler $homa_use_unsch_rate_in_scheduler
    HOMA set workloadType $homa_workload_type
    for {set j 0} {$j < $num_hosts} {incr j} {
        set rdTransportLayer($j) [new HOMA]
    }
    
    # connect agents to homa
    # making homa at each node aware of all its agents that connect to other nodes
    # R2P2 - must have connected agents before attaching them to r2p2
    foreach index [dict keys $agent_host_host] {
        set from_to [split $index "_"]
        set from [lindex $from_to 0]
        set to [lindex $from_to 1]
        $rdTransportLayer($from) attach-agent [dict get $agent_host_host "${from}_${to}"]
        # puts "Attaching agent ($from -> $to) to HOMA layer of $from"
    }
}

# --------------------- APPLICATION --------------------
Generic_app set request_size_B_ $mean_req_size_B
Generic_app set response_size_B_ $mean_resp_size_B
Generic_app set request_interval_sec_ [expr $mean_per_client_req_interval_us / 1000.0 / 1000.0]
Generic_app set incast_interval_sec_ $mean_incast_interval_s
Generic_app set enable_incast_ $enable_incast
Generic_app set incast_size_ $incast_size
Generic_app set incast_request_size_ $incast_request_size_bytes
Generic_app set num_clients_ $num_client_apps
Generic_app set num_servers_ $num_server_apps

Generic_app set service_time_sec_ [expr $mean_service_time_us / 1000.0 / 1000.0]
if {$transport_protocol == "r2p2" || $transport_protocol == "homa"} {
    # Generic_app/R2P2_APP set n_ $global_n
    set app_type Generic_app/R2P2_APP
} elseif {$transport_protocol == "pfabric" || $transport_protocol == "dctcp"} {
    set app_type Generic_app/PFABRIC
} elseif {$transport_protocol == "xpass"} {
    set app_type Generic_app/PFABRICXPASS
}

# Set up client apps
for {set app 0} {$app < $num_client_apps} {incr app} {
    # puts "Setting up client $app"
    set host [lindex $client_apps $app]
    set clientApplication($app) [new $app_type]
    $clientApplication($app) set-resp-dstr $resp_proc_time_distr [expr $app + $app * 150 + 2]
    # set load pattern
    if {$load_pattern == "fixed"} {
        $clientApplication($app) set-load-pattern $load_pattern
    } elseif {$load_pattern == "step"} {
        $clientApplication($app) set-load-pattern $load_pattern "$lp_step_high_ratio $lp_period $lp_high_value_mul $lp_low_value_mul"
    } else {
        puts "Load pattern $load_pattern is not supported. Exiting"
        exit 1
    }

    # set request distribution
    if { $req_interval_distr == "manual"} {
        $clientApplication($app) set-req-dstr $req_interval_distr $manual_req_interval_file $app
    } else {
        # exponential, fixed, manual. second param is seed.
        $clientApplication($app) set-req-dstr $req_interval_distr [expr $app + $app * 133 + 1]
    }
    if { $req_size_distr == "lognormal" } {
        $clientApplication($app) set-req-sz-dstr $req_size_distr $lognormal_sigma [expr $app + $app * 133 + 1]
    } elseif {$req_size_distr == "manual" } {
        $clientApplication($app) set-req-sz-dstr $req_size_distr $manual_req_interval_file $app
    } else {
        $clientApplication($app) set-req-sz-dstr $req_size_distr [expr $app + $app * 133 + 1]
    }
    # This is also assumed by r2p2-app. Fix (decouple)
    $clientApplication($app) set thread_id_ 100
    # puts "Client app $app runs on host $host with thread id 1"
    if {$transport_protocol == "r2p2" || $transport_protocol == "homa"} {
        # The thread Id MUST be provided before the r2p2 layer is attached
        # also, the cc module must be attached to the rdTransportLayer too. (bad, fix)
        $clientApplication($app) attach-r2p2-layer $rdTransportLayer($host)
    }
}


# Trace messages (specify file). Tracer is static (for now) - so one call is enough
if {$capture_msg_trace != 0} {
    $clientApplication(0) set-msg-trace-file $results_path
}

# Set up server apps
for {set app 0} {$app < $num_server_apps} {incr app} {
    set host [lindex $server_apps $app]
    set serverApplication($app) [new $app_type]
    # second param is seed
    $serverApplication($app) set-resp-dstr $resp_proc_time_distr [expr $app + $app * 150 + 2]
    if { $resp_size_distr == "lognormal" } {
        $serverApplication($app) set-resp-sz-dstr $resp_size_distr $lognormal_sigma [expr $app + $app * 150 + 2]
    } else {
        $serverApplication($app) set-resp-sz-dstr $resp_size_distr [expr $app + $app * 150 + 2]
    }
    # Only one server thread per host with thread id 0. The router selects threads not hosts, so I give attach-server-agent 1 thread per host. 
    $serverApplication($app) set thread_id_ 0
    # puts "Sever app $app runs on host $host with thread id 0"
    # puts "Server app $app runs on host $host with thread id 0"
    if {$transport_protocol == "r2p2" || $transport_protocol == "homa"} {
        # The thread Id MUST be provided before the r2p2 layer is attached
        # also, the cc module must be attached to the rdTransportLayer too. (bad, fix)
        $serverApplication($app) attach-r2p2-layer $rdTransportLayer($host)
    }
}

if {$transport_protocol == "pfabric"} {
    set agent_type Agent/TCP/FullTcp/Sack/MinTCP
} elseif {$transport_protocol == "dctcp"} {
    set agent_type Agent/TCP/FullTcp
} elseif {$transport_protocol == "xpass"} {
    set agent_type Agent/XPass
}

# Create pfabric agents
set fid 0
if {$transport_protocol == "pfabric" || $transport_protocol == "dctcp" || $transport_protocol == "xpass"} {
    # For each client app, create a source agent(s) & attach
    # For each server app create a dst agent(s) & attach
    # Set same fid on both
    # Connect them
    # attach to application
    # Set num workers on each app

    # set new_agent_attach 0
    # set connect_agent 0
    # set app_attach 0
    for {set j 0} {$j < $num_client_apps} {incr j} {
        set client_host [lindex $client_apps $j] 
        set num_workers 0
        for {set i 0} {$i < $num_server_apps} {incr i} {
            set server_host [lindex $server_apps $i] 
            if {$client_host != $server_host} {
                incr num_workers
                # puts "Creating TCP connections between hosts $client_host and $server_host"
                for {set c 0} {$c < $tcp_connections_per_thread_pair} {incr c} {
                    # # ---------------------------------------------------------------------
                    # set start [clock clicks]
                    set agent_cl($j,$i,$c) [new $agent_type]
                    $agent_cl($j,$i,$c) set fid_ $fid
                    $ns attach-agent $host_node($client_host) $agent_cl($j,$i,$c)
                    set agent_sr($j,$i,$c) [new $agent_type]
                    $agent_sr($j,$i,$c) set fid_ $fid
                    $ns attach-agent $host_node($server_host) $agent_sr($j,$i,$c)
                    # set end [clock clicks]
                    # set new_agent_attach [expr $new_agent_attach + $end - $start]
                    # ---------------------------------------------------------------------
                    incr fid
                    if {$fid % 50000 == 0} {
                        puts "$fid out of [expr $num_hosts * $num_hosts * $tcp_connections_per_thread_pair]"
                    }
                    # ---------------------------------------------------------------------
                    # set start [clock clicks]
                    $ns connect $agent_cl($j,$i,$c) $agent_sr($j,$i,$c)
                    $agent_sr($j,$i,$c) listen
                    # set end [clock clicks]
                    # set connect_agent [expr $connect_agent + $end - $start]
                    # ---------------------------------------------------------------------
                    # set start [clock clicks]
                    $clientApplication($j) attach-agent $agent_cl($j,$i,$c) [$serverApplication($i) set thread_id_]
                    $serverApplication($i) attach-agent $agent_sr($j,$i,$c) [$clientApplication($j) set thread_id_]
                    # set end [clock clicks]
                    # set app_attach [expr $app_attach + $end - $start]
                }
            }
        }
        # puts "Number of servers for client $client_host: $num_workers"
        set-req-target-distr $j $client_host $num_workers
    }
    # puts "new_agent_attach $new_agent_attach || connect_agent $connect_agent || app_attach $app_attach"
}

# Inform r2p2 client apps about the number of workers each can access and give their addresses
if {$transport_protocol == "r2p2" || $transport_protocol == "homa"} {
    # For each client app, create a source agent(s) & attach
    # For each server app create a dst agent(s) & attach
    # Set same fid on both
    # Connect them
    # attach to application
    # Set num workers on each app
    for {set j 0} {$j < $num_client_apps} {incr j} {
        set client_host [lindex $client_apps $j] 
        set num_workers 0
        for {set i 0} {$i < $num_server_apps} {incr i} {
            set server_host [lindex $server_apps $i] 
            if {$client_host != $server_host} {
                incr num_workers
                set agent_cl [dict get $agent_host_host "${client_host}_${server_host}"]
                set agent_sr [dict get $agent_host_host "${server_host}_${client_host}"]
                # puts "Attaching agent of client $client_host that targets $server_host"
                $clientApplication($j) attach-agent $agent_cl 1
                $serverApplication($i) attach-agent $agent_sr 1
            }
        }
        set-req-target-distr $j $client_host $num_workers
    }
}

# --------------------- EVENTS ---------------------
# |warmup_at|---<do warmup>-------|stop_wrmp_at|--|start_at|----<run apps>----|start_at + simul_dur|
set warmup_at 0.1
set stop_wrmp_at 9.5
# before changing start_at, check delay.h, red.cc, and drop-tail.cc
# to avoid incast (multiple connections per thread)
set warmup_gap 0.05

# progress tracker
proc printProgress {now} {
    global ns simul_dur start_at after_dur transport_protocol approx_leaves_load approx_core_load \
              r2p2_cc_scheme start_tracing_at simul_termination simulation_name
    puts "$now/$simul_termination | $r2p2_cc_scheme $simulation_name -l: [expr {floor($approx_leaves_load)}]%-> simulation at\
             [expr {floor([expr $now - $start_at]/[expr $simul_dur + $after_dur] * 100)}]% - tracing starts at $start_tracing_at"
    set next_print [expr $now + [expr [expr $simul_dur + $after_dur]/10.0]]
    $ns at $next_print "printProgress $next_print"
}

if {$transport_protocol == "pfabric" || $transport_protocol == "dctcp"} {
    for {set i 0} {$i < $num_server_apps} {incr i} {
        $serverApplication($i) set warmup_phase_ 1
        $ns at $stop_wrmp_at "$serverApplication($i) stop-warmup"
    }
}

for {set j 0} {$j < $num_client_apps} {incr j} {
    # No need to warmup xpass
    if {$transport_protocol == "pfabric" || $transport_protocol == "dctcp"} {
        $clientApplication($j) set warmup_phase_ 1
        set next_warmup [expr $warmup_at + $j * $warmup_gap]
        # puts "Next warmup $next_warmup" 
        $ns at $next_warmup "$clientApplication($j) warmup"
        $ns at $stop_wrmp_at "$clientApplication($j) stop-warmup"
    }
    $ns at $start_at "$clientApplication($j) start"
    $ns at $stop_at "$clientApplication($j) stop"
    $ns at $simul_termination "$clientApplication($j) finish"
}

if {$transport_protocol == "pfabric" || $transport_protocol == "dctcp"} {
    puts "Last Warmup was scheduled at [expr $j * $warmup_gap + $warmup_at]"
}

$ns at $start_at "printProgress $start_at"

$ns at $start_tracing_at "start-simple-tracing"

# deprecated feature
set switch_subset_buf_mon_interval_s $state_polling_ival_s

if {$state_polling_ival_s != -1} {
    # This whole 2-stage start is done to save space.
    # The idea is to start q monitoring a while into the simulation.
    # The problem is that starting everything at that time will result in incorrect (and negative) queue lengths
    # As the queue lenth is calculated by the diff departures - arrivals
    
    # The idea here is that the monitoring mechanism is created at start_time so that
    # it keeps track of all packets but starts reporting later.
    $ns at $start_at "start_q_monitoring $switch_subset_buf_mon_interval_s 1" 
    $ns at $start_tracing_at "start_q_monitoring $switch_subset_buf_mon_interval_s 0" 
}

# TEMPORARY VARIABLE ASSIGNMENTS
set approx_core_load $approx_leaves_load


set parmtr_file [open "${results_path}/parameters" a+]
puts $parmtr_file "transport_protocol $transport_protocol\nsim_start $start_at\nsim_dur $simul_dur\
    \nnum_aggr $num_aggr\nnum_tors $num_tors\
    \nnum_hosts $num_hosts\nnum_client_apps $num_client_apps\nnum_server_apps $num_server_apps\
    \nleaf_link_speed_gbps $leaf_link_speed_gbps\ncore_link_latency_ms $core_link_latency_ms\
    \nleaf_link_latency_ms $leaf_link_latency_ms\
    \nmean_per_client_req_interval_us $mean_per_client_req_interval_us\nmean_service_time_us $mean_service_time_us\
    \nmean_req_size_B $mean_req_size_B\nmean_resp_size_B $mean_resp_size_B\nreq_interval_distr $req_interval_distr\
    \nresp_proc_time_distr $resp_proc_time_distr\nreq_size_distr $req_size_distr\nresp_size_distr $resp_size_distr\
    \nqueue_size $queue_size\nr2p2_cc_scheme $r2p2_cc_scheme\ncc_pkt_cap_sr_thresh $cc_pkt_cap_sr_thresh\
    \nrouter_latency_us $router_latency_us\
    \ntcp_connections_per_thread_pair $tcp_connections_per_thread_pair\npfab_g $pfab_g\npfab_K $pfab_K\
    \npfab_min_rto $pfab_min_rto\
    \nper_server_capacity_rps $per_server_capacity_rps\ntotal_server_capacity_rps $total_server_capacity_rps\
    \nper_client_req_send_rate_rps $per_client_req_send_rate_rps\nper_server_resp_send_rate_rps $per_server_resp_send_rate_rps\
    \nglobal_req_send_rate_rps $global_req_send_rate_rps\nmean_per_client_req_interval_us $mean_per_client_req_interval_us\
    \nestim_send_rate_per_client_gbps_bgrnd $estim_send_rate_per_client_gbps_bgrnd\nestim_send_rate_per_server_gbps_bgrnd $estim_send_rate_per_server_gbps_bgrnd\
    \ntotal_cl_send_rate_gbps $total_cl_send_rate_gbps\ntotal_sr_send_rate_gbps $total_sr_send_rate_gbps\
    \napprox_app_load $approx_app_load\napprox_req_nwrk_load_leaves $approx_req_nwrk_load_leaves\
    \ntraffic_matrix_type $traffic_matrix_type\
    \ntraffic_matrix_ratio_interrack $traffic_matrix_ratio_interrack\
    \napprox_leaves_load $approx_leaves_load\
    \napprox_core_load $approx_core_load\
    \napprox_max_req_nwrk_load_core $approx_max_req_nwrk_load_core\
    \napprox_max_reply_nwrk_load_core $approx_max_reply_nwrk_load_core\
    \nlognormal_sigma $lognormal_sigma\
    \ncore_capacity_gbps $core_capacity_gbps\
    \ncore_link_speed_gbps $core_link_speed_gbps\
    \ntotal_client_downlink_cap_gbps $total_client_downlink_cap_gbps\
    \ntotal_server_downlink_cap_gbps $total_server_downlink_cap_gbps\
    \nrouter_op_mode $router_op_mode\nstate_polling_ival_s $state_polling_ival_s\
    \nswitch_subset_buf_mon_interval_s $switch_subset_buf_mon_interval_s\
    \ncapture_pkt_trace $capture_pkt_trace\ncapture_msg_trace $capture_msg_trace\
    \nstart_tracing_at $start_tracing_at\
    "
close $parmtr_file

$ns at $simul_termination "finish"
$ns run

} else {

########################################################################################################################
# Hack so that omnet runs can get access to the parmtr_file. TODO: do it properly.
set parmtr_file [open "${results_path}/parameters" w]
puts $parmtr_file "transport_protocol $transport_protocol\nsim_start $start_at\nsim_dur $simul_dur\
    \nnum_aggr $num_aggr\nnum_tors $num_tors\
    \nnum_hosts $num_hosts\nnum_client_apps $num_client_apps\nnum_server_apps $num_server_apps\
    \nleaf_link_speed_gbps $leaf_link_speed_gbps\ncore_link_latency_ms $core_link_latency_ms\
    \nleaf_link_latency_ms $leaf_link_latency_ms\
    \nmean_per_client_req_interval_us $mean_per_client_req_interval_us\nmean_service_time_us $mean_service_time_us\
    \nmean_req_size_B $mean_req_size_B\nmean_resp_size_B $mean_resp_size_B\nreq_interval_distr $req_interval_distr\
    \nresp_proc_time_distr $resp_proc_time_distr\nreq_size_distr $req_size_distr\nresp_size_distr $resp_size_distr\
    \nr2p2_cc_scheme $r2p2_cc_scheme\ncc_pkt_cap_sr_thresh $cc_pkt_cap_sr_thresh\
    \nrouter_latency_us $router_latency_us\
    \ntcp_connections_per_thread_pair $tcp_connections_per_thread_pair\npfab_g $pfab_g\npfab_K $pfab_K\
    \npfab_min_rto $pfab_min_rto\
    \nper_server_capacity_rps $per_server_capacity_rps\ntotal_server_capacity_rps $total_server_capacity_rps\
    \nper_client_req_send_rate_rps $per_client_req_send_rate_rps\nper_server_resp_send_rate_rps $per_server_resp_send_rate_rps\
    \nglobal_req_send_rate_rps $global_req_send_rate_rps\nmean_per_client_req_interval_us $mean_per_client_req_interval_us\
    \nestim_send_rate_per_client_gbps_bgrnd $estim_send_rate_per_client_gbps_bgrnd\nestim_send_rate_per_server_gbps_bgrnd $estim_send_rate_per_server_gbps_bgrnd\
    \ntotal_cl_send_rate_gbps $total_cl_send_rate_gbps\ntotal_sr_send_rate_gbps $total_sr_send_rate_gbps\
    \napprox_app_load $approx_app_load\napprox_req_nwrk_load_leaves $approx_req_nwrk_load_leaves\
    \ntraffic_matrix_type $traffic_matrix_type\
    \ntraffic_matrix_ratio_interrack $traffic_matrix_ratio_interrack\
    \napprox_leaves_load $approx_leaves_load\
    \napprox_max_req_nwrk_load_core $approx_max_req_nwrk_load_core\
    \napprox_max_reply_nwrk_load_core $approx_max_reply_nwrk_load_core\
    \nlognormal_sigma $lognormal_sigma\
    \ncore_capacity_gbps $core_capacity_gbps\
    \ncore_link_speed_gbps $core_link_speed_gbps\
    \ntotal_client_downlink_cap_gbps $total_client_downlink_cap_gbps\
    \ntotal_server_downlink_cap_gbps $total_server_downlink_cap_gbps\
    \nrouter_op_mode $router_op_mode\nstate_polling_ival_s $state_polling_ival_s\
    \ncapture_pkt_trace $capture_pkt_trace\ncapture_msg_trace $capture_msg_trace\
    \nstart_tracing_at $start_tracing_at\
    "
close $parmtr_file
}