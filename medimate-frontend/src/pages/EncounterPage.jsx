import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import { api, ApiError } from '../api/index.js';
import { useToast } from '../context/ToastContext.jsx';
import Banner from '../components/Banner.jsx';
import AudioRecorder from '../components/AudioRecorder.jsx';

const MAX_AUDIO_BYTES = 25 * 1024 * 1024;
const ALLOWED_AUDIO_EXT = ['.mp3', '.wav'];
const ALLOWED_AUDIO_TYPES = ['audio/mpeg', 'audio/wav', 'audio/x-wav'];

function validateAudioFile(file) {
  const nameLower = file.name.toLowerCase();
  const hasExt = ALLOWED_AUDIO_EXT.some((ext) => nameLower.endsWith(ext));
  const hasType = !file.type || ALLOWED_AUDIO_TYPES.includes(file.type);
  if (!hasExt || !hasType) return 'Only .mp3 or .wav recordings are supported.';
  if (file.size > MAX_AUDIO_BYTES) return `That file is too large. Please upload a recording under ${Math.round(MAX_AUDIO_BYTES / (1024 * 1024))}MB.`;
  return null;
}

function stripHtml(html) {
  const tmp = document.createElement('DIV');
  tmp.innerHTML = html;
  return tmp.textContent || tmp.innerText || '';
}

export default function EncounterPage() {
  const location = useLocation();
  const { showToast } = useToast();
  const patientId = location.state?.patientId ?? null;

  const [tab, setTab] = useState('audio');
  const [transcript, setTranscript] = useState('');
  const [transcriptError, setTranscriptError] = useState('');
  const [audioFile, setAudioFile] = useState(null);
  const [uploadError, setUploadError] = useState('');
  const fileInputRef = useRef(null);

  const [generating, setGenerating] = useState(false);
  const [apiError, setApiError] = useState('');
  const [note, setNote] = useState(null); // { noteId, soap, icd10, tests, safetyFlag, safetyReason }
  const [status, setStatus] = useState('idle'); // draft | approved
  const [draftState, setDraftState] = useState('unsaved'); // unsaved | saving | saved | error
  const [isEditing, setIsEditing] = useState(false);
  const [editValues, setEditValues] = useState({});
  const [approving, setApproving] = useState(false);
  const [timestamp, setTimestamp] = useState(null);
  const generateControllerRef = useRef(null);

  const [stats, setStats] = useState({ seenToday: '-', drafts: '-', timeSaved: '-' });

  useEffect(() => {
    let cancelled = false;
    async function loadStats() {
      try {
        const res = await api.listNotes();
        if (cancelled) return;
        const notes = res.items || [];
        const today = new Date().toDateString();
        const seenToday = notes.filter(n => new Date(n.createdAt).toDateString() === today).length;
        const drafts = notes.filter(n => n.status === 'draft').length;
        const timeSaved = (notes.length * 0.25).toFixed(1) + ' hr';
        setStats({ seenToday, drafts, timeSaved });
      } catch (err) {
        // ignore
      }
    }
    loadStats();
    return () => {
      cancelled = true;
      generateControllerRef.current?.abort();
    };
  }, []);

  function onFileChange(e) {
    setUploadError('');
    const file = e.target.files?.[0];
    if (!file) return;
    const err = validateAudioFile(file);
    if (err) {
      setUploadError(err);
      setAudioFile(null);
      e.target.value = '';
      return;
    }
    setAudioFile(file);
  }

  async function handleGenerate() {
    setApiError('');
    setTranscriptError('');
    setUploadError('');

    if (tab === 'text' && !transcript.trim()) {
      setTranscriptError('Type or paste the encounter transcript first.');
      return;
    }
    if (tab === 'audio' && !audioFile) {
      setUploadError('Record or upload an audio file first.');
      return;
    }

    generateControllerRef.current?.abort();
    const controller = new AbortController();
    generateControllerRef.current = controller;

    setGenerating(true);
    try {
      let finalTranscript = transcript.trim();
      if (tab === 'audio') {
        const result = await api.transcribeAudio(audioFile);
        finalTranscript = result.transcript;
      }
      const generated = await api.generateNote(finalTranscript, patientId);
      if (controller.signal.aborted) return;
      setNote(generated);
      setStatus('draft');
      setDraftState('unsaved');
      setTimestamp(new Date());
      setIsEditing(false);
    } catch (err) {
      if (controller.signal.aborted) return;
      setApiError(err instanceof ApiError ? err.message : 'Could not generate the note. Please try again.');
    } finally {
      if (!controller.signal.aborted) setGenerating(false);
    }
  }

  function startEdit() {
    setEditValues({
      subjective: note.soap.subjective,
      objective: note.soap.objective,
      assessment: note.soap.assessment,
      plan: note.soap.plan,
    });
    setIsEditing(true);
  }

  async function saveEdit() {
    setDraftState('saving');
    try {
      await api.saveNote(note.noteId, editValues);
      setNote((prev) => ({ ...prev, soap: editValues }));
      setDraftState('saved');
      setIsEditing(false);
      showToast('Changes saved.', 'success');
    } catch (err) {
      setDraftState('error');
      showToast(err instanceof ApiError ? err.message : 'Could not save your edits.', 'error');
    }
  }

  async function handleApprove() {
    setApproving(true);
    try {
      await api.approveNote(note.noteId);
      setStatus('approved');
      setDraftState('saved');
      showToast('Note approved and saved.', 'success');
    } catch (err) {
      showToast(err instanceof ApiError ? err.message : 'Could not approve the note. Please try again.', 'error');
    } finally {
      setApproving(false);
    }
  }

  function copyToEHR() {
    const text = `SUBJECTIVE:\n${stripHtml(note.soap.subjective)}\n\nOBJECTIVE:\n${stripHtml(note.soap.objective)}\n\nASSESSMENT:\n${stripHtml(note.soap.assessment)}\n\nPLAN:\n${stripHtml(note.soap.plan)}`;
    navigator.clipboard.writeText(text);
    showToast('Copied to clipboard.', 'success');
  }

  return (
    <div className="workspace" style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 24, alignItems: 'start' }}>
      <aside className="no-print">
        <div className="card">
          <p className="card__eyebrow">New encounter</p>
          <h2 className="card__title">Record the visit</h2>
          <p className="card__subtitle">Record audio or type the encounter to generate a note.</p>

          <div className="input-tabs" role="tablist" style={{ display: 'flex', borderBottom: '1px solid var(--rule)', marginBottom: 14 }}>
            <button
              type="button" role="tab" aria-selected={tab === 'audio'}
              className="tab-btn" style={tabStyle(tab === 'audio')}
              onClick={() => setTab('audio')}
            >Audio</button>
            <button
              type="button" role="tab" aria-selected={tab === 'text'}
              className="tab-btn" style={tabStyle(tab === 'text')}
              onClick={() => setTab('text')}
            >Text</button>
          </div>

          {tab === 'audio' ? (
            <div>
              <AudioRecorder onRecordingComplete={(file) => { setAudioFile(file); setUploadError(''); }} />
              
              <div style={{ textAlign: 'center', marginTop: 12 }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--ink-soft)' }}>or </span>
                <button type="button" className="link-btn" onClick={() => fileInputRef.current?.click()} style={{ padding: 0, color: 'var(--teal-dark)' }}>
                  upload an existing audio file
                </button>
              </div>

              {audioFile && (
                <div style={{ marginTop: 16, padding: '12px 16px', background: 'var(--teal-tint)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.76rem', color: 'var(--teal-dark)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{audioFile.name}</div>
                  <button type="button" className="link-btn" style={{ color: 'var(--alert)', padding: 0 }} onClick={() => setAudioFile(null)}>Remove</button>
                </div>
              )}

              {uploadError && <p className="field-error" role="alert">{uploadError}</p>}
              <input ref={fileInputRef} type="file" accept=".mp3,.wav,audio/mpeg,audio/wav" style={{ display: 'none' }} onChange={onFileChange} />
            </div>
          ) : (
            <div>
              <label className="sr-only" htmlFor="transcript">Encounter transcript</label>
              <textarea
                id="transcript" className="text-input"
                placeholder="Patient presents with persistent cough for three weeks, mild fever, no shortness of breath..."
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
                autoComplete="off" spellCheck="false"
              />
              {transcriptError && <p className="field-error" role="alert">{transcriptError}</p>}
            </div>
          )}

          <button type="button" className="btn-primary" style={{ width: '100%', marginTop: 16 }} onClick={handleGenerate} disabled={generating}>
            {generating && <span className="spinner" aria-hidden="true" />}
            {generating ? 'Generating…' : 'Generate SOAP note'}
          </button>
        </div>

      </aside>

      <main>
        {!note && (
          <div style={{ padding: '20px 0' }}>
            <h2 className="page-title" style={{ fontSize: '1.4rem', marginBottom: 24 }}>Dashboard</h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 32 }}>
              <div className="card" style={{ padding: 16 }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--ink-faint)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Patients Seen Today</div>
                <div style={{ fontSize: '1.8rem', fontFamily: 'var(--font-display)', fontWeight: 600, color: 'var(--teal-dark)' }}>{stats.seenToday}</div>
              </div>
              <div className="card" style={{ padding: 16 }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--ink-faint)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Pending Drafts</div>
                <div style={{ fontSize: '1.8rem', fontFamily: 'var(--font-display)', fontWeight: 600, color: 'var(--amber)' }}>{stats.drafts}</div>
              </div>
              <div className="card" style={{ padding: 16 }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--ink-faint)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Time Saved</div>
                <div style={{ fontSize: '1.8rem', fontFamily: 'var(--font-display)', fontWeight: 600, color: 'var(--success)' }}>{stats.timeSaved}</div>
              </div>
            </div>

            <div className="card" style={{ padding: '40px 40px', textAlign: 'center' }}>
              <p style={{ maxWidth: 440, margin: '0 auto', color: 'var(--ink-soft)', fontSize: '0.9rem', lineHeight: 1.6 }}>
                Record live, upload a recording, or type an encounter to generate an evidence-based SOAP note, ICD-10 codes, and diagnostic test suggestions.
              </p>
            </div>
          </div>
        )}

        <div className="no-print">
          {apiError && <Banner variant="danger" title="Something went wrong">{apiError}</Banner>}

          {note?.safetyFlag && (
            <Banner variant="danger" title="Clinical safety alert">
              {note.safetyReason || 'Symptoms described may indicate a time-critical condition. Confirm escalation before finalizing this note.'}
            </Banner>
          )}

          {note && status !== 'approved' && (
            <Banner variant="info" title="AI-generated draft">
              This note was generated by an AI model and has not been clinically verified. A licensed clinician must review and approve it before it is used in patient care or billing.
            </Banner>
          )}
        </div>

        {note && (
          <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}>
            
            <div className="card print-card" style={{ padding: 0 }}>
              <div style={{ padding: '20px 26px', borderBottom: '1px solid var(--rule)', display: 'flex', justifyContent: 'space-between' }}>
                <div>
                  <h1 className="card__title">Clinical note</h1>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--ink-faint)' }}>
                    Generated · {timestamp?.toLocaleString() ?? '—'} · <span className="no-print">{draftState}</span>
                  </div>
                </div>
                <motion.span
                  key={status}
                  initial={{ scale: 0.85, opacity: 0.6 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 22 }}
                  className={`status-pill status-pill--${status === 'approved' ? 'approved' : 'draft'} no-print`}
                >
                  {status === 'approved' ? 'Approved' : 'Draft'}
                </motion.span>
              </div>

              <div style={{ padding: '22px 26px' }} className="quill-content">
                {['subjective', 'objective', 'assessment', 'plan'].map((key, i) => (
                  <motion.div
                    key={key}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.22, delay: i * 0.06, ease: [0.22, 1, 0.36, 1] }}
                    style={{ marginBottom: 18 }}
                  >
                    <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', fontWeight: 700, letterSpacing: '0.08em', color: 'var(--teal-dark)', margin: '0 0 6px', textTransform: 'uppercase' }}>{key}</p>
                    
                    {isEditing ? (
                      <ReactQuill theme="snow" value={editValues[key]} onChange={(val) => setEditValues(prev => ({ ...prev, [key]: val }))} />
                    ) : (
                      <div style={{ fontSize: '0.92rem', lineHeight: 1.65 }} dangerouslySetInnerHTML={{ __html: note.soap[key] }} />
                    )}
                  </motion.div>
                ))}
              </div>

              <div className="no-print" style={{ padding: '16px 26px 22px', borderTop: '1px solid var(--rule)', display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {isEditing ? (
                  <motion.button whileTap={{ scale: 0.96 }} type="button" className="btn-outline" onClick={saveEdit}>Save edits</motion.button>
                ) : (
                  <motion.button whileTap={{ scale: 0.96 }} type="button" className="btn-outline" onClick={startEdit}>Edit note</motion.button>
                )}
                
                {status !== 'approved' && (
                  <motion.button whileTap={{ scale: 0.96 }} type="button" className="btn-success" onClick={handleApprove} disabled={approving}>
                    {approving && <span className="spinner" aria-hidden="true" />}
                    {approving ? 'Saving…' : 'Approve and save'}
                  </motion.button>
                )}

                {status === 'approved' && !isEditing && (
                  <>
                    <motion.button whileTap={{ scale: 0.96 }} type="button" className="btn-outline" onClick={copyToEHR}>
                      📋 Copy to EHR
                    </motion.button>
                    <motion.button whileTap={{ scale: 0.96 }} type="button" className="btn-outline" onClick={() => window.print()}>
                      🖨️ Print Note
                    </motion.button>
                  </>
                )}
              </div>
            </div>

            <div className="no-print">
              <ClinicalTools extractedEntities={note?.extractedEntities} />
            </div>

            <div className="no-print" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18, marginTop: 18 }}>
              <ChipSection title="Suggested ICD-10" items={note.icd10} />
              <ChipSection title="Recommended tests" items={note.tests} />
            </div>
          </motion.div>
        )}
      </main>
    </div>
  );
}

function ChipSection({ title, items }) {
  return (
    <div className="card">
      <p className="card__eyebrow">{title}</p>
      {items.length === 0 ? (
        <p className="table-empty" style={{ padding: '8px 0' }}>None suggested.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {items.map((item, i) => (
            <motion.div
              key={item.code}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2, delay: i * 0.05 }}
              style={{ display: 'flex', gap: 10, border: '1px solid var(--rule)', borderRadius: 6, padding: '8px 11px', fontSize: '0.82rem' }}
            >
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--teal-dark)' }}>{item.code}</span>
              <span style={{ color: 'var(--ink-soft)' }}>{item.description}</span>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}

function ClinicalTools({ extractedEntities }) {
  const drugs = extractedEntities?.drugs || [];
  const condition = extractedEntities?.condition || '';

  return (
    <div className="card no-print" style={{ marginTop: 18, background: 'var(--paper-alt)', border: 'none', padding: '20px 18px' }}>
      <p className="card__eyebrow" style={{ color: 'var(--ink-soft)' }}>Clinical tools</p>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 14 }}>
        <ToolItem 
          icon="💊" label="Drug interactions" mode="interaction" color="var(--teal-dark)" 
          autoQueryA={drugs.length > 0 ? drugs[0] : ''}
          autoQueryB={drugs.length >= 2 ? drugs[1] : ''}
        />
        <ToolItem 
          icon="📖" label="NICE guidelines" mode="guideline" color="var(--amber)" 
          autoQueryA={condition}
        />
        <ToolItem 
          icon="🔍" label="Drug lookup" mode="lookup" color="var(--success)" 
          autoQueryA={drugs.length > 0 ? drugs[0] : ''}
        />
      </div>
    </div>
  );
}

function ToolItem({ icon, label, mode, color, autoQueryA, autoQueryB }) {
  const [open, setOpen] = useState(false);
  const [inputA, setInputA] = useState('');
  const [inputB, setInputB] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (autoQueryA) {
      setOpen(true);
      setInputA(autoQueryA);
      setInputB(autoQueryB || '');
      
      if (mode === 'interaction' && (!autoQueryA || !autoQueryB)) return;

      async function autoRun() {
        setResult(null);
        setLoading(true);
        try {
          if (mode === 'interaction') {
            const res = await api.checkDrugInteraction(autoQueryA.trim(), autoQueryB.trim());
            const variant = res.severity === 'severe' ? 'severe' : res.severity === 'caution' ? 'caution' : 'clear';
            const flag = res.severity === 'none' ? 'Clear' : res.severity === 'severe' ? 'Severe' : 'Caution';
            setResult({ flag, variant, text: res.message });
          } else if (mode === 'guideline') {
            const res = await api.searchGuideline(autoQueryA.trim());
            setResult({ flag: null, variant: 'clear', text: res.summary + (res.source ? ` (Source: ${res.source})` : '') });
          } else {
            const res = await api.lookupDrug(autoQueryA.trim());
            setResult({ flag: 'Reference', variant: 'clear', text: (res.drugClass ? res.drugClass + ' · ' : '') + res.summary });
          }
        } catch (err) {
          setResult({ flag: 'Error', variant: 'error', text: err instanceof ApiError ? err.message : 'Unexpected error. Please try again.' });
        } finally {
          setLoading(false);
        }
      }
      autoRun();
    }
  }, [autoQueryA, autoQueryB, mode]);

  async function run() {
    setResult(null);
    if (mode === 'interaction' && (!inputA.trim() || !inputB.trim())) {
      setResult({ flag: null, variant: 'error', text: 'Enter both drug names to check.' });
      return;
    }
    if ((mode === 'guideline' || mode === 'lookup') && !inputA.trim()) {
      setResult({ flag: null, variant: 'error', text: `Enter a ${mode === 'guideline' ? 'condition' : 'drug name'} to look up.` });
      return;
    }
    setLoading(true);
    try {
      if (mode === 'interaction') {
        const res = await api.checkDrugInteraction(inputA.trim(), inputB.trim());
        const variant = res.severity === 'severe' ? 'severe' : res.severity === 'caution' ? 'caution' : 'clear';
        const flag = res.severity === 'none' ? 'Clear' : res.severity === 'severe' ? 'Severe' : 'Caution';
        setResult({ flag, variant, text: res.message });
      } else if (mode === 'guideline') {
        const res = await api.searchGuideline(inputA.trim());
        setResult({ flag: null, variant: 'clear', text: res.summary + (res.source ? ` (Source: ${res.source})` : '') });
      } else {
        const res = await api.lookupDrug(inputA.trim());
        setResult({ flag: 'Reference', variant: 'clear', text: (res.drugClass ? res.drugClass + ' · ' : '') + res.summary });
      }
    } catch (err) {
      setResult({ flag: 'Error', variant: 'error', text: err instanceof ApiError ? err.message : 'Unexpected error. Please try again.' });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <button
        type="button" onClick={() => setOpen((v) => !v)} aria-expanded={open}
        style={{ width: '100%', background: 'var(--paper)', border: '1px solid var(--rule)', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 12, padding: '12px 14px', cursor: 'pointer', textAlign: 'left', fontSize: '0.86rem', fontWeight: 600, color: 'var(--ink)', boxShadow: '0 1px 3px rgba(0,0,0,0.02)' }}
      >
        <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 28, height: 28, background: 'var(--paper-alt)', borderRadius: 6, fontSize: '1rem', border: '1px solid var(--rule)' }}>{icon}</span>
        <span>{label}</span>
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.18 }} style={{ marginLeft: 'auto', color: 'var(--ink-faint)' }}>⌄</motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            key="body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ padding: '12px 2px 4px' }}>
              <input
                className="text-input" style={{ marginBottom: 8, background: 'var(--paper)' }}
                placeholder={mode === 'interaction' ? 'First drug, e.g. Warfarin' : mode === 'guideline' ? 'e.g. Type 2 diabetes management' : 'e.g. Metformin'}
                value={inputA} onChange={(e) => setInputA(e.target.value)} maxLength={160}
              />
              {mode === 'interaction' && (
                <input className="text-input" style={{ marginBottom: 8, background: 'var(--paper)' }} placeholder="Second drug, e.g. Aspirin" value={inputB} onChange={(e) => setInputB(e.target.value)} maxLength={160} />
              )}
              <button type="button" className="btn-outline" style={{ background: 'var(--paper)' }} onClick={run} disabled={loading}>
                {loading && <span className="spinner spinner--dark" aria-hidden="true" />}
                {loading ? 'Checking…' : mode === 'interaction' ? 'Check interaction' : mode === 'guideline' ? 'Search guidelines' : 'Look up'}
              </button>
              <AnimatePresence>
                {result && (
                  <motion.div
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.18 }}
                    style={{ marginTop: 10, fontSize: '0.8rem', lineHeight: 1.55, color: 'var(--ink-soft)' }}
                  >
                    {result.flag && (
                      <span className={`status-pill status-pill--${result.variant === 'error' ? 'flagged' : result.variant === 'caution' ? 'draft' : 'approved'}`} style={{ marginBottom: 6, display: 'inline-block' }}>
                        {result.flag}
                      </span>
                    )}
                    <div>{result.text}</div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function tabStyle(active) {
  return {
    background: 'none', border: 'none', borderBottom: active ? '2px solid var(--teal)' : '2px solid transparent',
    padding: '8px 4px', marginRight: 20, fontSize: '0.84rem', fontWeight: 500,
    color: active ? 'var(--teal-dark)' : 'var(--ink-faint)', cursor: 'pointer'
  };
}
