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

def generate_host_sh_files(n_hosts, names, port_owners):
    host_sh_template = import_template("configurator_templates/host_sh_template")
    hostnames = []
    counter = 0
    for i in range(0, len(port_owners)):
        for j in range(0, port_owners[i]):
            hostnames.append(names[counter]["hostname"])
            names[counter]["hostname"] = names[counter]["hostname"].replace("_", "-")
            names[counter]["portname"] = "enp0s8"
            # Setting IP
            names[counter]["ip"] = "192.168."+ str(i) +"." + str(j + 2)
            names[counter]["gateway"] = "192.168."+ str(i) +".1"
            gen_sh = host_sh_template.safe_substitute(**names[counter])
            export_config(gen_sh, "generated_topology/" + hostnames[counter] + ".sh")
            counter += 1

def generate_router_sh_file(n_switches, names):
    # Generate Ethernet ports of the router
    eth = string.Template("       ${portname}:\n           dhcp4: false\n           addresses: [${router_ip}/24]\n")
    gen_eth = ""
    for i in range(0, n_switches):
        gen_eth += eth.substitute(**names[i])

    router_sh_template, router_sh_text = import_template("configurator_templates/router_sh_template", text_needed=True)
    gen_sh = router_sh_text.replace("${eth}", gen_eth)
    export_config(gen_sh, "generated_topology/router.sh")

def generate_common_sh_file():
    content = "export DEBIAN_FRONTEND=noninteractive\n# Startup commands go here"
    export_config(content, "generated_topology/common.sh")

def generate_switch_sh_files(n_hosts, n_switches, names, port_owners):
    switch_sh_template = import_template("configurator_templates/switch_sh_template")
    insert1 = "sudo ovs-vsctl add-br my_bridge"
    bridge_conf = string.Template("sudo ovs-vsctl add-port my_bridge ${portname}")
    insert2 = string.Template("echo \"${switchname} -> Port assign to VLAN..\\n\"")

    if n_switches > 1: 
        port_owners = [port + 1 for port in port_owners]

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
    
    if n_switches > 1: 
        port_owners = [port + 1 for port in port_owners]

    for i in range(0, n_switches):
        gen_conf = ""
        for j in range(0, port_owners[i]): # +1 for the router
            gen_conf += config.substitute(**names[j]) + "\n"
        export_config(gen_conf, "generated_topology/" + names[i]["switchname"] + "_always.sh")
        gen_router += config.substitute(**names[i]) + "\n"
    gen_router += "sudo iptables -P FORWARD ACCEPT"
    if n_switches > 1:
        export_config(gen_router, "generated_topology/router_always.sh")
    

def generate_external_files(n_hosts, n_switches, names):

    generate_switch_always_files(n_hosts, n_switches, names, port_owners)
    if n_switches > 1:
        generate_router_sh_file(n_switches, names)
    generate_switch_sh_files(n_hosts, n_switches, names, port_owners)
    generate_host_sh_files(n_hosts, names, port_owners)
    generate_common_sh_file()
    
def generate_component_templates(n_hosts, n_switches, names, port_owners):
    
    # Generating Virtual Network Interfaces
    promise = string.Template("vb.customize [\"modifyvm\", :id, \"--${promisename}\", \"allow-all\"]")
    gen_promises = ""
    # The limiting factor is the maximum number of hosts connected to a switch
    if n_switches < max(port_owners):
        n = max(port_owners)
        if n_switches > 1: n += 1
    # The limiting factor is the number of switches
    else:
        n = n_switches

    for i in range(0, n):
        gen_promise = promise.substitute(**{"promisename" : "nicpromisc" + str(i+2)})
        gen_promises += "    " + gen_promise + "\n"

    # Generating Hosts
    gen_hosts = ""
    host_template = import_template("configurator_templates/host_template")    
    for i in range(0, n_hosts):
        gen_hosts += host_template.substitute(**names[i]) + "\n"
    # Aligning the code by removing fist 2 spaces
    gen_hosts = gen_hosts[2:]

    if n_switches > 1:
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
            
        if n_switches > 1:
            # Add Router connection
            port_template = import_template("configurator_templates/port_template")
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
    if n_switches > 1:
        return gen_router, gen_promises, gen_hosts, gen_switches
    else:
        return gen_promises, gen_hosts, gen_switches


if __name__ == "__main__":

    os.system('cls')
    Path("generated_topology").mkdir(parents=True, exist_ok=True)
    print("---Starting network configurator script---\n")

    # Ask user for number of switches
    n_switches = input("Enter number of switches: (Default=2, Min=1, Max=6) ")
    n_switches = int(n_switches) if n_switches != '' else 2
    actual_switch = 1
    if int(n_switches) < 1 or int(n_switches) > 6:
        print("Number of switches must be between 1 and 6")
        exit()
    if int(n_switches) > 1:
        print("A router has been created, generating a TREE Topology")
    else:
        print("Generating a STAR Topology")
    # Ask user for number of hosts
    n_hosts = input("Enter number of hosts: (Default=4, Min=2, Max=" + str(6 * n_switches) + ") ")
    n_hosts = int(n_hosts) if n_hosts != '' else 4
    unasigned_hosts = n_hosts
    if int(n_hosts) < 2 or int(n_hosts) > (6 * n_switches):
        print("Number of hosts must be between 2 and " + str(6 * n_switches) + ", exiting")
        exit()

    if n_switches == 1: port_owners = [n_hosts]
    else:
        port_owners = []
        while unasigned_hosts > 0 and actual_switch <= n_switches:
            if actual_switch == n_switches:
                if unasigned_hosts < 6:
                    port_owners.append(unasigned_hosts)
                    print("The rest hosts (" + str(unasigned_hosts) + "x) are assigned to switch " + str(actual_switch))
                    unasigned_hosts = 0
                else:
                    print("Error: More than 6 hosts assigned to the last switch, exiting")
                    exit()
            else:
                n_ports = input("Enter number of hots connected to switch " + str(actual_switch) + ": (Default= " + str(min(2, unasigned_hosts)) +", Min=1, Max=" + str(min(6, unasigned_hosts)) + ") ")
                if n_ports == '':
                    n_ports = min(2, unasigned_hosts)
                    print("Assigned " + str(n_ports) + " ports to switch " + str(actual_switch))
                elif int(n_ports) > min(6, unasigned_hosts):
                    print("You have requested more hosts then available, assigning " + str(min(6, unasigned_hosts)) + " ports to the" + str(actual_switch) + " switch")
                    n_ports = min(6, unasigned_hosts)
                else:
                    n_ports = int(n_ports)
                
                port_owners.append(n_ports)
                unasigned_hosts -= n_ports
                if unasigned_hosts == 0:
                    for i in range(actual_switch, n_switches):
                        print("There is not any host available to connect to switch" + str(i))
                        port_owners.append(0)
                actual_switch += 1        

    # Generate host names ( {'hostname1': 'host-a', 'hostname2': 'host-b'} )    
    names = []
    for i in range(0, max(n_hosts, n_switches) + 1): # +1 for router
        
        if i >= 3: portname = "enp0s" + str(i+8+5)
        else: portname = "enp0s" + str(i+8)

        if i < n_hosts:
            hostname = "host-" + chr(ord('a') + i)
            print("Configure link capacity for {}".format(hostname))
            valid_input = False
            while valid_input == False:
                bandwidth = input("Bandwidth in Mbit/s (Max = 200 Mbit/s, ENTER for no limit) : ")
                if bandwidth != '':
                    bandwidth = int(bandwidth)
                    if bandwidth < 0 or bandwidth > 200:
                        print("Please enter a valid value!")
                    else:
                        valid_input = True
                else:
                    bandwidth = 0
                    valid_input = True

            valid_input = False
            while valid_input == False:
                delay = input("Network delay (Default = 0ms) : \n")
                if delay != '':
                    delay = int(delay)
                    if delay < 0 or delay > 10000:
                        print("Please enter a valid value!")
                    else:
                        valid_input = True
                else:
                    delay = 0
                    valid_input = True

        names.append({
                "switchname": "switch-" + chr(ord('a') + i), 
                "switch_variable_name" : "switch",
                "hostname": "host-" + chr(ord('a') + i), 
                "host_variable_name" : "host" + chr(ord('a') + i), 
                "portname": portname,
                "ip" : "192.168." + "0." + str(i + 2),
                "router_ip" : "192.168." + str(i) + ".1",
                "gateway" : "192.168." + str(i) + ".1",
                "bandwidth": bandwidth,
                "delay": delay
            })

    # Import empty template to be populated with components
    template = import_template()
    
    # Generate components (Routers, Switches, Hosts)
    # Adding components to the config template
    if n_switches > 1:
        gen_router, gen_promises, gen_hosts, gen_switches = generate_component_templates(n_hosts, n_switches, names, port_owners)
        data = {'router': gen_router, 'promises': gen_promises, 'hosts': gen_hosts, 'switches': gen_switches}
    else:
        gen_promises, gen_hosts, gen_switches = generate_component_templates(n_hosts, n_switches, names, port_owners)
        data = {'router': "", 'promises': gen_promises, 'hosts': gen_hosts, 'switches': gen_switches}

    final_config = template.substitute(**data)

    # Removing empty lines
    final_config = re.sub(r'\n\s*\n', '\n', final_config)
    
    # Export the final config
    export_config(final_config)

    print("Finalized generating Vagrantfile.")