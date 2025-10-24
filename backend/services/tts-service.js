const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

class TTSService {
    constructor() {
        this.isInitialized = false;
        this.tempDir = './temp/audio';
        this.outputDir = './public/audio';
        this.ensureDirectories();
    }

    async initialize() {
        try {
            console.log('🔊 Initializing TTS Service...');
            
            // Check for available TTS engines
            await this.checkTTSEngines();
            
            this.isInitialized = true;
            console.log('✅ TTS Service initialized');
            
        } catch (error) {
            console.error('❌ TTS Service initialization failed:', error);
            throw error;
        }
    }

    async checkTTSEngines() {
        const engines = ['espeak', 'festival', 'pico2wave'];
        const availableEngines = [];

        for (const engine of engines) {
            try {
                await this.checkEngine(engine);
                availableEngines.push(engine);
            } catch (error) {
                console.warn(`⚠️ ${engine} not available`);
            }
        }

        if (availableEngines.length === 0) {
            throw new Error('No TTS engines available. Please install espeak, festival, or pico2wave');
        }

        console.log(`✅ Available TTS engines: ${availableEngines.join(', ')}`);
        this.availableEngines = availableEngines;
    }

    async checkEngine(engine) {
        return new Promise((resolve, reject) => {
            const process = spawn(engine, ['--help']);
            
            process.on('error', (error) => {
                reject(error);
            });
            
            process.on('close', (code) => {
                if (code === 0 || code === 1) { // Some engines return 1 for help
                    resolve();
                } else {
                    reject(new Error(`${engine} not found`));
                }
            });
        });
    }

    ensureDirectories() {
        [this.tempDir, this.outputDir].forEach(dir => {
            if (!fs.existsSync(dir)) {
                fs.mkdirSync(dir, { recursive: true });
            }
        });
    }

    async synthesizeSpeech(text, options = {}) {
        try {
            const {
                voice = 'default',
                speed = 1.0,
                pitch = 1.0,
                volume = 1.0,
                language = 'en-US',
                engine = this.availableEngines[0]
            } = options;

            const timestamp = Date.now();
            const filename = `speech_${timestamp}.wav`;
            const outputPath = path.join(this.outputDir, filename);

            let audioBuffer;

            switch (engine) {
                case 'espeak':
                    audioBuffer = await this.synthesizeWithEspeak(text, outputPath, {
                        voice, speed, pitch, volume, language
                    });
                    break;
                case 'festival':
                    audioBuffer = await this.synthesizeWithFestival(text, outputPath, {
                        voice, speed, pitch, volume, language
                    });
                    break;
                case 'pico2wave':
                    audioBuffer = await this.synthesizeWithPico2wave(text, outputPath, {
                        voice, speed, pitch, volume, language
                    });
                    break;
                default:
                    throw new Error(`Unsupported TTS engine: ${engine}`);
            }

            return {
                audioBuffer,
                filename,
                duration: await this.getAudioDuration(outputPath),
                engine,
                voice
            };

        } catch (error) {
            console.error('❌ TTS synthesis failed:', error);
            throw error;
        }
    }

    async synthesizeWithEspeak(text, outputPath, options) {
        return new Promise((resolve, reject) => {
            const args = [
                '-s', Math.round(150 * options.speed), // Speed in words per minute
                '-p', Math.round(50 * options.pitch), // Pitch (0-99)
                '-a', Math.round(200 * options.volume), // Amplitude (0-200)
                '-v', options.voice,
                '-w', outputPath,
                text
            ];

            const espeak = spawn('espeak', args);

            espeak.on('close', (code) => {
                if (code === 0) {
                    const audioBuffer = fs.readFileSync(outputPath);
                    resolve(audioBuffer);
                } else {
                    reject(new Error(`espeak failed with code ${code}`));
                }
            });

            espeak.on('error', (error) => {
                reject(error);
            });
        });
    }

    async synthesizeWithFestival(text, outputPath, options) {
        return new Promise((resolve, reject) => {
            const script = `
                (Parameter.set 'Duration_Stretch ${1 / options.speed})
                (Parameter.set 'Int_Target_Mean ${Math.round(100 * options.pitch)})
                (Parameter.set 'Int_Target_Std ${Math.round(20 * options.volume)})
                (tts_text "${text}" '${options.voice})
            `;

            const festival = spawn('festival', ['--tts', '--pipe']);

            festival.stdin.write(script);
            festival.stdin.end();

            const output = fs.createWriteStream(outputPath);
            festival.stdout.pipe(output);

            festival.on('close', (code) => {
                if (code === 0) {
                    const audioBuffer = fs.readFileSync(outputPath);
                    resolve(audioBuffer);
                } else {
                    reject(new Error(`festival failed with code ${code}`));
                }
            });

            festival.on('error', (error) => {
                reject(error);
            });
        });
    }

    async synthesizeWithPico2wave(text, outputPath, options) {
        return new Promise((resolve, reject) => {
            const args = [
                '-l', options.language,
                '-w', outputPath,
                text
            ];

            const pico2wave = spawn('pico2wave', args);

            pico2wave.on('close', (code) => {
                if (code === 0) {
                    const audioBuffer = fs.readFileSync(outputPath);
                    resolve(audioBuffer);
                } else {
                    reject(new Error(`pico2wave failed with code ${code}`));
                }
            });

            pico2wave.on('error', (error) => {
                reject(error);
            });
        });
    }

    // Alternative: Use cloud TTS services
    async synthesizeWithElevenLabs(text, options = {}) {
        const { voice = 'pNInz6obpgDQGcFmaJgB', apiKey = process.env.ELEVENLABS_API_KEY } = options;
        
        if (!apiKey) {
            throw new Error('ElevenLabs API key not provided');
        }

        try {
            const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voice}`, {
                method: 'POST',
                headers: {
                    'Accept': 'audio/mpeg',
                    'Content-Type': 'application/json',
                    'xi-api-key': apiKey
                },
                body: JSON.stringify({
                    text: text,
                    model_id: 'eleven_monolingual_v1',
                    voice_settings: {
                        stability: 0.5,
                        similarity_boost: 0.5
                    }
                })
            });

            if (!response.ok) {
                throw new Error(`ElevenLabs API error: ${response.statusText}`);
            }

            const audioBuffer = await response.arrayBuffer();
            return Buffer.from(audioBuffer);

        } catch (error) {
            console.error('❌ ElevenLabs TTS failed:', error);
            throw error;
        }
    }

    async synthesizeWithOpenAI(text, options = {}) {
        const { voice = 'alloy', apiKey = process.env.OPENAI_API_KEY } = options;
        
        if (!apiKey) {
            throw new Error('OpenAI API key not provided');
        }

        try {
            const response = await fetch('https://api.openai.com/v1/audio/speech', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: 'tts-1',
                    input: text,
                    voice: voice
                })
            });

            if (!response.ok) {
                throw new Error(`OpenAI TTS API error: ${response.statusText}`);
            }

            const audioBuffer = await response.arrayBuffer();
            return Buffer.from(audioBuffer);

        } catch (error) {
            console.error('❌ OpenAI TTS failed:', error);
            throw error;
        }
    }

    async getAudioDuration(filePath) {
        return new Promise((resolve, reject) => {
            const ffprobe = spawn('ffprobe', [
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                filePath
            ]);

            let duration = '';

            ffprobe.stdout.on('data', (data) => {
                duration += data.toString();
            });

            ffprobe.on('close', (code) => {
                if (code === 0) {
                    resolve(parseFloat(duration.trim()));
                } else {
                    resolve(0);
                }
            });

            ffprobe.on('error', (error) => {
                resolve(0);
            });
        });
    }

    // Get available voices for each engine
    async getAvailableVoices(engine = null) {
        const engines = engine ? [engine] : this.availableEngines;
        const voices = {};

        for (const eng of engines) {
            try {
                voices[eng] = await this.getEngineVoices(eng);
            } catch (error) {
                console.warn(`Failed to get voices for ${eng}:`, error.message);
            }
        }

        return voices;
    }

    async getEngineVoices(engine) {
        switch (engine) {
            case 'espeak':
                return await this.getEspeakVoices();
            case 'festival':
                return await this.getFestivalVoices();
            case 'pico2wave':
                return await this.getPico2waveVoices();
            default:
                return [];
        }
    }

    async getEspeakVoices() {
        return new Promise((resolve, reject) => {
            const espeak = spawn('espeak', ['--voices']);
            let output = '';

            espeak.stdout.on('data', (data) => {
                output += data.toString();
            });

            espeak.on('close', (code) => {
                if (code === 0) {
                    const voices = output.split('\n')
                        .filter(line => line.trim())
                        .map(line => {
                            const parts = line.trim().split(/\s+/);
                            return {
                                name: parts[0],
                                language: parts[1],
                                gender: parts[2]
                            };
                        });
                    resolve(voices);
                } else {
                    resolve([]);
                }
            });

            espeak.on('error', (error) => {
                resolve([]);
            });
        });
    }

    async getFestivalVoices() {
        return new Promise((resolve, reject) => {
            const festival = spawn('festival', ['--pipe']);
            
            festival.stdin.write('(voice.list)\n');
            festival.stdin.end();

            let output = '';
            festival.stdout.on('data', (data) => {
                output += data.toString();
            });

            festival.on('close', (code) => {
                const voices = output.match(/\([^)]+\)/g) || [];
                resolve(voices.map(voice => voice.replace(/[()]/g, '')));
            });

            festival.on('error', (error) => {
                resolve([]);
            });
        });
    }

    async getPico2waveVoices() {
        // pico2wave has limited voice options
        return [
            { name: 'default', language: 'en-US' },
            { name: 'en-US', language: 'en-US' },
            { name: 'en-GB', language: 'en-GB' }
        ];
    }

    getStatus() {
        return {
            initialized: this.isInitialized,
            availableEngines: this.availableEngines || [],
            tempDir: this.tempDir,
            outputDir: this.outputDir
        };
    }
}

module.exports = TTSService;
