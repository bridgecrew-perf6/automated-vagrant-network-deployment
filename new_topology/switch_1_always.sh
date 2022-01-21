# Every time when switch give up, power on link
sudo ip link set enp0s8 up
sudo ip link set enp0s9 up
#sudo ip link set enp0s10 up
DELAY_MS=40
RATE_MBIT=10
BUF_PKTS=33
BDP_BYTES=$(echo "($DELAY_MS/1000.0)*($RATE_MBIT*1000000.0/8.0)" | bc -q -l)
BDP_PKTS=$(echo "$BDP_BYTES/1500" | bc -q)
LIMIT_PKTS=$(echo "$BDP_PKTS+$BUF_PKTS" | bc -q)
sudo tc qdisc replace dev enp0s8 root netem delay ${DELAY_MS}ms rate ${RATE_MBIT}Mbit limit ${LIMIT_PKTS}
sudo iptables -P FORWARD ACCEPT