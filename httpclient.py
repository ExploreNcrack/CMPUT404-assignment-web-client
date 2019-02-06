#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse

bufferSize = 1024
defaultHttpPort = 80

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class HTTPClient(object):
    def connect(self, URL_components):
        """
        input:  a urlparsed dictionary
        return: the host that is connected to
        """
        # if there protocol scheme is given (not start with "http://")
        host = URL_components.hostname 
        if URL_components.hostname == None:
            # if the protocol scheme is not given 
            host = URL_components.path.split("/")[0]
        # if port is given
        port = URL_components.port
        if URL_components.port == None:
            # if port not given use default http port 80
            port = defaultHttpPort
        # catch any socket problem just in case
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
        except:
            print("Connection error => Could not resolve host: {host} port: {port}".format(host=host,port=port))
            sys.exit(1)
        print("Successfully connect to: {host}:{port}...".format(host=host, port=port))
        return host

    def get_code(self, data):
        """
        input:  http response data
        return: response status code
        """
        begin = data.find("HTTP/")
        if begin != -1:
            return int(data[begin+9:12])
        else:
            return 500
        
    def get_first_line_of_header(self, data):
        """
        Not used in this assignment
        input:  http response data
        return: the first line of response header
        """
        begin = data.find("HTTP/")
        index = begin
        header = ""
        while True:
            if data[index] == "\r" or data[index] == "\n":
                break
            header += data[index]
            index += 1
        return header

    def get_headers(self, data):
        """
        input:  http response data
        return: the response header
        """
        separatePoint = data.find("\r\n\r\n")
        if separatePoint == -1:
            separatePoint = data.find("\n\n")
        return data[0:separatePoint]


    def get_body(self, data):
        """
        input:  http response data
        return: the response body(content)
        """
        skipLength = 4
        separatePoint = data.find("\r\n\r\n")
        if separatePoint == -1:
            separatePoint = data.find("\n\n")
            skipLength = 2
        return data[separatePoint+skipLength:]
    
    def sendall(self, data):
        """
        input: data need to be sent through socket to the another end host
        send all data that is given
        """
        self.socket.sendall(data.encode('utf-8'))
        
    def close(self):
        """
        close socket connection
        """
        self.socket.close()

    def recvall(self, sock):
        """
        input: socket 
        read   everything from the socket
        """
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer

    def GETRequestHeader(self, host, URL_components, HttpVersion="HTTP/1.1", charset="UTF-8", connection="close", userAgent=""):
        """
        input: all the necessary param for a GET request header (allow customize)
        generate a GET request header string
        """
        path = ""
        if host == URL_components.path.split("/")[0]:
            # no protocol scheme  eg: "www.google.com"
            length = 0
            for i in URL_components.path.split("/"):
                if len(i) != 0 :
                    length += 1
            if length == 1:
                # requested for root
                path = "/"
            else: 
                parts = URL_components.path.split("/")
                path = URL_components.path[len(parts[0]):]
        else:
            if URL_components.path == "":
                path = "/"
            else:
                path = URL_components.path
        if userAgent == "":
            userAgent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko)"

        return  "GET {path} {HttpVersion}\r\n"\
                "Host: {host}\r\n"\
                "Accept-Charset: {charset}\r\n"\
                "User-Agent: {userAgent}\r\n"\
                "Connection: {connection}\r\n\r\n".format(path=path, HttpVersion=HttpVersion, host=host, charset=charset, userAgent=userAgent, connection=connection)


    def readResponse(self, socket):
        """
        input:  socket 
        process the data from socket
        """
        # recieve all data from the socket
        fullData = self.recvall(socket)
        # make a copy of the data
        fullDataOrigin = fullData
        try: 
            # try using UTF-8 to decode
            fullData = fullData.decode()
        except:
            # if fail, then look for the charset format to decode
            fullData = str(fullData)
            # look for the encode format in the response header
            charsetBegin = fullData.find("charset=")
            index = charsetBegin + 8
            charset = ""
            while True:
                if fullData[index] == '\\':
                    break
                charset += fullData[index]
                index += 1
            # decode 
            fullData = fullDataOrigin.decode(charset)
        return fullData
        

    def GET(self, url, args=None):
        """
        input: url
        Handling GET request to given url
        """
        # url parsing
        URL_components = urllib.parse.urlparse(url)
        # TCP connection
        host = self.connect(URL_components)        
        # send GET request
        payload = self.GETRequestHeader(host, URL_components)
        # print(payload)
        # send
        self.sendall(payload)
        # read response
        fullData = self.readResponse(self.socket)
        # get code
        code = self.get_code(fullData)
        # get header
        header = self.get_headers(fullData)
        # get body
        body = self.get_body(fullData)
        # close the connection before return
        self.close()
        print("HTTP Response:")
        # print(fullData)
        print("Response status code: "+str(code))
        print("Response body:\n"+body)
        # print(header)
        # print(len(header))
        return HTTPResponse(code, body)

    def POST(self, url, args=None):
        code = 500
        body = ""
        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
