from lnst.Controller.Task import ctl
from lnst.Controller.PerfRepoUtils import netperf_baseline_template
from lnst.Controller.PerfRepoUtils import netperf_result_template

from lnst.RecipeCommon.IRQ import pin_dev_irqs
from lnst.RecipeCommon.PerfRepo import generate_perfrepo_comment

# ------
# SETUP
# ------

mapping_file = ctl.get_alias("mapping_file")
perf_api = ctl.connect_PerfRepo(mapping_file)

product_name = ctl.get_alias("product_name")

m1 = ctl.get_host("machine1")
m2 = ctl.get_host("machine2")

m1.sync_resources(modules=["Netperf"])
m2.sync_resources(modules=["Netperf"])

# ------
# TESTS
# ------

offloads = ["gro", "gso", "tso", "tx"]
offload_settings = [ [("gro", "on"), ("gso", "on"), ("tso", "on"), ("tx", "on"), ("rx", "on")],
                     [("gro", "off"), ("gso", "on"), ("tso", "on"), ("tx", "on"), ("rx", "on")],
                     [("gro", "on"), ("gso", "off"),  ("tso", "off"), ("tx", "on"), ("rx", "on")],
                     [("gro", "on"), ("gso", "on"), ("tso", "off"), ("tx", "off"), ("rx", "on")],
                     [("gro", "on"), ("gso", "on"), ("tso", "on"), ("tx", "on"), ("rx", "off")]]

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
pr_user_comment = ctl.get_alias("perfrepo_comment")

pr_comment = generate_perfrepo_comment([m1, m2], pr_user_comment)

m1_testiface = m1.get_interface("testiface")
m2_testiface = m2.get_interface("testiface")

m1_testiface.set_mtu(mtu)
m2_testiface.set_mtu(mtu)

if nperf_cpupin:
    m1.run("service irqbalance stop")
    m2.run("service irqbalance stop")

    for m, d in [ (m1, m1_testiface), (m2, m2_testiface) ]:
        pin_dev_irqs(m, d, 0)

p_opts = "-L %s" % (m2_testiface.get_ip(0))
if nperf_cpupin and nperf_mode != "multi":
    p_opts += " -T%s,%s" % (nperf_cpupin, nperf_cpupin)

p_opts6 = "-L %s -6" % (m2_testiface.get_ip(1))
if nperf_cpupin and nperf_mode != "multi":
    p_opts6 += " -T%s,%s" % (nperf_cpupin, nperf_cpupin)

netperf_cli_tcp = ctl.get_module("Netperf",
                                  options={
                                      "role" : "client",
                                      "netperf_server" : m1_testiface.get_ip(0),
                                      "duration" : netperf_duration,
                                      "testname" : "TCP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs" : nperf_max_runs,
                                      "netperf_opts" : p_opts
                                  })

netperf_cli_tcp6 = ctl.get_module("Netperf",
                                  options={
                                      "role" : "client",
                                      "netperf_server" : m1_testiface.get_ip(1),
                                      "duration" : netperf_duration,
                                      "testname" : "TCP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs" : nperf_max_runs,
                                      "netperf_opts" : p_opts6
                                  })

netperf_cli_udp = ctl.get_module("Netperf",
                                  options={
                                      "role" : "client",
                                      "netperf_server" : m1_testiface.get_ip(0),
                                      "duration" : netperf_duration,
                                      "testname" : "UDP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs" : nperf_max_runs,
                                      "netperf_opts" : p_opts
                                  })

netperf_cli_udp6 = ctl.get_module("Netperf",
                                  options={
                                      "role" : "client",
                                      "netperf_server" : m1_testiface.get_ip(1),
                                      "duration" : netperf_duration,
                                      "testname" : "UDP_STREAM",
                                      "confidence" : nperf_confidence,
                                      "cpu_util" : nperf_cpu_util,
                                      "runs" : nperf_max_runs,
                                      "netperf_opts" : p_opts6
                                  })

netperf_srv = ctl.get_module("Netperf",
                              options={
                                  "role" : "server",
                                  "bind" : m1_testiface.get_ip(0)
                                  })

netperf_srv6 = ctl.get_module("Netperf",
                              options={
                                  "role" : "server",
                                  "bind" : m1_testiface.get_ip(1)
                                  })

if nperf_mode == "multi":
    netperf_cli_tcp.unset_option("confidence")
    netperf_cli_udp.unset_option("confidence")
    netperf_cli_tcp6.unset_option("confidence")
    netperf_cli_udp6.unset_option("confidence")

    netperf_cli_tcp.update_options({"num_parallel" : nperf_num_parallel})
    netperf_cli_udp.update_options({"num_parallel" : nperf_num_parallel})
    netperf_cli_tcp6.update_options({"num_parallel" : nperf_num_parallel})
    netperf_cli_udp6.update_options({"num_parallel" : nperf_num_parallel})

ctl.wait(15)

for setting in offload_settings:
    dev_features = ""
    for offload in setting:
        dev_features += " %s %s" % (offload[0], offload[1])
    m1.run("ethtool -K %s %s" % (m1_testiface.get_devname(), dev_features))
    m2.run("ethtool -K %s %s" % (m2_testiface.get_devname(), dev_features))

    if ("rx", "off") in setting:
        # when rx offload is turned off some of the cards might get reset
        # and link goes down, so wait a few seconds until NIC is ready
        ctl.wait(15)

    # Netperf test
    if ipv in [ 'ipv4', 'both' ]:
        srv_proc = m1.run(netperf_srv, bg=True)
        ctl.wait(2)

        # prepare PerfRepo result for tcp
        result_tcp = perf_api.new_result("tcp_ipv4_id",
                                         "tcp_ipv4_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_tcp.set_parameter(offload[0], offload[1])

        result_tcp.add_tag(product_name)
        if nperf_mode == "multi":
            result_tcp.add_tag("multithreaded")
            result_tcp.set_parameter("num_parallel", nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_tcp)
        netperf_baseline_template(netperf_cli_tcp, baseline)
        tcp_res_data = m2.run(netperf_cli_tcp,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_tcp, tcp_res_data)
        result_tcp.set_comment(pr_comment)
        perf_api.save_result(result_tcp)

        # prepare PerfRepo result for udp
        result_udp = perf_api.new_result("udp_ipv4_id",
                                         "udp_ipv4_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_udp.set_parameter(offload[0], offload[1])

        result_udp.add_tag(product_name)
        if nperf_mode == "multi":
            result_udp.add_tag("multithreaded")
            result_udp.set_parameter("num_parallel", nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_udp)
        netperf_baseline_template(netperf_cli_udp, baseline)
        udp_res_data = m2.run(netperf_cli_udp,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_udp, udp_res_data)
        result_udp.set_comment(pr_comment)
        perf_api.save_result(result_udp)
        srv_proc.intr()

    if ipv in [ 'ipv6', 'both' ]:
        srv_proc = m1.run(netperf_srv6, bg=True)
        ctl.wait(2)

        # prepare PerfRepo result for tcp ipv6
        result_tcp = perf_api.new_result("tcp_ipv6_id",
                                         "tcp_ipv6_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_tcp.set_parameter(offload[0], offload[1])

        result_tcp.add_tag(product_name)
        if nperf_mode == "multi":
            result_tcp.add_tag("multithreaded")
            result_tcp.set_parameter("num_parallel", nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_tcp)
        netperf_baseline_template(netperf_cli_tcp6, baseline)
        tcp_res_data = m2.run(netperf_cli_tcp6,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_tcp, tcp_res_data)
        result_tcp.set_comment(pr_comment)
        perf_api.save_result(result_tcp)

        # prepare PerfRepo result for udp ipv6
        result_udp = perf_api.new_result("udp_ipv6_id",
                                         "udp_ipv6_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
        for offload in setting:
            result_udp.set_parameter(offload[0], offload[1])

        result_udp.add_tag(product_name)
        if nperf_mode == "multi":
            result_udp.add_tag("multithreaded")
            result_udp.set_parameter("num_parallel", nperf_num_parallel)

        baseline = perf_api.get_baseline_of_result(result_udp)
        netperf_baseline_template(netperf_cli_udp6, baseline)
        udp_res_data = m2.run(netperf_cli_udp6,
                              timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

        netperf_result_template(result_udp, udp_res_data)
        result_udp.set_comment(pr_comment)
        perf_api.save_result(result_udp)
        srv_proc.intr()

# reset offload states
dev_features = ""
for offload in offloads:
    dev_features += " %s %s" % (offload, "on")

m1.run("ethtool -K %s %s" % (m1_testiface.get_devname(), dev_features))
m2.run("ethtool -K %s %s" % (m2_testiface.get_devname(), dev_features))

if nperf_cpupin:
    m1.run("service irqbalance start")
    m2.run("service irqbalance start")
