import requests
import time
import json
import os
from datetime import datetime
from flask import Flask
from threading import Thread
import sys

print(f"Python version: {sys.version}")
print(f"Timezone set to: {os.environ.get('TZ')}")
# Set múi giờ Việt Nam
os.environ["TZ"] = "Asia/Ho_Chi_Minh"
try:
    time.tzset()
except:
    pass  # Windows không có tzset

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is alive!"


def run():
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()


# ===== META ADS =====
META_TOKEN = "EAAafzAo8hZAgBQ4ToAl5BounoYvYgUzvvHbterNXxui4OnsyHwXgiIaix2TfaeuHzsOTkH8m5D6sLSF4PGJmZAlXXyX6sVKfkZCFZC8A76ZBpYEFVchf5JbSkWM0mZBr7A511p0LCoa18V4Fr1IEHuyxYtGsVUxD6IWpppZA3krZA2WcKbKd1aQ3RSjnnAtX32XMoXDZAhJbJAKrKS6jvNlCAtNSKPeU9dF3AVefGakMRWUXReMBTACModL36G2yrLF7cY0HnqbWTii8hcePmZAehoOykN"
AD_ACCOUNT_ID = "act_460351299625267"
MY_NAME = "Nguyễn Hữu Huy"

# ===== TELEGRAM COMMAND =====
LAST_UPDATE_ID = None

# ===== TELEGRAM =====
TELEGRAM_TOKEN = "8689152984:AAEt7KA8lVhPjH-e85DKS_hN39EnVjaYfFI"
CHAT_ID = "6511673241"

# ===== MARKETING USERNAME =====
MY_USERNAME = "NhatTam045"

# ===== SANDBOX API =====
url = "https://api.sandbox.com.vn/contact/api/HoSoKhachHang/GetHoSoKhachHang_LeadMKT_Search"

headers = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://duocnhattam.sandbox.com.vn",
    "referer": "https://duocnhattam.sandbox.com.vn/",
    "user-agent": "Mozilla/5.0",
}

cookies = {
    "prouid": "4a915cef-6c5c-4a5a-9add-19fac8f0f54b",
    "protoken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjRhOTE1Y2VmLTZjNWMtNGE1YS05YWRkLTE5ZmFjOGYwZjU0YiIsInRob2lnaWFuIjoiMTc3MzQ0Mjk2MiIsImRvbWFpbiI6ImR1b2NuaGF0dGFtLnNhbmRib3guY29tLnZuIiwiZGV2aWNlIjoiZGVhZDI1ZDAtZWM5Yi00NDcwLTgxMGEtNmIzOTUyMDYxOTkxIiwibmJmIjoxNzczNDQyOTYyLCJleHAiOjE3NzQwNDc3NjIsImlhdCI6MTc3MzQ0Mjk2Mn0.-4v384YV6JWwmYSnVT6_PR_PrwL7O-Lw89tL-qozMCI",
    "prorefreshToken": "4339EF0B46D6563D86776b021ab241998eb15d5271a43cb5",
}

sent_orders = set()

report_1140_sent = False
report_1330_sent = False
report_15_sent = False
report_17_sent = False


def get_time_vn():
    """Lấy thời gian Việt Nam"""
    return datetime.now()


def send_telegram(msg):
    url_tele = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url_tele, data={"chat_id": CHAT_ID, "text": msg})
    except:
        print(f"Không gửi được Telegram lúc {get_time_vn().strftime('%H:%M:%S')}")


# ===== ADS REPORT =====
def get_ads_report():
    # ===== LẤY DANH SÁCH CAMPAIGN =====
    url_campaigns = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}/campaigns"

    params_camp = {
        "access_token": META_TOKEN,
        "fields": "id,name,status",
        "limit": 100,
    }

    res_camp = requests.get(url_campaigns, params=params_camp)
    data_camp = res_camp.json()

    campaign_names = {}  # Tất cả campaign của bạn (kể cả không có nhóm)

    if "data" in data_camp:
        for camp in data_camp["data"]:
            if MY_NAME in camp.get("name", ""):
                campaign_names[camp["id"]] = camp.get("name")

    # ===== LẤY DANH SÁCH ADSET =====
    url_adsets = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}/adsets"

    params_adsets = {
        "access_token": META_TOKEN,
        "fields": "id,name,campaign_id,status",
        "limit": 200,
    }

    res_adsets = requests.get(url_adsets, params=params_adsets)
    data_adsets = res_adsets.json()

    # Campaign có nhóm đang hoạt động
    campaigns_with_active_adsets = set()
    my_active_adsets = set()
    all_my_adsets = set()

    if "data" in data_adsets:
        for adset in data_adsets["data"]:
            if adset["campaign_id"] in campaign_names:
                all_my_adsets.add(adset["id"])
                if adset.get("status") == "ACTIVE":
                    my_active_adsets.add(adset["id"])
                    campaigns_with_active_adsets.add(adset["campaign_id"])

    # ===== LẤY DỮ LIỆU CHI TIÊU =====
    url_insights = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}/insights"

    params_insights = {
        "access_token": META_TOKEN,
        "level": "adset",
        "fields": "campaign_id,campaign_name,adset_id,adset_name,spend,actions",
        "date_preset": "today",
        "limit": 500,
    }

    res_insights = requests.get(url_insights, params=params_insights)
    data_insights = res_insights.json()

    total_spend = 0
    total_contact = 0

    bad_120 = []
    bad_240 = []
    bad_360 = []

    if "data" in data_insights:
        for ad in data_insights["data"]:
            campaign_id = ad.get("campaign_id")

            if campaign_id in campaign_names:
                spend = float(ad.get("spend", 0))
                total_spend += spend

                contact = 0
                for act in ad.get("actions", []):
                    if (
                        act["action_type"]
                        == "onsite_conversion.messaging_conversation_started_7d"
                    ):
                        contact = int(act["value"])

                total_contact += contact

                adset_id = ad.get("adset_id")
                if adset_id in my_active_adsets:
                    adset_name = ad.get("adset_name", "")

                    if spend > 120000 and contact == 0:
                        bad_120.append(adset_name)
                    if spend > 240000 and contact <= 1:
                        bad_240.append(adset_name)
                    if spend > 360000 and contact <= 3:
                        bad_360.append(adset_name)

    bad_120 = list(set(bad_120))
    bad_240 = list(set(bad_240))
    bad_360 = list(set(bad_360))

    print(f"✅ Đã gửi báo cáo ADS lúc {get_time_vn().strftime('%H:%M:%S')}")

    msg = f"""
📊 ADS MANAGER

Campaign đang hoạt động (có nhóm chạy): {len(campaigns_with_active_adsets)}
Nhóm quảng cáo đang hoạt động: {len(my_active_adsets)}

💰 Chi tiêu trong ngày: {int(total_spend):,}đ
💬 Liên hệ mới trong ngày: {total_contact}

⚠️ >120k chưa có tin: {len(bad_120)}
⚠️ >240k ≤1 tin: {len(bad_240)}
⚠️ >360k ≤3 tin: {len(bad_360)}
"""
    return msg


def stop_my_ads():
    # Lấy tất cả ADSET đang ACTIVE của bạn
    url_adsets = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}/adsets"

    params_adsets = {
        "access_token": META_TOKEN,
        "fields": "id,name,campaign_name,status",
        "limit": 200,
    }

    res_adsets = requests.get(url_adsets, params=params_adsets)
    data_adsets = res_adsets.json()

    stopped_adsets = []

    if "data" in data_adsets:
        for adset in data_adsets["data"]:
            if (
                MY_NAME in adset.get("campaign_name", "")
                and adset.get("status") == "ACTIVE"
            ):
                adset_id = adset["id"]
                adset_name = adset.get("name")

                # Tắt ADSET
                stop_url = f"https://graph.facebook.com/v24.0/{adset_id}"
                stop_res = requests.post(
                    stop_url, data={"access_token": META_TOKEN, "status": "PAUSED"}
                )

                if stop_res.json().get("success"):
                    stopped_adsets.append(adset_name)

    total_stopped = len(stopped_adsets)

    # Chỉ hiện 1 dòng thông báo gọn
    print(
        f"✅ Đã tắt {total_stopped} nhóm quảng cáo lúc {get_time_vn().strftime('%H:%M:%S')}"
    )

    msg = f"""
🛑 ĐÃ TẮT NHÓM QUẢNG CÁO

Đã tắt: {total_stopped} nhóm quảng cáo
"""

    send_telegram(msg)


# ===== TELEGRAM COMMAND =====
def check_telegram_commands():

    global LAST_UPDATE_ID

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"

    params = {"timeout": 1}

    if LAST_UPDATE_ID:
        params["offset"] = LAST_UPDATE_ID + 1

    res = requests.get(url, params=params).json()

    if not res["ok"]:
        return

    for update in res["result"]:

        LAST_UPDATE_ID = update["update_id"]

        if "message" not in update:
            continue

        text = update["message"].get("text", "")

        if text == "/ads":
            send_telegram(get_ads_report())

        elif text == "/stopads":
            stop_my_ads()


def get_payload():
    today = get_time_vn().strftime("%Y-%m-%d")

    return {
        "date": [f"{today}T00:00:00+07:00", f"{today}T23:59:59+07:00"],
        "tuNgay": f"{today}T00:00:00+07:00",
        "denNgay": f"{today}T23:59:59+07:00",
        "pageInfo": {"page": 1, "pageSize": 50},
        "sorts": [],
    }


print("Bot Sandbox đã khởi động")
keep_alive()

while True:
    try:
        check_telegram_commands()

        payload = get_payload()

        res = requests.post(url, headers=headers, cookies=cookies, json=payload)

        data = res.json()

        leads_today = []
        orders_today = []
        total_money = 0

        phone_first_owner = {}

        if "data" in data:

            for lead in data["data"]:

                phone = lead.get("khachHangSoDienThoai")
                marketing = lead.get("marketingUserName")

                if phone not in phone_first_owner:
                    phone_first_owner[phone] = marketing

            for lead in data["data"]:

                phone = lead.get("khachHangSoDienThoai")
                marketing = lead.get("marketingUserName")

                if marketing != MY_USERNAME:
                    continue

                if lead.get("isKhachCu"):
                    continue

                if phone_first_owner.get(phone) != MY_USERNAME:
                    continue

                leads_today.append(lead)

            for lead in leads_today:

                if lead.get("lgtDonHangTrangThaiChotDon") == 1:

                    orders_today.append(lead)

                    money = round(lead.get("lgtDonHangTienThuKhach") or 0)
                    total_money += money

                    if lead["id"] not in sent_orders:

                        name = lead.get("khachHangTen")
                        phone = lead.get("khachHangSoDienThoai")
                        sale = lead.get("saleDisplayName")

                        msg = f"""
💰 {money:,.0f}đ
👤 {name} | 📞 {phone}
👩 Sale: {sale}
"""

                        send_telegram(msg)

                        sent_orders.add(lead["id"])

            now = get_time_vn()

            leads_count = len(leads_today)
            orders_count = len(orders_today)

            cr = 0
            if leads_count > 0:
                cr = round((orders_count / leads_count) * 100, 2)

            report = f"""
📊 BÁO CÁO ADS HÔM NAY

Lead: {leads_count}
Đơn: {orders_count}
Doanh thu: {total_money:,}đ
CR: {cr}%
"""
            if (
                now.hour == 11
                and now.minute == 40
                and now.second < 30
                and not report_1140_sent
            ):
                send_telegram(report)
                report_1140_sent = True

            if (
                now.hour == 13
                and now.minute == 30
                and now.second < 30
                and not report_1330_sent
            ):
                send_telegram(report)
                report_1330_sent = True

            if (
                now.hour == 15
                and now.minute == 0
                and now.second < 30
                and not report_15_sent
            ):
                send_telegram(report)
                report_15_sent = True

            if (
                now.hour == 17
                and now.minute == 0
                and now.second < 30
                and not report_17_sent
            ):
                send_telegram(report)
                report_17_sent = True

        print(
            f"\r🟢 Bot running | {get_time_vn().strftime('%H:%M:%S')}",
            end="",
            flush=True,
        )

    except Exception as e:
        print(f"\nLỗi lúc {get_time_vn().strftime('%H:%M:%S')}: {e}")

    time.sleep(30)
