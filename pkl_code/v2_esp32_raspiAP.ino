#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <WebServer.h>

#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

// ================================
// WIFI (RASPI ACCESS POINT)
// ================================
const char* WIFI_SSID = "RASPI_AP_ESP32";
const char* WIFI_PASS = "raspi12345";

const char* RASPI_IP   = "192.168.4.1";
const int   RASPI_PORT = 5000;

// ================================
WebServer server(80);
bool isStreaming = false;

// metadata
String responden = "unknown";
String sesi = "default";

// ================================
// WIFI CONNECT
// ================================
void connectWiFi() {
  Serial.print("[WiFi] Connecting");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  int retry = 0;
  while (WiFi.status() != WL_CONNECTED && retry < 20) {
    delay(500);
    Serial.print(".");
    retry++;
  }

  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("[WiFi] Connected. ESP32 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("[WiFi] FAILED");
  }
}

// ================================
// HTTP CONTROL
// ================================
void handleSetSession() {
  responden = server.arg("responden");
  sesi      = server.arg("sesi");

  Serial.printf("[SESSION] responden=%s | sesi=%s\n",
                responden.c_str(), sesi.c_str());

  server.send(200, "text/plain", "OK");
}

void handleStart() {
  isStreaming = true;
  Serial.println("[STREAM] START");
  server.send(200, "text/plain", "STREAMING");
}

void handleStop() {
  isStreaming = false;
  Serial.println("[STREAM] STOP");
  server.send(200, "text/plain", "STOPPED");
}

// ================================
// SETUP
// ================================
void setup() {
  Serial.begin(115200);
  Serial.println("\nESP32-CAM START");

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;

  // 🔥 PENTING: ringan & stabil
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size   = FRAMESIZE_QVGA;   // 320x240
  config.jpeg_quality = 15;
  config.fb_count     = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("[CAM] INIT FAILED");
    while (true);
  }

  connectWiFi();

  server.on("/set_session", handleSetSession);
  server.on("/start", handleStart);
  server.on("/stop", handleStop);
  server.begin();

  Serial.println("[HTTP] Control server ready");
}

// ================================
// LOOP
// ================================
void loop() {
  server.handleClient();

  if (!isStreaming || WiFi.status() != WL_CONNECTED) {
    delay(10);
    return;
  }

  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("[CAM] Capture failed");
    return;
  }

  HTTPClient http;
  String url = "http://" + String(RASPI_IP) + ":" +
               String(RASPI_PORT) + "/upload_frame";

  http.begin(url);
  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("X-Responden", responden);
  http.addHeader("X-Sesi", sesi);
  http.addHeader("X-Filename", String(millis()) + ".jpg");

  int code = http.POST(fb->buf, fb->len);

  Serial.printf("[POST] size=%d | code=%d\n", fb->len, code);
  if (code > 0) {
    Serial.println(http.getString()); // harus "OK"
  }

  http.end();
  esp_camera_fb_return(fb);

  delay(200); // ~5 FPS
}