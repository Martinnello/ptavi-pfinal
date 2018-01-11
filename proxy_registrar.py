#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Servidor proxy SIP/UDP."""

import os
import sys
import json
import time
import random
import hashlib
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
        Log.write(Date + mess_type + message + '\r\n')
    elif  mess_type == ' Starting... ' or mess_type == ' Finishing ':
        Log = open(file, 'a')
        Log.write(Date + mess_type + message + '\r\n')
    elif mess_type == ' Error: ':
        Log = open(file, 'a')
        Log.write(Date + mess_type + message + '\r\n')
    elif mess_type == ' Envio RTP...':
        Log = open(file, 'a')
        Log.write(Date + mess_type + '\r\n')
    else:
        Log = open(file, 'a')
        Log.write(Date + mess_type + ip + ':' + str(port) 
                       + ': ' + message + '\r\n')


"""Client handler requests."""
class EchoHandler(socketserver.DatagramRequestHandler):
    
    Users = {}
    Chain = {} 
    Nonce = []

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


    def passwords(self):
        try:
            with open(PASS, 'r') as jsonfile:
                self.Chain = json.load(jsonfile)
        except FileNotFoundError:
            sys.exit('File Not Found!')


    """Resent the message from proxy to Dst waiting response"""
    def resent(self, ip, port, message, src_port, dst_port):

        try:

            px_sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            px_sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            px_sck.connect((ip, port))
            px_sck.send(bytes(message, 'utf-8'))
            Mess_Type = ' Sent to '
            write_Log(LOG, ip, port, Mess_Type, message)

            data = px_sck.recv(1024)
            Recv = data.decode('utf-8')

            Mess_Type = ' Received from '
            write_Log(LOG, ip, port, Mess_Type, Recv)
            self.wfile.write(bytes(Recv, 'utf-8'))
            Mess_Type = ' Sent to '
            write_Log(LOG, src_port, dst_port, Mess_Type, Recv)


        except ConnectionRefusedError:
            Error =  ('No server listening at '
                      + ip + ' port ' + str(port))
            Mess_Type = ' Error: '
            write_Log(LOG, ip, port, Mess_Type, Error)
            write_Log(LOG, '','', ' Finishing ','Proxy')
            sys.exit('Error: ' + Error)
            

    """Recieve & Sent SIP Messages."""
    def handle(self):
        
        self.create_database()
        self.passwords()
        Time = time.time()
        Del_List = []

        for user in self.Users:
            Date = int(self.Users[user][-1])
            if Date <= Time:
                print(user)
                Del_List.append(user)

        for user in Del_List:
            del self.Users[user]

        self.database_update()

        while 1:
            Lines = self.rfile.read()
            if len(Lines) == 0:
                break

            Message = Lines.decode('utf-8')
            Src_Info = Message.split()
            Src_ip = self.client_address[0]
            Src_port = self.client_address[1]
            UA_name = Src_Info[1].split(':')[1]
            print(Src_Info)
            
            Mess_Type = ' Received from '
            write_Log(LOG, Src_ip, Src_port, Mess_Type, Message)
            print('Received:\r\n' + Message)

            METHODS = ['REGISTER', 'INVITE', 'ACK', 'BYE']
            METHOD = Src_Info[0]

            if METHOD == 'REGISTER':
                
                EXPIRES = (int(Src_Info[4]) + Time)
                UAserver_PORT = Src_Info[1].split(':')[2]

                if Src_Info[4] == 0:
                    del self.Users[UA_name]
                    Reply = 'SIP/2.0 200 OK\r\n\r\n'
                    self.wfile.write(bytes(Reply, 'utf-8'))
                        
                else:
                    if len(Src_Info) == 5:
                        self.Nonce.append(str(random.randint(0000,9999)))
                        Reply = 'SIP/2.0 401 Unauthorized\r\n'
                        Reply += 'WWW-Authenticate: Digest nonce='
                        Reply += self.Nonce[0] + '\r\n\r\n'
                        self.wfile.write(bytes(Reply, 'utf-8'))
                        Mess_Type = ' Sent to '
                        write_Log(LOG, Src_ip, Src_port, Mess_Type, Reply)

                    elif len(Src_Info) == 8:
                        Password = self.Chain[UA_name]
                        Encryp = hashlib.sha1()
                        Encryp.update(bytes(self.Nonce[0], 'utf-8'))
                        Encryp.update(bytes(Password, 'utf-8'))
                        Encryp = Encryp.hexdigest()
                        Key = Src_Info[-1].split("=")[1]
                        if Encryp == Key:
                            self.Users[UA_name] = (Src_ip + ' ' 
                                            + str(UAserver_PORT) + ' ' 
                                            + str(Time) + ' ' + str(EXPIRES))

                            Reply = 'SIP/2.0 200 OK\r\n\r\n'
                            self.wfile.write(bytes(Reply, 'utf-8'))
                            Mess_Type = ' Sent to '
                            write_Log(LOG, Src_ip, Src_port, Mess_Type, Reply)

                self.database_update()

            elif METHOD == 'INVITE':
                
                if UA_name in self.Users:
                    Dst_Info = self.Users[UA_name].split()
                    Dst_ip = Dst_Info[0]
                    Dst_port = int(Dst_Info[1])

                    self.resent(Dst_ip, Dst_port, Message, Src_ip, Src_port)
                    print('Message resent\r\n')
                
                else:

                    Reply = 'SIP/2.0 404 User Not Found\r\n\r\n'
                    self.wfile.write(bytes(Reply, 'utf-8'))
                    Mess_Type = ' Sent to '
                    write_Log(LOG, Src_ip, Src_port, Mess_Type, Reply)

            elif METHOD == 'ACK':

                if UA_name in self.Users:
                    Dst_Info = self.Users[UA_name].split()
                    Dst_ip = Dst_Info[0]
                    Dst_port = int(Dst_Info[1])

                    px_sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    px_sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    px_sck.connect((Dst_ip, Dst_port))
                    px_sck.send(bytes(Message, 'utf-8'))

                    Mess_Type = ' Sent to '
                    write_Log(LOG, Dst_ip, Dst_port, Mess_Type, Message)
                    print('Message resent\r\n')

                else:

                    Reply = 'SIP/2.0 404 User Not Found\r\n\r\n'
                    self.wfile.write(bytes(Reply, 'utf-8'))
                    Mess_Type = ' Sent to '
                    write_Log(LOG, Src_ip, Src_port, Mess_Type, Reply)
            
            elif METHOD == 'BYE':

                if UA_name in self.Users:
                    Dst_Info = self.Users[UA_name].split()
                    Dst_ip = Dst_Info[0]
                    Dst_port = int(Dst_Info[1])

                    self.resent(Dst_ip, Dst_port, Message, Src_ip, Src_port)
                    print('Message resent\r\n')

                else:

                    Reply = 'SIP/2.0 404 User Not Found\r\n\r\n'
                    self.wfile.write(bytes(Reply, 'utf-8'))
                    Mess_Type = ' Sent to '
                    write_Log(LOG, Src_ip, Src_port, Mess_Type, Reply)

            elif METHOD not in METHODS:
                Reply = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
                self.wfile.write(bytes(Reply, 'utf-8'))
                Mess_Type = ' Sent to '
                write_Log(LOG, Src_ip, Src_port, Mess_Type, Reply)

            else:
                Reply = 'SIP/2.0 400 Bad Request\r\n\r\n'
                self.wfile.write(bytes(Reply, 'utf-8'))
                Mess_Type = ' Sent to '
                write_Log(LOG, Src_ip, Src_port, Mess_Type, Reply)


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
    LOG = Config['log_path']

    try:

        serv = socketserver.UDPServer((REGPROXY_IP, REGPROXY_PORT), EchoHandler)
        print("Server listening at port " + str(REGPROXY_PORT) + '...')
        write_Log(LOG, '','', ' Starting... ','Proxy')
        serv.serve_forever()

    except KeyboardInterrupt:
        write_Log(LOG, '','', ' Finishing ','Proxy')
        print("\n" + "Servidor finalizado")
