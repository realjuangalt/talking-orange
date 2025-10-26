# Talking Orange - Bitcoin AR Experience

An augmented reality application that brings a 3D talking orange character to life through marker-based AR and voice interaction, designed for Bitcoin education and evangelism.

## 🎯 Project Overview

This project creates an AR experience where users:
1. Point their camera at a printed talking orange marker
2. See a 3D talking orange character projected onto the marker
3. Interact with the character through voice commands about Bitcoin
4. Receive audio responses with synchronized mouth animations

## 🛠️ Technology Stack

### Frontend
- **HTML5, CSS3, Vanilla JavaScript** - Web Standards
- **MindAR** - Modern marker-based AR framework (MIT License)
- **A-Frame** - Web framework for VR/AR (MIT License)
- **Three.js** - 3D rendering (MIT License)
- **Web Speech API** - Voice recognition and synthesis
- **MediaRecorder API** - Audio recording

### Backend
- **Python Flask** - Web framework (BSD License)
- **Whisper** - Speech-to-text (MIT License)
- **OpenAI API** - LLM for Bitcoin responses
- **Text-to-Speech** - Audio response generation

### AR Assets
- **Custom PNG Images** - Talking orange character with mouth states
- **MindAR Targets** - Compiled `.mind` files for marker detection

## 📋 Current Status

### ✅ **CONFIRMED WORKING**

#### **Core Application Infrastructure**
- [x] **Welcome Screen & UI** - Clean, centered interface with permission explanations
- [x] **Camera & Microphone Permissions** - Proper permission flow and error handling
- [x] **Screen Management** - Smooth transitions between welcome, camera, and error screens
- [x] **Status Indicators** - Real-time camera and microphone status display

#### **Audio System**
- [x] **Audio Recording** - MediaRecorder API integration for voice capture
- [x] **Backend Communication** - Flask API for processing audio data
- [x] **Speech-to-Text** - Whisper integration for voice recognition
- [x] **LLM Integration** - OpenAI API for Bitcoin-related responses
- [x] **Text-to-Speech** - Audio response generation and playback
- [x] **Session Management** - Proper session handling and data flow

#### **AR Infrastructure**
- [x] **MindAR Integration** - A-Frame and MindAR framework loading
- [x] **Marker Detection** - Successfully detects the talking orange marker
- [x] **Scene Creation** - AR scene initialization and camera setup
- [x] **Asset Loading** - PNG images loaded correctly (base, half-open mouth, wide-open mouth)
- [x] **Event System** - `targetFound` and `targetLost` events working
- [x] **Talking Animation System** - Mouth state cycling logic implemented

#### **Modular Architecture**
- [x] **UIManager** - Handles all UI elements and screen transitions
- [x] **CameraManager** - Manages camera/microphone permissions and access
- [x] **AudioManager** - Handles recording, backend communication, audio playback
- [x] **MindARManager** - Dedicated AR functionality management
- [x] **Application Coordinator** - Orchestrates all modules

### ❌ **NOT CONFIRMED WORKING**

#### **AR Image Projection**
- [ ] **Transparent PNG Projection** - The talking orange image is not visible on the marker
- [ ] **Visual Feedback** - No visual confirmation that the AR overlay is working
- [ ] **Asset Positioning** - Image positioning and scaling on the marker

#### **Animation Integration**
- [ ] **Mouth Animation Triggering** - Talking animation not triggered by voice responses
- [ ] **Synchronized Audio/Visual** - Audio playback and mouth movement not synchronized

## 🎯 **CURRENT FOCUS**

**Primary Goal**: Get the transparent PNG image to project onto the marker in AR

**Secondary Goals**:
- Integrate talking animation with voice responses
- Ensure smooth audio-visual synchronization
- Optimize AR performance and stability

## 🔧 **Technical Details**

### **Working Components**
- **Permission System**: Robust camera/microphone access with proper error handling
- **Audio Pipeline**: Complete voice-to-text-to-speech workflow
- **Backend API**: Flask server with Whisper, OpenAI, and TTS integration
- **AR Detection**: MindAR successfully identifies the marker
- **Modular Code**: Clean separation of concerns for easy debugging

### **Current Issue**
The MindAR system detects the marker correctly but the `a-plane` element with the talking orange PNG is not visible. This appears to be a rendering or positioning issue within the A-Frame/MindAR setup.

### **Debugging Approach**
- Modular architecture allows isolated testing of AR components
- Global access to `window.mindar` for console debugging
- Exact replication of working `mindar-local.html` configuration
- Comprehensive logging throughout the AR pipeline

## 📁 Project Structure

```
talking-orange/
├── frontend/
│   ├── index.html          # Main application (modular architecture)
│   ├── mindar-local.html   # Working AR test page
│   ├── css/style.css       # Styling
│   └── targets.mind        # Compiled MindAR marker file
├── backend/
│   ├── app.py             # Flask server with API endpoints
│   └── venv/              # Python virtual environment
├── talking-orange-transparent.png      # Base character image
├── talking-orange-half-open-mouth.png  # Half-open mouth state
├── talking-orange-open-mouth.png       # Wide-open mouth state
└── README.md
```

## 🚀 Getting Started

### **Prerequisites**
- Python 3.x with Flask
- Modern web browser with camera/microphone support
- HTTPS or localhost (required for camera access)

### **Setup**
1. **Backend**: 
   ```bash
   cd backend
   source venv/bin/activate
   python app.py
   ```

2. **Frontend**: 
   - Navigate to `http://localhost:3000`
   - Grant camera and microphone permissions
   - Point camera at the talking orange marker

### **Testing**
- **AR Detection**: Console logs show "Target found!" when marker is detected
- **Audio System**: Microphone button records and processes voice input
- **Backend**: API endpoints respond with Bitcoin-related audio

## 🔒 License Compliance

All technologies used are open source and allow commercial use:
- **MIT License**: MindAR, A-Frame, Three.js, Whisper
- **BSD License**: Flask
- **Web Standards**: HTML5, CSS3, JavaScript, Web APIs

## 📄 License

This project is proprietary. All rights reserved.

---

**Note**: This is a Bitcoin evangelism tool with patent and copyright protection.