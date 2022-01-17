sudo apt update
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt install -y docker.io
sudo groupadd docker
sudo usermod -aG docker vagrant
newgrp docker
docker pull cturra/ntp

sudo ip link set enp0s8 up
echo "NTP_server -> net set up..\n"
sudo /bin/su -c \
"cat << EOF > /etc/netplan/51-ntp-netConf.yaml
network:
   ethernets:
       enp0s8:
           dhcp4: false
           addresses: [192.168.20.2/25]
           gateway4: 192.168.20.1
   version: 2
EOF
"
echo "NTP_server -> static IP set..\n"
echo "NTP_server -> Route add..\n"
sudo netplan apply
