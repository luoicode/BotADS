import requests
import time
import json
import os
from datetime import datetime
from flask import Flask
from threading import Thread
import pytz

# Set múi giờ Việt Nam
vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")


def get_time_vn():
    """Lấy thời gian Việt Nam"""
    return datetime.now(vn_tz)


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
META_TOKEN = "EAAafzAo8hZAgBQySvDvftjo0f68ZBLXdUuM9f6cvxiyIlHnlF1NfATIgy0trVAuFhoHMtSzy6tz3bZC7QpPAziuiZBmw3cuDUs0hlIsd0l7wf4QMDBQvnmyYyNRHebvgQMiV0ag5t4BtLiNYsAsPOMKllq33kOuo2NCizFSDTGEyGx944ZAbKugPO7iEZC5qfgUAZDZD"
AD_ACCOUNT_ID = "act_460351299625267"
MY_NAME = "Nguyễn Hữu Huy"

# ===== TELEGRAM =====
TELEGRAM_TOKEN = "8689152984:AAEt7KA8lVhPjH-e85DKS_hN39EnVjaYfFI"
CHAT_ID = "6511673241"
LAST_UPDATE_ID = None
last_command_time = 0
last_command_text = ""

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
processed_updates = set()

report_1140_sent = False
report_1330_sent = False
report_15_sent = False
report_17_sent = False

# ===== CHECK EXPIRY DATES =====
EXPIRY_CHECKED = False
META_EXPIRY = 1778780378  # 15/05/2026
SANDWICH_EXPIRY = 1774047762  # 20/03/2026


def check_expiry_dates():
    """Kiểm tra và thông báo các mục sắp hết hạn"""
    global EXPIRY_CHECKED

    if EXPIRY_CHECKED:
        return

    now = time.time()
    warnings = []

    # Kiểm tra Meta Token
    days_left = (META_EXPIRY - now) / 86400
    if days_left < 7:
        warnings.append(
            f"⚠️ Meta Token sắp hết hạn: {int(days_left)} ngày ({datetime.fromtimestamp(META_EXPIRY, vn_tz).strftime('%d/%m/%Y')})"
        )
    elif days_left < 30:
        warnings.append(
            f"📅 Meta Token còn: {int(days_left)} ngày ({datetime.fromtimestamp(META_EXPIRY, vn_tz).strftime('%d/%m/%Y')})"
        )

    # Kiểm tra Sandbox Token
    days_left = (SANDWICH_EXPIRY - now) / 86400
    if days_left < 3:
        warnings.append(
            f"⚠️⚠️ SANDWICH TOKEN HẾT HẠN TRONG {int(days_left)} NGÀY! ({datetime.fromtimestamp(SANDWICH_EXPIRY, vn_tz).strftime('%d/%m/%Y')})"
        )
    elif days_left < 7:
        warnings.append(
            f"⚠️ Sandwich Token sắp hết hạn: {int(days_left)} ngày ({datetime.fromtimestamp(SANDWICH_EXPIRY, vn_tz).strftime('%d/%m/%Y')})"
        )
    else:
        warnings.append(f"✅ Sandwich Token còn: {int(days_left)} ngày")

    # Kiểm tra Railway
    now_vn = get_time_vn()
    hours_used = (now_vn.day - 1) * 24 + now_vn.hour
    hours_left = 500 - hours_used

    if hours_left < 0:
        warnings.append(f"⚠️⚠️ RAILWAY ĐÃ HẾT GIỜ ({hours_used}/500 giờ)! Bot sẽ ngủ.")
    elif hours_left < 50:
        warnings.append(f"⚠️ Railway còn: {hours_left} giờ ({hours_used}/500)")
    else:
        warnings.append(f"✅ Railway còn: {hours_left} giờ")

    # Gửi thông báo
    if warnings:
        msg = "🔔 **KIỂM TRA HẠN SỬ DỤNG**\n\n" + "\n".join(warnings)
        send_telegram(msg)
        print(f"\n{'='*50}\n{msg}\n{'='*50}")

    EXPIRY_CHECKED = True


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

    campaign_names = {}

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

    campaigns_with_active_adsets = set()
    my_active_adsets = set()

    if "data" in data_adsets:
        for adset in data_adsets["data"]:
            if adset["campaign_id"] in campaign_names:
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

Campaign đang hoạt động: {len(campaigns_with_active_adsets)}
Nhóm quảng cáo đang hoạt động: {len(my_active_adsets)}

💰 Chi tiêu trong ngày: {int(total_spend):,}đ
💬 Liên hệ mới trong ngày: {total_contact}

⚠️ >120k chưa có tin: {len(bad_120)}
⚠️ >240k ≤1 tin: {len(bad_240)}
⚠️ >360k ≤3 tin: {len(bad_360)}
"""
    return msg


def stop_my_ads():
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

                stop_url = f"https://graph.facebook.com/v24.0/{adset_id}"
                stop_res = requests.post(
                    stop_url, data={"access_token": META_TOKEN, "status": "PAUSED"}
                )

                if stop_res.json().get("success"):
                    stopped_adsets.append(adset_name)

    total_stopped = len(stopped_adsets)

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
    global LAST_UPDATE_ID, last_command_time, last_command_text, processed_updates

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {
        "timeout": 1,
        "allowed_updates": ["message"],
        "limit": 1,  # CHỈ LẤY 1 TIN NHẮN MỖI LẦN
    }

    if LAST_UPDATE_ID:
        params["offset"] = LAST_UPDATE_ID + 1
    else:
        params["offset"] = -1

    try:
        res = requests.get(url, params=params, timeout=5)
        data = res.json()
    except Exception as e:
        print(f"Lỗi getUpdates: {e}")
        return

    if not data.get("ok"):
        return

    updates = data.get("result", [])
    if not updates:
        return

    # Chỉ xử lý update đầu tiên
    update = updates[0]
    update_id = update["update_id"]

    # Kiểm tra đã xử lý chưa
    if update_id in processed_updates:
        # Nếu đã xử lý, cập nhật offset để bỏ qua
        LAST_UPDATE_ID = update_id
        return

    if "message" not in update:
        LAST_UPDATE_ID = update_id
        processed_updates.add(update_id)
        return

    current_time = time.time()
    text = update["message"].get("text", "")

    # Kiểm tra thời gian trùng
    if text == last_command_text and current_time - last_command_time < 5:
        LAST_UPDATE_ID = update_id
        processed_updates.add(update_id)
        return

    # Xử lý lệnh
    if text == "/ads":
        print(f"📨 Xử lý /ads lúc {get_time_vn().strftime('%H:%M:%S')}")
        report = get_ads_report()
        send_telegram(report)
        last_command_text = text
        last_command_time = current_time
    elif text == "/stopads":
        print(f"📨 Xử lý /stopads lúc {get_time_vn().strftime('%H:%M:%S')}")
        stop_my_ads()
        last_command_text = text
        last_command_time = current_time
    else:
        # Không phải lệnh, vẫn đánh dấu đã xử lý
        last_command_text = ""
        last_command_time = 0

    # Đánh dấu đã xử lý
    processed_updates.add(update_id)
    LAST_UPDATE_ID = update_id

    # Giới hạn kích thước
    if len(processed_updates) > 100:
        processed_updates = set(list(processed_updates)[-100:])


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
        check_expiry_dates()
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
            cr = 0 if leads_count == 0 else round((orders_count / leads_count) * 100, 2)

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
