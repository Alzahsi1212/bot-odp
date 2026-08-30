import pandas as pd
import os
import json

from functools import wraps

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from config import TOKEN, OWNER_ID


URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSJ534j22x_3ltjW7WSWXbH0PAAiDUiBCjlRWCFtVuYVBVx_1Scs3xkR5_QfewWeLK0tD5pfd9c63KU/pub?output=csv"

# =========================================================
# KONFIGURASI ACCESS CONTROL
# =========================================================

USERS_FILE = "users.json"

cached_df = None


# =========================================================
# LOAD / SAVE USER
# =========================================================

def load_users():
    """
    Membaca daftar user dari users.json.
    Jika file belum ada, otomatis membuat dengan OWNER_ID.
    """

    if not os.path.exists(USERS_FILE):
        users = {
            str(OWNER_ID)
        }

        save_users(users)
        return users

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Pastikan semuanya string
        users = set(str(user_id) for user_id in data)

        # Owner selalu dimasukkan
        users.add(str(OWNER_ID))

        return users

    except Exception as e:
        print("Gagal membaca users.json:", e)

        # Jika terjadi error, minimal owner tetap memiliki akses
        return {str(OWNER_ID)}


def save_users(users):
    """
    Menyimpan daftar user ke users.json.
    """

    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(
                sorted(list(users)),
                f,
                indent=4
            )

    except Exception as e:
        print("Gagal menyimpan users.json:", e)


# Load user ketika bot mulai
ALLOWED_USERS = load_users()


# =========================================================
# ACCESS CONTROL
# =========================================================

def is_allowed(user_id):
    """
    Mengecek apakah Telegram User ID memiliki akses.
    """

    return str(user_id) in ALLOWED_USERS


def is_owner(user_id):
    """
    Mengecek apakah user adalah owner.
    """

    return int(user_id) == int(OWNER_ID)


def access_required(func):
    """
    Decorator untuk command yang hanya boleh digunakan
    oleh user yang sudah mendapatkan akses.
    """

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):

        user = update.effective_user

        if not user:
            return

        if not is_allowed(user.id):

            await update.message.reply_text(
                "⛔ AKSES DITOLAK\n\n"
                "Anda belum terdaftar sebagai pengguna bot.\n"
                "Silakan hubungi owner untuk mendapatkan akses."
            )

            print(
                f"[ACCESS DENIED] "
                f"{user.id} - "
                f"{user.username}"
            )

            return

        return await func(update, context)

    return wrapper


# =========================================================
# NORMALIZE
# =========================================================

def normalize(text):
    return str(text).strip().upper()


# =========================================================
# GET DATA
# =========================================================

def get_data():
    global cached_df

    if cached_df is None:

        cached_df = pd.read_csv(
            URL,
            dtype={
                "PIN": str,
                "Port1": str,
                "Port2": str,
                "Port3": str,
                "Port4": str,
                "Port5": str,
                "Port6": str,
                "Port7": str,
                "Port8": str,
                "Port9": str,
                "Port10": str,
                "Port11": str,
                "Port12": str,
                "Port13": str,
                "Port14": str,
                "Port15": str,
                "Port16": str
            }
        )

    return cached_df


# =========================================================
# AUTO REFRESH
# =========================================================

def refresh_data(context: ContextTypes.DEFAULT_TYPE):

    global cached_df

    try:

        cached_df = pd.read_csv(
            URL,
            dtype={
                "PIN": str,
                "Port1": str,
                "Port2": str,
                "Port3": str,
                "Port4": str,
                "Port5": str,
                "Port6": str,
                "Port7": str,
                "Port8": str,
                "Port9": str,
                "Port10": str,
                "Port11": str,
                "Port12": str,
                "Port13": str,
                "Port14": str,
                "Port15": str,
                "Port16": str
            }
        )

        print("Data berhasil di-refresh")

    except Exception as e:

        print("Gagal refresh:", e)


# =========================================================
# START
# =========================================================

@access_required
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "Bot ODP Biznet\n\n"
        "BOT dibuat sekedar untuk membantu pekerjaan. "
        "Maaf jika Bot sering mengalami kendala, "
        "jangan cari yang tidak ada :)\n\n"
        "/menu\n"
        "/info <ODP>\n"
        "/cari <RK>\n"
        "/list"
    )


# =========================================================
# INFO ODP
# =========================================================

@access_required
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "Format:\n"
            "/info <Nama ODP>\n\n"
            "Contoh:\n"
            "/info KMR010101"
        )

        return

    nama_odp = context.args[0]

    df = get_data()

    mask = (
        df["Nama ODP"]
        .astype(str)
        .apply(normalize)
        == normalize(nama_odp)
    )

    hasil = df[mask]

    if hasil.empty:

        await update.message.reply_text(
            "❌ ODP tidak ditemukan."
        )

        return

    row = hasil.iloc[0]

    pesan = f"""
📌 INFO ODP

Nama ODP : {row['Nama ODP']}
RK       : {row['RK']}
IP OLT   : {row['IP OLT']}
PIU      : {row['PIU']}
Lokasi   : {row['Lokasi']}

Port1    : {row['Port1']}
Port2    : {row['Port2']}
Port3    : {row['Port3']}
Port4    : {row['Port4']}
Port5    : {row['Port5']}
Port6    : {row['Port6']}
Port7    : {row['Port7']}
Port8    : {row['Port8']}
Port9    : {row['Port9']}
Port10   : {row['Port10']}
Port11   : {row['Port11']}
Port12   : {row['Port12']}
Port13   : {row['Port13']}
Port14   : {row['Port14']}
Port15   : {row['Port15']}
Port16   : {row['Port16']}
"""

    await update.message.reply_text(pesan)


# =========================================================
# CARI RK
# =========================================================

@access_required
async def cari(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text(
            "Format:\n"
            "/cari <RK>\n\n"
            "Contoh:\n"
            "/cari KMR"
        )

        return

    rk = context.args[0]

    df = get_data()

    mask = (
        df["RK"]
        .astype(str)
        .apply(normalize)
        == normalize(rk)
    )

    hasil = df[mask]

    if hasil.empty:

        await update.message.reply_text(
            "❌ RK tidak ditemukan."
        )

        return

    text = (
        f"📍 LIST ODP RK {rk.upper()}\n\n"
        f"PIN      : {hasil.iloc[0].get('PIN', '-')}\n"
        f"Backbone : {hasil.iloc[0].get('Backbone', '-')}\n"
        f"Tikor    : {hasil.iloc[0].get('Tikor', '-')}\n\n"
        f"Daftar ODP:\n"
    )

    for _, row in hasil.iterrows():

        text += (
            f"- {row.get('Nama ODP', '-')} | "
            f"{row.get('PIU', '-')} | "
            f"{row.get('Lokasi', '-')}\n"
        )

    await update.message.reply_text(text)


# =========================================================
# LIST SEMUA DATA
# =========================================================

@access_required
async def list_all(update: Update, context: ContextTypes.DEFAULT_TYPE):

    df = get_data()

    text = "📋 SEMUA DATA ODP\n\n"

    for _, row in df.iterrows():

        text += (
            f"{row['Nama ODP']} | "
            f"{row['RK']} | "
            f"{row['PIU']}\n"
        )

    await update.message.reply_text(text)


# =========================================================
# MENU
# =========================================================

@access_required
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "📍 Cari RK",
                callback_data="cari"
            )
        ],
        [
            InlineKeyboardButton(
                "ℹ️ Info ODP",
                callback_data="info"
            )
        ]
    ]

    await update.message.reply_text(
        "Pilih menu:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# BUTTON HANDLER
# =========================================================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user = query.from_user

    await query.answer()

    # -----------------------------------------------------
    # CEK AKSES
    # -----------------------------------------------------

    if not is_allowed(user.id):

        await query.edit_message_text(
            "⛔ AKSES DITOLAK\n\n"
            "Anda belum terdaftar sebagai pengguna bot.\n"
            "Silakan hubungi owner untuk mendapatkan akses."
        )

        print(
            f"[BUTTON ACCESS DENIED] "
            f"{user.id} - "
            f"{user.username}"
        )

        return

    # -----------------------------------------------------
    # AMBIL DATA
    # -----------------------------------------------------

    df = get_data()

    # -----------------------------------------------------
    # LIST
    # -----------------------------------------------------

    if query.data == "list":

        text = "📋 LIST DATA\n\n"

        text += "\n".join(
            [
                f"{r['Nama ODP']} | {r['RK']}"
                for _, r in df.iterrows()
            ]
        )

        await query.edit_message_text(text)

    # -----------------------------------------------------
    # CARI
    # -----------------------------------------------------

    elif query.data == "cari":

        await query.edit_message_text(
            "Gunakan command:\n\n"
            "/cari <RK>\n\n"
            "Contoh:\n"
            "/cari KMR"
        )

    # -----------------------------------------------------
    # INFO
    # -----------------------------------------------------

    elif query.data == "info":

        await query.edit_message_text(
            "Gunakan command:\n\n"
            "/info <Nama ODP>\n\n"
            "Contoh:\n"
            "/info KMR010101"
        )


# =========================================================
# ADD USER
# =========================================================

async def adduser(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    # -----------------------------------------------------
    # HANYA OWNER
    # -----------------------------------------------------

    if not is_owner(user.id):

        await update.message.reply_text(
            "⛔ PERMISSION DENIED\n\n"
            "Hanya owner yang dapat menambahkan user."
        )

        return

    # -----------------------------------------------------
    # CEK ARGUMENT
    # -----------------------------------------------------

    if not context.args:

        await update.message.reply_text(
            "Format:\n\n"
            "/adduser <Telegram_ID>\n\n"
            "Contoh:\n"
            "/adduser 123456789"
        )

        return

    # -----------------------------------------------------
    # VALIDASI ID
    # -----------------------------------------------------

    try:

        new_user_id = int(context.args[0])

    except ValueError:

        await update.message.reply_text(
            "❌ Telegram ID harus berupa angka."
        )

        return

    # -----------------------------------------------------
    # CEK USER SUDAH ADA
    # -----------------------------------------------------

    if str(new_user_id) in ALLOWED_USERS:

        await update.message.reply_text(
            f"ℹ️ User `{new_user_id}` "
            f"sudah memiliki akses.",
            parse_mode="Markdown"
        )

        return

    # -----------------------------------------------------
    # TAMBAHKAN USER
    # -----------------------------------------------------

    ALLOWED_USERS.add(str(new_user_id))

    save_users(ALLOWED_USERS)

    await update.message.reply_text(
        f"✅ USER BERHASIL DITAMBAHKAN\n\n"
        f"Telegram ID : `{new_user_id}`\n\n"
        f"User sekarang sudah dapat menggunakan bot.",
        parse_mode="Markdown"
    )

    print(
        f"[USER ADDED] "
        f"{new_user_id} "
        f"oleh OWNER {user.id}"
    )


# =========================================================
# DELETE USER
# =========================================================

async def deluser(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    # -----------------------------------------------------
    # HANYA OWNER
    # -----------------------------------------------------

    if not is_owner(user.id):

        await update.message.reply_text(
            "⛔ PERMISSION DENIED\n\n"
            "Hanya owner yang dapat menghapus user."
        )

        return

    # -----------------------------------------------------
    # CEK ARGUMENT
    # -----------------------------------------------------

    if not context.args:

        await update.message.reply_text(
            "Format:\n\n"
            "/deluser <Telegram_ID>\n\n"
            "Contoh:\n"
            "/deluser 123456789"
        )

        return

    # -----------------------------------------------------
    # VALIDASI ID
    # -----------------------------------------------------

    try:

        delete_user_id = int(context.args[0])

    except ValueError:

        await update.message.reply_text(
            "❌ Telegram ID harus berupa angka."
        )

        return

    # -----------------------------------------------------
    # OWNER TIDAK BOLEH DIHAPUS
    # -----------------------------------------------------

    if delete_user_id == OWNER_ID:

        await update.message.reply_text(
            "❌ Owner tidak dapat dihapus dari akses bot."
        )

        return

    # -----------------------------------------------------
    # CEK USER
    # -----------------------------------------------------

    if str(delete_user_id) not in ALLOWED_USERS:

        await update.message.reply_text(
            f"ℹ️ User `{delete_user_id}` "
            f"tidak ditemukan dalam daftar akses.",
            parse_mode="Markdown"
        )

        return

    # -----------------------------------------------------
    # HAPUS USER
    # -----------------------------------------------------

    ALLOWED_USERS.remove(str(delete_user_id))

    save_users(ALLOWED_USERS)

    await update.message.reply_text(
        f"✅ AKSES USER DICABUT\n\n"
        f"Telegram ID : `{delete_user_id}`\n\n"
        f"User tersebut tidak dapat menggunakan bot lagi.",
        parse_mode="Markdown"
    )

    print(
        f"[USER REMOVED] "
        f"{delete_user_id} "
        f"oleh OWNER {user.id}"
    )


# =========================================================
# LIST USER
# =========================================================

async def users(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    # -----------------------------------------------------
    # HANYA OWNER
    # -----------------------------------------------------

    if not is_owner(user.id):

        await update.message.reply_text(
            "⛔ PERMISSION DENIED\n\n"
            "Hanya owner yang dapat melihat daftar user."
        )

        return

    # -----------------------------------------------------
    # DAFTAR USER
    # -----------------------------------------------------

    text = (
        "👥 DAFTAR USER YANG MEMILIKI AKSES\n\n"
    )

    sorted_users = sorted(
        ALLOWED_USERS,
        key=lambda x: int(x)
    )

    for user_id in sorted_users:

        if int(user_id) == int(OWNER_ID):

            text += (
                f"👑 `{user_id}` — OWNER\n"
            )

        else:

            text += (
                f"👤 `{user_id}`\n"
            )

    text += (
        f"\nTotal user: {len(ALLOWED_USERS)}"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    # -----------------------------------------------------
    # COMMAND UTAMA
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "info",
            info
        )
    )

    app.add_handler(
        CommandHandler(
            "cari",
            cari
        )
    )

    app.add_handler(
        CommandHandler(
            "list",
            list_all
        )
    )

    app.add_handler(
        CommandHandler(
            "menu",
            menu
        )
    )

    # -----------------------------------------------------
    # COMMAND OWNER
    # -----------------------------------------------------

    app.add_handler(
        CommandHandler(
            "adduser",
            adduser
        )
    )

    app.add_handler(
        CommandHandler(
            "deluser",
            deluser
        )
    )

    app.add_handler(
        CommandHandler(
            "users",
            users
        )
    )

    # -----------------------------------------------------
    # BUTTON
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    # -----------------------------------------------------
    # AUTO REFRESH DATA
    # -----------------------------------------------------

    job_queue = app.job_queue

    job_queue.run_repeating(
        refresh_data,
        interval=60,
        first=5
    )

    print("Bot berjalan 🚀")
    print(f"Owner ID: {OWNER_ID}")
    print(f"User yang memiliki akses: {ALLOWED_USERS}")

    # -----------------------------------------------------
    # RUN BOT
    # -----------------------------------------------------

    app.run_polling(
        drop_pending_updates=True
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
