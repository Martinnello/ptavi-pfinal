#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Programa User Agent Cliente."""

import os
import sys
import socket
from uaserver import XmlHandler
from proxy_registrar import write_Log
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
    RTP_PORT = Config['rtpaudio_puerto']
    REGPROXY_IP = Config['regproxy_ip']
    REGPROXY_PORT = int(Config['regproxy_puerto'])
    LOG = Config['log_path']
    AUDIO = Config['audio_path']

    try:

        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((REGPROXY_IP, REGPROXY_PORT))
        write_Log(LOG, '','', ' Starting... ','Client')

        METHODS = ['REGISTER', 'INVITE', 'BYE']

        if METHOD == "REGISTER":
            Mess = (METHOD + ' sip:' + USER + ':' + str(UA_PORT))
            Mess += (' SIP/2.0\r\n' + 'Expires: ' + OPTION + '\r\n\r\n')
            print('Sent: \r\n' + Mess)
            my_socket.send(bytes(Mess, 'utf-8'))
            Mess_Type = ' Sent to '
            write_Log(LOG, REGPROXY_IP, REGPROXY_PORT, Mess_Type, Mess)

            try:
                data = my_socket.recv(1024)
            except ConnectionRefusedError:
                Error =  ('No server listening at '
                              + REGPROXY_IP + ' port ' + str(REGPROXY_PORT))
                write_Log(LOG, '', '', ' Error: ', Error)
                write_Log(LOG, '','', ' Finishing ','Client')
                sys.exit('Error: ' + Error)

            Recv = data.decode('utf-8')
            Reply = Recv.split()
            print('Received:\r\n' + Recv)
            Mess_Type = ' Received from '
            write_Log(LOG, REGPROXY_IP, REGPROXY_PORT, Mess_Type, Recv)

            if Reply[1] == '401':
                Nonce = Reply[-1].split('=')[1]
                Decryp = hashlib.sha1()
                Decryp.update(bytes(Nonce, 'utf-8'))
                Decryp.update(bytes(PASS, 'utf-8'))
                Decryp = Decryp.hexdigest()
                
                Mess += 'Authorization: Digest responce=' + Decryp
                my_socket.send(bytes(Mess, 'utf-8'))
                Mess_Type = ' Sent to '
                write_Log(LOG, REGPROXY_IP, REGPROXY_PORT, Mess_Type, Mess)

                data = my_socket.recv(1024)
                Recv = data.decode('utf-8')
                Mess_Type = ' Received from '
                write_Log(LOG, REGPROXY_IP, REGPROXY_PORT, Mess_Type, Recv)


        elif METHOD == "INVITE":
            Mess = (METHOD + ' sip:' + OPTION + ' SIP/2.0\r\n')
            SDP = ("Content-Type: application/sdp\r\n\r\n" + 'v=0\r\n')
            SDP += ('o=' + USER + ' ' + UA_IP + '\r\n' + 's=LiveSesion\r\n')
            SDP += ('t=0\r\n' + 'm=audio ' + RTP_PORT + ' RTP\r\n\r\n')
            Mess += SDP
            my_socket.send(bytes(Mess, 'utf-8'))
            Mess_Type = ' Sent to '
            write_Log(LOG, REGPROXY_IP, REGPROXY_PORT, Mess_Type, Mess)
            print('Sent: \r\n' + Mess)

            try:
                data = my_socket.recv(1024)
            except ConnectionRefusedError:
                Error =  ('No server listening at '
                              + REGPROXY_IP + ' port ' + str(REGPROXY_PORT))
                write_Log(LOG, '', '', ' Error: ', Error)
                write_Log(LOG, '','', ' Finishing ','Client')
                sys.exit('Error: ' + Error)

            Recv = data.decode('utf-8')
            Reply = Recv.split()
            print('Received:\r\n' + Recv)
            Mess_Type = ' Received from '
            write_Log(LOG, REGPROXY_IP, REGPROXY_PORT, Mess_Type, Recv)

            if Reply[1] == "100" and Reply[4] == "180" and Reply[7] == "200":
                Mess = ('ACK' + ' sip:' + OPTION + ' SIP/2.0\r\n\r\n')
                my_socket.send(bytes(Mess, 'utf-8'))
                Mess_Type = ' Sent to '
                write_Log(LOG, REGPROXY_IP, REGPROXY_PORT, Mess_Type, Mess)
                
                Exe = './mp32rtp -i 127.0.0.1 -p ' + RTP_PORT + ' < ' + AUDIO
                print("Ejecutando...   ", Exe)
                os.system(Exe)
                Mess_Type = ' Envio RTP...'
                write_Log(LOG, '', '', Mess_Type, '')

            elif Reply[1] == '404':
                write_Log(LOG, '', '', ' Error: ', Recv)
                write_Log(LOG, '','', ' Finishing ','Client')
                sys.exit('Error: User Not Found')

        elif METHOD == "BYE":
            Mess = (METHOD + ' sip:' + OPTION + ' SIP/2.0\r\n\r\n')
            print('Sent: \r\n' + Mess)
            my_socket.send(bytes(Mess, 'utf-8'))
            Mess_Type = ' Sent to '
            write_Log(LOG, REGPROXY_IP, REGPROXY_PORT, Mess_Type, Mess)

            try:
                data = my_socket.recv(1024)
            except ConnectionRefusedError:
                Error =  ('No server listening at '
                              + REGPROXY_IP + ' port ' + str(REGPROXY_PORT))
                write_Log(LOG, '', '', ' Error: ', Error)
                write_Log(LOG, '','', ' Finishing ','Client')
                sys.exit('Error: ' + Error)

            Recv = data.decode('utf-8')
            Reply = Recv.split()
            print('Received:\r\n' + Recv)
            Mess_Type = ' Received from '
            write_Log(LOG, REGPROXY_IP, REGPROXY_PORT, Mess_Type, Recv)

        elif METHOD not in METHODS:
            print("Method not allowed")
            sys.exit("Usage: python3 uaclient.py config method option")


        write_Log(LOG, '','', ' Finishing ','Client')

    except ConnectionRefusedError:
        Error =  ('No server listening at '
                  + ip + ' port ' + str(port))
        Mess_Type = ' Error: '
        write_Log(LOG, ip, port, Mess_Type, Error)
        sys.exit('Error: ' + Error)

        