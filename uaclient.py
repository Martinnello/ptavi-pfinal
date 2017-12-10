#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Programa User Agent Cliente."""

import sys
import socket
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


try:
    CONFIG_FILE = sys.argv[1]
    METHOD = str.upper(sys.argv[2])
    OPTION = sys.argv[3]
#except FileNotFoundError:
#    sys.exit("   File not found!")
except IndexError:
    sys.exit(" Usage: python uaclient.py config method opcion ")


"""Handler para manejar configuración en xml."""
class XmlHandler(ContentHandler):    

    def __init__(self):
        self.List = []
        self.Dicc_Xml = {"account": ['username', 'passwd'],
                         "uaserver": ['ip', 'puerto'],
                         "rtpaudio": ['puerto'],
                         "regproxy": ['ip', 'puerto'],
                         "log": ['path'],
                         "audio": ['path'],}

    """Añade atributos a la lista."""
    def startElement(self, name, attrs):

        if name in self.Dicc_Xml:
            Dicc_Atr = {}

            for atr in self.Dicc_Xml[name]:
                Dicc_Atr[atr] = attrs.get(atr, "")

            self.List.append([name, Dicc_Atr])

    """Devuelve la lista de atributos."""
    def get_tags(self):
            return (self.List)


if __name__ == "__main__":

    parser = make_parser()
    Handler = XmlHandler()
    parser.setContentHandler(Handler)
    parser.parse(open(CONFIG_FILE))
    Config = Handler.get_tags()

    user = Config [0][1]['username']
    password = Config [0][1]['passwd']
    ua_ip = Config [1][1]['ip']
    ua_port = Config [1][1]['puerto']
    rtp_port = Config [2][1]['puerto']
    proxy_ip = Config [3][1]['ip']
    proxy_port = Config [3][1]['puerto']
    log_path = Config [4][1]['path']
    mp3_path = Config [5][1]['path']


with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((proxy_ip, proxy_port))

    if METHOD == "REGISTER"
    if METHOD == "INVITE"
    if METHOD == "BYE"

    my_socket.send(bytes(METHOD + Mess, 'utf-8') + b'\r\n')


    data = my_socket.recv(1024)
    Reply = data.decode('utf-8').split()

    if METHOD == "REGISTER"
    if METHOD == "INVITE"
    if METHOD == "BYE"



















