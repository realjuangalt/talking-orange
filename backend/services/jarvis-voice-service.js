const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

class JarvisVoiceService {
    constructor() {
        this.isInitialized = false;
        this.genDir = path.join(__dirname, '../../gen');
        this.pythonPath = process.env.PYTHON_PATH || 'python3';
        this.veniceApiKey = process.env.VENICE_KEY;
        this.whisperModel = process.env.WHISPER_MODEL_NAME || 'small';
        this.modelDir = process.env.MODEL_DIR || '/opt/jarvis_editor/2.0/models';
    }

    async initialize() {
        try {
            console.log('🎤 Initializing Jarvis Voice Service...');
            
            // Check if gen directory exists
            if (!fs.existsSync(this.genDir)) {
                throw new Error('Gen directory not found. Please ensure the gen folder is present.');
            }
            
            // Check Python dependencies
            await this.checkPythonDependencies();
            
            // Check Whisper model
            await this.ensureWhisperModel();
            
            this.isInitialized = true;
            console.log('✅ Jarvis Voice Service initialized');
            
        } catch (error) {
            console.error('❌ Jarvis Voice Service initialization failed:', error);
            throw error;
        }
    }

    async checkPythonDependencies() {
        const requiredPackages = ['whisper', 'pydub', 'torch', 'requests'];
        
        for (const package of requiredPackages) {
            try {
                await this.runPythonScript(`
try:
    import ${package}
    print("${package} is available")
except ImportError:
    print("${package} not found")
                `);
            } catch (error) {
                console.warn(`⚠️ Python package ${package} not found. Install with: pip3 install ${package}`);
            }
        }
    }

    async ensureWhisperModel() {
        try {
            await this.runPythonScript(`
import whisper
import os
import sys

model_dir = "${this.modelDir}"
model_name = "${this.whisperModel}"

# Ensure model directory exists
os.makedirs(model_dir, exist_ok=True)

# Check if model exists
model_file = os.path.join(model_dir, f"{model_name}.pt")
if not os.path.exists(model_file):
    print(f"Downloading Whisper model {model_name}...")
    model = whisper.load_model(model_name, download_root=model_dir, device="cpu")
    del model
    print(f"Model {model_name} downloaded to {model_dir}")
else:
    print(f"Model {model_name} already exists at {model_file}")
            `);
        } catch (error) {
            console.warn('⚠️ Whisper model setup failed:', error.message);
        }
    }

    async transcribeAudio(audioBuffer, options = {}) {
        try {
            const {
                language = 'en',
                model = this.whisperModel
            } = options;

            // Create Python script using the new voice processing module
            const pythonScript = `
import sys
import os
import base64
import tempfile

# Add gen directory to path
gen_dir = "${this.genDir}"
if gen_dir not in sys.path:
    sys.path.insert(0, gen_dir)

try:
    from voice_to_text import VoiceToTextService
    
    # Initialize STT service
    stt_service = VoiceToTextService(model_name="${model}")
    if not stt_service.initialize():
        print("ERROR:Failed to initialize STT service")
        sys.exit(1)
    
    # Create temporary file from audio buffer
    audio_data = base64.b64decode("${audioBuffer.toString('base64')}")
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
        temp_file.write(audio_data)
        temp_path = temp_file.name
    
    try:
        # Transcribe audio
        result = stt_service.transcribe_audio(temp_path, "${language}")
        print(f"TRANSCRIPTION_RESULT:{result['text']}")
        print(f"LANGUAGE:{result['language']}")
        print(f"MODEL:{result['model']}")
        print(f"CONFIDENCE:{result['confidence']}")
    finally:
        # Clean up
        try:
            os.unlink(temp_path)
        except:
            pass
            
except Exception as e:
    print(f"ERROR:{str(e)}")
    sys.exit(1)
            `;

            const result = await this.runPythonScript(pythonScript);
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            // Extract transcription from output
            const output = result.output;
            const transcriptionMatch = output.match(/TRANSCRIPTION_RESULT:(.+)/);
            const languageMatch = output.match(/LANGUAGE:(.+)/);
            const modelMatch = output.match(/MODEL:(.+)/);
            const confidenceMatch = output.match(/CONFIDENCE:(.+)/);
            
            if (transcriptionMatch) {
                return {
                    text: transcriptionMatch[1],
                    language: languageMatch ? languageMatch[1] : language,
                    model: modelMatch ? modelMatch[1] : model,
                    confidence: confidenceMatch ? parseFloat(confidenceMatch[1]) : 0.9
                };
            } else {
                throw new Error('No transcription result found');
            }

        } catch (error) {
            console.error('Jarvis transcription failed:', error);
            throw error;
        }
    }

    async synthesizeSpeech(text, options = {}) {
        try {
            const {
                voice = 'default',
                engine = 'auto',
                speed = 1.0,
                language = 'en'
            } = options;

            // Create Python script using the new voice processing module
            const pythonScript = `
import sys
import os
import base64

# Add gen directory to path
gen_dir = "${this.genDir}"
if gen_dir not in sys.path:
    sys.path.insert(0, gen_dir)

try:
    from text_to_voice import TextToVoiceService
    
    # Initialize TTS service
    tts_service = TextToVoiceService()
    
    # Synthesize speech
    result = tts_service.synthesize_speech(
        """${text.replace(/"/g, '\\"')}""",
        voice="${voice}",
        language="${language}",
        engine="${engine}",
        speed=${speed}
    )
    
    # Encode audio data as base64
    audio_b64 = base64.b64encode(result['audio_data']).decode('utf-8')
    print(f"AUDIO_DATA:{audio_b64}")
    print(f"FORMAT:{result['format']}")
    print(f"ENGINE:{result['engine']}")
    print(f"VOICE:{result['voice']}")
    
except Exception as e:
    print(f"ERROR:{str(e)}")
    sys.exit(1)
            `;

            const result = await this.runPythonScript(pythonScript);
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            // Extract audio data from output
            const output = result.output;
            const audioMatch = output.match(/AUDIO_DATA:(.+)/);
            const formatMatch = output.match(/FORMAT:(.+)/);
            const engineMatch = output.match(/ENGINE:(.+)/);
            const voiceMatch = output.match(/VOICE:(.+)/);
            
            if (audioMatch) {
                const audioBuffer = Buffer.from(audioMatch[1], 'base64');
                
                return {
                    audioBuffer: audioBuffer,
                    format: formatMatch ? formatMatch[1] : 'wav',
                    engine: engineMatch ? engineMatch[1] : engine,
                    voice: voiceMatch ? voiceMatch[1] : voice
                };
            } else {
                throw new Error('No audio data found in TTS result');
            }

        } catch (error) {
            console.error('Jarvis TTS synthesis failed:', error);
            throw error;
        }
    }

    async generateBitcoinResponse(userInput, context = {}) {
        try {
            const {
                sessionId = 'anonymous',
                previousMessages = [],
                responseType = 'conversational'
            } = context;

            // Create Bitcoin-specific system prompt
            const systemPrompt = await this.createBitcoinSystemPrompt(responseType);
            
            // Generate response using Venice AI
            const response = await this.callVeniceAPI(userInput, systemPrompt);
            
            if (!response) {
                return this.getFallbackResponse(userInput);
            }
            
            // Log the interaction
            await this.logBitcoinInteraction(sessionId, userInput, response);
            
            return {
                text: response,
                confidence: 0.9,
                timestamp: new Date().toISOString(),
                source: 'jarvis-bitcoin-ai'
            };

        } catch (error) {
            console.error('❌ Jarvis Bitcoin content generation failed:', error);
            return this.getFallbackResponse(userInput);
        }
    }

    async callVeniceAPI(userInput, systemPrompt) {
        if (!this.veniceApiKey) {
            throw new Error('VENICE_KEY not found. Please set it in your .env file.');
        }

        const pythonScript = `
import requests
import json

api_key = "${this.veniceApiKey}"
system_prompt = """${systemPrompt.replace(/"/g, '\\"')}"""
user_input = """${userInput.replace(/"/g, '\\"')}"""

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

payload = {
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ],
    "model": "llama-3.3-70b",
    "temperature": 0.7,
    "venice_parameters": {
        "enable_web_search": "auto"
    },
    "parallel_tool_calls": True
}

try:
    response = requests.post(
        "https://api.venice.ai/api/v1/chat/completions",
        json=payload,
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        if "choices" in data and data["choices"]:
            result = data["choices"][0]["message"]["content"]
            print(f"RESPONSE:{result}")
        else:
            print("ERROR:No valid choices in LLM response")
    else:
        print(f"ERROR:Venice API error: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"ERROR:{str(e)}")
            `;

        const result = await this.runPythonScript(pythonScript);
        
        if (result.error) {
            throw new Error(result.error);
        }
        
        // Extract response from output
        const output = result.output;
        const match = output.match(/RESPONSE:(.+)/);
        
        if (match) {
            return match[1];
        } else {
            throw new Error('No response found in Venice API result');
        }
    }

    async createBitcoinSystemPrompt(responseType) {
        try {
            // Try to load the Bitcoin evangelism prompt from the gen system
            const promptPath = path.join(this.genDir, 'prompts', 'bitcoin_evangelism.txt');
            if (fs.existsSync(promptPath)) {
                const bitcoinPrompt = fs.readFileSync(promptPath, 'utf8');
                return bitcoinPrompt;
            }
        } catch (error) {
            console.warn('Failed to load Bitcoin evangelism prompt, using fallback:', error.message);
        }

        // Fallback prompt
        const basePrompt = `You are the Talking Orange, a friendly and enthusiastic Bitcoin evangelist. Your mission is to educate people about Bitcoin in an engaging, accessible way.

PERSONALITY:
- Enthusiastic and optimistic about Bitcoin
- Patient and educational
- Use simple, clear language
- Be encouraging and supportive
- Occasionally use orange-themed expressions
- Keep responses under 100 words
- End with a question to keep conversation going

You have access to web search capabilities, so you can provide up-to-date information about Bitcoin when needed.`;

        const topicSpecificPrompts = {
            'introduction': `Focus on introducing Bitcoin basics: what it is, why it's revolutionary, and how it gives people financial freedom.`,
            'benefits': `Explain Bitcoin's benefits: decentralization, security, global accessibility, and financial sovereignty.`,
            'technology': `Discuss Bitcoin's technical aspects: blockchain, mining, consensus, and cryptographic security.`,
            'economics': `Cover Bitcoin's economic properties: scarcity, store of value, medium of exchange, and monetary policy.`,
            'adoption': `Talk about Bitcoin adoption, use cases, and how it's changing the world.`,
            'myths': `Address common Bitcoin misconceptions and FUD with facts and clear explanations.`,
            'conversational': `Have a natural conversation about Bitcoin, answering questions and providing insights.`
        };

        const topicPrompt = topicSpecificPrompts[responseType] || topicSpecificPrompts['conversational'];
        
        return `${basePrompt}\n\nTOPIC FOCUS: ${topicPrompt}`;
    }

    getFallbackResponse(userInput) {
        const input = userInput.toLowerCase();
        
        if (input.includes('bitcoin') || input.includes('crypto') || input.includes('blockchain')) {
            return "Bitcoin is amazing! It's digital money that gives you financial freedom! 🍊 Ask me more about how Bitcoin works!";
        }
        
        if (input.includes('what is') || input.includes('explain')) {
            return "I'd love to explain! Bitcoin is decentralized digital money that works without banks. It's revolutionary! What would you like to know more about?";
        }
        
        if (input.includes('hello') || input.includes('hi')) {
            return "Hello there! I'm the Talking Orange! 🍊 I'm here to tell you all about Bitcoin! What would you like to know?";
        }
        
        return "That's interesting! Bitcoin is such an exciting topic! 🍊 What would you like to know about digital money and financial freedom?";
    }

    async logBitcoinInteraction(sessionId, userInput, response) {
        try {
            console.log(`₿ Jarvis Bitcoin Interaction - Session: ${sessionId}`);
            console.log(`👤 User: ${userInput}`);
            console.log(`🍊 Orange: ${response}`);
        } catch (error) {
            console.error('Bitcoin analytics logging failed:', error);
        }
    }

    async runPythonScript(script) {
        return new Promise((resolve, reject) => {
        const python = spawn(this.pythonPath, ['-c', script], {
            cwd: this.genDir,
            env: { ...process.env }
        });

            let stdout = '';
            let stderr = '';

            python.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            python.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            python.on('close', (code) => {
                if (code === 0) {
                    resolve({ output: stdout, error: null });
                } else {
                    reject(new Error(`Python script failed: ${stderr}`));
                }
            });

            python.on('error', (error) => {
                reject(error);
            });
        });
    }

    getStatus() {
        return {
            initialized: this.isInitialized,
            genDir: this.genDir,
            pythonPath: this.pythonPath,
            whisperModel: this.whisperModel,
            modelDir: this.modelDir
        };
    }
}

module.exports = JarvisVoiceService;
