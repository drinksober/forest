# -*- coding: utf-8 -*-

# Copyright (C) 2016, Maximilian Köhl <mail@koehlma.de>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

import uv

RESPONSE = (b'HTTP/1.1 200 OK\r\n'
            b'Content-Type: text/plain\r\n'
            b'Content-Length: 13\r\n\r\n'
            b'Hello World!\n')


def on_shutdown(request, _):
    request.stream.close()


def on_read(stream, status, data):
    if status != uv.StatusCodes.SUCCESS:
        stream.close()
    data = data.strip()
    if not data:
        return
    stream.write(RESPONSE)
    stream.shutdown(on_shutdown)


def on_connection(server, _):
    connection = server.accept()
    connection.read_start(on_read=on_read)


def on_quit(sigint, _):
    sigint.loop.close_all_handles()


def main():
    loop = uv.Loop.get_current()

    server = uv.TCP()
    server.bind(('0.0.0.0', 4444))
    server.listen(1000, on_connection=on_connection)

    sigint = uv.Signal()
    sigint.start(uv.Signals.SIGINT, on_signal=on_quit)

    loop.run_forever()


if __name__ == '__main__':
    main()
