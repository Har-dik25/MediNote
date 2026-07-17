import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { ApiError } from '../api/index.js';

export default function LoginPage() {
  const { status, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (status === 'authenticated') {
    const redirectTo = location.state?.from || '/';
    return <Navigate to={redirectTo} replace />;
  }

  function validate() {
    const errors = {};
    if (!email.trim()) errors.email = 'Enter your work email.';
    else if (!/^\S+@\S+\.\S+$/.test(email.trim())) errors.email = 'Enter a valid email address.';
    if (!password) errors.password = 'Enter your password.';
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError('');
    if (!validate()) return;
    setSubmitting(true);
    try {
      await login(email.trim(), password);
      navigate(location.state?.from || '/', { replace: true });
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Could not sign in. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <div className="auth-card__brand">
          <span className="brand__mark" style={{ width: 34, height: 34 }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" width="16" height="16">
              <path d="M11 2v20M2 11h20" style={{ stroke: '#12213A' }} />
            </svg>
          </span>
          <div className="brand__name" style={{ fontSize: '1.15rem' }}>MediMate</div>
        </div>
        <h1>Sign in to your workspace</h1>
        <p className="auth-sub">Use your clinic-issued credentials to access encounters and notes.</p>

        {formError && (
          <div className="banner banner--danger" role="alert" style={{ marginBottom: 16 }}>
            <span className="banner__icon" aria-hidden="true">!</span>
            <p className="banner__text">{formError}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="auth-field">
            <label className="field-label" htmlFor="email">Work email</label>
            <input
              id="email"
              type="email"
              className="text-input"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-invalid={!!fieldErrors.email}
              aria-describedby={fieldErrors.email ? 'email-error' : undefined}
            />
            {fieldErrors.email && <p className="field-error" id="email-error">{fieldErrors.email}</p>}
          </div>

          <div className="auth-field">
            <label className="field-label" htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              className="text-input"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              aria-invalid={!!fieldErrors.password}
              aria-describedby={fieldErrors.password ? 'password-error' : undefined}
            />
            {fieldErrors.password && <p className="field-error" id="password-error">{fieldErrors.password}</p>}
          </div>

          <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: 6 }} disabled={submitting}>
            {submitting && <span className="spinner" aria-hidden="true" />}
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="auth-footer">New to MediMate? <Link to="/signup">Create an account</Link></p>
      </div>
    </div>
  );
}
