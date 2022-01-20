### This script is used to perform the task of creating a Vagrantfile based on user unput to provide a network topology.
# The user can choose between the given network topolgies: for now we have two options: 
# basic configuration consisting of two hosts and one switch
# more complex bus configuration: hosts + switch + router
# The script prompts the user for the: number of hosts, bandwidth allocation, delay configuration
# We create a data structure containing all the user inputs and a template Vagrantfile
# Using template substitution, we provide the data for the template and generate the final Vagrantfile, that
# can be used to create the network based on the parameters provided by running the 'vagrant up' command
# Testing the configuration can be done by doing ping operations, using netperf program and running benchmarks

import string

print("Starting configurator script")

data = {
    "hostname1": "host-a",
    "hostname2": "host-b",
}

with open("Vagrantfile_template") as t:
    template = string.Template(t.read())

final_output = template.substitute(**data)

with open("/output/Vagrantfile_generated", "w") as output:
    output.write(final_output)

print("Finalized generating Vagrantfile.")