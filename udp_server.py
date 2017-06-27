# !/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import socket
import errno
import logging
from tornado import process
from tornado.ioloop import IOLoop
from tornado.platform.auto import set_close_exec

__author__ = "Neo"


def add_accept_handler(sock, callback, io_loop=None):
    if io_loop is None:
        io_loop = IOLoop.instance()

    def accept_handler(fd, events):
        while True:
            try:
                data, address = sock.recvfrom(4096)
            except socket.error as err:
                if err.args[0] in (errno.EWOULDBLOCK, errno.EAGAIN):
                    return

                raise

            callback(data, address)

    io_loop.add_handler(sock.fileno(), accept_handler, IOLoop.READ)


def bind_sockets(port, address=None, family=socket.AF_UNSPEC, backlog=25):
    sockets = []
    if address == "":
        address = None

    flags = socket.AI_PASSIVE
    if hasattr(socket, "AI_ADDRCONFIG"):
        flags |= socket.AI_ADDRCONFIG

    for res in set(socket.getaddrinfo(address, port, family, socket.SOCK_DGRAM, 0, flags)):
        af, socktype, proto, canonname, sockaddr = res
        sock = socket.socket(af, socktype, proto)
        set_close_exec(sock.fileno())

        if os.name != 'nt':
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if af == socket.AF_INET6:
            if hasattr(socket, "IPPROTO_IPV6"):
                sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)

        sock.setblocking(0)
        sock.bind(sockaddr)
        sockets.append(sock)

    return sockets


class UDPServer(object):
    def __init__(self, io_loop=None):
        self.io_loop = io_loop

        # fd -> socket object
        self._sockets = {}
        self._pending_sockets = []
        self._started = False

    def add_sockets(self, sockets):
        if self.io_loop is None:
            self.io_loop = IOLoop.instance()

        for sock in sockets:
            self._sockets[sock.fileno()] = sock
            add_accept_handler(sock, self._on_receive, io_loop=self.io_loop)

    def bind(self, port, address=None, family=socket.AF_UNSPEC, backlog=25):
        sockets = bind_sockets(port, address=address, family=family, backlog=backlog)

        if self._started:
            self.add_sockets(sockets)
        else:
            self._pending_sockets.extend(sockets)

    def start(self, num_processes=1):
        assert not self._started
        self._started = True

        if num_processes != 1:
            process.fork_processes(num_processes)

        sockets = self._pending_sockets
        self._pending_sockets = []
        self.add_sockets(sockets)

    def stop(self):
        for fd, sock in self._sockets.items():
            self.io_loop.remove_handler(fd)
            sock.close()

    @staticmethod
    def _on_receive(data, address):
        try:
            logging.info(data.decode())
        except:
            print("from {} - {}".format(address, data))
