import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';

// Basic components for Phase 1
const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    fetch('http://localhost:8000/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
      credentials: 'include'
    }).then(res => {
      if (res.ok) window.location.href = '/protected';
      else alert('Login failed');
    });
  };

  return (
    <div className="flex flex-col items-center p-10">
      <h2 className="text-2xl font-bold mb-4">Dayflow Login</h2>
      <form onSubmit={handleLogin} className="flex flex-col space-y-3">
        <input type="email" placeholder="Email" className="border p-2" value={email} onChange={e => setEmail(e.target.value)} />
        <input type="password" placeholder="Password" className="border p-2" value={password} onChange={e => setPassword(e.target.value)} />
        <button type="submit" className="bg-blue-600 text-white p-2 rounded">Sign In</button>
      </form>
    </div>
  );
};

const UnauthorizedPage = () => <div className="p-10 text-red-600">Unauthorized - You lack permissions</div>;

const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    // Check GET /api/v1/auth/me to verify the HTTP-Only cookie.
    fetch('http://localhost:8000/api/v1/auth/me', { credentials: 'include' })
      .then(res => setIsAuthenticated(res.ok))
      .catch(() => setIsAuthenticated(false));
  }, []);

  if (isAuthenticated === null) return <div>Loading...</div>;
  return isAuthenticated ? children : <Navigate to="/login" />;
};

const AuthenticatedLayout = ({ children }: { children: JSX.Element }) => (
  <div className="layout">
    <header>Dayflow HRMS</header>
    <main>{children}</main>
  </div>
);

const ProtectedDashboard = () => <div>Welcome to the Protected Area</div>;

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/unauthorized" element={<UnauthorizedPage />} />
        <Route 
          path="/protected" 
          element={
            <ProtectedRoute>
              <AuthenticatedLayout>
                <ProtectedDashboard />
              </AuthenticatedLayout>
            </ProtectedRoute>
          } 
        />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </Router>
  );
}

export default App;
