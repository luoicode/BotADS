import requests
import time
import json
import os
from datetime import datetime
from flask import Flask
from threading import Thread
import pytz
import logging

logging.basicConfig(level=logging.DEBUG)
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
    print("🔥 Flask server đang khởi động...")
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)


def keep_alive():
    print("🚀 Bắt đầu thread giữ bot sống...")
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print("✅ Thread đã chạy")


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
    "protoken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjRhOTE1Y2VmLTZjNWMtNGE1YS05YWRkLTE5ZmFjOGYwZjU0YiIsInRob2lnaWFuIjoiMTc3NDU0MzI0NiIsImRvbWFpbiI6ImR1b2NuaGF0dGFtLnNhbmRib3guY29tLnZuIiwiZGV2aWNlIjoiMTBlYjQ1NDgtNjUzOC00NWFkLWJlMTUtMDFlZWU3Yzg1ZTc1IiwibmJmIjoxNzc0NTQzMjQ2LCJleHAiOjE3NzUxNDgwNDYsImlhdCI6MTc3NDU0MzI0Nn0.ljKTxOreMkXoz5aeBRNZeiwnXdE44YABOnDqIJ0qptc",
    "prorefreshToken": "2CC93680958C6F6398943ddf7c6d4004866146a060e187dc",
    "_ga": "GA1.1.690778090.1772418379",
    "_ga_HC7STT03M5": "GS2.1.s1774542725$o209$g1$t1774543351$j60$l0$h0",
}

sent_orders = set()
processed_updates = set()

last_report_date = {"date": None}  # ✅ THÊM DÒNG NÀY
last_expiry_alert_date = None
last_cookie_alert_date = None

# ===== CHECK EXPIRY DATES =====
EXPIRY_CHECKED = False
META_EXPIRY = 1778780378  # 15/05/2026
SANDWICH_EXPIRY = 1775148046  # 03/04/2026

ads_cache = {"data": None, "time": 0}
CACHE_TIME = 60  # Cache 60 giây

# ===== SẢN PHẨM =====
PRODUCTS = {
    "Tâm Não An": {
        "keywords": [
            "Tâm Não An",
            "Tâm Não",
            "Tâm Não An -",
            "Bảo Thần Khang",
            "Bảo Thần",
            "BTK",
        ],
        "cmd_stop": "/stopadstna",
        "cmd_report": "/baocaotna",
        "include_gift": True,  # Có bao gồm Bảo Thần Khang
    },
    "Bảo Khớp Khang": {
        "keywords": ["Bảo Khớp Khang", "Bảo Khớp", "Bảo Khớp Khang -", "BKK"],
        "cmd_stop": "/stopadsbkk",
        "cmd_report": "/baocaobkk",
        "include_gift": False,
    },
    "Heart Gold": {
        "keywords": ["Heart Gold", "Heart Gold -", "Heart", "HG"],
        "cmd_stop": "/stopadshg",
        "cmd_report": "/baocaohg",
        "include_gift": False,
    },
}

# Cache cho báo cáo doanh thu
revenue_cache = {"data": None, "time": 0}
REVENUE_CACHE_TIME = 300  # 5 phút


def check_expiry_dates():
    global last_expiry_alert_date

    now_vn = get_time_vn()
    today = now_vn.strftime("%Y-%m-%d")

    # ❌ nếu đã gửi hôm nay rồi → bỏ qua
    if last_expiry_alert_date == today:
        return

    # ✅ CHỈ chạy lúc 00:00 - 00:05
    if not (now_vn.hour == 0 and now_vn.minute < 5):
        return

    now = time.time()
    warnings = []

    # ===== META TOKEN =====
    days_left = (META_EXPIRY - now) / 86400
    if days_left < 7:
        warnings.append(
            f"⚠️ Meta Token sắp hết hạn: {int(days_left)} ngày ({datetime.fromtimestamp(META_EXPIRY, vn_tz).strftime('%d/%m/%Y')})"
        )
    elif days_left < 30:
        warnings.append(
            f"📅 Meta Token còn: {int(days_left)} ngày ({datetime.fromtimestamp(META_EXPIRY, vn_tz).strftime('%d/%m/%Y')})"
        )

    # ===== SANDBOX TOKEN =====
    days_left = (SANDWICH_EXPIRY - now) / 86400
    if days_left < 3:
        warnings.append(
            f"⚠️⚠️ SANDWICH TOKEN HẾT HẠN TRONG {int(days_left)} NGÀY! ({datetime.fromtimestamp(SANDWICH_EXPIRY, vn_tz).strftime('%d/%m/%Y')})"
        )
    elif days_left < 7:
        warnings.append(
            f"⚠️ Sandwich Token sắp hết hạn: {int(days_left)} ngày ({datetime.fromtimestamp(SANDWICH_EXPIRY, vn_tz).strftime('%d/%m/%Y')})"
        )

    # ===== RAILWAY =====
    hours_used = (now_vn.day - 1) * 24 + now_vn.hour
    hours_left = 500 - hours_used

    if hours_left < 0:
        warnings.append(f"⚠️⚠️ RAILWAY ĐÃ HẾT GIỜ ({hours_used}/500 giờ)!")
    elif hours_left < 50:
        warnings.append(f"⚠️ Railway còn: {hours_left} giờ ({hours_used}/500)")

    # ===== GỬI TELE =====
    if warnings:
        msg = "🔔 KIỂM TRA HẠN SỬ DỤNG\n\n" + "\n".join(warnings)
        send_telegram(msg)

    # ✅ Đánh dấu đã gửi hôm nay
    last_expiry_alert_date = today


def send_telegram(msg):
    url_tele = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url_tele, data={"chat_id": CHAT_ID, "text": msg})
    except:
        print(f"Không gửi được Telegram lúc {get_time_vn().strftime('%H:%M:%S')}")


def get_product_from_lead(lead):
    text = ""

    # Ưu tiên lấy từ sản phẩm
    products = lead.get("sanPhamInfo") or []
    if isinstance(products, list) and products:
        first = products[0] or {}
        text = (
            first.get("tenSanPham")
            or first.get("sanPhamTen")
            or first.get("productName")
            or first.get("ten")
            or ""
        )

    # Nếu không có thì lấy từ landing
    if not text:
        text = lead.get("landingTen", "")

    text = text.lower().strip()

    # ✅ LOGIC CHUẨN CỦA BẠN
    if any(k in text for k in ["tâm não", "bảo thần"]):
        return "Tâm Não An"

    if "bảo mạch" in text:
        return "Bảo Mạch Khang"

    if any(k in text for k in ["bảo khớp", "bkk"]):
        return "Bảo Khớp Khang"

    if any(k in text for k in ["heart gold", "hg"]):
        return "Heart Gold"

    return "Khác"


def filter_leads_data(leads_data):
    today = get_time_vn().strftime("%Y-%m-%d")

    # Chỉ lấy lead trong ngày
    today_leads = [
        lead for lead in leads_data if lead.get("ngayTao", "").startswith(today)
    ]

    # Sắp xếp theo thời gian tăng dần
    today_leads = sorted(today_leads, key=lambda x: x.get("ngayTao", ""))

    phone_first_owner = {}
    valid_leads = []

    for lead in today_leads:
        phone = lead.get("khachHangSoDienThoai")
        marketing = lead.get("marketingUserName")

        if not phone or not marketing:
            continue

        # Nếu số chưa xuất hiện → ghi nhận người đầu tiên
        if phone not in phone_first_owner:
            phone_first_owner[phone] = marketing

        # ✅ CHỈ lấy nếu bạn là người đầu tiên
        if phone_first_owner[phone] == MY_USERNAME:
            # đảm bảo mỗi số chỉ 1 lần
            if not any(l.get("khachHangSoDienThoai") == phone for l in valid_leads):
                valid_leads.append(lead)

    return valid_leads


def get_revenue_report(product_filter=None):
    """Lấy báo cáo doanh thu, có thể lọc theo sản phẩm"""
    global revenue_cache

    # Kiểm tra cache nếu là báo cáo tổng hợp
    now = time.time()
    if (
        not product_filter
        and revenue_cache["data"]
        and now - revenue_cache["time"] < REVENUE_CACHE_TIME
    ):
        return revenue_cache["data"]

    # Lấy dữ liệu từ API
    payload = get_payload()
    res = requests.post(url, headers=headers, cookies=cookies, json=payload)

    # ✅ CHECK COOKIE DIE
    if res.status_code == 401:
        today = get_time_vn().strftime("%Y-%m-%d")

        global last_cookie_alert_date
        if last_cookie_alert_date != today:
            send_telegram("❌ COOKIE SANDBOX HẾT HẠN! Login lại ngay!")
            last_cookie_alert_date = today

        return "❌ Không lấy được dữ liệu (cookie hết hạn)"

    # ✅ THIẾU DÒNG NÀY (bạn phải thêm)
    data = res.json()

    if "data" not in data:
        return "Không có dữ liệu"

    # Lọc leads hợp lệ
    valid_leads = filter_leads_data(data["data"])

    # Khởi tạo báo cáo theo sản phẩm

    product_stats = {}

    for lead in valid_leads:
        product = get_product_from_lead(lead)

        print(f"DEBUG PRODUCT: {product}")

        # Nếu chưa có sản phẩm này thì tạo mới
        if product not in product_stats:
            product_stats[product] = {"leads": 0, "orders": 0, "revenue": 0}

        product_stats[product]["leads"] += 1

        # Nếu là đơn
        if lead.get("lgtDonHangTrangThaiChotDon") == 1:
            product_stats[product]["orders"] += 1
            money = round(lead.get("lgtDonHangTienThuKhach") or 0)
            product_stats[product]["revenue"] += money

    # Nếu có filter, gọi hàm báo cáo chi tiết theo sản phẩm
    if product_filter:
        stats = product_stats.get(
            product_filter, {"leads": 0, "orders": 0, "revenue": 0}
        )
        return get_product_detail_report(product_filter, stats)

    # ===== LẤY CHI PHÍ ADS TỪ INSIGHTS (CHỈ CAMPAIGN CÓ DỮ LIỆU) =====
    total_ads_spend = 0
    try:
        url_insights = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}/insights"
        params_insights = {
            "access_token": META_TOKEN,
            "fields": "campaign_name,spend",
            "date_preset": "today",
            "level": "campaign",
            "limit": 500,
        }
        res_insights = requests.get(url_insights, params=params_insights)
        data_insights = res_insights.json()
        if "error" in data_insights:
            send_telegram(f"❌ META TOKEN LỖI: {data_insights['error'].get('message')}")

        if "data" in data_insights:
            for item in data_insights["data"]:
                campaign_name = item.get("campaign_name", "")
                spend = float(item.get("spend", 0))

                # Chỉ tính campaign có tên chứa MY_NAME
                if MY_NAME.lower() in campaign_name.lower():
                    total_ads_spend += spend
                    print(f"📊 Campaign có chi tiêu: {campaign_name} - {spend:,.0f}đ")
    except Exception as e:
        print(f"❌ Lỗi lấy chi phí ads: {e}")

    # ===== TÍNH TỔNG =====
    total_leads = sum(s["leads"] for s in product_stats.values())
    total_orders = sum(s["orders"] for s in product_stats.values())
    total_revenue = sum(s["revenue"] for s in product_stats.values())
    cr = (total_orders / total_leads * 100) if total_leads > 0 else 0

    # ===== TẠO MESSAGE =====
    msg = "📊 BÁO CÁO DOANH THU HÔM NAY\n\n"

    # Sắp xếp theo doanh thu giảm dần
    sorted_products = sorted(
        product_stats.items(), key=lambda x: x[1]["revenue"], reverse=True
    )

    for product, stats in sorted_products:
        revenue = stats["revenue"]
        orders = stats["orders"]

        msg += f"📦 {product}: {revenue:,}đ ({orders} đơn)\n"

    # ===== TỔNG KẾT =====
    msg += "\n📈 TỔNG KẾT\n"
    msg += f"  • Tổng Lead: {total_leads}\n"
    msg += f"  • Tổng Đơn: {total_orders}\n"
    msg += f"  • Tổng Doanh thu: {total_revenue:,}đ\n"
    msg += f"  • Chi phí ads tổng: {int(total_ads_spend):,}đ\n"
    msg += f"  • CR: {cr:.2f}%"

    # ===== CACHE =====
    revenue_cache["data"] = msg
    revenue_cache["time"] = now

    return msg


def get_product_detail_report(product_name, stats):
    """Báo cáo chi tiết cho từng sản phẩm kèm chi phí ads"""

    spend = 0
    adsets_active = set()  # ✅ dùng set để không bị trùng

    try:
        url_insights = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}/insights"
        params_insights = {
            "access_token": META_TOKEN,
            "level": "adset",  # ✅ đổi sang adset
            "fields": "campaign_name,adset_name,adset_id,spend",
            "date_preset": "today",
            "limit": 500,
        }

        res_insights = requests.get(url_insights, params=params_insights)
        data_insights = res_insights.json()

        if "data" in data_insights:
            for ad in data_insights["data"]:
                campaign_name = ad.get("campaign_name", "")
                adset_id = ad.get("adset_id")
                adset_name = ad.get("adset_name", "")

                for keyword in PRODUCTS[product_name]["keywords"]:
                    if keyword.lower() in campaign_name.lower():
                        spend += float(ad.get("spend", 0))

                        # ✅ chỉ tính nhóm có spend (đang chạy)
                        if float(ad.get("spend", 0)) > 0:
                            adsets_active.add(adset_id)

                        break

    except Exception as e:
        print("Lỗi ads:", e)

    # Icon
    icons = {"Tâm Não An": "🧠", "Bảo Khớp Khang": "🦴", "Heart Gold": "💛"}
    icon = icons.get(product_name, "📦")

    # Message
    msg = f"{icon} {product_name}\n"
    msg += f"  • Data: {stats['leads']}\n"
    msg += f"  • Đơn: {stats['orders']}\n"
    msg += f"  • Doanh thu: {stats['revenue']:,}đ\n"
    msg += f"  • Chi phí ads: {int(spend):,}đ\n"
    msg += f"  • Nhóm QC đang chạy: {len(adsets_active)}"  # ✅ đổi text

    # ROAS
    if spend > 0 and stats["revenue"] > 0:
        roas = stats["revenue"] / spend
        msg += f"\n  • 📈 ROAS: {roas:.2f}x"

    return msg


def tra_cuoc_hoi_thoai(sdt):
    """Tra cứu lịch sử hội thoại và ghi chú của sale theo số điện thoại"""
    try:
        # Chuẩn hóa số điện thoại
        sdt = sdt.replace(" ", "").replace("+84", "0").replace("+", "")
        if not sdt.startswith("0"):
            sdt = "0" + sdt

        # Lấy dữ liệu từ API
        payload = get_payload()
        res = requests.post(url, headers=headers, cookies=cookies, json=payload)

        # ✅ CHECK COOKIE DIE
        if res.status_code == 401:
            today = get_time_vn().strftime("%Y-%m-%d")

            global last_cookie_alert_date
            if last_cookie_alert_date != today:
                send_telegram("❌ COOKIE SANDBOX HẾT HẠN! Login lại ngay!")
                last_cookie_alert_date = today

            return f"❌ Không tra được số {sdt} (cookie hết hạn)"

        # ✅ parse data sau khi check
        data = res.json()

        if "data" not in data:
            return f"❌ Không tìm thấy số {sdt}"

        # Lọc các lead có số điện thoại này
        leads = []
        for lead in data["data"]:
            lead_sdt = lead.get("khachHangSoDienThoai", "").replace(" ", "")
            if lead_sdt == sdt:
                leads.append(lead)

        if not leads:
            return f"❌ Không tìm thấy số {sdt}"

        # Sắp xếp theo thời gian
        leads = sorted(leads, key=lambda x: x.get("ngayTao", ""))

        msg = f"📞 {sdt}\n"
        msg += "─" * 25 + "\n"

        for i, lead in enumerate(leads, 1):
            # Thời gian
            thoi_gian = (
                lead.get("ngayTao", "")[11:16] if lead.get("ngayTao") else "??:??"
            )

            # Trạng thái
            if lead.get("lgtDonHangTrangThaiChotDon") == 1:
                trang_thai = "✅ CHỐT ĐƠN"
            else:
                trang_thai = "⏳ Chưa chốt"

            # Tin nhắn ghi chú
            tin_nhan = lead.get("lastMessage", "")
            if not tin_nhan:
                tin_nhan = "Không có ghi chú"

            # Sản phẩm
            products = lead.get("sanPhamInfo")

            # Tên sale - LẤY TRỰC TIẾP TỪ lead
            sale_name = lead.get("saleDisplayName", "Chưa có sale")

            msg += f"Lần {i} - {thoi_gian}\n"
            msg += f"Trạng thái: {trang_thai}\n"
            msg += f"📝 {tin_nhan}\n"
            msg += f"👤 Sale: {sale_name}\n"
            msg += f"📦 {product_name}\n"
            msg += "─" * 20 + "\n"

        return msg

    except Exception as e:
        return f"❌ Lỗi tra cứu: {str(e)}"


# ===== ADS REPORT =====
def get_ads_report():
    global ads_cache

    # Kiểm tra cache
    now = time.time()
    if ads_cache["data"] and now - ads_cache["time"] < CACHE_TIME:
        print(f"📦 Dùng cache ADS ({(now - ads_cache['time']):.0f} giây trước)")
        return ads_cache["data"]

    print("🔄 Đang lấy dữ liệu mới từ Facebook...")

    # Danh sách sản phẩm cần theo dõi
    products = [
        {"name": "Tâm Não An", "keywords": ["Tâm Não An", "Tâm Não", "Tâm Não An -"]},
        {
            "name": "Bảo Khớp Khang",
            "keywords": ["Bảo Khớp Khang", "Bảo Khớp", "Bảo Khớp Khang -"],
        },
        {"name": "Heart Gold", "keywords": ["Heart Gold", "Heart Gold -", "Heart"]},
    ]

    # ===== LẤY DANH SÁCH CAMPAIGN =====
    url_campaigns = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}/campaigns"

    params_camp = {
        "access_token": META_TOKEN,
        "fields": "id,name,status",
        "limit": 100,
    }

    res_camp = requests.get(url_campaigns, params=params_camp)
    data_camp = res_camp.json()

    all_campaigns = {}  # Lưu tất cả campaign của bạn

    if "data" in data_camp:
        for camp in data_camp["data"]:
            if MY_NAME in camp.get("name", ""):
                all_campaigns[camp["id"]] = {
                    "name": camp.get("name"),
                    "status": camp.get("status"),
                }

    # ===== LẤY DANH SÁCH ADSET =====
    url_adsets = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}/adsets"

    params_adsets = {
        "access_token": META_TOKEN,
        "fields": "id,name,campaign_id,status",
        "limit": 200,
    }

    res_adsets = requests.get(url_adsets, params=params_adsets)
    data_adsets = res_adsets.json()

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
    if "error" in data_insights:
        send_telegram(f"❌ META TOKEN LỖI: {data_insights['error'].get('message')}")
    # Xử lý dữ liệu theo từng sản phẩm
    product_reports = {}

    # Khởi tạo báo cáo cho từng sản phẩm
    for product in products:
        product_reports[product["name"]] = {
            "has_data": False,
            "campaigns_active": set(),
            "adsets_active": set(),
            "total_spend": 0,
            "total_contact": 0,
            "bad_120": set(),
            "bad_240": set(),
            "bad_360": set(),
            "adsets_list": [],
        }

    # Phân loại campaign theo sản phẩm
    campaign_to_product = {}
    for camp_id, camp_info in all_campaigns.items():
        camp_name = camp_info["name"]
        assigned = False
        for product in products:
            for keyword in product["keywords"]:
                if keyword in camp_name:
                    campaign_to_product[camp_id] = product["name"]
                    assigned = True
                    break
            if assigned:
                break

    # Lấy thông tin adset
    if "data" in data_adsets:
        for adset in data_adsets["data"]:
            campaign_id = adset["campaign_id"]
            if campaign_id in campaign_to_product:
                product_name = campaign_to_product[campaign_id]
                product_reports[product_name]["has_data"] = True

                if adset.get("status") == "ACTIVE":
                    product_reports[product_name]["adsets_active"].add(adset["id"])
                    product_reports[product_name]["campaigns_active"].add(campaign_id)

    # Xử lý dữ liệu chi tiêu
    if "data" in data_insights:
        for ad in data_insights["data"]:
            campaign_id = ad.get("campaign_id")
            adset_id = ad.get("adset_id")

            if campaign_id in campaign_to_product:
                product_name = campaign_to_product[campaign_id]
                spend = float(ad.get("spend", 0))
                contact = 0

                for act in ad.get("actions", []):
                    if (
                        act["action_type"]
                        == "onsite_conversion.messaging_conversation_started_7d"
                    ):
                        contact = int(act["value"])

                product_reports[product_name]["total_spend"] += spend
                product_reports[product_name]["total_contact"] += contact

    # Tạo báo cáo
    msg = "📊 BÁO CÁO ADS THEO SẢN PHẨM\n\n"

    for product in products:
        product_name = product["name"]
        report = product_reports[product_name]

        msg += f"⭐️ {product_name}\n"

        if not report["has_data"]:
            msg += "➡️ Đang không chạy\n\n"
            continue

        campaigns_active = len(report["campaigns_active"])
        adsets_active = len(report["adsets_active"])
        total_spend = int(report["total_spend"])
        total_contact = report["total_contact"]

        msg += f"  • Campaign: {campaigns_active}\n"
        msg += f"  • Nhóm QC: {adsets_active}\n"
        msg += f"  • Chi tiêu: {total_spend:,}đ\n"
        msg += f"  • Liên hệ: {total_contact}\n\n"

    # Thêm tổng kết - CHỈ TÍNH CAMP VÀ NHÓM ĐANG HOẠT ĐỘNG
    total_campaigns_active = 0
    total_adsets_active = 0
    total_spend_all = 0
    total_contact_all = 0

    for product in products:
        report = product_reports[product["name"]]
        total_campaigns_active += len(report["campaigns_active"])
        total_adsets_active += len(report["adsets_active"])
        total_spend_all += int(report["total_spend"])
        total_contact_all += report["total_contact"]

    msg += "📈 TỔNG KẾT\n"
    msg += f"• Tổng campaign đang hoạt động: {total_campaigns_active}\n"
    msg += f"• Tổng nhóm QC đang hoạt động: {total_adsets_active}\n"
    msg += f"• Tổng chi: {total_spend_all:,}đ\n"
    msg += f"• Tổng LH: {total_contact_all}"

    # Lưu vào cache
    ads_cache["data"] = msg
    ads_cache["time"] = now

    print(
        f"✅ Đã lấy dữ liệu mới và lưu cache lúc {get_time_vn().strftime('%H:%M:%S')}"
    )
    return msg


def stop_product_ads(product_name):
    """Tắt ads cho một sản phẩm cụ thể"""
    print(f"🔍 Bắt đầu tắt ads {product_name} lúc {get_time_vn().strftime('%H:%M:%S')}")

    # Kiểm tra token trước
    url_check = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}"
    params_check = {"access_token": META_TOKEN, "fields": "name"}
    check_res = requests.get(url_check, params=params_check)
    check_data = check_res.json()

    if "error" in check_data:
        error_msg = check_data["error"].get("message", "Lỗi không xác định")
        send_telegram(f"❌ Token lỗi: {error_msg}")
        return

    # BƯỚC 1: Lấy danh sách campaign của Nguyễn Hữu Huy
    url_campaigns = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}/campaigns"
    params_campaigns = {
        "access_token": META_TOKEN,
        "fields": "id,name",
        "limit": 100,
    }
    res_campaigns = requests.get(url_campaigns, params=params_campaigns)
    data_campaigns = res_campaigns.json()

    # Lọc campaign của Nguyễn Hữu Huy
    my_campaigns = {}
    my_name_lower = MY_NAME.lower()

    if "data" in data_campaigns:
        for camp in data_campaigns["data"]:
            camp_name = camp.get("name", "")
            camp_id = camp["id"]
            if my_name_lower in camp_name.lower():
                my_campaigns[camp_id] = camp_name
                print(f"✅ Campaign của bạn: {camp_name}")

    if not my_campaigns:
        send_telegram("❌ Không tìm thấy campaign nào của bạn")
        return

    # BƯỚC 2: Trong các campaign của bạn, lọc theo sản phẩm
    product_campaigns = set()
    product_info = PRODUCTS.get(product_name, {})
    keywords = product_info.get("keywords", [])

    for camp_id, camp_name in my_campaigns.items():
        for keyword in keywords:
            if keyword.lower() in camp_name.lower():
                product_campaigns.add(camp_id)
                print(f"  🎯 Campaign {product_name}: {camp_name}")
                break

    if not product_campaigns:
        send_telegram(f"❌ Không tìm thấy campaign {product_name} của bạn")
        return

    # BƯỚC 3: Lấy danh sách adset
    url_adsets = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}/adsets"
    params_adsets = {
        "access_token": META_TOKEN,
        "fields": "id,name,campaign_id,status",
        "limit": 200,
    }

    res_adsets = requests.get(url_adsets, params=params_adsets)
    data_adsets = res_adsets.json()

    if "error" in data_adsets:
        send_telegram(
            f"❌ Lỗi Facebook: {data_adsets['error'].get('message', 'Unknown')}"
        )
        return

    # BƯỚC 4: Tắt các adset thuộc campaign sản phẩm
    stopped_adsets = []

    if "data" in data_adsets:
        for adset in data_adsets["data"]:
            campaign_id = adset.get("campaign_id", "")
            status = adset.get("status", "")
            adset_name = adset.get("name", "")
            adset_id = adset.get("id", "")

            if campaign_id in product_campaigns and status == "ACTIVE":
                print(f"🔴 Tắt adset: {adset_name}")

                stop_url = f"https://graph.facebook.com/v24.0/{adset_id}"
                stop_res = requests.post(
                    stop_url, data={"access_token": META_TOKEN, "status": "PAUSED"}
                )

                result = stop_res.json()
                if result.get("success"):
                    stopped_adsets.append(adset_name)
                    print(f"  ✅ Đã tắt")
                else:
                    print(f"  ❌ Lỗi: {result}")

    total_stopped = len(stopped_adsets)
    msg = f"""
🛑 ĐÃ TẮT ADS {product_name.upper()}

Đã tắt: {total_stopped} nhóm quảng cáo
"""
    send_telegram(msg)


def stop_my_ads():
    """Tắt TẤT CẢ nhóm quảng cáo của Nguyễn Hữu Huy"""
    print(f"🔍 Bắt đầu tắt tất cả ads lúc {get_time_vn().strftime('%H:%M:%S')}")

    # Kiểm tra token trước
    url_check = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}"
    params_check = {"access_token": META_TOKEN, "fields": "name"}
    check_res = requests.get(url_check, params=params_check)
    check_data = check_res.json()

    if "error" in check_data:
        send_telegram(f"❌ Token lỗi: {check_data['error'].get('message')}")
        return

    # Lấy danh sách campaign của Nguyễn Hữu Huy
    url_campaigns = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}/campaigns"
    params_campaigns = {
        "access_token": META_TOKEN,
        "fields": "id,name",
        "limit": 100,
    }
    res_campaigns = requests.get(url_campaigns, params=params_campaigns)
    data_campaigns = res_campaigns.json()

    my_campaigns = set()
    my_name_lower = MY_NAME.lower()

    if "data" in data_campaigns:
        for camp in data_campaigns["data"]:
            camp_name = camp.get("name", "").lower()
            if my_name_lower in camp_name:
                my_campaigns.add(camp["id"])
                print(f"✅ Campaign của bạn: {camp.get('name')}")

    if not my_campaigns:
        send_telegram("❌ Không tìm thấy campaign nào của bạn")
        return

    # Lấy danh sách adset
    url_adsets = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}/adsets"
    params_adsets = {
        "access_token": META_TOKEN,
        "fields": "id,name,campaign_id,status",
        "limit": 200,
    }

    res_adsets = requests.get(url_adsets, params=params_adsets)
    data_adsets = res_adsets.json()

    if "error" in data_adsets:
        send_telegram(
            f"❌ Lỗi Facebook: {data_adsets['error'].get('message', 'Unknown')}"
        )
        return

    # Tắt các adset thuộc campaign của bạn
    stopped_adsets = []

    if "data" in data_adsets:
        for adset in data_adsets["data"]:
            campaign_id = adset.get("campaign_id", "")
            status = adset.get("status", "")
            adset_name = adset.get("name", "")
            adset_id = adset.get("id", "")

            if campaign_id in my_campaigns and status == "ACTIVE":
                print(f"🔴 Tắt adset: {adset_name}")

                stop_url = f"https://graph.facebook.com/v24.0/{adset_id}"
                stop_res = requests.post(
                    stop_url, data={"access_token": META_TOKEN, "status": "PAUSED"}
                )

                result = stop_res.json()
                if result.get("success"):
                    stopped_adsets.append(adset_name)
                    print(f"  ✅ Đã tắt")

    total_stopped = len(stopped_adsets)
    msg = f"""
🛑 ĐÃ TẮT TẤT CẢ NHÓM QUẢNG CÁO

Đã tắt: {total_stopped} nhóm quảng cáo
"""
    send_telegram(msg)


# ===== TELEGRAM COMMAND =====
def check_telegram_commands():
    global LAST_UPDATE_ID, last_command_time, last_command_text

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"

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

    for update in updates:
        update_id = update["update_id"]

        if LAST_UPDATE_ID and update_id <= LAST_UPDATE_ID:
            continue

        if "message" in update:
            current_time = time.time()
            text = update["message"].get("text", "")

            if text == last_command_text and current_time - last_command_time < 3:
                LAST_UPDATE_ID = update_id
                continue

            # Xử lý các lệnh
            if text == "/ads":
                print(f"📨 Xử lý /ads lúc {get_time_vn().strftime('%H:%M:%S')}")
                send_telegram(get_ads_report())
                last_command_text = text
                last_command_time = current_time

            elif text == "/baocao":
                print(f"📨 Xử lý /baocao lúc {get_time_vn().strftime('%H:%M:%S')}")
                send_telegram(get_revenue_report())
                last_command_text = text
                last_command_time = current_time

            elif text == "/baocaotna":
                print(f"📨 Xử lý /baocaotna lúc {get_time_vn().strftime('%H:%M:%S')}")
                send_telegram(get_revenue_report("Tâm Não An"))
                last_command_text = text
                last_command_time = current_time

            elif text == "/baocaobkk":
                print(f"📨 Xử lý /baocaobkk lúc {get_time_vn().strftime('%H:%M:%S')}")
                send_telegram(get_revenue_report("Bảo Khớp Khang"))
                last_command_text = text
                last_command_time = current_time

            elif text == "/baocaohg":
                print(f"📨 Xử lý /baocaohg lúc {get_time_vn().strftime('%H:%M:%S')}")
                send_telegram(get_revenue_report("Heart Gold"))
                last_command_text = text
                last_command_time = current_time

            elif text == "/stopadstna":
                print(f"📨 Xử lý /stopadstna lúc {get_time_vn().strftime('%H:%M:%S')}")
                stop_product_ads("Tâm Não An")
                last_command_text = text
                last_command_time = current_time

            elif text == "/stopadsbkk":
                print(f"📨 Xử lý /stopadsbkk lúc {get_time_vn().strftime('%H:%M:%S')}")
                stop_product_ads("Bảo Khớp Khang")
                last_command_text = text
                last_command_time = current_time

            elif text == "/stopadshg":
                print(f"📨 Xử lý /stopadshg lúc {get_time_vn().strftime('%H:%M:%S')}")
                stop_product_ads("Heart Gold")
                last_command_text = text
                last_command_time = current_time

            elif text == "/stopads":
                print(f"📨 Xử lý /stopads lúc {get_time_vn().strftime('%H:%M:%S')}")
                stop_my_ads()
                last_command_text = text
                last_command_time = current_time
            elif text.startswith("/tra "):
                parts = text.split()
                if len(parts) == 2:
                    sdt = parts[1]
                    print(
                        f"📨 Xử lý /tra {sdt} lúc {get_time_vn().strftime('%H:%M:%S')}"
                    )
                    send_telegram(tra_cuoc_hoi_thoai(sdt))
                    last_command_text = text
                    last_command_time = current_time

        LAST_UPDATE_ID = update_id


def get_payload():
    today = get_time_vn().strftime("%Y-%m-%d")
    return {
        "date": [f"{today}T00:00:00+07:00", f"{today}T23:59:59+07:00"],
        "tuNgay": f"{today}T00:00:00+07:00",
        "denNgay": f"{today}T23:59:59+07:00",
        "pageInfo": {"page": 1, "pageSize": 100},  # Tăng từ 50 lên 100
        "sorts": [],
    }


def auto_ping():
    while True:
        try:
            requests.get("http://localhost:8080")
            print("🔄 Ping giữ bot sống")
        except:
            print("❌ Ping lỗi")
        time.sleep(300)  # 5 phút


print("Bot Sandbox đã khởi động")
keep_alive()

# ✅ THÊM DÒNG NÀY
Thread(target=auto_ping, daemon=True).start()


while True:
    try:
        today = get_time_vn().strftime("%Y-%m-%d")

        if last_report_date["date"] != today:
            report_1140_sent = False
            report_1330_sent = False
            report_15_sent = False
            report_17_sent = False
            last_report_date["date"] = today
        print(f"🔄 [{get_time_vn().strftime('%H:%M:%S')}] Bắt đầu vòng lặp...")
        check_expiry_dates()
        check_telegram_commands()

        payload = get_payload()
        res = requests.post(url, headers=headers, cookies=cookies, json=payload)

        # ✅ CHECK COOKIE DIE
        if res.status_code == 401:
            today = get_time_vn().strftime("%Y-%m-%d")
            if last_cookie_alert_date != today:
                send_telegram("❌ COOKIE SANDBOX HẾT HẠN! Login lại ngay!")
                last_cookie_alert_date = today

            time.sleep(60)
            continue

        data = res.json()

        leads_today = []
        orders_today = []
        total_money = 0

        if "data" in data:
            # Lọc leads hợp lệ
            valid_leads = filter_leads_data(data["data"])
            leads_today = valid_leads

            # Xử lý đơn hàng
            for lead in leads_today:
                if lead.get("lgtDonHangTrangThaiChotDon") == 1:
                    orders_today.append(lead)
                    money = round(lead.get("lgtDonHangTienThuKhach") or 0)
                    total_money += money

                    if lead["id"] not in sent_orders:
                        # Lấy thông tin sản phẩm
                        product_name = get_product_from_lead(lead)

                        name = lead.get("khachHangTen", "")
                        phone = lead.get("khachHangSoDienThoai", "")
                        sale = lead.get("saleDisplayName", "")

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

            # Báo cáo tự động theo giờ
            if (
                now.hour == 11
                and now.minute == 40
                and now.second < 30
                and not report_1140_sent
            ):
                send_telegram(get_revenue_report())
                report_1140_sent = True
                print(
                    f"⏰ Đã gửi báo cáo 11:40 - {leads_count} leads, {orders_count} đơn, {total_money:,}đ"
                )

            if (
                now.hour == 13
                and now.minute == 30
                and now.second < 30
                and not report_1330_sent
            ):
                send_telegram(get_revenue_report())
                report_1330_sent = True
                print(
                    f"⏰ Đã gửi báo cáo 13:30 - {leads_count} leads, {orders_count} đơn, {total_money:,}đ"
                )

            if (
                now.hour == 15
                and now.minute == 0
                and now.second < 30
                and not report_15_sent
            ):
                send_telegram(get_revenue_report())
                report_15_sent = True
                print(
                    f"⏰ Đã gửi báo cáo 15:00 - {leads_count} leads, {orders_count} đơn, {total_money:,}đ"
                )

            if (
                now.hour == 17
                and now.minute == 0
                and now.second < 30
                and not report_17_sent
            ):
                send_telegram(get_revenue_report())
                report_17_sent = True
                print(
                    f"⏰ Đã gửi báo cáo 17:00 - {leads_count} leads, {orders_count} đơn, {total_money:,}đ"
                )

        # Hiển thị trạng thái mỗi 30 giây
        now = get_time_vn()
        print(
            f"\r🟢 [{now.strftime('%H:%M:%S')}] Bot đang chạy | Lead hôm nay: {len(leads_today)} | Đơn: {len(orders_today)} | {total_money:,.0f}đ",
            end="",
            flush=True,
        )

    except Exception as e:
        print(f"\n❌ LỖI NGHIÊM TRỌNG: {e}")
        import traceback

        traceback.print_exc()
        time.sleep(5)  # Đợi 5s rồi thử lại

    time.sleep(30)
