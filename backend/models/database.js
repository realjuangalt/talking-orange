const sqlite3 = require('sqlite3').verbose();
const path = require('path');

class Database {
  constructor() {
    this.db = new sqlite3.Database('./database.sqlite', (err) => {
      if (err) {
        console.error('Error opening database:', err.message);
      } else {
        console.log('Connected to SQLite database');
        this.initializeTables();
      }
    });
  }

  initializeTables() {
    this.db.serialize(() => {
      // Assets table for 3D models and animations
      this.db.run(`CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        path TEXT NOT NULL,
        metadata TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )`);

      // Bitcoin content table for responses
      this.db.run(`CREATE TABLE IF NOT EXISTS bitcoin_content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL,
        content TEXT NOT NULL,
        keywords TEXT,
        priority INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )`);

      // Analytics table for tracking usage
      this.db.run(`CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        event_type TEXT,
        data TEXT,
        ip_address TEXT,
        user_agent TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )`);

      // Sessions table for tracking user sessions
      this.db.run(`CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
        data TEXT
      )`);
    });
  }

  // Asset methods
  getAsset(id) {
    return new Promise((resolve, reject) => {
      this.db.get('SELECT * FROM assets WHERE id = ?', [id], (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
  }

  getAllAssets() {
    return new Promise((resolve, reject) => {
      this.db.all('SELECT * FROM assets ORDER BY created_at DESC', (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });
  }

  addAsset(name, type, path, metadata = null) {
    return new Promise((resolve, reject) => {
      this.db.run('INSERT INTO assets (name, type, path, metadata) VALUES (?, ?, ?, ?)', 
        [name, type, path, JSON.stringify(metadata)], 
        function(err) {
          if (err) reject(err);
          else resolve({ id: this.lastID, name, type, path, metadata });
        }
      );
    });
  }

  // Bitcoin content methods
  getBitcoinContent(topic) {
    return new Promise((resolve, reject) => {
      this.db.get('SELECT * FROM bitcoin_content WHERE topic = ?', [topic], (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
  }

  searchBitcoinContent(keywords) {
    return new Promise((resolve, reject) => {
      const searchTerm = `%${keywords}%`;
      this.db.all('SELECT * FROM bitcoin_content WHERE keywords LIKE ? OR content LIKE ? ORDER BY priority DESC', 
        [searchTerm, searchTerm], (err, rows) => {
          if (err) reject(err);
          else resolve(rows);
        }
      );
    });
  }

  addBitcoinContent(topic, content, keywords, priority = 1) {
    return new Promise((resolve, reject) => {
      this.db.run('INSERT INTO bitcoin_content (topic, content, keywords, priority) VALUES (?, ?, ?, ?)', 
        [topic, content, keywords, priority], 
        function(err) {
          if (err) reject(err);
          else resolve({ id: this.lastID, topic, content, keywords, priority });
        }
      );
    });
  }

  // Analytics methods
  logEvent(sessionId, eventType, data, ipAddress = null, userAgent = null) {
    return new Promise((resolve, reject) => {
      this.db.run('INSERT INTO analytics (session_id, event_type, data, ip_address, user_agent) VALUES (?, ?, ?, ?, ?)', 
        [sessionId, eventType, JSON.stringify(data), ipAddress, userAgent], 
        function(err) {
          if (err) reject(err);
          else resolve({ id: this.lastID });
        }
      );
    });
  }

  getAnalytics(limit = 100) {
    return new Promise((resolve, reject) => {
      this.db.all('SELECT * FROM analytics ORDER BY created_at DESC LIMIT ?', [limit], (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      });
    });
  }

  // Session methods
  createSession(sessionId, data = null) {
    return new Promise((resolve, reject) => {
      this.db.run('INSERT OR REPLACE INTO sessions (id, data) VALUES (?, ?)', 
        [sessionId, JSON.stringify(data)], 
        function(err) {
          if (err) reject(err);
          else resolve({ id: sessionId });
        }
      );
    });
  }

  getSession(sessionId) {
    return new Promise((resolve, reject) => {
      this.db.get('SELECT * FROM sessions WHERE id = ?', [sessionId], (err, row) => {
        if (err) reject(err);
        else resolve(row);
      });
    });
  }

  updateSession(sessionId, data) {
    return new Promise((resolve, reject) => {
      this.db.run('UPDATE sessions SET data = ?, last_activity = CURRENT_TIMESTAMP WHERE id = ?', 
        [JSON.stringify(data), sessionId], 
        function(err) {
          if (err) reject(err);
          else resolve({ id: sessionId });
        }
      );
    });
  }

  close() {
    return new Promise((resolve, reject) => {
      this.db.close((err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }
}

module.exports = Database;
