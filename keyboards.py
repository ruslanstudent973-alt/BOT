from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu(is_admin=False):
    kb = [
        [KeyboardButton(text='🛍 Magazinga kirish')]
    ]
    if is_admin:
        kb.append([KeyboardButton(text='➕ Mahsulot qo\'shish'), KeyboardButton(text='📋 Mahsulotlar')])
        kb.append([KeyboardButton(text='📤 Hozir yuborish'), KeyboardButton(text='👨💻 Admin Panel')])
    
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_buy_inline(product_id):
    kb = [
        [InlineKeyboardButton(text='Sotib olish', callback_data=f'buy_{product_id}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_admin_inline():
    kb = [
        [InlineKeyboardButton(text='Statistika', callback_data='admin_stats')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
