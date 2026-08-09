import uuid
import time
import logging
from datetime import datetime, timezone
try:
    from security_tests.tampering_test import run_tampering_test
    from security_tests.replay_test import run_replay_test
    from security_tests.mitm_test import run_mitm_test
    from security_tests.authentication_test import (
        run_authentication_test, run_packet_integrity_test, run_flooding_test
    )
    from security_tests.benchmark import measure_cryptographic_benchmark
    from security_tests.report_generator import generate_security_evaluation_report
    from ai.model_manager import ModelManager
    from models.security_test_result import SecurityTestResultModel
except ImportError:
    from backend.security_tests.tampering_test import run_tampering_test
    from backend.security_tests.replay_test import run_replay_test
    from backend.security_tests.mitm_test import run_mitm_test
    from backend.security_tests.authentication_test import (
        run_authentication_test, run_packet_integrity_test, run_flooding_test
    )
    from backend.security_tests.benchmark import measure_cryptographic_benchmark
    from backend.security_tests.report_generator import generate_security_evaluation_report
    from backend.ai.model_manager import ModelManager
    from app.models.security_test_result import SecurityTestResultModel

logger = logging.getLogger(__name__)

def execute_full_security_evaluation(scale=100, socketio=None):
    """
    Orchestrates the entire Penetration Testing & Formal Security Evaluation Framework across configurable scales (10, 50, 100, 500, 1000).
    Calculates real metrics, stores results in MongoDB SecurityTestResults, and generates research report.
    """
    exp_id = f"EXP_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:4]}"
    logger.info(f"Starting Formal Security Evaluation Experiment {exp_id} with scale={scale} per attack module...")
    
    if socketio:
        socketio.emit('security_test_update', {
            'event': 'TEST_SUITE_STARTED',
            'experimentId': exp_id,
            'scale': scale,
            'status': 'Running'
        })
        
    test_results = []
    
    # 1. Tampering Test
    logger.info("Executing Tampering Test Module...")
    res_tamper = run_tampering_test(attempts=scale, socketio=socketio)
    test_results.append(res_tamper)
    
    # 2. Replay Test
    logger.info("Executing Replay Test Module...")
    res_replay = run_replay_test(attempts=scale, socketio=socketio)
    test_results.append(res_replay)
    
    # 3. MITM Test
    logger.info("Executing MITM Test Module...")
    res_mitm = run_mitm_test(attempts=scale, socketio=socketio)
    test_results.append(res_mitm)
    
    # 4. Authentication Security Test
    logger.info("Executing Auth Security Test Module...")
    res_auth = run_authentication_test(attempts=scale, socketio=socketio)
    test_results.append(res_auth)
    
    # 5. Packet Integrity Test
    logger.info("Executing Packet Integrity Test Module...")
    res_integrity = run_packet_integrity_test(attempts=scale, socketio=socketio)
    test_results.append(res_integrity)
    
    # 6. Flooding Test
    logger.info("Executing Controlled Flooding Test Module...")
    res_flood = run_flooding_test(attempts=scale, socketio=socketio)
    test_results.append(res_flood)
    
    # 7. Measure Performance & Cryptographic Benchmark
    logger.info("Measuring Cryptographic Benchmark Overhead...")
    bench = measure_cryptographic_benchmark(iterations=min(scale, 100))
    
    # Aggregate Metrics Calculation
    total_detected = sum(r['detectedAttempts'] for r in test_results)
    total_attempts = sum(r['totalAttempts'] for r in test_results)
    total_missed = sum(r['missedAttempts'] for r in test_results)
    total_fp = sum(r['falsePositives'] for r in test_results)
    
    overall_detection_rate = round((total_detected / max(1, total_attempts)) * 100, 2)
    overall_fpr = round((total_fp / max(1, total_attempts)) * 100, 2)
    overall_fnr = round((total_missed / max(1, total_attempts)) * 100, 2)
    avg_latency = round(sum(r['avgLatencyMs'] for r in test_results) / len(test_results), 2)
    
    current_model = ModelManager.get_current_active_version()
    ai_ver = current_model.get("version", "v1") if current_model else "v1"
    
    # Save to MongoDB
    for res in test_results:
        SecurityTestResultModel.save_experiment_results(
            experiment_id=exp_id,
            attack_type=res['attackType'],
            total_attempts=res['totalAttempts'],
            detected_attempts=res['detectedAttempts'],
            missed_attempts=res['missedAttempts'],
            false_positives=res['falsePositives'],
            detection_rate=res['detectionRate'],
            false_positive_rate=res['falsePositiveRate'],
            false_negative_rate=res['falseNegativeRate'],
            avg_latency_ms=res['avgLatencyMs'],
            min_latency_ms=res['minLatencyMs'],
            max_latency_ms=res['maxLatencyMs'],
            encryption_overhead_ms=bench['avgEncryptionTimeMs'],
            cpu_usage_pct=bench['cpuUsagePct'],
            memory_usage_mb=bench['memoryUsageMb'],
            system_version="1.0.0",
            ai_model_version=ai_ver
        )
        
    summary_report_input = {
        "experimentId": exp_id,
        "systemVersion": "1.0.0",
        "aiModelVersion": ai_ver,
        "scaleAttempts": scale,
        "overallDetectionRate": overall_detection_rate,
        "overallFalsePositiveRate": overall_fpr,
        "overallFalseNegativeRate": overall_fnr,
        "avgDetectionLatencyMs": avg_latency,
        "securityOverheadPct": bench['securityOverheadPct'],
        "cpuUsagePct": bench['cpuUsagePct'],
        "memoryUsageMb": bench['memoryUsageMb'],
        "results": test_results
    }
    
    report_res = generate_security_evaluation_report(summary_report_input)
    
    if socketio:
        socketio.emit('security_test_update', {
            'event': 'TEST_SUITE_COMPLETED',
            'experimentId': exp_id,
            'summary': summary_report_input
        })
        socketio.emit('dashboard_update', {'type': 'SECURITY_TEST_COMPLETED'})
        
    logger.info(f"Completed Formal Security Evaluation Experiment {exp_id}.")
    return summary_report_input
