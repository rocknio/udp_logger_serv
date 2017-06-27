# !/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import logging.handlers
import tornado
from tornado import ioloop
from udp_server import UDPServer
from tornado.options import define, options


__author__ = "Neo"

define('port', default=10001, type=int, help='listen port')
define('log', default='udp_log.log', type=str, help='log file name')


def init_log_handler():
    try:
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        stream_handler = logging.StreamHandler()
        file_handler = logging.handlers.RotatingFileHandler(options.log, maxBytes=30 * 1024 * 1024, backupCount=5)

        log_format = logging.Formatter('%(message)s')
        stream_handler.setFormatter(log_format)
        file_handler.setFormatter(log_format)

        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

    except Exception as err_info:
        print(err_info)
        exit(-1)

if __name__ == '__main__':
    try:
        options.parse_command_line()

        # 日志初始化
        init_log_handler()

        io_loop = tornado.ioloop.IOLoop.instance()

        # 服务端，接收reader的notify消息
        server = UDPServer(io_loop=io_loop)
        server.bind(options.port, "0.0.0.0", )
        server.start()
        logging.info('udp server start at: {}'.format(options.port))

        try:
            io_loop.start()
        except Exception as err:
            try:
                logging.info("io loop exception, err = {}".format(err))
            except Exception:
                pass
            finally:
                io_loop.stop()
                io_loop.close()

    except Exception as err:
        logging.fatal(err)
        print(err)
