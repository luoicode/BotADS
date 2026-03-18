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
    "protoken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjRhOTE1Y2VmLTZjNWMtNGE1YS05YWRkLTE5ZmFjOGYwZjU0YiIsInRob2lnaWFuIjoiMTc3MzczNDA2NiIsImRvbWFpbiI6ImR1b2NuaGF0dGFtLnNhbmRib3guY29tLnZuIiwiZGV2aWNlIjoiMDUzYTAyNzMtMWVkNC00ODBjLTgwNjYtN2IzZmFjYTEzODc5IiwibmJmIjoxNzczNzM0MDY3LCJleHAiOjE3NzQzMzg4NjcsImlhdCI6MTc3MzczNDA2N30.AzANmTWplnJx3lwopUf37VBHap1hMQwWfBfLHajSICA",
    "prorefreshToken": "258B74C5338542FBc1a5e568bee14cd98de747590a35685f",
    "_ga": "GA1.1.690778090.1772418379",
    "_ga_HC7STT03M5": "GS2.1.s1773729347$o135$g1$t1773734939$j60$l0$h0",
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


def get_product_from_lead(lead):
    """Xác định sản phẩm từ lead dựa trên tên sản phẩm hoặc landing"""
    # Kiểm tra từ sanPhamInfo
    products = lead.get("sanPhamInfo") or []
    if isinstance(products, list) and products:
        first = products[0] or {}
        product_name = (
            first.get("tenSanPham")
            or first.get("sanPhamTen")
            or first.get("productName")
            or first.get("ten")
            or ""
        )

        # Kiểm tra từng sản phẩm
        for prod_key, prod_info in PRODUCTS.items():
            for keyword in prod_info["keywords"]:
                if keyword.lower() in product_name.lower():
                    return prod_key

    # Nếu không có, kiểm tra từ landingTen
    landing = lead.get("landingTen", "")
    for prod_key, prod_info in PRODUCTS.items():
        for keyword in prod_info["keywords"]:
            if keyword.lower() in landing.lower():
                return prod_key

    return "Khác"


def filter_leads_data(leads_data):
    """Lọc leads theo các tiêu chí: không khách cũ, không trùng marketing khác,
    nhưng vẫn giữ lead chốt đơn dù trùng số với chính mình"""

    phone_first_owner = {}  # Lưu marketing đầu tiên của mỗi số
    leads_with_orders = set()  # Lưu các số đã có đơn chốt
    valid_leads = []

    # Sắp xếp leads theo thời gian tạo (ngayTao) - cũ nhất lên trước
    sorted_leads = sorted(leads_data, key=lambda x: x.get("ngayTao", ""))

    # Bước 1: Xác định marketing đầu tiên của mỗi số
    for lead in sorted_leads:
        phone = lead.get("khachHangSoDienThoai")
        marketing = lead.get("marketingUserName")

        if phone and marketing:
            if phone not in phone_first_owner:
                phone_first_owner[phone] = marketing

    # Bước 2: Xác định số nào có đơn chốt
    for lead in sorted_leads:
        if lead.get("lgtDonHangTrangThaiChotDon") == 1:
            phone = lead.get("khachHangSoDienThoai")
            leads_with_orders.add(phone)

    # Bước 3: Lọc lead hợp lệ
    for lead in sorted_leads:
        phone = lead.get("khachHangSoDienThoai")
        marketing = lead.get("marketingUserName")
        is_order = lead.get("lgtDonHangTrangThaiChotDon") == 1

        # Bỏ qua nếu không phải lead của mình
        if marketing != MY_USERNAME:
            continue

        # Bỏ qua khách cũ
        if lead.get("isKhachCu"):
            continue

        # Nếu số này có đơn chốt ở bất kỳ lead nào, GIỮ LẠI TẤT CẢ leads của số đó
        if phone in leads_with_orders:
            valid_leads.append(lead)
            continue

        # Nếu không có đơn chốt, kiểm tra marketing đầu tiên
        # Chỉ lấy lead đầu tiên của mỗi số (nếu không có đơn)
        first_owner = phone_first_owner.get(phone)
        if first_owner == MY_USERNAME:
            # Kiểm tra xem đã có lead nào của số này chưa
            existing = next(
                (l for l in valid_leads if l.get("khachHangSoDienThoai") == phone), None
            )
            if not existing:
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
    data = res.json()

    if "data" not in data:
        return "Không có dữ liệu"

    # Lọc leads hợp lệ
    valid_leads = filter_leads_data(data["data"])

    # Khởi tạo báo cáo theo sản phẩm
    product_stats = {}
    for prod_key in PRODUCTS.keys():
        product_stats[prod_key] = {"leads": 0, "orders": 0, "revenue": 0}
    product_stats["Khác"] = {"leads": 0, "orders": 0, "revenue": 0}

    # Xử lý từng lead
    for lead in valid_leads:
        product = get_product_from_lead(lead)

        # Gộp Bảo Thần Khang vào Tâm Não An
        if product == "Bảo Thần Khang":
            product = "Tâm Não An"

        product_stats[product]["leads"] += 1

        # Kiểm tra đơn hàng
        if lead.get("lgtDonHangTrangThaiChotDon") == 1:
            product_stats[product]["orders"] += 1
            money = round(lead.get("lgtDonHangTienThuKhach") or 0)
            product_stats[product]["revenue"] += money

    # Nếu có filter, gọi hàm báo cáo chi tiết theo sản phẩm
    if product_filter:
        return get_product_detail_report(product_filter, product_stats[product_filter])

    # ===== LẤY CHI PHÍ ADS CHỈ TỪ CAMPAIGN CỦA BẠN =====
    total_ads_spend = 0
    try:
        # Lấy tổng chi phí từ báo cáo ads (đã lọc campaign của bạn)
        url_insights = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}/insights"
        params_insights = {
            "access_token": META_TOKEN,
            "fields": "spend",
            "date_preset": "today",
            "level": "campaign",
            "limit": 500,
        }
        res_insights = requests.get(url_insights, params=params_insights)
        data_insights = res_insights.json()

        if "data" in data_insights:
            for item in data_insights["data"]:
                # Lọc campaign có tên chứa MY_NAME
                campaign_name = item.get("campaign_name", "")
                if MY_NAME.lower() in campaign_name.lower():
                    total_ads_spend += float(item.get("spend", 0))
    except:
        pass

    # Tạo báo cáo tổng hợp dạng 1 dòng
    tna_revenue = product_stats["Tâm Não An"]["revenue"]
    bkk_revenue = product_stats["Bảo Khớp Khang"]["revenue"]
    hg_revenue = product_stats["Heart Gold"]["revenue"]

    total_leads = sum(s["leads"] for s in product_stats.values())
    total_orders = sum(s["orders"] for s in product_stats.values())
    total_revenue = sum(s["revenue"] for s in product_stats.values())
    cr = (total_orders / total_leads * 100) if total_leads > 0 else 0

    msg = "📊 BÁO CÁO DOANH THU HÔM NAY\n\n"
    msg += f"🧠 Tâm Não An: {tna_revenue:,}đ\n"
    msg += f"🦴 Bảo Khớp Khang: {bkk_revenue:,}đ\n"
    msg += f"💛 Heart Gold: {hg_revenue:,}đ\n\n"
    msg += "📈 TỔNG KẾT\n"
    msg += f"  • Tổng Lead: {total_leads}\n"
    msg += f"  • Tổng Đơn: {total_orders}\n"
    msg += f"  • Tổng Doanh thu: {total_revenue:,}đ\n"
    msg += f"  • Chi phí ads tổng: {int(total_ads_spend):,}đ\n"
    msg += f"  • CR: {cr:.2f}%"

    # Lưu cache
    revenue_cache["data"] = msg
    revenue_cache["time"] = now

    return msg


def get_product_detail_report(product_name, stats):
    """Báo cáo chi tiết cho từng sản phẩm kèm chi phí ads"""

    # Lấy chi phí ads cho sản phẩm
    spend = 0
    campaigns_active = 0

    # Lấy dữ liệu từ Facebook Ads
    try:
        url_insights = f"https://graph.facebook.com/v24.0/{AD_ACCOUNT_ID}/insights"
        params_insights = {
            "access_token": META_TOKEN,
            "level": "campaign",
            "fields": "campaign_name,spend",
            "date_preset": "today",
            "limit": 500,
        }

        res_insights = requests.get(url_insights, params=params_insights)
        data_insights = res_insights.json()

        campaigns = set()
        if "data" in data_insights:
            for ad in data_insights["data"]:
                campaign_name = ad.get("campaign_name", "")
                # Kiểm tra campaign có thuộc sản phẩm này không
                for keyword in PRODUCTS[product_name]["keywords"]:
                    if keyword.lower() in campaign_name.lower():
                        spend += float(ad.get("spend", 0))
                        campaigns.add(campaign_name)
                        break

        campaigns_active = len(campaigns)
    except:
        pass

    # Icon theo sản phẩm
    icons = {"Tâm Não An": "🧠", "Bảo Khớp Khang": "🦴", "Heart Gold": "💛"}
    icon = icons.get(product_name, "📦")

    # Tạo báo cáo
    msg = f"{icon} {product_name}\n"
    msg += f"  • Data: {stats['leads']}\n"
    msg += f"  • Đơn: {stats['orders']}\n"
    msg += f"  • Doanh thu: {stats['revenue']:,}đ\n"
    msg += f"  • Chi phí ads: {int(spend):,}đ\n"
    msg += f"  • Campaign đang hoạt động: {campaigns_active}"

    # Tính ROAS nếu có
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
            product_name = get_product_from_lead(lead)

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


print("Bot Sandbox đã khởi động")
keep_alive()

while True:
    try:
        print(f"🔄 [{get_time_vn().strftime('%H:%M:%S')}] Bắt đầu vòng lặp...")
        check_expiry_dates()
        check_telegram_commands()

        payload = get_payload()
        res = requests.post(url, headers=headers, cookies=cookies, json=payload)
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
