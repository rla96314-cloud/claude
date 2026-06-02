/*
 * M5Stack AtomS3R-CAM (GC0308) 를 WiFi 사진기로 사용하기
 * ------------------------------------------------------
 * 이 펌웨어를 AtomS3R-CAM 에 올리면 기기가 WiFi 카메라가 됩니다.
 *
 *   - 라이브 미리보기 :  http://<기기IP>/        (브라우저에서 실시간 영상)
 *   - 사진 한 장 저장  :  http://<기기IP>/capture (JPG 다운로드)
 *   - MJPEG 스트림     :  http://<기기IP>/stream  ( <img> 소스용 )
 *
 * 동작 방식
 *   1) 아래 WIFI_SSID / WIFI_PASS 에 집 WiFi 정보를 넣으면 그 네트워크에 접속(STA).
 *   2) 접속에 실패하거나 SSID 를 비워두면 기기가 스스로 핫스팟(AP) 을 만듭니다.
 *      - 핫스팟 이름 : AtomS3-CAM   /  비밀번호 : 12345678
 *      - 폰/PC 를 이 핫스팟에 연결한 뒤 브라우저에서  http://192.168.4.1  접속.
 *
 * 필요한 보드/라이브러리 (Arduino IDE)
 *   - 보드 매니저 : "esp32 by Espressif" 설치 후, 보드 = "M5AtomS3"
 *     (또는 "ESP32S3 Dev Module" + PSRAM: OPI PSRAM 활성화)
 *   - 추가 라이브러리 불필요 (esp32 코어에 esp_camera, WiFi, esp_http_server 포함)
 *
 * 핀 맵 출처 : M5Stack 공식 예제 camera_pins.h (AtomS3R-CAM, SKU C126)
 */

#include <WiFi.h>
#include "esp_camera.h"
#include "esp_http_server.h"
#include "img_converters.h"

// ===================== 사용자 설정 =====================
// 집 WiFi 에 붙이려면 채우고, 그냥 핫스팟으로 쓰려면 비워두세요("").
static const char *WIFI_SSID = "";
static const char *WIFI_PASS = "";

// 기기가 직접 만드는 핫스팟(AP) 정보
static const char *AP_SSID = "AtomS3-CAM";
static const char *AP_PASS = "12345678";  // 최소 8자

// 화질 설정 (GC0308 최대 해상도는 VGA 640x480)
//   더 부드러운 라이브 화면을 원하면 FRAMESIZE_QVGA(320x240) 로 낮추세요.
#define FRAME_SIZE   FRAMESIZE_VGA
#define JPEG_QUALITY 12  // 0(고화질,큼) ~ 63(저화질,작음)
// =======================================================

// --- AtomS3R-CAM (GC0308) 카메라 핀 맵 ---
#define PWDN_GPIO_NUM  -1
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM  21
#define SIOD_GPIO_NUM  12
#define SIOC_GPIO_NUM  9
#define Y9_GPIO_NUM    13
#define Y8_GPIO_NUM    11
#define Y7_GPIO_NUM    17
#define Y6_GPIO_NUM    4
#define Y5_GPIO_NUM    48
#define Y4_GPIO_NUM    46
#define Y3_GPIO_NUM    42
#define Y2_GPIO_NUM    3
#define VSYNC_GPIO_NUM 10
#define HREF_GPIO_NUM  14
#define PCLK_GPIO_NUM  40
#define POWER_GPIO_NUM 18  // 카메라 전원 enable (LOW = ON)

static httpd_handle_t camera_httpd = NULL;

// MJPEG 멀티파트 스트림용 상수
#define PART_BOUNDARY "123456789000000000000987654321"
static const char *STREAM_CONTENT_TYPE =
    "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char *STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char *STREAM_PART =
    "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

// ---------- 카메라 초기화 ----------
static bool initCamera() {
  // 카메라 전원 ON (AtomS3R 은 GPIO18 을 LOW 로 줘야 카메라에 전원 공급)
  pinMode(POWER_GPIO_NUM, OUTPUT);
  digitalWrite(POWER_GPIO_NUM, LOW);
  delay(500);

  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  // GC0308 은 JPEG 하드웨어 인코더가 없어 RGB565 로 받아 소프트웨어로 JPEG 변환합니다.
  config.pixel_format = PIXFORMAT_RGB565;
  config.frame_size = FRAME_SIZE;
  config.jpeg_quality = JPEG_QUALITY;
  config.fb_count = 2;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.grab_mode = CAMERA_GRAB_LATEST;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("카메라 초기화 실패: 0x%x\n", err);
    return false;
  }
  return true;
}

// 한 프레임을 JPEG 버퍼로 얻는다. 성공 시 true, 호출자는 free(*out_buf) 책임.
static bool grabJpeg(uint8_t **out_buf, size_t *out_len) {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) return false;

  bool ok;
  if (fb->format == PIXFORMAT_JPEG) {
    // 혹시 JPEG 네이티브 센서(M12 등)인 경우 복사
    *out_buf = (uint8_t *)malloc(fb->len);
    if (*out_buf) {
      memcpy(*out_buf, fb->buf, fb->len);
      *out_len = fb->len;
      ok = true;
    } else {
      ok = false;
    }
  } else {
    ok = frame2jpg(fb, JPEG_QUALITY, out_buf, out_len);
  }
  esp_camera_fb_return(fb);
  return ok;
}

// ---------- HTTP 핸들러: 메인 페이지 ----------
static esp_err_t indexHandler(httpd_req_t *req) {
  static const char *PAGE =
      "<!DOCTYPE html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
      "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
      "<title>AtomS3 사진기</title><style>"
      "body{margin:0;background:#111;color:#eee;font-family:sans-serif;"
      "text-align:center}"
      "h1{font-size:18px;margin:12px}"
      "img{max-width:100%;height:auto;border:4px solid #333;border-radius:8px}"
      "a.btn{display:inline-block;margin:16px;padding:14px 28px;font-size:20px;"
      "background:#e8453c;color:#fff;text-decoration:none;border-radius:40px}"
      "a.btn:active{background:#b5352e}</style></head><body>"
      "<h1>📷 AtomS3 사진기</h1>"
      "<img src=\"/stream\" alt=\"live\">"
      "<div><a class=\"btn\" href=\"/capture\" download>📸 사진 저장</a></div>"
      "</body></html>";
  httpd_resp_set_type(req, "text/html; charset=utf-8");
  return httpd_resp_send(req, PAGE, HTTPD_RESP_USE_STRLEN);
}

// ---------- HTTP 핸들러: 사진 한 장 (다운로드) ----------
static esp_err_t captureHandler(httpd_req_t *req) {
  uint8_t *buf = NULL;
  size_t len = 0;
  if (!grabJpeg(&buf, &len)) {
    httpd_resp_send_500(req);
    return ESP_FAIL;
  }
  httpd_resp_set_type(req, "image/jpeg");
  httpd_resp_set_hdr(req, "Content-Disposition",
                     "attachment; filename=atoms3_photo.jpg");
  esp_err_t res = httpd_resp_send(req, (const char *)buf, len);
  free(buf);
  return res;
}

// ---------- HTTP 핸들러: MJPEG 라이브 스트림 ----------
static esp_err_t streamHandler(httpd_req_t *req) {
  esp_err_t res = httpd_resp_set_type(req, STREAM_CONTENT_TYPE);
  if (res != ESP_OK) return res;
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

  char part_buf[64];
  while (true) {
    uint8_t *buf = NULL;
    size_t len = 0;
    if (!grabJpeg(&buf, &len)) {
      res = ESP_FAIL;
      break;
    }
    res = httpd_resp_send_chunk(req, STREAM_BOUNDARY, strlen(STREAM_BOUNDARY));
    if (res == ESP_OK) {
      size_t hlen = snprintf(part_buf, sizeof(part_buf), STREAM_PART, len);
      res = httpd_resp_send_chunk(req, part_buf, hlen);
    }
    if (res == ESP_OK) {
      res = httpd_resp_send_chunk(req, (const char *)buf, len);
    }
    free(buf);
    if (res != ESP_OK) break;  // 클라이언트가 연결을 끊음
  }
  return res;
}

static void startServer() {
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;
  config.max_uri_handlers = 8;

  if (httpd_start(&camera_httpd, &config) != ESP_OK) {
    Serial.println("HTTP 서버 시작 실패");
    return;
  }
  httpd_uri_t index_uri = {"/", HTTP_GET, indexHandler, NULL};
  httpd_uri_t capture_uri = {"/capture", HTTP_GET, captureHandler, NULL};
  httpd_uri_t stream_uri = {"/stream", HTTP_GET, streamHandler, NULL};
  httpd_register_uri_handler(camera_httpd, &index_uri);
  httpd_register_uri_handler(camera_httpd, &capture_uri);
  httpd_register_uri_handler(camera_httpd, &stream_uri);
}

static void startWiFi() {
  // 1) STA 모드 시도 (집 WiFi)
  if (WIFI_SSID && strlen(WIFI_SSID) > 0) {
    Serial.printf("WiFi 접속 시도: %s\n", WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < 10000) {
      delay(300);
      Serial.print(".");
    }
    Serial.println();
    if (WiFi.status() == WL_CONNECTED) {
      Serial.print("접속 성공! 브라우저에서 접속하세요 -> http://");
      Serial.println(WiFi.localIP());
      return;
    }
    Serial.println("STA 접속 실패. 핫스팟(AP) 모드로 전환합니다.");
  }

  // 2) AP 모드 (기기가 핫스팟 생성)
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASS);
  Serial.printf("핫스팟 생성됨: SSID=%s  PASS=%s\n", AP_SSID, AP_PASS);
  Serial.print("이 핫스팟에 연결 후 접속 -> http://");
  Serial.println(WiFi.softAPIP());
}

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\n=== AtomS3 사진기 시작 ===");

  if (!initCamera()) {
    Serial.println("카메라를 찾을 수 없습니다. 연결/모델을 확인하세요.");
    return;
  }
  startWiFi();
  startServer();
  Serial.println("준비 완료.");
}

void loop() {
  // 모든 처리는 esp_http_server 가 백그라운드에서 담당합니다.
  delay(1000);
}
