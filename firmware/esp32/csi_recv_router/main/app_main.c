/*
 * SPDX-FileCopyrightText: 2026 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
/* Get recv router csi

   This example code is in the Public Domain (or CC0 licensed, at your option.)

   Unless required by applicable law or agreed to in writing, this
   software is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
   CONDITIONS OF ANY KIND, either express or implied.
*/
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"

#include "nvs_flash.h"
#include "nvs.h"
#include "driver/uart.h"

#include "esp_mac.h"
#include "rom/ets_sys.h"
#include "esp_log.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_netif.h"
#include "esp_now.h"

#include "lwip/inet.h"
#include "lwip/netdb.h"
#include "lwip/sockets.h"
#include "ping/ping_sock.h"

#include "protocol_examples_common.h"
#include "esp_csi_gain_ctrl.h"

#define CONFIG_SEND_FREQUENCY      100
#if CONFIG_IDF_TARGET_ESP32C5 || CONFIG_IDF_TARGET_ESP32C61
#define CSI_FORCE_LLTF                      0
#endif
#define CONFIG_FORCE_GAIN                   0

#if CONFIG_IDF_TARGET_ESP32S3 || CONFIG_IDF_TARGET_ESP32C3 || CONFIG_IDF_TARGET_ESP32C5 || CONFIG_IDF_TARGET_ESP32C6 || CONFIG_IDF_TARGET_ESP32C61
#define CONFIG_GAIN_CONTROL                 1
#endif

#if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(6, 0, 0)
#define ESP_IF_WIFI_STA ESP_MAC_WIFI_STA
#endif

static const char *TAG = "csi_recv_router";

/* ---- RFVISION runtime Wi-Fi provisioning (additive) -----------------------
 * Replaces the permanent build-time credential assumption with NVS-backed
 * runtime credentials set over the existing USB-serial link. Validated
 * acquisition behavior (CSI format/filter, 100 Hz gateway ping) is
 * untouched: when no runtime credentials are stored, boot executes the
 * original path (example_connect -> wifi_csi_init -> ping) identically.
 *
 * Host protocol (host side: csi/transport/provisioning.py):
 *   Host -> RFV_PROV_BEGIN / RFV_SSID:<s> / RFV_PASS:<p> /
 *           RFV_PROV_COMMIT / RFV_PROV_ABORT / RFV_NET_STATUS
 *   Node -> RFV_OK <token> / RFV_ERR <reason> /
 *           RFV_NET ssid=<s> bssid=<m> channel=<c> ip=<a>
 * Passwords are NEVER printed. Run provisioning while the host live
 * provider is stopped so RFV_* lines never enter the CSI parser.
 */
#define RFV_NVS_NAMESPACE "rfvision"
#define RFV_PROV_LINE_LEN 160

/* Forward declarations (defined below; unchanged validated functions). */
static void wifi_csi_init(void);
static esp_err_t wifi_ping_router_start(void);

static char s_staged_ssid[33] = {0};
static char s_staged_pass[65] = {0};
static bool s_staged_has_ssid = false;

/* While a provisioning session is active the CSI line flood is
 * suppressed so RFV_* reply lines stay parseable (ROM ets_printf has
 * no cross-task line atomicity). Auto-expires after 30 s so a
 * dropped host can never silence the node permanently. */
static volatile bool s_rfv_quiet = false;
static TickType_t s_rfv_quiet_until = 0;

static bool rfv_load_runtime_creds(char *ssid_out, char *pass_out)
{
    nvs_handle_t handle = 0;
    if (nvs_open(RFV_NVS_NAMESPACE, NVS_READONLY, &handle) != ESP_OK) {
        return false;
    }
    size_t ssid_len = sizeof(s_staged_ssid);
    size_t pass_len = sizeof(s_staged_pass);
    bool ok = (nvs_get_str(handle, "ssid", ssid_out, &ssid_len) == ESP_OK)
        && (nvs_get_str(handle, "pass", pass_out, &pass_len) == ESP_OK)
        && (ssid_len > 1) && (ssid_len <= sizeof(s_staged_ssid));
    nvs_close(handle);
    return ok;
}

static esp_err_t rfv_store_runtime_creds(const char *ssid, const char *pass)
{
    nvs_handle_t handle = 0;
    esp_err_t err = nvs_open(RFV_NVS_NAMESPACE, NVS_READWRITE, &handle);
    if (err != ESP_OK) {
        return err;
    }
    err = nvs_set_str(handle, "ssid", ssid);
    if (err == ESP_OK) {
        err = nvs_set_str(handle, "pass", pass);
    }
    if (err == ESP_OK) {
        err = nvs_commit(handle);
    }
    nvs_close(handle);
    return err;
}

static void rfv_emit_net_status(void)
{
    wifi_ap_record_t ap = {0};
    esp_netif_ip_info_t ip = {0};
    if (esp_wifi_sta_get_ap_info(&ap) != ESP_OK) {
        ets_printf("RFV_ERR not-associated\n");
        return;
    }
    esp_netif_get_ip_info(esp_netif_get_handle_from_ifkey("WIFI_STA_DEF"), &ip);
    /* NOTE: ROM ets_printf has no %.*s — copy to a NUL-terminated buffer. */
    char ssid[sizeof(ap.ssid) + 1];
    memcpy(ssid, ap.ssid, sizeof(ap.ssid));
    ssid[sizeof(ap.ssid)] = '\0';
    ets_printf("RFV_NET ssid=%s bssid=" MACSTR " channel=%d ip=" IPSTR "\n",
               ssid, MAC2STR(ap.bssid), ap.primary,
               IP2STR(&ip.ip));
}

static bool rfv_wait_for_ip(uint32_t timeout_ms)
{
    esp_netif_ip_info_t ip = {0};
    uint32_t waited = 0;
    while (waited < timeout_ms) {
        esp_netif_get_ip_info(esp_netif_get_handle_from_ifkey("WIFI_STA_DEF"), &ip);
        if (ip.ip.addr != 0) {
            return true;
        }
        vTaskDelay(pdMS_TO_TICKS(200));
        waited += 200;
    }
    return false;
}

static esp_err_t rfv_wifi_reconnect(const char *ssid, const char *pass); /* below */
static void rfv_clear_runtime_creds(void)
{
    nvs_handle_t handle = 0;
    if (nvs_open(RFV_NVS_NAMESPACE, NVS_READWRITE, &handle) != ESP_OK) {
        return;
    }
    nvs_erase_key(handle, "ssid");
    nvs_erase_key(handle, "pass");
    nvs_commit(handle);
    nvs_close(handle);
}

/* Join an AP, absorbing races with the example_connect retry handler
 * (it may call esp_wifi_connect() concurrently -> ESP_ERR_WIFI_STATE).
 * Returns ESP_OK only when an IP is actually bound. */
static esp_err_t rfv_join_blocking(const char *ssid, const char *pass,
                                   uint32_t ip_timeout_ms)
{
    wifi_config_t cfg = {0};
    strncpy((char *)cfg.sta.ssid, ssid, sizeof(cfg.sta.ssid));
    strncpy((char *)cfg.sta.password, pass, sizeof(cfg.sta.password));
    cfg.sta.threshold.authmode =
        (pass[0] == '\0') ? WIFI_AUTH_OPEN : WIFI_AUTH_WPA2_PSK;
    for (int attempt = 0; attempt < 4; attempt++) {
        esp_wifi_disconnect();
        vTaskDelay(pdMS_TO_TICKS(200));
        /* Quiesce the driver: the example_connect retry handler calls
         * esp_wifi_connect() on every disconnect event, which otherwise
         * holds the driver in "connecting" state so set_config() can
         * never succeed (observed: "sta is connecting, cannot set
         * config" loop). Stop/start is a clean slate; the handler
         * goes idle once our own connect+IP completes. */
        esp_wifi_stop();
        vTaskDelay(pdMS_TO_TICKS(300));
        esp_wifi_start();
        vTaskDelay(pdMS_TO_TICKS(300));
        if (esp_wifi_set_config(WIFI_IF_STA, &cfg) != ESP_OK) {
            vTaskDelay(pdMS_TO_TICKS(500));
            continue;
        }
        if (esp_wifi_connect() != ESP_OK) {
            vTaskDelay(pdMS_TO_TICKS(500));
            continue;
        }
        if (rfv_wait_for_ip(ip_timeout_ms)) {
            return ESP_OK;
        }
    }
    return ESP_ERR_TIMEOUT;
}

static esp_err_t rfv_wifi_reconnect(const char *ssid, const char *pass)
{
    if (rfv_join_blocking(ssid, pass, 20000) != ESP_OK) {
        return ESP_ERR_TIMEOUT;
    }
    /* Re-bind CSI + stimulus to the NEW association (same functions,
     * same parameters as boot — no behavior change, new target only). */
    wifi_csi_init();
    wifi_ping_router_start();
    return ESP_OK;
}

/* Reconnect with stored runtime credentials when present. When they are
 * absent, the validated Kconfig boot path is untouched. A stored network
 * that is currently unreachable falls back to the Kconfig AP; this
 * function only returns ESP_OK while associated, so downstream CSI init
 * (which requires an association) can never observe a torn-down link.
 * Last resort when nothing is reachable: drop the poisoned record and
 * reboot into the clean Kconfig path instead of boot-looping. */
static esp_err_t rfv_runtime_reconnect_if_stored(void)
{
    char ssid[33] = {0};
    char pass[65] = {0};
    if (!rfv_load_runtime_creds(ssid, pass)) {
        return ESP_OK;
    }
    ESP_LOGI(TAG, "runtime credentials present; joining stored network");
    for (int round = 0; round < 3; round++) {
        if (rfv_join_blocking(ssid, pass, 8000) == ESP_OK) {
            return ESP_OK;
        }
        ESP_LOGW(TAG, "stored join attempt %d failed; retrying", round + 1);
    }
    ESP_LOGW(TAG, "stored network unreachable; falling back to Kconfig AP");
    if (rfv_join_blocking(CONFIG_EXAMPLE_WIFI_SSID,
                           CONFIG_EXAMPLE_WIFI_PASSWORD,
                           20000) == ESP_OK) {
        return ESP_OK;
    }
    ESP_LOGE(TAG, "no known network reachable; clearing stored creds");
    rfv_clear_runtime_creds();
    vTaskDelay(pdMS_TO_TICKS(500));
    esp_restart();
    return ESP_FAIL; /* unreachable */
}

static void rfv_handle_prov_line(const char *line)
{
    if (strcmp(line, "RFV_PROV_BEGIN") == 0) {
        s_staged_has_ssid = false;
        s_staged_ssid[0] = '\0';
        s_staged_pass[0] = '\0';
        s_rfv_quiet = true;
        s_rfv_quiet_until = xTaskGetTickCount() + pdMS_TO_TICKS(30000);
        ets_printf("RFV_OK BEGIN\n");
    } else if (strncmp(line, "RFV_SSID:", 9) == 0) {
        const char *ssid = line + 9;
        if (ssid[0] == '\0' || strlen(ssid) > 32) {
            ets_printf("RFV_ERR bad-ssid-length\n");
            return;
        }
        strncpy(s_staged_ssid, ssid, sizeof(s_staged_ssid) - 1);
        s_staged_has_ssid = true;
        ets_printf("RFV_OK SSID\n");
    } else if (strncmp(line, "RFV_PASS:", 9) == 0) {
        const char *pass = line + 9;
        if (strlen(pass) > 64) {
            ets_printf("RFV_ERR bad-pass-length\n");
            return;
        }
        strncpy(s_staged_pass, pass, sizeof(s_staged_pass) - 1);
        ets_printf("RFV_OK PASS\n");
    } else if (strcmp(line, "RFV_PROV_ABORT") == 0) {
        s_staged_has_ssid = false;
        s_rfv_quiet = false;
        ets_printf("RFV_OK ABORTED\n");
    } else if (strcmp(line, "RFV_PROV_COMMIT") == 0) {
        if (!s_staged_has_ssid) {
            ets_printf("RFV_ERR no-ssid-staged\n");
            return;
        }
        if (rfv_store_runtime_creds(s_staged_ssid, s_staged_pass) != ESP_OK) {
            ets_printf("RFV_ERR nvs-store-failed\n");
            return;
        }
        ets_printf("RFV_OK STORED\n");
        /* NOTE: staged password bytes stay in RAM only; never printed. */
        s_rfv_quiet_until = xTaskGetTickCount() + pdMS_TO_TICKS(120000);
        if (rfv_wifi_reconnect(s_staged_ssid, s_staged_pass) != ESP_OK) {
            ets_printf("RFV_ERR reconnect-failed\n");
            s_rfv_quiet = false;
            return;
        }
        ets_printf("RFV_OK CONNECTED\n");
        rfv_emit_net_status();
        s_rfv_quiet = false;
    } else if (strcmp(line, "RFV_NET_STATUS") == 0) {
        rfv_emit_net_status();
    }
}

/* UART RX task on the console UART (RX only; TX stays ROM ets_printf, so
 * CSI_DATA output is unaffected). If the driver cannot attach, the task
 * exits silently: acquisition continues, provisioning just stays
 * unavailable until reflash. */
static void rfv_prov_task(void *arg)
{
    (void)arg;
    if (uart_driver_install(UART_NUM_0, 2048, 256, 0, NULL, 0) != ESP_OK) {
        ESP_LOGW(TAG, "prov UART unavailable; runtime provisioning off");
        vTaskDelete(NULL);
        return;
    }
    static char line[RFV_PROV_LINE_LEN];
    static size_t pos = 0;
    uint8_t chunk[64];
    for (;;) {
        int n = uart_read_bytes(UART_NUM_0, chunk, sizeof(chunk),
                                pdMS_TO_TICKS(100));
        if (n <= 0) {
            continue;
        }
        for (int i = 0; i < n; i++) {
            char c = (char)chunk[i];
            if (c == '\n') {
                line[pos] = '\0';
                if (pos > 0 && line[pos - 1] == '\r') {
                    line[pos - 1] = '\0';
                }
                if (strncmp(line, "RFV_", 4) == 0) {
                    rfv_handle_prov_line(line);
                }
                pos = 0;
            } else if (pos < sizeof(line) - 1) {
                line[pos++] = c;
            } else {
                pos = 0; /* overlong line: drop, never act on truncation */
            }
        }
    }
}

static void wifi_csi_rx_cb(void *ctx, wifi_csi_info_t *info)
{
    if (!info || !info->buf) {
        ESP_LOGW(TAG, "<%s> wifi_csi_cb", esp_err_to_name(ESP_ERR_INVALID_ARG));
        return;
    }

    if (memcmp(info->mac, ctx, 6)) {
        return;
    }

    /* Provisioning session: suppress the CSI flood so RFV_* reply lines
     * stay parseable. Auto-clears on expiry (see s_rfv_quiet_until). */
    if (s_rfv_quiet) {
        if ((int32_t)(xTaskGetTickCount() - s_rfv_quiet_until) >= 0) {
            s_rfv_quiet = false;
        } else {
            return;
        }
    }

    const wifi_pkt_rx_ctrl_t *rx_ctrl = &info->rx_ctrl;
    static int s_count = 0;
    float compensate_gain = 1.0f;
    static uint8_t agc_gain = 0;
    static int8_t fft_gain = 0;
#if CONFIG_GAIN_CONTROL
    static uint8_t agc_gain_baseline = 0;
    static int8_t fft_gain_baseline = 0;
    esp_csi_gain_ctrl_get_rx_gain(rx_ctrl, &agc_gain, &fft_gain);
    if (s_count < 100) {
        esp_csi_gain_ctrl_record_rx_gain(agc_gain, fft_gain);
    } else if (s_count == 100) {
        esp_csi_gain_ctrl_get_rx_gain_baseline(&agc_gain_baseline, &fft_gain_baseline);
#if CONFIG_FORCE_GAIN
        esp_csi_gain_ctrl_set_rx_force_gain(agc_gain_baseline, fft_gain_baseline);
        ESP_LOGI(TAG, "fft_force %d, agc_force %d", fft_gain_baseline, agc_gain_baseline);
#endif
    }
    esp_csi_gain_ctrl_get_gain_compensation(&compensate_gain, agc_gain, fft_gain);
    ESP_LOGD(TAG, "compensate_gain %f, agc_gain %d, fft_gain %d", compensate_gain, agc_gain, fft_gain);
#endif

#if CONFIG_IDF_TARGET_ESP32C5 || CONFIG_IDF_TARGET_ESP32C6 || CONFIG_IDF_TARGET_ESP32C61
    if (!s_count) {
        ESP_LOGI(TAG, "================ CSI RECV ================");
        ets_printf("type,seq,mac,rssi,rate,noise_floor,fft_gain,agc_gain,channel,local_timestamp,sig_len,rx_format,len,first_word,data\n");
    }
    ets_printf("CSI_DATA,%d," MACSTR ",%d,%d,%d,%d,%d,%d,%d,%d,%d",
               s_count, MAC2STR(info->mac), rx_ctrl->rssi, rx_ctrl->rate,
               rx_ctrl->noise_floor, fft_gain, agc_gain, rx_ctrl->channel,
               rx_ctrl->timestamp, rx_ctrl->sig_len, rx_ctrl->cur_bb_format);
#else
    if (!s_count) {
        ESP_LOGI(TAG, "================ CSI RECV ================");
        ets_printf("type,id,mac,rssi,rate,sig_mode,mcs,bandwidth,smoothing,not_sounding,aggregation,stbc,fec_coding,sgi,noise_floor,ampdu_cnt,channel,secondary_channel,local_timestamp,ant,sig_len,rx_format,len,first_word,data\n");
    }
    ets_printf("CSI_DATA,%d," MACSTR ",%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d",
               s_count, MAC2STR(info->mac), rx_ctrl->rssi, rx_ctrl->rate, rx_ctrl->sig_mode,
               rx_ctrl->mcs, rx_ctrl->cwb, rx_ctrl->smoothing, rx_ctrl->not_sounding,
               rx_ctrl->aggregation, rx_ctrl->stbc, rx_ctrl->fec_coding, rx_ctrl->sgi,
               rx_ctrl->noise_floor, rx_ctrl->ampdu_cnt, rx_ctrl->channel, rx_ctrl->secondary_channel,
               rx_ctrl->timestamp, rx_ctrl->ant, rx_ctrl->sig_len, rx_ctrl->sig_mode);
#endif

#if (CONFIG_IDF_TARGET_ESP32C5 || CONFIG_IDF_TARGET_ESP32C61) && CSI_FORCE_LLTF

    int16_t csi = ((int16_t)(((((uint16_t)info->buf[1]) << 8) | info->buf[0]) << 4) >> 4);
    ets_printf(",%d,%d,\"[%d", (info->len - 2) / 2, info->first_word_invalid, (int16_t)(compensate_gain * csi));
    for (int i = 2; i < (info->len - 2); i += 2) {
        csi = ((int16_t)(((((uint16_t)info->buf[i + 1]) << 8) | info->buf[i]) << 4) >> 4);
        ets_printf(",%d", (int16_t)(compensate_gain * csi));
    }

#else
    ets_printf(",%d,%d,\"[%d", info->len, info->first_word_invalid, (int16_t)(compensate_gain * info->buf[0]));
    for (int i = 1; i < info->len; i++) {
        ets_printf(",%d", (int16_t)(compensate_gain * info->buf[i]));
    }
#endif
    ets_printf("]\"\n");
    s_count++;
}

static void wifi_csi_init(void)
{
    /**
     * @brief In order to ensure the compatibility of routers, only LLTF sub-carriers are selected.
     */
#if CONFIG_IDF_TARGET_ESP32C5 || CONFIG_IDF_TARGET_ESP32C61
    wifi_csi_config_t csi_config = {
        .enable                   = true,
        .acquire_csi_legacy       = true,
        .acquire_csi_force_lltf   = CSI_FORCE_LLTF,
        .acquire_csi_ht20         = true,
        .acquire_csi_ht40         = true,
        .acquire_csi_vht          = false,
        .acquire_csi_su           = false,
        .acquire_csi_mu           = false,
        .acquire_csi_dcm          = false,
        .acquire_csi_beamformed   = false,
        .acquire_csi_he_stbc_mode = 2,
        .val_scale_cfg            = 0,
        .dump_ack_en              = false,
        .reserved                 = false
    };
#elif CONFIG_IDF_TARGET_ESP32C6
    wifi_csi_config_t csi_config = {
        .enable                 = true,
        .acquire_csi_legacy     = true,
        .acquire_csi_ht20       = true,
        .acquire_csi_ht40       = true,
        .acquire_csi_su         = false,
        .acquire_csi_mu         = false,
        .acquire_csi_dcm        = false,
        .acquire_csi_beamformed = false,
        .acquire_csi_he_stbc    = 2,
        .val_scale_cfg          = false,
        .dump_ack_en            = false,
        .reserved               = false
    };
#else
    wifi_csi_config_t csi_config = {
        .lltf_en           = true,
        .htltf_en          = false,
        .stbc_htltf2_en    = false,
        .ltf_merge_en      = true,
        .channel_filter_en = true,
        .manu_scale        = true,
        .shift             = true,
    };
#endif
    static wifi_ap_record_t s_ap_info = {0};
    ESP_ERROR_CHECK(esp_wifi_sta_get_ap_info(&s_ap_info));
    ESP_ERROR_CHECK(esp_wifi_set_csi_config(&csi_config));
    ESP_ERROR_CHECK(esp_wifi_set_csi_rx_cb(wifi_csi_rx_cb, s_ap_info.bssid));
    ESP_ERROR_CHECK(esp_wifi_set_csi(true));
}

static esp_err_t wifi_ping_router_start(void)
{
    static esp_ping_handle_t ping_handle = NULL;

    /* Reconnect path calls this again for the new gateway: retire the
     * previous session first (no-op on first boot when NULL). */
    if (ping_handle != NULL) {
        esp_ping_stop(ping_handle);
        esp_ping_delete_session(ping_handle);
        ping_handle = NULL;
    }

    esp_ping_config_t ping_config = ESP_PING_DEFAULT_CONFIG();
    ping_config.count             = 0;
    ping_config.interval_ms       = 1000 / CONFIG_SEND_FREQUENCY;
    ping_config.task_stack_size   = 3072;
    ping_config.data_size         = 1;

    esp_netif_ip_info_t local_ip;
    esp_netif_get_ip_info(esp_netif_get_handle_from_ifkey("WIFI_STA_DEF"), &local_ip);
    ESP_LOGI(TAG, "got ip:" IPSTR ", gw: " IPSTR, IP2STR(&local_ip.ip), IP2STR(&local_ip.gw));
    ping_config.target_addr.u_addr.ip4.addr = ip4_addr_get_u32(&local_ip.gw);
    ping_config.target_addr.type = ESP_IPADDR_TYPE_V4;

    esp_ping_callbacks_t cbs = { 0 };
    esp_ping_new_session(&ping_config, &cbs, &ping_handle);
    esp_ping_start(ping_handle);

    return ESP_OK;
}

void app_main()
{
    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    /**
     * @brief This helper function configures Wi-Fi, as selected in menuconfig.
     *        Read "Establishing Wi-Fi Connection" section in esp-idf/examples/protocols/README.md
     *        for more information about this function.
     */
    ESP_ERROR_CHECK(example_connect());

    /* Runtime provisioning: joins the NVS-stored network when present,
     * no-op otherwise (validated boot path identical). Never aborts:
     * a stored network that is currently unreachable must fall back to
     * the Kconfig AP via the example_connect retry loop, not reboot. */
    if (rfv_runtime_reconnect_if_stored() != ESP_OK) {
        ESP_LOGW(TAG, "stored reconnect failed; staying on Kconfig AP");
    }

    wifi_csi_init();
    wifi_ping_router_start();
    xTaskCreate(rfv_prov_task, "rfv_prov", 3072, NULL,
                tskIDLE_PRIORITY + 1, NULL);
}
