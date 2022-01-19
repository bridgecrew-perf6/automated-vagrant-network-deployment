sudo apt update
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt install -y docker.io
sudo groupadd docker
sudo usermod -aG docker vagrant
newgrp docker
docker pull mariadb:latest
docker pull wordpress
sudo ip link set enp0s8 up
echo "wordpress_server -> net set up..\n"
sudo /bin/su -c \
"cat << EOF > /etc/netplan/51-wordpress-netConf.yaml
network:
   ethernets:
       # enp0s8:
           # dhcp4: false
           # addresses: [192.168.20.2/25]
           # gateway4: 192.168.20.1
       enp0s8:
           dhcp4: false
           addresses: [192.168.10.2/25]
           gateway4: 192.168.10.1		   
   version: 2
EOF
"
echo "wordpress_server -> static IP set..\n"
echo "wordpress_server -> Route add..\n"
sudo netplan apply
