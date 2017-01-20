from lnst.Controller.Task import ctl

from lnst.RecipeCommon.IRQ import pin_dev_irqs

# ------
# SETUP
# ------

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
nperf_cpu_util = ctl.get_alias("nperf_cpu_util")
nperf_max_dev = ctl.get_alias("nperf_max_dev")
nperf_cpupin = ctl.get_alias("nperf_cpupin")

m1_testiface = m1.get_interface("testiface")
m2_testiface = m2.get_interface("testiface")

m1_testiface.set_mtu(mtu)
m2_testiface.set_mtu(mtu)

if nperf_cpupin:
    m1.run("service irqbalance stop")
    m2.run("service irqbalance stop")

p_opts = "-L %s" % (m2_testiface.get_ip(0))

if nperf_cpupin:
    for m, d in [ (m1, m1_testiface), (m2, m2_testiface) ]:
        pin_dev_irqs(m, d, 0)
    p_opts += " -T%s,%s" % (nperf_cpupin, nperf_cpupin)

for size in ["1K,1K", "5K,5K", "7K,7K", "10K,10K", "12K,12K"]:

    n_p_opts = p_opts

    netperf_cli_tcp_rr = ctl.get_module("Netperf",
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
                                          "testoptions" : "-r %s" % size
                                      })

    netperf_cli_tcp_crr = ctl.get_module("Netperf",
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
                                          "testoptions" : "-r %s" % size
                                      })


    netperf_srv = ctl.get_module("Netperf",
                                  options={
                                      "role" : "server",
                                      "bind" : m1_testiface.get_ip(0)
                                      })

    ctl.wait(15)

    # Netperf test
    srv_proc = m1.run(netperf_srv, bg=True)
    ctl.wait(2)

    m2.run(netperf_cli_tcp_rr,
           timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)
    ctl.wait(15)
    m2.run(netperf_cli_tcp_crr,
           timeout = (netperf_duration + nperf_reserve)*nperf_max_runs)

    srv_proc.intr()

if nperf_cpupin:
    m1.run("service irqbalance start")
    m2.run("service irqbalance start")
