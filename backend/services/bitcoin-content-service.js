const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

class BitcoinContentService {
    constructor() {
        this.isInitialized = false;
        this.genDir = path.join(__dirname, '../../gen');
        this.pythonPath = process.env.PYTHON_PATH || 'python3';
    }

    async initialize() {
        try {
            console.log('₿ Initializing Bitcoin Content Service...');
            
            // Check if Python and gen directory exist
            await this.checkDependencies();
            
            this.isInitialized = true;
            console.log('✅ Bitcoin Content Service initialized');
            
        } catch (error) {
            console.error('❌ Bitcoin Content Service initialization failed:', error);
            throw error;
        }
    }

    async checkDependencies() {
        // Check if Python is available
        await this.checkPython();
        
        // Check if gen directory exists
        if (!fs.existsSync(this.genDir)) {
            throw new Error('Gen directory not found. Please ensure the gen folder is present.');
        }
        
        // Check if required Python packages are installed
        await this.checkPythonPackages();
    }

    async checkPython() {
        return new Promise((resolve, reject) => {
            const python = spawn(this.pythonPath, ['--version']);
            
            python.on('error', (error) => {
                reject(new Error(`Python not found: ${error.message}`));
            });
            
            python.on('close', (code) => {
                if (code === 0) {
                    resolve();
                } else {
                    reject(new Error('Python not properly installed'));
                }
            });
        });
    }

    async checkPythonPackages() {
        const requiredPackages = ['aiohttp', 'python-dotenv'];
        
        for (const package of requiredPackages) {
            try {
                await this.runPythonScript(`
import ${package}
print("${package} is available")
                `);
            } catch (error) {
                console.warn(`⚠️ Python package ${package} not found. Install with: pip3 install ${package}`);
            }
        }
    }

    async generateBitcoinResponse(userInput, context = {}) {
        try {
            const {
                sessionId = 'anonymous',
                previousMessages = [],
                responseType = 'conversational'
            } = context;

            // Create Bitcoin-specific prompt
            const prompt = this.createBitcoinPrompt(userInput, context);
            
            // Generate response using the existing text generator
            const response = await this.callTextGenerator(prompt, {
                model: 'llama-3.3-70b',
                max_tokens: 200,
                temperature: 0.8
            });
            
            if (!response) {
                return this.getFallbackResponse(userInput);
            }
            
            // Log the interaction
            await this.logBitcoinInteraction(sessionId, userInput, response);
            
            return {
                text: response,
                confidence: 0.9,
                timestamp: new Date().toISOString(),
                source: 'bitcoin-ai'
            };

        } catch (error) {
            console.error('❌ Bitcoin content generation failed:', error);
            return this.getFallbackResponse(userInput);
        }
    }

    createBitcoinPrompt(userInput, context) {
        const {
            previousMessages = [],
            responseType = 'conversational',
            bitcoinTopic = 'general'
        } = context;

        // Build conversation history
        const conversationHistory = previousMessages
            .slice(-5) // Last 5 messages for context
            .map(msg => `${msg.role}: ${msg.content}`)
            .join('\n');

        // Create Bitcoin-specific system prompt
        const systemPrompt = this.getBitcoinSystemPrompt(responseType, bitcoinTopic);
        
        // Build the full prompt
        let prompt = `${systemPrompt}\n\n`;
        
        if (conversationHistory) {
            prompt += `Previous conversation:\n${conversationHistory}\n\n`;
        }
        
        prompt += `User: ${userInput}\n\n`;
        prompt += `Talking Orange:`;

        return prompt;
    }

    getBitcoinSystemPrompt(responseType, bitcoinTopic) {
        const basePrompt = `You are the Talking Orange, a friendly and enthusiastic Bitcoin evangelist. Your mission is to educate people about Bitcoin in an engaging, accessible way.

PERSONALITY:
- Enthusiastic and optimistic about Bitcoin
- Patient and educational
- Use simple, clear language
- Be encouraging and supportive
- Occasionally use orange-themed expressions
- Keep responses under 100 words
- End with a question to keep conversation going`;

        const topicSpecificPrompts = {
            'introduction': `Focus on introducing Bitcoin basics: what it is, why it's revolutionary, and how it gives people financial freedom.`,
            'benefits': `Explain Bitcoin's benefits: decentralization, security, global accessibility, and financial sovereignty.`,
            'technology': `Discuss Bitcoin's technical aspects: blockchain, mining, consensus, and cryptographic security.`,
            'economics': `Cover Bitcoin's economic properties: scarcity, store of value, medium of exchange, and monetary policy.`,
            'adoption': `Talk about Bitcoin adoption, use cases, and how it's changing the world.`,
            'myths': `Address common Bitcoin misconceptions and FUD with facts and clear explanations.`,
            'conversational': `Have a natural conversation about Bitcoin, answering questions and providing insights.`
        };

        const topicPrompt = topicSpecificPrompts[bitcoinTopic] || topicSpecificPrompts['conversational'];
        
        return `${basePrompt}\n\nTOPIC FOCUS: ${topicPrompt}`;
    }

    async callTextGenerator(prompt, options = {}) {
        const {
            model = 'llama-3.3-70b',
            max_tokens = 200,
            temperature = 0.8
        } = options;

        try {
            // Create a Python script that uses the existing text generator
            const pythonScript = `
import sys
import os
import asyncio
import json

# Add gen directory to path
gen_dir = "${this.genDir}"
if gen_dir not in sys.path:
    sys.path.insert(0, gen_dir)

try:
    from text_generator import TextGenerator
    
    async def generate_response():
        generator = TextGenerator()
        response = await generator.generate_text(
            prompt="${prompt.replace(/"/g, '\\"')}",
            model="${model}",
            max_tokens=${max_tokens},
            temperature=${temperature}
        )
        return response
    
    # Run the async function
    result = asyncio.run(generate_response())
    print(json.dumps({"response": result}))
    
except Exception as e:
    print(json.dumps({"error": str(e)}))
`;

            const result = await this.runPythonScript(pythonScript);
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            return result.response;

        } catch (error) {
            console.error('Text generator call failed:', error);
            throw error;
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
                    try {
                        const result = JSON.parse(stdout);
                        resolve(result);
                    } catch (error) {
                        reject(new Error(`Failed to parse Python output: ${stdout}`));
                    }
                } else {
                    reject(new Error(`Python script failed: ${stderr}`));
                }
            });

            python.on('error', (error) => {
                reject(error);
            });
        });
    }

    getFallbackResponse(userInput) {
        const input = userInput.toLowerCase();
        
        // Bitcoin-related responses
        if (input.includes('bitcoin') || input.includes('crypto') || input.includes('blockchain')) {
            return "Bitcoin is amazing! It's digital money that gives you financial freedom! 🍊 Ask me more about how Bitcoin works!";
        }
        
        if (input.includes('what is') || input.includes('explain')) {
            return "I'd love to explain! Bitcoin is decentralized digital money that works without banks. It's revolutionary! What would you like to know more about?";
        }
        
        if (input.includes('hello') || input.includes('hi')) {
            return "Hello there! I'm the Talking Orange! 🍊 I'm here to tell you all about Bitcoin! What would you like to know?";
        }
        
        if (input.includes('help') || input.includes('how')) {
            return "I'm here to help you understand Bitcoin! It's digital money that's secure, fast, and gives you control over your finances!";
        }
        
        // Default response
        return "That's interesting! Bitcoin is such an exciting topic! 🍊 What would you like to know about digital money and financial freedom?";
    }

    async logBitcoinInteraction(sessionId, userInput, response) {
        try {
            // This would log to your analytics system
            console.log(`₿ Bitcoin Interaction - Session: ${sessionId}`);
            console.log(`👤 User: ${userInput}`);
            console.log(`🍊 Orange: ${response}`);
        } catch (error) {
            console.error('Bitcoin analytics logging failed:', error);
        }
    }

    // Generate Bitcoin educational content
    async generateBitcoinContent(contentType, options = {}) {
        const {
            topic = 'general',
            difficulty = 'beginner',
            length = 'short'
        } = options;

        const prompt = this.createContentPrompt(contentType, topic, difficulty, length);
        
        try {
            const content = await this.callTextGenerator(prompt, {
                model: 'llama-3.3-70b',
                max_tokens: 500,
                temperature: 0.7
            });
            
            return {
                content,
                type: contentType,
                topic,
                difficulty,
                length,
                timestamp: new Date().toISOString()
            };
            
        } catch (error) {
            console.error('Content generation failed:', error);
            return null;
        }
    }

    createContentPrompt(contentType, topic, difficulty, length) {
        const difficultyLevels = {
            'beginner': 'simple, easy-to-understand language',
            'intermediate': 'moderate complexity with some technical terms',
            'advanced': 'detailed technical explanations'
        };

        const lengthLevels = {
            'short': '2-3 sentences',
            'medium': '1-2 paragraphs',
            'long': 'detailed explanation with examples'
        };

        return `Create ${length} Bitcoin content about ${topic} using ${difficultyLevels[difficulty]}. 
        
Content type: ${contentType}
Topic: ${topic}
Difficulty: ${difficulty}
Length: ${length}

Make it engaging and educational for someone learning about Bitcoin.`;
    }

    getStatus() {
        return {
            initialized: this.isInitialized,
            genDir: this.genDir,
            pythonPath: this.pythonPath
        };
    }
}

module.exports = BitcoinContentService;
