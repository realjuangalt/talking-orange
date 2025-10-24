const fetch = require('node-fetch');

class LLMService {
    constructor() {
        this.isInitialized = false;
        this.apiKey = process.env.OPENAI_API_KEY;
        this.baseUrl = process.env.OPENAI_BASE_URL || 'https://api.openai.com/v1';
        this.model = process.env.LLM_MODEL || 'gpt-3.5-turbo';
    }

    async initialize() {
        try {
            console.log('🤖 Initializing LLM Service...');
            
            if (!this.apiKey) {
                console.warn('⚠️ No OpenAI API key provided. Using fallback responses.');
            }
            
            this.isInitialized = true;
            console.log('✅ LLM Service initialized');
            
        } catch (error) {
            console.error('❌ LLM Service initialization failed:', error);
            throw error;
        }
    }

    async generateResponse(userInput, context = {}) {
        try {
            const {
                sessionId = 'anonymous',
                previousMessages = [],
                bitcoinContext = true
            } = context;

            // Create the conversation context
            const messages = this.buildConversationContext(userInput, previousMessages, bitcoinContext);
            
            // Generate response using LLM
            const response = await this.callLLM(messages);
            
            // Log the interaction
            await this.logInteraction(sessionId, userInput, response);
            
            return {
                text: response,
                confidence: 0.9,
                timestamp: new Date().toISOString(),
                model: this.model
            };

        } catch (error) {
            console.error('❌ LLM generation failed:', error);
            // Return fallback response
            return this.getFallbackResponse(userInput);
        }
    }

    buildConversationContext(userInput, previousMessages, bitcoinContext) {
        const systemPrompt = bitcoinContext ? this.getBitcoinSystemPrompt() : this.getGeneralSystemPrompt();
        
        const messages = [
            { role: 'system', content: systemPrompt },
            ...previousMessages.slice(-10), // Keep last 10 messages for context
            { role: 'user', content: userInput }
        ];

        return messages;
    }

    getBitcoinSystemPrompt() {
        return `You are the Talking Orange, a friendly and enthusiastic Bitcoin evangelist. Your mission is to educate people about Bitcoin in an engaging, accessible way.

PERSONALITY:
- Enthusiastic and optimistic about Bitcoin
- Patient and educational
- Use simple, clear language
- Be encouraging and supportive
- Occasionally use orange-themed expressions

BITCOIN KNOWLEDGE:
- Bitcoin is digital money that works without banks or governments
- It's decentralized, meaning no single entity controls it
- Transactions are secure and transparent
- It gives people financial freedom and sovereignty
- It's a store of value and medium of exchange
- It's programmable money with smart contracts

RESPONSE GUIDELINES:
- Keep responses conversational and under 100 words
- Use analogies and simple explanations
- Be encouraging about Bitcoin adoption
- Address common misconceptions
- End with a question to keep the conversation going
- Use emojis sparingly but effectively

Remember: You're not giving financial advice, just educating about Bitcoin technology and philosophy.`;
    }

    getGeneralSystemPrompt() {
        return `You are the Talking Orange, a friendly and helpful AI assistant. You're here to help users with their questions and provide useful information.

PERSONALITY:
- Friendly and approachable
- Helpful and informative
- Use clear, simple language
- Be encouraging and supportive

RESPONSE GUIDELINES:
- Keep responses conversational and under 100 words
- Be helpful and informative
- Ask follow-up questions when appropriate
- Use emojis sparingly but effectively`;
    }

    async callLLM(messages) {
        if (!this.apiKey) {
            return this.getFallbackResponse(messages[messages.length - 1].content);
        }

        try {
            const response = await fetch(`${this.baseUrl}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: this.model,
                    messages: messages,
                    max_tokens: 150,
                    temperature: 0.7,
                    presence_penalty: 0.1,
                    frequency_penalty: 0.1
                })
            });

            if (!response.ok) {
                throw new Error(`LLM API error: ${response.statusText}`);
            }

            const data = await response.json();
            return data.choices[0].message.content.trim();

        } catch (error) {
            console.error('❌ LLM API call failed:', error);
            throw error;
        }
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

    async logInteraction(sessionId, userInput, response) {
        try {
            // This would log to your analytics system
            console.log(`📊 LLM Interaction - Session: ${sessionId}`);
            console.log(`👤 User: ${userInput}`);
            console.log(`🤖 Orange: ${response}`);
        } catch (error) {
            console.error('Analytics logging failed:', error);
        }
    }

    // Get conversation history for context
    async getConversationHistory(sessionId, limit = 10) {
        // This would retrieve from your database
        // For now, return empty array
        return [];
    }

    // Update conversation history
    async updateConversationHistory(sessionId, userInput, response) {
        try {
            // This would store in your database
            const interaction = {
                sessionId,
                userInput,
                response,
                timestamp: new Date().toISOString()
            };
            
            // Store in database here
            console.log('📝 Conversation updated:', interaction);
            
        } catch (error) {
            console.error('Failed to update conversation history:', error);
        }
    }

    // Get available models
    getAvailableModels() {
        return [
            'gpt-3.5-turbo',
            'gpt-4',
            'gpt-4-turbo-preview',
            'claude-3-haiku',
            'claude-3-sonnet'
        ];
    }

    // Set model
    setModel(model) {
        this.model = model;
    }

    // Get model info
    getModelInfo() {
        return {
            model: this.model,
            baseUrl: this.baseUrl,
            hasApiKey: !!this.apiKey
        };
    }

    getStatus() {
        return {
            initialized: this.isInitialized,
            model: this.model,
            hasApiKey: !!this.apiKey,
            baseUrl: this.baseUrl
        };
    }
}

module.exports = LLMService;
