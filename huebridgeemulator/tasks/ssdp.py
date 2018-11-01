"""???

.. todo:: Add description and some comments
"""
import random
import socket
import struct
from time import sleep
from uuid import getnode as get_mac

from huebridgeemulator.tools import get_ip_address
from huebridgeemulator.logger import sspd_search_logger, sspd_broadcast_logger


SSDP_ADDR = '239.255.255.250'
SSDP_PORT = 1900
MSEARCH_INTERVAL = 2


def ssdp_search():
    """???

    .. todo:: Add description and some comments
    """
    sspd_search_logger.debug("Thread ssdpSearch warming up")
    addr_ip = get_ip_address()
    mac = '%012x' % get_mac()
    multicast_group_c = SSDP_ADDR
    server_address = ('', SSDP_PORT)
    response_message = ('HTTP/1.1 200 OK\r\n'
                        'HOST: 239.255.255.250:1900\r\n'
                        'EXT:\r\n'
                        'CACHE-CONTROL: max-age=100\r\n'
                        'LOCATION: http://{}:80/description.xml\r\n'
                        'SERVER: Linux/3.14.0 UPnP/1.0 IpBridge/1.20.0\r\n'
                        'hue-bridgeid: {}\r\n'.format(addr_ip,
                                                      (mac[:6] + 'FFFE' + mac[6:]).upper()))
    custom_response_message = \
        {0: {"st": "upnp:rootdevice",
             "usn": "uuid:2f402f80-da50-11e1-9b23-" + mac + "::upnp:rootdevice"},
         1: {"st": "uuid:2f402f80-da50-11e1-9b23-" + mac,
             "usn": "uuid:2f402f80-da50-11e1-9b23-" + mac},
         2: {"st": "urn:schemas-upnp-org:device:basic:1",
             "usn": "uuid:2f402f80-da50-11e1-9b23-" + mac}}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(server_address)

    group = socket.inet_aton(multicast_group_c)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    sspd_search_logger.info("Thread ssdpSearch starting")

    while True:
        data, address = sock.recvfrom(1024)
        data = data.decode('utf-8')
        if data[0:19] == 'M-SEARCH * HTTP/1.1':
            if data.find("ssdp:discover") != -1:
                sleep(random.randrange(1, 10)/10)
                print("Sending M-Search response to " + address[0])
                for msg_id in range(3):
                    content = ("{}ST: {}\r\n"
                               "USN: {}\r\n\r\n").format(response_message,
                                                         custom_response_message[msg_id]["st"],
                                                         custom_response_message[msg_id]["usn"])
                    sock.sendto(bytes(content, "utf8"), address)
        sleep(1)


def ssdp_broadcast():
    """???

    .. todo:: Add description and some comments
    """
    sspd_broadcast_logger.debug("Thread ssdpBroadcast warming up")
    addr_ip = get_ip_address()
    mac = '%012x' % get_mac()
    multicast_group_s = (SSDP_ADDR, SSDP_PORT)
    message = ('NOTIFY * HTTP/1.1\r\n'
               'HOST: 239.255.255.250:1900\r\n'
               'CACHE-CONTROL: max-age=100\r\n'
               'LOCATION: http://{}:80/description.xml\r\n'
               'SERVER: Linux/3.14.0 UPnP/1.0 IpBridge/1.27.0\r\n'
               'NTS: ssdp:alive\r\n'
               'hue-bridgeid: {}\r\n'.format(addr_ip,
                                             (mac[:6] + 'FFFE' + mac[6:]).upper()))
    custom_message = {0: {"nt": "upnp:rootdevice",
                          "usn": "uuid:2f402f80-da50-11e1-9b23-" + mac + "::upnp:rootdevice"},
                      1: {"nt": "uuid:2f402f80-da50-11e1-9b23-" + mac,
                          "usn": "uuid:2f402f80-da50-11e1-9b23-" + mac},
                      2: {"nt": "urn:schemas-upnp-org:device:basic:1",
                          "usn": "uuid:2f402f80-da50-11e1-9b23-" + mac}}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(MSEARCH_INTERVAL+0.5)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    sspd_search_logger.info("Thread ssdpBroadcast starting")
    while True:
        for msg_id in range(3):
            content = "{}NT: {}\r\nUSN: {}\r\n\r\n".format(message,
                                                           custom_message[msg_id]["nt"],
                                                           custom_message[msg_id]["usn"])
            sock.sendto(bytes(content, "utf8"), multicast_group_s)
            sock.sendto(bytes(content, "utf8"), multicast_group_s)
        sleep(60)
