#!/usr/bin/env python3
"""
Kyto 심장 박동 측정기 -> OSC 전송기

Kyto BLE 심박 측정기에서 심박수를 읽어 OSC로 int32 형태로 초당 전송합니다.
OSC 주소: /heart_rate
타입: int32

사용법:
    python heart_rate_osc.py [--device-name DEVICE_NAME] [--device-address ADDRESS]
                             [--osc-host HOST] [--osc-port PORT]

기본값:
    --osc-host  127.0.0.1
    --osc-port  9000
"""

import argparse
import asyncio
import struct
import sys
import time

from bleak import BleakClient, BleakScanner
from pythonosc.udp_client import SimpleUDPClient

# Bluetooth Heart Rate 표준 UUID
HEART_RATE_SERVICE_UUID = "0000180d-0000-1000-8000-00805f9b34fb"
HEART_RATE_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"

# Kyto 기기 이름 키워드 (장치 스캔 시 사용)
KYTO_NAME_KEYWORDS = ["kyto", "hr", "heart"]

OSC_ADDRESS = "/heart_rate"


def parse_heart_rate(data: bytearray) -> int:
    """Heart Rate Measurement 특성 데이터를 파싱해 BPM(int) 반환."""
    flags = data[0]
    hr_format_uint16 = flags & 0x01  # 비트0: 0=uint8, 1=uint16
    if hr_format_uint16:
        bpm = struct.unpack_from("<H", data, 1)[0]
    else:
        bpm = data[1]
    return int(bpm)


async def scan_for_kyto(timeout: float = 10.0) -> str | None:
    """BLE 스캔으로 Kyto 심박 측정기를 찾아 주소를 반환."""
    print(f"BLE 기기 스캔 중... ({timeout}초)")
    devices = await BleakScanner.discover(timeout=timeout)
    for device in devices:
        name = (device.name or "").lower()
        if any(kw in name for kw in KYTO_NAME_KEYWORDS):
            print(f"Kyto 기기 발견: {device.name} [{device.address}]")
            return device.address
    return None


async def run(device_address: str, osc_host: str, osc_port: int) -> None:
    """BLE 연결 후 심박수를 OSC로 초당 전송."""
    osc_client = SimpleUDPClient(osc_host, osc_port)
    last_bpm: int | None = None
    last_send_time: float = 0.0

    def on_notification(_sender, data: bytearray) -> None:
        nonlocal last_bpm
        last_bpm = parse_heart_rate(data)

    print(f"기기 연결 중: {device_address}")
    async with BleakClient(device_address) as client:
        print(f"연결 성공: {client.address}")
        await client.start_notify(HEART_RATE_MEASUREMENT_UUID, on_notification)
        print(
            f"심박수 수신 시작 -> OSC {osc_host}:{osc_port}{OSC_ADDRESS} (int32, 1초 간격)\n"
            "종료하려면 Ctrl+C 를 누르세요.\n"
        )

        try:
            while True:
                now = time.monotonic()
                if last_bpm is not None and now - last_send_time >= 1.0:
                    bpm_int32 = last_bpm & 0xFFFFFFFF  # int32 범위로 제한
                    osc_client.send_message(OSC_ADDRESS, bpm_int32)
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] {OSC_ADDRESS} ,i {bpm_int32}")
                    last_send_time = now
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        finally:
            await client.stop_notify(HEART_RATE_MEASUREMENT_UUID)
            print("\n연결 종료.")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Kyto 심박 측정기에서 심박수를 읽어 OSC로 전송합니다."
    )
    parser.add_argument(
        "--device-name",
        default=None,
        help="연결할 BLE 기기 이름 (생략 시 자동 스캔)",
    )
    parser.add_argument(
        "--device-address",
        default=None,
        help="연결할 BLE 기기 MAC 주소 (예: AA:BB:CC:DD:EE:FF)",
    )
    parser.add_argument("--osc-host", default="127.0.0.1", help="OSC 수신 호스트 (기본: 127.0.0.1)")
    parser.add_argument("--osc-port", type=int, default=9000, help="OSC 수신 포트 (기본: 9000)")
    args = parser.parse_args()

    address = args.device_address

    if address is None and args.device_name:
        # 이름으로 스캔
        print(f"'{args.device_name}' 기기 스캔 중...")
        devices = await BleakScanner.discover(timeout=10.0)
        for device in devices:
            if args.device_name.lower() in (device.name or "").lower():
                address = device.address
                print(f"기기 발견: {device.name} [{address}]")
                break
        if address is None:
            print(f"오류: '{args.device_name}' 기기를 찾지 못했습니다.", file=sys.stderr)
            sys.exit(1)

    if address is None:
        address = await scan_for_kyto()
        if address is None:
            print(
                "오류: Kyto 심박 측정기를 찾지 못했습니다.\n"
                "--device-address 또는 --device-name 옵션으로 직접 지정하세요.",
                file=sys.stderr,
            )
            sys.exit(1)

    try:
        await run(address, args.osc_host, args.osc_port)
    except KeyboardInterrupt:
        print("\n사용자 종료.")


if __name__ == "__main__":
    asyncio.run(main())
