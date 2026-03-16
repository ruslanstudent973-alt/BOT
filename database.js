const Database = require('better-sqlite3');
const db = new Database('shop.db');

function initDb() {
    db.prepare(`
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id TEXT,
            media_type TEXT,
            name TEXT,
            description TEXT,
            price REAL
        )
    `).run();

    db.prepare(`
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    `).run();

    db.prepare(`
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    `).run();
}

function setGroupId(groupId) {
    db.prepare("INSERT OR REPLACE INTO settings (key, value) VALUES ('group_id', ?)").run(groupId.toString());
}

function getGroupId() {
    const row = db.prepare("SELECT value FROM settings WHERE key = 'group_id'").get();
    return row ? parseInt(row.value) : null;
}

function addProduct(mediaId, mediaType, name, description, price) {
    db.prepare("INSERT INTO products (media_id, media_type, name, description, price) VALUES (?, ?, ?, ?, ?)")
      .run(mediaId, mediaType, name, description, price);
}

function getAllProducts() {
    return db.prepare("SELECT * FROM products").all();
}

function getRandomProduct() {
    return db.prepare("SELECT * FROM products ORDER BY RANDOM() LIMIT 1").get();
}

initDb();

module.exports = {
    setGroupId,
    getGroupId,
    addProduct,
    getAllProducts,
    getRandomProduct
};
