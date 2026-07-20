import { useEffect, useState } from 'react';
import { api, ApiError } from '../api/index.js';
import { useAuth } from '../context/AuthContext.jsx';
import { useToast } from '../context/ToastContext.jsx';
import Banner from '../components/Banner.jsx';

const SPECIALTIES = [
  'General practice', 'Internal medicine', 'Family medicine', 'Pediatrics', 
  'Cardiology', 'Dermatology', 'Endocrinology', 'Gastroenterology', 
  'Neurology', 'Oncology', 'Psychiatry', 'Rheumatology', 
  'Obstetrics and Gynecology', 'Orthopedics', 'Ophthalmology', 
  'Otolaryngology (ENT)', 'Urology', 'Emergency medicine', 
  'Anesthesiology', 'Radiology', 'Pathology', 'Surgery (General)', 
  'Pulmonology', 'Nephrology', 'Infectious Disease', 'Other'
];

export default function SettingsPage() {
  const { user, updateUser } = useAuth();
  const { showToast } = useToast();
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const [profileForm, setProfileForm] = useState(null);
  const [savingProfile, setSavingProfile] = useState(false);

  useEffect(() => {
    if (user && !profileForm) {
      setProfileForm({
        name: user.name || '',
        clinicName: user.clinicName || '',
        specialty: user.specialty || SPECIALTIES[0],
        phone: user.phone || ''
      });
    }
  }, [user, profileForm]);

  async function saveProfile(e) {
    e.preventDefault();
    setSavingProfile(true);
    try {
      await updateUser(profileForm);
      showToast('Profile updated.', 'success');
    } catch (err) {
      showToast(err instanceof ApiError ? err.message : 'Could not update your profile.', 'error');
    } finally {
      setSavingProfile(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    api.getSettings()
      .then((res) => { if (!cancelled) setSettings(res.settings); })
      .catch((err) => { if (!cancelled) setError(err instanceof ApiError ? err.message : 'Could not load settings.'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  async function persist(next) {
    setSettings(next);
    setSaving(true);
    try {
      await api.updateSettings(next);
      showToast('Settings saved.', 'success');
    } catch (err) {
      showToast(err instanceof ApiError ? err.message : 'Could not save settings.', 'error');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Manage your profile, guideline region, and notification preferences.</p>
        </div>
        {saving && <span style={{ fontSize: '0.8rem', color: 'var(--ink-faint)' }}>Saving…</span>}
      </div>

      {error && <Banner variant="danger" title="Could not load settings">{error}</Banner>}

      <div className="card">
        <div className="settings-section">
          <h2 className="settings-section__title">Profile</h2>
          <p className="settings-section__desc">This is what you entered when you signed up — update it any time.</p>

          {!profileForm ? (
            <div className="skeleton" style={{ height: 140 }} aria-label="Loading profile" role="status" />
          ) : (
            <form onSubmit={saveProfile}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
                <div>
                  <label className="field-label" htmlFor="profileName">Full name</label>
                  <input id="profileName" className="text-input" value={profileForm.name} onChange={(e) => setProfileForm({ ...profileForm, name: e.target.value })} />
                </div>
                <div>
                  <label className="field-label">Email</label>
                  <input className="text-input" value={user?.email || ''} disabled />
                  <p className="field-hint">Contact support to change your sign-in email.</p>
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
                <div>
                  <label className="field-label" htmlFor="profileClinic">Clinic / practice name</label>
                  <input id="profileClinic" className="text-input" value={profileForm.clinicName} onChange={(e) => setProfileForm({ ...profileForm, clinicName: e.target.value })} />
                </div>
                <div>
                  <label className="field-label" htmlFor="profileSpecialty">Specialty</label>
                  <select id="profileSpecialty" className="select-input" value={profileForm.specialty} onChange={(e) => setProfileForm({ ...profileForm, specialty: e.target.value })}>
                    {SPECIALTIES.map((s) => <option key={s}>{s}</option>)}
                  </select>
                </div>
              </div>
              <div style={{ marginBottom: 16, maxWidth: 260 }}>
                <label className="field-label" htmlFor="profilePhone">Phone</label>
                <input id="profilePhone" type="tel" className="text-input" value={profileForm.phone} onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })} />
              </div>
              <button type="submit" className="btn-primary" disabled={savingProfile}>
                {savingProfile && <span className="spinner" aria-hidden="true" />}
                {savingProfile ? 'Saving…' : 'Save profile'}
              </button>
            </form>
          )}
        </div>
      </div>

      <div className="card">
        {loading || !settings ? (
          <div className="skeleton" style={{ height: 160 }} aria-label="Loading settings" role="status" />
        ) : (
          <>
            <div className="settings-section">
              <h2 className="settings-section__title">Clinical guidelines</h2>
              <p className="settings-section__desc">Which regional guideline set to ground note generation in. Set during sign-up, editable here.</p>
              <div className="settings-row">
                <div>
                  <div className="settings-row__label">Guideline region</div>
                  <div className="settings-row__hint">Affects RAG retrieval source for the guideline lookup tool.</div>
                </div>
                <select
                  className="select-input"
                  style={{ width: 200 }}
                  value={user?.region || 'UK (NICE)'}
                  onChange={(e) => updateUser({ region: e.target.value }).catch(() => showToast('Could not update region.', 'error'))}
                >
                  <option>UK (NICE)</option>
                  <option>US (USPSTF)</option>
                  <option>EU (EMA)</option>
                  <option>WHO (Global)</option>
                </select>
              </div>
            </div>

            <div className="settings-section">
              <h2 className="settings-section__title">Notifications</h2>
              <div className="settings-row">
                <div>
                  <div className="settings-row__label">Email notifications</div>
                  <div className="settings-row__hint">Get notified when a note needs review.</div>
                </div>
                <ToggleSwitch
                  checked={settings.emailNotifications}
                  onChange={(v) => persist({ ...settings, emailNotifications: v })}
                  label="Email notifications"
                />
              </div>
              <div className="settings-row">
                <div>
                  <div className="settings-row__label">Clinical safety alerts</div>
                  <div className="settings-row__hint">Show the on-screen banner when a note flags a time-critical symptom.</div>
                </div>
                <ToggleSwitch
                  checked={settings.safetyAlerts}
                  onChange={(v) => persist({ ...settings, safetyAlerts: v })}
                  label="Clinical safety alerts"
                />
              </div>
            </div>

            <div className="settings-section">
              <h2 className="settings-section__title">Session</h2>
              <div className="settings-row">
                <div>
                  <div className="settings-row__label">Auto sign-out after inactivity</div>
                  <div className="settings-row__hint">Minutes of inactivity before you're signed out, to protect patient data on shared devices.</div>
                </div>
                <select
                  className="select-input"
                  style={{ width: 140 }}
                  value={settings.autoLogoutMinutes}
                  onChange={(e) => persist({ ...settings, autoLogoutMinutes: Number(e.target.value) })}
                >
                  <option value={5}>5 minutes</option>
                  <option value={15}>15 minutes</option>
                  <option value={30}>30 minutes</option>
                </select>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ToggleSwitch({ checked, onChange, label }) {
  return (
    <label className="toggle" aria-label={label}>
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span className="toggle__track" />
      <span className="toggle__thumb" />
    </label>
  );
}
