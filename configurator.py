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
        gen_sh = host_sh_template.substitute(**names[i])
        export_config(gen_sh, "generated_topology/" + hostnames[i] + ".sh")

def generate_common_sh_file():
    content = "export DEBIAN_FRONTEND=noninteractive\n# Startup commands go here"
    export_config(content, "generated_topology/common.sh")

def generate_switch_sh_files(n_hosts, n_switches, names):
    switch_sh_template = import_template("configurator_templates/switch_sh_template")
    insert1 = "sudo ovs-vsctl add-br my_bridge"
    bridge_conf = string.Template("sudo ovs-vsctl add-port my_bridge ${portname}")
    insert2 = string.Template("echo \"${switchname} -> Port assign to VLAN..\\n\"")

    for i in range(0, n_switches):
        gen_sh = switch_sh_template.substitute(**names[i])

        bridge = "\n" + insert1 + "\n"
        for j in range(n_hosts):
            bridge += bridge_conf.substitute(**names[j]) + "\n"
        bridge += insert2.substitute(**names[i])
        gen_sh += bridge
        export_config(gen_sh, "generated_topology/" + names[i]["switch_variable_name"] + ".sh")

def generate_switch_always_file(n_hosts, names):
    # Every time when switch give up, power on link (Interesting behaviour: If method called as first, it overwrites the global variable)
    config = string.Template("sudo ip link set ${portname} up")
    gen_conf = ""
    for i in range(0, n_hosts):
        gen_conf += config.substitute(**names[i]) + "\n"
    export_config(gen_conf, "generated_topology/switch_always.sh")

def generate_external_files(n_hosts, n_switches, names):

    generate_switch_always_file(n_hosts, names)
    generate_switch_sh_files(n_hosts, n_switches, names)
    generate_host_sh_files(n_hosts, names)
    generate_common_sh_file()
    
def generate_component_templates(n_hosts, n_switches, names):
    
    # Generating Hosts
    gen_hosts = ""
    host_template = import_template("configurator_templates/host_template")    
    for i in range(0, n_hosts):
        gen_hosts += host_template.substitute(**names[i]) + "\n"
    # Aligning the code by removing fist 2 spaces
    gen_hosts = gen_hosts[2:]

    # Generating Switches
    gen_switches = ""
    switch_template, switch_text = import_template("configurator_templates/switch_template", True)
    for i in range(0, n_switches):
        # Generating Switch Ports
        port_template, port_text = import_template("configurator_templates/port_template", True)
        port_text = port_text.replace("    ", "")
        
        gen_ports = ""
        for j in range(0, n_hosts):
            # Substituting the port number with the host number
            port = port_template.substitute(**names[j]) + "\n    "
            # Substituting the switch variable name as it would be wrong due to indexing
            port_name = names[i]["switch_variable_name"]
            port = port_name + port[10:]
            gen_ports += port

        #Gen_ports is GOOD
        # switch_text is not good.
        switch_text = switch_text.replace("${ports}", gen_ports)
        #Below is GOOD
        switch_template = string.Template(switch_text)
        gen_switches += switch_template.substitute(**names[i])
        
    # Aligning the code by removing the last \n
    gen_switches = gen_switches[:len(gen_switches) - 1]

    # Generate and configure file for each component
    generate_external_files(n_hosts, n_switches, names)
    return gen_hosts, gen_switches

if __name__ == "__main__":

    os.system('cls')
    Path("generated_topology").mkdir(parents=True, exist_ok=True)
    print("Starting configurator script")

    # Ask user for number of hosts
    n_hosts = input("Enter number of hosts: (Default=2) ")
    n_hosts = int(n_hosts) if n_hosts != '' else 2

    # Ask user for number of switches
    # n_switches = input("Enter number of hosts: (Default=2) ")
    # n_switches = int(n_switches) if n_switches != '' else 1
    # n_hosts = 2
    n_switches = 1

    # Generate host names ( {'hostname1': 'host-a', 'hostname2': 'host-b'} )
    names = []
    for i in range(0, n_hosts):
        
        if i >= 3: portname = "enp0s" + str(i+8+5)
        else: portname = "enp0s" + str(i+8)

        names.append({
                "switchname": "switch-" + chr(ord('a') + i), 
                "switch_variable_name" : "switch",# + chr(ord('a') + i), 
                "hostname": "host-" + chr(ord('a') + i), 
                "host_variable_name" : "host" + chr(ord('a') + i), 
                "portname": portname,
                "ip" : "192.168." + "0." + str(i + 1)
            })

    # Import empty template to be populated with components
    template = import_template()
    
    # Generate components (Routers, Switches, Hosts)
    gen_hosts, gen_switches = generate_component_templates(n_hosts, n_switches, names)

    # Adding components to the config template
    data = {'hosts': gen_hosts, 'switches': gen_switches}
    final_config = template.substitute(**data)

    # Removing empty lines
    final_config = re.sub(r'\n\s*\n', '\n', final_config)
    
    # Export the final config
    export_config(final_config)

    print("Finalized generating Vagrantfile.")