#include "esp_camera.h"

#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"

#define BAUDRATE 921600

void setup() {
  Serial.begin(BAUDRATE);
  Serial.println("ESP32_CAM_USB_STREAM");

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

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size   = FRAMESIZE_QVGA;
  config.jpeg_quality = 15;
  config.fb_count     = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("CAMERA INIT FAILED");
    while (true);
  }

  Serial.println("CAMERA READY");
}

void loop() {
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) return;

  // Header
  Serial.write(0xAA);
  Serial.write(0x55);

  // Length (4 bytes)
  uint32_t len = fb->len;
  Serial.write((uint8_t*)&len, 4);

  // JPEG data
  Serial.write(fb->buf, fb->len);

  esp_camera_fb_return(fb);

  delay(200); // ~5 FPS
}