import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { motion } from 'framer-motion';
import { FiLock, FiUser, FiShield } from 'react-icons/fi';

const Register = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('User');
    const [error, setError] = useState('');
    const { register } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await register(username, password, role);
            navigate('/login');
        } catch (err) {
            setError(err.response?.data?.error || 'Registration failed');
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4">
            <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="glass-panel p-8 w-full max-w-md"
            >
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">Secure Morse Communication</h1>
                    <p className="text-text-muted">Create your user identity</p>
                </div>

                {error && (
                    <div className="bg-danger/20 border border-danger/50 text-danger px-4 py-3 rounded-lg mb-6 text-sm">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div className="relative">
                        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                            <FiUser className="text-textMuted" />
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
                            <FiLock className="text-textMuted" />
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
                    

                    <button type="submit" className="btn-primary w-full mt-4">
                        Submit Request
                    </button>
                </form>

                <p className="mt-6 text-center text-sm text-textMuted">
                    Already have clearance?{' '}
                    <Link to="/login" className="text-primary hover:text-primaryDark transition-colors">
                        Initialize Session
                    </Link>
                </p>
            </motion.div>
        </div>
    );
};

export default Register;
