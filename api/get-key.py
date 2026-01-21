from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
import re
import urllib.parse
import json

# ==========================================
# 1. CẤU HÌNH DỮ LIỆU CÁC GAME
# ==========================================
# Điền link nguồn để lấy key và link tải mediafire tương ứng cho từng game
GAME_DATA = {
    "pubg": {
        "source_url": "https://hackobbvip.site/GETKEY/ObbVip&type=PUBG",
        "download_url": "https://www.mediafire.com/file/pubg-link-ví-dụ"
    },
    "freefire": {
        "source_url": "https://hackobbvip.site/GETKEY/ObbVip&type=PUBG",
        "download_url": "https://www.mediafire.com/file/ff-link-ví-dụ"
    },
    "lienquan": {
        "source_url": "https://hackobbvip.site/GETKEY/ObbVip&type=com.garena.game.kgvo",
        "download_url": "https://www.mediafire.com/file/lq-link-ví-dụ"
    },
    "deltaforce": {
        "source_url": "https://hackobbvip.site/GETKEY/ObbVip&type=com.netease.newspike",
        "download_url": "https://www.mediafire.com/file/df-link-ví-dụ"
    },
    "bloodstrike": {
        "source_url": "https://hackobbvip.site/GETKEY/ObbVip&type=com.netease.newspike", # Ví dụ từ code cũ
        "download_url": "https://www.mediafire.com/file/bs-link-ví-dụ"
    }
}

# API Key của bạn (Vẫn cảnh báo: nên dùng biến môi trường trên Vercel để bảo mật)
MY_API_KEY = os.environ.get("LINK4M_API_KEY")

# ==========================================
# 2. LOGIC CŨ CỦA BẠN (GIỮ NGUYÊN)
# ==========================================
# --- Hàm Bước 1: Lấy link Yeulink (Giữ nguyên) ---
def get_yeulink_from_source(source_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(source_url, headers=headers, timeout=10)
        match = re.search(r'https://yeulink\.com/[a-zA-Z0-9]+', response.text)
        if match:
            return match.group(0)
        return None
    except Exception as e:
        return None

# --- Hàm Bước 2: Lấy link đích sau khi chuyển hướng (Giữ nguyên logic của bạn) ---
def get_final_redirect_url(long_url):
    base_api = "https://link4m.co/st" 
    api_key = MY_API_KEY
    encoded_url = urllib.parse.quote(long_url)
    full_request_url = f"{base_api}?api={api_key}&url={encoded_url}"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        # requests.get mặc định sẽ "đi theo" chuyển hướng (follow redirects)
        response = requests.get(full_request_url, headers=headers, timeout=15)
        final_url = response.url
        
        # Kiểm tra xem có đúng là đã ra link kết quả chưa
        if "link4m.com" in final_url or "link4m.co" in final_url:
            return final_url
        else:
            return f"Có lỗi, link dừng lại tại: {final_url}"
    except Exception as e:
        return f"Lỗi ở Bước 2: {e}"

# ==========================================
# 3. VERCEL SERVERLESS HANDLER
# ==========================================
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Phân tích URL để lấy tham số 'game' (ví dụ: /api/get-key?game=pubg)
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        game_id = query_params.get('game', [None])[0]

        # Kiểm tra game có tồn tại trong data không
        if game_id not in GAME_DATA:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Game không hợp lệ"}).encode('utf-8'))
            return

        # Lấy URL nguồn tương ứng
        url_nguon = GAME_DATA[game_id]["source_url"]

        # --- CHẠY LOGIC CỦA BẠN ---
        link_buoc_1 = get_yeulink_from_source(url_nguon)
        
        result_link = ""
        status = "error"

        if link_buoc_1:
            # Chạy bước 2
            link_ket_qua = get_final_redirect_url(link_buoc_1)
            if "http" in link_ket_qua and "Lỗi" not in link_ket_qua:
                 result_link = link_ket_qua
                 status = "success"
            else:
                 result_link = link_ket_qua # Trả về thông báo lỗi từ hàm bước 2
        else:
             result_link = "Không lấy được link gốc từ nguồn."

        # Trả về kết quả dạng JSON cho Frontend
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        # Cho phép frontend gọi API này (CORS)
        self.send_header('Access-Control-Allow-Origin', '*') 
        self.end_headers()
        response_data = {"status": status, "link": result_link}
        self.wfile.write(json.dumps(response_data).encode('utf-8'))

        return
