# Startup commands for host-c go here
sudo apt update
sudo ip link set enp0s10 up
echo "host-c -> net set up..\n"
sudo /bin/su -c \
"cat << EOF > /etc/netplan/51-host-c-netConf.yaml
network:
   ethernets:
       enp0s10:
           dhcp4: false
           addresses:
           - 192.168.0.3/24
   version: 2
EOF
"
echo "host-c -> static IP set..\n"
sudo netplan apply
echo "host-c -> Route add..\n"
