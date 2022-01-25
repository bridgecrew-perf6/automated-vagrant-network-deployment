### This script is used to perform the task of creating a Vagrantfile based on user input to provide a network topology.
# The user can choose between the given network topolgies: for now we have two options: 
# Star: Basic configuration consisting of two hosts and one switch
# Complex: More complex bus configuration: hosts + switch + router
# The script prompts the user for the: number of hosts, bandwidth allocation, delay configuration
# We create a data structure containing all the user inputs and a template Vagrantfile
# Using template substitution, we provide the data for the template and generate the final Vagrantfile, that
# can be used to create the network based on the parameters provided by running the 'vagrant up' command
# Testing the configuration can be done by doing ping operations, using netperf program and running benchmarks.

from operator import ge
from statistics import variance
from pathlib import Path
import string
import os
import re

def import_template(fpath="configurator_templates/Vagrantfile_template", text_needed=False):
    with open(fpath) as t:
        text = t.read()
        template = string.Template(text)
    t.close()
    if text_needed: return template, text
    else: return template

def export_config(config, fpath="generated_topology/Vagrantfile"):
    with open(fpath, "w") as output:
        output.write(config)
    output.close()

def generate_host_sh_files(n_hosts, names):
    host_sh_template = import_template("configurator_templates/host_sh_template")
    hostnames = []
    for i in range(0, n_hosts):
        hostnames.append(names[i]["hostname"])
        names[i]["hostname"] = names[i]["hostname"].replace("_", "-")
        names[i]["portname"] = "enp0s8"
        gen_sh = host_sh_template.safe_substitute(**names[i])
        export_config(gen_sh, "generated_topology/" + hostnames[i] + ".sh")

def generate_common_sh_file():
    content = "export DEBIAN_FRONTEND=noninteractive\n# Startup commands go here"
    export_config(content, "generated_topology/common.sh")

def generate_switch_sh_files(n_hosts, n_switches, names, port_owners):
    switch_sh_template = import_template("configurator_templates/switch_sh_template")
    insert1 = "sudo ovs-vsctl add-br my_bridge"
    bridge_conf = string.Template("sudo ovs-vsctl add-port my_bridge ${portname}")
    insert2 = string.Template("echo \"${switchname} -> Port assign to VLAN..\\n\"")

    for i in range(0, n_switches):
        gen_sh = switch_sh_template.substitute(**names[i])

        bridge = "\n" + insert1 + "\n"
        for j in range(0, port_owners[i]):
            bridge += bridge_conf.substitute(**names[j]) + "\n"
        bridge += insert2.substitute(**names[i])
        gen_sh += bridge
        export_config(gen_sh, "generated_topology/" + names[i]["switchname"] + ".sh")


def generate_switch_always_files(n_hosts, n_switches, names, port_owners):
    # Every time when switch give up, power on link (Interesting behaviour: If method called as first, it overwrites the global variable)
    config = string.Template("sudo ip link set ${portname} up")
    gen_router = ""
    
    for i in range(0, n_switches):
        gen_conf = ""
        for j in range(0, port_owners[i] + 1): # +1 for the router
            gen_conf += config.substitute(**names[j]) + "\n"
        export_config(gen_conf, "generated_topology/" + names[i]["switchname"] + "_always.sh")
        gen_router += config.substitute(**names[i]) + "\n"
    gen_router += "sudo iptables -P FORWARD ACCEPT"
    export_config(gen_router, "generated_topology/router_always.sh")
    

def generate_external_files(n_hosts, n_switches, names):

    generate_switch_always_files(n_hosts, n_switches, names, port_owners)
    generate_switch_sh_files(n_hosts, n_switches, names, port_owners)
    generate_host_sh_files(n_hosts, names)
    generate_common_sh_file()
    
def generate_component_templates(n_hosts, n_switches, names, port_owners):
    
    # Generating porimsenames
    promise = string.Template("vb.customize [\"modifyvm\", :id, \"--${promisename}\", \"allow-all\"]")
    gen_promises = ""
    for i in range(0, n_hosts):
        gen_promise = promise.substitute(**{"promisename" : "nicpromisc" + str(i+2)})
        gen_promises += "    " + gen_promise + "\n"

    # Generating Hosts
    gen_hosts = ""
    host_template = import_template("configurator_templates/host_template")    
    for i in range(0, n_hosts):
        gen_hosts += host_template.substitute(**names[i]) + "\n"
    # Aligning the code by removing fist 2 spaces
    gen_hosts = gen_hosts[2:]

    # Generating Router
    router_template, router_text = import_template("configurator_templates/switch_template", True)
    gen_router_ports = ""
    for i in range(0, n_switches):
        port_template, port_text = import_template("configurator_templates/port_template", True)
        router_port_t = {"hostname": names[i]["switchname"], "portname": names[i]["portname"], "switch_variable_name": "router"}
        gen_router_ports += port_template.substitute(**router_port_t) + "\n"
    gen_router_ports = gen_router_ports[4:]

    router_text = router_text.replace("${ports}", gen_router_ports)
    router_template = string.Template(router_text)
    router_config = {"switchname" : "router", "switch_variable_name" : "router"}
    gen_router = router_template.substitute(**router_config)

    # Generating Switches
    gen_switches = ""
    host_counter = 0
    for i in range(0, n_switches):
        switch_template, switch_text = import_template("configurator_templates/switch_template", True)
        
        gen_ports = ""
        port_counter = 0
        for j in range(0, port_owners[i]):
            # Generating Switch Ports
            port_template, port_text = import_template("configurator_templates/port_template", True)
            port_t = {"hostname": names[host_counter]["hostname"], "portname": names[port_counter]["portname"], "switch_variable_name": "switch"}
            host_counter += 1
            port_counter += 1
            
            # Substituting the port number with the host number
            port = port_template.substitute(**port_t) + "\n    "
            gen_ports += port[4:]
            
        # Add Router connection
        port_template = import_template("configurator_templates/port_template")
        # TODO WRONG LINE BELOW
        port_t = {"hostname": names[i]["switchname"], "portname": names[port_counter]["portname"], "switch_variable_name": "switch"}
        port = port_template.substitute(**port_t) + "\n"
        gen_ports += port[4:]
        switch_text = switch_text.replace("${ports}", gen_ports)
        switch_template = string.Template(switch_text)
        gen_switches += switch_template.substitute(**names[i])
        
    # Aligning the code by removing the last \n
    gen_switches = gen_switches[:len(gen_switches) - 1]

    # Generate and configure file for each component
    generate_external_files(n_hosts, n_switches, names)
    return gen_router, gen_promises, gen_hosts, gen_switches


if __name__ == "__main__":

    os.system('cls')
    Path("generated_topology").mkdir(parents=True, exist_ok=True)
    print("---Starting network configurator script---\n\n")

    # Ask user for number of hosts
    n_hosts = input("Enter number of hosts: (Default=2) \n")
    n_hosts = int(n_hosts) if n_hosts != '' else 2

    # Ask user for number of switches
    n_switches = input("Enter number of switches: (Default=2) ")
    n_switches = int(n_switches) if n_switches != '' else 2

    if n_switches == 1:
        port_owners = [n_hosts]
    elif n_switches == 2:
        n_hosts_of_switch_a = int(input("Enter number of hosts connected to switch_a: (Free hosts remaining: " + str(n_hosts) + ") "))
        if n_hosts_of_switch_a > n_hosts:
            print("Number of hosts connected to switch_a is greater than the number of requested hosts!")
            print("Note: All the hosts are connected to switch_a...")
            n_hosts_of_switch_a = n_hosts
            n_hosts_of_switch_b = 0
        else: n_available_hosts = n_hosts - n_hosts_of_switch_a
        n_hosts_of_switch_b = n_available_hosts
        port_owners = [n_hosts_of_switch_a, n_hosts_of_switch_b]

    # Generate host names ( {'hostname1': 'host-a', 'hostname2': 'host-b'} )    
    names = []
    for i in range(0, n_hosts + 1): # +1 for router
        
        if i >= 3: portname = "enp0s" + str(i+8+5)
        else: portname = "enp0s" + str(i+8)

        hostname = "host-" + chr(ord('a') + i)
        print("Configure link capacity for {}".format(hostname))
        bandwidth = input("Bandwidth in Mbit/s (Max = 200 Mbit/s, ENTER for no limit) : ")
        bandwidth = int(bandwidth) if bandwidth != '' else 0;
        delay = input("Network delay (Default = 0ms) : \n")
        delay = int(delay) if delay != '' else 0;

        names.append({
                "switchname": "switch-" + chr(ord('a') + i), 
                "switch_variable_name" : "switch",
                "hostname": "host-" + chr(ord('a') + i), 
                "host_variable_name" : "host" + chr(ord('a') + i), 
                "portname": portname,
                "ip" : "192.168." + "0." + str(i + 1),
                "bandwidth": bandwidth,
                "delay": delay
            })

    # Import empty template to be populated with components
    template = import_template()
    
    # Generate components (Routers, Switches, Hosts)
    gen_router, gen_promises, gen_hosts, gen_switches = generate_component_templates(n_hosts, n_switches, names, port_owners)

    # Adding components to the config template
    data = {'router': gen_router, 'promises': gen_promises, 'hosts': gen_hosts, 'switches': gen_switches}
    final_config = template.substitute(**data)

    # Removing empty lines
    final_config = re.sub(r'\n\s*\n', '\n', final_config)
    
    # Export the final config
    export_config(final_config)

    print("Finalized generating Vagrantfile.")