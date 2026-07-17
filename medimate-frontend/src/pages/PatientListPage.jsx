import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { api, ApiError } from '../api/index.js';
import Banner from '../components/Banner.jsx';

export default function PatientListPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const handle = setTimeout(async () => {
      setLoading(true);
      setError('');
      try {
        const res = await api.listPatients({ query, page: '1' });
        if (!cancelled) setPatients(res.items);
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.message : 'Could not load patients.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 250); // debounce search input
    return () => { cancelled = true; clearTimeout(handle); };
  }, [query, refreshKey]);

  function startEncounter(patientId) {
    navigate(`/patients/${patientId}`);
  }

  function handlePatientAdded() {
    setShowAddForm(false);
    setRefreshKey((k) => k + 1);
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Patients</h1>
          <p className="page-subtitle">Search your panel and start a documented encounter.</p>
        </div>
        <button type="button" className="btn-primary" onClick={() => setShowAddForm((v) => !v)}>
          {showAddForm ? 'Cancel' : '+ Add patient'}
        </button>
      </div>

      <AnimatePresence>
        {showAddForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
            style={{ overflow: 'hidden' }}
          >
            <AddPatientForm onAdded={handlePatientAdded} onCancel={() => setShowAddForm(false)} />
          </motion.div>
        )}
      </AnimatePresence>

      <div className="card">
        <div className="search-row">
          <label className="sr-only" htmlFor="patientSearch">Search patients</label>
          <input
            id="patientSearch"
            className="text-input"
            placeholder="Search by name or MRN…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>

        {error && <Banner variant="danger" title="Could not load patients">{error}</Banner>}

        {loading ? (
          <div aria-hidden="true">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="skeleton" style={{ height: 44, marginBottom: 8 }} />
            ))}
          </div>
        ) : patients.length === 0 && query ? (
          <p className="table-empty">No patients match "{query}".</p>
        ) : patients.length === 0 ? (
          <div className="table-empty">
            <p style={{ marginBottom: 12 }}>No patients yet — add your first patient to start documenting encounters.</p>
            <button type="button" className="btn-outline" onClick={() => setShowAddForm(true)}>+ Add patient</button>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>MRN</th>
                <th>Date of birth</th>
                <th>Last visit</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((p, i) => (
                <motion.tr
                  key={p.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.18, delay: Math.min(i, 8) * 0.03 }}
                  className="is-clickable"
                  tabIndex={0}
                  role="button"
                  aria-label={`Start encounter for ${p.name}`}
                  onClick={() => startEncounter(p.id)}
                  onKeyDown={(e) => { if (e.key === 'Enter') startEncounter(p.id); }}
                >
                  <td>{p.name}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>{p.mrn}</td>
                  <td>{p.dob || '—'}</td>
                  <td>{p.lastVisit || 'No visits yet'}</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function AddPatientForm({ onAdded, onCancel }) {
  const [name, setName] = useState('');
  const [mrn, setMrn] = useState('');
  const [dob, setDob] = useState('');
  const [phone, setPhone] = useState('');
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  function validate() {
    const e = {};
    if (!name.trim()) e.name = 'Patient name is required.';
    if (!mrn.trim()) e.mrn = 'MRN is required.';
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  async function handleSubmit(ev) {
    ev.preventDefault();
    setFormError('');
    if (!validate()) return;
    setSubmitting(true);
    try {
      await api.createPatient({ name: name.trim(), mrn: mrn.trim(), dob, phone: phone.trim() });
      onAdded();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : 'Could not add this patient. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card">
      <p className="card__eyebrow">New patient</p>
      <h2 className="card__title" style={{ marginBottom: 16 }}>Add to your panel</h2>

      {formError && <Banner variant="danger" title="Could not add patient">{formError}</Banner>}

      <form onSubmit={handleSubmit} noValidate>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
          <div>
            <label className="field-label" htmlFor="pName">Full name</label>
            <input id="pName" className="text-input" value={name} onChange={(e) => setName(e.target.value)} />
            {errors.name && <p className="field-error">{errors.name}</p>}
          </div>
          <div>
            <label className="field-label" htmlFor="pMrn">MRN</label>
            <input id="pMrn" className="text-input" value={mrn} onChange={(e) => setMrn(e.target.value)} />
            {errors.mrn && <p className="field-error">{errors.mrn}</p>}
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
          <div>
            <label className="field-label" htmlFor="pDob">Date of birth</label>
            <input id="pDob" type="date" className="text-input" value={dob} onChange={(e) => setDob(e.target.value)} />
          </div>
          <div>
            <label className="field-label" htmlFor="pPhone">Phone (optional)</label>
            <input id="pPhone" type="tel" className="text-input" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button type="submit" className="btn-primary" disabled={submitting}>
            {submitting && <span className="spinner" aria-hidden="true" />}
            {submitting ? 'Adding…' : 'Add patient'}
          </button>
          <button type="button" className="btn-outline" onClick={onCancel}>Cancel</button>
        </div>
      </form>
    </div>
  );
}
