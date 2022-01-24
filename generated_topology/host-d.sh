# Startup commands for host-d go here
sudo apt update
sudo ip link set enp0s11 up
echo "host-d -> net set up..\n"
sudo /bin/su -c \
"cat << EOF > /etc/netplan/51-host-d-netConf.yaml
network:
   ethernets:
       enp0s11:
           dhcp4: false
           addresses:
           - 192.168.0.4/24
   version: 2
EOF
"
echo "host-d -> static IP set..\n"
sudo netplan apply
echo "host-d -> Route add..\n"
