import React, { useRef, useState, useEffect } from 'react';
import { FiCamera, FiCheck, FiAlertCircle, FiRefreshCw, FiShield, FiUserCheck } from 'react-icons/fi';
import { extractFaceBiometricsFromVideo } from '../utils/faceBiometrics';

const FaceWebcamCapture = ({ onCapture, buttonText = "Capture Face", title = "Face Registration", mode = "register" }) => {
    const videoRef = useRef(null);
    const [cameraActive, setCameraActive] = useState(false);
    const [cameraError, setCameraError] = useState('');
    const [statusMessage, setStatusMessage] = useState('Position your face inside the frame.');
    const [faceDetected, setFaceDetected] = useState(false);
    const [processing, setProcessing] = useState(false);

    useEffect(() => {
        let stream = null;
        const startCamera = async () => {
            try {
                setCameraError('');
                setStatusMessage('Initializing camera...');
                stream = await navigator.mediaDevices.getUserMedia({
                    video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
                });
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    setCameraActive(true);
                    setStatusMessage('Camera active. Position your face inside the frame.');
                }
            } catch (err) {
                console.error("Camera access error:", err);
                setCameraError("Camera access is required for face registration.");
                setStatusMessage("Camera access is required for face registration.");
            }
        };

        startCamera();

        return () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    // Periodic detection loop for real-time visual feedback
    useEffect(() => {
        if (!cameraActive) return;

        const interval = setInterval(() => {
            if (videoRef.current && videoRef.current.readyState >= 2) {
                const res = extractFaceBiometricsFromVideo(videoRef.current);
                if (res.success && res.faceCount === 1) {
                    setFaceDetected(true);
                    setCameraError('');
                    setStatusMessage("Valid face detected. Click button to complete.");
                } else {
                    setFaceDetected(false);
                    if (res.error) {
                        setCameraError(res.error);
                    }
                }
            }
        }, 600);

        return () => clearInterval(interval);
    }, [cameraActive]);

    const handleActionClick = () => {
        if (!videoRef.current) return;

        setProcessing(true);
        const biometricResult = extractFaceBiometricsFromVideo(videoRef.current);

        if (!biometricResult.success || biometricResult.faceCount !== 1) {
            setCameraError(biometricResult.error || "No face was detected. Please position your face inside the frame.");
            setProcessing(false);
            return;
        }

        setCameraError('');
        setStatusMessage("Biometric feature template extracted successfully.");
        onCapture(biometricResult);
        setProcessing(false);
    };

    return (
        <div className="glass-panel p-6 border border-hackerGreen/30 flex flex-col items-center">
            <div className="flex items-center justify-between w-full mb-4 border-b border-hackerGreen/20 pb-3">
                <h3 className="text-sm font-bold text-hackerGreen glow-text-green font-mono uppercase flex items-center gap-2">
                    <FiShield /> {title}
                </h3>
                <span className={`text-[11px] font-mono px-2.5 py-1 rounded-md border ${
                    cameraActive ? 'bg-hackerGreen/10 text-hackerGreen border-hackerGreen/40' : 'bg-cyberRed/10 text-cyberRed border-cyberRed/40'
                }`}>
                    {cameraActive ? 'CAMERA: ACTIVE' : 'CAMERA: OFF'}
                </span>
            </div>

            {/* Webcam Video Box with Hacker Cyber Overlay Frame */}
            <div className="relative w-full max-w-[360px] aspect-[4/3] bg-background/90 rounded-xl overflow-hidden border-2 border-hackerGreen/40 shadow-neon-green mb-4">
                <video
                    ref={videoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover transform -scale-x-100"
                />

                {/* Oval Face Bounding Frame Overlay */}
                <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                    <div className={`w-[60%] h-[75%] rounded-[50%] border-2 ${
                        faceDetected ? 'border-hackerGreen shadow-neon-green' : 'border-yellow-400/60'
                    } transition-all duration-300 relative flex items-center justify-center`}>
                        <div className="absolute -top-3 bg-background/90 text-[10px] font-mono px-2 py-0.5 rounded border border-white/10 text-textMuted">
                            FACE TARGET AREA
                        </div>
                    </div>
                </div>

                {/* Status Indicator Badge */}
                <div className="absolute bottom-2 left-2 right-2 bg-background/90 backdrop-blur-md p-2 rounded border border-white/10 text-center text-[11px] font-mono">
                    {cameraError ? (
                        <span className="text-cyberRed flex items-center justify-center gap-1 font-bold">
                            <FiAlertCircle /> {cameraError}
                        </span>
                    ) : (
                        <span className="text-hackerGreen flex items-center justify-center gap-1">
                            <FiCheck /> {statusMessage}
                        </span>
                    )}
                </div>
            </div>

            {/* Action Button */}
            <button
                type="button"
                onClick={handleActionClick}
                disabled={!cameraActive || processing}
                className="btn-primary w-full max-w-[360px] text-xs flex items-center justify-center gap-2 py-3"
            >
                {processing ? (
                    <>
                        <FiRefreshCw className="animate-spin" /> Processing Biometric Template...
                    </>
                ) : (
                    <>
                        <FiUserCheck /> {buttonText}
                    </>
                )}
            </button>
        </div>
    );
};

export default FaceWebcamCapture;
