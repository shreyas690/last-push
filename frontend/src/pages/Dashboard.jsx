import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  FiActivity, FiUsers, FiShield, FiAlertTriangle, FiCheckCircle, FiCheck, FiX, 
  FiCpu, FiDatabase, FiRefreshCw, FiDownload, FiBarChart2, FiPlay, FiFileText 
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
    
    // Objective 1: AI Threat Detection & Continuous Learning State
    const [aiMetrics, setAiMetrics] = useState(null);
    const [aiLoading, setAiLoading] = useState(false);
    const [activeModalImage, setActiveModalImage] = useState(null);
    const [aiActionMessage, setAiActionMessage] = useState('');

    // Objective 2: Formal Security Evaluation & Penetration Testing Framework State
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
            ? "Are you sure you want to approve this user?" 
            : "Are you sure you want to reject this user?";
            
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
            alert(err.response?.data?.error || `Failed to ${action} user. Check console.`);
        } finally {
            setProcessingUsers(prev => ({ ...prev, [userId]: false }));
        }
    };

    // AI Action Handlers
    const handleTrainModel = async () => {
        setAiLoading(true);
        setAiActionMessage('Training multi-model suite...');
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
        setAiActionMessage('Executing continuous learning retrain...');
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

    // Security Test Runner
    const handleRunSecurityTests = async () => {
        setSecTestRunning(true);
        setSecLiveProgress({ event: 'TEST_SUITE_STARTED', scale: secScale, status: 'Initializing...' });
        try {
            const res = await api.post('/security-tests/run', { scale: secScale });
            alert(res.data.message);
            await fetchSecurityResults();
        } catch (err) {
            alert(err.response?.data?.error || "Security Test Execution failed.");
        } finally {
            setSecTestRunning(false);
        }
    };

    const chartOptions = {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
            x: { grid: { color: 'rgba(255, 255, 255, 0.1)' } },
            y: { grid: { color: 'rgba(255, 255, 255, 0.1)' } }
        }
    };

    const performanceData = {
        labels: ['-30s', '-25s', '-20s', '-15s', '-10s', '-5s', 'Now'],
        datasets: [
            {
                fill: true,
                label: 'Total Encryptions',
                data: encryptionHistory,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.2)',
                tension: 0.4
            }
        ]
    };

    const activeVersion = aiMetrics?.activeVersion;
    const latestMetrics = aiMetrics?.evaluationReport?.metrics;

    return (
        <div className="min-h-screen p-6">
            <header className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold">System Admin Command Center</h1>
                    <p className="text-text-muted">Welcome back, {user?.username}</p>
                </div>
            </header>

            {user?.role === 'Admin' ? (
                <>
                    {/* Live System Stats Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
                        <StatCard icon={<FiUsers />} title="Total Users" value={stats.totalUsers} color="text-primary" />
                        <StatCard icon={<FiActivity />} title="Online Users" value={stats.onlineUsers} color="text-accent" />
                        <StatCard icon={<FiUsers />} title="Offline Users" value={stats.offlineUsers} color="text-text-muted" />
                        <StatCard icon={<FiCheckCircle />} title="Approved Users" value={stats.approvedUsers} color="text-accent" />
                        <StatCard icon={<FiAlertTriangle />} title="Pending Approvals" value={stats.pendingApproval} color="text-yellow-500" />
                        <StatCard icon={<FiShield />} title="Rejected Users" value={stats.rejectedUsers} color="text-danger" />
                        <StatCard icon={<FiActivity />} title="Messages Sent Today" value={stats.messagesSentToday} color="text-primary" />
                        <StatCard icon={<FiCheckCircle />} title="Messages Received Today" value={stats.messagesReceivedToday} color="text-accent" />
                        <StatCard icon={<FiCheckCircle />} title="Successful Deliveries" value={stats.successfulDeliveries} color="text-accent" />
                        <StatCard icon={<FiAlertTriangle />} title="Failed Deliveries" value={stats.failedDeliveries} color="text-danger" />
                        <StatCard icon={<FiActivity />} title="Current Active Sessions" value={stats.activeSessions} color="text-primary" />
                        <StatCard icon={<FiCpu />} title="Communication Logs" value={aiMetrics?.totalCommunicationLogs || 0} color="text-primary" />
                    </div>

                    {/* OBJECTIVE 1 — AI THREAT DETECTION & CONTINUOUS LEARNING */}
                    <div className="glass-panel p-6 mb-8 border border-primary/20">
                        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4 border-b border-white/10 pb-4">
                            <div>
                                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                    <FiCpu className="text-primary" /> AI Threat Detection & Continuous Learning
                                </h2>
                                <p className="text-xs text-text-muted mt-1">Multi-model behavioral security guard trained on CIC-IDS2017 & real application logs.</p>
                            </div>
                            <div className="flex flex-wrap gap-2">
                                <button onClick={handleTrainModel} disabled={aiLoading} className="btn-secondary text-xs flex items-center gap-1">
                                    <FiRefreshCw className={aiLoading ? "animate-spin" : ""} /> Train Model
                                </button>
                                <button onClick={handleRetrainModel} disabled={aiLoading} className="btn-primary text-xs flex items-center gap-1">
                                    <FiRefreshCw className={aiLoading ? "animate-spin" : ""} /> Retrain Model
                                </button>
                                <button onClick={handleExportDataset} className="btn-secondary text-xs flex items-center gap-1">
                                    <FiDatabase /> Export Dataset
                                </button>
                            </div>
                        </div>

                        {aiActionMessage && <div className="text-xs text-primary bg-primary/10 p-3 rounded-lg mb-4 animate-pulse">{aiActionMessage}</div>}

                        {activeVersion ? (
                            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
                                <div className="bg-surface/50 p-3 rounded-lg border border-white/5">
                                    <span className="text-[10px] text-text-muted uppercase">Active Model</span>
                                    <p className="text-sm font-bold text-white truncate">{activeVersion.model_type}</p>
                                </div>
                                <div className="bg-surface/50 p-3 rounded-lg border border-white/5">
                                    <span className="text-[10px] text-text-muted uppercase">Version</span>
                                    <p className="text-sm font-bold text-primary">{activeVersion.version}</p>
                                </div>
                                <div className="bg-surface/50 p-3 rounded-lg border border-white/5">
                                    <span className="text-[10px] text-text-muted uppercase">Accuracy</span>
                                    <p className="text-sm font-bold text-accent">{(activeVersion.accuracy * 100).toFixed(1)}%</p>
                                </div>
                                <div className="bg-surface/50 p-3 rounded-lg border border-white/5">
                                    <span className="text-[10px] text-text-muted uppercase">F1 Score</span>
                                    <p className="text-sm font-bold text-accent">{(activeVersion.f1_score * 100).toFixed(1)}%</p>
                                </div>
                                <div className="bg-surface/50 p-3 rounded-lg border border-white/5">
                                    <span className="text-[10px] text-text-muted uppercase">Recall</span>
                                    <p className="text-sm font-bold text-white">{(activeVersion.recall * 100).toFixed(1)}%</p>
                                </div>
                                <div className="bg-surface/50 p-3 rounded-lg border border-white/5">
                                    <span className="text-[10px] text-text-muted uppercase">ROC-AUC</span>
                                    <p className="text-sm font-bold text-white">{(activeVersion.roc_auc * 100).toFixed(1)}%</p>
                                </div>
                            </div>
                        ) : (
                            <div className="text-center p-4 text-text-muted text-sm">No trained AI model version found. Click "Train Model" to initialize.</div>
                        )}

                        {/* Visual Metrics Buttons */}
                        {aiMetrics?.images && (
                            <div className="flex flex-wrap gap-4 border-t border-white/10 pt-4">
                                {aiMetrics.images.confusionMatrix && (
                                    <button onClick={() => setActiveModalImage({ title: "Confusion Matrix", src: `data:image/png;base64,${aiMetrics.images.confusionMatrix}` })} className="btn-secondary text-xs flex items-center gap-2">
                                        <FiBarChart2 className="text-primary"/> View Confusion Matrix
                                    </button>
                                )}
                                {aiMetrics.images.rocCurve && (
                                    <button onClick={() => setActiveModalImage({ title: "ROC Curve", src: `data:image/png;base64,${aiMetrics.images.rocCurve}` })} className="btn-secondary text-xs flex items-center gap-2">
                                        <FiBarChart2 className="text-primary"/> View ROC Curve
                                    </button>
                                )}
                                {aiMetrics.images.featureImportance && (
                                    <button onClick={() => setActiveModalImage({ title: "Feature Importance", src: `data:image/png;base64,${aiMetrics.images.featureImportance}` })} className="btn-secondary text-xs flex items-center gap-2">
                                        <FiBarChart2 className="text-primary"/> View Feature Importance
                                    </button>
                                )}
                            </div>
                        )}
                    </div>

                    {/* OBJECTIVE 2 — FORMAL SECURITY EVALUATION & PENETRATION TESTING FRAMEWORK */}
                    <div className="glass-panel p-6 mb-8 border border-danger/20">
                        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4 border-b border-white/10 pb-4">
                            <div>
                                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                                    <FiShield className="text-danger" /> Formal Security Evaluation & Penetration Testing
                                </h2>
                                <p className="text-xs text-text-muted mt-1">Controlled penetration testing framework evaluating Tampering, Replay, MITM, Auth, Integrity & Flooding.</p>
                            </div>
                            <div className="flex items-center gap-3">
                                <label className="text-xs text-text-muted">Attempts per Category:</label>
                                <select value={secScale} onChange={(e) => setSecScale(Number(e.target.value))} className="bg-surface border border-white/10 text-xs rounded px-2 py-1 text-white">
                                    <option value={10}>10</option>
                                    <option value={50}>50</option>
                                    <option value={100}>100 (Default)</option>
                                    <option value={500}>500</option>
                                    <option value={1000}>1000</option>
                                </select>
                                <button onClick={handleRunSecurityTests} disabled={secTestRunning} className="btn-primary bg-danger hover:bg-danger/80 text-xs flex items-center gap-1">
                                    <FiPlay className={secTestRunning ? "animate-spin" : ""} /> {secTestRunning ? "Executing Suite..." : "Run Security Test Suite"}
                                </button>
                            </div>
                        </div>

                        {/* Real-time Socket.IO Test Monitor */}
                        {secLiveProgress && (
                            <div className="bg-surface/50 p-4 rounded-lg border border-danger/30 mb-6 font-mono text-xs">
                                <div className="flex justify-between items-center text-danger font-bold mb-2">
                                    <span>LIVE SECURITY TEST STREAM</span>
                                    <span className="animate-pulse">{secLiveProgress.status || "RUNNING"}</span>
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-text-muted">
                                    <div>Attack: <span className="text-white font-bold">{secLiveProgress.attackType || "Initialization"}</span></div>
                                    <div>Progress: <span className="text-white font-bold">{secLiveProgress.attempt || 0} / {secLiveProgress.total || secScale}</span></div>
                                    <div>AI Risk: <span className="text-yellow-400 font-bold">{secLiveProgress.aiRisk || "Analyzing"}</span></div>
                                    <div>Latency: <span className="text-accent font-bold">{secLiveProgress.latencyMs || 0} ms</span></div>
                                </div>
                            </div>
                        )}

                        {/* Security Evaluation Results Table */}
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="border-b border-white/10 text-text-muted text-xs uppercase">
                                        <th className="p-2">Attack Vector</th>
                                        <th className="p-2">Attempts</th>
                                        <th className="p-2">Detected</th>
                                        <th className="p-2">Missed</th>
                                        <th className="p-2">Detection Rate</th>
                                        <th className="p-2">FPR</th>
                                        <th className="p-2">Avg Latency</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {secResults.length > 0 ? secResults.slice(0, 6).map((res, idx) => (
                                        <tr key={idx} className="border-b border-white/5 hover:bg-white/5 text-sm font-mono">
                                            <td className="p-2 font-bold text-white">{res.attackType}</td>
                                            <td className="p-2 text-text-muted">{res.totalAttempts}</td>
                                            <td className="p-2 text-accent font-bold">{res.detectedAttempts}</td>
                                            <td className="p-2 text-danger">{res.missedAttempts}</td>
                                            <td className="p-2 text-accent font-bold">{res.detectionRate}%</td>
                                            <td className="p-2 text-text-muted">{res.falsePositiveRate}%</td>
                                            <td className="p-2 text-primary">{res.avgDetectionLatencyMs} ms</td>
                                        </tr>
                                    )) : (
                                        <tr>
                                            <td colSpan="7" className="p-4 text-center text-text-muted font-bold">No security evaluation results available yet. Click "Run Security Test Suite" to execute.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Encryption Load Matrix & Pending Approvals Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                        <div className="glass-panel p-6">
                            <h3 className="text-lg font-bold mb-4">Encryption Load Matrix (AES-256-GCM)</h3>
                            <Line options={chartOptions} data={performanceData} />
                        </div>
                        
                        <div className="glass-panel p-6 flex flex-col">
                            <h3 className="text-lg font-bold mb-4 flex justify-between items-center">
                                Pending User Approvals
                                {pendingUsers.length > 0 && <span className="text-xs bg-yellow-500/20 text-yellow-500 px-2 py-1 rounded-full animate-pulse">{pendingUsers.length} PENDING</span>}
                            </h3>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="border-b border-white/10 text-text-muted text-sm">
                                            <th className="p-2">Username</th>
                                            <th className="p-2">Email</th>
                                            <th className="p-2">Role</th>
                                            <th className="p-2">Registration Date & Time</th>
                                            <th className="p-2">Status</th>
                                            <th className="p-2">Action Buttons</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {pendingUsers.length > 0 ? pendingUsers.map((u) => (
                                            <tr key={u._id} className="border-b border-white/5 hover:bg-white/5 text-sm">
                                                <td className="p-2 font-bold">{u.username}</td>
                                                <td className="p-2">{u.email}</td>
                                                <td className="p-2">{u.role}</td>
                                                <td className="p-2 text-xs text-text-muted">{new Date(u.createdAt).toLocaleString()}</td>
                                                <td className="p-2 text-yellow-500">{u.status}</td>
                                                <td className="p-2">
                                                    <div style={{ display: 'flex', gap: '8px' }}>
                                                        <button 
                                                            onClick={() => handleApproval(u._id, 'approve')} 
                                                            disabled={processingUsers[u._id]}
                                                            style={{
                                                                backgroundColor: '#10b981',
                                                                color: '#ffffff',
                                                                padding: '6px 14px',
                                                                borderRadius: '6px',
                                                                border: 'none',
                                                                cursor: processingUsers[u._id] ? 'not-allowed' : 'pointer',
                                                                opacity: processingUsers[u._id] ? 0.6 : 1,
                                                                fontWeight: '600',
                                                                display: 'inline-flex',
                                                                alignItems: 'center',
                                                                gap: '6px'
                                                            }}
                                                        >
                                                            <FiCheck />
                                                            {processingUsers[u._id] ? "Processing..." : "Approve"}
                                                        </button>
                                                        <button 
                                                            onClick={() => handleApproval(u._id, 'reject')} 
                                                            disabled={processingUsers[u._id]}
                                                            style={{
                                                                backgroundColor: '#ef4444',
                                                                color: '#ffffff',
                                                                padding: '6px 14px',
                                                                borderRadius: '6px',
                                                                border: 'none',
                                                                cursor: processingUsers[u._id] ? 'not-allowed' : 'pointer',
                                                                opacity: processingUsers[u._id] ? 0.6 : 1,
                                                                fontWeight: '600',
                                                                display: 'inline-flex',
                                                                alignItems: 'center',
                                                                gap: '6px'
                                                            }}
                                                        >
                                                            <FiX />
                                                            {processingUsers[u._id] ? "Processing..." : "Reject"}
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        )) : (
                                            <tr>
                                                <td colSpan="6" className="p-4 text-center text-text-muted font-bold text-lg">No pending approval requests.</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    {/* Recent Security Events Table */}
                    <div className="glass-panel p-6">
                        <h3 className="text-lg font-bold mb-4 flex justify-between items-center">
                            Recent Security Events
                            {stats.securityEvents.length > 0 && <span className="text-xs bg-danger/20 text-danger px-2 py-1 rounded-full animate-pulse">LIVE</span>}
                        </h3>
                        <div className="overflow-x-auto max-h-[400px]">
                            <table className="w-full text-left border-collapse">
                                <thead className="sticky top-0 bg-[#0f172a]">
                                    <tr className="border-b border-white/10 text-text-muted text-sm">
                                        <th className="p-2">Timestamp</th>
                                        <th className="p-2">Username</th>
                                        <th className="p-2">Event Type</th>
                                        <th className="p-2">Description</th>
                                        <th className="p-2">Severity</th>
                                        <th className="p-2">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {stats.securityEvents.length > 0 ? stats.securityEvents.map((evt, idx) => (
                                        <tr key={idx} className="border-b border-white/5 hover:bg-white/5 text-sm">
                                            <td className="p-2 text-xs text-text-muted">{new Date(evt.timestamp).toLocaleString()}</td>
                                            <td className="p-2 font-bold">{evt.username}</td>
                                            <td className="p-2 text-danger">{evt.eventType || evt.event}</td>
                                            <td className="p-2 text-text-muted font-mono text-xs">{evt.description || evt.details}</td>
                                            <td className="p-2">{evt.role || evt.severity}</td>
                                            <td className="p-2">{evt.status || "Unknown"}</td>
                                        </tr>
                                    )) : (
                                        <tr>
                                            <td colSpan="6" className="p-4 text-center text-text-muted">No recent security anomalies detected.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            ) : (
                <div className="glass-panel p-12 text-center">
                    <FiShield className="mx-auto text-6xl text-primary mb-4" />
                    <h2 className="text-2xl font-bold mb-2">Access Restricted</h2>
                    <p className="text-text-muted mb-6">You need Admin clearance to view the monitoring dashboard.</p>
                </div>
            )}

            {/* Modal for AI Metric Images */}
            {activeModalImage && (
                <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4" onClick={() => setActiveModalImage(null)}>
                    <div className="glass-panel p-6 max-w-2xl w-full flex flex-col items-center" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-between items-center w-full mb-4">
                            <h3 className="text-lg font-bold text-white">{activeModalImage.title}</h3>
                            <button onClick={() => setActiveModalImage(null)} className="text-white hover:text-danger"><FiX className="text-xl"/></button>
                        </div>
                        <img src={activeModalImage.src} alt={activeModalImage.title} className="max-h-[500px] object-contain rounded-lg border border-white/10" />
                    </div>
                </div>
            )}
        </div>
    );
};

const StatCard = ({ icon, title, value, color }) => (
    <div className="glass-panel p-6 flex items-center gap-4">
        <div className={`text-3xl ${color} bg-surface p-3 rounded-xl`}>
            {icon}
        </div>
        <div>
            <p className="text-sm text-text-muted">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
        </div>
    </div>
);

export default Dashboard;
