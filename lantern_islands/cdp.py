from __future__ import annotations

import base64
import json
import os
import socket
import struct
from urllib.parse import urlparse


class CdpWebSocket:
    def __init__(self, url: str):
        parsed = urlparse(url)
        self.socket = socket.create_connection((parsed.hostname, parsed.port), timeout=5)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {parsed.path} HTTP/1.1\r\nHost: {parsed.hostname}:{parsed.port}\r\n"
            f"Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.socket.sendall(request.encode("ascii"))
        response = b""
        while b"\r\n\r\n" not in response:
            response += self.socket.recv(4096)
        if b" 101 " not in response.split(b"\r\n", 1)[0]:
            raise RuntimeError("Chrome DevTools websocket handshake failed")
        self.next_id = 1

    def close(self) -> None:
        self.socket.close()

    def _send_text(self, text: str) -> None:
        payload = text.encode("utf-8")
        mask = os.urandom(4)
        length = len(payload)
        if length < 126:
            header = bytes((0x81, 0x80 | length))
        elif length < 65536:
            header = bytes((0x81, 0xFE)) + struct.pack("!H", length)
        else:
            header = bytes((0x81, 0xFF)) + struct.pack("!Q", length)
        masked = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        self.socket.sendall(header + mask + masked)

    def _read_exact(self, count: int) -> bytes:
        result = b""
        while len(result) < count:
            chunk = self.socket.recv(count - len(result))
            if not chunk:
                raise ConnectionError("Chrome DevTools websocket closed")
            result += chunk
        return result

    def _read_text(self) -> str:
        first, second = self._read_exact(2)
        opcode, length = first & 0x0F, second & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._read_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._read_exact(8))[0]
        masked = bool(second & 0x80)
        mask = self._read_exact(4) if masked else b""
        payload = self._read_exact(length)
        if masked:
            payload = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
        if opcode == 8:
            raise ConnectionError("Chrome DevTools websocket closed")
        return payload.decode("utf-8")

    def call(self, method: str, params: dict | None = None) -> dict:
        call_id = self.next_id
        self.next_id += 1
        self._send_text(json.dumps({"id": call_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self._read_text())
            if message.get("id") == call_id:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result", {})
