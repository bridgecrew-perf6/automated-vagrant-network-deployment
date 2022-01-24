export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y tcpdump
apt-get install -y openvswitch-common openvswitch-switch apt-transport-https ca-certificates curl software-properties-common

# Startup commands for switch go here
# Enable packet forwarding
sudo /bin/su -c "echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.conf"
sudo sysctl -p /etc/sysctl.conf
echo "switch-a -> IP packet forward active..\n"
# Set-up VLAN port
sudo ovs-vsctl add-br my_bridge
sudo ovs-vsctl add-port my_bridge enp0s8
sudo ovs-vsctl add-port my_bridge enp0s9
sudo ovs-vsctl add-port my_bridge enp0s10
sudo ovs-vsctl add-port my_bridge enp0s11
echo "switch-a -> Port assign to VLAN..\n"