import logging
import asyncio
import time
import aiohttp
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultPhoto, InlineQueryResultVideo
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import json
import os
from aiogram.types import InputMediaPhoto

import config
import database
import keyboards

# Logging
logging.basicConfig(level=logging.INFO)

# Bot initialization
if not config.BOT_TOKEN:
    logging.error("BOT_TOKEN is missing! Please set it in the platform settings.")
    # Don't exit immediately, let the Flask server run so the user can see the status
    bot = None
else:
    bot = Bot(token=config.BOT_TOKEN)

dp = Dispatcher(storage=MemoryStorage())

# Flask for keeping the bot alive (REPLACED BY AIOHTTP)
start_time = datetime.now()

async def handle_home(request):
    return web.Response(text="Bot is running", status=200)

async def handle_health(request):
    return web.Response(text="OK", status=200)

async def on_startup(bot: Bot):
    if config.APP_URL:
        webhook_url = f"{config.APP_URL}{config.WEBHOOK_PATH}"
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logging.info(f"Webhook set to: {webhook_url}")
    else:
        logging.warning("APP_URL not set! Falling back to Polling.")

# States
class AddProduct(StatesGroup):
    waiting_for_media = State()
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()

class SendProduct(StatesGroup):
    waiting_for_duration = State()

class Registration(StatesGroup):
    waiting_for_phone = State()
    waiting_for_address = State()

# Handlers
def get_product_text(product, is_sale=True):
    base_price = product[5]
    markup_price = base_price * 1.2
    
    if is_sale:
        price_text = (
            f"Narxlar:\n"
            f"🔴 <s>{markup_price:,.0f} so'm</s> — eski narx\n"
            f"🟢 {base_price:,.0f} so'm ✅ — sizga\n\n"
            f"🔥 Aksiya faqat belgilangan vaqt davom etadi!\n"
        )
    else:
        price_text = (
            f"Narx:\n"
            f"💰 {markup_price:,.0f} so'm\n\n"
            f"⚠️ Aksiya vaqti tugagan."
        )

    return (
        f"⚡️ FLASH SALE • #ID-{product[0]}\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"📦 {product[3]}\n\n"
        f"📝 {product[4]}\n\n"
        f"{price_text}"
        f"🔥 Ulguring — miqdor cheklangan!\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👇 Xarid qilish uchun quyidagi tugmani bosing:"
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user = database.get_user(user_id)
    
    if not user:
        await message.answer(
            "Xush kelibsiz! Botdan foydalanish uchun ro'yxatdan o'tishingiz kerak.\n"
            "Iltimos, telefon raqamingizni yuboring:",
            reply_markup=keyboards.get_phone_keyboard()
        )
        await state.set_state(Registration.waiting_for_phone)
        return

    is_admin = user_id == config.ADMIN_ID
    await message.answer(
        f"Xush kelibsiz, {user[3]}!", 
        reply_markup=keyboards.get_main_menu(is_admin)
    )

@dp.message(Registration.waiting_for_phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer(
        "Rahmat! Endi mahsulotlarni yetkazib berish uchun manzilingizni yuboring (masalan: Toshkent sh, Yunusobod tumani...):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(Registration.waiting_for_address)

@dp.message(Registration.waiting_for_phone)
async def process_phone_text(message: Message, state: FSMContext):
    if message.text and (message.text.startswith('+') or message.text.isdigit()):
        await state.update_data(phone=message.text)
        await message.answer(
            "Rahmat! Endi mahsulotlarni yetkazib berish uchun manzilingizni yuboring (masalan: Toshkent sh, Yunusobod tumani...):",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.set_state(Registration.waiting_for_address)
    else:
        await message.answer("Iltimos, pastdagi tugmani bosing yoki telefon raqamingizni to'g'ri formatda yuboring.")

@dp.message(Registration.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    
    database.add_user(user_id, data['phone'], message.text, full_name)
    
    await state.clear()
    is_admin = user_id == config.ADMIN_ID
    await message.answer(
        "Ro'yxatdan muvaffaqiyatli o'tdingiz! Endi magazinimizdan foydalanishingiz mumkin.",
        reply_markup=keyboards.get_main_menu(is_admin)
    )

@dp.message(Command("setgroup"))
async def cmd_setgroup(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        return
    group_id = message.chat.id
    database.set_group_id(group_id)
    await message.answer(f"Guruh ID saqlandi: {group_id}")

@dp.message(F.text == '➕ Mahsulot qo\'shish')
async def add_product_start(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        return
    await state.set_state(AddProduct.waiting_for_media)
    await message.answer("Mahsulot uchun rasm yoki video yuboring:")

@dp.message(AddProduct.waiting_for_media, F.photo | F.video)
async def process_media(message: types.Message, state: FSMContext):
    if message.photo:
        media_id = message.photo[-1].file_id
        media_type = 'photo'
    else:
        media_id = message.video.file_id
        media_type = 'video'
    
    await state.update_data(media_id=media_id, media_type=media_type)
    await state.set_state(AddProduct.waiting_for_name)
    await message.answer("Mahsulot nomini kiriting:")

@dp.message(AddProduct.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProduct.waiting_for_description)
    await message.answer("Mahsulot ta'rifini kiriting:")

@dp.message(AddProduct.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddProduct.waiting_for_price)
    await message.answer("Mahsulot narxini kiriting (faqat son):")

@dp.message(AddProduct.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
    except ValueError:
        await message.answer("Iltimos, narxni son ko'rinishida kiriting:")
        return

    data = await state.get_data()
    database.add_product(data['media_id'], data['media_type'], data['name'], data['description'], price)
    
    await state.clear()
    await message.answer("Mahsulot muvaffaqiyatli qo'shildi!", reply_markup=keyboards.get_main_menu(True))

@dp.inline_query()
async def inline_search(inline_query: InlineQuery):
    query = inline_query.query.lower()
    offset = int(inline_query.offset) if inline_query.offset else 0
    limit = 10  # Har bir sahifada 10 ta mahsulot
    
    all_products = database.get_all_products()
    filtered_products = [p for p in all_products if query in p[3].lower() or query in p[4].lower()]
    
    # Sahifalash uchun kesib olish
    paginated_products = filtered_products[offset : offset + limit]
    
    results = []
    for p in paginated_products:
        text = get_product_text(p, is_sale=False)
        markup = keyboards.get_buy_inline(p[0])
        
        if p[2] == 'photo':
            results.append(InlineQueryResultPhoto(
                id=str(p[0]),
                photo_url=p[1],
                thumbnail_url=p[1],
                caption=text,
                reply_markup=markup,
                parse_mode="HTML"
            ))
        else:
            results.append(InlineQueryResultVideo(
                id=str(p[0]),
                video_url=p[1],
                title=p[3],
                caption=text,
                reply_markup=markup,
                mime_type="video/mp4",
                parse_mode="HTML"
            ))
    
    # Keyingi sahifa bormi yoki yo'qligini aniqlash
    next_offset = str(offset + limit) if offset + limit < len(filtered_products) else ""
    
    await inline_query.answer(results, cache_time=1, next_offset=next_offset)

@dp.message(F.text == '📋 Mahsulotlar')
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

@dp.message(F.text == '📤 Hozir yuborish')
async def send_to_group_start(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        return
    group_id = database.get_group_id()
    if not group_id:
        await message.answer("Guruh ID sozlanmagan! /setgroup buyrug'ini guruhda ishlating.")
        return
    
    products = database.get_all_products()
    if not products:
        await message.answer("Bazada mahsulotlar yo'q!")
        return
    
    await message.answer("Mahsulot guruhda qancha vaqt tursin? (Vaqt tugagach o'chiriladi va pin'dan olinadi)", reply_markup=keyboards.get_duration_inline())

@dp.callback_query(F.data.startswith('dur_'))
async def process_duration(callback_query: types.CallbackQuery):
    duration_min = int(callback_query.data.split('_')[1])
    group_id = database.get_group_id()
    
    product = database.get_random_product()
    if not product:
        await callback_query.message.answer("Mahsulot topilmadi!")
        return

    text = get_product_text(product, is_sale=True)
    markup = keyboards.get_buy_inline(product[0])
    
    try:
        if product[2] == 'photo':
            msg = await bot.send_photo(group_id, product[1], caption=text, reply_markup=markup, parse_mode="HTML")
        else:
            msg = await bot.send_video(group_id, product[1], caption=text, reply_markup=markup, parse_mode="HTML")
        
        # Pin the message
        await bot.pin_chat_message(group_id, msg.message_id)
        
        await callback_query.message.edit_text(f"Mahsulot guruhga yuborildi va pin qilindi! {'O\'chirish vaqti: ' + str(duration_min) + ' minut' if duration_min > 0 else 'O\'chirilmaydi'}")
        
        if duration_min > 0:
            # Schedule update
            asyncio.create_task(update_later(group_id, msg.message_id, product[0], duration_min))
            
    except Exception as e:
        await callback_query.message.answer(f"Xatolik: {str(e)}")

async def update_later(chat_id, message_id, product_id, minutes):
    await asyncio.sleep(minutes * 60)
    try:
        product = database.get_product_by_id(product_id)
        if product:
            new_text = get_product_text(product, is_sale=False)
            await bot.edit_message_caption(chat_id, message_id, caption=new_text, reply_markup=keyboards.get_buy_inline(product_id), parse_mode="HTML")
        await bot.unpin_chat_message(chat_id, message_id)
    except Exception as e:
        logging.error(f"Error updating message: {e}")

@dp.message(F.text == '🛍 Magazinga kirish')
async def enter_shop(message: types.Message):
    await message.answer("Magazinimizga xush kelibsiz! Mahsulotlarni ko'rish uchun pastdagi tugmalardan foydaning.")

@dp.message(F.text == '👨💻 Admin Panel')
async def admin_panel(message: types.Message):
    if message.from_user.id == config.ADMIN_ID:
        await message.answer("Admin panelga xush kelibsiz!", reply_markup=keyboards.get_admin_inline())

@dp.callback_query(F.data == 'admin_stats')
async def admin_stats(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != config.ADMIN_ID:
        return
    
    products = database.get_all_products()
    uptime = datetime.now() - start_time
    
    text = (
        f"📊 BOT STATISTIKASI\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"📦 Mahsulotlar soni: {len(products)} ta\n"
        f"⏱ Bot ish vaqti: {str(uptime).split('.')[0]}\n"
        f"🌐 Server: Google Cloud (24/7 Online)\n"
    )
    await callback_query.message.answer(text)
    await callback_query.answer()

@dp.callback_query(F.data.startswith('buy_'))
async def process_buy(callback_query: types.CallbackQuery):
    product_id = int(callback_query.data.split('_')[1])
    await callback_query.message.answer("Kargo turini tanlang:", reply_markup=keyboards.get_cargo_inline(product_id))
    await callback_query.answer()

@dp.callback_query(F.data.startswith('cargo_'))
async def process_cargo(callback_query: types.CallbackQuery):
    data = callback_query.data.split('_')
    product_id = int(data[1])
    cargo_type = data[2]
    await callback_query.message.edit_text("To'lov turini tanlang:", reply_markup=keyboards.get_payment_inline(product_id, cargo_type))

@dp.callback_query(F.data.startswith('pay_'))
async def process_payment(callback_query: types.CallbackQuery):
    data = callback_query.data.split('_')
    product_id = int(data[1])
    cargo_type = data[2]
    pay_type = data[3]
    
    product = database.get_product_by_id(product_id)
    user_tg = callback_query.from_user
    user_db = database.get_user(user_tg.id)
    
    cargo_name = "🚀 2-8 kunlik (Fast)" if cargo_type == "fast" else "🐢 12-15 kunlik (Slow)"
    pay_name = "💳 50% oldindan" if pay_type == "50" else "💰 100% to'liq"
    
    # Notify User
    await callback_query.message.edit_text("✅ Buyurtmangiz qabul qilindi! Admin tez orada bog'lanadi.")
    
    # Notify Admin
    phone = user_db[1] if user_db else "Mavjud emas"
    address = user_db[2] if user_db else "Mavjud emas"
    
    admin_text = (
        f"🛒 YANGI BUYURTMA!\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"👤 Xaridor: {user_tg.full_name}\n"
        f"📱 Username: @{user_tg.username if user_tg.username else 'Mavjud emas'}\n"
        f"🆔 Telegram ID: {user_tg.id}\n"
        f"📞 Telefon: {phone}\n"
        f"📍 Manzil: {address}\n\n"
        f"📦 Mahsulot: {product[3]}\n"
        f"💰 Narx: {product[5]:,.0f} so'm\n"
        f"🚚 Kargo: {cargo_name}\n"
        f"💳 To'lov: {pay_name}\n\n"
        f"💬 Xaridorga yozish:"
    )
    
    await bot.send_message(
        config.ADMIN_ID, 
        admin_text, 
        reply_markup=keyboards.get_contact_inline(user.id)
    )
    await callback_query.answer()

async def main():
    if not bot:
        logging.error("Bot cannot start because BOT_TOKEN is missing!")
        return
            
    # Create aiohttp application
    app = web.Application()
    app.router.add_get('/', handle_home)
    app.router.add_get('/health', handle_health)
    
    # Start web server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 3000)
    await site.start()
    logging.info("Web server started on port 3000")

    if config.APP_URL:
        logging.info("Setting up Webhook...")
        dp.startup.register(on_startup)
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot
        )
        webhook_requests_handler.register(app, path=config.WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        
        # Webhook rejimida botni ushlab turish
        while True:
            await asyncio.sleep(3600)
    else:
        logging.warning("APP_URL not set! Falling back to Polling mode.")
        logging.info("Starting Polling...")
        await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
