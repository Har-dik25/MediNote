import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { api, ApiError } from '../api/index.js';
import Banner from '../components/Banner.jsx';

export default function PatientProfilePage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const [patientRes, notesRes] = await Promise.all([
          api.getPatient(id),
          api.listNotes({ patientId: id })
        ]);
        if (!cancelled) {
          setPatient(patientRes.patient);
          setNotes(notesRes.items);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.message : 'Could not load patient.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [id]);

  function startEncounter() {
    navigate('/', { state: { patientId: id } });
  }

  async function handleDeleteNote(noteId) {
    if (!window.confirm("Are you sure you want to delete this note? This cannot be undone.")) return;
    try {
      await api.deleteNote(noteId);
      setNotes(notes.filter(n => n.id !== noteId));
    } catch (err) {
      alert("Failed to delete note.");
    }
  }

  async function handleClearAllHistory() {
    if (!window.confirm("Are you sure you want to delete ALL notes for this patient? This cannot be undone.")) return;
    try {
      await api.deleteNotesForPatient(id);
      setNotes([]);
    } catch (err) {
      alert("Failed to clear history.");
    }
  }

  if (loading) {
    return (
      <div>
        <div className="skeleton" style={{ height: 60, marginBottom: 24 }} />
        <div className="skeleton" style={{ height: 200 }} />
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div>
        <Banner variant="danger" title="Error">{error || 'Patient not found'}</Banner>
        <button className="btn-outline" onClick={() => navigate('/patients')}>← Back to Patients</button>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <button type="button" className="link-btn" onClick={() => navigate('/patients')} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, marginBottom: 12, padding: 0 }}>
            ← Back to all patients
          </button>
          <h1 className="page-title">{patient.name}</h1>
          <p className="page-subtitle" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}>
            MRN: <strong style={{ color: 'var(--teal-dark)' }}>{patient.mrn}</strong>
            {patient.dob && ` • DOB: ${patient.dob}`}
            {patient.phone && ` • Phone: ${patient.phone}`}
          </p>
        </div>
        <button type="button" className="btn-primary" onClick={startEncounter}>
          Start new encounter
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 24, alignItems: 'start' }}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>Clinical History</h3>
            {notes.length > 0 && (
              <button 
                type="button" 
                className="btn-outline" 
                style={{ color: 'var(--danger)', borderColor: 'var(--danger)', padding: '4px 8px', fontSize: '0.75rem' }}
                onClick={handleClearAllHistory}
              >
                Clear all history
              </button>
            )}
          </div>
          
          {notes.length === 0 ? (
            <div className="card table-empty">
              <p>No encounters documented yet.</p>
            </div>
          ) : (
            <div className="timeline" style={{ position: 'relative', paddingLeft: 24, marginLeft: 12, borderLeft: '2px solid var(--rule)' }}>
              {notes.map((note, i) => (
                <motion.div
                  key={note.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.08 }}
                  style={{ position: 'relative', marginBottom: 24 }}
                >
                  <div style={{
                    position: 'absolute', left: -31, top: 4,
                    width: 12, height: 12, borderRadius: '50%',
                    background: note.status === 'approved' ? 'var(--success)' : 'var(--amber)',
                    border: '2px solid var(--paper)'
                  }} />
                  <div className="card" style={{ padding: '16px 20px', margin: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--ink-faint)' }}>
                        {new Date(note.createdAt).toLocaleString()}
                      </div>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <button 
                          type="button" 
                          className="link-btn" 
                          style={{ color: 'var(--danger)', padding: 0, fontSize: '0.8rem' }}
                          onClick={() => handleDeleteNote(note.id)}
                          title="Delete Note"
                        >
                          Delete
                        </button>
                        <span className={`status-pill status-pill--${note.status === 'approved' ? 'approved' : 'draft'}`}>
                          {note.status}
                        </span>
                      </div>
                    </div>
                    
                    <div>
                      <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', fontWeight: 600, letterSpacing: '0.05em', color: 'var(--teal-dark)', textTransform: 'uppercase', marginBottom: 4 }}>Subjective</p>
                      <p style={{ fontSize: '0.85rem', color: 'var(--ink-soft)', margin: '0 0 12px', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                        {note.soap.subjective}
                      </p>

                      <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', fontWeight: 600, letterSpacing: '0.05em', color: 'var(--teal-dark)', textTransform: 'uppercase', marginBottom: 4 }}>Assessment</p>
                      <p style={{ fontSize: '0.85rem', color: 'var(--ink-soft)', margin: '0 0 12px' }}>
                        {note.soap.assessment}
                      </p>
                    </div>

                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--rule)' }}>
                      {note.icd10.map(icd => (
                        <span key={icd.code} style={{ background: 'var(--paper-alt)', padding: '2px 6px', borderRadius: 4, fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: 'var(--ink)' }}>
                          {icd.code}
                        </span>
                      ))}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="card">
            <h3 style={{ fontSize: '0.95rem', marginBottom: 16 }}>Patient Details</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--ink-faint)', fontWeight: 600 }}>Full Name</div>
                <div style={{ fontSize: '0.85rem' }}>{patient.name}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--ink-faint)', fontWeight: 600 }}>Medical Record Number</div>
                <div style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)' }}>{patient.mrn}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--ink-faint)', fontWeight: 600 }}>Date of Birth</div>
                <div style={{ fontSize: '0.85rem' }}>{patient.dob || 'Not provided'}</div>
              </div>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--ink-faint)', fontWeight: 600 }}>Phone</div>
                <div style={{ fontSize: '0.85rem' }}>{patient.phone || 'Not provided'}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
