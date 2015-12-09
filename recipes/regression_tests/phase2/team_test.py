from lnst.Controller.Task import ctl
from lnst.Controller.PerfRepoUtils import netperf_baseline_template
from lnst.Controller.PerfRepoUtils import netperf_result_template

from lnst.RecipeCommon.IRQ import pin_dev_irqs

# ------
# SETUP
# ------

mapping_file = ctl.get_alias("mapping_file")
perf_api = ctl.connect_PerfRepo(mapping_file)

product_name = ctl.get_alias("product_name")

m1 = ctl.get_host("testmachine1")
m2 = ctl.get_host("testmachine2")

m1.sync_resources(modules=["IcmpPing", "Icmp6Ping", "Netperf"])
m2.sync_resources(modules=["IcmpPing", "Icmp6Ping", "Netperf"])

# ------
# TESTS
# ------

offloads = ["gro", "gso", "tso", "tx"]
offload_settings = [ [("gro", "on"), ("gso", "on"), ("tso", "on"), ("tx", "on")],
                     [("gro", "off"), ("gso", "on"), ("tso", "on"), ("tx", "on")],
                     [("gro", "on"), ("gso", "off"),  ("tso", "off"), ("tx", "on")],
                     [("gro", "on"), ("gso", "on"), ("tso", "off"), ("tx", "off")]]

ipv = ctl.get_alias("ipv")
mtu = ctl.get_alias("mtu")
netperf_duration = int(ctl.get_alias("netperf_duration"))
nperf_reserve = int(ctl.get_alias("nperf_reserve"))
nperf_confidence = ctl.get_alias("nperf_confidence")
nperf_max_runs = int(ctl.get_alias("nperf_max_runs"))
nperf_cpupin = ctl.get_alias("nperf_cpupin")
nperf_cpu_util = ctl.get_alias("nperf_cpu_util")
nperf_mode = ctl.get_alias("nperf_mode")
nperf_num_parallel = int(ctl.get_alias("nperf_num_parallel"))

test_if1 = m1.get_interface("test_if")
test_if1.set_mtu(mtu)
test_if2 = m2.get_interface("test_if")
test_if2.set_mtu(mtu)

if nperf_cpupin:
    m1.run("service irqbalance stop")
    m2.run("service irqbalance stop")

    m1_phy1 = m1.get_interface("eth1")
    m1_phy2 = m1.get_interface("eth2")
    dev_list = [(m1, m1_phy1), (m1, m1_phy2)]

    if test_if2.get_type() == "team":
        m2_phy1 = m2.get_interface("eth1")
        m2_phy2 = m2.get_interface("eth2")
        dev_list.extend([(m2, m2_phy1), (m2, m2_phy2)])
    else:
        dev_list.append((m2, test_if2))

    # this will pin devices irqs to cpu #0
    for m, d in dev_list:
        pin_dev_irqs(m, d, 0)

ping_mod = ctl.get_module("IcmpPing",
                           options={
                               "addr" : test_if2.get_ip(0),
                               "count" : 100,
                               "iface" : test_if1.get_devname(),
                               "interval" : 0.1
                           })

ping_mod6 = ctl.get_module("Icmp6Ping",
                           options={
                               "addr" : test_if2.get_ip(1),
                               "count" : 100,
                               "iface" : test_if1.get_ip(1),
                               "interval" : 0.1
                           })

netperf_srv = ctl.get_module("Netperf",
                              options = {
                                  "role" : "server",
                                  "bind" : test_if1.get_ip(0)
                              })

netperf_srv6 = ctl.get_module("Netperf",
                              options = {
                                  "role" : "server",
                                  "bind" : test_if1.get_ip(1),
                                  "netperf_opts" : " -6"
                              })

p_opts = "-L %s" % (test_if2.get_ip(0))
if nperf_cpupin and nperf_mode != "multi":
    p_opts += " -T%s,%s" % (nperf_cpupin, nperf_cpupin)

netperf_cli_tcp = ctl.get_module("Netperf",
                                  options = {
                                      "role" : "client",
                                      "netperf_server" : test_if1.get_ip(0),
                                      "duration" : netperf_duration,
                                      "testname" : "TCP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs": nperf_max_runs,
                                      "netperf_opts" : p_opts
                                })

netperf_cli_udp = ctl.get_module("Netperf",
                                  options = {
                                      "role" : "client",
                                      "netperf_server" : test_if1.get_ip(0),
                                      "duration" : netperf_duration,
                                      "testname" : "UDP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs": nperf_max_runs,
                                      "netperf_opts" : p_opts
                                  })

netperf_cli_tcp6 = ctl.get_module("Netperf",
                                  options={
                                      "role" : "client",
                                      "netperf_server" :
                                          test_if1.get_ip(1),
                                      "duration" : netperf_duration,
                                      "testname" : "TCP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs": nperf_max_runs,
                                      "netperf_opts" :
                                          "-L %s -6" % (test_if2.get_ip(1))
                                  })
netperf_cli_udp6 = ctl.get_module("Netperf",
                                  options={
                                      "role" : "client",
                                      "netperf_server" :
                                          test_if1.get_ip(1),
                                      "duration" : netperf_duration,
                                      "testname" : "UDP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs": nperf_max_runs,
                                      "netperf_opts" :
                                          "-L %s -6" % (test_if2.get_ip(1))
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

ctl.wait(15)

for setting in offload_settings:
    dev_features = ""
    for offload in setting:
        dev_features += " %s %s" % (offload[0], offload[1])
    m1.run("ethtool -K %s %s" % (test_if1.get_devname(), dev_features))
    m2.run("ethtool -K %s %s" % (test_if2.get_devname(), dev_features))

    if ipv in [ 'ipv4', 'both' ]:
        m1.run(ping_mod)

        server_proc = m1.run(netperf_srv, bg=True)
        ctl.wait(2)

        # prepare PerfRepo result for tcp
        result_tcp = perf_api.new_result("tcp_ipv4_id",
                                         "tcp_ipv4_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_tcp.set_parameter(offload[0], offload[1])
        result_tcp.set_parameter('netperf_server', "testmachine1")
        result_tcp.set_parameter('netperf_client', "testmachine2")
        result_tcp.add_tag(product_name)
        if nperf_mode == "multi":
            result_tcp.add_tag("multithreaded")
            result_tcp.set_parameter('num_parallel', nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_tcp)
        netperf_baseline_template(netperf_cli_tcp, baseline)

        tcp_res_data = m2.run(netperf_cli_tcp,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_tcp, tcp_res_data)
        perf_api.save_result(result_tcp)

        # prepare PerfRepo result for udp
        result_udp = perf_api.new_result("udp_ipv4_id",
                                         "udp_ipv4_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_udp.set_parameter(offload[0], offload[1])
        result_udp.set_parameter('netperf_server', "testmachine1")
        result_udp.set_parameter('netperf_client', "testmachine2")
        result_udp.add_tag(product_name)
        if nperf_mode == "multi":
            result_udp.add_tag("multithreaded")
            result_udp.set_parameter('num_parallel', nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_udp)
        netperf_baseline_template(netperf_cli_udp, baseline)

        udp_res_data = m2.run(netperf_cli_udp,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_udp, udp_res_data)
        perf_api.save_result(result_udp)

        server_proc.intr()
    if ipv in [ 'ipv6', 'both' ]:
        m1.run(ping_mod6)

        server_proc = m1.run(netperf_srv6, bg=True)
        ctl.wait(2)

        # prepare PerfRepo result for tcp
        result_tcp = perf_api.new_result("tcp_ipv6_id",
                                         "tcp_ipv6_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_tcp.set_parameter(offload[0], offload[1])
        result_tcp.set_parameter('netperf_server', "testmachine1")
        result_tcp.set_parameter('netperf_client', "testmachine2")
        result_tcp.add_tag(product_name)
        if nperf_mode == "multi":
            result_tcp.add_tag("multithreaded")
            result_tcp.set_parameter('num_parallel', nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_tcp)
        netperf_baseline_template(netperf_cli_tcp6, baseline)

        tcp_res_data = m2.run(netperf_cli_tcp6,
                              timeout = (netperf_duration + nperf_reserve)*5)

        netperf_result_template(result_tcp, tcp_res_data)
        perf_api.save_result(result_tcp)

        # prepare PerfRepo result for udp
        result_udp = perf_api.new_result("udp_ipv4_id",
                                         "udp_ipv6_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_udp.set_parameter(offload[0], offload[1])
        result_udp.set_parameter('netperf_server', "testmachine1")
        result_udp.set_parameter('netperf_client', "testmachine2")
        result_udp.add_tag(product_name)
        if nperf_mode == "multi":
            result_udp.add_tag("multithreaded")
            result_udp.set_parameter('num_parallel', nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_udp)
        netperf_baseline_template(netperf_cli_udp6, baseline)

        udp_res_data = m2.run(netperf_cli_udp6,
                              timeout = (netperf_duration + nperf_reserve)*5)

        netperf_result_template(result_udp, udp_res_data)
        perf_api.save_result(result_udp)

        server_proc.intr()

#reset offload states
dev_features = ""
for offload in offloads:
    dev_features += " %s %s" % (offload, "on")
m1.run("ethtool -K %s %s" % (test_if1.get_devname(), dev_features))
m2.run("ethtool -K %s %s" % (test_if2.get_devname(), dev_features))

ping_mod.update_options({"addr" : test_if1.get_ip(0),
                          "iface" : test_if2.get_devname()})

ping_mod6.update_options({"addr" : test_if1.get_ip(1),
                          "iface" : test_if2.get_devname()})

netperf_srv.update_options({"bind" : test_if2.get_ip(0)})

netperf_srv6.update_options({"bind" : test_if2.get_ip(1)})

p_opts = "-L %s" % (test_if1.get_ip(0))
if nperf_cpupin and nperf_mode != "multi":
    p_opts += " -T%s,%s" % (nperf_cpupin, nperf_cpupin)

netperf_cli_tcp.update_options({"netperf_server" : test_if2.get_ip(0),
                                "netperf_opts" : p_opts})

netperf_cli_udp.update_options({"netperf_server" : test_if2.get_ip(0),
                                "netperf_opts" : p_opts})

netperf_cli_tcp6.update_options({"netperf_server" : test_if2.get_ip(1),
                                "netperf_opts" : "-L %s -6" % (test_if1.get_ip(1))})

netperf_cli_udp6.update_options({"netperf_server" : test_if2.get_ip(1),
                                 "netperf_opts" : "-L %s -6" % (test_if1.get_ip(1))})

for setting in offload_settings:
    dev_features = ""
    for offload in setting:
        dev_features += " %s %s" % (offload[0], offload[1])
    m1.run("ethtool -K %s %s" % (test_if1.get_devname(), dev_features))
    m2.run("ethtool -K %s %s" % (test_if2.get_devname(), dev_features))

    if ipv in [ 'ipv4', 'both' ]:
        m2.run(ping_mod)

        server_proc = m2.run(netperf_srv, bg=True)
        ctl.wait(2)

        # prepare PerfRepo result for tcp
        result_tcp = perf_api.new_result("tcp_ipv4_id",
                                         "tcp_ipv4_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_tcp.set_parameter(offload[0], offload[1])
        result_tcp.set_parameter('netperf_server', "testmachine2")
        result_tcp.set_parameter('netperf_client', "testmachine1")
        result_tcp.add_tag(product_name)
        if nperf_mode == "multi":
            result_tcp.add_tag("multithreaded")
            result_tcp.set_parameter('num_parallel', nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_tcp)
        netperf_baseline_template(netperf_cli_tcp, baseline)

        tcp_res_data = m1.run(netperf_cli_tcp,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_tcp, tcp_res_data)
        perf_api.save_result(result_tcp)

        # prepare PerfRepo result for udp
        result_udp = perf_api.new_result("udp_ipv4_id",
                                         "udp_ipv4_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_udp.set_parameter(offload[0], offload[1])
        result_udp.set_parameter('netperf_server', "testmachine2")
        result_udp.set_parameter('netperf_client', "testmachine1")
        result_udp.add_tag(product_name)
        if nperf_mode == "multi":
            result_udp.add_tag("multithreaded")
            result_udp.set_parameter('num_parallel', nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_udp)
        netperf_baseline_template(netperf_cli_udp, baseline)

        udp_res_data = m1.run(netperf_cli_udp,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_udp, udp_res_data)
        perf_api.save_result(result_udp)

        server_proc.intr()
    if ipv in [ 'ipv6', 'both' ]:
        m2.run(ping_mod6)

        server_proc = m2.run(netperf_srv6, bg=True)
        ctl.wait(2)

        # prepare PerfRepo result for tcp
        result_tcp = perf_api.new_result("tcp_ipv6_id",
                                         "tcp_ipv6_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_tcp.set_parameter(offload[0], offload[1])
        result_tcp.set_parameter('netperf_server', "testmachine2")
        result_tcp.set_parameter('netperf_client', "testmachine1")
        result_tcp.add_tag(product_name)
        if nperf_mode == "multi":
            result_tcp.add_tag("multithreaded")
            result_tcp.set_parameter('num_parallel', nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_tcp)
        netperf_baseline_template(netperf_cli_tcp6, baseline)

        tcp_res_data = m1.run(netperf_cli_tcp6,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_tcp, tcp_res_data)
        perf_api.save_result(result_tcp)

        # prepare PerfRepo result for udp
        result_udp = perf_api.new_result("udp_ipv4_id",
                                         "udp_ipv6_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_udp.set_parameter(offload[0], offload[1])
        result_udp.set_parameter('netperf_server', "testmachine2")
        result_udp.set_parameter('netperf_client', "testmachine1")
        result_udp.add_tag(product_name)
        if nperf_mode == "multi":
            result_udp.add_tag("multithreaded")
            result_udp.set_parameter('num_parallel', nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_udp)
        netperf_baseline_template(netperf_cli_udp6, baseline)

        udp_res_data = m1.run(netperf_cli_udp6,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_udp, udp_res_data)
        perf_api.save_result(result_udp)

        server_proc.intr()

#reset offload states
dev_features = ""
for offload in offloads:
    dev_features += " %s %s" % (offload, "on")
m1.run("ethtool -K %s %s" % (test_if1.get_devname(), dev_features))
m2.run("ethtool -K %s %s" % (test_if2.get_devname(), dev_features))

if nperf_cpupin:
    m1.run("service irqbalance start")
    m2.run("service irqbalance start")
