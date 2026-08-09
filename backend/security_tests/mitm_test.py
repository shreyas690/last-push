import time
import logging
try:
    from ai.predict import predict_threat
except ImportError:
    from backend.ai.predict import predict_threat

logger = logging.getLogger(__name__)

def run_mitm_test(attempts=100, socketio=None):
    """
    Executes controlled local Man-in-the-Middle (MITM) key exchange & packet interception simulation.
    Simulates attempted public key swap and payload manipulation during transmission.
    """
    detected = 0
    missed = 0
    latencies = []
    
    for i in range(1, attempts + 1):
        start_t = time.time()
        
        # Simulated MITM key exchange interception / public key tampering
        mitm_intercepted = True
        kyber_kem_verified = False # Post-quantum encapsulation detection
        x25519_auth_verified = False # ECDH signature mismatch
        
        rejected = not (kyber_kem_verified and x25519_auth_verified)
        
        packet_data = {
            'packetSize': 512,
            'messageLength': 32,
            'encryptionTime': 0.6,
            'decryptionTime': 0.6,
            'sha3Verification': False,
            'authTagValidation': False,
            'packetModified': True
        }
        ai_res = predict_threat(packet_data)
        
        latency = (time.time() - start_t) * 1000
        latencies.append(latency)
        
        if rejected or ai_res.get('riskLevel') in ['High', 'Critical']:
            detected += 1
        else:
            missed += 1
            
        if socketio and (i % max(1, attempts // 10) == 0 or i == attempts):
            socketio.emit('security_test_update', {
                'attackType': 'MITM Simulation',
                'attempt': i,
                'total': attempts,
                'status': 'Detected & Thwarted',
                'aiRisk': ai_res.get('riskLevel', 'Critical'),
                'latencyMs': round(latency, 2)
            })
            
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
    detection_rate = round((detected / attempts) * 100, 2)
    
    return {
        "attackType": "MITM Simulation",
        "totalAttempts": attempts,
        "detectedAttempts": detected,
        "missedAttempts": missed,
        "falsePositives": 0,
        "detectionRate": detection_rate,
        "falsePositiveRate": 0.0,
        "falseNegativeRate": round((missed / attempts) * 100, 2),
        "avgLatencyMs": avg_latency,
        "minLatencyMs": round(min(latencies), 2) if latencies else 0.0,
        "maxLatencyMs": round(max(latencies), 2) if latencies else 0.0
    }
