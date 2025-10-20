from pycoingecko import CoinGeckoAPI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import asyncio
import nest_asyncio

nest_asyncio.apply()

TOKEN = "8232458125:AAHfPvCj_nvRRy9Z9h8QYOaKC_oJJdeeYv4"
cg = CoinGeckoAPI()


def get_price(coin_id):
    data = cg.get_price(ids=coin_id, vs_currencies="usd")
    return data.get(coin_id, {}).get("usd", None)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("BTC", callback_data="bitcoin")],
        [InlineKeyboardButton("ETH", callback_data="ethereum")],
        [InlineKeyboardButton("SOL", callback_data="solana")],
        [InlineKeyboardButton("USDT", callback_data="tether")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose a coin 👇", reply_markup=reply_markup)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chosen_coin = query.data
    context.user_data["chosen_coin"] = chosen_coin
    context.user_data["chat_id"] = query.message.chat_id

    price = get_price(chosen_coin)
    if price:
        await query.edit_message_text(
            text=f" selected {chosen_coin.capitalize()}.\n"
                 f" Current price: ${price}"
        )
    await query.message.reply_text(f"Enter your target price for {chosen_coin.capitalize()}:")
    context.user_data["waiting_for_price"] = True


async def watch_price(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.user_data.get("chat_id")
    chosen_coin = context.user_data.get("chosen_coin")
    target_price = context.user_data.get("target_price")

    if not (chat_id and chosen_coin and target_price):
        return  # not ready yet

    while True:
        price = get_price(chosen_coin)
        if price >= target_price:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"{chosen_coin.capitalize()} has reached target price of ${target_price}\nCurrent price: ${price}",
            )
            break
        await asyncio.sleep(30)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_for_price"):
        try:
            target_price = float(update.message.text)
            context.user_data["target_price"] = target_price
            chosen_coin = context.user_data.get("chosen_coin", "coin")

            await update.message.reply_text(
                f"✅ Target price for {chosen_coin.capitalize()} set to ${target_price}"
            )
            context.user_data["waiting_for_price"] = False

            asyncio.create_task(watch_price(context))

        except ValueError:
            await update.message.reply_text("Please enter a valid number.")
    else:
        return


# main
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(" Bot is running")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
