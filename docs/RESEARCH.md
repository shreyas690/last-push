# Research Materials

## 1. Abstract
The rapid advancement of quantum computing poses a critical threat to classical cryptographic systems. In response, this project proposes a Defense-Grade Secure Communication System utilizing hybrid Post-Quantum Cryptography (PQC). We implement a simulated integration of CRYSTALS-Kyber Key Encapsulation alongside classical X25519 ECDH, securing payloads with AES-256 GCM and verifying integrity via SHA3-512. Uniquely, the system translates physical Morse code inputs into secure digital packets, evaluated in real-time by an AI-driven Random Forest Threat Detector. The platform successfully mitigates Replay and Man-in-the-Middle (MITM) attacks while maintaining sub-50ms encryption latency, providing a robust architecture for next-generation secure military and industrial communications.

## 2. IEEE Paper Outline
- **I. Introduction**
  - Background on Quantum Threats
  - Motivation for Morse Code in Low-Bandwidth Scenarios
- **II. Literature Review**
  - Existing AES-GCM implementations
  - Post-Quantum Cryptography (Kyber KEM)
  - Machine Learning in Intrusion Detection Systems (IDS)
- **III. Proposed Methodology**
  - System Architecture (React, Flask, SocketIO)
  - Hybrid Cryptographic Engine Design
  - AI Threat Model Features (Time Delta, Sequence, Auth Fails)
- **IV. Implementation Details**
  - Key derivation and Forward Secrecy
  - Real-time Morse Audio Synthesis and Encoding
  - Attack Simulation Environment
- **V. Results & Analysis**
  - Encryption/Decryption Latency Benchmarks
  - AI Model Accuracy (Precision/Recall on synthetic MITM data)
  - Dashboard Metrics
- **VI. Conclusion & Future Work**
  - Hardware integration (ESP32)
  - Real-world Kyber benchmarking

## 3. Future Enhancements
- Full C++ hardware implementation for ESP32 transceivers.
- Training the AI model on real-world Wireshark packet captures instead of synthetic data.
- Implementing fully decentralized WebRTC channels instead of a central SocketIO relay.
