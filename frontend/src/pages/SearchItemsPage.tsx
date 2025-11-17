import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosClient from '../api/axiosClient';

interface Item {
  id: number;
  title: string;
  description?: string;
  location?: string;
  type: 'lost' | 'found';
  status: string;
  images?: { id: number; image_url: string }[];
}

function SearchItemsPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [type, setType] = useState<string>('');
  const [name, setName] = useState<string>('');
  const [location, setLocation] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const fetchItems = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axiosClient.get('/items', {
        params: {
          type: type || undefined,
          name: name || undefined,
          location: location || undefined,
        },
      });
      setItems(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Failed to load items');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchItems();
  };

  return (
    <main>
      <button type="button" onClick={() => navigate(-1)}>
        Back
      </button>
      <h1>Search Items</h1>
      <form onSubmit={handleSearch} className="filters">
        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="">All Types</option>
          <option value="lost">Lost</option>
          <option value="found">Found</option>
        </select>
        <input
          placeholder="Item Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          placeholder="Location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
        <button type="submit">Search</button>
      </form>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <ul className="item-list">
        {items.map((item) => (
          <li key={item.id} className="item-card">
            <h3>
              [{item.type.toUpperCase()}] {item.title}
            </h3>
            {item.images && item.images.length > 0 && (
              <img
                src={`http://localhost:8000${item.images[0].image_url}`}
                alt={item.title}
                style={{ maxWidth: '200px', display: 'block', marginBottom: '0.5rem' }}
              />
            )}
            {item.description && <p>{item.description}</p>}
            <p>
              <strong>Location:</strong> {item.location || 'N/A'}
            </p>
            <p>
              <strong>Status:</strong> {item.status}
            </p>
          </li>
        ))}
        {!loading && !error && items.length === 0 && <p>No items found.</p>}
      </ul>
    </main>
  );
}

export default SearchItemsPage;
