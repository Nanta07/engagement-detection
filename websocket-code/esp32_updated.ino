#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include "FS.h"
#include "SD_MMC.h"
#include <WebServer.h>

#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

// =====================================================
// CONFIG (NANTI DISESUAIKAN DENGAN RASPI)
// =====================================================
const char* WIFI_SSID = "RASPI_AP_PLACEHOLDER";
const char* WIFI_PASS = "raspi_password";

const char* GATEWAY_IP = "192.168.4.1";   // IP Raspi (nanti)
const int   GATEWAY_PORT = 5000;

// =====================================================
WebServer server(80);

// STATE
bool isRecording = false;
bool sdReady = false;
String sessionFolder = "";
String responden = "unknown";
String sesi = "default";

// =====================================================
// WIFI HELPER
// =====================================================
void ensureWiFi() {
  if (WiFi.status() == WL_CONNECTED) return;

  WiFi.disconnect();
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - start < 15000) {
    delay(300);
  }
}

// =====================================================
// SESSION CONTROL
// =====================================================
void handleSetSession() {
  if (!server.hasArg("responden") || !server.hasArg("sesi")) {
    server.send(400, "text/plain", "Missing responden or sesi");
    return;
  }
  responden = server.arg("responden");
  sesi = server.arg("sesi");
  server.send(200, "text/plain", "Session set");
}

// =====================================================
// START RECORDING
// =====================================================
void startRecording() {
  if (!sdReady) {
    server.send(500, "text/plain", "SD not ready");
    return;
  }

  sessionFolder = "/session_" + String(millis());
  SD_MMC.mkdir(sessionFolder);

  File meta = SD_MMC.open(sessionFolder + "/meta.txt", FILE_WRITE);
  meta.printf("responden=%s\nsesi=%s\n", responden.c_str(), sesi.c_str());
  meta.close();

  isRecording = true;
  server.send(200, "text/plain", "Recording started");
}

// =====================================================
// STOP & UPLOAD
// =====================================================
void stopRecording() {
  isRecording = false;
  uploadAllFrames();
  server.send(200, "text/plain", "Recording stopped & uploaded");
}

// =====================================================
// UPLOAD FRAMES
// =====================================================
void uploadAllFrames() {
  ensureWiFi();
  if (WiFi.status() != WL_CONNECTED) return;

  File root = SD_MMC.open(sessionFolder);
  File file = root.openNextFile();

  while (file) {
    if (!file.isDirectory()) {
      HTTPClient http;
      String url = "http://" + String(GATEWAY_IP) + ":" + String(GATEWAY_PORT) + "/upload_frame";

      http.begin(url);
      http.addHeader("Content-Type", "image/jpeg");
      http.addHeader("X-Responden", responden);
      http.addHeader("X-Sesi", sesi);
      http.addHeader("X-Filename", file.name());

      http.POST(file);
      http.end();
    }
    file = root.openNextFile();
  }
  root.close();
}

// =====================================================
// SETUP
// =====================================================
void setup() {
  Serial.begin(115200);

  // Camera config
  camera_config_t config;
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
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_SVGA;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  esp_camera_init(&config);

  sdReady = SD_MMC.begin();

  WiFi.begin(WIFI_SSID, WIFI_PASS);

  server.on("/set_session", handleSetSession);
  server.on("/start_recording", startRecording);
  server.on("/stop_recording", stopRecording);

  server.begin();
}

// =====================================================
// LOOP
// =====================================================
void loop() {
  server.handleClient();

  if (isRecording && sdReady) {
    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) return;

    String fname = sessionFolder + "/frame_" + String(millis()) + ".jpg";
    File f = SD_MMC.open(fname, FILE_WRITE);
    f.write(fb->buf, fb->len);
    f.close();

    esp_camera_fb_return(fb);
    delay(150);
  }
}