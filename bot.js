const { Telegraf, session, Scenes } = require('telegraf');
const express = require('express');
const config = require('./config');
const database = require('./database');
const keyboards = require('./keyboards');

const bot = new Telegraf(config.BOT_TOKEN);
const app = express();

// Flask equivalent in Node.js
app.get('/', (req, res) => res.send('Bot is running!'));
app.listen(3000, '0.0.0.0', () => console.log('Server running on port 3000'));

// Scenes for Product Addition
const addProductScene = new Scenes.WizardScene(
    'ADD_PRODUCT_SCENE',
    async (ctx) => {
        await ctx.reply("Mahsulot uchun rasm yoki video yuboring:");
        return ctx.wizard.next();
    },
    async (ctx) => {
        if (ctx.message.photo) {
            ctx.scene.state.media_id = ctx.message.photo[ctx.message.photo.length - 1].file_id;
            ctx.scene.state.media_type = 'photo';
        } else if (ctx.message.video) {
            ctx.scene.state.media_id = ctx.message.video.file_id;
            ctx.scene.state.media_type = 'video';
        } else {
            return ctx.reply("Iltimos, rasm yoki video yuboring:");
        }
        await ctx.reply("Mahsulot nomini kiriting:");
        return ctx.wizard.next();
    },
    async (ctx) => {
        ctx.scene.state.name = ctx.message.text;
        await ctx.reply("Mahsulot ta'rifini kiriting:");
        return ctx.wizard.next();
    },
    async (ctx) => {
        ctx.scene.state.description = ctx.message.text;
        await ctx.reply("Mahsulot narxini kiriting (faqat son):");
        return ctx.wizard.next();
    },
    async (ctx) => {
        const price = parseFloat(ctx.message.text);
        if (isNaN(price)) {
            return ctx.reply("Iltimos, narxni son ko'rinishida kiriting:");
        }
        const { media_id, media_type, name, description } = ctx.scene.state;
        database.addProduct(media_id, media_type, name, description, price);
        await ctx.reply("Mahsulot muvaffaqiyatli qo'shildi!", keyboards.getMainMenu(true));
        return ctx.scene.leave();
    }
);

const stage = new Scenes.Stage([addProductScene]);
bot.use(session());
bot.use(stage.middleware());

// Handlers
bot.start((ctx) => {
    const isAdmin = ctx.from.id === config.ADMIN_ID;
    ctx.reply("Xush kelibsiz!", keyboards.getMainMenu(isAdmin));
});

bot.command('setgroup', (ctx) => {
    if (ctx.from.id !== config.ADMIN_ID) return;
    const groupId = ctx.chat.id;
    database.setGroupId(groupId);
    ctx.reply(`Guruh ID saqlandi: ${groupId}`);
});

bot.hears('➕ Mahsulot qo\'shish', (ctx) => {
    if (ctx.from.id !== config.ADMIN_ID) return;
    ctx.scene.enter('ADD_PRODUCT_SCENE');
});

bot.hears('📋 Mahsulotlar', async (ctx) => {
    if (ctx.from.id !== config.ADMIN_ID) return;
    const products = database.getAllProducts();
    if (products.length === 0) return ctx.reply("Hozircha mahsulotlar yo'q.");
    
    for (const p of products) {
        const text = `Nom: ${p.name}\nNarx: ${p.price} so'm\nTa'rif: ${p.description}`;
        if (p.media_type === 'photo') {
            await ctx.replyWithPhoto(p.media_id, { caption: text });
        } else {
            await ctx.replyWithVideo(p.media_id, { caption: text });
        }
    }
});

bot.hears('📤 Hozir yuborish', async (ctx) => {
    if (ctx.from.id !== config.ADMIN_ID) return;
    const groupId = database.getGroupId();
    if (!groupId) return ctx.reply("Guruh ID sozlanmagan! /setgroup buyrug'ini guruhda ishlating.");
    
    const product = database.getRandomProduct();
    if (!product) return ctx.reply("Bazada mahsulotlar yo'q!");
    
    const text = `🔥 YANGI MAHSULOT!\n\nNom: ${product.name}\nNarx: ${product.price} so'm\n\n${product.description}`;
    const markup = keyboards.getBuyInline(product.id);
    
    try {
        if (product.media_type === 'photo') {
            await bot.telegram.sendPhoto(groupId, product.media_id, { caption: text, ...markup });
        } else {
            await bot.telegram.sendVideo(groupId, product.media_id, { caption: text, ...markup });
        }
        ctx.reply("Mahsulot guruhga yuborildi!");
    } catch (e) {
        ctx.reply(`Xatolik: ${e.message}`);
    }
});

bot.hears('🛍 Magazinga kirish', (ctx) => {
    ctx.reply("Magazinimizga xush kelibsiz! Mahsulotlarni ko'rish uchun pastdagi tugmalardan foydalaning.");
});

bot.hears('👨💻 Admin Panel', (ctx) => {
    if (ctx.from.id === config.ADMIN_ID) {
        ctx.reply("Admin panelga xush kelibsiz!", keyboards.getAdminInline());
    }
});

bot.action(/buy_(.+)/, async (ctx) => {
    const productId = ctx.match[1];
    await ctx.answerCbQuery("Sotib olish so'rovi qabul qilindi!");
    await ctx.reply(`Siz ${productId}-raqamli mahsulotni sotib olishni tanladingiz. Tez orada operator bog'lanadi.`);
});

bot.launch();

// Enable graceful stop
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
