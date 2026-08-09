# Defense-Grade Secure Morse Communication System
**Using AES-GCM Encryption and SHA-3 Based Integrity Verification**

## Abstract
This project presents a highly secure, modular communication platform utilizing Morse code as the underlying transmission protocol, hardened by defense-grade cryptographic primitives. Built as a Final Year Engineering Project, the system replaces traditional vulnerable chat applications with a robust Mailbox architecture, ensuring confidentiality through AES-256 GCM, integrity via SHA3-512, and forward secrecy using X25519 and CRYSTALS-Kyber hybrid key exchange.

## System Architecture

The platform follows a modern microservices-inspired monolithic architecture:

### 1. Frontend (React + Vite + TailwindCSS + Framer Motion)
- **Glassmorphism UI**: A dark, cyber-defense themed aesthetic.
- **Real-Time Client**: Socket.IO integrated event listeners for live metrics and messaging.
- **Educational Visualizer**: Interactive module demonstrating MITM, Tampering, Sniffing, and Replay attacks layer-by-layer.

### 2. Backend (Flask + WebSockets + PyMongo)
- **RESTful API**: Standardized endpoints for Authentication (JWT) and Admin operations.
- **WebSocket Engine**: Real-time Socket.IO pipelines for instant message delivery and dashboard broadcasting.
- **Cryptographic Engine**: Integration layer handling AES, SHA3, and Kyber post-quantum algorithms.
- **AI Threat Model**: Predictive heuristics analyzing packet timestamp deltas, auth tag validations, and packet sizes.

### 3. Database (MongoDB)
- **Collections**: Users, Sessions, Messages, AttackLogs, SecurityLogs.
- **Indexing**: Optimized schema for high-throughput live dashboard aggregations.

## Security Features

1. **Authentication & Access Control**
   - Single Root System Admin (`admin@morsecom.com`).
   - Role-Based Access Control (Admin, Sender, Receiver).
   - Strict Approval Workflow: Agents remain in `Pending` state until explicitly approved by the Admin.

2. **Multi-Layer Cryptography**
   - **Layer 1: Key Exchange**: X25519 Elliptic Curve Diffie-Hellman combined with CRYSTALS-Kyber for Post-Quantum encapsulation.
   - **Layer 2: Payload Encryption**: AES-256 GCM ensuring authenticated encryption with associated data.
   - **Layer 3: Integrity**: SHA3-512 cryptographic hashing to prevent packet tampering.
   - **Layer 4: Threat Detection**: Timestamp validation preventing Replay Attacks.

## Modules Overview

- **Admin Dashboard**: Live Command Center showing active agents, encryption throughput matrices, and a real-time security event feed.
- **Secure Mailbox**: A Gmail-like interface allowing Agents to compose plaintext, view real-time Morse translation, encrypt, and transmit instantly to approved peers.
- **Attack Matrix**: A purely educational module visually simulating how the architecture mitigates Sniffing, Tampering, Replay, and MITM vectors.

## Running the Application Locally

### Requirements
- Python 3.10+
- Node.js 18+
- MongoDB instance (running locally at `mongodb://localhost:27017`)

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```
*Note: The System Admin account (`admin@morsecom.com`, Password: `admin123`) is automatically generated on startup.*

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Future Scope (Hardware Integration)
The platform is designed to be hardware-agnostic. The WebSocket engine can easily emit Morse payloads (`.` and `-`) to an ESP32 or Raspberry Pi connected via serial or MQTT to actuate physical LEDs or buzzers in real-time.
