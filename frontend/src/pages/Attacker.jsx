import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiAlertTriangle, FiActivity, FiShield, FiLock, FiCpu, FiHash, FiZap, FiRadio, FiTerminal } from 'react-icons/fi';

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
        if (!activeAttack) return (
            <div className="flex flex-col items-center justify-center min-h-[400px] text-textMuted font-mono">
                {/* SOC Cyber Radar Sweep Widget */}
                <div className="relative w-48 h-48 rounded-full border border-cyberRed/40 bg-surface/50 mb-4 flex items-center justify-center shadow-neon-red overflow-hidden">
                    <div className="absolute inset-0 rounded-full border border-cyberRed/20"></div>
                    <div className="absolute w-36 h-36 rounded-full border border-cyberRed/20"></div>
                    <div className="absolute w-24 h-24 rounded-full border border-cyberRed/20"></div>
                    <div className="absolute w-12 h-12 rounded-full border border-cyberRed/20"></div>
                    {/* Sweeping Radar Beam */}
                    <div className="absolute w-full h-full rounded-full animate-radar-sweep bg-gradient-to-tr from-transparent via-transparent to-cyberRed/30"></div>
                    <FiRadio className="text-3xl text-cyberRed animate-pulse z-10" />
                </div>
                <p className="text-xs uppercase tracking-widest text-cyberRed glow-text-red">RADAR SCANNER ACTIVE // SELECT ATTACK VECTOR TO SIMULATE</p>
            </div>
        );

        return (
            <div className="space-y-6">
                {/* Layer 1: X25519 & Kyber Key Exchange */}
                <motion.div initial={{opacity: 0, y: 10}} animate={{opacity: simulationStep >= 1 ? 1 : 0.3, y: 0}} className="bg-surface/80 p-4 rounded-xl border border-yellow-400/30 shadow-inner">
                    <h3 className="font-bold flex items-center gap-2 mb-2 text-yellow-400 font-mono uppercase text-sm"><FiZap/> Layer 1: Key Exchange (X25519 + CRYSTALS-Kyber)</h3>
                    <div className="text-xs font-mono text-textMuted flex justify-between">
                        <span>Alice PubKey &rarr;</span>
                        <span className={activeAttack === 'mitm' && simulationStep >= 1 ? "text-cyberRed font-bold animate-pulse" : "text-hackerGreen font-bold"}>
                            {activeAttack === 'mitm' && simulationStep >= 1 ? "MITM: Keys Intercepted & Replaced!" : "Secure Encapsulated Exchange"}
                        </span>
                        <span>&larr; Bob PubKey</span>
                    </div>
                    {activeAttack === 'mitm' && simulationStep >= 2 && (
                        <div className="mt-2 text-xs text-cyberCyan bg-cyberCyan/10 border border-cyberCyan/30 p-2.5 rounded-lg font-mono">
                            <FiShield className="inline mr-1 text-cyberCyan"/> Defense: Kyber Post-Quantum encapsulation verifies the true recipient. MITM attempt thwarted.
                        </div>
                    )}
                </motion.div>

                {/* Layer 2: AES-256 GCM Encryption */}
                <motion.div initial={{opacity: 0, y: 10}} animate={{opacity: simulationStep >= 2 ? 1 : 0.3, y: 0}} className="bg-surface/80 p-4 rounded-xl border border-hackerGreen/30 shadow-inner">
                    <h3 className="font-bold flex items-center gap-2 mb-2 text-hackerGreen font-mono uppercase text-sm"><FiLock/> Layer 2: AES-256 GCM Payload Encryption</h3>
                    <div className="grid grid-cols-4 gap-2 text-xs font-mono text-center">
                        <div className="p-2.5 bg-background/80 rounded border border-white/5 text-textMain">Plaintext<br/>"SECRET"</div>
                        <div className="p-2.5 bg-background/80 rounded border border-white/5 text-cyberCyan">&rarr; Encrypt &rarr;</div>
                        <div className={`p-2.5 bg-background/80 rounded border ${activeAttack === 'sniff' && simulationStep >= 2 ? 'border-cyberRed text-cyberRed font-bold' : 'border-hackerGreen/40 text-hackerGreen'}`}>
                            Ciphertext<br/>{activeAttack === 'tamper' && simulationStep >= 3 ? '0x8F (Modified)' : '0x4A9B'}
                        </div>
                        <div className="p-2.5 bg-background/80 rounded border border-white/5 text-cyberCyan">Auth Tag<br/>0xAB12</div>
                    </div>
                    {activeAttack === 'sniff' && simulationStep >= 3 && (
                        <div className="mt-2 text-xs text-hackerGreen bg-hackerGreen/10 border border-hackerGreen/30 p-2.5 rounded-lg font-mono">
                            <FiShield className="inline mr-1 text-hackerGreen"/> Defense: Attacker captured Ciphertext, but without the Session Key, it remains mathematically unbreakable.
                        </div>
                    )}
                </motion.div>

                {/* Layer 3: SHA3-512 Integrity */}
                <motion.div initial={{opacity: 0, y: 10}} animate={{opacity: simulationStep >= 3 ? 1 : 0.3, y: 0}} className="bg-surface/80 p-4 rounded-xl border border-cyberCyan/30 shadow-inner">
                    <h3 className="font-bold flex items-center gap-2 mb-2 text-cyberCyan font-mono uppercase text-sm"><FiHash/> Layer 3: SHA3-512 Cryptographic Digest</h3>
                    <div className="text-xs font-mono flex flex-col gap-1.5">
                        <span className="text-textMuted">Original Hash: <span className="text-hackerGreen font-bold">a8f5c8d2e...99b2</span></span>
                        <span className="text-textMuted">Received Hash: {activeAttack === 'tamper' && simulationStep >= 4 ? <span className="text-cyberRed font-bold glow-text-red">b3d1f0001...44a1</span> : <span className="text-hackerGreen font-bold">a8f5c8d2e...99b2</span>}</span>
                        <div className="mt-1">
                            {activeAttack === 'tamper' && simulationStep >= 4 ? (
                                <span className="text-cyberRed font-bold uppercase bg-cyberRed/10 border border-cyberRed/40 p-2 rounded block animate-pulse">
                                    Integrity Verification Failed. Authentication Tag Mismatch.
                                </span>
                            ) : (
                                <span className="text-hackerGreen font-bold uppercase bg-hackerGreen/10 border border-hackerGreen/40 p-2 rounded block">
                                    Comparison Match. Digest Integrity Verified.
                                </span>
                            )}
                        </div>
                    </div>
                </motion.div>

                {/* Layer 4: AI Replay Defense */}
                <motion.div initial={{opacity: 0, y: 10}} animate={{opacity: simulationStep >= 4 ? 1 : 0.3, y: 0}} className="bg-surface/80 p-4 rounded-xl border border-cyberRed/30 shadow-inner">
                    <h3 className="font-bold flex items-center gap-2 mb-2 text-cyberRed font-mono uppercase text-sm"><FiCpu/> Layer 4: AI Threat Detection & Anti-Replay</h3>
                    <div className="text-xs font-mono">
                        <div className="flex justify-between mb-1.5 text-textMuted">
                            <span>Packet Timestamp Delta:</span>
                            <span className={activeAttack === 'replay' ? "text-cyberRed font-bold glow-text-red" : "text-hackerGreen font-bold"}>
                                {activeAttack === 'replay' ? "600,000 ms (Replay Detected)" : "45 ms"}
                            </span>
                        </div>
                        {activeAttack === 'replay' && simulationStep >= 5 && (
                            <div className="mt-2 text-xs text-cyberRed font-bold bg-cyberRed/10 border border-cyberRed/40 p-2.5 rounded-lg uppercase tracking-wider animate-pulse">
                                <FiAlertTriangle className="inline mr-1 text-cyberRed"/> Replay Attack Identified by AI Threat Guard. Nonce Reuse Blocked.
                            </div>
                        )}
                        {activeAttack !== 'replay' && simulationStep >= 5 && (
                            <div className="mt-2 text-xs text-hackerGreen font-bold bg-hackerGreen/10 border border-hackerGreen/40 p-2.5 rounded-lg uppercase tracking-wider">
                                <FiShield className="inline mr-1 text-hackerGreen"/> Threat Model: BENIGN / Normal. Message Verified.
                            </div>
                        )}
                    </div>
                </motion.div>
            </div>
        );
    };

    return (
        <div className="min-h-screen p-6 relative">
            <header className="mb-6 glass-panel p-4 border border-cyberRed/40 flex flex-col md:flex-row justify-between items-center gap-4">
                <div className="flex items-center gap-3">
                    <FiTerminal className="text-2xl text-cyberRed animate-pulse" />
                    <div>
                        <h1 className="text-xl font-bold text-cyberRed glow-text-red tracking-wider uppercase font-mono">
                            CYBER ATTACK MATRIX // PENETRATION LAB
                        </h1>
                        <p className="text-xs text-textMuted font-mono">Simulate controlled threat vectors against Defense-Grade Post-Quantum architecture.</p>
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="glass-panel border-cyberRed/30 p-6 col-span-1 h-fit shadow-neon-red">
                    <h2 className="text-md font-bold text-cyberRed mb-4 flex items-center gap-2 font-mono uppercase tracking-wide">
                        <FiActivity /> Select Threat Vector
                    </h2>
                    
                    <div className="space-y-3 font-mono text-xs">
                        {attackVectors.map(attack => (
                            <button 
                                key={attack.id}
                                onClick={() => runSimulation(attack.id)}
                                className={`w-full text-left p-4 rounded-xl border transition-all duration-300 ${
                                    activeAttack === attack.id 
                                        ? 'bg-cyberRed/20 border-cyberRed text-white shadow-neon-red' 
                                        : 'bg-surface/50 border-white/10 text-textMuted hover:border-cyberRed/40 hover:text-white'
                                }`}
                            >
                                <h3 className="font-bold text-sm mb-1 flex items-center gap-1.5">
                                    {attack.name}
                                </h3>
                                <p className="text-[11px] opacity-80 leading-relaxed">{attack.desc}</p>
                            </button>
                        ))}
                    </div>
                </div>

                <div className="cyber-panel-red p-6 col-span-1 lg:col-span-2 min-h-[600px] shadow-neon-red">
                    <h2 className="text-md font-bold text-hackerGreen mb-6 flex items-center gap-2 border-b border-hackerGreen/20 pb-4 font-mono uppercase tracking-wide">
                        <FiShield className="text-hackerGreen" /> Multi-Layer Defense Telemetry Stream
                    </h2>
                    
                    {renderLayerVisualization()}
                </div>
            </div>
        </div>
    );
};

export default Attacker;
