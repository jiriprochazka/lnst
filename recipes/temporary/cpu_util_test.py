from lnst.Controller.Task import ctl

m1 = ctl.get_host("machine1")
m2 = ctl.get_host("machine2")

m1.sync_resources(modules=["Netperf"])
m2.sync_resources(modules=["Netperf"])

m1_eth1 = m1.get_interface("eth1")
m2_eth1 = m2.get_interface("eth1")

nperf_cpu_util = ctl.get_alias("nperf_cpu_util") 
nperf_loc_cpu = ctl.get_alias("loc_cpu")
nperf_rem_cpu = ctl.get_alias("rem_cpu")
nperf_duration = ctl.get_alias("netperf_duration")

netperf_srv = ctl.get_module("Netperf",
                              options={
                                  "role" :  "server",
                                  "bind" : m1_eth1.get_ip(0)
                              })

netperf_cli = ctl.get_module("Netperf",
                              options={
                                  "role" : "client",
                                  "duration" : nperf_duration,
                                  "testname" : "TCP_STREAM",
                                  "netperf_server" : m1_eth1.get_ip(0),
                                  "loc_cpu" : nperf_loc_cpu,
                                  "rem_cpu" : nperf_rem_cpu,
                                  "cpu_util" : nperf_cpu_util
                              })

srv_proc = m1.run(netperf_srv, bg=True)

ctl.wait(2)

m2.run(netperf_cli, timeout=300)

srv_proc.intr()
