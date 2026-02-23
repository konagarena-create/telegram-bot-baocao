import re
import gspread
import pandas as pd
import schedule
import time
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from oauth2client.service_account import ServiceAccountCredentials

TOKEN = "8010095154:AAHZqtWjrmNTXjSG1ndxdZ8F_t0CTatk75w"

# ===== KẾT NỐI GOOGLE SHEETS =====
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("BaoCaoCa").worksheet("DuLieu")


# ===== HÀM TÁCH SỐ =====
def extract_number(pattern, text):
    match = re.search(pattern, text, re.IGNORECASE)
    return int(match.group(1)) if match else 0


# ===== HÀM PARSE BÁO CÁO =====
def parse_report(text):
    data = {}
    lines = text.split("\n")

    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()

    # TÁCH TỐC ĐỘ
    td_text = data.get("Tốc độ", "")
    td_bb = extract_number(r"(\d+)\s*biên\s*bản", td_text)
    td_nguoi = extract_number(r"(\d+)\s*nguội", td_text)

    return {
        "Ngày": data.get("Ngày", ""),
        "Ca": data.get("Ca", ""),
        "Tổ": data.get("Tổ", ""),
        "Bb": int(data.get("Bb", 0)),
        "Cồn": data.get("Cồn", ""),
        "QKQT": int(data.get("QKQT", 0)),
        "Tốc độ BB": td_bb,
        "Tốc độ nguội": td_nguoi,
        "Xe khách": int(data.get("Xe khách", 0)),
        "Vạch kẻ đường": int(data.get("Vạch kẻ đường", 0)),
        "Khác": int(data.get("Khác", 0)),
        "Tạm giữ": int(data.get("Tạm giữ", 0)),
        "ĐKP": int(data.get("ĐKP", 0))
    }


# ===== XỬ LÝ TIN NHẮN =====
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text.startswith("/ca"):

        parsed = parse_report(update.message.text)

        row = [
            parsed["Ngày"],
            parsed["Ca"],
            parsed["Tổ"],
            parsed["Bb"],
            parsed["Cồn"],
            parsed["QKQT"],
            parsed["Tốc độ BB"],
            parsed["Tốc độ nguội"],
            parsed["Xe khách"],
            parsed["Vạch kẻ đường"],
            parsed["Khác"],
            parsed["Tạm giữ"],
            parsed["ĐKP"]
        ]

        sheet.append_row(row)

        await update.message.reply_text("Đã ghi nhận báo cáo ✅")


# ===== TỔNG HỢP 23H =====
def daily_summary():
    ws = client.open("BaoCaoCa").worksheet("DuLieu")
    data = ws.get_all_records()
    df = pd.DataFrame(data)

    today = datetime.now().strftime("%d/%m/%Y")
    df_today = df[df["Ngày"] == today]

    if not df_today.empty:
        summary = df_today.sum(numeric_only=True)

        client.open("BaoCaoCa").worksheet("ThongKe").append_row(
            [today] + summary.tolist()
        )


schedule.every().day.at("23:00").do(daily_summary)


# ===== CHẠY BOT =====
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, handle_message))

print("Bot đang chạy...")
app.run_polling()