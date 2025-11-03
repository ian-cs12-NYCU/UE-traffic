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


def format_interface_name(simulator_type: str, id_val: int) -> str:
    """
    根據 UE simulator 類型格式化介面名稱
    
    Args:
        simulator_type: 'ueransim' 或 'packetrusher'
        id_val: UE 的數字 id
        
    Returns:
        組合後的介面名稱字串
        - ueransim: uesimtun0, uesimtun1, uesimtun2, ...
        - packetrusher: val0000000001, val0000000009, val0000000010, val9999999999
                       (always 'val' prefix + exactly 10 digits with zero-padding)
    
    Raises:
        ValueError: 當 packetrusher id 超過 10 位數時
    """
    if simulator_type == "ueransim":
        return f"uesimtun{id_val}"
    elif simulator_type == "packetrusher":
        # packetrusher 永遠使用 val + 10 位數字（zero-padded）
        if id_val > 9999999999:  # 超過 10 位數
            raise ValueError(f"PacketRusher interface id {id_val} exceeds maximum (9999999999)")
        return f"val{id_val:010d}"  # :010d = zero-pad to 10 digits
    else:
        # 預設使用 ueransim 格式
        return f"uesimtun{id_val}"


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


if __name__ == "__main__":
    """
    測試介面命名功能
    執行方式: python -m lib.packet_sender.utils
    """
    print("=" * 60)
    print("UE 介面命名測試")
    print("=" * 60)
    
    # 測試 PacketRusher 格式
    print("\n【PacketRusher 格式】val + 10位數字 (zero-padded)")
    print("-" * 60)
    test_cases_pr = [
        (0, "val0000000000"),
        (1, "val0000000001"),
        (4, "val0000000004"),
        (9, "val0000000009"),
        (10, "val0000000010"),
        (99, "val0000000099"),
        (100, "val0000000100"),
        (9999999999, "val9999999999"),
    ]
    
    for id_val, expected in test_cases_pr:
        result = format_interface_name("packetrusher", id_val)
        status = "✓" if result == expected else "✗"
        print(f"  {status} id={id_val:10d} -> {result:15s} (expected: {expected})")
    
    # 測試 UERANSIM 格式
    print("\n【UERANSIM 格式】uesimtun + 數字 (無固定長度)")
    print("-" * 60)
    test_cases_ue = [
        (0, "uesimtun0"),
        (1, "uesimtun1"),
        (4, "uesimtun4"),
        (10, "uesimtun10"),
        (99, "uesimtun99"),
    ]
    
    for id_val, expected in test_cases_ue:
        result = format_interface_name("ueransim", id_val)
        status = "✓" if result == expected else "✗"
        print(f"  {status} id={id_val:2d} -> {result:12s} (expected: {expected})")
    
    # 測試邊界情況
    print("\n【邊界測試】")
    print("-" * 60)
    try:
        format_interface_name("packetrusher", 10000000000)
        print("  ✗ 應該要拋出 ValueError (id > 9999999999)")
    except ValueError as e:
        print(f"  ✓ 正確拋出 ValueError: {e}")
    
    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)
