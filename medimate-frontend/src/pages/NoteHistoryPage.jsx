import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { api, ApiError } from '../api/index.js';
import Banner from '../components/Banner.jsx';

const STATUS_LABEL = { draft: 'Draft', approved: 'Approved', flagged: 'Flagged' };

export default function NoteHistoryPage() {
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('');
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const handle = setTimeout(async () => {
      setLoading(true);
      setError('');
      try {
        const res = await api.listNotes({ query, status, page: '1' });
        if (!cancelled) setNotes(res.items);
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.message : 'Could not load notes.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 250);
    return () => { cancelled = true; clearTimeout(handle); };
  }, [query, status]);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Note history</h1>
          <p className="page-subtitle">Every note this account has generated, with its current review status.</p>
        </div>
      </div>

      <div className="card">
        <div className="search-row">
          <label className="sr-only" htmlFor="noteSearch">Search notes by patient</label>
          <input
            id="noteSearch"
            className="text-input"
            placeholder="Search by patient name…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <label className="sr-only" htmlFor="statusFilter">Filter by status</label>
          <select id="statusFilter" className="select-input" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="approved">Approved</option>
            <option value="flagged">Flagged</option>
          </select>
        </div>

        {error && <Banner variant="danger" title="Could not load notes">{error}</Banner>}

        {loading ? (
          <div aria-hidden="true">
            {[0, 1, 2].map((i) => <div key={i} className="skeleton" style={{ height: 44, marginBottom: 8 }} />)}
          </div>
        ) : notes.length === 0 ? (
          <p className="table-empty">No notes match your filters.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr><th>Patient</th><th>Created</th><th>Status</th><th></th></tr>
            </thead>
            <tbody>
              {notes.map((n, i) => (
                <motion.tr key={n.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.18, delay: Math.min(i, 8) * 0.03 }}>
                  <td>{n.patientName}</td>
                  <td>{new Date(n.createdAt).toLocaleString()}</td>
                  <td><span className={`status-pill status-pill--${n.status}`}>{STATUS_LABEL[n.status] || n.status}</span></td>
                  <td>
                    <button type="button" className="btn-outline" onClick={() => setSelected(n)}>View</button>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <AnimatePresence>
        {selected && (
          <motion.div
            className="card"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            style={{ marginTop: 18 }}
          >
            <div className="page-header" style={{ marginBottom: 12 }}>
              <div>
                <p className="card__eyebrow">{selected.patientName}</p>
                <h2 className="card__title">Clinical note</h2>
              </div>
              <button type="button" className="link-btn" onClick={() => setSelected(null)}>Close</button>
            </div>
            {['subjective', 'objective', 'assessment', 'plan'].map((key) => (
              <div key={key} style={{ marginBottom: 14 }}>
                <p className="card__eyebrow" style={{ textTransform: 'capitalize' }}>{key}</p>
                <p style={{ margin: 0, fontSize: '0.92rem', lineHeight: 1.6 }}>{selected.soap[key]}</p>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
