if hasil.empty:
        await update.message.reply_text("RK tidak ditemukan.")
        return

    # Informasi RK (ditampilkan sekali)
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


if name == "main":
    main()
