import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { ApiError } from '../api/index.js';

const SPECIALTIES = ['General practice', 'Internal medicine', 'Pediatrics', 'Cardiology', 'Psychiatry', 'Other'];
const REGIONS = ['UK (NICE)', 'US (USPSTF)', 'EU (EMA)'];

export default function SignupPage() {
  const { status, signup } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: '', email: '', password: '', confirmPassword: '',
    clinicName: '', specialty: SPECIALTIES[0], phone: '', region: REGIONS[0]
  });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (status === 'authenticated') return <Navigate to="/" replace />;

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  function validate() {
    const e = {};
    if (!form.name.trim()) e.name = 'Enter your full name.';
    if (!form.email.trim()) e.email = 'Enter your work email.';
    else if (!/^\S+@\S+\.\S+$/.test(form.email.trim())) e.email = 'Enter a valid email address.';
    if (!form.password || form.password.length < 8) e.password = 'Use at least 8 characters.';
    if (form.confirmPassword !== form.password) e.confirmPassword = 'Passwords do not match.';
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSubmit(ev) {
    ev.preventDefault();
    setFormError('');
    if (!validate()) return;
    setSubmitting(true);
    try {
      await signup({
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
        clinicName: form.clinicName.trim(),
        specialty: form.specialty,
        phone: form.phone.trim(),
        region: form.region
      });
      navigate('/', { replace: true });
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Could not create your account. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-card" style={{ maxWidth: 460 }}>
        <div className="auth-card__brand">
          <span className="brand__mark" style={{ width: 34, height: 34 }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" width="16" height="16">
              <path d="M11 2v20M2 11h20" style={{ stroke: '#12213A' }} />
            </svg>
          </span>
          <div className="brand__name" style={{ fontSize: '1.15rem' }}>MediMate</div>
        </div>
        <h1>Create your workspace</h1>
        <p className="auth-sub">Tell us about you and your practice — this fills in your profile, so there's nothing to redo later.</p>

        {formError && (
          <div className="banner banner--danger" role="alert" style={{ marginBottom: 16 }}>
            <span className="banner__icon" aria-hidden="true">!</span>
            <p className="banner__text">{formError}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <FieldRow label="Full name" htmlFor="name" error={errors.name}>
            <input id="name" className="text-input" autoComplete="name" value={form.name} onChange={(e) => set('name', e.target.value)} />
          </FieldRow>

          <FieldRow label="Work email" htmlFor="email" error={errors.email}>
            <input id="email" type="email" className="text-input" autoComplete="username" value={form.email} onChange={(e) => set('email', e.target.value)} />
          </FieldRow>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <FieldRow label="Password" htmlFor="password" error={errors.password}>
              <input id="password" type="password" className="text-input" autoComplete="new-password" value={form.password} onChange={(e) => set('password', e.target.value)} />
            </FieldRow>
            <FieldRow label="Confirm password" htmlFor="confirmPassword" error={errors.confirmPassword}>
              <input id="confirmPassword" type="password" className="text-input" autoComplete="new-password" value={form.confirmPassword} onChange={(e) => set('confirmPassword', e.target.value)} />
            </FieldRow>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <FieldRow label="Specialty" htmlFor="specialty">
              <select id="specialty" className="select-input" value={form.specialty} onChange={(e) => set('specialty', e.target.value)}>
                {SPECIALTIES.map((s) => <option key={s}>{s}</option>)}
              </select>
            </FieldRow>
            <FieldRow label="Guideline region" htmlFor="region">
              <select id="region" className="select-input" value={form.region} onChange={(e) => set('region', e.target.value)}>
                {REGIONS.map((r) => <option key={r}>{r}</option>)}
              </select>
            </FieldRow>
          </div>

          <FieldRow label="Phone (optional)" htmlFor="phone">
            <input id="phone" type="tel" className="text-input" autoComplete="tel" value={form.phone} onChange={(e) => set('phone', e.target.value)} />
          </FieldRow>

          <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: 6 }} disabled={submitting}>
            {submitting && <span className="spinner" aria-hidden="true" />}
            {submitting ? 'Creating your workspace…' : 'Create account'}
          </button>
        </form>

        <p className="auth-footer">Already have an account? <Link to="/login">Sign in</Link></p>
      </div>
    </div>
  );
}

function FieldRow({ label, htmlFor, error, children }) {
  return (
    <div className="auth-field">
      <label className="field-label" htmlFor={htmlFor}>{label}</label>
      {children}
      {error && <p className="field-error" id={`${htmlFor}-error`}>{error}</p>}
    </div>
  );
}
