import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

TOKEN = os.getenv("TOKEN")
ADMIN_ID = 647251759

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Состояния диалога
ASK_NAME, ASK_PHONE, SELECTING_CITY, STAT_DAY, WORK_DONE, WORKERS_COUNT, PHOTO, EXPENSES, NEEDS, DEADLINE = range(10)

def city_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏙️ Кишинев", callback_data="loc_kisinau")],
        [InlineKeyboardButton("🏢 Бельцы", callback_data="loc_beltsy")],
        [InlineKeyboardButton("🏰 Тирасполь", callback_data="loc_tiraspol")],
        [InlineKeyboardButton("📍 Другая", callback_data="loc_other")]
    ])

def status_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ По плану", callback_data="stat_ok")],
        [InlineKeyboardButton("⚠️ Задержка", callback_data="stat_delay")],
        [InlineKeyboardButton("🏁 Завершено", callback_data="stat_done")]
    ])

def workers_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1–3 человека", callback_data="w_1_3")],
        [InlineKeyboardButton("4–6 человек", callback_data="w_4_6")],
        [InlineKeyboardButton("7+ человек", callback_data="w_7_plus")]
    ])

def needs_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Всё есть", callback_data="need_none")],
        [InlineKeyboardButton("🛒 Нужны материалы", callback_data="need_mat")],
        [InlineKeyboardButton("🔨 Нужен инструмент", callback_data="need_tools")],
        [InlineKeyboardButton("💰 Нужен аванс/смета", callback_data="need_money")]
    ])

def deadline_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏳ Завтра", callback_data="time_tomorrow")],
        [InlineKeyboardButton("📅 2-3 дня", callback_data="time_few_days")],
        [InlineKeyboardButton("🧱 Неделя+", callback_data="time_long")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 **BrigadaMD Control**\n\nДля отмены в любой момент отправь /cancel\n\nКак вас зовут? (Фамилия Имя):",
        parse_mode="Markdown"
    )
    return ASK_NAME

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Отчет отменен. Нажми /start, чтобы начать заново.")
    return ConversationHandler.END

async def process_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["brigadier_name"] = update.message.text
    contact_keyboard = [[KeyboardButton("📱 Отправить номер телефона", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(contact_keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Поделитесь номером телефона:", reply_markup=reply_markup)
    return ASK_PHONE

async def process_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.contact.phone_number if update.message.contact else update.message.text
    context.user_data["brigadier_phone"] = phone
    await update.message.reply_text("Выберите объект:", reply_markup=city_kb())
    return SELECTING_CITY

async def process_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    city_map = {"loc_kisinau": "🏙️ Кишинев", "loc_beltsy": "🏢 Бельцы", "loc_tiraspol": "🏰 Тирасполь", "loc_other": "📍 Другая"}
    context.user_data["city"] = city_map.get(query.data, query.data)
    await query.edit_message_text("⚡ Статус дня:", reply_markup=status_kb(), parse_mode="Markdown")
    return STAT_DAY

async def process_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    status_map = {"stat_ok": "✅ По плану", "stat_delay": "⚠️ Задержка", "stat_done": "🏁 Завершено"}
    context.user_data["status"] = status_map.get(query.data, query.data)
    await query.edit_message_text("🛠️ Что сделано сегодня? (напишите текстом):", parse_mode="Markdown")
    return WORK_DONE

async def process_work_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["work_done"] = update.message.text
    await update.message.reply_text("👥 Сколько человек работало?", reply_markup=workers_kb())
    return WORKERS_COUNT

async def process_workers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    workers_map = {"w_1_3": "1–3 человека", "w_4_6": "4–6 человек", "w_7_plus": "7+ человек"}
    context.user_data["workers_count"] = workers_map.get(query.data, query.data)
    await query.edit_message_text("📸 **Отправьте фото с объекта** (или напишите 'нет', если фото нет):", parse_mode="Markdown")
    return PHOTO

async def process_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data["photo_file_id"] = update.message.photo[-1].file_id
    else:
        context.user_data["photo_file_id"] = None
    
    await update.message.reply_text("💵 Укажите сумму расходов за сегодня (в леях/валюте) или напишите '0':")
    return EXPENSES

async def process_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["expenses"] = update.message.text
    await update.message.reply_text("🛒 Текущие потребности / смета:", reply_markup=needs_kb(), parse_mode="Markdown")
    return NEEDS

async def process_needs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    needs_map = {"need_none": "📦 Всё есть", "need_mat": "🛒 Нужны материалы", "need_tools": "🔨 Нужен инструмент", "need_money": "💰 Нужен аванс/смета"}
    context.user_data["needs"] = needs_map.get(query.data, query.data)
    await query.edit_message_text("⏳ Сроки сдачи этапа:", reply_markup=deadline_kb(), parse_mode="Markdown")
    return DEADLINE

async def process_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    deadline_map = {"time_tomorrow": "⏳ Завтра", "time_few_days": "📅 2-3 дня", "time_long": "🧱 Неделя+"}
    context.user_data["deadline"] = deadline_map.get(query.data, query.data)
    
    data = context.user_data
    report = (
        f"🚨 **ОТЧЕТ ПО ОБЪЕКТУ**\n\n"
        f"👤 **Бригадир:** {data.get('brigadier_name')}\n"
        f"📞 **Телефон:** `{data.get('brigadier_phone')}`\n"
        f"📍 **Локация:** {data.get('city')}\n"
        f"📊 **Статус:** {data.get('status')}\n"
        f"📝 **Сделано:** {data.get('work_done')}\n"
        f"👷 **Людей:** {data.get('workers_count')}\n"
        f"💵 **Расходы/Аванс:** {data.get('expenses')}\n"
        f"🛒 **Потребности:** {data.get('needs')}\n"
        f"⏳ **Сроки:** {data.get('deadline')}"
    )
    
    try:
        if data.get('photo_file_id'):
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=data.get('photo_file_id'), caption=report, parse_mode="Markdown")
        else:
            await context.bot.send_message(chat_id=ADMIN_ID, text=report, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error sending report: {e}")
        
    await query.edit_message_text("✅ Отчет отправлен руководству!", parse_mode="Markdown")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_name)],
            ASK_PHONE: [MessageHandler(filters.CONTACT | filters.TEXT, process_phone)],
            SELECTING_CITY: [CallbackQueryHandler(process_city, pattern="^loc_")],
            STAT_DAY: [CallbackQueryHandler(process_status, pattern="^stat_")],
            WORK_DONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_work_done)],
            WORKERS_COUNT: [CallbackQueryHandler(workers_kb, pattern="^w_") | MessageHandler(filters.TEXT, process_workers)], # Поддержка кнопок
            PHOTO: [MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), process_photo)],
            EXPENSES: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_expenses)],
            NEEDS: [CallbackQueryHandler(process_needs, pattern="^need_")],
            DEADLINE: [CallbackQueryHandler(process_deadline, pattern="^time_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()