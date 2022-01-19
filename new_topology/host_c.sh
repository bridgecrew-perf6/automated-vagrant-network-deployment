# Startup commands for host-C go here
sudo apt update
sudo ip link set enp0s8 up
echo "Host-C -> net set up..\n"
sudo /bin/su -c \
"cat << EOF > /etc/netplan/51-host-c-netConf.yaml
network:
   ethernets:
       enp0s8:
           dhcp4: false
           addresses: [192.168.10.2/24]
           gateway4: 192.168.10.1
   version: 2
EOF
"
echo "Host-C -> static IP set..\n"
sudo netplan apply
echo "Host-C -> Route add..\n"
