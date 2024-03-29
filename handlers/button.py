# THIS TEMPLATE DEFINES AND HANDLES THE CALLBACK QUERIES FROM ANY INLINE KEYBOARD
# CALLBACKQUERY HANDLER

from telegram import Update
from telegram.ext import ContextTypes
import config
from utils.flight_search import next_step
from utils.decoraters import check_save_alert_limit
from utils.database import DB

# HANDLER IMPORTS
from handlers.flight_alerts import flight_alerts

# KEY BOARD IMPORTS
from utils.keyboards import flight_type_menu, main_menu, flight_result_menu, delete_all_menu


@check_save_alert_limit
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    callback = update.callback_query
    await callback.answer()
    callback_data = callback.data
    chat_id = update.effective_chat.id
    first_name = update.effective_chat.first_name
    last_name = update.effective_chat.last_name
    username = update.effective_chat.username

    match callback_data:
        case 'start_flight_search':
            context.user_data.clear()
            context.user_data['Departure Airport'] = None
            context.user_data['Destination Airport'] = None
            context.user_data['Departure Date (Earliest)'] = None
            context.user_data['Departure Date (Latest)'] = None
            context.user_data['Minimum Lenth Of Stay'] = None
            context.user_data['Maximum Lenth Of Stay'] = None
            context.user_data['How Many Adults'] = None
            context.user_data['currency'] = 'ZAR'
            context.user_data['flight_type'] = None
            await context.bot.send_message(chat_id=chat_id, reply_markup=flight_type_menu, text='🤖 Please select option 👇')
        case 'oneway' | 'return':
            # sends option on flight search type
            # This will delete the inline keyboard after user has clicked on option
            current_menu = callback
            await current_menu.delete_message()

            if callback_data == 'oneway':
                context.user_data['flight_type'] = 'ONEWAY'
                context.user_data['Minimum Lenth Of Stay'] = 'VOID'
                context.user_data['Maximum Lenth Of Stay'] = 'VOID'
                await next_step(update=update, context=context)
            elif callback_data == 'return':
                context.user_data['flight_type'] = 'RETURN'
                await next_step(update=update, context=context)
        case 'main_menu':
            await context.bot.send_message(chat_id=chat_id, text='What can I do for you', reply_markup=main_menu)
        case 'track_flight':
            if 'link' in context.user_data:
                db = DB(file=config.DATABASE_PATH)

                menu = flight_result_menu(link=context.user_data['link'], tracked=True)

                Departure_Airport = context.user_data['Departure Airport']
                Destination_Airport = context.user_data['Destination Airport']
                Departure_Date_Earliest = context.user_data['Departure Date (Earliest)']
                Departure_Date_Latest = context.user_data['Departure Date (Latest)']
                Minimum_Lenth_Of_Stay = context.user_data['Minimum Lenth Of Stay']
                Maximum_Lenth_Of_Stay = context.user_data['Maximum Lenth Of Stay']
                How_Many_Adults = context.user_data['How Many Adults']
                currency = context.user_data['currency']
                flight_type = context.user_data['flight_type']
                price = context.user_data['price']


                user = db.cursor.execute("SELECT * FROM users WHERE chat_id= ?", (chat_id,)).fetchone()
                if user != None:
                    db.add_flight_data(chat_id=chat_id, fly_from=Departure_Airport, fly_to=Destination_Airport, date_from=Departure_Date_Earliest, date_to=Departure_Date_Latest,
                                       nights_from=Minimum_Lenth_Of_Stay, nights_to=Maximum_Lenth_Of_Stay, adults=How_Many_Adults, curr=currency, flight_type=flight_type, current_price=price)
                    db.close()
                    await callback.edit_message_reply_markup(reply_markup=menu)
                else:
                    db.add_user(chat_id=chat_id, username=username,
                                first_name=first_name, last_name=last_name)
                    db.add_flight_data(chat_id=chat_id, fly_from=Departure_Airport, fly_to=Destination_Airport, date_from=Departure_Date_Earliest, date_to=Departure_Date_Latest,
                                       nights_from=Minimum_Lenth_Of_Stay, nights_to=Maximum_Lenth_Of_Stay, adults=How_Many_Adults, curr=currency, flight_type=flight_type, current_price=price)
                    db.close()
                    await callback.edit_message_reply_markup(reply_markup=menu)
            else:
                menu = flight_result_menu(link=None, err=True)
                await callback.edit_message_reply_markup(reply_markup=menu)
        case 'get_flight_alerts':
            await flight_alerts(update, context)
        case 'del_all_FA':
            db = DB(file=config.DATABASE_PATH)
            db.del_all_flight_data(chat_id=chat_id)
            db.close()
            menu = delete_all_menu(success=True)
            await callback.edit_message_text(text='You have no flight alerts yet. Start a flight search and create a new flight alert.', reply_markup=menu)
