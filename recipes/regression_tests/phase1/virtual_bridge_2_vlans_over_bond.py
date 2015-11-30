import logging
from lnst.Controller.Task import ctl
from lnst.Controller.PerfRepoUtils import netperf_baseline_template
from lnst.Controller.PerfRepoUtils import netperf_result_template

# ------
# SETUP
# ------

mapping_file = ctl.get_alias("mapping_file")
perf_api = ctl.connect_PerfRepo(mapping_file)

product_name = ctl.get_alias("product_name")

# Host 1 + guests 1 and 2
h1 = ctl.get_host("host1")
g1 = ctl.get_host("guest1")
g1.sync_resources(modules=["IcmpPing", "Icmp6Ping", "Netperf"])
g2 = ctl.get_host("guest2")
g2.sync_resources(modules=["IcmpPing", "Icmp6Ping", "Netperf"])

# Host 2 + guests 3 and 4
h2 = ctl.get_host("host2")
g3 = ctl.get_host("guest3")
g3.sync_resources(modules=["IcmpPing", "Icmp6Ping", "Netperf"])
g4 = ctl.get_host("guest4")
g4.sync_resources(modules=["IcmpPing", "Icmp6Ping", "Netperf"])

# ------
# TESTS
# ------

offloads = ["gro", "gso", "tso", "tx"]
offload_settings = [ [("gro", "on"), ("gso", "on"), ("tso", "on"), ("tx", "on")],
                     [("gro", "off"), ("gso", "on"), ("tso", "on"), ("tx", "on")],
                     [("gro", "on"), ("gso", "off"),  ("tso", "off"), ("tx", "on")],
                     [("gro", "on"), ("gso", "on"), ("tso", "off"), ("tx", "off")]]

ipv = ctl.get_alias("ipv")
netperf_duration = int(ctl.get_alias("netperf_duration"))
nperf_reserve = int(ctl.get_alias("nperf_reserve"))
nperf_confidence = ctl.get_alias("nperf_confidence")
nperf_max_runs = int(ctl.get_alias("nperf_max_runs"))
nperf_cpu_util = ctl.get_alias("nperf_cpu_util")
nperf_mode = ctl.get_alias("nperf_mode")
nperf_num_parallel = int(ctl.get_alias("nperf_num_parallel"))
nperf_loc_cpu = ctl.get_alias("loc_cpu")
nperf_rem_cpu = ctl.get_alias("rem_cpu")

mtu = ctl.get_alias("mtu")
enable_udp_perf = ctl.get_alias("enable_udp_perf")

h1_nic1 = h1.get_interface("nic1")
h1_nic2 = h1.get_interface("nic2")
h2_nic1 = h2.get_interface("nic1")
h2_nic2 = h2.get_interface("nic2")
g1_guestnic = g1.get_interface("guestnic")
g2_guestnic = g2.get_interface("guestnic")
g3_guestnic = g3.get_interface("guestnic")
g4_guestnic = g4.get_interface("guestnic")

ping_mod = ctl.get_module("IcmpPing",
                           options={
                               "addr" : g3_guestnic.get_ip(0),
                               "count" : 100,
                               "iface" : g1_guestnic.get_devname(),
                               "interval" : 0.1
                           })
ping_mod2 = ctl.get_module("IcmpPing",
                           options={
                               "addr" : g2_guestnic.get_ip(0),
                               "count" : 100,
                               "iface" : g4_guestnic.get_devname(),
                               "interval" : 0.1
                           })

ping_mod6 = ctl.get_module("Icmp6Ping",
                           options={
                               "addr" : g3_guestnic.get_ip(1),
                               "count" : 100,
                               "iface" : g1_guestnic.get_devname(),
                               "interval" : 0.1
                           })

ping_mod62 = ctl.get_module("Icmp6Ping",
                           options={
                               "addr" : g2_guestnic.get_ip(1),
                               "count" : 100,
                               "iface" : g4_guestnic.get_devname(),
                               "interval" : 0.1
                           })

netperf_srv = ctl.get_module("Netperf",
                              options={
                                  "role": "server",
                                  "bind" : g1_guestnic.get_ip(0)
                              })

netperf_srv6 = ctl.get_module("Netperf",
                              options={
                                  "role" : "server",
                                  "bind" : g1_guestnic.get_ip(1),
                                  "netperf_opts" : " -6",
                              })

netperf_cli_tcp = ctl.get_module("Netperf",
                                  options={
                                      "role" : "client",
                                      "netperf_server" : g1_guestnic.get_ip(0),
                                      "duration" : netperf_duration,
                                      "testname" : "TCP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "loc_cpu" : nperf_loc_cpu,
                                      "rem_cpu" : nperf_rem_cpu,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs": nperf_max_runs,
                                      "netperf_opts" : "-L %s" %
                                                          (g3_guestnic.get_ip(0))
                                  })

netperf_cli_udp = ctl.get_module("Netperf",
                                  options={
                                      "role" : "client",
                                      "netperf_server" : g1_guestnic.get_ip(0),
                                      "duration" : netperf_duration,
                                      "testname" : "UDP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "loc_cpu" : nperf_loc_cpu,
                                      "rem_cpu" : nperf_rem_cpu,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs": nperf_max_runs,
                                      "netperf_opts" : "-L %s" %
                                                          (g3_guestnic.get_ip(0))
                                  })

netperf_cli_tcp6 = ctl.get_module("Netperf",
                                  options={
                                      "role" : "client",
                                      "netperf_server" :
                                          g1_guestnic.get_ip(1),
                                      "duration" : netperf_duration,
                                      "testname" : "TCP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "loc_cpu" : nperf_loc_cpu,
                                      "rem_cpu" : nperf_rem_cpu,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs": nperf_max_runs,
                                      "netperf_opts" :
                                          "-L %s -6" % (g3_guestnic.get_ip(1))
                                  })

netperf_cli_udp6 = ctl.get_module("Netperf",
                                  options={
                                      "role" : "client",
                                      "netperf_server" :
                                          g1_guestnic.get_ip(1),
                                      "duration" : netperf_duration,
                                      "testname" : "UDP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "loc_cpu" : nperf_loc_cpu,
                                      "rem_cpu" : nperf_rem_cpu,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs": nperf_max_runs,
                                      "netperf_opts" :
                                          "-L %s -6" % (g3_guestnic.get_ip(1))
                                  })

if nperf_mode == "multi":
    netperf_cli_tcp.unset_option("confidence")
    netperf_cli_udp.unset_option("confidence")
    netperf_cli_tcp6.unset_option("confidence")
    netperf_cli_udp6.unset_option("confidence")

    netperf_cli_tcp.update_options({"num_parallel": nperf_num_parallel})
    netperf_cli_udp.update_options({"num_parallel": nperf_num_parallel})
    netperf_cli_tcp6.update_options({"num_parallel": nperf_num_parallel})
    netperf_cli_udp6.update_options({"num_parallel": nperf_num_parallel})

ping_mod_bad = ctl.get_module("IcmpPing",
                               options={
                                   "addr" : g4_guestnic.get_ip(0),
                                   "count" : 100,
                                   "iface" : g1_guestnic.get_devname(),
                                   "interval" : 0.1
                               })

ping_mod_bad2 = ctl.get_module("IcmpPing",
                               options={
                                   "addr" : g2_guestnic.get_ip(0),
                                   "count" : 100,
                                   "iface" : g3_guestnic.get_devname(),
                                   "interval" : 0.1
                               })

ping_mod6_bad = ctl.get_module("Icmp6Ping",
                           options={
                               "addr" : g4_guestnic.get_ip(1),
                               "count" : 100,
                               "iface" : g1_guestnic.get_devname(),
                               "interval" : 0.1
                           })

ping_mod6_bad2 = ctl.get_module("Icmp6Ping",
                           options={
                               "addr" : g2_guestnic.get_ip(1),
                               "count" : 100,
                               "iface" : g3_guestnic.get_devname(),
                               "interval" : 0.1
                           })

# configure mtu
h1.get_interface("bond").set_mtu(mtu)
h1.get_interface("tap1").set_mtu(mtu)
h1.get_interface("tap2").set_mtu(mtu)
h1.get_interface("vlan10").set_mtu(mtu)
h1.get_interface("vlan20").set_mtu(mtu)
h1.get_interface("br1").set_mtu(mtu)
h1.get_interface("br2").set_mtu(mtu)

h2.get_interface("bond").set_mtu(mtu)
h2.get_interface("tap1").set_mtu(mtu)
h2.get_interface("tap2").set_mtu(mtu)
h2.get_interface("vlan10").set_mtu(mtu)
h2.get_interface("vlan20").set_mtu(mtu)
h2.get_interface("br1").set_mtu(mtu)
h2.get_interface("br2").set_mtu(mtu)

g1.get_interface("guestnic").set_mtu(mtu)
g2.get_interface("guestnic").set_mtu(mtu)
g3.get_interface("guestnic").set_mtu(mtu)
g4.get_interface("guestnic").set_mtu(mtu)

ctl.wait(15)

for setting in offload_settings:
    dev_features = ""
    for offload in setting:
        dev_features += " %s %s" % (offload[0], offload[1])
    h1.run("ethtool -K %s %s" % (h1_nic1.get_devname(), dev_features))
    h1.run("ethtool -K %s %s" % (h1_nic2.get_devname(), dev_features))
    h2.run("ethtool -K %s %s" % (h2_nic1.get_devname(), dev_features))
    h2.run("ethtool -K %s %s" % (h2_nic2.get_devname(), dev_features))
    g1.run("ethtool -K %s %s" % (g1_guestnic.get_devname(), dev_features))
    g2.run("ethtool -K %s %s" % (g2_guestnic.get_devname(), dev_features))
    g3.run("ethtool -K %s %s" % (g3_guestnic.get_devname(), dev_features))
    g4.run("ethtool -K %s %s" % (g4_guestnic.get_devname(), dev_features))

    if ipv in [ 'ipv4', 'both' ]:
        g1.run(ping_mod)
        g4.run(ping_mod2)
        g1.run(ping_mod_bad, expect="fail")
        g3.run(ping_mod_bad2, expect="fail")

        server_proc = g1.run(netperf_srv, bg=True)
        ctl.wait(2)

        # prepare PerfRepo result for tcp
        result_tcp = perf_api.new_result("tcp_ipv4_id",
                                         "tcp_ipv4_result",
                                         hash_ignore=['kernel_release',
                                             'redhat_release',
                                             r'guest\d+\.hostname',
                                             r'guest\d+\..*hwaddr',
                                             r'host\d+\..*tap\d*\.hwaddr',
                                             r'host\d+\..*tap\d*\.devname'])
        for offload in setting:
            result_tcp.set_parameter(offload[0], offload[1])
        result_tcp.add_tag(product_name)
        if nperf_mode == "multi":
            result_tcp.add_tag("multithreaded")
            result_tcp.set_parameter('num_parallel', nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_tcp)
        netperf_baseline_template(netperf_cli_tcp, baseline)

        tcp_res_data = g3.run(netperf_cli_tcp,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_tcp, tcp_res_data)
        perf_api.save_result(result_tcp)

        if enable_udp_perf is not None:
            # prepare PerfRepo result for udp
            result_udp = perf_api.new_result("udp_ipv4_id",
                                             "udp_ipv4_result",
                                             hash_ignore=['kernel_release',
                                                 'redhat_release',
                                                 r'guest\d+\.hostname',
                                                 r'guest\d+\..*hwaddr',
                                                 r'host\d+\..*tap\d*\.hwaddr',
                                                 r'host\d+\..*tap\d*\.devname'])
            for offload in setting:
                result_udp.set_parameter(offload[0], offload[1])
            result_udp.add_tag(product_name)
            if nperf_mode == "multi":
                result_udp.add_tag("multithreaded")
                result_udp.set_parameter('num_parallel', nperf_num_parallel)

            baseline = perf_api.get_baseline_of_result(result_udp)
            netperf_baseline_template(netperf_cli_udp, baseline)

            udp_res_data = g3.run(netperf_cli_udp,
                                  timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

            netperf_result_template(result_udp, udp_res_data)
            perf_api.save_result(result_udp)

        server_proc.intr()

    if ipv in [ 'ipv6', 'both' ]:
        g1.run(ping_mod6)
        g4.run(ping_mod62)
        g1.run(ping_mod6_bad, expect="fail")
        g3.run(ping_mod6_bad2, expect="fail")

        server_proc = g1.run(netperf_srv6, bg=True)
        ctl.wait(2)

        # prepare PerfRepo result for tcp ipv6
        result_tcp = perf_api.new_result("tcp_ipv6_id",
                                         "tcp_ipv6_result",
                                         hash_ignore=['kernel_release',
                                             'redhat_release',
                                             r'guest\d+\.hostname',
                                             r'guest\d+\..*hwaddr',
                                             r'host\d+\..*tap\d*\.hwaddr',
                                             r'host\d+\..*tap\d*\.devname'])
        for offload in setting:
            result_tcp.set_parameter(offload[0], offload[1])
        result_tcp.add_tag(product_name)
        if nperf_mode == "multi":
            result_tcp.add_tag("multithreaded")
            result_tcp.set_parameter('num_parallel', nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_tcp)
        netperf_baseline_template(netperf_cli_tcp6, baseline)

        tcp_res_data = g3.run(netperf_cli_tcp6,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_tcp, tcp_res_data)
        perf_api.save_result(result_tcp)

        # prepare PerfRepo result for udp ipv6
        if enable_udp_perf is not None:
            result_udp = perf_api.new_result("udp_ipv6_id",
                                             "udp_ipv6_result",
                                             hash_ignore=['kernel_release',
                                                 'redhat_release',
                                                 r'guest\d+\.hostname',
                                                 r'guest\d+\..*hwaddr',
                                                 r'host\d+\..*tap\d*\.hwaddr',
                                                 r'host\d+\..*tap\d*\.devname'])
            for offload in setting:
                result_udp.set_parameter(offload[0], offload[1])
            result_udp.add_tag(product_name)
            if nperf_mode == "multi":
                result_udp.add_tag("multithreaded")
                result_udp.set_parameter('num_parallel', nperf_num_parallel)

            baseline = perf_api.get_baseline_of_result(result_udp)
            netperf_baseline_template(netperf_cli_udp6, baseline)

            udp_res_data = g3.run(netperf_cli_udp6,
                                  timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

            netperf_result_template(result_udp, udp_res_data)
            perf_api.save_result(result_udp)

        server_proc.intr()

#reset offload states
dev_features = ""
for offload in offloads:
    dev_features = " %s %s" % (offload, "on")
h1.run("ethtool -K %s %s" % (h1_nic1.get_devname(), dev_features))
h1.run("ethtool -K %s %s" % (h1_nic2.get_devname(), dev_features))
h2.run("ethtool -K %s %s" % (h2_nic1.get_devname(), dev_features))
h2.run("ethtool -K %s %s" % (h2_nic2.get_devname(), dev_features))
g1.run("ethtool -K %s %s" % (g1_guestnic.get_devname(), dev_features))
g2.run("ethtool -K %s %s" % (g2_guestnic.get_devname(), dev_features))
g3.run("ethtool -K %s %s" % (g3_guestnic.get_devname(), dev_features))
g4.run("ethtool -K %s %s" % (g4_guestnic.get_devname(), dev_features))
