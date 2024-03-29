
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from utils.database import DB
from utils.flight_search import is_date_in_past, search_flights, calc_percentage
import config

# KEY BOARD IMPORTS
from utils.keyboards import flight_alert_menu, main_menu_redirect


async def flight_search_job(context: ContextTypes.DEFAULT_TYPE):
    """This function will add flight data in a job que and will check if the resulting price is lower
    than the current price. If true it will notify the user."""

    db = DB(file=config.DATABASE_PATH)

    flight_data = db.cursor.execute('SELECT * FROM flight_data').fetchall()

    if flight_data != []:
        for i in flight_data:
            if is_date_in_past(date=i[4]) and is_date_in_past(date=i[5]):
                user_flight_data = {
                    'Departure Airport': i[2],
                    'Destination Airport': i[3],
                    'Departure Date (Earliest)': i[4],
                    'Departure Date (Latest)': i[5],
                    'Minimum Lenth Of Stay': i[6],
                    'Maximum Lenth Of Stay': i[7],
                    'How Many Adults': i[8],
                    'currency': i[9],
                    'flight_type': i[10],
                }
                result = await search_flights(user_data=user_flight_data)
                if result == None or result == False:
                    continue
                else:
                    if result[0] < i[11]:
                        percentage = calc_percentage(
                            old_p=i[11], new_p=result[0])
                        db.update_flight_data(
                            id=i[0], price=result[0], data="current_price")
                        response = f'🔻<b>{percentage}% PRICE DROP ON YOUR FLIGHT ALERT</b>🔻\n\n<b>Your Price alert</b>:\n{i[2]}-{i[3]}\n{i[4]}-{i[5]}\n<b>Price</b>: R{i[11]}\n\n<b>PRICE DROPPED TO</b> R{result[0]}\n\nTravel dates and airports may have changed! Click on the link below to view the exact dates, airports, and duration of travel. 👇'
                        menu = flight_alert_menu(link=result[1])
                        await context.bot.send_message(chat_id=i[1], text=response, reply_markup=menu, parse_mode=ParseMode.HTML)
            else:
                # notify user that the dates in flight data is in the past and data will be deleted.
                response = f'❗<b>FLIGHT ALERT EXPIRED</b>❗\n\nThe flight alert bellow has expired and has been deleted.\n{i[2]}-{i[3]}\n{i[4]}-{i[5]}\n<b>Price</b>: {i[11]}'
                await context.bot.send_message(chat_id=i[1], text=response, reply_markup=main_menu_redirect, parse_mode=ParseMode.HTML)
                db.del_flight_data(id=i[0])
    else:
        db.close()

    # close db once for loop executes successfully
    db.close()





