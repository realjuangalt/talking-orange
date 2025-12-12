# Nostr Authentication Implementation Plan

## Overview
Implement Nostr-based authentication for account security and management. Users will authenticate using their Nostr private key (nsec) or create a new one, with the public key (npub) used as their user identifier.

## Library Choice
**Primary Library: `nostr-tools`** (via CDN)
- Lightweight, minimal dependencies
- Provides key generation, signing, and encoding utilities
- Supports Bech32 encoding (nsec/npub format)
- Well-maintained and widely used

**Installation:**
Since the project doesn't use npm for frontend dependencies, we'll use a CDN:
```html
<script src="https://unpkg.com/nostr-tools@latest/lib/nostr.bundle.js"></script>
```
Or download and include in `frontend/lib/nostr-tools.min.js` for offline use.

## Architecture

### Key Components

1. **Frontend Authentication Module** (`frontend/js/nostr-auth.js`)
   - Handle key generation
   - Handle key import/validation
   - Manage authentication state
   - Cookie management (secure, httpOnly via backend)

2. **Backend Authentication Endpoints** (`backend/app.py`)
   - `/api/auth/nostr/login` (POST) - Validate nsec, set cookie, return npub
   - `/api/auth/nostr/status` (GET) - Check authentication status
   - `/api/auth/nostr/logout` (POST) - Clear authentication cookie

3. **Login Modal Component** (`frontend/js/nostr-login-modal.js`)
   - Modal UI for login flow
   - Options: "Create New Key" or "Import Existing Key"
   - Secure input handling for nsec

4. **User ID Derivation**
   - Use npub directly as user ID (if acceptable length ~63 chars)
   - OR: Hash npub to create shorter user ID (e.g., SHA256, take first 32 chars)
   - Store mapping: `npub -> user_id` in backend if hashing

## Implementation Steps

### Phase 1: Setup and Dependencies

1. **Add nostr-tools library**
   - Option A (CDN - Recommended): Add script tag to index.html
     ```html
     <script src="https://unpkg.com/nostr-tools@latest/lib/nostr.bundle.js"></script>
     ```
   - Option B (Local): Download nostr-tools bundle and place in `frontend/lib/nostr-tools.min.js`
     ```html
     <script src="./lib/nostr-tools.min.js"></script>
     ```

2. **Create frontend authentication module**
   - File: `frontend/js/nostr-auth.js`
   - Functions:
     - `generateNostrKeyPair()` - Generate new nsec/npub
     - `validateNsec(nsec)` - Validate nsec format
     - `getNpubFromNsec(nsec)` - Derive npub from nsec
     - `checkAuthStatus()` - Check if user is authenticated
     - `loginWithNsec(nsec)` - Send nsec to backend, get cookie
     - `createNewAccount()` - Generate new key pair and login
     - `logout()` - Clear authentication

3. **Create login modal component**
   - File: `frontend/js/nostr-login-modal.js` (or inline in index.html)
   - Modal with:
     - Tab/buttons: "Create New" vs "Import Existing"
     - Input field for nsec (password-masked)
     - Generate button for new keys
     - Import button for existing keys
     - Display npub after generation (read-only)
     - Warning about backing up nsec

### Phase 2: Backend Authentication

1. **Add authentication endpoints to `backend/app.py`**
   
   ```python
   @app.route('/api/auth/nostr/login', methods=['POST'])
   def nostr_login():
       """
       Authenticate with Nostr private key (nsec).
       Validates nsec, derives npub, sets secure cookie.
       """
       # 1. Get nsec from request body
       # 2. Validate nsec format (Bech32)
       # 3. Derive npub from nsec
       # 4. Set secure, httpOnly cookie with npub
       # 5. Return npub and user_id
   
   @app.route('/api/auth/nostr/status', methods=['GET'])
   def nostr_auth_status():
       """
       Check if user is authenticated.
       Returns npub and user_id if authenticated.
       """
       # 1. Read npub from cookie
       # 2. Return authentication status
   
   @app.route('/api/auth/nostr/logout', methods=['POST'])
   def nostr_logout():
       """
       Logout user by clearing authentication cookie.
       """
       # Clear cookie
   ```

2. **Install Python Nostr library** (if needed for backend validation)
   - `nostr` package or use JavaScript validation via subprocess
   - OR: Use `bech32` Python library for Bech32 decoding

3. **Cookie Security**
   - Set `httpOnly=True` (prevents JavaScript access)
   - Set `secure=True` (HTTPS only in production)
   - Set `samesite='Lax'` or `'Strict'`
   - Cookie name: `nostr_auth` or `nostr_npub`

### Phase 3: Frontend Integration

1. **Update burger menu button** (`frontend/index.html`)
   - Change button text/behavior based on auth status
   - If not authenticated: "🔐 Login"
   - If authenticated: "👤 [npub short]"
   - On click: Show login modal if not authenticated, or show user menu if authenticated

2. **Update user.html**
   - Check authentication on page load
   - Redirect to login if not authenticated
   - Use npub as userId instead of localStorage-generated ID
   - Remove old `generateUserId()` function

3. **Add login modal to index.html**
   - Include modal HTML
   - Include nostr-auth.js script
   - Wire up burger menu button to show modal

### Phase 4: User ID Handling

**Option A: Use npub directly as user_id**
- Pros: Simple, no mapping needed
- Cons: Long user_id (~63 characters)
- Implementation: `user_id = npub`

**Option B: Hash npub to create shorter user_id**
- Pros: Shorter, cleaner user_id
- Cons: Need to store mapping, more complex
- Implementation: 
  ```python
  import hashlib
  user_id = hashlib.sha256(npub.encode()).hexdigest()[:32]
  # Store mapping: user_id -> npub in database/file
  ```

**Recommendation: Option A (use npub directly)**
- Simpler implementation
- No additional storage needed
- User_id length is acceptable for file paths
- Can always hash later if needed

### Phase 5: Security Considerations

1. **nsec Storage**
   - NEVER store nsec in cookies or localStorage
   - Only send nsec to backend during login
   - Backend validates and immediately discards nsec
   - Only npub is stored in cookie

2. **Cookie Security**
   - httpOnly flag prevents XSS attacks
   - secure flag (in production)
   - SameSite protection

3. **Input Validation**
   - Validate nsec format before sending to backend
   - Sanitize all inputs
   - Rate limiting on login endpoint

4. **Key Generation**
   - Use cryptographically secure random number generator
   - Warn users to backup their nsec
   - Display seed phrase option (future enhancement)

## File Structure

```
frontend/
  js/
    nostr-auth.js          # Core authentication logic
    nostr-login-modal.js   # Login modal UI (optional, can be inline)
  index.html               # Updated with login modal
  user.html                # Updated to use Nostr auth

backend/
  app.py                   # Added auth endpoints
  nostr_utils.py           # Optional: Nostr validation utilities
```

## API Endpoints

### POST `/api/auth/nostr/login`
**Request:**
```json
{
  "nsec": "nsec1..."
}
```

**Response:**
```json
{
  "success": true,
  "npub": "npub1...",
  "userId": "npub1..." // or hashed version
}
```

### GET `/api/auth/nostr/status`
**Response:**
```json
{
  "authenticated": true,
  "npub": "npub1...",
  "userId": "npub1..."
}
```

### POST `/api/auth/nostr/logout`
**Response:**
```json
{
  "success": true
}
```

## User Flow

1. User clicks "Login" button in burger menu
2. Modal appears with options:
   - "Create New Account" - Generates new nsec/npub
   - "Import Existing Key" - Input field for nsec
3. User selects option and completes action
4. Frontend sends nsec to backend `/api/auth/nostr/login`
5. Backend validates nsec, derives npub, sets cookie
6. Frontend receives npub, stores in memory (not localStorage)
7. User is now authenticated
8. All subsequent requests use cookie for authentication
9. User ID (npub) is used for all user operations

## Migration Strategy

1. **Existing Users**
   - Users with localStorage userId can continue using it
   - Prompt them to "upgrade" to Nostr auth
   - Map old userId to new npub if they migrate

2. **Backward Compatibility**
   - Support both auth methods initially
   - Check for Nostr cookie first, fall back to localStorage
   - Gradually phase out localStorage auth

## Testing Checklist

- [ ] Generate new Nostr key pair
- [ ] Import existing nsec
- [ ] Validate nsec format
- [ ] Cookie is set correctly (httpOnly, secure)
- [ ] Authentication status check works
- [ ] Logout clears cookie
- [ ] User ID (npub) is used correctly in all operations
- [ ] Error handling for invalid nsec
- [ ] Error handling for network failures
- [ ] UI updates correctly based on auth status

## Future Enhancements

1. **Seed Phrase Support**
   - Generate seed phrase along with keys
   - Allow recovery via seed phrase

2. **Nostr Connect**
   - Support external Nostr clients (e.g., Alby, nos2x)
   - OAuth-like flow with Nostr Connect

3. **Multi-Device Support**
   - Sync projects across devices using npub
   - Cloud backup of project data

4. **Key Derivation**
   - Support BIP-32 style key derivation
   - Multiple projects per npub with different keys

## Notes

- npub format: `npub1` prefix + Bech32 encoded public key (~63 chars)
- nsec format: `nsec1` prefix + Bech32 encoded private key (~63 chars)
- Bech32 encoding is used for human-readable keys
- Private keys should NEVER be stored on server or in cookies
- Consider adding rate limiting to prevent brute force attacks
