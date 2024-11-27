import telebot
import requests
from telebot import types
from telebot.types import InlineKeyboardButton,InlineKeyboardMarkup

bot = telebot.TeleBot("7565834235:AAErYbmri3B2YhdA4rHWCqVwxdPA59sV6kk")
API_URL = 'https://shrustamovna.uz/api'  # Django API endpoint

user_registration_state = {}
user_payment_requests = {}
@bot.message_handler(commands=['start'])
def start(message):
    telegram_id = message.from_user.id
    referrer_id = None

    # Check if the user came through a referral link
    if len(message.text.split()) > 1:
        referrer_id = message.text.split()[1]

    # Check if the user is already registered
    response = requests.get(f"{API_URL}/users/{telegram_id}/")
    if response.status_code == 404:  # User is not registered
        bot.send_message(
            message.chat.id,
            "Assalomu alaykum!\n\nKeling, hammasini boshlashdan oldin tanishib olaylik.\n\nIsmingizni yozing:"
        )
        user_registration_state[telegram_id] = {"step": "first_name", "referrer_id": referrer_id}
    else:  # User exists
        user_data = response.json()
        first_name = user_data.get('first_name', '')  # Retrieve the first name

        # Check the user's referral count
        referral_response = requests.get(f"{API_URL}/user-referral/{telegram_id}/")
        if referral_response.status_code == 200:
            referral_data = referral_response.json()
            referral_count = referral_data.get('referral_count', 0)

            if referral_count >= 20:
                markup = InlineKeyboardMarkup()
                channel_markup = InlineKeyboardMarkup()
                button = types.InlineKeyboardButton(text="Guruhga qo'shilish", url="https://t.me/+1lvkRjiuQilkYzM6")
                markup.add(button)
                channel = InlineKeyboardButton(text="Kitobni qo'lga kiritish", callback_data="get_book")
                channel_markup.add(channel)
                bot.send_message(
                    message.chat.id,
                    f"🎉 Tabriklaymiz, {first_name}!\n\nSizning referal linkingiz orqali 20 ta foydalanuvchi ro'yxatdan o'tdi. Siz vazifani bajardingiz! 👏\n\nPastagi 'Guruhga qo'shilish' tugmasini bosib guruhga qo'shiling",
                    reply_markup=markup
                )
                bot.send_message(
                    message.chat.id,
                    f"Sizga yana bir sirli sovg'am bor🤫🎁Sovg'ani olish uchun ushbu kanalga a'zo bo'ling.",
                    reply_markup=channel_markup
                )
                return

        # Check payment status
        payment_response = requests.get(f"{API_URL}/payments/{telegram_id}/")
        if payment_response.status_code == 200:
            payment_data = payment_response.json()
            if payment_data['is_confirmed']:
                markup = types.InlineKeyboardMarkup()
                button = types.InlineKeyboardButton(text="Adminga yozish", url="https://t.me/shrustamovna_menejerr")
                markup.add(button)
                channel_markup = InlineKeyboardMarkup()
                channel = InlineKeyboardButton(text="Kitobni qo'lga kiritish", callback_data="get_book")
                channel_markup.add(channel)
                bot.send_message(
                    message.chat.id,
                    "Siz to'lov qilib ro'yxatdan o'tgansiz. Agar yordam kerak bo'lsa, adminga yozing.",
                    reply_markup=markup
                )
                bot.send_message(
                    message.chat.id,
                    f"Sizga yana bir sirli sovg'am bor🤫🎁Sovg'ani olish uchun ushbu kanalga a'zo bo'ling.",
                    reply_markup=channel_markup
                )
            else:
                markup = types.InlineKeyboardMarkup()
                button = types.InlineKeyboardButton(text="Adminga yozish", url="https://t.me/shrustamovna_menejerr")
                markup.add(button)
                bot.send_message(
                    message.chat.id,
                    "To'lov qilgansiz. Tasdiqlanishini kuting!",
                    reply_markup=markup
                )
        else:
            # User is registered but hasn't paid
            send_invite_button(message, first_name)

@bot.callback_query_handler(func=lambda call: call.data == "get_book")
def handle_get_book(call):
    telegram_id = call.from_user.id
    channel_id = -1001631066521  # Kanal ID (kanalning to'g'ri ID sini ishlating)
    book_channel_id = -1002481236498
    message_id = 4  # Kanaldagi yuborilayotgan xabar ID'si

    try:
        # Kanalga a'zo ekanligini tekshirish
        member = bot.get_chat_member(chat_id=channel_id, user_id=telegram_id)

        # Foydalanuvchining statusini tekshirish
        if member.status in ["member", "administrator", "creator"]:
            # Foydalanuvchi kanalga a'zo
            bot.copy_message(
                chat_id=call.message.chat.id,  # Foydalanuvchiga xabar yuborish
                from_chat_id=book_channel_id,  # Kanal ID
                message_id=message_id  # Kanaldagi xabar ID
            )
        else:
            markup = InlineKeyboardMarkup()
            button = InlineKeyboardButton(text="Kanalga qo'shilish", url="https://t.me/YellowIncOfficial")
            markup.add(button)
            bot.send_message(
                call.message.chat.id,
                "❌ Siz kanalga a'zo emassiz. Kitobni olish uchun avval kanalga a'zo bo'ling",
                parse_mode="Markdown",
                reply_markup=markup
            )
    except Exception as e:
        # Xatolik yuz berganda foydalanuvchini ogohlantirish
        print(f"Xatolik: {e}")  # Debug maqsadida konsolga xatoni chiqarish
        bot.send_message(
            call.message.chat.id,
            "⚠️ Kanalga a'zo bo'lishni tekshirishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring."
        )

@bot.message_handler(content_types=["document"])
def log_message(message):
    print(message)


def send_payment_prompt(message, first_name=""):
    bot.send_message(message.chat.id, f"{first_name}, iltimos, to'lovni amalga oshiring.")


@bot.message_handler(func=lambda message: message.from_user.id in user_registration_state)
def registration_handler(message):
    telegram_id = message.from_user.id
    state = user_registration_state[telegram_id]

    if state["step"] == "first_name":
        user_registration_state[telegram_id]["first_name"] = message.text
        
        # Telefon raqamni so'rash
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        phone_button = types.KeyboardButton(text="Telefon raqamni ulashish 📞", request_contact=True)
        markup.add(phone_button)
        bot.send_message(message.chat.id, "Telefon raqamingizni ulashing:", reply_markup=markup)
        
        state["step"] = "phone"

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    telegram_id = message.from_user.id
    if telegram_id in user_registration_state and user_registration_state[telegram_id]["step"] == "phone":
        state = user_registration_state[telegram_id]
        contact = message.contact
        
        if contact.user_id == telegram_id:
            referrer_id = state.get("referrer_id")
            
            # Foydalanuvchini ro'yxatdan o'tkazish
            data = {
                'telegram_id': telegram_id,
                'first_name': state["first_name"],
                'phone': contact.phone_number,
                'username': message.from_user.username or '',
            }
            response = requests.post(f"{API_URL}/users/", json=data)

            if response.status_code == 201:
                # Referal qo'shish
                if referrer_id:
                    referral_data = {"referrer_id": referrer_id, "invited_id": telegram_id}
                    requests.post(f"{API_URL}/add-referral/", json=referral_data)

                first_name = data['first_name']
                bot.send_message(
                    message.chat.id,
                    f"{first_name}, 3 kunlik marafonda siz:\n\n"

                "-iHerb orqali vitamin va badlarni arzon narxda buyurtma qilishni;\n\n"
                "-programmaning o’zidan daromad ishlash yo’llari;\n\n"
                "-Amerika kargosi;\n\n"
                "-vitamin sotish orqali biznes boshlash yo’llari\n\n"

                "Hamda yana qo’shimcha bebaxo bilimlarni Marafon kanalimizga obuna bo’lib qo’lga kiritasiz🤗\n\n",
                reply_markup=types.ReplyKeyboardRemove()
                )
                send_invite_button(message, first_name)
            else:
                bot.send_message(message.chat.id, "Ro'yxatdan o'tishda xatolik yuz berdi. Qaytadan urinib ko'ring.")

            del user_registration_state[telegram_id]
        else:
            bot.send_message(message.chat.id, "Iltimos, o'zingizning telefon raqamingizni ulashing.")

# Send invite button
def send_invite_button(message, first_name):
    chat_id = message.chat.id
    channel_id = -1002481236498  # Kanalning to'liq IDsi (-100 bilan)

    # Inline tugmalar yaratish
    markup = InlineKeyboardMarkup()
    pay_button = InlineKeyboardButton("To'lov qilaman💸", callback_data="payer")
    invite_button = InlineKeyboardButton("Do'stlarni taklif qilaman👫", callback_data="show_referral_info")
    markup.add(invite_button)
    markup.add(pay_button)

    try:
        # Videolarni forward qilish yoki nusxa olish
        bot.copy_message(chat_id=chat_id, from_chat_id=channel_id, message_id=2)
        bot.copy_message(chat_id=chat_id, from_chat_id=channel_id, message_id=3)
    except Exception as e:
        bot.send_message(chat_id, f"Xato yuz berdi: {str(e)}")
        return

    # Tugmalar bilan xabar yuborish
    bot.send_message(chat_id, f"Salom {first_name}, quyidagi variantlardan birini tanlang:", reply_markup=markup)

# Show referral info
@bot.callback_query_handler(func=lambda call: call.data == "show_referral_info")
def show_referral_info(call):
    telegram_id = call.from_user.id
    referral_response = requests.get(f"{API_URL}/user-referral/{telegram_id}/")
    
    if referral_response.status_code == 200:
        referral_data = referral_response.json()
        referral_count = referral_data.get("referral_count", 0)
        invited_users = referral_data.get("invited_users", [])
        invited_list = "\n".join([f"- {u['first_name']} (@{u['username']})" for u in invited_users])
        invited_text = f"\nTaklif qilinganlar:\n{invited_list}" if invited_users else "Hozircha hech kimni taklif qilmagansiz."
        referral_link = f"https://t.me/{bot.get_me().username}?start={telegram_id}"

        caption = f"Salom yaxshimisz🙋‍♀️\n\nMan Shaxnoza Rustamovnaning ,,iHerb orqali daromad” marafonida qatnashib,\n\nO'zimizda qimmaat vitaminlarni aarzonga Amerikadan zakaz qilishni o'rganyapman.\n\nUshbu bilimlardan siz ham foydalanishizni xoxladim🤗va kanalga qo'shilvolishiz uchun link jo'natyapman. Bu link orqali botga qo'shilasiz va kanalga qabul qilinasiz.\n\nMana o'sha link:\n👇👇👇\n\n{referral_link}"

        with open('fon.jpg', 'rb') as image:
            send_safe_photo(call.message.chat.id, image, caption)

        bot.send_message(
            call.message.chat.id,
            f"Ushbu yuqoridagi xabarni nusxalab yaqinlaringizga jo’nating.\n\nQachonki 20 ta odam kanalga qo'shilsa, sizga ,,iHerb orqali daromad” marafonimizga dostup beriladi🤗\n\n\n✅Sizdan nechta odam qo’shilganini bilish uchun /start tugmasini bosing✅\n\nTaklif qilgan do‘stlaringiz soni: {referral_count}\n\n"
            f"{invited_text}"
        )
    else:
        bot.send_message(call.message.chat.id, "Referal ma'lumotlarini olishda xatolik yuz berdi.")
def send_safe_message(chat_id, text, reply_markup=None):
    try:
        bot.send_message(chat_id, text, reply_markup=reply_markup)
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 403:
            print(f"Error: User {chat_id} has blocked the bot or is unavailable.")
        else:
            print(f"Error: {e}")

# Safe photo sending with 403 error handling
def send_safe_photo(chat_id, photo, caption, reply_markup=None):
    try:
        bot.send_photo(chat_id, photo=photo, caption=caption, reply_markup=reply_markup)
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 403:
            print(f"Error: User {chat_id} has blocked the bot or is unavailable.")
        else:
            print(f"Error: {e}")

# Payment button callback
@bot.callback_query_handler(func=lambda call: call.data == 'payer')
def payer(call):
    first_name = call.from_user.first_name
    markup = InlineKeyboardMarkup()
    pay_button = InlineKeyboardButton(text="Chekni yuborish", callback_data='pay_chek')
    adminga_button = InlineKeyboardButton(text="Admin orqali", url="https://t.me/shrustamovna_menejerr")
    markup.add(pay_button)
    markup.add(adminga_button)

    send_safe_message(call.message.chat.id, f"{first_name} Risk qilishdan qo'rqmasligizdan xursandman.\n\nIHerb marafon darslarini boshlashiz uchun quyidagi karta raqamga 2$ o'tkazing.\n\nKarta raqam: 9860 1766 0290 8681\nNavruzova Shakhnoza\n\nTo'lovni amalga oshirganingizdan keyin, to'lov chekini pastdagi 'Chekni yuborish' tugmasini bosib shu yerga yuboring yoki 'Adminga yuboring' tugmasini bosib adminga yuboring!", reply_markup=markup)
    


# Callback for sending the receipt
# Callback for sending the receipt
@bot.callback_query_handler(func=lambda call: call.data == 'pay_chek')
def ask_for_receipt(call):
    user_id = call.from_user.id
    first_name = call.from_user.first_name

    # Enable receipt upload tracking
    user_payment_requests[user_id] = True

    send_safe_message(
        call.message.chat.id,
        f"To'lov chekini skreenshot qilib, shu yerga yuboring!👇\n\n{first_name}, 10 daqiqa ichida chekingizni tekshirib, Sizga IHerb marafoni uchun dostup beraman!\n\nIltimos, faqat haqiqiy chekni rasmini yuboring!"
    )

# Save and process the receipt
@bot.message_handler(content_types=['photo'])
def save_receipt(message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    if user_payment_requests.get(user_id, False):  # Check if the user is allowed to upload a receipt
        if message.photo:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            files = {'chek': ('receipt.jpg', downloaded_file, 'image/jpeg')}
            data = {'telegram_id': user_id}

            response = requests.post(f"{API_URL}/payments/{user_id}/", files=files, data=data)

            if response.status_code == 201:
                bot.send_message(
                    message.chat.id,
                    f"{first_name}, To'lovingizni tekshiruvda.🔍\n\nTez orada Chekni tekshirib, Sizga IHerb marafoni uchun Dostup ochib beraman!😊\n\n📌Botni yo'qotib qo'ymaslik uchun 'PIN' qilib qo'ying!"
                )
                user_payment_requests[user_id] = False  # Reset the state after successful upload
            else:
                bot.send_message(message.chat.id, "To'lovda xatolik yuz berdi. Iltimos, yana urinib ko'ring.")
        else:
            bot.send_message(message.chat.id, "Iltimos, faqat rasm yuboring.")
    else:
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton(text="Adminga yozish", url="https://t.me/shrustamovna_menejerr")
        markup.add(button)
        bot.send_message(
            message.chat.id,
            "Iltimos, faqat 'To'lov qilish' tugmasini bosganingizdan keyin rasm yuboring.\n\nMuammo bor bo'lsa adminga yozing",
            reply_markup=markup
        )

@bot.message_handler(func=lambda message: True)
def save_message(message):
    telegram_id = message.from_user.id
    data = {}
    files = None

    # Handling different message types
    if message.text:
        data = {'text': message.text}
    elif message.photo:
        # Handle photo message
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("photo.jpg", 'wb') as new_file:
            new_file.write(downloaded_file)
        files = {'image': open("photo.jpg", 'rb')}
    elif message.video:
        # Handle video message
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("video.mp4", 'wb') as new_file:
            new_file.write(downloaded_file)
        files = {'video': open("video.mp4", 'rb')}
    
    # Send the message data to Django API
    try:
        response = requests.post(f"{API_URL}/messages/{telegram_id}/", data=data, files=files)
        
        # Check for successful response
        if response.status_code == 201:
            bot.send_message(message.chat.id, "Xabaringiz yuborildi, admin javobini kuting.")
        else:
            bot.send_message(message.chat.id, "Xabarni yuborishda xatolik yuz berdi, iltimos qaytadan urinib ko'ring.")
    
    except Exception as e:
        # Handle any exceptions during the request
        bot.send_message(message.chat.id, "Xabarni yuborishda muammo yuz berdi.")
        print(e)
    
    finally:
        # Close files if opened
        if files:
            for file in files.values():
                file.close()


bot.polling()