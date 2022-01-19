# automated-vagrant-network-deployment

First version.

two hosts connected to a switch.
Host-a  > IP: 192.168.0.2	
Host-b  > IP: 192.168.0.3	

## Running the program
User will be able to provide network configuration parameters based on the script prompts.
To run the program:
1. Clone the repository: `git clone https://github.com/nlacko97/automated-vagrant-network-deployment.git`
2. Run the configurator script
    1. Directly: `python configurator.py`
    2. Using Docker: `docker build -t conf`, then `docker run -it --rm -v $(pwd)/output:/output conf`
3. The generated Vagrantfile will be in the `output` folder. Run the `vagrant up` command to deploy and test the network topology 