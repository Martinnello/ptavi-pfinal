#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Programa User Agent Cliente."""

import sys
import socket
from uaserver import XmlHandler
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


try:
    CONFIG_FILE = sys.argv[1]
    METHOD = str.upper(sys.argv[2])
    OPTION = str(sys.argv[3])

except IndexError:
    sys.exit("  Usage: python3 uaclient.py config method option ")


if __name__ == "__main__":

    try:
        parser = make_parser()
        Handler = XmlHandler()
        parser.setContentHandler(Handler)
        parser.parse(open(CONFIG_FILE))
        Config = Handler.get_tags()

    except FileNotFoundError:
        sys.exit('  File not found!')

    USER = Config['account_username']
    PASS = Config['account_passwd']
    UA_IP = Config['uaserver_ip']
    UA_PORT = int(Config['uaserver_puerto'])
    RTP_PORT = int(Config['rtpaudio_puerto'])
    REGPROXY_IP = Config['regproxy_ip']
    REGPROXY_PORT = int(Config['regproxy_puerto'])
    LOG = Config['log_path']
    AUDIO = Config['audio_path']

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((REGPROXY_IP, REGPROXY_PORT))

    if METHOD == "REGISTER":
        Mess = (METHOD + ' sip:' + USER + ':' + str(UA_PORT))
        Mess += (' SIP/2.0\r\n' + 'Expires: ' + OPTION + '\r\n\r\n')
        print(Mess)
        my_socket.send(bytes(Mess, 'utf-8'))

    elif METHOD == "INVITE":
        Mess = (METHOD + ' sip:' + OPTION + ' SIP/2.0\r\n')
        SDP = ("Content-Type: application/sdp\r\n\r\n" + 'v= 0\r\n')
        SDP += ('o=' + OPTION + ' ' + UA_IP + '\r\n' + 's=LiveSesion\r\n')
        SDP += ('t=0\r\n' + 'm=audio ' + str(RTP_PORT) + ' RTP\r\n\r\n')
        print(Mess + SDP)
        my_socket.send(bytes(Mess + SDP, 'utf-8'))

    elif METHOD == "BYE":
        Mess = (METHOD + ' sip: ' + OPTION + ' SIP/2.0\r\n\r\n')
        print(Mess)
        my_socket.send(bytes(Mess, 'utf-8'))

    try:
        data = my_socket.recv(1024)
        Reply = data.decode('utf-8').split()
        print(Reply)
        if Reply[1] == '401':
            Mess += ("Authorization: Digest response = " + "213421" + '\r\n\r\n')
            my_socket.send(bytes(Mess, 'utf-8'))

        elif Reply[1] == '400':
            print(Reply)
            
        elif Reply[1] == "100" and Reply[4] == "180" and Reply[7] == "200":
            Mess = ('ACK' + ' sip: ' + OPTION + ' SIP/2.0\r\n\r\n')
            my_socket.send(bytes(Mess, 'utf-8'))

    except IndexError:
        print('Usuario Registrado')

    except ConnectionRefusedError:
        print('Error: No server listening at '
                            + REGPROXY_IP + ' port ' + str(REGPROXY_PORT))

