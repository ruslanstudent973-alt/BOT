const { Markup } = require('telegraf');

function getMainMenu(isAdmin = false) {
    const buttons = [['🛍 Magazinga kirish']];
    if (isAdmin) {
        buttons.push(['➕ Mahsulot qo\'shish', '📋 Mahsulotlar']);
        buttons.push(['📤 Hozir yuborish', '👨💻 Admin Panel']);
    }
    return Markup.keyboard(buttons).resize();
}

function getBuyInline(productId) {
    return Markup.inlineKeyboard([
        Markup.button.callback('Sotib olish', `buy_${productId}`)
    ]);
}

function getAdminInline() {
    return Markup.inlineKeyboard([
        Markup.button.callback('Statistika', 'admin_stats')
    ]);
}

module.exports = {
    getMainMenu,
    getBuyInline,
    getAdminInline
};
