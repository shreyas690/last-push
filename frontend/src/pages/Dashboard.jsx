import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  FiActivity, FiUsers, FiShield, FiAlertTriangle, FiCheckCircle, FiCheck, FiX, 
  FiCpu, FiDatabase, FiRefreshCw, FiBarChart2, FiPlay, FiTerminal, FiLock, FiRadio 
} from 'react-icons/fi';
import api from '../services/api';
import socket from '../services/socket';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Format date according to Indian Standard Time (IST)
const formatISTDate = (timestamp) => {
    if (!timestamp) return 'N/A';
    try {
        const date = new Date(timestamp);
        return date.toLocaleString('en-IN', {
            timeZone: 'Asia/Kolkata',
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        }) + ' IST';
    } catch (e) {
        return String(timestamp);
    }
};

const Dashboard = () => {
    const { user } = useAuth();
    const [stats, setStats] = useState({
        totalUsers: 0,
        approvedUsers: 0,
        pendingApproval: 0,
        encryptionRequests: 0,
        securityEvents: [],
        successfulDeliveries: 0,
        failedDeliveries: 0,
        onlineUsers: 0,
        offlineUsers: 0,
        rejectedUsers: 0,
        messagesSentToday: 0,
        messagesReceivedToday: 0,
        activeSessions: 0
    });
    
    const [pendingUsers, setPendingUsers] = useState([]);
    const [encryptionHistory, setEncryptionHistory] = useState([0, 0, 0, 0, 0, 0, 0]);
    const [processingUsers, setProcessingUsers] = useState({});
    
    // Objective 1 State
    const [aiMetrics, setAiMetrics] = useState(null);
    const [aiLoading, setAiLoading] = useState(false);
    const [activeModalImage, setActiveModalImage] = useState(null);
    const [aiActionMessage, setAiActionMessage] = useState('');

    // Objective 2 State
    const [secScale, setSecScale] = useState(100);
    const [secTestRunning, setSecTestRunning] = useState(false);
    const [secLiveProgress, setSecLiveProgress] = useState(null);
    const [secResults, setSecResults] = useState([]);
    
    useEffect(() => {
        let timer = null;
        const fetchStats = async () => {
            if (user?.role === 'Admin') {
                try {
                    const res = await api.get(`/dashboard/stats?t=${Date.now()}`);
                    setStats(res.data);
                    
                    setEncryptionHistory(prev => {
                        const newHistory = [...prev.slice(1), res.data.encryptionRequests];
                        return newHistory;
                    });
                    
                    const pendingRes = await api.get(`/admin/pending-users?t=${Date.now()}`);
                    setPendingUsers(pendingRes.data);
                } catch (err) {
                    console.error("Failed to fetch dashboard data", err);
                }
            }
        };
        
        fetchStats();
        fetchAiMetrics();
        fetchSecurityResults();

        const debouncedFetch = () => {
            if (timer) clearTimeout(timer);
            timer = setTimeout(fetchStats, 500);
        };

        socket.on('dashboard_update', debouncedFetch);
        socket.on('security_test_update', (eventData) => {
            setSecLiveProgress(eventData);
            if (eventData.event === 'TEST_SUITE_COMPLETED') {
                setSecTestRunning(false);
                fetchSecurityResults();
            }
        });

        return () => {
            if (timer) clearTimeout(timer);
            socket.off('dashboard_update', debouncedFetch);
            socket.off('security_test_update');
        };
    }, [user]);

    const fetchAiMetrics = async () => {
        if (user?.role !== 'Admin') return;
        try {
            const res = await api.get('/ai/metrics');
            setAiMetrics(res.data);
        } catch (err) {
            console.error("Failed to fetch AI metrics", err);
        }
    };

    const fetchSecurityResults = async () => {
        if (user?.role !== 'Admin') return;
        try {
            const res = await api.get('/security-tests/results');
            setSecResults(res.data);
        } catch (err) {
            console.error("Failed to fetch security evaluation results", err);
        }
    };

    const handleApproval = async (userId, action) => {
        const confirmMsg = action === 'approve' 
            ? "Approve access for this user?" 
            : "Reject access for this user?";
            
        if (!window.confirm(confirmMsg)) return;

        setProcessingUsers(prev => ({ ...prev, [userId]: true }));
        try {
            const res = await api.put(`/admin/${action}/${userId}`);
            setPendingUsers(prev => prev.filter(u => u._id !== userId));
            setStats(prev => ({
                ...prev,
                pendingApproval: Math.max(0, (prev.pendingApproval || 1) - 1),
                approvedUsers: action === 'approve' ? (prev.approvedUsers || 0) + 1 : prev.approvedUsers,
                rejectedUsers: action === 'reject' ? (prev.rejectedUsers || 0) + 1 : prev.rejectedUsers
            }));
            alert(res.data.message);
            setTimeout(() => socket.emit('dashboard_update'), 100);
        } catch (err) {
            console.error(`Failed to ${action} user`, err);
            alert(err.response?.data?.error || `Failed to ${action} user.`);
        } finally {
            setProcessingUsers(prev => ({ ...prev, [userId]: false }));
        }
    };

    const handleTrainModel = async () => {
        setAiLoading(true);
        setAiActionMessage('Initializing multi-model AI suite training...');
        try {
            const res = await api.post('/ai/train');
            alert(res.data.message);
            await fetchAiMetrics();
        } catch (err) {
            alert(err.response?.data?.error || "Training failed.");
        } finally {
            setAiLoading(false);
            setAiActionMessage('');
        }
    };

    const handleRetrainModel = async () => {
        setAiLoading(true);
        setAiActionMessage('Executing continuous learning retrain workflow...');
        try {
            const res = await api.post('/ai/retrain');
            alert(res.data.message);
            await fetchAiMetrics();
        } catch (err) {
            alert(err.response?.data?.error || "Retraining failed.");
        } finally {
            setAiLoading(false);
            setAiActionMessage('');
        }
    };

    const handleExportDataset = async () => {
        try {
            const res = await api.post('/ai/export-dataset');
            alert(res.data.message);
        } catch (err) {
            alert(err.response?.data?.error || "Dataset export failed.");
        }
    };

    const handleRunSecurityTests = async () => {
        setSecTestRunning(true);
        setSecLiveProgress({ event: 'TEST_SUITE_STARTED', scale: secScale, status: 'Initializing Framework...' });
        try {
            const res = await api.post('/security-tests/run', { scale: secScale });
            alert(res.data.message);
            await fetchSecurityResults();
        } catch (err) {
            alert(err.response?.data?.error || "Security test execution failed.");
        } finally {
            setSecTestRunning(false);
        }
    };

    const chartOptions = {
        responsive: true,
        plugins: { 
            legend: { display: false },
            tooltip: {
                backgroundColor: '#0a192f',
                titleColor: '#00ff66',
                bodyColor: '#00f3ff',
                borderColor: '#00ff66',
                borderWidth: 1
            }
        },
        scales: {
            x: { grid: { color: 'rgba(0, 255, 102, 0.1)' }, ticks: { color: '#8892b0' } },
            y: { grid: { color: 'rgba(0, 255, 102, 0.1)' }, ticks: { color: '#8892b0' } }
        }
    };

    const performanceData = {
        labels: ['-30s', '-25s', '-20s', '-15s', '-10s', '-5s', 'Now'],
        datasets: [
            {
                fill: true,
                label: 'Payload Encryptions',
                data: encryptionHistory,
                borderColor: '#00ff66',
                backgroundColor: 'rgba(0, 255, 102, 0.15)',
                tension: 0.3,
                pointBackgroundColor: '#00f3ff'
            }
        ]
    };

    const activeVersion = aiMetrics?.activeVersion;

    return (
        <div className="min-h-screen p-6 relative">
            {/* Hacker Simulator Top Banner Bar */}
            <div className="glass-panel p-4 mb-6 border border-hackerGreen/40 flex flex-col md:flex-row justify-between items-center gap-4">
                <div className="flex items-center gap-3">
                    <FiTerminal className="text-2xl text-hackerGreen animate-pulse" />
                    <div>
                        <h1 className="text-xl font-bold text-hackerGreen glow-text-green tracking-wider uppercase">
                          CYBER DEFENSE MATRIX // ADMIN COMMAND CENTER
                        </h1>
                        <p className="text-xs text-textMuted font-mono">OPERATOR: <span className="text-cyberCyan">{user?.username}</span> | NODE: LOCALHOST:5000</p>
                    </div>
                </div>

                {/* Telemetry Status Badges */}
                <div className="flex flex-wrap gap-2 text-[11px] font-mono">
                    <span className="bg-hackerGreen/10 border border-hackerGreen/40 text-hackerGreen px-2.5 py-1 rounded-md flex items-center gap-1.5 shadow-neon-green">
                        <span className="w-2 h-2 rounded-full bg-hackerGreen animate-ping"></span>
                        SYS.STATUS: ONLINE
                    </span>
                    <span className="bg-cyberCyan/10 border border-cyberCyan/40 text-cyberCyan px-2.5 py-1 rounded-md flex items-center gap-1">
                        <FiLock className="text-xs" /> ENCRYPTION: AES-256-GCM
                    </span>
                    <span className="bg-cyberCyan/10 border border-cyberCyan/40 text-cyberCyan px-2.5 py-1 rounded-md flex items-center gap-1">
                        <FiRadio className="text-xs" /> PQC: KYBER-512
                    </span>
                    <span className="bg-hackerGreen/10 border border-hackerGreen/40 text-hackerGreen px-2.5 py-1 rounded-md flex items-center gap-1">
                        <FiShield className="text-xs" /> AI DEFENSE: ACTIVE
                    </span>
                </div>
            </div>

            {user?.role === 'Admin' ? (
                <>
                    {/* Live System Telemetry Metrics Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
                        <StatCard icon={<FiUsers />} title="Total Users" value={stats.totalUsers} color="text-hackerGreen" cardBorder="border-hackerGreen/30" />
                        <StatCard icon={<FiActivity />} title="Online Users" value={stats.onlineUsers} color="text-hackerGreen" cardBorder="border-hackerGreen/40" isLive />
                        <StatCard icon={<FiUsers />} title="Offline Users" value={stats.offlineUsers} color="text-textMuted" cardBorder="border-white/10" />
                        <StatCard icon={<FiCheckCircle />} title="Approved Users" value={stats.approvedUsers} color="text-cyberCyan" cardBorder="border-cyberCyan/30" />
                        <StatCard icon={<FiAlertTriangle />} title="Pending Approvals" value={stats.pendingApproval} color="text-yellow-400" cardBorder="border-yellow-400/30" />
                        <StatCard icon={<FiShield />} title="Rejected Users" value={stats.rejectedUsers} color="text-cyberRed" cardBorder="border-cyberRed/30" />
                        <StatCard icon={<FiActivity />} title="Sent Today" value={stats.messagesSentToday} color="text-hackerGreen" cardBorder="border-hackerGreen/30" />
                        <StatCard icon={<FiCheckCircle />} title="Received Today" value={stats.messagesReceivedToday} color="text-cyberCyan" cardBorder="border-cyberCyan/30" />
                        <StatCard icon={<FiCheckCircle />} title="Successful Deliveries" value={stats.successfulDeliveries} color="text-hackerGreen" cardBorder="border-hackerGreen/30" />
                        <StatCard icon={<FiAlertTriangle />} title="Blocked Threats" value={stats.failedDeliveries} color="text-cyberRed" cardBorder="border-cyberRed/40" />
                        <StatCard icon={<FiActivity />} title="Active Sessions" value={stats.activeSessions} color="text-cyberCyan" cardBorder="border-cyberCyan/30" />
                        <StatCard icon={<FiCpu />} title="Communication Logs" value={aiMetrics?.totalCommunicationLogs || 0} color="text-hackerGreen" cardBorder="border-hackerGreen/30" />
                    </div>

                    {/* OBJECTIVE 1 — AI THREAT DETECTION & CONTINUOUS LEARNING */}
                    <div className="glass-panel p-6 mb-8 border border-hackerGreen/30 shadow-neon-green">
                        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4 border-b border-hackerGreen/20 pb-4">
                            <div>
                                <h2 className="text-lg font-bold text-hackerGreen glow-text-green flex items-center gap-2 uppercase tracking-wide">
                                    <FiCpu /> OBJECTIVE 1 // AI Threat Detection & Continuous Learning
                                </h2>
                                <p className="text-xs text-textMuted mt-1">Multi-model behavioral security guard trained on CIC-IDS2017 & live application log streams.</p>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                <button onClick={handleTrainModel} disabled={aiLoading} className="btn-secondary text-xs flex items-center gap-1.5">
                                    <FiRefreshCw className={aiLoading ? "animate-spin" : ""} /> Train AI Suite
                                </button>
                                <button onClick={handleRetrainModel} disabled={aiLoading} className="btn-primary text-xs flex items-center gap-1.5">
                                    <FiRefreshCw className={aiLoading ? "animate-spin" : ""} /> Continuous Retrain
                                </button>
                                <button onClick={handleExportDataset} className="btn-secondary text-xs flex items-center gap-1.5">
                                    <FiDatabase /> Export Dataset
                                </button>
                            </div>
                        </div>

                        {aiActionMessage && <div className="text-xs text-hackerGreen bg-hackerGreen/10 border border-hackerGreen/30 p-3 rounded-lg mb-4 animate-pulse">{aiActionMessage}</div>}

                        {activeVersion ? (
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6 font-mono text-xs">
                                <div className="bg-background/80 p-3 rounded-lg border border-hackerGreen/20">
                                    <span className="text-[10px] text-textMuted uppercase block">Active Model</span>
                                    <span className="text-sm font-bold text-hackerGreen truncate block">{activeVersion.model_type}</span>
                                </div>
                                <div className="bg-background/80 p-3 rounded-lg border border-hackerGreen/20">
                                    <span className="text-[10px] text-textMuted uppercase block">Version</span>
                                    <span className="text-sm font-bold text-cyberCyan block">{activeVersion.version}</span>
                                </div>
                                <div className="bg-background/80 p-3 rounded-lg border border-hackerGreen/20">
                                    <span className="text-[10px] text-textMuted uppercase block">Accuracy</span>
                                    <span className="text-sm font-bold text-hackerGreen block">{(activeVersion.accuracy * 100).toFixed(1)}%</span>
                                </div>
                                <div className="bg-background/80 p-3 rounded-lg border border-hackerGreen/20">
                                    <span className="text-[10px] text-textMuted uppercase block">F1 Score</span>
                                    <span className="text-sm font-bold text-hackerGreen block">{(activeVersion.f1_score * 100).toFixed(1)}%</span>
                                </div>
                                <div className="bg-background/80 p-3 rounded-lg border border-hackerGreen/20">
                                    <span className="text-[10px] text-textMuted uppercase block">Recall</span>
                                    <span className="text-sm font-bold text-cyberCyan block">{(activeVersion.recall * 100).toFixed(1)}%</span>
                                </div>
                                <div className="bg-background/80 p-3 rounded-lg border border-hackerGreen/20">
                                    <span className="text-[10px] text-textMuted uppercase block">ROC-AUC</span>
                                    <span className="text-sm font-bold text-cyberCyan block">{(activeVersion.roc_auc * 100).toFixed(1)}%</span>
                                </div>
                            </div>
                        ) : (
                            <div className="text-center p-4 text-textMuted text-xs font-mono">No trained model loaded. Click "Train AI Suite" to generate model versioning.</div>
                        )}

                        {aiMetrics?.images && (
                            <div className="flex flex-wrap gap-3 border-t border-hackerGreen/20 pt-4">
                                {aiMetrics.images.confusionMatrix && (
                                    <button onClick={() => setActiveModalImage({ title: "Confusion Matrix Plot", src: `data:image/png;base64,${aiMetrics.images.confusionMatrix}` })} className="btn-secondary text-xs flex items-center gap-2">
                                        <FiBarChart2 className="text-cyberCyan"/> Confusion Matrix
                                    </button>
                                )}
                                {aiMetrics.images.rocCurve && (
                                    <button onClick={() => setActiveModalImage({ title: "ROC Curve Analysis", src: `data:image/png;base64,${aiMetrics.images.rocCurve}` })} className="btn-secondary text-xs flex items-center gap-2">
                                        <FiBarChart2 className="text-cyberCyan"/> ROC Curve
                                    </button>
                                )}
                                {aiMetrics.images.featureImportance && (
                                    <button onClick={() => setActiveModalImage({ title: "Feature Importance Ranking", src: `data:image/png;base64,${aiMetrics.images.featureImportance}` })} className="btn-secondary text-xs flex items-center gap-2">
                                        <FiBarChart2 className="text-cyberCyan"/> Feature Importance
                                    </button>
                                )}
                            </div>
                        )}
                    </div>

                    {/* OBJECTIVE 2 — FORMAL SECURITY EVALUATION & PENETRATION TESTING FRAMEWORK */}
                    <div className="cyber-panel-red p-6 mb-8 border border-cyberRed/30 shadow-neon-red">
                        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4 border-b border-cyberRed/20 pb-4">
                            <div>
                                <h2 className="text-lg font-bold text-cyberRed glow-text-red flex items-center gap-2 uppercase tracking-wide">
                                    <FiShield /> OBJECTIVE 2 // Formal Security Evaluation & Penetration Testing
                                </h2>
                                <p className="text-xs text-textMuted mt-1">Controlled penetration testing framework evaluating Tampering, Replay, MITM, Auth, Integrity & Flooding.</p>
                            </div>
                            <div className="flex items-center gap-3">
                                <label className="text-xs text-textMuted font-mono">Attempts / Category:</label>
                                <select value={secScale} onChange={(e) => setSecScale(Number(e.target.value))} className="bg-background border border-cyberRed/40 text-xs rounded px-3 py-1.5 text-cyberRed font-mono focus:outline-none">
                                    <option value={10}>10</option>
                                    <option value={50}>50</option>
                                    <option value={100}>100 (Default)</option>
                                    <option value={500}>500</option>
                                    <option value={1000}>1000</option>
                                </select>
                                <button onClick={handleRunSecurityTests} disabled={secTestRunning} className="btn-danger text-xs flex items-center gap-1.5">
                                    <FiPlay className={secTestRunning ? "animate-spin" : ""} /> {secTestRunning ? "Executing Suite..." : "Run Security Test Suite"}
                                </button>
                            </div>
                        </div>

                        {/* Live Socket.IO Test Monitor */}
                        {secLiveProgress && (
                            <div className="bg-background/90 p-4 rounded-lg border border-cyberRed/40 mb-6 font-mono text-xs shadow-inner">
                                <div className="flex justify-between items-center text-cyberRed font-bold mb-2">
                                    <span className="flex items-center gap-2">
                                        <span className="w-2 h-2 rounded-full bg-cyberRed animate-ping"></span>
                                        LIVE PENETRATION TEST STREAM
                                    </span>
                                    <span className="animate-pulse">{secLiveProgress.status || "RUNNING"}</span>
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-textMuted">
                                    <div>Attack: <span className="text-white font-bold">{secLiveProgress.attackType || "Initialization"}</span></div>
                                    <div>Progress: <span className="text-white font-bold">{secLiveProgress.attempt || 0} / {secLiveProgress.total || secScale}</span></div>
                                    <div>AI Risk: <span className="text-yellow-400 font-bold">{secLiveProgress.aiRisk || "Analyzing"}</span></div>
                                    <div>Latency: <span className="text-cyberCyan font-bold">{secLiveProgress.latencyMs || 0} ms</span></div>
                                </div>
                            </div>
                        )}

                        {/* Security Evaluation Results Table */}
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse font-mono text-xs">
                                <thead>
                                    <tr className="border-b border-cyberRed/20 text-textMuted uppercase text-[11px]">
                                        <th className="p-2.5">Attack Vector</th>
                                        <th className="p-2.5">Attempts</th>
                                        <th className="p-2.5">Detected</th>
                                        <th className="p-2.5">Missed</th>
                                        <th className="p-2.5">Detection Rate</th>
                                        <th className="p-2.5">FPR</th>
                                        <th className="p-2.5">Avg Latency</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {secResults.length > 0 ? secResults.slice(0, 6).map((res, idx) => (
                                        <tr key={idx} className="border-b border-white/5 hover:bg-white/5">
                                            <td className="p-2.5 font-bold text-white">{res.attackType}</td>
                                            <td className="p-2.5 text-textMuted">{res.totalAttempts}</td>
                                            <td className="p-2.5 text-hackerGreen font-bold">{res.detectedAttempts}</td>
                                            <td className="p-2.5 text-cyberRed">{res.missedAttempts}</td>
                                            <td className="p-2.5 text-hackerGreen font-bold">{res.detectionRate}%</td>
                                            <td className="p-2.5 text-textMuted">{res.falsePositiveRate}%</td>
                                            <td className="p-2.5 text-cyberCyan">{res.avgDetectionLatencyMs} ms</td>
                                        </tr>
                                    )) : (
                                        <tr>
                                            <td colSpan="7" className="p-4 text-center text-textMuted font-bold">No penetration test metrics recorded. Click "Run Security Test Suite" to execute framework.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Encryption Load Chart & Pending Approvals Table */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div className="glass-panel p-6">
                            <h3 className="text-md font-bold text-hackerGreen mb-4 font-mono uppercase tracking-wide">
                                Encryption Telemetry Matrix (AES-256-GCM)
                            </h3>
                            <Line options={chartOptions} data={performanceData} />
                        </div>
                        
                        {/* Pending Approvals Table (NO EMOJIS, CLEAN SVG ICONS & STYLED BUTTONS) */}
                        <div className="glass-panel p-6 flex flex-col">
                            <h3 className="text-md font-bold text-yellow-400 mb-4 flex justify-between items-center font-mono uppercase tracking-wide">
                                Pending User Access Requests
                                {pendingUsers.length > 0 && (
                                    <span className="text-xs bg-yellow-400/10 border border-yellow-400/40 text-yellow-400 px-2.5 py-1 rounded-md animate-pulse">
                                        {pendingUsers.length} PENDING
                                    </span>
                                )}
                            </h3>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse font-mono text-xs">
                                    <thead>
                                        <tr className="border-b border-white/10 text-textMuted text-[11px] uppercase">
                                            <th className="p-2.5">Username</th>
                                            <th className="p-2.5">Email</th>
                                            <th className="p-2.5">Role</th>
                                            <th className="p-2.5">Registration Time (IST)</th>
                                            <th className="p-2.5">Status</th>
                                            <th className="p-2.5">Action Controls</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {pendingUsers.length > 0 ? pendingUsers.map((u) => (
                                            <tr key={u._id} className="border-b border-white/5 hover:bg-white/5">
                                                <td className="p-2.5 font-bold text-white">{u.username}</td>
                                                <td className="p-2.5 text-textMuted">{u.email}</td>
                                                <td className="p-2.5 text-cyberCyan">{u.role}</td>
                                                <td className="p-2.5 text-textMuted text-[11px]">{formatISTDate(u.createdAt)}</td>
                                                <td className="p-2.5 text-yellow-400">{u.status}</td>
                                                <td className="p-2.5">
                                                    <div className="flex gap-2">
                                                        <button 
                                                            onClick={() => handleApproval(u._id, 'approve')} 
                                                            disabled={processingUsers[u._id]}
                                                            className="bg-hackerGreen/15 hover:bg-hackerGreen hover:text-black border border-hackerGreen text-hackerGreen text-[11px] font-bold px-3 py-1.5 rounded flex items-center gap-1 transition-all"
                                                        >
                                                            <FiCheck className="text-xs" />
                                                            {processingUsers[u._id] ? "Saving..." : "Approve"}
                                                        </button>
                                                        <button 
                                                            onClick={() => handleApproval(u._id, 'reject')} 
                                                            disabled={processingUsers[u._id]}
                                                            className="bg-cyberRed/15 hover:bg-cyberRed hover:text-white border border-cyberRed text-cyberRed text-[11px] font-bold px-3 py-1.5 rounded flex items-center gap-1 transition-all"
                                                        >
                                                            <FiX className="text-xs" />
                                                            {processingUsers[u._id] ? "Saving..." : "Reject"}
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        )) : (
                                            <tr>
                                                <td colSpan="6" className="p-4 text-center text-textMuted font-mono">No pending authorization requests in queue.</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    {/* Recent Security Events Table with Indian Standard Time (IST) */}
                    <div className="glass-panel p-6">
                        <h3 className="text-md font-bold text-hackerGreen mb-4 flex justify-between items-center font-mono uppercase tracking-wide">
                            Recent Security Event Logs
                            {stats.securityEvents.length > 0 && (
                                <span className="text-xs bg-cyberRed/10 border border-cyberRed/40 text-cyberRed px-2.5 py-1 rounded-md animate-pulse">
                                    LIVE MONITOR
                                </span>
                            )}
                        </h3>
                        <div className="overflow-x-auto max-h-[400px]">
                            <table className="w-full text-left border-collapse font-mono text-xs">
                                <thead className="sticky top-0 bg-[#0a192f] border-b border-hackerGreen/20">
                                    <tr className="text-textMuted uppercase text-[11px]">
                                        <th className="p-2.5">Timestamp (IST)</th>
                                        <th className="p-2.5">User Node</th>
                                        <th className="p-2.5">Event Signature</th>
                                        <th className="p-2.5">Telemetry Details</th>
                                        <th className="p-2.5">Severity</th>
                                        <th className="p-2.5">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {stats.securityEvents.length > 0 ? stats.securityEvents.map((evt, idx) => (
                                        <tr key={idx} className="border-b border-white/5 hover:bg-white/5">
                                            <td className="p-2.5 text-textMuted text-[11px] font-mono">{formatISTDate(evt.timestamp)}</td>
                                            <td className="p-2.5 font-bold text-white">{evt.username}</td>
                                            <td className="p-2.5 text-cyberRed">{evt.eventType || evt.event}</td>
                                            <td className="p-2.5 text-textMuted text-[11px]">{evt.description || evt.details}</td>
                                            <td className="p-2.5 text-cyberCyan">{evt.role || evt.severity}</td>
                                            <td className="p-2.5 text-hackerGreen">{evt.status || "Completed"}</td>
                                        </tr>
                                    )) : (
                                        <tr>
                                            <td colSpan="6" className="p-4 text-center text-textMuted">No security anomalies recorded.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            ) : (
                <div className="glass-panel p-12 text-center border border-cyberRed/40">
                    <FiShield className="mx-auto text-6xl text-cyberRed mb-4 animate-pulse" />
                    <h2 className="text-2xl font-bold mb-2 text-cyberRed glow-text-red font-mono uppercase">ACCESS DENIED // ADMIN REQUIRED</h2>
                    <p className="text-textMuted mb-6 font-mono">Higher level clearance required to view defense dashboard telemetry.</p>
                </div>
            )}

            {/* Modal for AI Metric Charts */}
            {activeModalImage && (
                <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4" onClick={() => setActiveModalImage(null)}>
                    <div className="glass-panel p-6 max-w-2xl w-full flex flex-col items-center border border-hackerGreen/40 shadow-neon-green" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-between items-center w-full mb-4">
                            <h3 className="text-md font-bold text-hackerGreen font-mono uppercase">{activeModalImage.title}</h3>
                            <button onClick={() => setActiveModalImage(null)} className="text-textMuted hover:text-cyberRed transition-colors"><FiX className="text-xl"/></button>
                        </div>
                        <img src={activeModalImage.src} alt={activeModalImage.title} className="max-h-[480px] object-contain rounded-lg border border-hackerGreen/20 shadow-inner" />
                    </div>
                </div>
            )}
        </div>
    );
};

const StatCard = ({ icon, title, value, color, cardBorder = "border-hackerGreen/20", isLive }) => (
    <div className={`glass-panel p-4 flex items-center gap-3 border ${cardBorder}`}>
        <div className={`text-2xl ${color} bg-background/80 p-2.5 rounded-lg border border-white/5`}>
            {icon}
        </div>
        <div>
            <p className="text-[11px] text-textMuted font-mono flex items-center gap-1">
                {title}
                {isLive && <span className="w-1.5 h-1.5 rounded-full bg-hackerGreen animate-ping"></span>}
            </p>
            <p className={`text-xl font-bold font-mono ${color}`}>{value}</p>
        </div>
    </div>
);

export default Dashboard;
