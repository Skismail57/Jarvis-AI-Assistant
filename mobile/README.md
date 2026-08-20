# Jarvis Mobile Companion App

React Native mobile app for Jarvis AI assistant - control your Jarvis assistant from anywhere.

## Features

- **Voice Chat**: Real-time voice interaction with Jarvis
- **Text Chat**: Text-based communication
- **System Metrics**: View CPU, RAM, and system status
- **Reminders**: Manage and view reminders
- **Profiles**: Switch between user profiles
- **Push Notifications**: Get reminder notifications
- **Remote Control**: Execute commands remotely

## Prerequisites

- Node.js 16+
- React Native CLI
- Android Studio (for Android development)
- Xcode (for iOS development, macOS only)

## Installation

```bash
cd mobile
npm install
```

## Running on Android

```bash
npm run android
```

## Running on iOS

```bash
cd ios
pod install
cd ..
npm run ios
```

## Configuration

Edit `src/config.js` to set your Jarvis server URL:

```javascript
export const JARVIS_SERVER_URL = 'http://YOUR_SERVER_IP:8000';
export const WS_CHAT_URL = 'ws://YOUR_SERVER_IP:8000/ws/chat';
export const WS_METRICS_URL = 'ws://YOUR_SERVER_IP:8000/ws/metrics';
```

## Architecture

- **WebSocket Connection**: Real-time chat and metrics streaming
- **Async Storage**: Local data persistence
- **React Navigation**: Screen navigation
- **Expo**: Managed React Native workflow (optional)

## Development Notes

This is a skeleton app that can be expanded with:
- Biometric authentication
- Background voice recognition
- Local wake word detection
- Offline mode support
- More sophisticated UI components
