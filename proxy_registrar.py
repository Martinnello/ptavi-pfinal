#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Servidor proxy SIP/UDP."""

import os
import sys
import json
import time
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

    """Añade los atributos al diccionario."""
    def startElement(self, name, attrs):
        if name in self.Dicc_Xml:
            for atr in self.Dicc_Xml[name]:
                self.Atributos[name + "_" + atr] = attrs.get(atr, "")

    """Devuelve los atributos del xml."""
    def get_tags(self):
            return (self.Atributos)


"""Add Log Comments"""
def Write_Log(ip, port, mess_type, message):

    Time = '%Y%m%d%H%M%S'
    Date = str(time.strftime(Time, time.localtime(time.time())))
    message = message.replace('\r\n', ' ')

    if not os.path.exists (LOG_FILE):
        Log = open(LOG_FILE, 'w')
        Log.write(Date + mess_type + '\r\n')
    elif  mess_type == ' Starting... ' or mess_type == ' Finishing.':
        Log = open(LOG_FILE, 'a')
        Log.write(Date + mess_type + '\r\n')
    else:
        Log = open(LOG_FILE, 'a')
        Log.write(Date + mess_type + ip + ':' + str(port) 
                       + ': ' + message + '\r\n')


"""Client handler requests."""
class EchoHandler(socketserver.DatagramRequestHandler):
    
    Users = {}

    """See if database.json exist."""
    def create_database(self):
        try:
            with open(DATABASE, 'r') as jsonfile:
                self.Users = json.load(jsonfile)
        except FileNotFoundError:
            pass


    """Make/Update database.json file."""
    def database_update(self):
        with open(DATABASE, 'w') as jsonfile:
            json.dump(self.Users, jsonfile, indent = 2)
            

    """Recieve & Sent SIP Messages."""
    def handle(self):
        
        self.create_database()

        while 1:
            Lines = self.rfile.read()
            if len(Lines) == 0:
                break

            Message = Lines.decode('utf-8')
            Info = Message.split()
            UA_ip = self.client_address[0]
            UA_port = self.client_address[1]
            print(Info)
            Mess_Type = ' Received from '
            Write_Log(UA_ip, UA_port, Mess_Type, Message)

            METHODS = ['REGISTER', 'INVITE', 'ACK', 'BYE']
            METHOD = Info[0]

            if METHOD == 'REGISTER':
                UA_name = Info[1].split(':')[1]
                Time = time.time()
                EXPIRES = Info[4]

                try:
                    if int(EXPIRES) == 0:
                        del self.Users[UA_name]
                        Reply = 'SIP/2.0 200 OK\r\n\r\n'
                        self.wfile.write(bytes(Reply, 'utf-8'))
                        
                    else:
                        if len(Info) == 5:
                            Reply = 'SIP/2.0 401 Unauthorized\r\n\r\n'
                            self.wfile.write(bytes(Reply, 'utf-8'))

                        if len(Info) == 10:
                            self.Users[UA_name] = (UA_ip + ' ' + str(UA_port) 
                                            + ' ' + str(Time) + ' ' + EXPIRES)

                            Reply = 'SIP/2.0 200 OK\r\n\r\n'
                            self.wfile.write(bytes(Reply, 'utf-8'))

                    self.database_update()
                    Mess_Type = ' Sent to '
                    Write_Log(UA_ip, UA_port, Mess_Type, Reply)

                except KeyError:
                    self.wfile.write(b'SIP/2.0 404 User Not Found\r\n\r\n')


            elif METHOD == 'INVITE':
                self.wfile.write(b'SIP/2.0 100 Trying\r\n\r\n')
                self.wfile.write(b'SIP/2.0 180 Ringing\r\n\r\n')
                self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
                Mess = (METHOD + ' sip:' + OPTION + ' SIP/2.0\r\n' + 'o=')
                SDP = ("Content-Type: application/sdp\r\n\r\n" + 'v= 0\r\n')
                SDP += (OPTION + ' ' + UA_IP + '\r\n' + 's=LiveSesion\r\n')
                SDP += ('t=0\r\n' + 'm=audio ' + str(RTP_PORT) + ' RTP\r\n\r\n')
                print(Mess + SDP)
                my_socket.send(bytes(Mess + SDP, 'utf-8'))

            elif METHOD == 'ACK':
                my_socket.send(bytes(Message, 'utf-8'))
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
    REGPROXY_PORT = int(Config['server_puerto'])
    DATABASE = Config['database_path']
    PASS = Config['database_passwdpath']
    LOG_FILE = Config['log_path']

    try:

        serv = socketserver.UDPServer((REGPROXY_IP, REGPROXY_PORT), EchoHandler)
        print("Server listening at port " + str(REGPROXY_PORT) + '...')
        Write_Log('','', ' Starting... ','')
        serv.serve_forever()

    except KeyboardInterrupt:
        Write_Log('','', ' Finishing.','')
        print("\n" + "Servidor finalizado")

