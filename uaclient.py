#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Programa cliente que abre un socket a un servidor."""

import sys
import socket
from xml.sax import make_parser
from xml.sax.handler import ContentHandler


try:
    Config_File = sys.argv[1]
    METHOD = str.upper(sys.argv[2])
    OPTION = sys.argv[3]
#except FileNotFoundError:
#    sys.exit("   File not found!")
except IndexError:
    sys.exit(" Usage: python uaclient.py config method opcion ")


class XmlHandler(ContentHandler):    # Handler para manejar configuración en xml

    def __init__(self):
        self.List = []
        self.Dicc_Xml = {"account": ['username', 'passwd'],
                         "uaserver": ['ip', 'puerto'],
                         "rtpaudio": ['puerto'],
                         "regproxy": ['ip', 'puerto'],
                         "log": ['path'],
                         "audio": ['path'],}

    def startElement(self, name, attrs):      # Añade atributos a la lista

        if name in self.Dicc_Xml:
            Dicc_Atr = {}

            for atr in self.Dicc_Xml[name]:
                Dicc_Atr[atr] = attrs.get(atr, "")

            self.List.append([name, Dicc_Atr])

    def get_tags(self):                     # Devuelve la lista de atributos
            return (self.List)

if __name__ == "__main__":

    parser = make_parser()
    cHandler = XmlHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(Config_File))
    Config = cHandler.get_tags()
    print(Config)

    user = Config [0][1]['username']
    print(user)
    password = Config [0][1]['passwd']
    print(password)
    ua_ip = Config [1][1]['ip']
    print(ua_ip)
    ua_port = Config [1][1]['puerto']
    print(ua_port)
    rtp_port = Config [2][1]['puerto']
    print(rtp_port)
    proxy_ip = Config [3][1]['ip']
    print(proxy_ip)
    proxy_port = Config [3][1]['puerto']
    print(proxy_port)
    log_path = Config [4][1]['path']
    print(log_path)
    mp3_path = Config [5][1]['path']
    print(mp3_path)




















