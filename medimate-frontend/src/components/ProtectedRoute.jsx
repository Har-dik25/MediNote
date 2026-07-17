import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext.jsx';

export default function ProtectedRoute({ children }) {
  const { status } = useAuth();
  const location = useLocation();

  if (status === 'loading') {
    return (
      <div className="app-wrapper">
        <div className="skeleton" style={{ height: 200, borderRadius: 10 }} aria-label="Loading" role="status" />
      </div>
    );
  }
  if (status === 'anonymous') {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  return children;
}
