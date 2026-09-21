"""Minimal RFC 6455 WebSocket server codec (RFVISION-005).

RF Vision native, stdlib only (``hashlib`` + ``socket`` + ``struct``).
Implements exactly what the console needs: server-side opening handshake,
text-frame send, masked-frame receive, ping/pong, and close. No extensions,
no fragmentation support (control + single-frame text only — oversized or
fragmented frames raise :class:`WsError` and the connection is dropped).

Adapted pattern (not code) from RuView's reconnect/heartbeat discipline:
the server sends JSON ``ping`` heartbeats; clients answer ``pong``.
"""

from __future__ import annotations

import base64
import hashlib
import socket
import struct
from typing import Optional, Tuple

__all__ = ["WsError", "accept_key", "server_handshake",
           "send_text", "recv_frame"]

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

OPCODE_TEXT = 0x1
OPCODE_CLOSE = 0x8
OPCODE_PING = 0x9
OPCODE_PONG = 0xA


class WsError(ValueError):
    """Raised on any WebSocket protocol violation."""


def accept_key(client_key: str) -> str:
    """Compute ``Sec-WebSocket-Accept`` for a client key."""
    digest = hashlib.sha1(
        (client_key.strip() + GUID).encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


def server_handshake(request_text: str) -> Tuple[str, str]:
    """Validate an opening handshake, return (client_key, response_text).

    Raises :class:`WsError` when the request is not a valid WS upgrade.
    """
    lines = request_text.split("\r\n")
    if not lines or not lines[0].upper().startswith("GET "):
        raise WsError("not a GET upgrade request")
    headers = {}
    for line in lines[1:]:
        if not line:
            break
        if ":" in line:
            name, value = line.split(":", 1)
            headers[name.strip().lower()] = value.strip()
    if headers.get("upgrade", "").lower() != "websocket":
        raise WsError("missing Upgrade: websocket")
    key = headers.get("sec-websocket-key", "")
    if not key:
        raise WsError("missing Sec-WebSocket-Key")
    response = (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept_key(key)}\r\n"
        "\r\n"
    )
    return key, response


def _send_all(sock: socket.socket, data: bytes) -> None:
    sock.sendall(data)


def send_text(sock: socket.socket, text: str) -> None:
    """Send one unmasked text frame (raises WsError on oversize)."""
    payload = text.encode("utf-8")
    if len(payload) > 16_777_215:  # 64-bit lengths not implemented
        raise WsError("text frame too large")
    header = bytes([0x80 | OPCODE_TEXT])
    n = len(payload)
    if n < 126:
        header += bytes([n])
    elif n < 65536:
        header += bytes([126]) + struct.pack("!H", n)
    else:
        header += bytes([127]) + struct.pack("!Q", n)
    _send_all(sock, header + payload)


def send_control(sock: socket.socket, opcode: int,
                 payload: bytes = b"") -> None:
    """Send a control frame (ping/pong/close, payload <= 125)."""
    if len(payload) > 125:
        raise WsError("control payload too large")
    _send_all(sock, bytes([0x80 | opcode, len(payload)]) + payload)


def _recv_exact(sock: socket.socket, nbytes: int,
                timeout: Optional[float] = None) -> bytes:
    sock.settimeout(timeout)
    chunks = []
    remaining = nbytes
    try:
        while remaining:
            chunk = sock.recv(remaining)
            if not chunk:
                raise WsError("connection closed mid-frame")
            chunks.append(chunk)
            remaining -= len(chunk)
    except socket.timeout as exc:
        raise WsError("read timeout") from exc
    finally:
        sock.settimeout(None)
    return b"".join(chunks)


def recv_frame(sock: socket.socket,
               timeout: Optional[float] = None) -> Tuple[int, bytes]:
    """Read one frame; returns (opcode, payload).

    Handles client masking (required), answers pings with pongs, and
    raises :class:`WsError` on close frames, fragmentation, or any
    protocol violation. Callers loop until OPCODE_TEXT arrives.
    """
    hdr = _recv_exact(sock, 2, timeout)
    fin = hdr[0] & 0x80
    opcode = hdr[0] & 0x0F
    masked = hdr[1] & 0x80
    length = hdr[1] & 0x7F
    if not fin:
        raise WsError("fragmented frames not supported")
    if not masked:
        raise WsError("client frames must be masked")
    if length == 126:
        length = struct.unpack("!H", _recv_exact(sock, 2, timeout))[0]
    elif length == 127:
        length = struct.unpack("!Q", _recv_exact(sock, 8, timeout))[0]
        if length > 16_777_215:
            raise WsError("frame too large")
    mask = _recv_exact(sock, 4, timeout)
    masked_payload = _recv_exact(sock, length, timeout)
    payload = bytes(b ^ mask[i % 4] for i, b in enumerate(masked_payload))
    if opcode == OPCODE_PING:
        send_control(sock, OPCODE_PONG, payload)
        return recv_frame(sock, timeout)
    if opcode == OPCODE_PONG:
        return recv_frame(sock, timeout)
    if opcode == OPCODE_CLOSE:
        raise WsError("client closed connection")
    if opcode != OPCODE_TEXT:
        raise WsError(f"unsupported opcode: {opcode:#x}")
    return opcode, payload
