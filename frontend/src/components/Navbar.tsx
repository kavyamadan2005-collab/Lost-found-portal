import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Navbar() {
  const { token, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-left">
        <Link to="/search" className="navbar-brand">Lost &amp; Found</Link>
        <Link to="/search">Home</Link>
      </div>
      <div className="navbar-right">
        {token ? (
          <>
            {user && <span style={{ marginRight: '1rem' }}>Welcome, {user.name}</span>}
            <Link to="/lost/new">Post Lost</Link>
            <Link to="/found/new">Post Found</Link>
            <Link to="/matches">Matches</Link>
            <Link to="/admin">Items Overview</Link>
            <button type="button" onClick={handleLogout}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/register">Register</Link>
          </>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
