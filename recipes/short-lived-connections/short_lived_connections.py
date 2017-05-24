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

mtu = ctl.get_alias("mtu")
netperf_duration = int(ctl.get_alias("netperf_duration"))
nperf_reserve = int(ctl.get_alias("nperf_reserve"))
nperf_confidence = ctl.get_alias("nperf_confidence")
nperf_max_runs = int(ctl.get_alias("nperf_max_runs"))
nperf_cpupin = ctl.get_alias("nperf_cpupin")
nperf_cpu_util = ctl.get_alias("nperf_cpu_util")
nperf_mode = ctl.get_alias("nperf_mode")
nperf_num_parallel = int(ctl.get_alias("nperf_num_parallel"))
nperf_debug = ctl.get_alias("nperf_debug")
nperf_max_dev = ctl.get_alias("nperf_max_dev")
pr_user_comment = ctl.get_alias("perfrepo_comment")

m1_testiface = m1.get_interface("testiface")
m2_testiface = m2.get_interface("testiface")

m1_testiface.set_mtu(mtu)
m2_testiface.set_mtu(mtu)

pr_comment = generate_perfrepo_comment([m1, m2], pr_user_comment)

if nperf_cpupin:
    m1.run("service irqbalance stop")
    m2.run("service irqbalance stop")

    for m, d in [ (m1, m1_testiface), (m2, m2_testiface) ]:
        pin_dev_irqs(m, d, 0)

p_opts = "-L %s" % (m2_testiface.get_ip(0))

if nperf_cpupin and nperf_mode != "multi":
    p_opts += " -T%s,%s" % (nperf_cpupin, nperf_cpupin)

for size in ["1K,1K", "5K,5K", "7K,7K", "10K,10K", "12K,12K"]:

    n_p_opts = p_opts

    netperf_cli_tcp_rr = ctl.get_module("Netperf",
                                      options={
                                          "role" : "client",
                                          "netperf_server" : m1_testiface.get_ip(0),
                                          "duration" : netperf_duration,
                                          "testname" : "TCP_RR",
                                          "confidence" : nperf_confidence,
                                          "cpu_util" : nperf_cpu_util,
                                          "runs" : nperf_max_runs,
                                          "netperf_opts" : n_p_opts,
                                          "max_deviation" : nperf_max_dev,
                                          "debug" : nperf_debug,
                                          "testoptions" : "-r %s" % size
                                      })


    netperf_cli_tcp_crr = ctl.get_module("Netperf",
                                      options={
                                          "role" : "client",
                                          "netperf_server" : m1_testiface.get_ip(0),
                                          "duration" : netperf_duration,
                                          "testname" : "TCP_CRR",
                                          "confidence" : nperf_confidence,
                                          "cpu_util" : nperf_cpu_util,
                                          "runs" : nperf_max_runs,
                                          "netperf_opts" : n_p_opts,
                                          "max_deviation" : nperf_max_dev,
                                          "debug" : nperf_debug,
                                          "testoptions" : "-r %s" % size
                                      })


    netperf_srv = ctl.get_module("Netperf",
                                  options={
                                      "role" : "server",
                                      "bind" : m1_testiface.get_ip(0)
                                      })

    if nperf_mode == "multi":
        netperf_cli_tcp_rr.unset_option("confidence")
        netperf_cli_tcp_crr.unset_option("confidence")

        netperf_cli_tcp_rr.update_options({"num_parallel": nperf_num_parallel})
        netperf_cli_tcp_crr.update_options({"num_parallel": nperf_num_parallel})

        # we have to use multiqueue qdisc to get appropriate data
        m1.run("tc qdisc replace dev %s root mq" % m1_phy1.get_devname())
        m2.run("tc qdisc replace dev %s root mq" % m2_phy1.get_devname())

    ctl.wait(15)

    # Netperf test
    srv_proc = m1.run(netperf_srv, bg=True)
    ctl.wait(2)

    # prepare PerfRepo result for tcp_rr
    result_tcp_rr = perf_api.new_result("tcp_rr_id",
                                        "tcp_rr_result",
                                        hash_ignore=[
                                            'kernel_release',
                                            'redhat_release'])
    result_tcp_rr.add_tag(product_name)
    if nperf_mode == "multi":
        result_tcp_rr.add_tag("multithreaded")
        result_tcp_rr.set_parameter('num_parallel', nperf_num_parallel)

    result_tcp_rr.set_parameter("rr_size", size)

    baseline = perf_api.get_baseline_of_result(result_tcp_rr)
    netperf_baseline_template(netperf_cli_tcp_rr, baseline)

    tcp_rr_res_data = m2.run(netperf_cli_tcp_rr,
                          timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

    netperf_result_template(result_tcp_rr, tcp_rr_res_data)
    result_tcp_rr.set_comment(pr_comment)
    perf_api.save_result(result_tcp_rr)

    # prepare PerfRepo result for tcp_crr
    result_tcp_crr = perf_api.new_result("tcp_crr_id",
                                         "tcp_crr_result",
                                         hash_ignore=[
                                             'kernel_release',
                                             'redhat_release'])
    result_tcp_crr.add_tag(product_name)
    if nperf_mode == "multi":
        result_tcp_crr.add_tag("multithreaded")
        result_tcp_crr.set_parameter('num_parallel', nperf_num_parallel)

    result_tcp_crr.set_parameter("rr_size", size)

    baseline = perf_api.get_baseline_of_result(result_tcp_crr)
    netperf_baseline_template(netperf_cli_tcp_crr, baseline)

    tcp_crr_res_data = m2.run(netperf_cli_tcp_crr,
                          timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

    netperf_result_template(result_tcp_crr, tcp_crr_res_data)
    result_tcp_crr.set_comment(pr_comment)
    perf_api.save_result(result_tcp_crr)

    srv_proc.intr()

if nperf_cpupin:
    m1.run("service irqbalance start")
    m2.run("service irqbalance start")
