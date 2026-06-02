# AtomS3 사진기 (M5Stack AtomS3R-CAM)

연결된 **M5Stack AtomS3R-CAM (GC0308)** 을 WiFi 사진기로 사용하기 위한 펌웨어와 PC 도구입니다.

> AtomS3 는 PC 에 USB 웹캠처럼 바로 잡히지 않는 마이크로컨트롤러입니다.
> 그래서 기기에 펌웨어를 올려 **WiFi 로 영상을 내보내고**, 브라우저나 PC 에서 보는 방식을 사용합니다.

## 구성

| 파일 | 설명 |
|------|------|
| `atoms3_camera.ino` | AtomS3R-CAM 에 올리는 펌웨어 (라이브 영상 + 사진 촬영 웹서버) |
| `../atoms3_cam.py` | PC 에서 사진을 받아 저장하는 파이썬 도구 (표준 라이브러리만 사용) |

## 1. 펌웨어 올리기 (Arduino IDE)

1. **보드 설치**: `파일 > 기본 설정 > 추가 보드 매니저 URL` 에 아래 추가
   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```
   그 후 `툴 > 보드 매니저` 에서 **esp32 by Espressif** 설치.
2. **보드 선택**: `툴 > 보드 > esp32 > M5AtomS3`
   - 목록에 없으면 **ESP32S3 Dev Module** 선택 후 `PSRAM: OPI PSRAM` 활성화.
3. `atoms3_camera.ino` 를 열고, 필요하면 파일 상단의 WiFi 설정을 수정.
   - **집 WiFi 로 쓰기**: `WIFI_SSID`, `WIFI_PASS` 입력.
   - **그냥 핫스팟으로 쓰기**: 비워둔 채로 두면 기기가 핫스팟을 만듭니다.
4. USB-C 로 AtomS3 를 연결하고 포트 선택 후 **업로드(→)**.

추가 라이브러리는 필요 없습니다 (`esp_camera`, `WiFi`, `esp_http_server` 는 esp32 코어에 포함).

## 2. 사용하기

업로드 후 시리얼 모니터(115200 baud) 에 접속 주소가 표시됩니다.

- **핫스팟(AP) 모드**: 폰/PC 를 WiFi `AtomS3-CAM` (비번 `12345678`) 에 연결한 뒤
  브라우저에서 **http://192.168.4.1** 접속.
- **집 WiFi(STA) 모드**: 시리얼에 찍힌 `http://192.168.x.x` 주소로 접속.

웹 화면에서:
- 실시간 미리보기가 보이고
- **📸 사진 저장** 버튼을 누르면 JPG 가 다운로드됩니다.

### PC 에서 사진 저장 (선택)

```bash
# 한 장 촬영해서 ./photos 에 저장
python atoms3_cam.py --host 192.168.4.1

# 3초 간격 10장 연속 촬영
python atoms3_cam.py --host 192.168.0.42 --count 10 --interval 3

# 라이브 영상을 브라우저로 열기
python atoms3_cam.py --host 192.168.4.1 --view
```

## 엔드포인트

| 주소 | 내용 |
|------|------|
| `/`        | 라이브 미리보기 + 사진 버튼 (HTML) |
| `/stream`  | MJPEG 실시간 스트림 |
| `/capture` | JPG 사진 한 장 (다운로드) |

## 참고 / 다른 모델인 경우

- 핀 맵은 **AtomS3R-CAM (SKU C126, GC0308)** 기준입니다
  (M5Stack 공식 예제 `camera_pins.h`).
- 다른 ESP32-S3 카메라(예: AtomS3R-M12, Unit CamS3)라면 `.ino` 상단의 핀 `#define`
  값만 해당 모델에 맞게 바꾸면 됩니다.
- 화질/속도 조절: `.ino` 의 `FRAME_SIZE`(기본 VGA 640x480) 를 `FRAMESIZE_QVGA`
  로 낮추면 라이브 화면이 더 부드러워집니다. GC0308 최대 해상도는 VGA 입니다.
