from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import config

def get_main_menu(is_admin=False):
    kb = [
        [KeyboardButton(text='🛍 Magazinga kirish', web_app=WebAppInfo(url="https://saytcha-seven.vercel.app/"))]
    ]
    if is_admin:
        kb.append([KeyboardButton(text='➕ Mahsulot qo\'shish'), KeyboardButton(text='📋 Mahsulotlar')])
        kb.append([KeyboardButton(text='📤 Hozir yuborish'), KeyboardButton(text='👨💻 Admin Panel')])
    
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_buy_inline(product_id):
    kb = [
        [InlineKeyboardButton(text='Sotib olaman', callback_data=f'buy_{product_id}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_contact_inline(user_id):
    kb = [
        [InlineKeyboardButton(text='👉 Aloqa qilish', url=f'tg://user?id={user_id}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_cargo_inline(product_id):
    kb = [
        [InlineKeyboardButton(text='🚀 2-8 kunlik (100g/14,000)', callback_data=f'cargo_{product_id}_fast')],
        [InlineKeyboardButton(text='🐢 12-15 kunlik (100g/10,000)', callback_data=f'cargo_{product_id}_slow')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_payment_inline(product_id, cargo_type):
    kb = [
        [InlineKeyboardButton(text='💳 50% oldindan to\'lov', callback_data=f'pay_{product_id}_{cargo_type}_50')],
        [InlineKeyboardButton(text='💰 100% to\'liq to\'lov', callback_data=f'pay_{product_id}_{cargo_type}_100')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_duration_inline():
    kb = [
        [
            InlineKeyboardButton(text='30 minut', callback_data='dur_30'),
            InlineKeyboardButton(text='1 soat', callback_data='dur_60')
        ],
        [
            InlineKeyboardButton(text='3 soat', callback_data='dur_180'),
            InlineKeyboardButton(text='6 soat', callback_data='dur_360')
        ],
        [
            InlineKeyboardButton(text='12 soat', callback_data='dur_720'),
            InlineKeyboardButton(text='24 soat', callback_data='dur_1440')
        ],
        [InlineKeyboardButton(text='O\'chirmaslik', callback_data='dur_0')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_admin_inline():
    kb = [
        [InlineKeyboardButton(text='Statistika', callback_data='admin_stats')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_phone_keyboard():
    kb = [
        [KeyboardButton(text='📱 Telefon raqamni yuborish', request_contact=True)]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)
