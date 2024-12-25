from telegram.ext import Application, CommandHandler, MessageHandler, filters
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import re

# Thiết lập logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Cấu hình Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Đọc thông tin từ biến môi trường
credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if not credentials_json:
    raise ValueError("Environment variable GOOGLE_APPLICATION_CREDENTIALS_JSON is not set")

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    json.loads(credentials_json),
    scope
)
client = gspread.authorize(creds)
sheet = client.open("Thu Chi").sheet1  # Đảm bảo tên Google Sheet chính xác

# Hàm xử lý lệnh /start
async def start(update, context):
    await update.message.reply_text("Chào mừng bạn đến với bot quản lý thu chi! Gõ tin nhắn để thêm dữ liệu.")

# Hàm xử lý lệnh /add
async def add(update, context):
    try:
        # Lấy nội dung tin nhắn
        message = update.message.text.strip()

        # Xác định loại giao dịch
        if message.startswith('+'):  # Nếu có dấu +
            loai = "Thu"
            message = message[1:].strip()  # Bỏ dấu + và các khoảng trắng
        else:
            loai = "Chi"

        # Tách số tiền và mô tả
        match = re.match(r"(\d+(\.\d+)?)([kKtrTR]*)\s+(.*)", message)
        if not match:
            await update.message.reply_text(
                "Sai cú pháp! Vui lòng nhập như: '+25k tiền lương' hoặc '5tr ny cho'"
            )
            return

        # Lấy số tiền
        so_tien = float(match.group(1))  # Lấy phần số
        don_vi = match.group(3).lower()  # Lấy đơn vị (k hoặc tr)

        if don_vi == "k":  # Nếu đơn vị là "k" (nghìn)
            so_tien *= 1000
        elif don_vi == "tr":  # Nếu đơn vị là "tr" (triệu)
            so_tien *= 1000000

        so_tien = int(so_tien)  # Chuyển số tiền thành số nguyên

        # Lấy mô tả
        mo_ta = match.group(4).strip()

        # Lưu vào Google Sheet
        sheet.append_row([loai, mo_ta, so_tien])
        await update.message.reply_text(f"Đã ghi nhận: {loai} {so_tien:,} VND - {mo_ta}")
    except Exception as e:
        await update.message.reply_text(f"Có lỗi xảy ra: {e}")

# Hàm xử lý tin nhắn không hợp lệ
async def unknown(update, context):
    await update.message.reply_text("Xin lỗi, tôi không hiểu lệnh của bạn.")

def main():
    # Đọc Telegram Bot Token từ biến môi trường
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("Environment variable TELEGRAM_BOT_TOKEN is not set")

    # Tạo ứng dụng bot
    application = Application.builder().token(bot_token).build()

    # Thêm các handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add))  # Xử lý tin nhắn

    # Chạy bot
    application.run_polling()

if __name__ == "__main__":
    main()
