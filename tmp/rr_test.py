from lnst.Controller.Task import ctl
m1 = ctl.get_host("machine1")
m2 = ctl.get_host("machine2")

m1.sync_resources(modules=["Netperf"])
m2.sync_resources(modules=["Netperf"])

m1_testiface = m1.get_interface("testiface")

netperf_duration = ctl.get_alias("netperf_duration")

nperf_cpu_util = ctl.get_alias("nperf_cpu_util")

# TCP_RR, UDP_RR, SCTP_RR, TCP_CRR
stream_tests = []
rr_tests = []
for testname in ["TCP_STREAM", "UDP_STREAM", "SCTP_STREAM"]:
    stream_tests.append(ctl.get_module("Netperf",
                             options={
                                 "role" : "client",
                                 "netperf_server" : m1_testiface.get_ip(0),
                                 "cpu_util" : nperf_cpu_util,
                                 "duration" : netperf_duration,
                                 "testname" : testname,
                                 "confidence" : "99,5"
                             }))

for testname in ["TCP_RR", "TCP_CRR", "SCTP_RR"]:
    rr_tests.append(ctl.get_module("Netperf",
                             options={
                                 "role" : "client",
                                 "netperf_server" : m1_testiface.get_ip(0),
                                 "cpu_util" : nperf_cpu_util,
                                 "duration" : netperf_duration,
                                 "testname" : testname,
                                 "confidence" : "99,5"
                             }))

netperf_srv = ctl.get_module("Netperf",
                              options={
                                  "role" : "server",
                                  "bind" : m1_testiface.get_ip(0)
                                  })

srv_proc = m1.run(netperf_srv, bg=True)
ctl.wait(2)

for test in stream_tests:
    m2.run(test, timeout = 600)
for test in rr_tests:
    m2.run(test, timeout = 600)

srv_proc.intr()
