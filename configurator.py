### This script is used to perform the task of creating a Vagrantfile based on user input to provide a network topology.
# The user can choose between the given network topolgies: for now we have two options: 
# Star: Basic configuration consisting of two hosts and one switch
# Complex: More complex bus configuration: hosts + switch + router
# The script prompts the user for the: number of hosts, bandwidth allocation, delay configuration
# We create a data structure containing all the user inputs and a template Vagrantfile
# Using template substitution, we provide the data for the template and generate the final Vagrantfile, that
# can be used to create the network based on the parameters provided by running the 'vagrant up' command
# Testing the configuration can be done by doing ping operations, using netperf program and running benchmarks.

from statistics import variance
import string
import os

def import_template(fpath="Vagrantfile_template"):
    with open(fpath) as t:
        text = t.read()
        template = string.Template(text)
    t.close()
    return text, template

def export_config(config, fpath="Vagrantfile_generated"):
    with open(fpath, "w") as output:
        output.write(config)
    output.close()

def generate_component_templates(n_hosts, host_names):

    # Import host template
    host_text, host_template = import_template("host_template")
    
    output = ""
    for i in range(0, n_hosts):
        curr_template = host_template.substitute(**host_names[i])
        output += curr_template + "\n"
    return output


if __name__ == "__main__":

    os.system('cls')
    print("Starting configurator script")

    # Ask user for number of hosts
    # n_hosts = input("Enter number of hosts: (Default=2) ")
    # n_hosts = int(n_hosts) if n_hosts != '' else 2
    n_hosts = 2

    # Generate host names ( {'hostname1': 'host-a', 'hostname2': 'host-b'} )
    host_names = []
    for i in range(0, n_hosts):
        host_names.append({"hostname": "host_" + chr(ord('a') + i), "host_variable_name" : "host" + chr(ord('a') + i)})

    # Import empty template to be populated with components
    text, template = import_template()
    
    # Generate components (Routers, Switches, Hosts)
    gen_text = generate_component_templates(n_hosts, host_names)

    # Adding components to the config template
    data = {'hosts': gen_text}
    final_config = template.substitute(**data)

    # Export the final config
    export_config(final_config)

    print("Finalized generating Vagrantfile.")