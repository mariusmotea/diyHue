#!/bin/bash

set -ex

cat <<EOF
Welcome to the marvambass/nginx-ssl-secure container
IMPORTANT:
  IF you use SSL inside your personal NGINX-config,
  you should add the Strict-Transport-Security header like:
    # only this domain
    add_header Strict-Transport-Security "max-age=31536000";
    # apply also on subdomains
    add_header Strict-Transport-Security "max-age=31536000; includeSubdomains";
  to your config.
  After this you should gain a A+ Grade on the Qualys SSL Test
EOF

if [ -z ${DH_SIZE+x} ]
then
  >&2 echo ">> no \$DH_SIZE specified using default" 
  DH_SIZE="2048"
fi


DH="/etc/nginx/external/dh.pem"

if [ ! -e "$DH" ]
then
  echo ">> seems like the first start of nginx"
  echo ">> doing some preparations..."
  echo ""

  echo ">> generating $DH with size: $DH_SIZE"
  openssl dhparam -out "$DH" $DH_SIZE
fi

if [ ! -e "/etc/nginx/external/cert.pem" ] || [ ! -e "/etc/nginx/external/key.pem" ]
then
    if [ -z ${MAC+x} ]; then 
        echo "MAC not passed"
        mac=`cat /sys/class/net/$(ip route get 8.8.8.8 | sed -n 's/.* dev \([^ ]*\).*/\1/p')/address`
    else
        echo "MAC passed as '$1'"
        mac=$1
    fi
    echo $mac

    echo -e "\033[33m--Host MAC address is $mac--\033[0m"

    serial="${mac:0:2}${mac:3:2}${mac:6:2}fffe${mac:9:2}${mac:12:2}${mac:15:2}"
    dec_serial=`python3 -c "print(int(\"$serial\", 16))"`
    openssl req -new \
    -config /opt/openssl.conf \
    -nodes \
    -x509 \
    -newkey ec \
    -pkeyopt ec_paramgen_curve:P-256 \
    -pkeyopt ec_param_enc:named_curve \
    -subj "/C=NL/O=Philips Hue/CN=$serial" \
    -keyout /etc/nginx/external/key.pem \
    -out /etc/nginx/external/cert.pem \
    -set_serial $dec_serial
fi
echo ">> copy /etc/nginx/external/*.conf files to /etc/nginx/conf.d/"
cp /etc/nginx/external/*.conf /etc/nginx/conf.d/ 2> /dev/null > /dev/null

# exec CMD
echo ">> exec docker CMD"
echo "$@"
exec "$@"
