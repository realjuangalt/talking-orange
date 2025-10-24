// QR Manager - Handles QR code generation and scanning
class QRManager {
    constructor() {
        this.isInitialized = false;
        this.callbacks = {
            onQRDetected: [],
            onQRError: []
        };
    }

    async initialize() {
        try {
            console.log('📱 Initializing QR Manager...');
            
            // Check for QR code library support
            if (!this.isQRCodeSupported()) {
                throw new Error('QR code library not available');
            }
            
            this.isInitialized = true;
            console.log('✅ QR Manager initialized');
            
        } catch (error) {
            console.error('❌ QR Manager initialization failed:', error);
            throw error;
        }
    }

    isQRCodeSupported() {
        return typeof QRCode !== 'undefined' && typeof jsQR !== 'undefined';
    }

    // Generate QR code
    async generateQRCode(text, options = {}) {
        try {
            const defaultOptions = {
                width: 256,
                margin: 2,
                color: {
                    dark: '#000000',
                    light: '#FFFFFF'
                },
                errorCorrectionLevel: 'M'
            };
            
            const qrOptions = { ...defaultOptions, ...options };
            
            const qrCodeDataURL = await QRCode.toDataURL(text, qrOptions);
            return qrCodeDataURL;
            
        } catch (error) {
            console.error('❌ QR code generation failed:', error);
            throw error;
        }
    }

    // Generate QR code as SVG
    async generateQRCodeSVG(text, options = {}) {
        try {
            const defaultOptions = {
                width: 256,
                margin: 2,
                color: {
                    dark: '#000000',
                    light: '#FFFFFF'
                }
            };
            
            const qrOptions = { ...defaultOptions, ...options };
            
            const qrCodeSVG = await QRCode.toString(text, { type: 'svg', ...qrOptions });
            return qrCodeSVG;
            
        } catch (error) {
            console.error('❌ QR code SVG generation failed:', error);
            throw error;
        }
    }

    // Scan QR code from image data
    scanQRCode(imageData, width, height) {
        try {
            const code = jsQR(imageData, width, height);
            
            if (code) {
                console.log('📱 QR code detected:', code.data);
                this.triggerCallbacks('onQRDetected', code);
                return code;
            } else {
                return null;
            }
            
        } catch (error) {
            console.error('❌ QR code scanning failed:', error);
            this.triggerCallbacks('onQRError', error);
            return null;
        }
    }

    // Scan QR code from canvas
    scanQRCodeFromCanvas(canvas) {
        const context = canvas.getContext('2d');
        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
        return this.scanQRCode(imageData.data, canvas.width, canvas.height);
    }

    // Scan QR code from video element
    scanQRCodeFromVideo(video) {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        const context = canvas.getContext('2d');
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        return this.scanQRCodeFromCanvas(canvas);
    }

    // Create QR code for Bitcoin content
    async createBitcoinQRCode(contentType = 'introduction', baseUrl = null) {
        const url = baseUrl || window.location.origin;
        const qrData = `${url}?content=${contentType}`;
        
        return await this.generateQRCode(qrData, {
            width: 300,
            margin: 3,
            color: {
                dark: '#FF8C00', // Orange color for Bitcoin theme
                light: '#FFFFFF'
            }
        });
    }

    // Create QR code for AR marker
    async createARMarkerQRCode(markerId = 'hiro', baseUrl = null) {
        const url = baseUrl || window.location.origin;
        const qrData = `${url}?marker=${markerId}`;
        
        return await this.generateQRCode(qrData, {
            width: 200,
            margin: 2,
            color: {
                dark: '#000000',
                light: '#FFFFFF'
            }
        });
    }

    // Download QR code as image
    downloadQRCode(qrCodeDataURL, filename = 'qr-code.png') {
        const link = document.createElement('a');
        link.download = filename;
        link.href = qrCodeDataURL;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Display QR code in element
    displayQRCode(element, qrCodeDataURL) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (element) {
            element.innerHTML = `<img src="${qrCodeDataURL}" alt="QR Code" style="max-width: 100%; height: auto;">`;
        }
    }

    // Event listener registration
    onQRDetected(callback) {
        this.callbacks.onQRDetected.push(callback);
    }

    onQRError(callback) {
        this.callbacks.onQRError.push(callback);
    }

    triggerCallbacks(eventType, data = null) {
        if (this.callbacks[eventType]) {
            this.callbacks[eventType].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`QR callback error for ${eventType}:`, error);
                }
            });
        }
    }

    // Get QR code info
    getQRCodeInfo(qrCode) {
        if (!qrCode) return null;
        
        return {
            data: qrCode.data,
            location: qrCode.location,
            version: qrCode.version,
            errorCorrectionLevel: qrCode.errorCorrectionLevel
        };
    }

    // Validate QR code data
    validateQRCodeData(data) {
        try {
            // Basic validation - check if it's a URL
            const url = new URL(data);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch (error) {
            return false;
        }
    }

    // Get available QR code options
    getQRCodeOptions() {
        return {
            errorCorrectionLevels: ['L', 'M', 'Q', 'H'],
            modes: ['numeric', 'alphanumeric', 'byte'],
            sizes: [100, 200, 300, 400, 500]
        };
    }

    // Get current status
    getStatus() {
        return {
            initialized: this.isInitialized,
            supported: this.isQRCodeSupported()
        };
    }
}
