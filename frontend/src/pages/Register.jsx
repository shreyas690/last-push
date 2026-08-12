import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { FiLock, FiUser, FiMail, FiCheckCircle, FiShield, FiArrowRight, FiArrowLeft } from 'react-icons/fi';
import FaceWebcamCapture from '../components/FaceWebcamCapture';

const Register = () => {
    const [step, setStep] = useState(1); // Step 1: Details, Step 2: Face Capture
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [capturedFaceData, setCapturedFaceData] = useState(null);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const { register } = useAuth();
    const navigate = useNavigate();

    const handleStep1Next = (e) => {
        e.preventDefault();
        setError('');

        if (!username || !password || !email) {
            setError("Username, password, and Gmail address are required.");
            return;
        }

        if (!email.toLowerCase().endsWith('@gmail.com')) {
            setError("A valid Gmail address (@gmail.com) is required for registration.");
            return;
        }

        setStep(2);
    };

    const handleFaceCaptured = async (biometricData) => {
        setError('');
        setCapturedFaceData(biometricData);
        setSubmitting(true);

        try {
            const res = await register(username, password, email, biometricData, 'User');
            setSuccessMessage(res?.message || "User registered successfully. Pending Admin approval.");
            setTimeout(() => {
                navigate('/login');
            }, 3000);
        } catch (err) {
            console.error("Registration error:", err);
            setError(err.response?.data?.error || "Registration failed. Please try again.");
            setSubmitting(false);
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
                        CYBER DEFENSE MATRIX // REGISTRATION
                    </h1>
                    <p className="text-xs text-textMuted font-mono mt-1">
                        STEP {step} OF 2: {step === 1 ? 'CREDENTIALS & GMAIL VERIFICATION' : 'BIOMETRIC FACE REGISTRATION'}
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
                    <form onSubmit={handleStep1Next} className="space-y-4">
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

                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <FiMail className="text-hackerGreen/70" />
                            </div>
                            <input
                                type="email"
                                placeholder="Gmail Address (e.g. user@gmail.com)"
                                className="input-field pl-11"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>

                        <button type="submit" className="btn-primary w-full mt-4 text-xs flex items-center justify-center gap-2">
                            Proceed to Face Registration <FiArrowRight />
                        </button>
                    </form>
                ) : (
                    <div className="space-y-4">
                        <FaceWebcamCapture 
                            onCapture={handleFaceCaptured} 
                            buttonText={submitting ? "Submitting Registration..." : "Complete Face Registration"}
                            title="Biometric Face Template Registration"
                            mode="register"
                        />

                        <button
                            type="button"
                            onClick={() => setStep(1)}
                            disabled={submitting}
                            className="btn-secondary w-full text-xs flex items-center justify-center gap-2 mt-3"
                        >
                            <FiArrowLeft /> Back to Account Details
                        </button>
                    </div>
                )}

                <p className="mt-6 text-center text-xs font-mono text-textMuted">
                    Already have clearance?{' '}
                    <Link to="/login" className="text-cyberCyan hover:underline transition-colors font-bold">
                        Initialize Session
                    </Link>
                </p>
            </motion.div>
        </div>
    );
};

export default Register;
