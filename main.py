import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

TOKEN = os.getenv("TOKEN", "8625974540:AAEX6_RvqiR3wegyGbCYUiJLOA6mz5ZNV6k")
ADMIN_ID = 647251759

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

SELECTING_CITY, STAT_DAY, WORK_DONE, NEEDS, DEADLINE = range(5)

def city_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏙️ Кишинев", callback_data="loc_kisinau")],
        [InlineKeyboardButton("🏢 Бельцы", callback_data="loc_beltsy")],
        [InlineKeyboardButton("🏰 Тирасполь", callback_data="loc_tiraspol")],
        [InlineKeyboardButton("📍 Другой", callback_data="loc_other")]
    ])

def status_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ По плану", callback_data="stat_ok")],
        [InlineKeyboardButton("⚠️ Задержка", callback_data="stat_delay")],
        [InlineKeyboardButton("🏁 Завершено", callback_data="stat_done")]
    ])

def needs_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Всё есть", callback_data="need_none")],
        [InlineKeyboardButton("🛒 Нужны материалы", callback_data="need_mat")],
        [InlineKeyboardButton("🔨 Нужен инструмент", callback_data="need_tools")]
    ])

def deadline_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏳ Завтра", callback_data="time_tomorrow")],
        [InlineKeyboardButton("📅 2-3 дня", callback_data="time_few_days")],
        [InlineKeyboardButton("🧱 Неделя+", callback_data="time_long")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 **Отчет бригадира (BrigadaMD)**\n\nВыбери локацию:", reply_markup=city_kb(), parse_mode="Markdown")
    return SELECTING_CITY

async def process_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["city"] = query.data
    await query.edit_message_text("⚡ Статус дня:", reply_markup=status_kb(), parse_mode="Markdown")
    return STAT_DAY

async def process_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["status"] = query.data
    await query.edit_message_text("🛠️ Что сделано сегодня? (напиши текстом):", parse_mode="Markdown")
    return WORK_DONE

async def process_work_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["work_done"] = update.message.text
    await update.message.reply_text("🛒 Потребности:", reply_markup=needs_kb(), parse_mode="Markdown")
    return NEEDS

async def process_needs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["needs"] = query.data
    await query.edit_message_text("⏳ Сроки сдачи:", reply_markup=deadline_kb(), parse_mode="Markdown")
    return DEADLINE

async def process_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = context.user_data
    report = f"🚨 **ОТЧЕТ**\n📍 {data.get('city')}\n📊 {data.get('status')}\n📝 {data.get('work_done')}"
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=report, parse_mode="Markdown")
    except Exception as e:
        logging.error(e)
    await query.edit_message_text("✅ Отчет отправлен!", parse_mode="Markdown")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_CITY: [CallbackQueryHandler(process_city, pattern="^loc_")],
            STAT_DAY: [CallbackQueryHandler(process_status, pattern="^stat_")],
            WORK_DONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_work_done)],
            NEEDS: [CallbackQueryHandler(process_needs, pattern="^need_")],
            DEADLINE: [CallbackQueryHandler(process_deadline, pattern="^time_")],
        },
        fallbacks=[],
    )
    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()
