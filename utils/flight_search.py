import requests
import config
from datetime import datetime
from telegram.constants import ParseMode 

from utils.keyboards import adults_menu, flight_result_menu, main_menu_redirect


def get_airports(location):
    """This function calls the location kiwi api and returns airport name and iata code"""

    header = {'apikey': config.KIWI_API_KEY}
    endpoint = 'https://api.tequila.kiwi.com/locations/query' 
    params = {
        'term': location,
        'location_types': 'airport'
    }
    try:
        response = requests.get(
            url=endpoint, params=params, headers=header)
        response.raise_for_status()
    except Exception as error:
        print(error)
        return 'Connection Error'
    else:
        data = response.json()
        results = data['results_retrieved']
        try:
            if results == 0:
                raise IndexError
            airports = []
            for i in range(results):
                airport = f'{data["locations"][i]["name"]}: {data["locations"][i]["code"]}'
                airports.append(airport)
        except IndexError:
            airports = None
            return airports
        else:
            return airports
        
def format_date(date):
    """This checks if the user has input the date in the correct format. 
    If not this function will try and format the date.
    Date format Day/Month/Year. """

    if '/' in date:
        try:
            date_obj = datetime.strptime(date, '%d/%m/%Y')
            formated_date = date_obj.strftime('%d/%m/%Y')
        except ValueError:
            return None
        else:
            return formated_date
    else:
        return None
    
def is_date_in_past(date):
    """This function will check date presence and return true if date is in the present or future and return false if it is in the past."""
    input_date = datetime.strptime(date, "%d/%m/%Y").date()
    today = datetime.today().date()
    if input_date > today:
        return True
    elif input_date == today:
        return True
    else:
        return False
        
def validate_number(number):
    """This function check if arg is a number and not a string number"""
    try:
        int(number)
        return True
    except ValueError:
        return False
    
def is_int_0(number):
    """This function check if the arg is == 0"""
    if int(number) == 0:
        return True
    else:
        return False
    
async def search_flights(user_data):
    """This function takes in a dict arg of all user data need to call api to search for flights.
    The function will also search and get the cheapest price. 
    Returns a list: price, destination and departure"""

    header = {'apikey': config.KIWI_API_KEY}
    endpoint = 'https://api.tequila.kiwi.com/v2/search'
    if user_data['flight_type'] == 'ONEWAY':
        params = {
            'fly_from': user_data['Departure Airport'],
            'fly_to': user_data['Destination Airport'],
            'date_from': user_data['Departure Date (Earliest)'],
            'date_to': user_data['Departure Date (Latest)'],
            'adults': user_data['How Many Adults'],
            'curr': user_data['currency'],
            'limit': 1000,
        }
    elif user_data['flight_type'] == 'RETURN':
        params = {
            'fly_from': user_data['Departure Airport'],
            'fly_to': user_data['Destination Airport'],
            'date_from': user_data['Departure Date (Earliest)'],
            'date_to': user_data['Departure Date (Latest)'],
            'nights_in_dst_from': user_data['Minimum Lenth Of Stay'],
            'nights_in_dst_to': user_data['Maximum Lenth Of Stay'],
            'adults': user_data['How Many Adults'],
            'curr': user_data['currency'],
            'limit': 1000,
        }

    try:
        response = requests.get(
            url=endpoint, headers=header, params=params)
        response.raise_for_status()
    except Exception as error:
        print(error)
        return False
    else:
        data = response.json()
        price_list = []
        data_len = len(data['data'])
        try:
            for i in range(data_len):
                price_list.append(data['data'][i]['price'])
            min_price = min(price_list)
            for i in range(data_len):
                if data['data'][i]['price'] == min_price:
                    link = data['data'][i]['deep_link']
                    destination = data['data'][i]['cityTo']
                    departure = data['data'][i]['cityFrom']
                result = [min_price, link, destination, departure, data_len]
        except (IndexError, ValueError):
            return None
        else:
            return result
        

async def next_step(update, context):
    """This Fuction iterates through the user data asks user for info if data is None
    This function will also iniate the flight search and provide the result to the user.
    """
    chat_id = update.effective_chat.id

    for key, value in context.user_data.items():
        if value == None:
            if key == 'Departure Airport':
                return await context.bot.send_message(chat_id=chat_id, text='🛫 Provide your departure city.')
            if key == 'Destination Airport':
                return await context.bot.send_message(chat_id=chat_id, text='🛬 Please provide your destination city.')
            if key == 'Departure Date (Earliest)':
                return await context.bot.send_message(chat_id=chat_id, text='📅 Please enter your earliest departure date. e.g Day/Month/Year')
            if key == 'Departure Date (Latest)':
                return await context.bot.send_message(chat_id=chat_id, text='📅 Please enter your latest departure date. e.g Day/Month/Year')
            if key == 'Minimum Lenth Of Stay':
                return await context.bot.send_message(chat_id=chat_id, text='🏨 Please enter your minimum length of stay.')
            if key == 'Maximum Lenth Of Stay':
                return await context.bot.send_message(chat_id=chat_id, text='🏨 Please enter your maximum length of stay.')
            if key == 'How Many Adults':
                possible_adults = adults_menu()
                return await context.bot.send_message(chat_id=chat_id, text='👪 How many adults?', reply_markup=possible_adults)
            

    if context.user_data['How Many Adults'] != None:
        await context.bot.send_message(chat_id=chat_id, text='🤖 Okay, give me a sec. Searching for flights... 🔎')
        result = await search_flights(user_data=context.user_data)
        if result == False:
            await context.bot.send_message(chat_id=chat_id, text='🤖 looks like something went wrong, sorry. Please try again later.', reply_markup=main_menu_redirect)
        elif result == None:
            await context.bot.send_message(chat_id=chat_id, text='🤖 Sorry, no flights found at this moment. Try again later.', reply_markup=main_menu_redirect)
        else:
            reply = f'<b>Cheapest Flight Found!</b>\n\n🔎 Searched through {result[4]} flight results.\n\n📍 <b>Fly From:</b> {result[3].capitalize()} To {result[2].capitalize()}\n\n❗<b>Flight Type:</b> {context.user_data["flight_type"]}\n\n💵 <b>Cheapest Price:</b> R{result[0]}\n\nTravel dates and airports may have changed! Click on the link below to view the exact dates, airports, and duration of travel. 👇'
            link = flight_result_menu(link=result[1])
            # Save link and price to temp data to access for other functions
            context.user_data['link'] = result[1]
            context.user_data['price'] = result[0]
            await context.bot.send_message(chat_id=chat_id, text=reply, reply_markup=link, parse_mode=ParseMode.HTML)


        
def calc_percentage(old_p, new_p):
    """This function takes two arguments old_p == old price and new_p == new price. This will calculate the percentage in the price drop"""
    percentage = ((old_p - new_p) / old_p) * 100
    if percentage < 1:
        return round(percentage, 2)
    else:
        return round(percentage)




