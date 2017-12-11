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
        self.Dicc_Xml = {"server": ['name', 'ip', 'puerto'],
                         "database": ['path', 'passwdpath'],
                         "log": ['path']}

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
            elif METHOD == 'ACK':
                Exe = './mp32rtp -i 127.0.0.1 -p 23032 < ' + AUDIO_FILE
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
        sys.exit("  Usage: python3 proxy_registrar.py config")

    NAME = Config['server_name']
    REGPROXY_IP = Config['server_ip']
    REGPROXY_PORT = Config['server_puerto']
    DATABASE = Config['database_path']
    PASS = Config['database_passwdpath']
    LOG = Config['log_path']

    try:

        serv = socketserver.UDPServer((REGPROXY_IP, REGPROXY_PORT), EchoHandler)
        print("Server " + + "listening at port " + str(REGPROXY_PORT) + '...')
        serv.serve_forever()

    except KeyboardInterrupt:
        print("\n" + "Servidor finalizado")

