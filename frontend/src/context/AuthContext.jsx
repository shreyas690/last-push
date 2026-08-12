import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';
import socket from '../services/socket';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');
        if (token && storedUser) {
            setUser(JSON.parse(storedUser));
            socket.connect();
        }
        setLoading(false);
    }, []);

    const login = async (username, password, isAdmin = false) => {
        const endpoint = isAdmin ? '/auth/admin/login' : '/auth/login';
        const response = await api.post(endpoint, { username, password });
        
        // If regular user requires face verification step
        if (response.data.requiresFaceVerification) {
            return response.data;
        }

        const { access_token, user } = response.data;
        localStorage.setItem('token', access_token);
        localStorage.setItem('user', JSON.stringify(user));
        setUser(user);
        socket.connect();
        return { user, success: true };
    };

    const verifyFace = async (username, faceData) => {
        const response = await api.post('/auth/verify-face', { username, faceData });
        const { access_token, user } = response.data;
        localStorage.setItem('token', access_token);
        localStorage.setItem('user', JSON.stringify(user));
        setUser(user);
        socket.connect();
        return user;
    };

    const register = async (username, password, email, faceData, role = "User") => {
        const response = await api.post('/auth/register', {
            username,
            password,
            email,
            faceData,
            role
        });
        return response.data;
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
        socket.disconnect();
    };

    return (
        <AuthContext.Provider value={{ user, login, verifyFace, register, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
