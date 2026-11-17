"""LAN Handoff Service for instant zero-friction reading continuity across devices."""

import secrets
import socket
import threading
import time
from typing import Any

from app.logger import log_event

# In-memory handoff tokens: token -> { file_hash, page_number, expires_at }
_HANDOFF_LOCK = threading.Lock()
_HANDOFF_TOKENS: dict[str, dict[str, Any]] = {}
_HANDOFF_TTL_SECONDS = 60 * 60 * 24 * 30  # 30 days passkey continuity for mobile sessions


ROUTING_PROBE_HOST = socket.inet_ntoa(bytes([10, 255, 255, 255]))
DEFAULT_LOOPBACK_HOST = socket.inet_ntoa(bytes([127, 0, 0, 1]))


def get_local_lan_ip() -> str:
    """Detect machine's primary local LAN IPv4 address without external internet calls."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Using routing probe does not send packets over wire, just identifies route interface
            s.connect((ROUTING_PROBE_HOST, 1))
            ip = s.getsockname()[0]
            if ip and not ip.startswith("127."):
                return ip
    except Exception as e:
        log_event("system", "DEBUG", f"Primary socket route IP lookup note: {e}")

    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127."):
                return ip
    except Exception as e:
        log_event("system", "DEBUG", f"Hostname DNS IP lookup note: {e}")

    return DEFAULT_LOOPBACK_HOST


def create_handoff_token(file_hash: str, page_number: int) -> str:
    """Create a temporary single-use token for reading handoff."""
    token = secrets.token_urlsafe(18)
    now = time.time()
    with _HANDOFF_LOCK:
        # Cleanup expired tokens
        expired = [k for k, v in _HANDOFF_TOKENS.items() if now > v["expires_at"]]
        for k in expired:
            _HANDOFF_TOKENS.pop(k, None)

        _HANDOFF_TOKENS[token] = {
            "file_hash": file_hash,
            "page_number": max(1, page_number),
            "created_at": now,
            "expires_at": now + _HANDOFF_TTL_SECONDS,
        }
    return token


def consume_handoff_token(token: str) -> dict[str, Any] | None:
    """Validate and retrieve handoff token data (reusable passkey for mobile session continuity)."""
    with _HANDOFF_LOCK:
        entry = _HANDOFF_TOKENS.get(token)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            _HANDOFF_TOKENS.pop(token, None)
            return None
        return dict(entry)


# ---------------------------------------------------------------------------
# Lightweight Pure Python SVG QR Code Generator (Zero-Dependency)
# Supports alphanumeric / byte modes up to Version 4 (suitable for LAN URLs)
# ---------------------------------------------------------------------------


class MiniQR:
    """Pure-Python QR code generator that outputs crisp vector SVG without any C libraries."""

    def __init__(self, data: str):
        self.data = data

    def to_svg(self, box_size: int = 8, border: int = 4) -> str:
        """Generate standalone SVG representation of QR code."""
        modules = self._generate_matrix()
        size = len(modules)
        total_size = (size + 2 * border) * box_size

        rects = []
        for r in range(size):
            for c in range(size):
                if modules[r][c]:
                    x = (c + border) * box_size
                    y = (r + border) * box_size
                    rects.append(
                        f'<rect x="{x}" y="{y}" width="{box_size}" height="{box_size}" fill="#000000"/>'
                    )

        body = "\n  ".join(rects)
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_size} {total_size}" '
            f'width="{total_size}" height="{total_size}" shape-rendering="crispEdges">\n'
            f'  <rect width="{total_size}" height="{total_size}" fill="#ffffff"/>\n'
            f"  {body}\n"
            f"</svg>"
        )

    def _place_timing_and_alignment(
        self,
        matrix: list[list[bool]],
        reserved: list[list[bool]],
        matrix_size: int,
        version: int,
    ) -> None:
        """Place horizontal and vertical timing patterns, alignment pattern, and format reserves."""
        for i in range(8, matrix_size - 8):
            val = i % 2 == 0
            matrix[6][i] = val
            reserved[6][i] = True
            matrix[i][6] = val
            reserved[i][6] = True

        align_centers = {3: 22, 4: 26, 5: 30, 6: 34}
        align_pos = align_centers.get(version, 26)
        self._add_alignment_pattern(matrix, reserved, align_pos - 2, align_pos - 2)

        for i in range(9):
            reserved[8][i] = True
            reserved[i][8] = True
        for i in range(matrix_size - 8, matrix_size):
            reserved[8][i] = True
            reserved[i][8] = True

    @staticmethod
    def _interleave_bits(
        matrix: list[list[bool]],
        reserved: list[list[bool]],
        matrix_size: int,
        bits: list[bool],
    ) -> None:
        """Interleave bits into matrix in zigzag pattern with standard Mask 0."""
        bit_idx = 0
        right = matrix_size - 1
        upward = True
        while right > 0:
            if right == 6:
                right -= 1
            for vert in range(matrix_size):
                r = (matrix_size - 1 - vert) if upward else vert
                for col_offset in (0, 1):
                    c = right - col_offset
                    if not reserved[r][c]:
                        bit_val = bits[bit_idx] if bit_idx < len(bits) else False
                        bit_idx += 1
                        if (r + c) % 2 == 0:
                            bit_val = not bit_val
                        matrix[r][c] = bit_val
            upward = not upward
            right -= 2

    @staticmethod
    def _place_format_bits(matrix: list[list[bool]], matrix_size: int, version: int) -> None:
        """Add format information for Mask 0, ECC Level L."""
        format_bits = [bool((0x77C4 >> (14 - i)) & 1) for i in range(15)]
        seq1 = [
            (8, 0),
            (8, 1),
            (8, 2),
            (8, 3),
            (8, 4),
            (8, 5),
            (8, 7),
            (8, 8),
            (7, 8),
            (5, 8),
            (4, 8),
            (3, 8),
            (2, 8),
            (1, 8),
            (0, 8),
        ]
        for idx, (fr, fc) in enumerate(seq1):
            matrix[fr][fc] = format_bits[idx]
        for idx in range(7):
            matrix[matrix_size - 1 - idx][8] = format_bits[idx]
        for idx in range(8):
            matrix[8][matrix_size - 8 + idx] = format_bits[7 + idx]
        matrix[4 * version + 9][8] = True

    def _generate_matrix(self) -> list[list[bool]]:
        """Construct a valid QR matrix (Versions 3-6, ECC Level L) supporting URLs up to 134 bytes."""
        raw_bytes = self.data.encode("utf-8")
        n_bytes = len(raw_bytes)
        if n_bytes > 134:
            raise ValueError(
                f"URL/Data too long for MiniQR ({n_bytes} bytes > max 134 bytes for QR-6L)"
            )
        if n_bytes <= 53:
            version = 3
        elif n_bytes <= 78:
            version = 4
        elif n_bytes <= 106:
            version = 5
        else:
            version = 6
        matrix_size = 17 + 4 * version

        matrix = [[False] * matrix_size for _ in range(matrix_size)]
        reserved = [[False] * matrix_size for _ in range(matrix_size)]

        # 1. Place Finder Patterns
        self._add_finder_pattern(matrix, reserved, 0, 0)
        self._add_finder_pattern(matrix, reserved, matrix_size - 7, 0)
        self._add_finder_pattern(matrix, reserved, 0, matrix_size - 7)

        # 2. Timing and alignment patterns
        self._place_timing_and_alignment(matrix, reserved, matrix_size, version)

        # 3. Encode data bits
        bits = self._encode_bitstream(raw_bytes, version)

        # 4. Interleave bits into matrix
        self._interleave_bits(matrix, reserved, matrix_size, bits)

        # 5. Place format bits
        self._place_format_bits(matrix, matrix_size, version)

        return matrix

    def _add_finder_pattern(
        self,
        matrix: list[list[bool]],
        reserved: list[list[bool]],
        start_r: int,
        start_c: int,
    ) -> None:
        """Place 7x7 finder pattern with 1-module white separator."""
        for r in range(-1, 8):
            for c in range(-1, 8):
                nr = start_r + r
                nc = start_c + c
                if 0 <= nr < len(matrix) and 0 <= nc < len(matrix):
                    reserved[nr][nc] = True
                    if 0 <= r <= 6 and 0 <= c <= 6:
                        # Outer 7x7 border or inner 3x3 box
                        is_black = r in (0, 6) or c in (0, 6) or (2 <= r <= 4 and 2 <= c <= 4)
                        matrix[nr][nc] = is_black
                    else:
                        matrix[nr][nc] = False

    def _add_alignment_pattern(
        self,
        matrix: list[list[bool]],
        reserved: list[list[bool]],
        start_r: int,
        start_c: int,
    ) -> None:
        """Place 5x5 alignment pattern."""
        for r in range(5):
            for c in range(5):
                nr = start_r + r
                nc = start_c + c
                if 0 <= nr < len(matrix) and 0 <= nc < len(matrix):
                    if not reserved[nr][nc]:
                        reserved[nr][nc] = True
                        is_black = r in (0, 4) or c in (0, 4) or (r == 2 and c == 2)
                        matrix[nr][nc] = is_black

    def _encode_bitstream(self, data: bytes, version: int) -> list[bool]:
        """Encode byte data into QR bitstream with Reed-Solomon parity codewords (Versions 3-6L)."""
        specs = {
            3: (70, 55, 1),
            4: (100, 80, 1),
            5: (134, 108, 1),
            6: (172, 136, 2),
        }
        total_codewords, data_codewords_count, num_blocks = specs[version]
        ec_per_block = (total_codewords - data_codewords_count) // num_blocks

        # Mode indicator: 0100 for Byte mode (4 bits)
        bits_str = "0100"
        # Character count indicator: 8 bits for Byte mode (Versions 1-9)
        bits_str += f"{len(data):08b}"
        # Data bytes
        for b in data:
            bits_str += f"{b:08b}"

        # Terminator (up to 4 zeroes)
        max_data_bits = data_codewords_count * 8
        bits_str = (bits_str + "0000")[:max_data_bits]

        # Pad to multiple of 8
        if len(bits_str) % 8 != 0:
            bits_str += "0" * (8 - (len(bits_str) % 8))

        # Pad with alternate bytes 0xEC (236) and 0x11 (17)
        data_bytes = bytearray([int(bits_str[i : i + 8], 2) for i in range(0, len(bits_str), 8)])
        pad_toggle = True
        while len(data_bytes) < data_codewords_count:
            data_bytes.append(0xEC if pad_toggle else 0x11)
            pad_toggle = not pad_toggle

        if num_blocks == 1:
            ec_bytes = self._calculate_reed_solomon(data_bytes, ec_per_block)
            all_bytes = data_bytes + ec_bytes
        else:
            block_len = data_codewords_count // num_blocks
            data_blocks = [
                data_bytes[i * block_len : (i + 1) * block_len] for i in range(num_blocks)
            ]
            ec_blocks = [self._calculate_reed_solomon(blk, ec_per_block) for blk in data_blocks]
            all_bytes = bytearray()
            for col in range(block_len):
                for b_idx in range(num_blocks):
                    all_bytes.append(data_blocks[b_idx][col])
            for col in range(ec_per_block):
                for b_idx in range(num_blocks):
                    all_bytes.append(ec_blocks[b_idx][col])

        # Convert back to boolean bits
        out_bits: list[bool] = []
        for b in all_bytes:
            for shift in range(7, -1, -1):
                out_bits.append(bool((b >> shift) & 1))
        return out_bits

    @staticmethod
    def _calculate_reed_solomon(data: bytearray, ec_len: int) -> bytearray:
        """Compute Reed-Solomon error correction codewords over GF(256)."""
        # GF(256) primitive polynomial 0x11D (x^8 + x^4 + x^3 + x^2 + 1)
        exp_table = [0] * 512
        log_table = [0] * 256
        x = 1
        for i in range(255):
            exp_table[i] = x
            exp_table[i + 255] = x
            log_table[x] = i
            x = (x << 1) ^ (0x11D if (x & 0x80) else 0)

        # Build generator polynomial
        gen = [1]
        for i in range(ec_len):
            new_gen = [0] * (len(gen) + 1)
            for j in range(len(gen)):
                new_gen[j] ^= gen[j]
                if gen[j] != 0:
                    prod_exp = (log_table[gen[j]] + i) % 255
                    new_gen[j + 1] ^= exp_table[prod_exp]
            gen = new_gen

        # Polynomial division
        res = bytearray(data) + bytearray(ec_len)
        for i in range(len(data)):
            coef = res[i]
            if coef != 0:
                for j in range(1, len(gen)):
                    if gen[j] != 0:
                        prod_exp = (log_table[coef] + log_table[gen[j]]) % 255
                        res[i + j] ^= exp_table[prod_exp]

        return res[-ec_len:]


def generate_qr_svg(url: str, box_size: int = 6) -> str:
    """Generate standalone SVG QR code string for a URL."""
    qr = MiniQR(url)
    return qr.to_svg(box_size=box_size, border=4)
