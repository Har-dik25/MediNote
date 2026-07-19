// Mock adapter — same method signatures as realApi, backed by in-memory data.
// Enabled via VITE_USE_MOCKS=true. Swap to realApi with zero component
// changes once the backend is live; only src/api/index.js needs to change.
//
// Deliberately starts EMPTY: no seeded doctor account, no seeded patients.
// A real user signs up (collecting their real profile details), and adds
// their own patients — nothing is pre-populated, same as a real deployment.
import { ApiError } from './client.js';

const delay = (ms) => new Promise((res) => setTimeout(res, 50)); // minimized for speed

function loadFromStorage(key, defaultValue) {
  try {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : defaultValue;
  } catch (e) {
    return defaultValue;
  }
}

function saveToStorage(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) {}
}

let mockSession = loadFromStorage('mockSession', null);
let mockAccounts = loadFromStorage('mockAccounts', []);
let mockPatients = loadFromStorage('mockPatients', []);
let mockNotes = loadFromStorage('mockNotes', []);

function persistMockState() {
  saveToStorage('mockSession', mockSession);
  saveToStorage('mockAccounts', mockAccounts);
  saveToStorage('mockPatients', mockPatients);
  saveToStorage('mockNotes', mockNotes);
}
function findAccountByEmail(email) {
  return mockAccounts.find((a) => a.email.toLowerCase() === String(email).toLowerCase());
}

function publicUser(account) {
  const { password, ...user } = account;
  return user;
}

function requireSession() {
  if (!mockSession) throw new ApiError(401, 'Not signed in.');
  return mockSession;
}

export const mockApi = {
  // ---------------------------------------------------------------- auth
  async signup({ name, email, password, clinicName, specialty, phone, region }) {
    await delay(600);
    const errors = {};
    if (!name || !name.trim()) errors.name = true;
    if (!email || !/^\S+@\S+\.\S+$/.test(email)) errors.email = true;
    if (!password || password.length < 8) errors.password = true;
    if (Object.keys(errors).length) throw new ApiError(400, 'Please fill in your name, a valid email, and a password of at least 8 characters.');
    if (findAccountByEmail(email)) throw new ApiError(409, 'An account with this email already exists. Try signing in instead.');

    const account = {
      id: 'u_' + Math.random().toString(36).slice(2, 9),
      name: name.trim(),
      email: email.trim(),
      password,
      clinicName: (clinicName || '').trim(),
      specialty: specialty || '',
      phone: (phone || '').trim(),
      region: region || 'UK (NICE)',
      role: 'clinician'
    };
    mockAccounts.push(account);
    mockSession = { user: publicUser(account) };
    persistMockState();
    return { user: publicUser(account) };
  },

  async login(email, password) {
    await delay(500);
    const account = findAccountByEmail(email);
    if (!account || account.password !== password) {
      throw new ApiError(401, 'Incorrect email or password.');
    }
    mockSession = { user: publicUser(account) };
    persistMockState();
    return { user: publicUser(account) };
  },

  async logout() {
    await delay(200);
    mockSession = null;
    persistMockState();
    return {};
  },

  async me() {
    await delay(150);
    requireSession();
    return { user: mockSession.user };
  },

  async updateProfile(fields) {
    await delay(400);
    requireSession();
    const account = mockAccounts.find((a) => a.id === mockSession.user.id);
    if (!account) throw new ApiError(404, 'Account not found.');
    Object.assign(account, fields);
    mockSession.user = publicUser(account);
    persistMockState();
    return { user: mockSession.user };
  },

  // ------------------------------------------------------------ patients
  async listPatients({ query = '', page = '1' } = {}) {
    await delay(350);
    requireSession();
    const q = String(query).toLowerCase();
    const filtered = mockPatients.filter((p) => p.name.toLowerCase().includes(q) || p.mrn.toLowerCase().includes(q));
    return { items: filtered, total: filtered.length, page: Number(page), pageSize: 20 };
  },

  async createPatient({ name, mrn, dob, phone }) {
    await delay(450);
    requireSession();
    if (!name || !name.trim()) throw new ApiError(400, 'Patient name is required.');
    if (!mrn || !mrn.trim()) throw new ApiError(400, 'MRN is required.');
    if (mockPatients.some((p) => p.mrn.toLowerCase() === mrn.trim().toLowerCase())) {
      throw new ApiError(409, 'A patient with this MRN already exists.');
    }
    const patient = {
      id: 'p_' + Math.random().toString(36).slice(2, 9),
      name: name.trim(),
      mrn: mrn.trim(),
      dob: dob || '',
      phone: phone || '',
      lastVisit: null
    };
    mockPatients.unshift(patient);
    persistMockState();
    return { patient };
  },

  async getPatient(id) {
    await delay(200);
    requireSession();
    const patient = mockPatients.find((p) => p.id === id);
    if (!patient) throw new ApiError(404, 'Patient not found.');
    return { patient };
  },

  // ---------------------------------------------------------------- notes
  async listNotes({ query = '', status = '', page = '1', patientId } = {}) {
    await delay(350);
    requireSession();
    const q = String(query).toLowerCase();
    const filtered = mockNotes
      .filter((n) => (!status || n.status === status) && (!q || n.patientName.toLowerCase().includes(q)) && (!patientId || n.patientId === patientId))
      .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    return { items: filtered, total: filtered.length, page: Number(page), pageSize: 20 };
  },

  async transcribeAudio(_file) {
    await delay(1200);
    requireSession();
    return { transcript: 'Patient presents with persistent cough for three weeks, mild fever, no shortness of breath.' };
  },

  async generateNote(transcript, patientId) {
    await delay(1600);
    requireSession();
    const patient = patientId ? mockPatients.find((p) => p.id === patientId) : null;
    const lower = (transcript || '').toLowerCase();
    const safetyFlag = lower.includes('chest pain') || lower.includes('cannot breathe') || lower.includes('unresponsive');

    const soap = {
      subjective: 'Patient reports persistent cough for three weeks with intermittent low-grade fever. Denies shortness of breath, chest pain, or hemoptysis.',
      objective: 'Temp 37.8C, HR 84, RR 16, SpO2 98% on room air. Mild bilateral crackles at bases, no wheeze.',
      assessment: 'Findings consistent with a resolving lower respiratory tract infection. Atypical pneumonia remains on the differential given symptom duration.',
      plan: 'Order chest X-ray and CRP. Start a five-day course of amoxicillin if bacterial etiology is suspected. Return if fever persists beyond 48 hours.'
    };
    const icd10 = [
      { code: 'J20.9', description: 'Acute bronchitis, unspecified' },
      { code: 'R05', description: 'Cough' },
      { code: 'J18.9', description: 'Pneumonia, unspecified organism' }
    ];
    const tests = [
      { code: 'CXR', description: 'Chest X-ray, PA view' },
      { code: 'CRP', description: 'C-reactive protein panel' },
      { code: 'CBC', description: 'Full blood count' }
    ];

    const note = {
      id: 'n_' + Math.random().toString(36).slice(2, 9),
      patientId: patient ? patient.id : null,
      patientName: patient ? patient.name : 'Unlinked encounter',
      createdAt: new Date().toISOString(),
      status: 'draft',
      soap, icd10, tests
    };
    mockNotes.unshift(note);
    if (patient) patient.lastVisit = note.createdAt.slice(0, 10);
    persistMockState();

    return { 
      noteId: note.id, 
      soap, 
      icd10, 
      tests, 
      safetyFlag, 
      safetyReason: safetyFlag ? 'Transcript mentions symptoms that may indicate a time-critical condition. Confirm escalation before finalizing this note.' : null,
      extractedEntities: {
        drugs: ['Amoxicillin', 'Ibuprofen'],
        condition: 'Lower respiratory tract infection'
      }
    };
  },

  async saveNote(noteId, soap) {
    await delay(500);
    requireSession();
    const note = mockNotes.find((n) => n.id === noteId);
    if (!note) throw new ApiError(404, 'Note not found.');
    note.soap = soap;
    persistMockState();
    return { ok: true };
  },

  async approveNote(noteId) {
    await delay(500);
    requireSession();
    const note = mockNotes.find((n) => n.id === noteId);
    if (!note) throw new ApiError(404, 'Note not found.');
    note.status = 'approved';
    persistMockState();
    return { ok: true, approvedAt: new Date().toISOString() };
  },

  // --------------------------------------------------------- clinical tools
  async checkDrugInteraction(drugA, drugB) {
    await delay(500);
    requireSession();
    const known = /warfarin/i.test(drugA + drugB) && /aspirin/i.test(drugA + drugB);
    if (known) return { severity: 'caution', message: `${drugA} with ${drugB} may increase bleeding risk. Monitor INR closely and confirm with a pharmacist before prescribing together.` };
    return { severity: 'none', message: `No major interaction on record between ${drugA} and ${drugB}. Always confirm with an up-to-date formulary before prescribing.` };
  },

  async searchGuideline(query) {
    await delay(500);
    requireSession();
    return { summary: `NICE guidance recommends first-line, evidence-based management for ${query}, with lifestyle intervention offered in parallel from diagnosis.`, source: 'NICE (mock)' };
  },

  async lookupDrug(query) {
    await delay(500);
    requireSession();
    return { summary: `${query} — common dosing and contraindications would be pulled from OpenFDA/formulary data here.`, drugClass: 'Reference (mock)' };
  },

  // ------------------------------------------------------------- settings
  async getSettings() {
    await delay(300);
    requireSession();
    return { settings: { emailNotifications: true, safetyAlerts: true, autoLogoutMinutes: 15 } };
  },
  async updateSettings(settings) {
    await delay(400);
    requireSession();
    return { settings };
  }
};
