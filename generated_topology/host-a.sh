# Startup commands for host-a go here
sudo apt update
sudo ip link set enp0s8 up
echo "host-a -> net set up..\n"
sudo /bin/su -c \
"cat << EOF > /etc/netplan/51-host-a-netConf.yaml
network:
   ethernets:
       enp0s8:
           dhcp4: false
           addresses:
           - 192.168.0.1/24
   version: 2
EOF
"
echo "host-a -> static IP set..\n"
sudo netplan apply
echo "host-a -> Route add..\n"
