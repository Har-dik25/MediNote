import { AnimatePresence, motion } from 'framer-motion';
import { Route, Routes, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext.jsx';
import { ToastProvider } from './context/ToastContext.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import Layout from './components/Layout.jsx';
import LoginPage from './pages/LoginPage.jsx';
import SignupPage from './pages/SignupPage.jsx';
import EncounterPage from './pages/EncounterPage.jsx';
import PatientListPage from './pages/PatientListPage.jsx';
import PatientProfilePage from './pages/PatientProfilePage.jsx';
import NoteHistoryPage from './pages/NoteHistoryPage.jsx';
import SettingsPage from './pages/SettingsPage.jsx';
import NotFoundPage from './pages/NotFoundPage.jsx';

const pageVariants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.22, ease: [0.22, 1, 0.36, 1] } },
  exit: { opacity: 0, y: -6, transition: { duration: 0.14, ease: 'easeIn' } }
};

function AnimatedPage({ children }) {
  return (
    <motion.div variants={pageVariants} initial="initial" animate="animate" exit="exit">
      {children}
    </motion.div>
  );
}

function AnimatedRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/login" element={<AnimatedPage><LoginPage /></AnimatedPage>} />
        <Route path="/signup" element={<AnimatedPage><SignupPage /></AnimatedPage>} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<AnimatedPage><EncounterPage /></AnimatedPage>} />
          <Route path="patients" element={<AnimatedPage><PatientListPage /></AnimatedPage>} />
          <Route path="patients/:id" element={<AnimatedPage><PatientProfilePage /></AnimatedPage>} />
          <Route path="notes" element={<AnimatedPage><NoteHistoryPage /></AnimatedPage>} />
          <Route path="settings" element={<AnimatedPage><SettingsPage /></AnimatedPage>} />
        </Route>
        <Route path="*" element={<AnimatedPage><NotFoundPage /></AnimatedPage>} />
      </Routes>
    </AnimatePresence>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <AnimatedRoutes />
      </ToastProvider>
    </AuthProvider>
  );
}
