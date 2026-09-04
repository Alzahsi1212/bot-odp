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

PHOTO_API_URL = (
    "https://script.google.com/macros/s/AKfycbwkZ9B4Uhhgcg6zBvdJdGJ7DHtjTt196ExSwue4XVJr0QtjblkMDj84o45c3nIPaTME/exec"
)


# =========================================================
# API KEY
# =========================================================

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
# USER ACCESS / LEVEL
#
# Format users.json:
#
# {
#     "123456789": 2,
#     "987654321": 1
# }
#
# Level:
#
# 0 = tidak memiliki akses
# 1 = user biasa
# 2 = user level 2
#
# Owner selalu level 2.
# =========================================================


def load_users():

    users = {}

    # -----------------------------------------------------
    # Owner selalu level 2
    # -----------------------------------------------------

    try:

        owner_id = str(
            int(OWNER_ID)
        )

        users[owner_id] = 2

    except (
        ValueError,
        TypeError
    ):

        print(
            "OWNER_ID tidak valid."
        )


    # -----------------------------------------------------
    # Jika users.json belum ada
    # -----------------------------------------------------

    if not os.path.exists(
        USERS_FILE
    ):

        try:

            save_users(
                users
            )

            print(
                "users.json dibuat."
            )

        except Exception as e:

            print(
                "Gagal membuat users.json:",
                e
            )

        return users


    # -----------------------------------------------------
    # Baca users.json
    # -----------------------------------------------------

    try:

        with open(
            USERS_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(
                f
            )


        # -------------------------------------------------
        # FORMAT BARU
        #
        # {
        #   "123456": 2
        # }
        # -------------------------------------------------

        if isinstance(
            data,
            dict
        ):

            for user_id, level in data.items():

                try:

                    user_id = str(
                        int(user_id)
                    )

                    level = int(
                        level
                    )

                    # Pastikan level valid
                    if level < 1:
                        level = 1

                    if level > 2:
                        level = 2

                    users[user_id] = level

                except (
                    ValueError,
                    TypeError
                ):

                    print(
                        f"Data user tidak valid: "
                        f"{user_id} -> {level}"
                    )


        # -------------------------------------------------
        # FORMAT LAMA
        #
        # [
        #   123456,
        #   987654
        # ]
        #
        # Semua user lama dianggap level 1.
        # -------------------------------------------------

        elif isinstance(
            data,
            list
        ):

            for user_id in data:

                try:

                    user_id = str(
                        int(user_id)
                    )

                    users[user_id] = 1

                except (
                    ValueError,
                    TypeError
                ):

                    print(
                        f"ID user tidak valid: {user_id}"
                    )


    except Exception as e:

        print(
            "Gagal membaca users.json:",
            e
        )


    # -----------------------------------------------------
    # Owner selalu level 2
    # -----------------------------------------------------

    try:

        users[
            str(int(OWNER_ID))
        ] = 2

    except (
        ValueError,
        TypeError
    ):

        pass


    return users


# =========================================================
# SAVE USERS
# =========================================================

def save_users(
    users
):

    try:

        normalized_users = {}

        # -------------------------------------------------
        # Jika menerima dictionary
        # -------------------------------------------------

        if isinstance(
            users,
            dict
        ):

            for user_id, level in users.items():

                try:

                    user_id = str(
                        int(user_id)
                    )

                    level = int(
                        level
                    )

                    if level < 1:
                        level = 1

                    if level > 2:
                        level = 2

                    normalized_users[
                        user_id
                    ] = level

                except (
                    ValueError,
                    TypeError
                ):

                    print(
                        f"User tidak valid: "
                        f"{user_id}"
                    )


        # -------------------------------------------------
        # Support format set/list lama
        # -------------------------------------------------

        else:

            for user_id in users:

                try:

                    normalized_users[
                        str(int(user_id))
                    ] = 1

                except (
                    ValueError,
                    TypeError
                ):

                    print(
                        f"User tidak valid: "
                        f"{user_id}"
                    )


        # -------------------------------------------------
        # Owner selalu level 2
        # -------------------------------------------------

        normalized_users[
            str(int(OWNER_ID))
        ] = 2


        # -------------------------------------------------
        # Simpan
        # -------------------------------------------------

        with open(
            USERS_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                normalized_users,
                f,
                indent=4
            )


        print(
            f"users.json berhasil disimpan: "
            f"{normalized_users}"
        )


    except Exception as e:

        print(
            "Gagal menyimpan users.json:",
            e
        )


# =========================================================
# GET USER LEVEL
# =========================================================

def get_user_level(
    user_id
):

    try:

        user_id = str(
            int(user_id)
        )

    except (
        ValueError,
        TypeError
    ):

        return 0


    # -----------------------------------------------------
    # Owner selalu level 2
    # -----------------------------------------------------

    try:

        if int(user_id) == int(
            OWNER_ID
        ):

            return 2

    except (
        ValueError,
        TypeError
    ):

        pass


    users = load_users()

    return int(
        users.get(
            user_id,
            0
        )
    )


# =========================================================
# IS ALLOWED
# =========================================================

def is_allowed(
    user_id
):

    return (
        get_user_level(
            user_id
        ) >= 1
    )


# =========================================================
# IS LEVEL 2
# =========================================================

def is_level2(
    user_id
):

    return (
        get_user_level(
            user_id
        ) >= 2
    )


# =========================================================
# IS OWNER
# =========================================================

def is_owner(
    user_id
):

    try:

        return (
            int(user_id)
            ==
            int(OWNER_ID)
        )

    except (
        ValueError,
        TypeError
    ):

        return False


# =========================================================
# ACCESS DECORATOR
# =========================================================

def access_required(
    func
):

    @wraps(func)
    async def wrapper(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        user = update.effective_user

        if not user:
            return


        level = get_user_level(
            user.id
        )


        print(
            f"[ACCESS CHECK] "
            f"ID={user.id} "
            f"Username=@{user.username} "
            f"Level={level}"
        )


        if level < 1:

            if update.message:

                await update.message.reply_text(
                    "⛔️ AKSES DITOLAK\n\n"
                    "Anda belum terdaftar sebagai pengguna bot.\n\n"
                    "Silakan ketik /myid lalu hubungi owner untuk mendapatkan akses."
                )

            print(
                f"[ACCESS DENIED] "
                f"ID={user.id}"
            )

            return


        print(
            f"[ACCESS GRANTED] "
            f"ID={user.id} "
            f"Level={level}"
        )


        return await func(
            update,
            context
        )


    return wrapper


# =========================================================
# LEVEL 2 DECORATOR
#
# Digunakan khusus untuk /cari
# =========================================================

def level2_required(
    func
):

    @wraps(func)
    async def wrapper(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        user = update.effective_user

        if not user:
            return


        level = get_user_level(
            user.id
        )


        print(
            f"[LEVEL 2 CHECK] "
            f"ID={user.id} "
            f"Username=@{user.username} "
            f"Level={level}"
        )


        if level < 2:

            if update.message:

                await update.message.reply_text(
                    "⛔️ AKSES DITOLAK\n\n"
                    "Menu /cari hanya dapat digunakan "
                    "oleh user Level 2."
                )

            print(
                f"[LEVEL 2 DENIED] "
                f"ID={user.id}"
            )

            return


        print(
            f"[LEVEL 2 GRANTED] "
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

def normalize(
    text
):

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
            "Contoh: /info GPK020101"
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
# BUILD CARI RESULT
# =========================================================

def build_cari_result(
    df,
    rk
):

    mask = (
        df["RK"]
        .astype(str)
        .apply(normalize)
        ==
        normalize(rk)
    )

    return df[mask]


# =========================================================
# BUILD CARI MESSAGE
# =========================================================

def build_cari_message(
    hasil,
    rk
):

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


    return text


# =========================================================
# CARI RK
#
# KHUSUS LEVEL 2
#
# Jika dari GROUP:
# hasil TIDAK dikirim ke group.
#
# Bot hanya mengirim:
#
# 🔐 Hasil pencarian dikirim ke private chat Anda.
#
# Kemudian hasil dikirim ke private chat user.
#
# =========================================================

@level2_required
async def cari(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    message = update.message

    if not user or not message:
        return


    # =====================================================
    # CEK ARGUMENT
    # =====================================================

    if not context.args:

        await message.reply_text(
            "Format: /cari <RK>\n"
            "Contoh: /cari GPK0"
        )

        return


    rk = context.args[0].strip()


    if not rk:

        await message.reply_text(
            "❌ RK tidak boleh kosong."
        )

        return


    # =====================================================
    # AMBIL DATA
    # =====================================================

    try:

        df = get_data()

    except Exception as e:

        print(
            "Gagal mengambil data ODP:",
            e
        )

        await message.reply_text(
            "❌ Gagal membaca data ODP."
        )

        return


    # =====================================================
    # CARI RK
    # =====================================================

    hasil = build_cari_result(
        df,
        rk
    )


    # =====================================================
    # RK TIDAK DITEMUKAN
    #
    # Pesan ini aman dikirim ke group karena
    # tidak mengandung data hasil pencarian.
    # =====================================================

    if hasil.empty:

        await message.reply_text(
            "❌ RK tidak ditemukan."
        )

        return


    # =====================================================
    # BUAT HASIL
    # =====================================================

    text = build_cari_message(
        hasil,
        rk
    )


    # =====================================================
    # CEK APAKAH COMMAND DARI GROUP
    # =====================================================

    chat = update.effective_chat

    if not chat:
        return


    is_private = (
        chat.type == "private"
    )


    # =====================================================
    # JIKA COMMAND DARI PRIVATE CHAT
    #
    # Hasil langsung ditampilkan.
    # =====================================================

    if is_private:

        await message.reply_text(
            text
        )

        print(
            f"[CARI] "
            f"User={user.id} "
            f"RK={rk} "
            f"CHAT=PRIVATE"
        )

        return


    # =====================================================
    # JIKA COMMAND DARI GROUP
    #
    # JANGAN KIRIM HASIL KE GROUP.
    #
    # Kirim notifikasi terlebih dahulu.
    # =====================================================

    try:

        await message.reply_text(
            "🔐 Hasil pencarian dikirim ke private chat Anda."
        )

    except Exception as e:

        print(
            "[CARI] Gagal mengirim notifikasi ke group:",
            e
        )


    # =====================================================
    # KIRIM HASIL KE PRIVATE CHAT
    #
    # chat_id user = user.id
    # =====================================================

    try:

        await context.bot.send_message(
            chat_id=user.id,
            text=text
        )


        print(
            f"[CARI] "
            f"Hasil RK={rk} "
            f"berhasil dikirim ke private chat "
            f"User={user.id}"
        )


    except Exception as e:

        print(
            f"[CARI] "
            f"Gagal mengirim private message "
            f"User={user.id}:",
            e
        )


        # -------------------------------------------------
        # Gagal biasanya karena user belum pernah
        # membuka private chat / belum /start bot.
        # -------------------------------------------------

        try:

            await message.reply_text(
                "⚠️ Saya tidak dapat mengirim hasil ke private chat Anda.\n\n"
                "Silakan buka private chat bot ini lalu tekan /start.\n"
                "Setelah itu ulangi /cari <RK> di grup."
            )

        except Exception as notify_error:

            print(
                "[CARI] "
                "Gagal mengirim pesan error ke group:",
                notify_error
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


    mask_sn = (
        df["SN"]
        .astype(str)
        .str.strip()
        .str.upper()
        ==
        keyword_normalized
    )


    mask_brim = (
        df["BRIM ID"]
        .astype(str)
        .str.strip()
        .str.upper()
        ==
        keyword_normalized
    )


    mask_cust = (
        df["CUST ID"]
        .astype(str)
        .str.strip()
        .str.upper()
        ==
        keyword_normalized
    )


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


        if not nama:

            nama = "Nama tidak tersedia"


        if not cust_id:

            cust_id = "CUST ID kosong"


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
# BUILD HIST LIST
# =========================================================

def build_hist_list_message(
    hasil,
    keyword
):

    keyboard = build_hist_keyboard(
        hasil
    )


    text = (
        "🔎 HASIL PENCARIAN CUSTOMER\n\n"
        f"Keyword : {keyword}\n"
        f"Ditemukan : {len(hasil)} data\n\n"
        "Silakan pilih customer:"
    )


    return (
        text,
        InlineKeyboardMarkup(
            keyboard
        )
    )


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


    context.user_data[
        "hist_keyword"
    ] = keyword


    context.user_data[
        "hist_indexes"
    ] = [
        int(index)
        for index in hasil.index
    ]


    text, reply_markup = build_hist_list_message(
        hasil,
        keyword
    )


    await update.message.reply_text(
        text,
        reply_markup=reply_markup
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
# BUILD BACK BUTTON
# =========================================================

def build_hist_back_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Kembali ke List Customer",
                    callback_data="hist_back"
                )
            ]
        ]
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


    caption_detail = build_customer_detail(
        row
    )


    cust_id = str(
        row.get(
            "CUST ID",
            ""
        )
    ).strip()


    # =====================================================
    # HAPUS PESAN MENU PILIHAN LAMA
    # =====================================================

    try:

        await query.delete_message()

        print(
            "[HIST DETAIL] "
            "Pesan list customer berhasil dihapus."
        )

    except Exception as e:

        print(
            "[HIST DETAIL] "
            f"Gagal menghapus pesan list lama: {e}"
        )


    # =====================================================
    # JIKA CUST ID KOSONG
    # =====================================================

    if not cust_id:

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=(
                f"{caption_detail}\n"
                "⚠️ CUST ID kosong, foto tidak dapat dicari."
            ),
            reply_markup=build_hist_back_keyboard()
        )

        return


    # =====================================================
    # NOTIFIKASI SEMENTARA
    # =====================================================

    loading_msg = await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="🔄 Mencari foto rumah..."
    )


    # =====================================================
    # AMBIL FOTO
    # =====================================================

    photo_result = get_customer_photo(
        cust_id
    )


    # =====================================================
    # HAPUS PESAN STATUS PENCARIAN
    # =====================================================

    try:

        await loading_msg.delete()

    except Exception:

        pass


    # =====================================================
    # FOTO TIDAK TERSEDIA
    # =====================================================

    if not photo_result:

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=(
                f"{caption_detail}\n"
                "📷 Foto Rumah tidak tersedia."
            ),
            reply_markup=build_hist_back_keyboard()
        )

        return


    image_bytes, mime_type, extension = (
        photo_result
    )


    # =====================================================
    # KIRIM FOTO DENGAN CAPTION DETAIL
    # =====================================================

    try:

        photo_file = io.BytesIO(
            image_bytes
        )


        photo_file.name = (
            f"foto_rumah_{cust_id}.{extension}"
        )


        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=photo_file,
            caption=caption_detail,
            reply_markup=build_hist_back_keyboard()
        )


        print(
            f"[PHOTO SENT WITH CAPTION] "
            f"CUST ID={cust_id}"
        )


    except Exception as e:

        print(
            "Gagal mengirim foto Telegram:",
            e
        )


        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=(
                f"{caption_detail}\n"
                "❌ Foto ditemukan, tetapi gagal dikirim ke Telegram."
            ),
            reply_markup=build_hist_back_keyboard()
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

        try:

            await query.edit_message_text(
                "⛔️ AKSES DITOLAK\n\n"
                "Anda tidak memiliki akses."
            )

        except Exception:

            pass

        return


    # =====================================================
    # AMBIL KEYWORD PENCARIAN SEBELUMNYA
    # =====================================================

    keyword = context.user_data.get(
        "hist_keyword"
    )


    if not keyword:

        try:

            await query.message.reply_text(
                "❌ Pencarian sebelumnya sudah tidak tersedia."
            )

        except Exception:

            pass

        return


    # =====================================================
    # AMBIL DATA CUSTOMER TERBARU
    # =====================================================

    try:

        df = get_customer_data()

    except Exception as e:

        print(
            "Gagal mengambil data customer:",
            e
        )

        try:

            await query.message.reply_text(
                "❌ Gagal membaca data customer."
            )

        except Exception:

            pass

        return


    # =====================================================
    # CARI ULANG BERDASARKAN KEYWORD
    # =====================================================

    hasil = build_hist_result(
        df,
        keyword
    )


    if hasil.empty:

        try:

            await query.message.reply_text(
                "❌ Data customer sudah tidak ditemukan."
            )

        except Exception:

            pass

        return


    # =====================================================
    # UPDATE INDEX HASIL PENCARIAN
    # =====================================================

    context.user_data[
        "hist_indexes"
    ] = [
        int(index)
        for index in hasil.index
    ]


    # =====================================================
    # BUAT ULANG LIST CUSTOMER
    # =====================================================

    text, reply_markup = build_hist_list_message(
        hasil,
        keyword
    )


    # =====================================================
    # HAPUS PESAN FOTO / DETAIL TERLEBIH DAHULU
    # =====================================================

    try:

        await query.message.delete()

        print(
            "[HIST BACK] "
            "Foto/detail customer berhasil dihapus."
        )

    except Exception as e:

        print(
            "[HIST BACK] "
            f"Gagal menghapus foto/detail customer: {e}"
        )


    # =====================================================
    # KIRIM ULANG LIST CUSTOMER
    # =====================================================

    try:

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=reply_markup
        )

        print(
            "[HIST BACK] "
            "List customer berhasil dikirim ulang."
        )

    except Exception as e:

        print(
            "[HIST BACK] "
            f"Gagal mengirim list customer: {e}"
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
                "📋 History Cust",
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
    # BUTTON CARI
    #
    # HANYA LEVEL 2
    # =====================================================

    if query.data == "cari":

        if not is_level2(
            user.id
        ):

            await query.edit_message_text(
                "⛔️ AKSES DITOLAK\n\n"
                "Menu /cari hanya dapat digunakan "
                "oleh user Level 2."
            )

            return


        await query.edit_message_text(
            "📍 CARI RK\n\n"
            "Gunakan:\n"
            "/cari <RK>\n\n"
            "Contoh:\n"
            "/cari GPK0\n\n"
            "🔐 Jika digunakan dari grup, "
            "hasil akan dikirim ke private chat Anda."
        )

        return


    # =====================================================
    # BUTTON INFO
    # =====================================================

    if query.data == "info":

        await query.edit_message_text(
            "Gunakan:\n"
            "/info <Nama ODP>\n\n"
            "Contoh:\n"
            "/info GPK010101"
        )

        return


    # =====================================================
    # BUTTON HIST
    # =====================================================

    if query.data == "hist":

        await query.edit_message_text(
            "🔎 HISTORY CUSTOMER\n\n"
            "Gunakan:\n"
            "/hist <Nama/SN/Cust ID/BRIM ID>\n\n"
            "Contoh:\n"
            "/hist budi\n"
            "/hist 48575443XXXXXX"
        )

        return


# =========================================================
# ADD USER
#
# Sekarang:
#
# /adduser <Telegram ID>
#
# Default level = 1
#
# Untuk menambahkan Level 2:
#
# /adduser <Telegram ID> 2
#
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
            "/adduser <Telegram ID> [level]\n\n"
            "Default level: 1\n\n"
            "Contoh user biasa:\n"
            "/adduser 392836663\n\n"
            "Contoh user Level 2:\n"
            "/adduser 392836663 2"
        )

        return


    # =====================================================
    # TELEGRAM ID
    # =====================================================

    try:

        new_user_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Telegram ID harus berupa angka."
        )

        return


    # =====================================================
    # LEVEL
    # =====================================================

    level = 1


    if len(
        context.args
    ) >= 2:

        try:

            level = int(
                context.args[1]
            )

        except ValueError:

            await update.message.reply_text(
                "❌ Level harus berupa angka 1 atau 2."
            )

            return


    # =====================================================
    # VALIDASI LEVEL
    # =====================================================

    if level not in (
        1,
        2
    ):

        await update.message.reply_text(
            "❌ Level hanya boleh 1 atau 2.\n\n"
            "1 = User biasa\n"
            "2 = User Level 2"
        )

        return


    # =====================================================
    # OWNER TIDAK PERLU DITAMBAHKAN
    # =====================================================

    if new_user_id == int(
        OWNER_ID
    ):

        await update.message.reply_text(
            "ℹ️ User tersebut adalah OWNER dan otomatis Level 2."
        )

        return


    # =====================================================
    # LOAD USERS
    # =====================================================

    allowed_users = load_users()


    # =====================================================
    # JIKA SUDAH ADA
    # =====================================================

    if str(
        new_user_id
    ) in allowed_users:

        old_level = allowed_users[
            str(new_user_id)
        ]


        # Update level
        allowed_users[
            str(new_user_id)
        ] = level


        save_users(
            allowed_users
        )


        await update.message.reply_text(
            f"✅ LEVEL USER DIPERBARUI\n\n"
            f"Telegram ID: `{new_user_id}`\n"
            f"Level lama: `{old_level}`\n"
            f"Level baru: `{level}`",
            parse_mode="Markdown"
        )


        print(
            f"[USER LEVEL UPDATED] "
            f"ID={new_user_id} "
            f"Level={old_level}->{level} "
            f"oleh OWNER={user.id}"
        )

        return


    # =====================================================
    # TAMBAHKAN USER BARU
    # =====================================================

    allowed_users[
        str(new_user_id)
    ] = level


    save_users(
        allowed_users
    )


    # =====================================================
    # VERIFY
    # =====================================================

    verify_users = load_users()


    if (
        str(new_user_id)
        in verify_users
    ):

        await update.message.reply_text(
            f"✅ USER BERHASIL DITAMBAHKAN\n\n"
            f"Telegram ID: `{new_user_id}`\n"
            f"Level: `{level}`\n\n"
            f"Level 2 dapat menggunakan /cari.",
            parse_mode="Markdown"
        )


        print(
            f"[USER ADDED] "
            f"ID={new_user_id} "
            f"Level={level} "
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


    user_key = str(
        delete_user_id
    )


    if user_key not in allowed_users:

        await update.message.reply_text(
            f"ℹ️ User {delete_user_id} "
            f"tidak ditemukan.",
            parse_mode="Markdown"
        )

        return


    allowed_users.pop(
        user_key
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
        allowed_users,
        key=lambda x: int(x)
    ):

        level = allowed_users[
            user_id
        ]


        if int(
            user_id
        ) == int(
            OWNER_ID
        ):

            text += (
                f"👑 `{user_id}` — OWNER — Level 2\n"
            )

        elif level == 2:

            text += (
                f"⭐ `{user_id}` — Level 2\n"
            )

        else:

            text += (
                f"👤 `{user_id}` — Level 1\n"
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
# SET LEVEL
#
# Command tambahan:
#
# /setlevel <Telegram ID> <level>
#
# Contoh:
#
# /setlevel 392836663 2
#
# =========================================================

async def setlevel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user


    if not is_owner(
        user.id
    ):

        await update.message.reply_text(
            "⛔️ AKSES DITOLAK\n\n"
            "Hanya owner yang dapat mengubah level user."
        )

        return


    if len(
        context.args
    ) < 2:

        await update.message.reply_text(
            "Format:\n\n"
            "/setlevel <Telegram ID> <level>\n\n"
            "Contoh:\n"
            "/setlevel 392836663 2"
        )

        return


    try:

        target_user_id = int(
            context.args[0]
        )

        new_level = int(
            context.args[1]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Telegram ID dan level harus berupa angka."
        )

        return


    if new_level not in (
        1,
        2
    ):

        await update.message.reply_text(
            "❌ Level hanya boleh 1 atau 2."
        )

        return


    if target_user_id == int(
        OWNER_ID
    ):

        await update.message.reply_text(
            "ℹ️ Owner selalu Level 2."
        )

        return


    allowed_users = load_users()


    target_key = str(
        target_user_id
    )


    old_level = allowed_users.get(
        target_key
    )


    if old_level is None:

        await update.message.reply_text(
            "❌ User tidak ditemukan.\n\n"
            "Tambahkan terlebih dahulu dengan:\n"
            "/adduser <Telegram ID> <level>"
        )

        return


    allowed_users[
        target_key
    ] = new_level


    save_users(
        allowed_users
    )


    await update.message.reply_text(
        f"✅ LEVEL BERHASIL DIUBAH\n\n"
        f"Telegram ID: `{target_user_id}`\n"
        f"Level lama: `{old_level}`\n"
        f"Level baru: `{new_level}`",
        parse_mode="Markdown"
    )


    print(
        f"[LEVEL CHANGED] "
        f"ID={target_user_id} "
        f"{old_level}->{new_level} "
        f"oleh OWNER={user.id}"
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
        f"USERS: {load_users()}"
    )


    print(
        "================================="
    )


    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )


    # =====================================================
    # COMMAND HANDLERS
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


    app.add_handler(
        CommandHandler(
            "myid",
            myid
        )
    )


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


    app.add_handler(
        CommandHandler(
            "setlevel",
            setlevel
        )
    )


    # =====================================================
    # HISTORY CUSTOMER CALLBACK
    # =====================================================

    app.add_handler(
        CallbackQueryHandler(
            hist_detail_handler,
            pattern=r"^hist_detail:"
        )
    )


    app.add_handler(
        CallbackQueryHandler(
            hist_back_handler,
            pattern=r"^hist_back$"
        )
    )


    # =====================================================
    # GENERAL BUTTON CALLBACK
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
    # RUN BOT
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
