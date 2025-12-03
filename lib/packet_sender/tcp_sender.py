import socket
import os
import struct
import logging
from typing import Optional
from .utils import get_interface_ip, bind_socket_to_interface

logger = logging.getLogger("UE-traffic")


class TCPSender:
    def __init__(self, iface: str):
        self.iface = iface
        if not os.path.exists(f"/sys/class/net/{iface}"):
            raise ValueError(f"Interface {iface} does not exist.")
        
        # 在初始化時就獲取該 interface 的 IP 地址
        self.interface_ip = get_interface_ip(iface)
        if self.interface_ip is None:
            logger.warning(f"Could not determine IP address for interface '{iface}'")
            self.interface_ip = "unknown"
        else:
            logger.debug(f"Interface '{iface}' IP: {self.interface_ip}")

    def _checksum(self, data: bytes) -> int:
        """計算 TCP/IP checksum"""
        if len(data) % 2 != 0:
            data += b'\x00'
        s = sum(struct.unpack('!%sH' % (len(data) // 2), data))
        s = (s >> 16) + (s & 0xffff)
        s += s >> 16
        return ~s & 0xffff

    def _build_tcp_syn_packet(self, src_ip: str, dst_ip: str, src_port: int, dst_port: int, payload_size: int) -> bytes:
        """構建 TCP SYN 封包（含 payload）"""
        # TCP header fields
        seq_num = 0
        ack_num = 0
        data_offset = 5  # TCP header = 20 bytes (5 * 4)
        flags = 0x02  # SYN flag
        window = 65535
        urgent_ptr = 0
        
        # Payload（全 0）
        payload = bytes(payload_size)
        
        # Pseudo header for checksum
        pseudo_header = struct.pack(
            '!4s4sBBH',
            socket.inet_aton(src_ip),
            socket.inet_aton(dst_ip),
            0,
            socket.IPPROTO_TCP,
            20 + len(payload)  # TCP header + payload length
        )
        
        # TCP header (without checksum)
        tcp_header_without_checksum = struct.pack(
            '!HHIIBBHHH',
            src_port,
            dst_port,
            seq_num,
            ack_num,
            (data_offset << 4) | 0,
            flags,
            window,
            0,  # checksum placeholder
            urgent_ptr
        )
        
        # Calculate checksum
        checksum = self._checksum(pseudo_header + tcp_header_without_checksum + payload)
        
        # TCP header (with checksum)
        tcp_header = struct.pack(
            '!HHIIBBH',
            src_port,
            dst_port,
            seq_num,
            ack_num,
            (data_offset << 4) | 0,
            flags,
            window
        ) + struct.pack('H', checksum) + struct.pack('!H', urgent_ptr)
        
        return tcp_header + payload

    def send_packet(self, *, target_ip: str, payload_size: int, target_port: Optional[int] = None):
        """
        發送 TCP SYN 封包（只發送 SYN，不完成三次握手）
        使用 raw socket 直接發送
        """
        sock = None
        try:
            # 創建 raw socket（需要 root 權限）
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 0)  # Kernel 會自動添加 IP header
            
            # 綁定到指定介面
            bind_socket_to_interface(sock, self.iface)
            
            # 使用目標端口作為源端口
            src_port = target_port
            src_ip = self.interface_ip
            
            # 構建 TCP SYN 封包
            tcp_packet = self._build_tcp_syn_packet(src_ip, target_ip, src_port, target_port, payload_size)
            
            # 發送封包
            sock.sendto(tcp_packet, (target_ip, 0))
            
            print(f"[{self.iface}] Sent TCP SYN with {payload_size} bytes payload from {src_ip}:{src_port} to {target_ip}:{target_port}")
            
            return {
                'src_ip': src_ip,
                'src_port': src_port,
                'dst_ip': target_ip,
                'dst_port': target_port,
                'protocol': 'TCP',
                'success': True
            }
            
        except Exception as e:
            print(f"[{self.iface}] TCP SYN send failed: {e}")
            return {
                'src_ip': self.interface_ip,
                'src_port': target_port,
                'dst_ip': target_ip,
                'dst_port': target_port,
                'protocol': 'TCP',
                'success': False,
                'error': str(e)
            }
        finally:
            if sock:
                sock.close()
