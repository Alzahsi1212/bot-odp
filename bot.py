import pandas as pd
import os
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from config import TOKEN


# =========================================================
# KONFIGURASI
# =========================================================

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSJ534j22x_3ltjW7WSWXbH0PAAiDUiBCjlRWCFtVuYVBVx_1Scs3xkR5_QfewWeLK0tD5pfd9c63KU/pub?output=csv"

# Telegram User ID OWNER
# Ambil dari Railway Variables
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# File untuk menyimpan daftar user
USERS_FILE = "users.json"

# Cache data Google Sheet
cached_df = None


# =========================================================
# USER ACCESS / WHITELIST
# =========================================================

def load_users():
    """
    Membaca daftar Telegram ID yang diizinkan.
    """

    if not os.path.exists(USERS_FILE):

        users = [OWNER_ID]

        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(users, f, indent=4)

        except Exception as e:
            print("Gagal membuat users.json:", e)

        return set(users)

    try:

        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)

        users = set(int(user_id) for user_id in users)

        # Owner selalu mendapatkan akses
        users.add(OWNER_ID)

        return users

    except Exception as e:

        print("Gagal membaca users.json:", e)

        # Jika file bermasalah, owner tetap memiliki akses
        return {OWNER_ID}


def save_users():

    try:

        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(
                sorted(ALLOWED_USERS),
                f,
                indent=4
            )

    except Exception as e:

        print("Gagal menyimpan users.json:", e)


# Daftar user yang memiliki akses
ALLOWED_USERS = load_users()


def is_allowed(user_id):

    return user_id in ALLOWED_USERS


def is_owner(user_id):

    return user_id == OWNER_ID


# =========================================================
# ACCESS DECORATOR
# =========================================================

def access_required(func):

    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):

        user = update.effective_user

        if not user:
            return

        # Cek Telegram ID
        if not is_allowed(user.id):

            if update.message:

                await update.message.reply_text(
                    "⛔ AKSES DITOLAK\n\n"
                    "Anda belum terdaftar sebagai pengguna bot.\n\n"
                    "Silakan hubungi owner untuk mendapatkan akses."
                )

            print(
                f"[ACCESS DENIED] "
                f"ID={user.id} "
                f"Username=@{user.username}"
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
            "Format: /info <Nama ODP>\n"
            "Contoh: /info KMR010101"
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
            "ODP tidak ditemukan."
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
            "Format: /cari <RK>\n"
            "Contoh: /cari KMR"
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
            "RK tidak ditemukan."
        )

        return

    # Informasi RK
    text = (
        f"📍 LIST ODP RK {rk.upper()}\n\n"
        f"PIN      : {hasil.iloc[0].get('PIN', '-')}\n"
        f"Backbone : {hasil.iloc[0].get('Backbone', '-')}\n"
        f"Tikor    : {hasil.iloc[0].get('Tikor', '-')}\n\n"
        f"Daftar ODP:\n"
    )

    # Daftar ODP
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
            "Anda belum terdaftar sebagai pengguna bot.\n\n"
            "Silakan hubungi owner untuk mendapatkan akses."
        )

        return

    # -----------------------------------------------------
    # DATA
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
            "Gunakan:\n"
            "/cari <RK>\n\n"
            "Contoh:\n"
            "/cari KMR"
        )

    # -----------------------------------------------------
    # INFO
    # -----------------------------------------------------

    elif query.data == "info":

        await query.edit_message_text(
            "Gunakan:\n"
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

    # Hanya OWNER
    if not is_owner(user.id):

        await update.message.reply_text(
            "⛔ AKSES DITOLAK\n\n"
            "Hanya owner yang dapat menambahkan user."
        )

        return

    if not context.args:

        await update.message.reply_text(
            "Format:\n\n"
            "/adduser <Telegram ID>\n\n"
            "Contoh:\n"
            "/adduser 123456789"
        )

        return

    try:

        new_user_id = int(context.args[0])

    except ValueError:

        await update.message.reply_text(
            "❌ Telegram ID harus berupa angka."
        )

        return

    # Cek apakah sudah ada
    if new_user_id in ALLOWED_USERS:

        await update.message.reply_text(
            f"ℹ️ User {new_user_id} sudah memiliki akses."
        )

        return

    # Tambahkan
    ALLOWED_USERS.add(new_user_id)

    save_users()

    await update.message.reply_text(
        f"✅ USER BERHASIL DITAMBAHKAN\n\n"
        f"Telegram ID: `{new_user_id}`\n\n"
        f"User sekarang dapat menggunakan bot.",
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

    # Hanya OWNER
    if not is_owner(user.id):

        await update.message.reply_text(
            "⛔ AKSES DITOLAK\n\n"
            "Hanya owner yang dapat menghapus user."
        )

        return

    if not context.args:

        await update.message.reply_text(
            "Format:\n\n"
            "/deluser <Telegram ID>\n\n"
            "Contoh:\n"
            "/deluser 123456789"
        )

        return

    try:

        delete_user_id = int(context.args[0])

    except ValueError:

        await update.message.reply_text(
            "❌ Telegram ID harus berupa angka."
        )

        return

    # Owner tidak boleh dihapus
    if delete_user_id == OWNER_ID:

        await update.message.reply_text(
            "❌ Owner tidak dapat dihapus."
        )

        return

    # Cek user
    if delete_user_id not in ALLOWED_USERS:

        await update.message.reply_text(
            f"ℹ️ User {delete_user_id} tidak ditemukan."
        )

        return

    # Hapus user
    ALLOWED_USERS.remove(delete_user_id)

    save_users()

    await update.message.reply_text(
        f"✅ AKSES USER DICABUT\n\n"
        f"Telegram ID: `{delete_user_id}`",
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

    # Hanya OWNER
    if not is_owner(user.id):

        await update.message.reply_text(
            "⛔ AKSES DITOLAK\n\n"
            "Hanya owner yang dapat melihat daftar user."
        )

        return

    text = "👥 USER YANG MEMILIKI AKSES\n\n"

    for user_id in sorted(ALLOWED_USERS):

        if user_id == OWNER_ID:

            text += (
                f"👑 {user_id} — OWNER\n"
            )

        else:

            text += (
                f"👤 {user_id}\n"
            )

    text += (
        f"\nTotal user: {len(ALLOWED_USERS)}"
    )

    await update.message.reply_text(text)


# =========================================================
# MAIN
# =========================================================

def main():

    app = Application.builder().token(TOKEN).build()

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
    # BUTTON HANDLER
    # -----------------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    # -----------------------------------------------------
    # AUTO REFRESH
    # -----------------------------------------------------

    job_queue = app.job_queue

    job_queue.run_repeating(
        refresh_data,
        interval=60,
        first=5
    )

    # -----------------------------------------------------
    # START
    # -----------------------------------------------------

    print("Bot berjalan 🚀")
    print(f"OWNER_ID: {OWNER_ID}")
    print(f"ALLOWED_USERS: {ALLOWED_USERS}")

    app.run_polling(
        drop_pending_updates=True
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
