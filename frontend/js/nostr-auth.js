/**
 * Nostr Authentication Module
 * Handles Nostr key generation, validation, and authentication
 */

// Check if nostr-tools is loaded
// nostr-tools can be exposed as window.NostrTools or window.nostr depending on the bundle
console.log('🔍 [NOSTR-AUTH] Checking for nostr-tools library...');
console.log('🔍 [NOSTR-AUTH] window.NostrTools:', typeof window.NostrTools);
console.log('🔍 [NOSTR-AUTH] window.nostr:', typeof window.nostr);

// Use a different variable name to avoid conflict with window.NostrTools
let nostrToolsLib = null;
if (typeof window.NostrTools !== 'undefined') {
    nostrToolsLib = window.NostrTools;
    console.log('✅ [NOSTR-AUTH] Found nostr-tools as window.NostrTools');
} else if (typeof window.nostr !== 'undefined') {
    nostrToolsLib = window.nostr;
    console.log('✅ [NOSTR-AUTH] Found nostr-tools as window.nostr');
} else {
    console.error('❌ [NOSTR-AUTH] nostr-tools library not loaded. Make sure nostr-tools.min.js is included.');
    console.error('❌ [NOSTR-AUTH] Available window properties:', Object.keys(window).filter(k => k.toLowerCase().includes('nostr')));
}

/**
 * Generate a new Nostr key pair
 * @returns {Object} { nsec: string, npub: string }
 */
function generateNostrKeyPair() {
    try {
        if (!nostrToolsLib) {
            throw new Error('nostr-tools library not loaded');
        }
        
        console.log('🔍 [NOSTR-AUTH] Checking available key generation functions...');
        console.log('🔍 [NOSTR-AUTH] generatePrivateKey:', typeof nostrToolsLib.generatePrivateKey);
        console.log('🔍 [NOSTR-AUTH] generateSecretKey:', typeof nostrToolsLib.generateSecretKey);
        
        // Generate private key - need to get it as Uint8Array for encoding
        let privateKeyBytes; // Will be Uint8Array
        let privateKeyHex;   // Will be hex string for getPublicKey
        
        if (typeof nostrToolsLib.generateSecretKey === 'function') {
            // generateSecretKey returns Uint8Array (preferred)
            privateKeyBytes = nostrToolsLib.generateSecretKey();
            // Convert Uint8Array to hex for getPublicKey
            privateKeyHex = Array.from(privateKeyBytes).map(b => b.toString(16).padStart(2, '0')).join('');
            console.log('✅ [NOSTR-AUTH] Used generateSecretKey, got Uint8Array');
        } else if (typeof nostrToolsLib.generatePrivateKey === 'function') {
            // generatePrivateKey might return hex string or Uint8Array
            const result = nostrToolsLib.generatePrivateKey();
            if (result instanceof Uint8Array) {
                privateKeyBytes = result;
                privateKeyHex = Array.from(result).map(b => b.toString(16).padStart(2, '0')).join('');
            } else if (typeof result === 'string') {
                // It's a hex string, convert to Uint8Array
                privateKeyHex = result;
                privateKeyBytes = new Uint8Array(result.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
            } else {
                throw new Error('Unexpected return type from generatePrivateKey');
            }
            console.log('✅ [NOSTR-AUTH] Used generatePrivateKey');
        } else {
            throw new Error('No key generation function found in nostr-tools');
        }
        
        console.log('🔍 [NOSTR-AUTH] privateKeyBytes type:', privateKeyBytes.constructor.name);
        console.log('🔍 [NOSTR-AUTH] privateKeyBytes length:', privateKeyBytes.length);
        console.log('🔍 [NOSTR-AUTH] privateKeyHex length:', privateKeyHex.length);
        
        // Get public key from private key
        // getPublicKey typically accepts hex string and returns hex string
        let publicKeyHex;
        let publicKeyBytes;
        
        if (typeof nostrToolsLib.getPublicKey === 'function') {
            // Try with Uint8Array first, then hex string
            let publicKeyResult;
            try {
                publicKeyResult = nostrToolsLib.getPublicKey(privateKeyBytes);
                console.log('✅ [NOSTR-AUTH] getPublicKey accepted Uint8Array');
            } catch (e) {
                console.log('🔍 [NOSTR-AUTH] getPublicKey with Uint8Array failed, trying hex string...');
                publicKeyResult = nostrToolsLib.getPublicKey(privateKeyHex);
            }
            
            if (publicKeyResult instanceof Uint8Array) {
                publicKeyBytes = publicKeyResult;
                publicKeyHex = Array.from(publicKeyResult).map(b => b.toString(16).padStart(2, '0')).join('');
            } else if (typeof publicKeyResult === 'string') {
                publicKeyHex = publicKeyResult;
                // Convert hex string to Uint8Array for encoding
                publicKeyBytes = new Uint8Array(publicKeyResult.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
            } else {
                throw new Error('Unexpected return type from getPublicKey: ' + typeof publicKeyResult);
            }
            console.log('✅ [NOSTR-AUTH] Got public key, hex length:', publicKeyHex.length);
            console.log('🔍 [NOSTR-AUTH] publicKeyBytes type:', publicKeyBytes.constructor.name);
            console.log('🔍 [NOSTR-AUTH] publicKeyBytes length:', publicKeyBytes.length);
        } else {
            throw new Error('getPublicKey function not found in nostr-tools');
        }
        
        // Verify privateKeyBytes is Uint8Array
        if (!(privateKeyBytes instanceof Uint8Array)) {
            throw new Error('privateKeyBytes is not a Uint8Array, got: ' + typeof privateKeyBytes);
        }
        
        // Verify we have hex strings for encoding
        if (!privateKeyHex || typeof privateKeyHex !== 'string') {
            throw new Error('privateKeyHex is not a string, got: ' + typeof privateKeyHex);
        }
        if (!publicKeyHex || typeof publicKeyHex !== 'string') {
            throw new Error('publicKeyHex is not a string, got: ' + typeof publicKeyHex);
        }
        
        // Convert to Bech32 format (nsec/npub)
        // nsecEncode might accept Uint8Array or hex string
        // npubEncode expects hex string based on the error
        console.log('🔍 [NOSTR-AUTH] Encoding nsec...');
        let nsec;
        try {
            // Try with Uint8Array first
            nsec = nostrToolsLib.nip19.nsecEncode(privateKeyBytes);
            console.log('✅ [NOSTR-AUTH] nsecEncode accepted Uint8Array');
        } catch (e) {
            // If that fails, try with hex string
            console.log('🔍 [NOSTR-AUTH] nsecEncode with Uint8Array failed, trying hex string...');
            nsec = nostrToolsLib.nip19.nsecEncode(privateKeyHex);
            console.log('✅ [NOSTR-AUTH] nsecEncode accepted hex string');
        }
        
        console.log('🔍 [NOSTR-AUTH] Encoding npub with hex string (length:', publicKeyHex.length, ')...');
        // npubEncode expects hex string based on error message
        const npub = nostrToolsLib.nip19.npubEncode(publicKeyHex);
        
        console.log('✅ [NOSTR-AUTH] Generated nsec (length):', nsec.length);
        console.log('✅ [NOSTR-AUTH] Generated npub (length):', npub.length);
        
        return {
            nsec: nsec,
            npub: npub,
            privateKeyHex: privateKeyHex,
            publicKeyHex: publicKeyHex
        };
    } catch (error) {
        console.error('Error generating Nostr key pair:', error);
        throw error;
    }
}

/**
 * Validate nsec format
 * @param {string} nsec - Nostr private key in Bech32 format
 * @returns {boolean} True if valid
 */
function validateNsec(nsec) {
    try {
        if (!nsec || typeof nsec !== 'string') {
            return false;
        }
        
        // Check if it starts with 'nsec1'
        if (!nsec.startsWith('nsec1')) {
            return false;
        }
        
        // Try to decode it
        if (!nostrToolsLib) {
            return false;
        }
        const decoded = nostrToolsLib.nip19.decode(nsec);
        return decoded && decoded.type === 'nsec' && decoded.data;
    } catch (error) {
        console.error('Error validating nsec:', error);
        return false;
    }
}

/**
 * Get npub from nsec
 * @param {string} nsec - Nostr private key in Bech32 format
 * @returns {string} npub in Bech32 format
 */
function getNpubFromNsec(nsec) {
    try {
        if (!validateNsec(nsec)) {
            throw new Error('Invalid nsec format');
        }
        
        if (!nostrToolsLib) {
            throw new Error('nostr-tools library not loaded');
        }
        
        // Decode nsec to get private key (decoded.data is Uint8Array)
        const decoded = nostrToolsLib.nip19.decode(nsec);
        const privateKeyBytes = decoded.data; // This is already Uint8Array
        
        console.log('🔍 [NOSTR-AUTH] Decoded nsec, privateKeyBytes type:', privateKeyBytes.constructor.name);
        console.log('🔍 [NOSTR-AUTH] privateKeyBytes length:', privateKeyBytes.length);
        
        // Convert to hex for getPublicKey
        const privateKeyHex = Array.from(privateKeyBytes).map(b => b.toString(16).padStart(2, '0')).join('');
        console.log('🔍 [NOSTR-AUTH] privateKeyHex length:', privateKeyHex.length);
        
        // Get public key from private key
        // Try with Uint8Array first, then hex string
        let publicKeyHex;
        try {
            const publicKeyResult = nostrToolsLib.getPublicKey(privateKeyBytes);
            if (publicKeyResult instanceof Uint8Array) {
                publicKeyHex = Array.from(publicKeyResult).map(b => b.toString(16).padStart(2, '0')).join('');
            } else {
                publicKeyHex = publicKeyResult;
            }
            console.log('✅ [NOSTR-AUTH] getPublicKey with Uint8Array succeeded');
        } catch (e) {
            console.log('🔍 [NOSTR-AUTH] getPublicKey with Uint8Array failed, trying hex string...');
            publicKeyHex = nostrToolsLib.getPublicKey(privateKeyHex);
        }
        
        console.log('✅ [NOSTR-AUTH] Got publicKeyHex, length:', publicKeyHex ? publicKeyHex.length : 'null');
        console.log('🔍 [NOSTR-AUTH] publicKeyHex type:', typeof publicKeyHex);
        console.log('🔍 [NOSTR-AUTH] publicKeyHex value (first 20 chars):', publicKeyHex ? publicKeyHex.substring(0, 20) : 'null');
        
        // Ensure publicKeyHex is a string
        if (!publicKeyHex || typeof publicKeyHex !== 'string') {
            throw new Error('publicKeyHex must be a hex string, got: ' + typeof publicKeyHex);
        }
        
        // Encode to npub (needs hex string, not Uint8Array)
        console.log('🔍 [NOSTR-AUTH] Encoding npub with hex string (length:', publicKeyHex.length, ')...');
        const npub = nostrToolsLib.nip19.npubEncode(publicKeyHex);
        console.log('✅ [NOSTR-AUTH] npub encoded successfully, length:', npub.length);
        
        return npub;
    } catch (error) {
        console.error('Error getting npub from nsec:', error);
        throw error;
    }
}

/**
 * Check authentication status
 * @returns {Promise<Object>} { authenticated: boolean, npub?: string, userId?: string }
 */
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/nostr/status', {
            method: 'GET',
            credentials: 'include' // Include cookies
        });
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error checking auth status:', error);
        return { authenticated: false };
    }
}

/**
 * Login with nsec
 * @param {string} nsec - Nostr private key
 * @returns {Promise<Object>} { success: boolean, npub?: string, userId?: string, error?: string }
 */
async function loginWithNsec(nsec) {
    try {
        if (!validateNsec(nsec)) {
            return { success: false, error: 'Invalid nsec format' };
        }
        
        // Get npub from nsec before sending
        const npub = getNpubFromNsec(nsec);
        
        const response = await fetch('/api/auth/nostr/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include', // Include cookies
            body: JSON.stringify({ nsec: nsec, npub: npub })
        });
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error logging in:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Create new account (generate keys and login)
 * @returns {Promise<Object>} { success: boolean, nsec?: string, npub?: string, userId?: string, error?: string }
 */
async function createNewAccount() {
    try {
        // Generate new key pair
        const keyPair = generateNostrKeyPair();
        
        // Login with the new nsec
        const loginResult = await loginWithNsec(keyPair.nsec);
        
        if (loginResult.success) {
            return {
                success: true,
                nsec: keyPair.nsec,
                npub: keyPair.npub,
                userId: loginResult.userId || loginResult.npub
            };
        } else {
            return {
                success: false,
                error: loginResult.error || 'Failed to create account'
            };
        }
    } catch (error) {
        console.error('Error creating account:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Logout user
 * @returns {Promise<Object>} { success: boolean }
 */
async function logout() {
    try {
        const response = await fetch('/api/auth/nostr/logout', {
            method: 'POST',
            credentials: 'include'
        });
        
        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error logging out:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Get short npub for display (first 8 chars + last 8 chars)
 * @param {string} npub - Full npub
 * @returns {string} Short npub
 */
function getShortNpub(npub) {
    if (!npub || npub.length < 16) {
        return npub;
    }
    return npub.substring(0, 8) + '...' + npub.substring(npub.length - 8);
}

// Export functions to window
if (typeof window !== 'undefined') {
    window.nostrAuth = {
        generateNostrKeyPair,
        validateNsec,
        getNpubFromNsec,
        checkAuthStatus,
        loginWithNsec,
        createNewAccount,
        logout,
        getShortNpub
    };
    console.log('✅ [NOSTR-AUTH] Module exported to window.nostrAuth');
    console.log('✅ [NOSTR-AUTH] Available functions:', Object.keys(window.nostrAuth));
} else {
    console.error('❌ [NOSTR-AUTH] window is undefined, cannot export module');
}

console.log('✅ [NOSTR-AUTH] Nostr authentication module loaded');
