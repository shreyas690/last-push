# Setup & Execution Guide

## Prerequisites
- Node.js (v18+)
- Python (3.12+)
- MongoDB (Running locally on default port 27017, or update `.env` with Atlas URI)

## 1. MongoDB Setup
Ensure MongoDB is running locally:
```bash
# Windows (If running as service, it should already be up)
# Verify connection using MongoDB Compass: mongodb://localhost:27017
```

## 2. Backend Setup
Open a terminal and navigate to the backend directory:
```powershell
cd morse-secure-comm/backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python run.py
```
*The backend runs on http://localhost:5000*

## 3. Frontend Setup
Open a new terminal and navigate to the frontend directory:
```powershell
cd morse-secure-comm/frontend
npm install
npm run dev
```
*The frontend runs on http://localhost:5173*

## 4. Demo Instructions (Conference Flow)
1. **Initialize**: Open the frontend URL.
2. **Register**: Create two users (User A: Sender, User B: Receiver) and an Admin.
3. **Session**: Log in as Sender. Open an incognito window and log in as Receiver. Go to `/chat`.
4. **Communicate**: Use the Spacebar or input box to send Morse code. Notice the AES-256 GCM encryption visualizer.
5. **Attack Simulation**: Log in as Admin. Navigate to `/attack` (Simulator) and trigger a Replay or Tampering attack.
6. **Defense**: Show the AI model blocking the attack in real-time.
7. **Monitoring**: Navigate to `/dashboard` to show the active real-time stats and packet loss graphs.
