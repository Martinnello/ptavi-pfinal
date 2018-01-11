#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Servidor proxy SIP/UDP."""

import os
import sys
import json
import time
import socket
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
def write_Log(file, ip, port, mess_type, message):

    Time = '%Y%m%d%H%M%S'
    Date = str(time.strftime(Time, time.localtime(time.time())))
    message = message.replace('\r\n', ' ')

    if not os.path.exists (file):
        Log = open(file, 'w')
        Log.write(Date + mess_type + '\r\n')
    elif  mess_type == ' Starting... ' or mess_type == ' Finishing.':
        Log = open(file, 'a')
        Log.write(Date + mess_type + '\r\n')
    elif mess_type == ' Error: ':
        Log = open(file, 'a')
        Log.write(Date + mess_type + message + '\r\n')
    else:
        Log = open(file, 'a')
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


    """Resent the message from proxy to destiny waiting response"""
    def resent(self, ip, port, message, src_port, dst_port):

        try:

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as proxy_socket:
                proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                proxy_socket.connect((ip, port))
                proxy_socket.send(bytes(message, 'utf-8'))
                Mess_Type = ' Sent to '
                write_Log(LOG_FILE, ip, port, Mess_Type, message)

                data = proxy_socket.recv(1024)
                Recv = data.decode('utf-8')

                Mess_Type = ' Received from '
                write_Log(LOG_FILE, ip, port, Mess_Type, Recv)
                self.wfile.write(bytes(Recv, 'utf-8'))
                Mess_Type = ' Sent to '
                write_Log(LOG_FILE, src_port, dst_port, Mess_Type, Recv)


        except ConnectionRefusedError:
            Error =  ('No server listening at '
                      + ip + ' port ' + str(port))
            Mess_Type = ' Error: '
            write_Log(LOG_FILE, ip, port, Mess_Type, Error)
            sys.exit('Error: ' + Error)
            

    """Recieve & Sent SIP Messages."""
    def handle(self):
        
        self.create_database()

        while 1:
            Lines = self.rfile.read()
            if len(Lines) == 0:
                break

            Message = Lines.decode('utf-8')
            Source_Info = Message.split()
            Source_ip = self.client_address[0]
            Source_port = self.client_address[1]
            UA_name = Source_Info[1].split(':')[1]
            
            Mess_Type = ' Received from '
            write_Log(LOG_FILE, Source_ip, Source_port, Mess_Type, Message)

            METHODS = ['REGISTER', 'INVITE', 'ACK', 'BYE']
            METHOD = Source_Info[0]


            try:

                if METHOD == 'REGISTER':
                    
                    Time = time.time()
                    EXPIRES = Source_Info[4]
                    UAserver_PORT = Source_Info[1].split(':')[2]

                    try:
                        if int(EXPIRES) == 0:
                            del self.Users[UA_name]
                            Reply = 'SIP/2.0 200 OK\r\n\r\n'
                            self.wfile.write(bytes(Reply, 'utf-8'))
                            
                        else:
                            if len(Source_Info) == 5:
                                Reply = 'SIP/2.0 401 Unauthorized\r\n\r\n'
                                self.wfile.write(bytes(Reply, 'utf-8'))

                            if len(Source_Info) == 10:
                                self.Users[UA_name] = (Source_ip + ' ' 
                                                    + str(UAserver_PORT) + ' ' 
                                                    + str(Time) + ' ' + EXPIRES)

                                Reply = 'SIP/2.0 200 OK\r\n\r\n'
                                self.wfile.write(bytes(Reply, 'utf-8'))

                        self.database_update()
                        Mess_Type = ' Sent to '
                        write_Log(LOG_FILE, Source_ip, Source_port, Mess_Type, Reply)

                    except KeyError:
                        Reply = 'SIP/2.0 404 User Not Found\r\n\r\n'
                        self.wfile.write(bytes(Reply, 'utf-8'))
                        Mess_Type = ' Sent to '
                        write_Log(LOG_FILE, Source_ip, Source_port, Mess_Type, Reply)


                elif METHOD == 'INVITE':
                    
                    if UA_name in self.Users:
                        Destiny_Info = self.Users[UA_name].split()
                        Destiny_ip = Destiny_Info[0]
                        Destiny_port = int(Destiny_Info[1])

                        self.resent(Destiny_ip, Destiny_port, Message, Source_ip, Source_port)
                    
                    else:

                        Reply = 'SIP/2.0 404 User Not Found\r\n\r\n'
                        self.wfile.write(bytes(Reply, 'utf-8'))
                        Mess_Type = ' Sent to '
                        write_Log(LOG_FILE, Source_ip, Source_port, Mess_Type, Reply)

                elif METHOD == 'ACK':

                    if UA_name in self.Users:
                        Destiny_Info = self.Users[UA_name].split()
                        Destiny_ip = Destiny_Info[0]
                        Destiny_port = int(Destiny_Info[1])

                    try:
                        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as proxy_socket:
                            proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            proxy_socket.connect((Destiny_ip, Destiny_port))
                            proxy_socket.send(bytes(Message, 'utf-8'))
                            Mess_Type = ' Sent to '
                            write_Log(LOG_FILE, Destiny_ip, Destiny_port, Mess_Type, Message)

                    else:

                        Reply = 'SIP/2.0 404 User Not Found\r\n\r\n'
                        self.wfile.write(bytes(Reply, 'utf-8'))
                        Mess_Type = ' Sent to '
                        write_Log(LOG_FILE, Source_ip, Source_port, Mess_Type, Reply)
                
                elif METHOD == 'BYE':

                    if UA_name in self.Users:
                        Destiny_Info = self.Users[UA_name].split()
                        Destiny_ip = Destiny_Info[0]
                        Destiny_port = int(Destiny_Info[1])

                        self.resent(Destiny_ip, Destiny_port, Message, Source_ip, Source_port)

                    else:

                        Reply = 'SIP/2.0 404 User Not Found\r\n\r\n'
                        self.wfile.write(bytes(Reply, 'utf-8'))
                        Mess_Type = ' Sent to '
                        write_Log(LOG_FILE, Source_ip, Source_port, Mess_Type, Reply)

                elif METHOD not in METHODS:
                    Reply = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
                    self.wfile.write(bytes(Reply, 'utf-8'))
                    Mess_Type = ' Sent to '
                    write_Log(LOG_FILE, Source_ip, Source_port, Mess_Type, Reply)

            except ValueError:
                Reply = 'SIP/2.0 400 Bad Request\r\n\r\n'
                self.wfile.write(bytes(Reply, 'utf-8'))
                Mess_Type = ' Sent to '
                write_Log(LOG_FILE, Source_ip, Source_port, Mess_Type, Reply)

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
        write_Log(LOG_FILE, '','', ' Starting... ','')
        serv.serve_forever()

    except KeyboardInterrupt:
        write_Log(LOG_FILE, '','', ' Finishing.','')
        print("\n" + "Servidor finalizado")

