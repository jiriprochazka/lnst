from lnst.Controller.Task import ctl

hostA = ctl.get_host("machine1")
hostB = ctl.get_host("machine2")

hostA.sync_resources(modules=["IcmpPing", "Netperf"])
hostB.sync_resources(modules=["IcmpPing", "Netperf"])

ping_mod = ctl.get_module("IcmpPing",
                           options={
                              "addr": hostB.get_ip("testiface", 0),
                              "count": 100,
                              "interval": 0.2,
                              "iface" : hostA.get_devname("testiface"),
                              "limit_rate": 90})

#netperf_srv = ctl.get_module("Netperf",
#                              options={
#                                  "role" : "server",
#                                  "bind" : hostA.get_ip("testiface")
#                            })
#
#netperf_cli_tcp = ctl.get_module("Netperf",
#                                  options={
#                                      "role" : "client",
#                                      "netperf_server" : hostA.get_ip("testiface"),
#                                      "duration" : 60,
#                                      "testname" : "TCP_STREAM",
#                                      "netperf_opts" : "-L %s" % hostB.get_ip("testiface")
#                                  })
#
#netperf_cli_udp= ctl.get_module("Netperf",
#                                  options={
#                                      "role" : "client",
#                                      "netperf_server" : hostA.get_ip("testiface"),
#                                      "duration" : 60,
#                                      "testname" : "UDP_STREAM",
#                                      "netperf_opts" : "-L %s" % hostB.get_ip("testiface")
#                                  })

hostA.run(ping_mod)
#server_proc = hostA.run(netperf_srv, bg=True)
#ctl.wait(2)
#hostB.run(netperf_cli_tcp, timeout=70)
#hostB.run(netperf_cli_udp, timeout=70)
#server_proc.intr()
