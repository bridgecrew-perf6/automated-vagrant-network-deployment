# Startup commands for host-b go here
sudo apt update
sudo ip link set ens0s9 up
echo "host-b -> net set up..\n"
sudo /bin/su -c \
"cat << EOF > /etc/netplan/51-host-b-netConf.yaml
network:
   ethernets:
       ens0s9:
           dhcp4: false
           addresses:
           - 192.168.0.2/24
   version: 2
EOF
"
echo "host-b -> static IP set..\n"
sudo netplan apply
echo "host-b -> Route add..\n"
