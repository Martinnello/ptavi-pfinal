#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Servidor de eco en UDP simple."""

import os
import sys
import socketserver
from proxy_registrar import write_Log
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


class XmlHandler(ContentHandler):
    """Handler para manejar configuración en xml."""

    def __init__(self):
        """Inicia el manejador."""
        self.Atributos = {}
        self.Dicc_Xml = {"account": ['username', 'passwd'],
                         "uaserver": ['ip', 'puerto'],
                         "rtpaudio": ['puerto'],
                         "regproxy": ['ip', 'puerto'],
                         "log": ['path'],
                         "audio": ['path']}

    def startElement(self, name, attrs):
        """Añade atributos a la lista."""
        if name in self.Dicc_Xml:
            for atr in self.Dicc_Xml[name]:
                self.Atributos[name + "_" + atr] = attrs.get(atr, "")

    def get_tags(self):
        """Devuelve la lista de atributos."""
        return (self.Atributos)


class EchoHandler(socketserver.DatagramRequestHandler):
    """Client handler requests."""

    RTP_Listen = []

    def handle(self):
        """Recieve & Sent SIP Messages."""
        while 1:
            Lines = self.rfile.read()
            if len(Lines) == 0:
                break

            Message = Lines.decode('utf-8')
            Info = Message.split()
            METHODS = ['INVITE', 'ACK', 'BYE']
            METHOD = Info[0]
            Source_ip = self.client_address[0]
            Source_port = self.client_address[1]
            print('Received:\r\n' + Message)
            Mess_Type = ' Received from '
            write_Log(LOG, Source_ip, Source_port, Mess_Type, Message)

            if METHOD == 'INVITE':
                self.RTP_Listen.append(Info[-2])

                Call = 'SIP/2.0 100 Trying\r\n\r\n'
                Call += 'SIP/2.0 180 Ringing\r\n\r\n'
                Call += 'SIP/2.0 200 OK\r\n\r\n'
                SDP = ("Content-Type: application/sdp\r\n\r\n")
                SDP += ('v=0\r\n' + "o=" + USER + ' ' + UA_IP + '\r\n')
                SDP += ('s=LiveSesion\r\n' + 't=0\r\n' + 'm=audio ')
                SDP += RTP_PORT + ' RTP\r\n\r\n'
                Call += SDP

                self.wfile.write(bytes(Call, 'utf-8'))
                Mess_Type = ' Sent to '
                write_Log(LOG, REGPROXY_IP, REGPROXY_PORT, Mess_Type, Call)

            elif METHOD == 'ACK':
                Exe = './mp32rtp -i 127.0.0.1 -p ' + self.RTP_Listen[0]
                Exe += ' < ' + AUDIO
                print("Ejecutando...   ", Exe)
                os.system(Exe)

                Cvlc = 'cvlc rtp://@' + '127.0.0.1' + ':' + self.RTP_Listen[0]
                print("Ejecutando...   ", Cvlc)
                os.system(Cvlc)

                Mess_Type = ' Envio RTP...'
                write_Log(LOG, '', '', Mess_Type, '')

            elif METHOD == 'BYE':
                Reply = 'SIP/2.0 200 OK\r\n\r\n'
                self.wfile.write(bytes(Reply, 'utf-8'))
                Mess_Type = ' Sent to '
                write_Log(LOG, REGPROXY_IP, REGPROXY_PORT, Mess_Type, Reply)

            elif METHOD not in METHODS:
                Reply = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
                self.wfile.write(bytes(Reply, 'utf-8'))
                Mess_Type = ' Sent to '
                write_Log(LOG, REGPROXY_IP, REGPROXY_PORT, Mess_Type, Reply)
            else:
                Reply = 'SIP/2.0 400 Bad Request\r\n\r\n'
                self.wfile.write(bytes(Reply, 'utf-8'))
                Mess_Type = ' Sent to '
                write_Log(LOG, REGPROXY_IP, REGPROXY_PORT, Mess_Type, Reply)


if __name__ == "__main__":

    try:
        CONFIG_FILE = sys.argv[1]
        parser = make_parser()
        Handler = XmlHandler()
        parser.setContentHandler(Handler)
        parser.parse(open(CONFIG_FILE))
        Config = Handler.get_tags()

    except FileNotFoundError:
        sys.exit('  File not found!')
    except IndexError:
        sys.exit("  Usage: python3 uaserver.py config")

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

        serv = socketserver.UDPServer((UA_IP, UA_PORT), EchoHandler)
        print("Listening...")
        write_Log(LOG, '', '', ' Starting... ', 'UA_Server')
        serv.serve_forever()

    except KeyboardInterrupt:
        print("\n" + "Servidor finalizado")
        write_Log(LOG, '', '', ' Finishing ', 'UA_Server')
