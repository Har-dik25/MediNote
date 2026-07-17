import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { api, ApiError } from '../api/index.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState('loading'); // 'loading' | 'authenticated' | 'anonymous'

  useEffect(() => {
    let cancelled = false;
    api.me()
      .then((res) => { if (!cancelled) { setUser(res.user); setStatus('authenticated'); } })
      .catch(() => { if (!cancelled) { setUser(null); setStatus('anonymous'); } });
    return () => { cancelled = true; };
  }, []);

  const login = useCallback(async (email, password) => {
    const res = await api.login(email, password);
    setUser(res.user);
    setStatus('authenticated');
    return res.user;
  }, []);

  const signup = useCallback(async (payload) => {
    const res = await api.signup(payload);
    setUser(res.user);
    setStatus('authenticated');
    return res.user;
  }, []);

  const logout = useCallback(async () => {
    try { await api.logout(); } catch { /* proceed to clear client state regardless */ }
    setUser(null);
    setStatus('anonymous');
  }, []);

  const updateUser = useCallback(async (fields) => {
    const res = await api.updateProfile(fields);
    setUser(res.user);
    return res.user;
  }, []);

  return (
    <AuthContext.Provider value={{ user, status, login, signup, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export { ApiError };
