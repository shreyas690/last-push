import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Terminal from './pages/Terminal';
import Attacker from './pages/Attacker';
import AdminLogin from './pages/AdminLogin';

const ProtectedRoute = ({ children, roles }) => {
  const { user, loading } = useAuth();
  
  if (loading) return <div className="h-screen flex items-center justify-center text-white">Initializing Secure Environment...</div>;
  
  if (!user) return <Navigate to="/login" replace />;
  
  if (user.status === 'Pending' && !window.location.pathname.includes('/dashboard')) {
      return <div className="h-screen flex flex-col items-center justify-center text-white space-y-4">
          <h2 className="text-2xl text-yellow-500 font-bold">Access Pending</h2>
          <p className="text-text-muted">Your account is waiting for System Admin approval.</p>
          <button onClick={() => window.location.href='/login'} className="btn-secondary mt-4">Return to Login</button>
      </div>;
  }

  if (user.status === 'Rejected') {
      return <div className="h-screen flex items-center justify-center text-danger font-bold text-xl">Access Denied by System Admin.</div>;
  }
  
  if (roles && !roles.includes(user.role)) {
      if (user.role === 'Admin') return <Navigate to="/dashboard" replace />;
      if (user.role === 'User') return <Navigate to="/terminal" replace />;
      return <Navigate to="/login" replace />;
  }
  
  if (user.role === 'User' && !user.terminalAccess) {
      return <div className="h-screen flex items-center justify-center text-danger font-bold text-xl">Your account does not currently have permission to access the Secure Communication Terminal.</div>;
  }
  
  return children;
};

const App = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/dashboard" element={<ProtectedRoute roles={['Admin']}><Dashboard /></ProtectedRoute>} />
          <Route path="/terminal" element={<ProtectedRoute roles={['User']}><Terminal /></ProtectedRoute>} />
          <Route path="/attacker" element={<ProtectedRoute roles={['Admin', 'User']}><Attacker /></ProtectedRoute>} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
