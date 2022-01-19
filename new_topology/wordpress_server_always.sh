#sudo docker run --name=ntp --restart=always --detach --publish=123:123/udp --read-only   --tmpfs=/etc/chrony:rw,mode=1750  --tmpfs=/run/chrony:rw,mode=1750  --tmpfs=/var/lib/chrony:rw,mode=1750 cturra/ntp
docker network create red_wp
docker run -d --name servidor_mysql \
                --network red_wp \
                -v /opt/mysql_wp:/var/lib/mysql \
                -e MYSQL_DATABASE=bd_wp \
                -e MYSQL_USER=user_wp \
                -e MYSQL_PASSWORD=asdasd \
                -e MYSQL_ROOT_PASSWORD=asdasd \
                mariadb
docker run -d --name servidor_wp \
                --network red_wp \
                -v /opt/wordpress:/var/www/html/wp-content \
                -e WORDPRESS_DB_HOST=servidor_mysql \
                -e WORDPRESS_DB_USER=user_wp \
                -e WORDPRESS_DB_PASSWORD=asdasd \
                -e WORDPRESS_DB_NAME=bd_wp \
                -p 80:80 \
                wordpress
echo "NTP_server -> NTP Server run..\n"
