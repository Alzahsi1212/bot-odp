import pandas as pd
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from config import TOKEN

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSJ534j22x_3ltjW7WSWXbH0PAAiDUiBCjlRWCFtVuYVBVx_1Scs3xkR5_QfewWeLK0tD5pfd9c63KU/pub?output=csv"

cached_df = None


def normalize(text):
    return str(text).strip().upper()


def get_data():
    global cached_df
    if cached_df is None:
        cached_df = pd.read_csv(URL)
    return cached_df


# =========================
# AUTO REFRESH (JOBQUEUE FIX)
# =========================
def refresh_data(context: ContextTypes.DEFAULT_TYPE):
    global cached_df
    try:
        cached_df = pd.read_csv(URL)
        print("Data berhasil di-refresh")
    except Exception as e:
        print("Gagal refresh:", e)


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot ODP Biznet\n\n"
        "/menu\n"
        "/info <ODP>\n"
        "/cari <RK>\n"
        "/list\n"
    )


# =========================
# INFO ODP (FIX KEYERROR)
# =========================
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Format: /info <Nama ODP> contoh: /info KMR010101")
        return

    nama_odp = context.args[0]
    df = get_data()

    # FIX: pakai boolean mask yang benar
    mask = df["Nama ODP"].astype(str).apply(normalize) == normalize(nama_odp)
    hasil = df[mask]

    if hasil.empty:
        await update.message.reply_text("ODP tidak ditemukan.")
        return

    row = hasil.iloc[0]

    pesan = f"""
📌 INFO ODP

Nama ODP : {row['Nama ODP']}
RK       : {row['RK']}
IP OLT   : {row['IP OLT']}
PIU      : {row['PIU']}
Lokasi   : {row['Lokasi']}
"""

    await update.message.reply_text(pesan)


# =========================
# CARI RK
# =========================
async def cari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Format: /cari <RK> contoh: /cari KMR")
        return

    rk = context.args[0]
    df = get_data()

    mask = df["RK"].astype(str).apply(normalize) == normalize(rk)
    hasil = df[mask]

    if hasil.empty:
        await update.message.reply_text("RK tidak ditemukan.")
        return

    text = f"📍 LIST ODP RK {rk.upper()}\n\n"

    for _, row in hasil.iterrows():
        text += f"- {row['Nama ODP']} | {row['PIU']} | {row['Lokasi']}\n"

    await update.message.reply_text(text)


# =========================
# LIST
# =========================
async def list_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    df = get_data()

    text = "📋 SEMUA DATA ODP\n\n"

    for _, row in df.iterrows():
        text += f"{row['Nama ODP']} | {row['RK']} | {row['PIU']}\n"

    await update.message.reply_text(text)


# =========================
# MENU
# =========================
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📍 Cari RK", callback_data="cari")],
        [InlineKeyboardButton("📋 List Data", callback_data="list")],
        [InlineKeyboardButton("ℹ️ Info ODP", callback_data="info")]
    ]

    await update.message.reply_text(
        "Pilih menu:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# BUTTON HANDLER
# =========================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    df = get_data()

    if query.data == "list":
        text = "📋 LIST DATA\n\n"
        text += "\n".join([f"{r['Nama ODP']} | {r['RK']}" for _, r in df.iterrows()])
        await query.edit_message_text(text)

    elif query.data == "cari":
        await query.edit_message_text("Gunakan: /cari <RK>")

    elif query.data == "info":
        await query.edit_message_text("Gunakan: /info <Nama ODP>")


# =========================
# MAIN
# =========================
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("cari", cari))
    app.add_handler(CommandHandler("list", list_all))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button_handler))

    # JOBQUEUE SAFE
    job_queue = app.job_queue
    job_queue.run_repeating(refresh_data, interval=60, first=5)

    print("Bot berjalan 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
