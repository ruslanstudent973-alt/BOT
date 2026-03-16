from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu(is_admin=False):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('🛍 Magazinga kirish'))
    if is_admin:
        keyboard.add(KeyboardButton('➕ Mahsulot qo\'shish'), KeyboardButton('📋 Mahsulotlar'))
        keyboard.add(KeyboardButton('📤 Hozir yuborish'), KeyboardButton('👨💻 Admin Panel'))
    return keyboard

def get_buy_inline(product_id):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('Sotib olish', callback_data=f'buy_{product_id}'))
    return keyboard

def get_admin_inline():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton('Statistika', callback_data='admin_stats'))
    return keyboard
