# Startup commands for host-D go here
sudo apt update
sudo ip link set enp0s8 up
echo "Host-D -> net set up..\n"
sudo /bin/su -c \
"cat << EOF > /etc/netplan/51-host-d-netConf.yaml
network:
   ethernets:
       enp0s8:
           dhcp4: false
           addresses: [192.168.10.3/24]
           gateway4: 192.168.10.1
   version: 2
EOF
"
echo "Host-D -> static IP set..\n"
sudo netplan apply
echo "Host-D -> Route add..\n"
