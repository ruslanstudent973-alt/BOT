import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from flask import Flask
from threading import Thread

import config
import database
import keyboards

# Logging
logging.basicConfig(level=logging.INFO)

# Bot initialization
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=memory_storage if 'memory_storage' in locals() else storage)

# Flask for keeping the bot alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=3000)

# States
class AddProduct(StatesGroup):
    waiting_for_media = State()
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()

# Handlers
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    is_admin = message.from_user.id == config.ADMIN_ID
    await message.answer("Xush kelibsiz!", reply_markup=keyboards.get_main_menu(is_admin))

@dp.message_handler(commands=['setgroup'])
async def cmd_setgroup(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        return
    group_id = message.chat.id
    database.set_group_id(group_id)
    await message.answer(f"Guruh ID saqlandi: {group_id}")

@dp.message_handler(lambda message: message.text == '➕ Mahsulot qo\'shish')
async def add_product_start(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        return
    await AddProduct.waiting_for_media.set()
    await message.answer("Mahsulot uchun rasm yoki video yuboring:")

@dp.message_handler(state=AddProduct.waiting_for_media, content_types=['photo', 'video'])
async def process_media(message: types.Message, state: FSMContext):
    if message.photo:
        media_id = message.photo[-1].file_id
        media_type = 'photo'
    else:
        media_id = message.video.file_id
        media_type = 'video'
    
    await state.update_data(media_id=media_id, media_type=media_type)
    await AddProduct.next()
    await message.answer("Mahsulot nomini kiriting:")

@dp.message_handler(state=AddProduct.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await AddProduct.next()
    await message.answer("Mahsulot ta'rifini kiriting:")

@dp.message_handler(state=AddProduct.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await AddProduct.next()
    await message.answer("Mahsulot narxini kiriting (faqat son):")

@dp.message_handler(state=AddProduct.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
    except ValueError:
        await message.answer("Iltimos, narxni son ko'rinishida kiriting:")
        return

    data = await state.get_data()
    database.add_product(data['media_id'], data['media_type'], data['name'], data['description'], price)
    
    await state.finish()
    await message.answer("Mahsulot muvaffaqiyatli qo'shildi!", reply_markup=keyboards.get_main_menu(True))

@dp.message_handler(lambda message: message.text == '📋 Mahsulotlar')
async def list_products(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        return
    products = database.get_all_products()
    if not products:
        await message.answer("Hozircha mahsulotlar yo'q.")
        return
    
    for p in products:
        text = f"Nom: {p[3]}\nNarx: {p[5]} so'm\nTa'rif: {p[4]}"
        if p[2] == 'photo':
            await bot.send_photo(message.chat.id, p[1], caption=text)
        else:
            await bot.send_video(message.chat.id, p[1], caption=text)

@dp.message_handler(lambda message: message.text == '📤 Hozir yuborish')
async def send_to_group(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        return
    group_id = database.get_group_id()
    if not group_id:
        await message.answer("Guruh ID sozlanmagan! /setgroup buyrug'ini guruhda ishlating.")
        return
    
    product = database.get_random_product()
    if not product:
        await message.answer("Bazada mahsulotlar yo'q!")
        return
    
    text = f"🔥 YANGI MAHSULOT!\n\nNom: {product[3]}\nNarx: {product[5]} so'm\n\n{product[4]}"
    markup = keyboards.get_buy_inline(product[0])
    
    try:
        if product[2] == 'photo':
            await bot.send_photo(group_id, product[1], caption=text, reply_markup=markup)
        else:
            await bot.send_video(group_id, product[1], caption=text, reply_markup=markup)
        await message.answer("Mahsulot guruhga yuborildi!")
    except Exception as e:
        await message.answer(f"Xatolik: {str(e)}")

@dp.message_handler(lambda message: message.text == '🛍 Magazinga kirish')
async def enter_shop(message: types.Message):
    await message.answer("Magazinimizga xush kelibsiz! Mahsulotlarni ko'rish uchun pastdagi tugmalardan foydalaning.")

@dp.message_handler(lambda message: message.text == '👨💻 Admin Panel')
async def admin_panel(message: types.Message):
    if message.from_user.id == config.ADMIN_ID:
        await message.answer("Admin panelga xush kelibsiz!", reply_markup=keyboards.get_admin_inline())

@dp.callback_query_handler(lambda c: c.data.startswith('buy_'))
async def process_buy(callback_query: types.CallbackQuery):
    product_id = callback_query.data.split('_')[1]
    await bot.answer_callback_query(callback_query.id, text="Sotib olish so'rovi qabul qilindi!")
    await bot.send_message(callback_query.from_user.id, f"Siz {product_id}-raqamli mahsulotni sotib olishni tanladingiz. Tez orada operator bog'lanadi.")

if __name__ == '__main__':
    # Start Flask in a separate thread
    Thread(target=run_flask).start()
    # Start Bot
    executor.start_polling(dp, skip_updates=True)
