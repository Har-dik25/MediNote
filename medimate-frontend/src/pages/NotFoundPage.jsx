import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div className="card" style={{ textAlign: 'center', padding: '60px 40px' }}>
      <h1 className="page-title">Page not found</h1>
      <p className="page-subtitle" style={{ marginBottom: 20 }}>The page you're looking for doesn't exist or has moved.</p>
      <Link to="/" className="btn-primary" style={{ display: 'inline-flex' }}>Back to workspace</Link>
    </div>
  );
}
