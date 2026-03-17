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
META_TOKEN = "EAAafzAo8hZAgBQ3cRZCCs3KXeKZBaSLMnp3uSBs7gzqgf3UF7QrQNA7nqXduOpfB0PlCTHjvhoxP39VKZCO6hhqoT0Goe2Ym8T7XRKIsc4sRhzHL7CNUVCh2XPEj1ZAxCfZBbvtYKMQ8dVZAywpXhdnYhqZA3a36ZA9fXufUUZCYPdlyh2xnK1uRpzRU3mooMNfw0d"
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

ads_cache = {"data": None, "time": 0}
CACHE_TIME = 60  # Cache 60 giây


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
    global ads_cache

    # Kiểm tra cache
    now = time.time()
    if ads_cache["data"] and now - ads_cache["time"] < CACHE_TIME:
        print(f"📦 Dùng cache ADS ({(now - ads_cache['time']):.0f} giây trước)")
        return ads_cache["data"]

    print("🔄 Đang lấy dữ liệu mới từ Facebook...")

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

    # Lưu vào cache
    ads_cache["data"] = msg
    ads_cache["time"] = now

    print(
        f"✅ Đã lấy dữ liệu mới và lưu cache lúc {get_time_vn().strftime('%H:%M:%S')}"
    )
    return msg


def stop_my_ads():
    print(f"🔍 Bắt đầu tắt ads lúc {get_time_vn().strftime('%H:%M:%S')}")

    # Kiểm tra token trước
    url_check = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}"
    params_check = {"access_token": META_TOKEN, "fields": "name"}
    check_res = requests.get(url_check, params=params_check)
    print(f"📊 Kiểm tra token: {check_res.json()}")

    if "error" in check_res.json():
        send_telegram(f"❌ Token lỗi: {check_res.json()['error'].get('message')}")
        return

    url_adsets = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}/adsets"

    params_adsets = {
        "access_token": META_TOKEN,
        "fields": "id,name,campaign_name,status",
        "limit": 200,
    }

    res_adsets = requests.get(url_adsets, params=params_adsets)
    data_adsets = res_adsets.json()

    print(f"📊 Response adsets: {json.dumps(data_adsets, indent=2)[:500]}")

    if "error" in data_adsets:
        print(f"❌ Lỗi Facebook: {data_adsets['error']}")
        send_telegram(
            f"❌ Lỗi Facebook: {data_adsets['error'].get('message', 'Unknown')}"
        )
        return

    stopped_adsets = []
    my_name_lower = MY_NAME.lower()

    print(f"🔍 Tìm campaign có tên chứa: '{my_name_lower}'")

    if "data" in data_adsets:
        print(f"📋 Tổng số adset trả về: {len(data_adsets['data'])}")

        for i, adset in enumerate(data_adsets["data"]):
            campaign_name = adset.get("campaign_name", "")
            status = adset.get("status", "")
            adset_name = adset.get("name", "")
            adset_id = adset.get("id", "")

            print(f"\n--- Adset {i+1} ---")
            print(f"  ID: {adset_id}")
            print(f"  Tên adset: {adset_name}")
            print(f"  Campaign: {campaign_name}")
            print(f"  Status: {status}")

            # Kiểm tra campaign có chứa tên không
            if my_name_lower in campaign_name.lower():
                print(f"  ✅ Campaign có chứa '{MY_NAME}'")

                if status == "ACTIVE":
                    print(f"  🔴 ĐANG ACTIVE - sẽ tắt")

                    stop_url = f"https://graph.facebook.com/v24.0/{adset_id}"
                    stop_res = requests.post(
                        stop_url, data={"access_token": META_TOKEN, "status": "PAUSED"}
                    )

                    result = stop_res.json()
                    print(f"  Kết quả tắt: {result}")

                    if result.get("success"):
                        stopped_adsets.append(adset_name)
                        print(f"  ✅ Đã tắt thành công")
                    else:
                        print(f"  ❌ Lỗi khi tắt: {result}")
                        if "error" in result:
                            send_telegram(
                                f"❌ Lỗi tắt adset {adset_name}: {result['error'].get('message')}"
                            )
                else:
                    print(f"  ⏭️ Không active (status: {status})")
            else:
                print(f"  ❌ Không chứa '{MY_NAME}'")
                # In thử campaign name để kiểm tra
                print(f"     Campaign name thực tế: '{campaign_name}'")

    total_stopped = len(stopped_adsets)
    print(f"\n✅ Đã tắt {total_stopped} nhóm quảng cáo")

    msg = f"""
🛑 ĐÃ TẮT NHÓM QUẢNG CÁO

Đã tắt: {total_stopped} nhóm quảng cáo
"""
    send_telegram(msg)


# ===== TELEGRAM COMMAND =====
def check_telegram_commands():
    global LAST_UPDATE_ID, last_command_time, last_command_text

    # Luôn lấy offset mới nhất
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"

    # Nếu chưa có LAST_UPDATE_ID, lấy tin cuối cùng
    if LAST_UPDATE_ID is None:
        params = {"offset": -1, "limit": 1}
    else:
        params = {"offset": LAST_UPDATE_ID + 1, "limit": 1}

    try:
        res = requests.get(url, params=params, timeout=5)
        data = res.json()
    except:
        return

    if not data.get("ok"):
        return

    updates = data.get("result", [])
    if not updates:
        return

    # Xử lý từng update
    for update in updates:
        update_id = update["update_id"]

        # Bỏ qua nếu đã xử lý (dự phòng)
        if LAST_UPDATE_ID and update_id <= LAST_UPDATE_ID:
            continue

        if "message" in update:
            current_time = time.time()
            text = update["message"].get("text", "")

            # Kiểm tra trùng lệnh trong 3 giây
            if text == last_command_text and current_time - last_command_time < 3:
                LAST_UPDATE_ID = update_id
                continue

            if text == "/ads":
                print(f"📨 Xử lý /ads lúc {get_time_vn().strftime('%H:%M:%S')}")
                send_telegram(get_ads_report())
                last_command_text = text
                last_command_time = current_time
            elif text == "/stopads":
                print(f"📨 Xử lý /stopads lúc {get_time_vn().strftime('%H:%M:%S')}")
                stop_my_ads()
                last_command_text = text
                last_command_time = current_time

        # Cập nhật LAST_UPDATE_ID
        LAST_UPDATE_ID = update_id


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
            # Xác định marketing đầu tiên của số
            for lead in data["data"]:
                phone = lead.get("khachHangSoDienThoai")
                marketing = lead.get("marketingUserName")
                if phone not in phone_first_owner:
                    phone_first_owner[phone] = marketing

            # Lọc lead hợp lệ
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

            # Xử lý đơn hàng từ leads_today (ĐÃ SỬA - không lồng nhau)
            for lead in leads_today:
                if lead.get("lgtDonHangTrangThaiChotDon") == 1:
                    orders_today.append(lead)
                    money = round(lead.get("lgtDonHangTienThuKhach") or 0)
                    total_money += money

                    if lead["id"] not in sent_orders:
                        name = lead.get("khachHangTen")
                        phone = lead.get("khachHangSoDienThoai")
                        sale = lead.get("saleDisplayName")

                        # Lấy thông tin sản phẩm từ sanPhamInfo
                        products = lead.get("sanPhamInfo") or []
                        product_name = ""

                        if isinstance(products, list) and products:
                            first = products[0] or {}
                            product_name = (
                                first.get("tenSanPham")
                                or first.get("sanPhamTen")
                                or first.get("productName")
                                or first.get("ten")
                                or ""
                            )
                        # Nếu vẫn không có thì dùng tên landing
                        if not product_name:
                            product_name = lead.get("landingTen", "")

                        msg = f"""
💰 {money:,.0f}đ | {product_name}
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
