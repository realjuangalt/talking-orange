/**
 * QR Code Manager for Talking Orange
 * Handles QR code generation and scanning for AR trigger
 */

class QRManager {
    constructor() {
        this.qrCode = null;
        this.isScanning = false;
        this.scanInterval = null;
    }
    
    generateQRCode(url) {
        console.log('🔗 Generating QR code for:', url);
        
        // Create QR code element
        const qrContainer = document.createElement('div');
        qrContainer.id = 'qr-code';
        qrContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 10px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            z-index: 1000;
        `;
        
        // Generate QR code using qrcode.js
        if (typeof QRCode !== 'undefined') {
            this.qrCode = new QRCode(qrContainer, {
                text: url,
                width: 150,
                height: 150,
                colorDark: "#000000",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.M
            });
        }
        
        document.body.appendChild(qrContainer);
        console.log('✅ QR code generated');
    }
    
    startScanning() {
        console.log('📱 Starting QR code scanning...');
        this.isScanning = true;
        
        // This would integrate with a QR scanner library
        // For now, we'll simulate detection
        this.simulateQRDetection();
    }
    
    simulateQRDetection() {
        // Simulate QR code detection after 2 seconds
        setTimeout(() => {
            if (this.isScanning) {
                console.log('📱 QR Code detected! Starting AR experience...');
                this.onQRDetected();
            }
        }, 2000);
    }
    
    onQRDetected() {
        console.log('🎯 QR Code detected - triggering AR experience');
        
        // Hide QR code
        const qrContainer = document.getElementById('qr-code');
        if (qrContainer) {
            qrContainer.style.display = 'none';
        }
        
        // Trigger AR experience
        if (window.talkingOrangeApp && window.talkingOrangeApp.arManager) {
            window.talkingOrangeApp.arManager.showOrangeCharacter();
        }
    }
    
    stopScanning() {
        console.log('🛑 Stopping QR code scanning...');
        this.isScanning = false;
        
        if (this.scanInterval) {
            clearInterval(this.scanInterval);
            this.scanInterval = null;
        }
    }
    
    destroy() {
        this.stopScanning();
        
        const qrContainer = document.getElementById('qr-code');
        if (qrContainer) {
            qrContainer.remove();
        }
        
        console.log('🧹 QR Manager cleaned up');
    }
}

// Export for use in main app
window.QRManager = QRManager;