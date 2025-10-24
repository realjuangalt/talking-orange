const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

class WhisperService {
    constructor() {
        this.isInitialized = false;
        this.modelPath = process.env.WHISPER_MODEL_PATH || './models/whisper';
        this.tempDir = './temp/audio';
        this.ensureTempDir();
    }

    async initialize() {
        try {
            console.log('🎤 Initializing Whisper Service...');
            
            // Check if Whisper is available
            await this.checkWhisperInstallation();
            
            this.isInitialized = true;
            console.log('✅ Whisper Service initialized');
            
        } catch (error) {
            console.error('❌ Whisper Service initialization failed:', error);
            throw error;
        }
    }

    async checkWhisperInstallation() {
        return new Promise((resolve, reject) => {
            const whisper = spawn('whisper', ['--help']);
            
            whisper.on('error', (error) => {
                console.warn('⚠️ Whisper not found in PATH. Using fallback method.');
                resolve(false);
            });
            
            whisper.on('close', (code) => {
                if (code === 0) {
                    console.log('✅ Whisper found in PATH');
                    resolve(true);
                } else {
                    console.warn('⚠️ Whisper not properly installed');
                    resolve(false);
                }
            });
        });
    }

    ensureTempDir() {
        if (!fs.existsSync(this.tempDir)) {
            fs.mkdirSync(this.tempDir, { recursive: true });
        }
    }

    async transcribeAudio(audioBuffer, options = {}) {
        try {
            const {
                language = 'en',
                model = 'base',
                format = 'wav'
            } = options;

            // Generate unique filename
            const timestamp = Date.now();
            const inputFile = path.join(this.tempDir, `input_${timestamp}.${format}`);
            const outputFile = path.join(this.tempDir, `output_${timestamp}.txt`);

            // Write audio buffer to file
            fs.writeFileSync(inputFile, audioBuffer);

            // Transcribe using Whisper
            const transcription = await this.runWhisperTranscription(inputFile, outputFile, {
                language,
                model
            });

            // Clean up temporary files
            this.cleanupFiles([inputFile, outputFile]);

            return {
                text: transcription,
                confidence: 0.9, // Whisper doesn't provide confidence scores directly
                language: language
            };

        } catch (error) {
            console.error('❌ Whisper transcription failed:', error);
            throw error;
        }
    }

    async runWhisperTranscription(inputFile, outputFile, options) {
        return new Promise((resolve, reject) => {
            const args = [
                inputFile,
                '--model', options.model,
                '--language', options.language,
                '--output_format', 'txt',
                '--output_dir', path.dirname(outputFile)
            ];

            const whisper = spawn('whisper', args);

            let stdout = '';
            let stderr = '';

            whisper.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            whisper.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            whisper.on('close', (code) => {
                if (code === 0) {
                    try {
                        // Read the output file
                        const transcription = fs.readFileSync(outputFile, 'utf8').trim();
                        resolve(transcription);
                    } catch (error) {
                        reject(new Error('Failed to read transcription output'));
                    }
                } else {
                    reject(new Error(`Whisper failed with code ${code}: ${stderr}`));
                }
            });

            whisper.on('error', (error) => {
                reject(error);
            });
        });
    }

    // Alternative method using OpenAI API (if Whisper CLI not available)
    async transcribeWithOpenAI(audioBuffer, options = {}) {
        const { language = 'en' } = options;
        
        try {
            // This would require OpenAI API key
            const response = await fetch('https://api.openai.com/v1/audio/transcriptions', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
                    'Content-Type': 'multipart/form-data'
                },
                body: this.createFormData(audioBuffer, language)
            });

            if (!response.ok) {
                throw new Error(`OpenAI API error: ${response.statusText}`);
            }

            const result = await response.json();
            return {
                text: result.text,
                confidence: 0.9,
                language: language
            };

        } catch (error) {
            console.error('❌ OpenAI Whisper API failed:', error);
            throw error;
        }
    }

    createFormData(audioBuffer, language) {
        const formData = new FormData();
        formData.append('file', new Blob([audioBuffer]), 'audio.wav');
        formData.append('model', 'whisper-1');
        formData.append('language', language);
        return formData;
    }

    // Fallback method using Web Speech API (client-side)
    getWebSpeechAPIFallback() {
        return `
        // Client-side fallback using Web Speech API
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';
            
            return new Promise((resolve, reject) => {
                recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    resolve({ text: transcript, confidence: event.results[0][0].confidence });
                };
                recognition.onerror = (event) => reject(event.error);
                recognition.start();
            });
        } else {
            throw new Error('Speech recognition not supported');
        }
        `;
    }

    cleanupFiles(files) {
        files.forEach(file => {
            try {
                if (fs.existsSync(file)) {
                    fs.unlinkSync(file);
                }
            } catch (error) {
                console.warn(`Failed to cleanup file ${file}:`, error.message);
            }
        });
    }

    // Get available models
    getAvailableModels() {
        return [
            'tiny', 'base', 'small', 'medium', 'large'
        ];
    }

    // Get supported languages
    getSupportedLanguages() {
        return [
            'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh'
        ];
    }

    getStatus() {
        return {
            initialized: this.isInitialized,
            tempDir: this.tempDir,
            modelPath: this.modelPath
        };
    }
}

module.exports = WhisperService;
