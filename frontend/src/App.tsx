import { Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import PostLostItemPage from './pages/PostLostItemPage';
import PostFoundItemPage from './pages/PostFoundItemPage';
import SearchItemsPage from './pages/SearchItemsPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import MatchesPage from './pages/MatchesPage';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <div>
      <Navbar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/lost/new"
          element={
            <ProtectedRoute>
              <PostLostItemPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/found/new"
          element={
            <ProtectedRoute>
              <PostFoundItemPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AdminDashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/matches"
          element={
            <ProtectedRoute>
              <MatchesPage />
            </ProtectedRoute>
          }
        />
        <Route path="/search" element={<SearchItemsPage />} />
        <Route path="/" element={<Navigate to="/search" replace />} />
      </Routes>
    </div>
  );
}

export default App;
