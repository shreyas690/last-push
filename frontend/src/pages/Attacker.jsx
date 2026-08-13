import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiAlertTriangle, FiActivity, FiShield, FiLock, FiCpu, FiHash, FiZap } from 'react-icons/fi';

const Attacker = () => {
    const [activeAttack, setActiveAttack] = useState(null);
    const [simulationStep, setSimulationStep] = useState(0);

    const attackVectors = [
        { id: 'sniff', name: 'Ciphertext Capture (Sniffing)', desc: 'Attacker passively captures the encrypted packets over the network.' },
        { id: 'tamper', name: 'Packet Tampering (Modification)', desc: 'Attacker modifies a single byte in the ciphertext to change the message.' },
        { id: 'replay', name: 'Replay Attack', desc: 'Attacker captures a valid packet and resends it later to duplicate an action.' },
        { id: 'mitm', name: 'Man-in-the-Middle (MITM)', desc: 'Attacker attempts to intercept and replace the public keys during Key Exchange.' },
    ];

    const runSimulation = (attackId) => {
        setActiveAttack(attackId);
        setSimulationStep(0);
        
        // Progress through simulation steps automatically for educational purposes
        let step = 0;
        const interval = setInterval(() => {
            step += 1;
            setSimulationStep(step);
            if (step >= 5) {
                clearInterval(interval);
            }
        }, 2000);
    };

    const renderLayerVisualization = () => {
        if (!activeAttack) return <div className="text-center text-text-muted mt-20">Select an attack vector to begin the simulation.</div>;

        return (
            <div className="space-y-6">
                {/* Layer 1: X25519 & Kyber Key Exchange */}
                <motion.div initial={{opacity: 0, y: 10}} animate={{opacity: simulationStep >= 1 ? 1 : 0.3, y: 0}} className="bg-surface/50 p-4 rounded-lg border border-white/10">
                    <h3 className="font-bold flex items-center gap-2 mb-2 text-yellow-400"><FiZap/> Layer 1: Key Exchange (X25519 + CRYSTALS-Kyber)</h3>
                    <div className="text-sm font-mono text-text-muted flex justify-between">
                        <span>Alice PubKey &rarr;</span>
                        <span className={activeAttack === 'mitm' && simulationStep >= 1 ? "text-danger" : ""}>
                            {activeAttack === 'mitm' && simulationStep >= 1 ? "MITM: Keys Intercepted & Replaced!" : "Secure Exchange"}
                        </span>
                        <span>&larr; Bob PubKey</span>
                    </div>
                    {activeAttack === 'mitm' && simulationStep >= 2 && (
                        <div className="mt-2 text-xs text-primary bg-primary/10 p-2 rounded">
                            <FiShield className="inline mr-1"/> Defense: Kyber Post-Quantum encapsulation verifies the true recipient. MITM attempt thwarted.
                        </div>
                    )}
                </motion.div>

                {/* Layer 2: AES-256 GCM Encryption */}
                <motion.div initial={{opacity: 0, y: 10}} animate={{opacity: simulationStep >= 2 ? 1 : 0.3, y: 0}} className="bg-surface/50 p-4 rounded-lg border border-white/10">
                    <h3 className="font-bold flex items-center gap-2 mb-2 text-accent"><FiLock/> Layer 2: AES-256 GCM Payload</h3>
                    <div className="grid grid-cols-4 gap-2 text-xs font-mono text-center">
                        <div className="p-2 bg-black/30 rounded">Plaintext<br/>"HELLO"</div>
                        <div className="p-2 bg-black/30 rounded">&rarr; Encrypt &rarr;</div>
                        <div className={`p-2 bg-black/30 rounded ${activeAttack === 'sniff' && simulationStep >= 2 ? 'border border-danger text-danger' : ''}`}>
                            Ciphertext<br/>{activeAttack === 'tamper' && simulationStep >= 3 ? '0x8F (Modified)' : '0x4A'}
                        </div>
                        <div className="p-2 bg-black/30 rounded">Auth Tag<br/>0xAB12</div>
                    </div>
                    {activeAttack === 'sniff' && simulationStep >= 3 && (
                        <div className="mt-2 text-xs text-primary bg-primary/10 p-2 rounded">
                            <FiShield className="inline mr-1"/> Defense: Attacker captured Ciphertext, but without the Session Key, it remains mathematically unbreakable.
                        </div>
                    )}
                </motion.div>

                {/* Layer 3: SHA3-512 Integrity */}
                <motion.div initial={{opacity: 0, y: 10}} animate={{opacity: simulationStep >= 3 ? 1 : 0.3, y: 0}} className="bg-surface/50 p-4 rounded-lg border border-white/10">
                    <h3 className="font-bold flex items-center gap-2 mb-2 text-blue-400"><FiHash/> Layer 3: SHA3-512 Integrity</h3>
                    <div className="text-sm font-mono flex flex-col gap-1">
                        <span className="text-text-muted">Original Hash: a8f5c...99b2</span>
                        <span className="text-text-muted">Received Hash: {activeAttack === 'tamper' && simulationStep >= 4 ? <span className="text-danger">b3d1f...44a1</span> : 'a8f5c...99b2'}</span>
                        <div className="mt-1">
                            {activeAttack === 'tamper' && simulationStep >= 4 ? (
                                <span className="text-danger font-bold uppercase">&times; Integrity Verification Failed. Authentication Failed.</span>
                            ) : (
                                <span className="text-accent font-bold uppercase">&check; Comparison Match. Integrity Verified.</span>
                            )}
                        </div>
                    </div>
                </motion.div>

                {/* Layer 4: AI Replay Defense */}
                <motion.div initial={{opacity: 0, y: 10}} animate={{opacity: simulationStep >= 4 ? 1 : 0.3, y: 0}} className="bg-surface/50 p-4 rounded-lg border border-white/10">
                    <h3 className="font-bold flex items-center gap-2 mb-2 text-purple-400"><FiCpu/> Layer 4: AI Threat Detection</h3>
                    <div className="text-sm font-mono">
                        <div className="flex justify-between mb-1 text-text-muted">
                            <span>Packet Timestamp Delta:</span>
                            <span className={activeAttack === 'replay' ? "text-danger" : ""}>{activeAttack === 'replay' ? "600,000 ms" : "45 ms"}</span>
                        </div>
                        {activeAttack === 'replay' && simulationStep >= 5 && (
                            <div className="mt-2 text-xs text-danger font-bold bg-danger/10 p-2 rounded uppercase tracking-wider">
                                <FiAlertTriangle className="inline mr-1"/> Replay Attack Detected. Message Rejected.
                            </div>
                        )}
                        {activeAttack !== 'replay' && simulationStep >= 5 && (
                            <div className="mt-2 text-xs text-primary font-bold bg-primary/10 p-2 rounded uppercase tracking-wider">
                                <FiCheckCircle className="inline mr-1"/> Threat Model: Normal. Packet Accepted.
                            </div>
                        )}
                    </div>
                </motion.div>
            </div>
        );
    };

    return (
        <div className="min-h-screen p-6 bg-[#050505]">
            <header className="mb-8 border-b border-danger/20 pb-4">
                <h1 className="text-3xl font-bold text-danger flex items-center gap-3">
                    <FiAlertTriangle /> Educational Attack Matrix
                </h1>
                <p className="text-text-muted mt-2">Simulate and visualize how the Defense-Grade architecture mitigates quantum and classical threats.</p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="glass-panel border-danger/30 p-6 col-span-1 h-fit">
                    <h2 className="text-xl font-bold mb-6 flex items-center gap-2"><FiActivity /> Select Threat Vector</h2>
                    
                    <div className="space-y-3">
                        {attackVectors.map(attack => (
                            <button 
                                key={attack.id}
                                onClick={() => runSimulation(attack.id)}
                                className={`w-full text-left p-4 rounded-lg border transition-all ${activeAttack === attack.id ? 'bg-danger/20 border-danger text-white' : 'bg-surface border-white/5 text-text-muted hover:bg-white/5'}`}
                            >
                                <h3 className="font-bold mb-1">{attack.name}</h3>
                                <p className="text-xs opacity-80 leading-relaxed">{attack.desc}</p>
                            </button>
                        ))}
                    </div>
                </div>

                <div className="glass-panel p-6 bg-surface/80 col-span-1 lg:col-span-2 min-h-[600px]">
                    <h2 className="text-xl font-bold mb-6 flex items-center gap-2 border-b border-white/10 pb-4">
                        <FiShield className="text-primary" /> Multi-Layer Security Visualization
                    </h2>
                    
                    {renderLayerVisualization()}
                </div>
            </div>
        </div>
    );
};

// Mock icon missing in imports
const FiCheckCircle = ({ className }) => <svg className={className} stroke="currentColor" fill="none" strokeWidth="2" viewBox="0 0 24 24" strokeLinecap="round" strokeLinejoin="round" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>;

export default Attacker;
