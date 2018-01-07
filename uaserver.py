#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Servidor de eco en UDP simple."""

import os
import sys
import socketserver
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


"""Handler para manejar configuración en xml."""
class XmlHandler(ContentHandler):    

    def __init__(self):
        self.Atributos = {}
        self.Dicc_Xml = {"account": ['username', 'passwd'],
                         "uaserver": ['ip', 'puerto'],
                         "rtpaudio": ['puerto'],
                         "regproxy": ['ip', 'puerto'],
                         "log": ['path'],
                         "audio": ['path']}

    """Añade atributos a la lista."""
    def startElement(self, name, attrs):

        if name in self.Dicc_Xml:
            for atr in self.Dicc_Xml[name]:
                self.Atributos[name + "_" + atr] = attrs.get(atr, "")

    """Devuelve la lista de atributos."""
    def get_tags(self):
            return (self.Atributos)


class EchoHandler(socketserver.DatagramRequestHandler):
    """Client handler requests."""

    def handle(self):
        """Recieve & Sent SIP Messages."""
        while 1:
            Lines = self.rfile.read()
            if len(Lines) == 0:
                break

            Info = Lines.decode('utf-8').split()
            METHODS = ['REGISTER', 'INVITE', 'ACK', 'BYE']
            METHOD = Info[0]
            print(Info)

            if METHOD == 'REGISTER':
                self.wfile.write(b'SIP/2.0 401 Unauthorized\r\n\r\n')
            elif METHOD == 'INVITE':

                self.wfile.write(b'SIP/2.0 100 Trying\r\n\r\n')
                self.wfile.write(b'SIP/2.0 180 Ringing\r\n\r\n')
                self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
                UA_name = Info[1].split(':')[1]
               
                SDP = ("Content-Type: application/sdp\r\n\r\n")
                SDP += ('v=0\r\n' + "o=" + USER + ' ' + UA_IP + '\r\n')
                SDP += ('s=LiveSesion\r\n' + 't=0\r\n' + 'm=audio ')
                SDP += RTP_PORT + ' RTP\r\n\r\n'
                self.wfile.write(bytes(SDP, 'utf-8'))

            elif METHOD == 'ACK':
                Exe = './mp32rtp -i 127.0.0.1 -p ' + RTP_PORT + ' < ' + AUDIO_FILE
                print("Ejecutando...   ", Exe)
                os.system(Exe)
            elif METHOD == 'BYE':
                self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
            elif METHOD not in METHODS:
                self.wfile.write(b'SIP/2.0 405 Method Not Allowed\r\n\r\n')
            else:
                self.wfile.write(b'SIP/2.0 400 Bad Request\r\n\r\n')


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
    AUDIO_FILE = Config['audio_path'] 

    try:

        serv = socketserver.UDPServer((UA_IP, UA_PORT), EchoHandler)
        print("Listening...")
        serv.serve_forever()

    except KeyboardInterrupt:
        print("\n" + "Servidor finalizado")
