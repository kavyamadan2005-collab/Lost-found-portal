import { useEffect, useState } from 'react';
import axiosClient from '../api/axiosClient';
import { useNavigate } from 'react-router-dom';

interface Item {
  id: number;
  title: string;
  type: 'lost' | 'found';
  status: string;
  location?: string;
}

function AdminDashboardPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchItems = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axiosClient.get('/items');
      setItems(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Failed to load items');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this item?')) return;
    try {
      await axiosClient.delete(`/items/${id}`);
      setItems((prev) => prev.filter((item) => item.id !== id));
    } catch (err: any) {
      alert(err.response?.data?.detail ?? 'Failed to delete item');
    }
  };

  return (
    <main>
      <button type="button" onClick={() => navigate(-1)}>
        Back
      </button>
      <h1>Admin Dashboard</h1>
      <p>Simple overview of all items (lost and found).</p>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <table className="admin-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Type</th>
            <th>Title</th>
            <th>Status</th>
            <th>Location</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.id}</td>
              <td>{item.type}</td>
              <td>{item.title}</td>
              <td>{item.status}</td>
              <td>{item.location || 'N/A'}</td>
              <td>
                <button type="button" onClick={() => handleDelete(item.id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
          {!loading && !error && items.length === 0 && (
            <tr>
              <td colSpan={5}>No items found.</td>
            </tr>
          )}
        </tbody>
      </table>
    </main>
  );
}

export default AdminDashboardPage;
