import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { FiLock, FiUser, FiShield, FiCheckCircle, FiArrowRight, FiArrowLeft } from 'react-icons/fi';
import FaceWebcamCapture from '../components/FaceWebcamCapture';

const Login = () => {
    const [step, setStep] = useState(1); // Step 1: Username/Password, Step 2: Face Verification
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');
    const [verifying, setVerifying] = useState(false);

    const { login, verifyFace } = useAuth();
    const navigate = useNavigate();

    const handleStep1Login = async (e) => {
        e.preventDefault();
        setError('');

        try {
            const res = await login(username, password);
            
            // If user is Admin or login completed directly
            if (res.user && res.user.role === 'Admin') {
                navigate('/dashboard');
                return;
            }

            // If user requires Step 2: Biometric Face Verification
            if (res.requiresFaceVerification) {
                setStep(2);
            } else if (res.user) {
                navigate('/terminal');
            }
        } catch (err) {
            console.error("Login Step 1 error:", err);
            setError(err.response?.data?.error || 'Invalid username or password.');
        }
    };

    const handleFaceVerification = async (biometricData) => {
        setError('');
        setVerifying(true);

        try {
            const loggedInUser = await verifyFace(username, biometricData);
            setSuccessMessage("Face verification successful. Access granted.");
            setTimeout(() => {
                if (loggedInUser.role === 'Admin') {
                    navigate('/dashboard');
                } else {
                    navigate('/terminal');
                }
            }, 1000);
        } catch (err) {
            console.error("Face verification error:", err);
            setError(err.response?.data?.error || "Face verification failed. Please try again.");
            setVerifying(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4">
            <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="glass-panel p-8 w-full max-w-lg border border-hackerGreen/30 shadow-neon-green"
            >
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-hackerGreen/10 border border-hackerGreen/40 text-hackerGreen mb-3 shadow-neon-green">
                        <FiShield className="text-2xl" />
                    </div>
                    <h1 className="text-2xl font-bold text-hackerGreen glow-text-green tracking-wide uppercase font-mono">
                        CYBER DEFENSE MATRIX // AUTHENTICATION
                    </h1>
                    <p className="text-xs text-textMuted font-mono mt-1">
                        STEP {step} OF 2: {step === 1 ? 'USERNAME & PASSWORD VERIFICATION' : 'BIOMETRIC FACE AUTHENTICATION'}
                    </p>
                </div>

                {error && (
                    <div className="bg-cyberRed/10 border border-cyberRed/50 text-cyberRed px-4 py-3 rounded-lg mb-6 text-xs font-mono">
                        {error}
                    </div>
                )}

                {successMessage && (
                    <div className="bg-hackerGreen/10 border border-hackerGreen/50 text-hackerGreen px-4 py-3 rounded-lg mb-6 text-xs font-mono flex items-center gap-2">
                        <FiCheckCircle className="text-base" /> {successMessage}
                    </div>
                )}

                {step === 1 ? (
                    <form onSubmit={handleStep1Login} className="space-y-4">
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <FiUser className="text-hackerGreen/70" />
                            </div>
                            <input
                                type="text"
                                placeholder="Username"
                                className="input-field pl-11"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                            />
                        </div>

                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <FiLock className="text-hackerGreen/70" />
                            </div>
                            <input
                                type="password"
                                placeholder="Password"
                                className="input-field pl-11"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>

                        <button type="submit" className="btn-primary w-full mt-4 text-xs flex items-center justify-center gap-2">
                            Verify Password & Continue <FiArrowRight />
                        </button>
                    </form>
                ) : (
                    <div className="space-y-4">
                        <FaceWebcamCapture 
                            onCapture={handleFaceVerification} 
                            buttonText={verifying ? "Verifying Face Template..." : "Verify Face Biometrics"}
                            title="Biometric Face Authentication"
                            mode="verify"
                        />

                        <button
                            type="button"
                            onClick={() => setStep(1)}
                            disabled={verifying}
                            className="btn-secondary w-full text-xs flex items-center justify-center gap-2 mt-3"
                        >
                            <FiArrowLeft /> Back to Password Entry
                        </button>
                    </div>
                )}

                <p className="mt-6 text-center text-xs font-mono text-textMuted">
                    Don't have clearance?{' '}
                    <Link to="/register" className="text-cyberCyan hover:underline transition-colors font-bold">
                        Request Access
                    </Link>
                </p>
            </motion.div>
        </div>
    );
};

export default Login;
