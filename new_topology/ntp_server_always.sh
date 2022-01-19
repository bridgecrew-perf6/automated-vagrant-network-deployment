#sudo docker run --name=ntp --restart=always --detach --publish=123:123/udp --read-only   --tmpfs=/etc/chrony:rw,mode=1750  --tmpfs=/run/chrony:rw,mode=1750  --tmpfs=/var/lib/chrony:rw,mode=1750 cturra/ntp
sudo docker run --name=ntp                           \
              --restart=always                     \
              --detach                             \
              --publish=123:123/udp                \
              --read-only                          \
              --tmpfs=/etc/chrony:rw,mode=1750     \
              --tmpfs=/run/chrony:rw,mode=1750     \
              --tmpfs=/var/lib/chrony:rw,mode=1750 \
              cturra/ntp
echo "NTP_server -> NTP Server run..\n"
