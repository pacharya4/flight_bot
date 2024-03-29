from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.keyboards import single_button

async def flight_search_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.user_data.clear()
    menu = single_button(text='🔎 New Flight Search',
                         callback_data='start_flight_search')
    await context.bot.send_message(chat_id=chat_id, text='🤖 Okie Dokes, Your flight search has been cleared.', reply_markup=menu, parse_mode=ParseMode.HTML)