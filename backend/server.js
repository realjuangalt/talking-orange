const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const path = require('path');
const sqlite3 = require('sqlite3').verbose();
const multer = require('multer');
const QRCode = require('qrcode');
const WebSocket = require('ws');

// Import services
const WhisperService = require('./services/whisper-service');
const TTSService = require('./services/tts-service');
const LLMService = require('./services/llm-service');
const BitcoinContentService = require('./services/bitcoin-content-service');
const JarvisVoiceService = require('./services/jarvis-voice-service');

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize services
const whisperService = new WhisperService();
const ttsService = new TTSService();
const llmService = new LLMService();
const bitcoinContentService = new BitcoinContentService();
const jarvisVoiceService = new JarvisVoiceService();

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../frontend')));

// Database setup
const db = new sqlite3.Database('./database.sqlite', (err) => {
  if (err) {
    console.error('Error opening database:', err.message);
  } else {
    console.log('Connected to SQLite database');
    initializeDatabase();
  }
});

// Initialize database tables
function initializeDatabase() {
  db.serialize(() => {
    // Assets table for 3D models and animations
    db.run(`CREATE TABLE IF NOT EXISTS assets (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      type TEXT NOT NULL,
      path TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    // Bitcoin content table for responses
    db.run(`CREATE TABLE IF NOT EXISTS bitcoin_content (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      topic TEXT NOT NULL,
      content TEXT NOT NULL,
      keywords TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    // Analytics table for tracking usage
    db.run(`CREATE TABLE IF NOT EXISTS analytics (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      session_id TEXT,
      event_type TEXT,
      data TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    // Insert sample Bitcoin content
    const sampleContent = [
      {
        topic: 'introduction',
        content: 'Hello! I\'m the Talking Orange, your guide to Bitcoin! Bitcoin is digital money that works without banks or governments.',
        keywords: 'hello,hi,intro,what is bitcoin'
      },
      {
        topic: 'benefits',
        content: 'Bitcoin gives you financial freedom! You can send money anywhere in the world, anytime, without asking permission.',
        keywords: 'benefits,advantages,why bitcoin,freedom'
      },
      {
        topic: 'decentralization',
        content: 'Bitcoin is decentralized - no single person or company controls it. It\'s run by a network of computers worldwide.',
        keywords: 'decentralized,control,network,computers'
      }
    ];

    const stmt = db.prepare(`INSERT OR IGNORE INTO bitcoin_content (topic, content, keywords) VALUES (?, ?, ?)`);
    sampleContent.forEach(item => {
      stmt.run(item.topic, item.content, item.keywords);
    });
    stmt.finalize();
  });
}

// File upload configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + '-' + file.originalname);
  }
});
const upload = multer({ storage: storage });

// API Routes

// Serve 3D assets
app.get('/api/assets/:id', (req, res) => {
  const assetId = req.params.id;
  
  db.get('SELECT * FROM assets WHERE id = ?', [assetId], (err, row) => {
    if (err) {
      res.status(500).json({ error: 'Database error' });
    } else if (row) {
      res.json(row);
    } else {
      res.status(404).json({ error: 'Asset not found' });
    }
  });
});

// Get all assets
app.get('/api/assets', (req, res) => {
  db.all('SELECT * FROM assets', (err, rows) => {
    if (err) {
      res.status(500).json({ error: 'Database error' });
    } else {
      res.json(rows);
    }
  });
});

// Process speech input and return Bitcoin response
app.post('/api/speech/process', async (req, res) => {
  try {
    const { text, sessionId, audioData } = req.body;
    
    let userInput = text;
    
    // If audio data is provided, transcribe it first
    if (audioData && !text) {
      try {
        const audioBuffer = Buffer.from(audioData, 'base64');
        const transcription = await whisperService.transcribeAudio(audioBuffer);
        userInput = transcription.text;
      } catch (error) {
        console.error('Speech transcription failed:', error);
        return res.status(500).json({ error: 'Speech transcription failed' });
      }
    }
    
    if (!userInput) {
      return res.status(400).json({ error: 'No text or audio provided' });
    }

    // Generate response using Jarvis Voice Service (preferred), Bitcoin Content Service, or LLM fallback
    let llmResponse;
    try {
      llmResponse = await jarvisVoiceService.generateBitcoinResponse(userInput, {
        sessionId: sessionId || 'anonymous',
        bitcoinContext: true
      });
    } catch (error) {
      console.warn('Jarvis Voice Service failed, trying Bitcoin Content Service:', error.message);
      try {
        llmResponse = await bitcoinContentService.generateBitcoinResponse(userInput, {
          sessionId: sessionId || 'anonymous',
          bitcoinContext: true
        });
      } catch (error2) {
        console.warn('Bitcoin Content Service failed, falling back to LLM:', error2.message);
        llmResponse = await llmService.generateResponse(userInput, {
          sessionId: sessionId || 'anonymous',
          bitcoinContext: true
        });
      }
    }

    // Generate speech audio
    let audioUrl = null;
    try {
      const ttsResult = await ttsService.synthesizeSpeech(llmResponse.text, {
        voice: 'default',
        language: 'en-US'
      });
      
      // Save audio file and return URL
      const audioFilename = `speech_${Date.now()}.wav`;
      const audioPath = path.join(__dirname, '../public/audio', audioFilename);
      fs.writeFileSync(audioPath, ttsResult.audioBuffer);
      audioUrl = `/audio/${audioFilename}`;
      
    } catch (error) {
      console.error('TTS synthesis failed:', error);
      // Continue without audio
    }

    // Log analytics
    db.run('INSERT INTO analytics (session_id, event_type, data) VALUES (?, ?, ?)', 
      [sessionId || 'anonymous', 'speech_processed', JSON.stringify({ 
        input: userInput, 
        response: llmResponse.text,
        audioUrl: audioUrl
      })], 
      (err) => {
        if (err) console.error('Analytics error:', err);
      }
    );

    res.json({ 
      response: llmResponse.text,
      audioUrl: audioUrl,
      timestamp: new Date().toISOString(),
      model: llmResponse.model
    });
    
  } catch (error) {
    console.error('Speech processing error:', error);
    res.status(500).json({ error: 'Speech processing failed' });
  }
});

// Generate QR code
app.post('/api/qr/generate', (req, res) => {
  const { url, options = {} } = req.body;
  
  if (!url) {
    return res.status(400).json({ error: 'URL is required' });
  }

  QRCode.toDataURL(url, options, (err, qrCodeDataURL) => {
    if (err) {
      res.status(500).json({ error: 'QR code generation failed' });
    } else {
      res.json({ qrCode: qrCodeDataURL });
    }
  });
});

// Upload asset
app.post('/api/assets/upload', upload.single('asset'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }

  const { name, type } = req.body;
  const filePath = req.file.path;

  db.run('INSERT INTO assets (name, type, path) VALUES (?, ?, ?)', 
    [name, type, filePath], 
    function(err) {
      if (err) {
        res.status(500).json({ error: 'Database error' });
      } else {
        res.json({ 
          id: this.lastID, 
          name, 
          type, 
          path: filePath 
        });
      }
    }
  );
});

// Bitcoin content generation endpoint
app.post('/api/bitcoin/content', async (req, res) => {
  try {
    const { contentType, topic, difficulty, length } = req.body;
    
    const content = await bitcoinContentService.generateBitcoinContent(contentType, {
      topic: topic || 'general',
      difficulty: difficulty || 'beginner',
      length: length || 'short'
    });
    
    if (!content) {
      return res.status(500).json({ error: 'Content generation failed' });
    }
    
    res.json(content);
    
  } catch (error) {
    console.error('Bitcoin content generation error:', error);
    res.status(500).json({ error: 'Content generation failed' });
  }
});

// Analytics endpoint
app.post('/api/analytics', (req, res) => {
  const { sessionId, eventType, data } = req.body;
  
  db.run('INSERT INTO analytics (session_id, event_type, data) VALUES (?, ?, ?)', 
    [sessionId, eventType, JSON.stringify(data)], 
    (err) => {
      if (err) {
        res.status(500).json({ error: 'Analytics error' });
      } else {
        res.json({ success: true });
      }
    }
  );
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    timestamp: new Date().toISOString(),
    version: '1.0.0'
  });
});

// Serve frontend
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../frontend/index.html'));
});

// Initialize services and start server
async function startServer() {
  try {
    console.log('🔧 Initializing services...');
    
    // Initialize all services
    await whisperService.initialize();
    await ttsService.initialize();
    await llmService.initialize();
    await bitcoinContentService.initialize();
    await jarvisVoiceService.initialize();
    
    console.log('✅ All services initialized');
    
    // Start server
    app.listen(PORT, () => {
      console.log(`🚀 Talking Orange server running on http://localhost:${PORT}`);
      console.log(`📊 API endpoints available at http://localhost:${PORT}/api/`);
      console.log(`🎯 Frontend served at http://localhost:${PORT}/`);
      console.log(`🎤 Whisper: ${whisperService.getStatus().initialized ? '✅' : '❌'}`);
      console.log(`🔊 TTS: ${ttsService.getStatus().initialized ? '✅' : '❌'}`);
      console.log(`🤖 LLM: ${llmService.getStatus().initialized ? '✅' : '❌'}`);
      console.log(`₿ Bitcoin AI: ${bitcoinContentService.getStatus().initialized ? '✅' : '❌'}`);
      console.log(`🎭 Jarvis Voice: ${jarvisVoiceService.getStatus().initialized ? '✅' : '❌'}`);
    });
    
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

// Start the server
startServer();

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Shutting down server...');
  db.close((err) => {
    if (err) {
      console.error('Error closing database:', err.message);
    } else {
      console.log('Database connection closed.');
    }
    process.exit(0);
  });
});
