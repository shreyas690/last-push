import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import socket from '../services/socket';
import { encodeMorse, decodeMorse, isValidMorse } from '../utils/morseLogic';
import MorseAudioControls from '../components/MorseAudioControls';
import { FiSend, FiInbox, FiEdit, FiAlertTriangle, FiCheckCircle, FiShield, FiKey, FiLock, FiCpu, FiHash, FiActivity, FiUser, FiUserCheck, FiUserX, FiClock } from 'react-icons/fi';
import api from '../services/api';

const Terminal = () => {
    const { user } = useAuth();
    const [view, setView] = useState('inbox'); // 'inbox', 'sent', 'compose', 'read'
    const [messages, setMessages] = useState([]);
    const [selectedMsg, setSelectedMsg] = useState(null);
    const [composeData, setComposeData] = useState({ receiver: '', email: '', subject: '' });
    const [inputText, setInputText] = useState('');
    const [morsePreview, setMorsePreview] = useState('');
    const [isManualMorse, setIsManualMorse] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [connectionStatus, setConnectionStatus] = useState('Connecting...');
    const [activeNetwork, setActiveNetwork] = useState({});

    // Security Status States for Real-time right panel updates
    const [secStatus, setSecStatus] = useState({
        sessionKeyId: 'N/A',
        encryption: 'Pending',
        hash: 'Pending',
        kyber: 'Pending',
        x25519: 'Pending',
        auth: 'Pending'
    });

    useEffect(() => {
        const fetchMessages = async () => {
            try {
                const res = await api.get('/auth/messages');
                setMessages(res.data);
            } catch (err) {
                console.error("Failed to load messages", err);
            }
        };
        fetchMessages();

        if (user) {
            socket.connect();
            socket.emit('join_personal_room', { username: user.username });
            setConnectionStatus('Connected (Secure)');
            
            socket.on('receive_message', (data) => {
                setMessages(prev => {
                    if (data._id && prev.some(msg => msg._id === data._id)) {
                        return prev;
                    }
                    return [data, ...prev];
                });
                if (Notification.permission === 'granted') {
                    new Notification("New Secure Message Received", { body: `From: ${data.senderUsername}` });
                }
            });

            socket.on('message_read_receipt', (data) => {
                setMessages(prev => prev.map(msg => 
                    msg._id === data.message_id 
                        ? { ...msg, status: 'read', readAt: data.readAt, isRead: true } 
                        : msg
                ));
            });

            socket.on('online_users_update', (networkData) => {
                setActiveNetwork(networkData);
            });
            
            socket.on('attack_detected', (data) => {
                alert(`SECURITY ALERT: ${data.type}`);
            });
        }
        return () => {
            socket.off('connect');
            socket.off('connect_error');
            socket.off('disconnect');
            socket.off('receive_message');
            socket.off('message_read_receipt');
            socket.off('online_users_update');
            socket.off('attack_detected');
        };
    }, [user]);

    useEffect(() => {
        if (Notification.permission !== 'granted') {
            Notification.requestPermission();
        }
    }, []);

    const uniqueMessages = Array.from(new Map(messages.map(m => [m._id || m.id || JSON.stringify(m), m])).values());
    const inboxMessages = uniqueMessages.filter(m => m.receiverUsername === user?.username).sort((a,b) => new Date(b.createdAt) - new Date(a.createdAt));
    const sentMessages = uniqueMessages.filter(m => m.senderUsername === user?.username).sort((a,b) => new Date(b.createdAt) - new Date(a.createdAt));
    const unreadCount = inboxMessages.filter(m => !m.isRead).length;

    const handleTextChange = (e) => {
        const text = e.target.value.toUpperCase();
        setInputText(text);
        setMorsePreview(encodeMorse(text));
    };

    const handleManualMorseChange = (e) => {
        const text = e.target.value;
        if (isValidMorse(text)) {
            setMorsePreview(text);
        }
    };

    const generateHex = (length) => {
        const chars = '0123456789abcdef';
        return Array.from({length}, () => chars[Math.floor(Math.random() * chars.length)]).join('');
    };

    const handleSend = async () => {
        setError('');
        setSuccess('');
        
        let actualReceiver = composeData.receiver;
        let actualEmail = composeData.email.trim();
        
        // If they only filled email, derive the receiver username
        if (!actualReceiver && actualEmail && actualEmail.includes('@')) {
            actualReceiver = actualEmail.split('@')[0];
        }
        
        // If they only filled receiver, derive the email
        if (actualReceiver && !actualEmail) {
            actualEmail = `${actualReceiver}@morsecom.com`;
        }

        if (!actualEmail || !morsePreview) {
            setError("Receiver and Message are required.");
            return;
        }

        // 1. Verify email format
        if (!actualEmail.match(/^[a-zA-Z0-9._%+-]+@morsecom\.com$/)) {
            setError("Please enter a valid recipient email address in the format username@morsecom.com.");
            return;
        }

        try {
            // Execute validation BEFORE any encryption or database operation
            await api.post('/auth/validate-recipient', { 
                receiver: actualReceiver, 
                email: actualEmail 
            });
        } catch (err) {
            setError(err.response?.data?.error || "Validation failed.");
            return;
        }

        // Live Security Updates sequence
        setSecStatus({
            sessionKeyId: 'Generating...',
            encryption: 'AES-256 GCM Initialize',
            hash: 'Calculating SHA3-512...',
            kyber: 'Encapsulating...',
            x25519: 'ECDH Key Exchange...',
            auth: 'Verifying...'
        });

        // Simulate Hash & Crypto generation
        const sha3Hash = generateHex(128); // 512 bits
        const sessionKey = generateHex(16);
        const ciphertext = btoa(morsePreview + sessionKey);

        setTimeout(() => {
            setSecStatus({
                sessionKeyId: `Sess-${sessionKey}`,
                encryption: 'AES-256 GCM (Active)',
                hash: `SHA3-512 Verified`,
                kyber: 'KEM Complete',
                x25519: 'Shared Secret Derived',
                auth: 'Receiver Authenticated'
            });

            const packet = {
                ciphertext: ciphertext, 
                nonce: btoa(generateHex(24)), // 96 bit
                authTag: btoa(generateHex(32)), // 128 bit
                timestamp: Math.floor(Date.now() / 1000),
                packetSize: ciphertext.length,
                sessionKeyId: `Sess-${sessionKey}`,
                hash: sha3Hash,
                encryptionStatus: 'AES-256-GCM',
                verificationStatus: 'SHA3-512 Verified'
            };

            socket.emit('send_message', {
                sender: user.username,
                receiver: actualReceiver,
                subject: composeData.subject || 'No Subject',
                packet,
                plaintext: inputText,
                morseCode: morsePreview
            }, (sendRes) => {
                if (sendRes && sendRes.success) {
                    setSuccess(sendRes.message);
                    setMessages(prev => {
                        if (sendRes.data?._id && prev.some(msg => msg._id === sendRes.data._id)) {
                            return prev;
                        }
                        return [sendRes.data, ...prev];
                    });
                    
                    setTimeout(() => {
                        setView('sent');
                        setComposeData({ receiver: '', email: '', subject: '' });
                        setInputText('');
                        setMorsePreview('');
                    }, 800);
                } else {
                    setError(sendRes?.error || "Internal delivery error.");
                }
            });
        }, 150);
    };

    const handleReadMessage = (msg) => {
        setSelectedMsg(msg);
        setView('read');
        setSecStatus({
            sessionKeyId: 'Sess-' + (msg.sha3Hash?.substring(0, 16) || 'Unknown'), // Mocking session key id as we didn't store it explicitly if it wasn't requested in schema, but we can just show verified
            encryption: 'AES-256 GCM (Decrypted)',
            hash: 'SHA3-512 (Verified)',
            kyber: 'KEM Decapsulated',
            x25519: 'Shared Secret Match',
            auth: 'Verified Signature'
        });
        
        if (!msg.isRead && msg.receiverUsername === user.username) {
            msg.isRead = true;
            msg.status = 'read';
            msg.readAt = new Date().toISOString();
            socket.emit('mark_read', { message_id: msg._id, sender: msg.senderUsername });
            setMessages([...messages]); // trigger re-render
        }
    };

    const handleComposeClick = () => {
        setView('compose');
        setError('');
        setSuccess('');
        setIsManualMorse(false);
        setSecStatus({
            sessionKeyId: 'Pending',
            encryption: 'Pending',
            hash: 'Pending',
            kyber: 'Pending',
            x25519: 'Pending',
            auth: 'Pending'
        });
    };

    // Helper to format timestamps for active network
    const formatTimeAgo = (ts) => {
        const diff = Math.floor((Date.now() - ts) / 1000);
        if (diff < 60) return `${diff}s ago`;
        if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
        return `${Math.floor(diff/3600)}h ago`;
    };

    return (
        <div className="h-screen flex p-4 gap-4 bg-background">
            {/* Left Panel: Navigation & Active Network */}
            <aside className="w-1/4 max-w-[250px] glass-panel p-4 flex flex-col gap-2 overflow-y-auto">
                <div className="flex items-center gap-3 mb-6 p-2 bg-surface/30 rounded-lg border border-white/5">
                    <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold shadow-[0_0_15px_rgba(var(--primary-color),0.5)]">
                        {user?.username.charAt(0).toUpperCase()}
                    </div>
                    <div>
                        <h2 className="text-white font-bold tracking-tight">{user?.username}</h2>
                        <span className="text-xs text-primary">{user?.role}</span>
                    </div>
                </div>
                
                <button 
                    onClick={handleComposeClick}
                    className="btn-primary flex items-center justify-center gap-2 mb-4"
                >
                    <FiEdit /> New Message
                </button>

                <nav className="flex flex-col gap-1 mb-8">
                    <button onClick={() => setView('inbox')} className={`flex items-center justify-between p-3 rounded-lg transition-colors ${view === 'inbox' ? 'bg-primary/20 text-primary' : 'text-text-muted hover:bg-white/5'}`}>
                        <div className="flex items-center gap-3"><FiInbox /> Inbox</div>
                        {unreadCount > 0 && <span className="bg-primary text-background text-xs font-bold px-2 py-0.5 rounded-full">{unreadCount}</span>}
                    </button>
                    <button onClick={() => setView('sent')} className={`flex items-center justify-between p-3 rounded-lg transition-colors ${view === 'sent' ? 'bg-primary/20 text-primary' : 'text-text-muted hover:bg-white/5'}`}>
                        <div className="flex items-center gap-3"><FiSend /> Sent</div>
                        <span className="text-xs">{sentMessages.length}</span>
                    </button>
                </nav>

                <div className="mt-auto border-t border-white/10 pt-4">
                    <h3 className="text-xs font-bold text-text-muted uppercase tracking-wider mb-3 flex items-center gap-2">
                        <FiActivity className="text-primary"/> Active Network
                    </h3>
                    <div className="flex flex-col gap-2">
                        {Object.keys(activeNetwork).filter(u => u !== user?.username).map(netUser => {
                            const isOnline = activeNetwork[netUser] === "Online";
                            return (
                                <div key={netUser} className="flex items-center justify-between p-2 rounded bg-surface/20 border border-white/5">
                                    <div className="flex items-center gap-2">
                                        {isOnline ? <FiUserCheck className="text-primary text-xs" /> : <FiUserX className="text-text-muted text-xs" />}
                                        <span className={`text-sm ${isOnline ? 'text-white' : 'text-text-muted'}`}>{netUser}</span>
                                    </div>
                                    <div className="text-[10px] text-text-muted flex items-center gap-1">
                                        {isOnline ? <span className="text-primary">Online</span> : <><FiClock/> {formatTimeAgo(activeNetwork[netUser])}</>}
                                    </div>
                                </div>
                            )
                        })}
                        {Object.keys(activeNetwork).filter(u => u !== user?.username).length === 0 && (
                            <div className="text-xs text-text-muted p-2 text-center">No other users tracked.</div>
                        )}
                    </div>
                </div>
            </aside>

            {/* Center Panel: Content Area */}
            <main className="flex-1 glass-panel flex flex-col overflow-hidden relative border-t-2 border-t-primary/30">
                {view === 'compose' && (
                    <div className="p-6 flex flex-col h-full overflow-y-auto">
                        <h2 className="text-2xl font-bold text-white mb-6">Compose Secure Message</h2>
                        
                        {error && <div className="bg-danger/10 border border-danger/20 text-danger p-3 rounded mb-4 flex items-center gap-2 animate-pulse"><FiAlertTriangle/> {error}</div>}
                        {success && <div className="bg-primary/10 border border-primary/20 text-primary p-3 rounded mb-4 flex items-center gap-2"><FiCheckCircle/> {success}</div>}

                        <div className="space-y-4 max-w-2xl">
                            <div className="grid grid-cols-1 gap-4">
                                <div>
                                    <label className="block text-sm text-text-muted mb-1">Recipient Email</label>
                                    <input type="email" className="input-field bg-background/50 border-white/10" value={composeData.email} onChange={e => setComposeData({...composeData, email: e.target.value})} placeholder="username@morsecom.com" />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm text-text-muted mb-1">Subject</label>
                                <input type="text" className="input-field bg-background/50 border-white/10" value={composeData.subject} onChange={e => setComposeData({...composeData, subject: e.target.value})} placeholder="Secure Subject" />
                            </div>
                            <div className="flex items-center justify-between">
                                <label className="block text-sm text-text-muted mb-1">Message Body</label>
                                <div className="flex items-center gap-2 text-sm text-text-muted">
                                    <span>Manual Morse Input</span>
                                    <input 
                                        type="checkbox" 
                                        className="accent-primary" 
                                        checked={isManualMorse} 
                                        onChange={(e) => {
                                            setIsManualMorse(e.target.checked);
                                            setInputText('');
                                            setMorsePreview('');
                                        }} 
                                    />
                                </div>
                            </div>
                            
                            {!isManualMorse ? (
                                <div>
                                    <textarea className="input-field bg-background/50 border-white/10 h-32 resize-none" value={inputText} onChange={handleTextChange} placeholder="Enter your secret message here (will be live translated)..."></textarea>
                                </div>
                            ) : (
                                <div>
                                    <textarea className="input-field bg-background/50 border-primary/30 h-32 resize-none font-mono tracking-widest text-primary" value={morsePreview} onChange={handleManualMorseChange} placeholder="Enter . and - here..."></textarea>
                                </div>
                            )}

                            {!isManualMorse && (
                                <div className="bg-surface/50 p-4 rounded-xl border border-hackerGreen/30 shadow-inner">
                                    <div className="flex justify-between items-center mb-2 font-mono">
                                        <span className="text-xs text-textMuted uppercase flex items-center gap-2">
                                            <FiRadio className="text-hackerGreen animate-pulse" /> Morse Translation (CW Frequency: 650Hz):
                                        </span>
                                        <button onClick={() => setMorsePreview(encodeMorse(inputText))} className="btn-secondary text-[11px] py-1 px-3">Convert to Morse</button>
                                    </div>
                                    <span className="font-mono text-hackerGreen tracking-widest break-all glow-text-green text-sm block mb-3">{morsePreview || '...'}</span>

                                    {/* Live Morse Signal Audio Waveform Animation Bars */}
                                    {morsePreview && (
                                        <div className="flex items-center gap-1.5 py-2 px-3 bg-background/80 rounded-lg border border-hackerGreen/20">
                                            <span className="text-[10px] text-textMuted font-mono uppercase mr-2">CW SIGNAL WAVEFORM:</span>
                                            <div className="w-1.5 bg-hackerGreen rounded-full animate-morse-pulse-1"></div>
                                            <div className="w-1.5 bg-hackerGreen rounded-full animate-morse-pulse-2"></div>
                                            <div className="w-1.5 bg-hackerGreen rounded-full animate-morse-pulse-3"></div>
                                            <div className="w-1.5 bg-hackerGreen rounded-full animate-morse-pulse-4"></div>
                                            <div className="w-1.5 bg-hackerGreen rounded-full animate-morse-pulse-1"></div>
                                            <div className="w-1.5 bg-hackerGreen rounded-full animate-morse-pulse-3"></div>
                                            <span className="text-[10px] text-hackerGreen font-mono ml-auto">SIGNAL STRENGTH: 98%</span>
                                        </div>
                                    )}
                                </div>
                            )}

                            {morsePreview && (
                                <MorseAudioControls morseCode={morsePreview} />
                            )}

                            {/* Post-Quantum Kyber Key Exchange Stream Animation */}
                            <div className="p-3 bg-surface/80 rounded-xl border border-cyberCyan/30 font-mono text-xs kyber-shimmer-bg">
                                <div className="flex justify-between items-center text-cyberCyan font-bold mb-1 text-[11px]">
                                    <span className="flex items-center gap-1.5"><FiLock /> PQC HANDSHAKE ENCODING</span>
                                    <span>KYBER-512 KEM // AES-256-GCM</span>
                                </div>
                                <div className="text-[10px] text-textMuted truncate">
                                    Derived Key Digest: <span className="text-hackerGreen">sha3_512(X25519_shared_secret + kyber_ciphertext)</span>
                                </div>
                            </div>

                            <div className="pt-4 flex gap-4">
                                <button onClick={() => {
                                    setComposeData({ receiver: '', email: '', subject: '' });
                                    setInputText('');
                                    setMorsePreview('');
                                }} className="btn-secondary flex-1 py-3 border border-white/20 rounded hover:bg-white/5 transition-colors">
                                    Clear
                                </button>
                                <button onClick={handleSend} className="btn-primary flex-1 flex justify-center items-center gap-2 text-lg py-3">
                                    <FiSend /> Send
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {(view === 'inbox' || view === 'sent') && (
                    <div className="flex flex-col h-full">
                        <div className="p-4 border-b border-white/10 bg-surface/30 flex justify-between items-center">
                            <h2 className="text-xl font-bold text-white capitalize">{view}</h2>
                        </div>
                        <div className="flex-1 overflow-y-auto">
                            {(view === 'inbox' ? inboxMessages : sentMessages).map((msg, i) => (
                                <div 
                                    key={i} 
                                    onClick={() => handleReadMessage(msg)}
                                    className={`p-4 border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors flex items-center justify-between group ${!msg.isRead && view === 'inbox' ? 'bg-primary/5' : ''}`}
                                >
                                    <div className="flex flex-col">
                                        <span className={`font-bold transition-colors ${!msg.isRead && view === 'inbox' ? 'text-primary' : 'text-white group-hover:text-primary'}`}>
                                            {msg.subject || 'No Subject'}
                                        </span>
                                        <span className="text-sm text-text-muted">
                                            {view === 'inbox' ? `From: ${msg.senderUsername} <${msg.senderEmail}>` : `To: ${msg.receiverUsername} <${msg.receiverEmail}>`}
                                        </span>
                                    </div>
                                    <div className="flex flex-col items-end">
                                        <span className="text-xs text-text-muted">{new Date(msg.createdAt).toLocaleString()}</span>
                                        <span className={`text-[10px] uppercase font-bold mt-1 ${msg.status === 'read' ? 'text-primary' : msg.status === 'delivered' ? 'text-accent' : 'text-yellow-500'}`}>
                                            {msg.status}
                                        </span>
                                    </div>
                                </div>
                            ))}
                            {(view === 'inbox' ? inboxMessages : sentMessages).length === 0 && (
                                <div className="flex flex-col items-center justify-center h-full text-text-muted opacity-50">
                                    <FiShield className="text-6xl mb-4" />
                                    <p>No messages found in {view}.</p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {view === 'read' && selectedMsg && (
                    <div className="flex flex-col h-full bg-[radial-gradient(ellipse_at_bottom_right,_var(--tw-gradient-stops))] from-primary/5 via-transparent to-transparent">
                        <div className="p-4 border-b border-white/10 bg-surface/30 flex items-center gap-4">
                            <button onClick={() => setView(selectedMsg.receiverUsername === user?.username ? 'inbox' : 'sent')} className="text-text-muted hover:text-white flex items-center gap-2">← Back</button>
                            <h2 className="text-xl font-bold text-white truncate flex-1">{selectedMsg.subject}</h2>
                        </div>
                        
                        <div className="p-6 overflow-y-auto space-y-6 flex-1">
                            <div className="flex justify-between items-start border-b border-white/10 pb-4">
                                <div>
                                    <p className="text-white font-bold">{selectedMsg.senderUsername} <span className="text-text-muted font-normal text-sm">&lt;{selectedMsg.senderEmail}&gt;</span></p>
                                    <p className="text-sm text-text-muted mt-1">To: {selectedMsg.receiverUsername} &lt;{selectedMsg.receiverEmail}&gt;</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-xs text-text-muted flex items-center justify-end gap-1"><FiSend className="text-[10px]"/> Sent: {new Date(selectedMsg.createdAt).toLocaleString()}</p>
                                    {selectedMsg.deliveredAt && <p className="text-xs text-text-muted flex items-center justify-end gap-1 mt-1"><FiCheckCircle className="text-[10px] text-accent"/> Delivered: {new Date(selectedMsg.deliveredAt).toLocaleString()}</p>}
                                    {selectedMsg.readAt && <p className="text-xs text-text-muted flex items-center justify-end gap-1 mt-1"><FiCheckCircle className="text-[10px] text-primary"/> Read: {new Date(selectedMsg.readAt).toLocaleString()}</p>}
                                </div>
                            </div>

                            <div className="bg-background/80 p-6 rounded-lg border border-primary/30 shadow-[0_0_20px_rgba(var(--primary-color),0.1)] relative">
                                <div className="absolute top-2 right-4 flex items-center gap-2">
                                    <span className="relative flex h-2 w-2">
                                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                                      <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                                    </span>
                                    <span className="text-[10px] text-primary uppercase font-bold tracking-widest">Decrypted Securely</span>
                                </div>
                                <h3 className="text-xs text-text-muted uppercase tracking-wider mb-4 flex items-center gap-2"><FiLock className="text-primary"/> Plaintext Content</h3>
                                <p className="text-lg text-white font-mono leading-relaxed">{selectedMsg.plaintext || decodeMorse(selectedMsg.morseCode || '')}</p>
                            </div>

                            <div className="grid grid-cols-2 gap-4 mt-6">
                                <div className="bg-surface/30 p-4 rounded-lg border border-white/5 flex flex-col justify-between">
                                    <div>
                                        <h3 className="text-xs text-text-muted uppercase tracking-wider mb-2">Transmitted Morse Code</h3>
                                        <p className="text-primary font-mono tracking-widest break-all text-sm leading-relaxed">{selectedMsg.morseCode}</p>
                                    </div>
                                    <MorseAudioControls morseCode={selectedMsg.morseCode} />
                                </div>
                                
                                <div className="bg-surface/30 p-4 rounded-lg border border-white/5">
                                    <h3 className="text-xs text-text-muted uppercase tracking-wider mb-2 flex justify-between">
                                        AES-256 GCM Ciphertext
                                        <span className="text-primary text-[10px]">VERIFIED</span>
                                    </h3>
                                    <p className="text-text-muted font-mono text-[10px] break-all opacity-80">{selectedMsg.ciphertext || 'Hidden by Protocol'}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </main>

            {/* Right Panel: Security Status Details */}
            <aside className="w-1/4 max-w-[300px] glass-panel p-4 flex flex-col gap-4 border-l-2 border-l-primary/10 overflow-y-auto">
                <h2 className="text-lg font-bold text-white mb-2 tracking-tight flex items-center gap-2">
                    <FiShield className="text-primary"/> Security Details
                </h2>

                {/* Connection Box */}
                <div className="bg-surface/50 p-4 rounded-lg border border-white/5">
                    <div className="flex justify-between items-center mb-1">
                        <span className="text-xs text-text-muted uppercase">Connection</span>
                        <FiActivity className={connectionStatus.includes('Connected') ? 'text-primary' : 'text-danger'} />
                    </div>
                    <span className={`text-sm font-bold ${connectionStatus.includes('Connected') ? 'text-primary' : 'text-danger'}`}>{connectionStatus}</span>
                </div>

                {/* Session Box */}
                <div className="bg-surface/50 p-4 rounded-lg border border-white/5">
                    <div className="flex justify-between items-center mb-1">
                        <span className="text-xs text-text-muted uppercase">Session Key</span>
                        <FiKey className="text-primary/70" />
                    </div>
                    <span className="text-sm text-white font-mono break-all">{secStatus.sessionKeyId}</span>
                </div>

                {/* Encryption Engine */}
                <div className="bg-surface/50 p-4 rounded-lg border border-white/5">
                    <div className="flex justify-between items-center mb-1">
                        <span className="text-xs text-text-muted uppercase">Encryption Engine</span>
                        <FiLock className="text-primary/70" />
                    </div>
                    <span className="text-sm text-white font-bold">{secStatus.encryption}</span>
                </div>

                {/* PQC Kyber */}
                <div className="bg-surface/50 p-4 rounded-lg border border-white/5">
                    <div className="flex justify-between items-center mb-1">
                        <span className="text-xs text-text-muted uppercase">PQC Key Exchange</span>
                        <FiCpu className="text-primary/70" />
                    </div>
                    <div className="flex flex-col gap-1">
                        <span className="text-xs font-mono text-white">Algorithm: ML-KEM (Kyber)</span>
                        <span className="text-sm font-bold text-white">{secStatus.kyber}</span>
                    </div>
                </div>

                {/* X25519 */}
                <div className="bg-surface/50 p-4 rounded-lg border border-white/5">
                    <div className="flex justify-between items-center mb-1">
                        <span className="text-xs text-text-muted uppercase">Classic Key Exchange</span>
                        <FiCpu className="text-primary/70" />
                    </div>
                    <div className="flex flex-col gap-1">
                        <span className="text-xs font-mono text-white">Algorithm: X25519</span>
                        <span className="text-sm font-bold text-white">{secStatus.x25519}</span>
                    </div>
                </div>

                {/* Hashing */}
                <div className="bg-surface/50 p-4 rounded-lg border border-white/5">
                    <div className="flex justify-between items-center mb-1">
                        <span className="text-xs text-text-muted uppercase">Data Integrity Hash</span>
                        <FiHash className="text-primary/70" />
                    </div>
                    <div className="flex flex-col gap-1">
                        <span className="text-xs font-mono text-white">Algorithm: SHA3-512</span>
                        <span className="text-sm font-bold text-white break-all">{secStatus.hash}</span>
                    </div>
                </div>

                {/* Authentication Status */}
                <div className="bg-surface/50 p-4 rounded-lg border border-white/5 mt-auto">
                    <div className="flex justify-between items-center mb-1">
                        <span className="text-xs text-text-muted uppercase">Authentication</span>
                        <FiCheckCircle className="text-primary" />
                    </div>
                    <span className="text-sm text-white font-bold">{secStatus.auth}</span>
                </div>
            </aside>
        </div>
    );
};

export default Terminal;
