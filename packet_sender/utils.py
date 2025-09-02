"""
Utility functions shared across packet sender modules
"""
import socket
import subprocess
import os
from typing import Optional


def check_interface_binding_permission() -> bool:
    """
    檢查是否有權限綁定到網路介面
    
    Returns:
        True 如果有權限，False 如果沒有權限
    """
    try:
        # 創建一個測試 socket
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 嘗試綁定到 lo 介面（loopback，通常存在且安全）
            test_sock.setsockopt(socket.SOL_SOCKET, 25, b'lo')  # 25 = SO_BINDTODEVICE
            return True
        finally:
            test_sock.close()
    except PermissionError:
        return False
    except Exception:
        # 其他錯誤（如系統不支援）也視為沒有權限
        return False


def get_interface_ip(iface: str) -> Optional[str]:
    """
    獲取指定介面的 IP 地址
    
    Args:
        iface: 網路介面名稱 (例如: eth0, uesimtun0)
        
    Returns:
        介面的 IP 地址字串，如果無法獲取則返回 None
    """
    try:
        result = subprocess.run(['ip', 'addr', 'show', iface], 
                              capture_output=True, text=True, check=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if 'inet ' in line and not line.strip().startswith('inet 127.'):
                ip_part = line.strip().split('inet ')[1].split(' ')[0]
                ip = ip_part.split('/')[0]
                return ip
    except (subprocess.CalledProcessError, IndexError, AttributeError):
        pass
    return None


def bind_socket_to_interface(sock: socket.socket, iface: str, strict: bool = True) -> bool:
    """
    將 socket 綁定到指定的網路介面
    
    Args:
        sock: socket 對象
        iface: 網路介面名稱 (例如: eth0, uesimtun0)
        strict: 如果為 True，綁定失敗時會拋出異常；如果為 False，只會返回 False
        
    Returns:
        True 如果綁定成功，False 如果失敗
        
    Raises:
        PermissionError: 當 strict=True 且沒有足夠權限時
        OSError: 當 strict=True 且系統不支援介面綁定時
    """
    try:
        sock.setsockopt(socket.SOL_SOCKET, 25, iface.encode())  # 25 = SO_BINDTODEVICE
        print(f"[INFO] Successfully bound socket to interface '{iface}'")
        return True
    except PermissionError as e:
        error_msg = f"Cannot bind to interface '{iface}' - need root privileges"
        print(f"[ERROR] {error_msg}")
        if strict:
            raise PermissionError(error_msg) from e
        return False
    except OSError as e:
        error_msg = f"OS does not support binding to interface '{iface}'"
        print(f"[ERROR] {error_msg}")
        if strict:
            raise OSError(error_msg) from e
        return False
    except Exception as e:
        error_msg = f"Failed to bind to interface '{iface}': {e}"
        print(f"[ERROR] {error_msg}")
        if strict:
            raise Exception(error_msg) from e
        return False
