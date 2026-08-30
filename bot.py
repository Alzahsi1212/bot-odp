import pandas as pd
import os
import json
import base64
import io
import requests

from functools import wraps

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from config import TOKEN, OWNER_ID


# =========================================================
# KONFIGURASI
# =========================================================


# =========================================================
# GOOGLE SHEET 1 - DATA ODP
# =========================================================

URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vSJ534j22x_3ltjW7WSWXbH0PAAiDUiBCjlRWCFtVuYVBVx_1Scs3xkR5_QfewWeLK0tD5pfd9c63KU/"
    "pub?output=csv"
)


# =========================================================
# GOOGLE SHEET 2 - DATA CUSTOMER
# =========================================================

CUSTOMER_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vSJ534j22x_3ltjW7WSWXbH0PAAiDUiBCjlRWCFtVuYVBVx_1Scs3xkR5_QfewWeLK0tD5pfd9c63KU/"
    "pub?gid=2141022117&single=true&output=csv"
)


# =========================================================
# GOOGLE APPS SCRIPT - FOTO CUSTOMER
# =========================================================
#
# MASUKKAN URL WEB APP APPS SCRIPT ANDA DI SINI.
#
# Contoh:
#
# PHOTO_API_URL = "https://script.google.com/macros/s/XXXXXXXXXXXX/exec"
#
# Jangan menggunakan URL Google Sheet.
# Yang digunakan adalah URL deployment Web App Apps Script.
#

PHOTO_API_URL = (
    "https://script.google.com/macros/s/AKfycbwkZ9B4Uhhgcg6zBvdJdGJ7DHtjTt196ExSwue4XVJr0QtjblkMDj84o45c3nIPaTME/exec"
)


# =========================================================
# API KEY
# =========================================================
#
# Harus sama dengan API_KEY di Apps Script.
#
# Contoh:
#
# API_KEY = "ODP_BOT_2026_RAHASIA"
#

API_KEY = (
    "8962683694:AAHdUNfswp0hRAYyoBnfcsS3d8NKvdd9yzs"
)


# =========================================================
# LOKASI USERS.JSON
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

USERS_FILE = os.path.join(
    BASE_DIR,
    "users.json"
)


# =========================================================
# CACHE DATA
# =========================================================

cached_df = None

cached_customer_df = None


# =========================================================
# USER ACCESS
# =========================================================

def load_users():

    users = set()

    # Owner selalu memiliki akses
    users.add(
        int(OWNER_ID)
    )

    if not os.path.exists(USERS_FILE):

        try:

            save_users(users)

            print(
                "users.json dibuat."
            )

        except Exception as e:

            print(
                "Gagal membuat users.json:",
                e
            )

        return users

    try:

        with open(
            USERS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        for user_id in data:

            try:

                users.add(
                    int(user_id)
                )

            except (
                ValueError,
                TypeError
            ):

                print(
                    f"ID user tidak valid di users.json: {user_id}"
                )

    except Exception as e:

        print(
            "Gagal membaca users.json:",
            e
        )

    # Owner selalu ditambahkan
    users.add(
        int(OWNER_ID)
    )

    return users


# =========================================================
# SAVE USERS
# =========================================================

def save_users(users):

    try:

        data = sorted(
            [
                int(user_id)
                for user_id in users
            ]
        )

        with open(
            USERS_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4
            )

        print(
            f"users.json berhasil disimpan: {data}"
        )

    except Exception as e:

        print(
            "Gagal menyimpan users.json:",
            e
        )


# =========================================================
# IS ALLOWED
# =========================================================

def is_allowed(user_id):

    try:

        user_id = int(
            user_id
        )

    except (
        ValueError,
        TypeError
    ):

        return False

    allowed_users = load_users()

    return user_id in allowed_users


# =========================================================
# IS OWNER
# =========================================================

def is_owner(user_id):

    try:

        return (
            int(user_id)
            == int(OWNER_ID)
        )

    except (
        ValueError,
        TypeError
    ):

        return False


# =========================================================
# ACCESS DECORATOR
# =========================================================

def access_required(func):

    @wraps(func)
    async def wrapper(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        user = update.effective_user

        if not user:
            return

        print(
            f"[ACCESS CHECK] "
            f"ID={user.id} "
            f"Username=@{user.username}"
        )

        if not is_allowed(
            user.id
        ):

            if update.message:

                await update.message.reply_text(
                    "⛔️ AKSES DITOLAK\n\n"
                    "Anda belum terdaftar sebagai pengguna bot.\n\n"
                    "Silakan hubungi owner untuk mendapatkan akses."
                )

            print(
                f"[ACCESS DENIED] "
                f"ID={user.id}"
            )

            return

        print(
            f"[ACCESS GRANTED] "
            f"ID={user.id}"
        )

        return await func(
            update,
            context
        )

    return wrapper


# =========================================================
# NORMALIZE
# =========================================================

def normalize(text):

    return str(
        text
    ).strip().upper()


# =========================================================
# GET DATA ODP
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
# GET DATA CUSTOMER
# =========================================================

def get_customer_data():

    global cached_customer_df

    if cached_customer_df is None:

        cached_customer_df = pd.read_csv(
            CUSTOMER_URL,
            dtype=str
        ).fillna("")

    return cached_customer_df


# =========================================================
# AUTO REFRESH
# =========================================================

def refresh_data(
    context: ContextTypes.DEFAULT_TYPE
):

    global cached_df
    global cached_customer_df


    # =====================================================
    # REFRESH DATA ODP
    # =====================================================

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

        print(
            "Data ODP berhasil di-refresh"
        )

    except Exception as e:

        print(
            "Gagal refresh data ODP:",
            e
        )


    # =====================================================
    # REFRESH CUSTOMER
    # =====================================================

    try:

        cached_customer_df = pd.read_csv(
            CUSTOMER_URL,
            dtype=str
        ).fillna("")

        print(
            "Data Customer berhasil di-refresh"
        )

    except Exception as e:

        print(
            "Gagal refresh data Customer:",
            e
        )


# =========================================================
# MY ID
# =========================================================

async def myid(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    if not user:
        return

    await update.message.reply_text(
        f"🆔 TELEGRAM ID ANDA\n\n"
        f"ID: `{user.id}`\n\n"
        f"Username: @{user.username if user.username else '-'}",
        parse_mode="Markdown"
    )


# =========================================================
# START
# =========================================================

@access_required
async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "Bot ODP Biznet\n\n"
        "BOT dibuat sekedar untuk membantu pekerjaan. "
        "Maaf jika Bot sering mengalami kendala, "
        "jangan cari yang tidak ada :)\n\n"
        "/menu\n"
        "/info <ODP>\n"
        "/cari <RK>\n"
        "/hist <Nama/SN/BRIM ID/CUST ID>"
    )


# =========================================================
# INFO ODP
# =========================================================

@access_required
async def info(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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
        ==
        normalize(nama_odp)
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

    await update.message.reply_text(
        pesan
    )


# =========================================================
# CARI RK
# =========================================================

@access_required
async def cari(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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
        ==
        normalize(rk)
    )

    hasil = df[mask]

    if hasil.empty:

        await update.message.reply_text(
            "RK tidak ditemukan."
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
            f"- {row.get('Nama ODP', '-')}"
            f" | {row.get('PIU', '-')}"
            f" | {row.get('Lokasi', '-')}\n"
        )

    await update.message.reply_text(
        text
    )


# =========================================================
# BUILD HIST RESULT
# =========================================================

def build_hist_result(
    df,
    keyword
):

    keyword_normalized = normalize(
        keyword
    )


    # =====================================================
    # NAMA = PARTIAL
    # =====================================================

    mask_nama = (
        df["Nama"]
        .astype(str)
        .str.upper()
        .str.contains(
            keyword_normalized,
            regex=False,
            na=False
        )
    )


    # =====================================================
    # SN = EXACT
    # =====================================================

    mask_sn = (
        df["SN"]
        .astype(str)
        .str.strip()
        .str.upper()
        ==
        keyword_normalized
    )


    # =====================================================
    # BRIM ID = EXACT
    # =====================================================

    mask_brim = (
        df["BRIM ID"]
        .astype(str)
        .str.strip()
        .str.upper()
        ==
        keyword_normalized
    )


    # =====================================================
    # CUST ID = EXACT
    # =====================================================

    mask_cust = (
        df["CUST ID"]
        .astype(str)
        .str.strip()
        .str.upper()
        ==
        keyword_normalized
    )


    # =====================================================
    # GABUNGKAN
    # =====================================================

    return df[
        mask_nama
        |
        mask_sn
        |
        mask_brim
        |
        mask_cust
    ]


# =========================================================
# BUILD HIST KEYBOARD
# =========================================================

def build_hist_keyboard(
    hasil
):

    keyboard = []

    for index, row in hasil.iterrows():

        nama = str(
            row.get(
                "Nama",
                "-"
            )
        ).strip()

        cust_id = str(
            row.get(
                "CUST ID",
                "-"
            )
        ).strip()


        # Telegram callback_data maksimal 64 byte.
        # Index dataframe biasanya cukup pendek.
        callback_data = (
            f"hist_detail:{index}"
        )


        keyboard.append(
            [
                InlineKeyboardButton(
                    f"👤 {nama} | {cust_id}",
                    callback_data=callback_data
                )
            ]
        )

    return keyboard


# =========================================================
# HIST CUSTOMER
# =========================================================

@access_required
async def hist(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(
            "🔎 PENCARIAN CUSTOMER\n\n"
            "Format:\n"
            "/hist <kata pencarian>\n\n"
            "Pencarian berdasarkan:\n"
            "• Nama → sebagian nama\n"
            "• SN → sama persis\n"
            "• BRIM ID → sama persis\n"
            "• CUST ID → sama persis\n\n"
            "Contoh:\n"
            "/hist budi\n"
            "/hist ZTE123456\n"
            "/hist BRM123456\n"
            "/hist CUST123456"
        )

        return


    keyword = " ".join(
        context.args
    ).strip()


    if not keyword:

        await update.message.reply_text(
            "❌ Kata pencarian tidak boleh kosong."
        )

        return


    try:

        df = get_customer_data()

    except Exception as e:

        print(
            "Gagal mengambil data customer:",
            e
        )

        await update.message.reply_text(
            "❌ Gagal membaca data Customer dari Google Sheet."
        )

        return


    kolom_wajib = [
        "Nama",
        "SN",
        "BRIM ID",
        "CUST ID"
    ]


    kolom_tidak_ada = [
        kolom
        for kolom in kolom_wajib
        if kolom not in df.columns
    ]


    if kolom_tidak_ada:

        await update.message.reply_text(
            "❌ Kolom berikut tidak ditemukan di Sheet2:\n\n"
            +
            "\n".join(
                kolom_tidak_ada
            )
        )

        return


    hasil = build_hist_result(
        df,
        keyword
    )


    if hasil.empty:

        await update.message.reply_text(
            f"❌ DATA CUSTOMER TIDAK DITEMUKAN\n\n"
            f"Pencarian: {keyword}"
        )

        return


    # =====================================================
    # SIMPAN KEYWORD
    # =====================================================

    context.user_data[
        "hist_keyword"
    ] = keyword


    # =====================================================
    # SIMPAN INDEX HASIL
    # =====================================================

    context.user_data[
        "hist_indexes"
    ] = [
        int(index)
        for index in hasil.index
    ]


    keyboard = build_hist_keyboard(
        hasil
    )


    text = (
        "🔎 HASIL PENCARIAN CUSTOMER\n\n"
        f"Keyword : {keyword}\n"
        f"Ditemukan : {len(hasil)} data\n\n"
        "Silakan pilih customer:"
    )


    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# GET PHOTO FROM APPS SCRIPT
# =========================================================

def get_customer_photo(
    cust_id
):

    if (
        not PHOTO_API_URL
        or
        PHOTO_API_URL.startswith(
            "PASTE_"
        )
    ):

        print(
            "PHOTO_API_URL belum dikonfigurasi."
        )

        return None


    try:

        response = requests.get(
            PHOTO_API_URL,
            params={
                "cust_id": str(cust_id),
                "api_key": API_KEY
            },
            timeout=30
        )


        print(
            f"[PHOTO API] "
            f"HTTP={response.status_code}"
        )


        if response.status_code != 200:

            print(
                "PHOTO API error:",
                response.text[:500]
            )

            return None


        result = response.json()


        if not result.get(
            "success",
            False
        ):

            print(
                "PHOTO API gagal:",
                result.get(
                    "error",
                    "Unknown error"
                )
            )

            return None


        image_base64 = result.get(
            "image_base64"
        )


        if not image_base64:

            print(
                "PHOTO API: image_base64 kosong."
            )

            return None


        image_bytes = base64.b64decode(
            image_base64
        )


        mime_type = result.get(
            "mime_type",
            "image/jpeg"
        )


        extension = (
            "jpg"
            if mime_type == "image/jpeg"
            else
            "png"
            if mime_type == "image/png"
            else
            "jpg"
        )


        return (
            image_bytes,
            mime_type,
            extension
        )


    except Exception as e:

        print(
            "Gagal mengambil foto customer:",
            e
        )

        return None


# =========================================================
# BUILD CUSTOMER DETAIL
# =========================================================

def build_customer_detail(
    row
):

    return (
        "👤 DETAIL CUSTOMER\n\n"

        f"Tim        : {row.get('Tim', '-')}\n"
        f"Tanggal    : {row.get('Tanggal', '-')}\n"
        f"Nama       : {row.get('Nama', '-')}\n"
        f"BRIM ID    : {row.get('BRIM ID', '-')}\n"
        f"CUST ID    : {row.get('CUST ID', '-')}\n"
        f"SN         : {row.get('SN', '-')}\n"
        f"Layanan    : {row.get('Layanan', '-')}\n"
        f"Alamat     : {row.get('Alamat', '-')}\n"
        f"ODP        : {row.get('ODP', '-')}\n"
        f"Port DP    : {row.get('Port DP', '-')}\n"
        f"Kabel      : {row.get('Kabel', '-')}\n"
        f"Tikor      : {row.get('Tikor', '-')}\n"
    )


# =========================================================
# HIST DETAIL
# =========================================================

async def hist_detail_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user = query.from_user

    await query.answer()


    # =====================================================
    # CEK AKSES
    # =====================================================

    if not is_allowed(
        user.id
    ):

        await query.edit_message_text(
            "⛔️ AKSES DITOLAK\n\n"
            "Anda tidak memiliki akses."
        )

        return


    # =====================================================
    # AMBIL INDEX
    # =====================================================

    try:

        index = int(
            query.data.split(
                ":",
                1
            )[1]
        )

    except Exception:

        await query.edit_message_text(
            "❌ Data customer tidak valid."
        )

        return


    # =====================================================
    # AMBIL DATA
    # =====================================================

    try:

        df = get_customer_data()

    except Exception as e:

        print(
            "Gagal mengambil data customer:",
            e
        )

        await query.edit_message_text(
            "❌ Gagal membaca data customer."
        )

        return


    # =====================================================
    # CEK INDEX
    # =====================================================

    if index not in df.index:

        await query.edit_message_text(
            "❌ Data customer sudah tidak tersedia."
        )

        return


    row = df.loc[index]


    # =====================================================
    # DETAIL
    # =====================================================

    pesan = build_customer_detail(
        row
    )


    # =====================================================
    # TOMBOL KEMBALI
    # =====================================================

    keyboard = [

        [
            InlineKeyboardButton(
                "🔙 Kembali ke hasil",
                callback_data="hist_back"
            )
        ]

    ]


    reply_markup = InlineKeyboardMarkup(
        keyboard
    )


    # =====================================================
    # EDIT PESAN MENJADI DETAIL
    # =====================================================

    try:

        await query.edit_message_text(
            pesan,
            reply_markup=reply_markup
        )

    except Exception as e:

        print(
            "Gagal edit detail:",
            e
        )

        return


    # =====================================================
    # AMBIL CUST ID
    # =====================================================

    cust_id = str(
        row.get(
            "CUST ID",
            ""
        )
    ).strip()


    if not cust_id:

        await query.message.reply_text(
            "⚠️ CUST ID kosong, foto tidak dapat dicari."
        )

        return


    # =====================================================
    # CEK FOTO
    # =====================================================

    await query.message.reply_text(
        "🔄 Mencari foto rumah..."
    )


    photo_result = get_customer_photo(
        cust_id
    )


    if not photo_result:

        await query.message.reply_text(
            "📷 Foto Rumah tidak tersedia."
        )

        return


    image_bytes, mime_type, extension = (
        photo_result
    )


    # =====================================================
    # KIRIM FOTO
    # =====================================================

    try:

        photo_file = io.BytesIO(
            image_bytes
        )


        photo_file.name = (
            f"foto_rumah_{cust_id}.{extension}"
        )


        await query.message.reply_photo(
            photo=photo_file,
            caption=(
                f"📷 Foto Rumah\n"
                f"CUST ID: {cust_id}"
            )
        )


        print(
            f"[PHOTO SENT] "
            f"CUST ID={cust_id}"
        )


    except Exception as e:

        print(
            "Gagal mengirim foto Telegram:",
            e
        )

        await query.message.reply_text(
            "❌ Foto ditemukan, tetapi gagal dikirim ke Telegram."
        )


# =========================================================
# HIST BACK
# =========================================================

async def hist_back_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user = query.from_user

    await query.answer()


    # =====================================================
    # CEK AKSES
    # =====================================================

    if not is_allowed(
        user.id
    ):

        await query.edit_message_text(
            "⛔️ AKSES DITOLAK\n\n"
            "Anda tidak memiliki akses."
        )

        return


    # =====================================================
    # KEYWORD
    # =====================================================

    keyword = context.user_data.get(
        "hist_keyword"
    )


    if not keyword:

        await query.edit_message_text(
            "❌ Pencarian sebelumnya sudah tidak tersedia."
        )

        return


    # =====================================================
    # DATA
    # =====================================================

    try:

        df = get_customer_data()

    except Exception as e:

        print(
            "Gagal mengambil data customer:",
            e
        )

        await query.edit_message_text(
            "❌ Gagal membaca data customer."
        )

        return


    # =====================================================
    # HASIL
    # =====================================================

    hasil = build_hist_result(
        df,
        keyword
    )


    if hasil.empty:

        await query.edit_message_text(
            "❌ Data customer sudah tidak ditemukan."
        )

        return


    # =====================================================
    # UPDATE INDEX
    # =====================================================

    context.user_data[
        "hist_indexes"
    ] = [
        int(index)
        for index in hasil.index
    ]


    # =====================================================
    # KEYBOARD
    # =====================================================

    keyboard = build_hist_keyboard(
        hasil
    )


    text = (
        "🔎 HASIL PENCARIAN CUSTOMER\n\n"
        f"Keyword : {keyword}\n"
        f"Ditemukan : {len(hasil)} data\n\n"
        "Silakan pilih customer:"
    )


    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# =========================================================
# LIST
# =========================================================

@access_required
async def list_all(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    df = get_data()

    text = (
        "📋 SEMUA DATA ODP\n\n"
    )

    for _, row in df.iterrows():

        text += (
            f"{row['Nama ODP']} | "
            f"{row['RK']} | "
            f"{row['PIU']}\n"
        )

    await update.message.reply_text(
        text
    )


# =========================================================
# MENU
# =========================================================

@access_required
async def menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

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
        ],

        [
            InlineKeyboardButton(
                "📋 History Customer",
                callback_data="hist"
            )
        ]

    ]


    await update.message.reply_text(
        "Pilih menu:",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
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


    # =====================================================
    # CEK AKSES
    # =====================================================

    if not is_allowed(
        user.id
    ):

        await query.edit_message_text(
            "⛔️ AKSES DITOLAK\n\n"
            "Anda belum terdaftar sebagai pengguna bot.\n\n"
            "Silakan hubungi owner untuk mendapatkan akses."
        )

        print(
            f"[BUTTON ACCESS DENIED] "
            f"ID={user.id}"
        )

        return


    # =====================================================
    # CARI RK
    # =====================================================

    if query.data == "cari":

        await query.edit_message_text(
            "Gunakan:\n"
            "/cari <RK>\n\n"
            "Contoh:\n"
            "/cari KMR"
        )

        return


    # =====================================================
    # INFO ODP
    # =====================================================

    if query.data == "info":

        await query.edit_message_text(
            "Gunakan:\n"
            "/info <Nama ODP>\n\n"
            "Contoh:\n"
            "/info KMR010101"
        )

        return


    # =====================================================
    # HIST
    # =====================================================

    if query.data == "hist":

        await query.edit_message_text(
            "🔎 HISTORY CUSTOMER\n\n"
            "Gunakan:\n"
            "/hist <kata pencarian>\n\n"
            "Contoh:\n"
            "/hist budi\n"
            "/hist CUST123456"
        )

        return


# =========================================================
# ADD USER
# =========================================================

async def adduser(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if not is_owner(
        user.id
    ):

        await update.message.reply_text(
            "⛔️ AKSES DITOLAK\n\n"
            "Hanya owner yang dapat menambahkan user."
        )

        return


    if not context.args:

        await update.message.reply_text(
            "Format:\n\n"
            "/adduser <Telegram ID>\n\n"
            "Contoh:\n"
            "/adduser 392836663"
        )

        return


    try:

        new_user_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Telegram ID harus berupa angka."
        )

        return


    allowed_users = load_users()


    if new_user_id in allowed_users:

        await update.message.reply_text(
            f"ℹ️ User `{new_user_id}` "
            f"sudah memiliki akses.",
            parse_mode="Markdown"
        )

        return


    allowed_users.add(
        new_user_id
    )


    save_users(
        allowed_users
    )


    verify_users = load_users()


    if new_user_id in verify_users:

        await update.message.reply_text(
            f"✅ USER BERHASIL DITAMBAHKAN\n\n"
            f"Telegram ID: `{new_user_id}`\n\n"
            f"User sekarang dapat menggunakan bot.",
            parse_mode="Markdown"
        )

        print(
            f"[USER ADDED] "
            f"ID={new_user_id} "
            f"oleh OWNER={user.id}"
        )

    else:

        await update.message.reply_text(
            "❌ User gagal disimpan.\n\n"
            "Periksa log Railway."
        )


# =========================================================
# DELETE USER
# =========================================================

async def deluser(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if not is_owner(
        user.id
    ):

        await update.message.reply_text(
            "⛔️ AKSES DITOLAK\n\n"
            "Hanya owner yang dapat menghapus user."
        )

        return


    if not context.args:

        await update.message.reply_text(
            "Format:\n\n"
            "/deluser <Telegram ID>\n\n"
            "Contoh:\n"
            "/deluser 392836663"
        )

        return


    try:

        delete_user_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Telegram ID harus berupa angka."
        )

        return


    if delete_user_id == int(
        OWNER_ID
    ):

        await update.message.reply_text(
            "❌ Owner tidak dapat dihapus."
        )

        return


    allowed_users = load_users()


    if delete_user_id not in allowed_users:

        await update.message.reply_text(
            f"ℹ️ User `{delete_user_id}` "
            f"tidak ditemukan.",
            parse_mode="Markdown"
        )

        return


    allowed_users.remove(
        delete_user_id
    )


    save_users(
        allowed_users
    )


    await update.message.reply_text(
        f"✅ AKSES USER DICABUT\n\n"
        f"Telegram ID: `{delete_user_id}`",
        parse_mode="Markdown"
    )


    print(
        f"[USER REMOVED] "
        f"ID={delete_user_id} "
        f"oleh OWNER={user.id}"
    )


# =========================================================
# USERS
# =========================================================

async def users(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if not is_owner(
        user.id
    ):

        await update.message.reply_text(
            "⛔️ AKSES DITOLAK\n\n"
            "Hanya owner yang dapat melihat daftar user."
        )

        return


    allowed_users = load_users()


    text = (
        "👥 USER YANG MEMILIKI AKSES\n\n"
    )


    for user_id in sorted(
        allowed_users
    ):

        if user_id == int(
            OWNER_ID
        ):

            text += (
                f"👑 `{user_id}` — OWNER\n"
            )

        else:

            text += (
                f"👤 `{user_id}`\n"
            )


    text += (
        f"\nTotal user: "
        f"{len(allowed_users)}"
    )


    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "================================="
    )

    print(
        "BOT ODP BIZNET"
    )

    print(
        f"OWNER_ID: {OWNER_ID}"
    )

    print(
        f"USERS_FILE: {USERS_FILE}"
    )

    print(
        f"ALLOWED_USERS: {load_users()}"
    )

    print(
        "================================="
    )


    # =====================================================
    # BUILD APPLICATION
    # =====================================================

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )


    # =====================================================
    # COMMAND
    # =====================================================

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
            "hist",
            hist
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


    # =====================================================
    # MY ID
    # =====================================================

    app.add_handler(
        CommandHandler(
            "myid",
            myid
        )
    )


    # =====================================================
    # OWNER
    # =====================================================

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


    # =====================================================
    # HIST DETAIL
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            hist_detail_handler,
            pattern=r"^hist_detail:"
        )
    )


    # =====================================================
    # HIST BACK
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            hist_back_handler,
            pattern=r"^hist_back$"
        )
    )


    # =====================================================
    # BUTTON UMUM
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )


    # =====================================================
    # AUTO REFRESH
    # =====================================================

    job_queue = app.job_queue


    job_queue.run_repeating(
        refresh_data,
        interval=60,
        first=5
    )


    # =====================================================
    # RUN
    # =====================================================

    print(
        "Bot berjalan 🚀"
    )


    app.run_polling(
        drop_pending_updates=True
    )


# =========================================================
# RUN PROGRAM
# =========================================================

if __name__ == "__main__":

    main()
