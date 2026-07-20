import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';
import { useToast } from '../context/ToastContext.jsx';

const NAV_ITEMS = [
  { to: '/', label: 'Workspace', end: true },
  { to: '/patients', label: 'Patients' },
  { to: '/notes', label: 'Note history' },
  { to: '/settings', label: 'Settings' }
];

function initials(name) {
  return name.split(' ').map((p) => p[0]).slice(0, 2).join('').toUpperCase();
}

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { showToast } = useToast();

  async function handleLogout() {
    await logout();
    showToast('Signed out.');
    navigate('/login', { replace: true });
  }

  return (
    <div className="app-shell">
      <header className="letterhead">
        <div className="letterhead__inner">
          <div className="brand">
            <span className="brand__mark">
              <img src="/logo.png" alt="MediMate Logo" className="brand-logo" />
            </span>
            <div>
              <div className="brand__name">MediMate</div>
              <div className="brand__tag">Clinical documentation copilot</div>
            </div>
          </div>

          <nav className="main-nav" aria-label="Primary">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => 'main-nav__link' + (isActive ? ' active' : '')}
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="header-actions">
            {user && (
              <div className="user-chip">
                <span className="user-chip__avatar">{initials(user.name)}</span>
                <span>{user.name}</span>
              </div>
            )}
            <button type="button" className="link-btn" onClick={handleLogout}>Sign out</button>
          </div>
        </div>
      </header>

      <div className="app-wrapper">
        <Outlet />
      </div>
    </div>
  );
}
