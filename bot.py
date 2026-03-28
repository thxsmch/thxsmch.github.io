"""
Empire Showroom — Telegram Bot
Requires: pip install python-telegram-bot==20.7
Set BOT_TOKEN and WEBAPP_URL in env or directly below.
"""

import os
import json
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    WebAppInfo, MenuButtonWebApp,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── CONFIG ──────────────────────────────────────────────
BOT_TOKEN  = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com/empire_showroom/")
# ────────────────────────────────────────────────────────


# ── /start ──────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "🛍  Открыть магазин",
            web_app=WebAppInfo(url=WEBAPP_URL),
        )
    ]])
    await update.message.reply_photo(
        photo="https://i.imgur.com/placeholder.png",  # replace with your banner
        caption=(
            f"Привет, *{user.first_name}*\\! 👋\n\n"
            "Добро пожаловать в *Empire Showroom* — магазин премиальной одежды\\.\n\n"
            "Нажми кнопку ниже, чтобы открыть каталог:"
        ),
        parse_mode="MarkdownV2",
        reply_markup=keyboard,
    )


# ── /catalog ────────────────────────────────────────────
async def catalog(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "👔  ОДЕЖДА",    callback_data="cat:clothes"),
        InlineKeyboardButton(
            "👟  ОБУВЬ",     callback_data="cat:shoes"),
    ], [
        InlineKeyboardButton(
            "💼  АКСЕССУАРЫ", callback_data="cat:accessories"),
        InlineKeyboardButton(
            "🎁  СЕРТИФИКАТЫ", callback_data="cat:certificates"),
    ], [
        InlineKeyboardButton(
            "🔥  SALE",      callback_data="cat:sale"),
        InlineKeyboardButton(
            "🏪  Marketplace", callback_data="cat:marketplace"),
    ], [
        InlineKeyboardButton(
            "🛍  Открыть Mini App",
            web_app=WebAppInfo(url=WEBAPP_URL),
        ),
    ]])
    await update.message.reply_text(
        "📦 *Каталог Empire Showroom*\n\nВыберите категорию:",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


# ── /cart ────────────────────────────────────────────────
async def cart_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "🛍  Перейти в корзину",
            web_app=WebAppInfo(url=WEBAPP_URL + "#cart"),
        )
    ]])
    await update.message.reply_text(
        "🛒 Ваша корзина доступна в Mini App:",
        reply_markup=keyboard,
    )


# ── /help ────────────────────────────────────────────────
async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *Команды Empire Showroom*\n\n"
        "/start — Главное меню\n"
        "/catalog — Каталог товаров\n"
        "/cart — Корзина\n"
        "/help — Помощь\n\n"
        "По вопросам: @empire_support",
        parse_mode="Markdown",
    )


# ── CATEGORY CALLBACKS ──────────────────────────────────
CATEGORY_NAMES = {
    "clothes":      "👔 Одежда",
    "shoes":        "👟 Обувь",
    "accessories":  "💼 Аксессуары",
    "certificates": "🎁 Сертификаты",
    "sale":         "🔥 SALE",
    "marketplace":  "🏪 Marketplace",
}

async def category_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data.split(":")[1]
    name = CATEGORY_NAMES.get(cat, cat)
    url = WEBAPP_URL + f"?tab={cat}"
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(f"Открыть {name}", web_app=WebAppInfo(url=url))
    ], [
        InlineKeyboardButton("⬅️ Назад", callback_data="back:catalog")
    ]])
    await query.edit_message_text(
        f"Категория: *{name}*\n\nОткройте Mini App для просмотра товаров:",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def back_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dest = query.data.split(":")[1]
    if dest == "catalog":
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("👔 ОДЕЖДА",    callback_data="cat:clothes"),
            InlineKeyboardButton("👟 ОБУВЬ",     callback_data="cat:shoes"),
        ], [
            InlineKeyboardButton("💼 АКСЕССУАРЫ", callback_data="cat:accessories"),
            InlineKeyboardButton("🎁 СЕРТИФИКАТЫ", callback_data="cat:certificates"),
        ], [
            InlineKeyboardButton("🔥 SALE",      callback_data="cat:sale"),
            InlineKeyboardButton("🏪 Marketplace", callback_data="cat:marketplace"),
        ], [
            InlineKeyboardButton("🛍 Открыть Mini App", web_app=WebAppInfo(url=WEBAPP_URL)),
        ]])
        await query.edit_message_text(
            "📦 *Каталог Empire Showroom*\n\nВыберите категорию:",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


# ── WEB APP DATA (order from Mini App) ──────────────────
async def webapp_data(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Receives checkout data sent via Telegram.WebApp.sendData()"""
    data_str = update.effective_message.web_app_data.data
    try:
        data = json.loads(data_str)
    except json.JSONDecodeError:
        await update.message.reply_text("Ошибка обработки заказа.")
        return

    if data.get("action") == "checkout":
        items = data.get("items", [])
        total = data.get("total", 0)

        lines = []
        for it in items:
            size_str = f" (р. {it['size']})" if it.get("size") else ""
            lines.append(
                f"• *{it['brand']}* — {it['name']}{size_str}\n"
                f"  {it['qty']} шт × {it['price']:,} ₽"
            )

        order_text = (
            "🛍 *Новый заказ!*\n\n"
            + "\n".join(lines)
            + f"\n\n💰 *Итого: {total:,} ₽*\n\n"
            "Наш менеджер свяжется с вами в ближайшее время."
        )

        # Send to customer
        await update.message.reply_text(order_text, parse_mode="Markdown")

        # TODO: forward to admin channel
        # await ctx.bot.send_message(ADMIN_CHAT_ID, order_text, parse_mode="Markdown")


# ── MAIN ────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("catalog", catalog))
    app.add_handler(CommandHandler("cart",    cart_cmd))
    app.add_handler(CommandHandler("help",    help_cmd))
    app.add_handler(CallbackQueryHandler(category_callback, pattern=r"^cat:"))
    app.add_handler(CallbackQueryHandler(back_callback,     pattern=r"^back:"))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data))

    logger.info("Empire Showroom bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
