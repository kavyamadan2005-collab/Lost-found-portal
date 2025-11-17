import { useEffect, useState } from 'react';
import axiosClient from '../api/axiosClient';
import { useNavigate } from 'react-router-dom';

interface Item {
  id: number;
  title: string;
  description?: string;
  location?: string;
  type: 'lost' | 'found';
  images?: { id: number; image_url: string }[];
}

interface MatchResult {
  item_id: number;
  score: number;
}

function MatchesPage() {
  const [lostItems, setLostItems] = useState<Item[]>([]);
  const [selectedLostId, setSelectedLostId] = useState<number | ''>('');
  const [matches, setMatches] = useState<(MatchResult & { item: Item | null })[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const loadLostItems = async () => {
      try {
        const res = await axiosClient.get<Item[]>('/items', { params: { type: 'lost' } });
        setLostItems(res.data);
      } catch (err: any) {
        setError(err.response?.data?.detail ?? 'Failed to load lost items');
      }
    };
    loadLostItems();
  }, []);

  const fetchMatches = async () => {
    if (!selectedLostId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await axiosClient.get<MatchResult[]>(`/items/matches/${selectedLostId}`);

      // For each match, fetch full found item details (including images)
      const enriched = await Promise.all(
        res.data.map(async (m) => {
          try {
            const itemRes = await axiosClient.get<Item>(`/items/${m.item_id}`);
            return { ...m, item: itemRes.data };
          } catch {
            return { ...m, item: null };
          }
        }),
      );

      setMatches(enriched);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Failed to load matches');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main>
      <button type="button" onClick={() => navigate(-1)}>
        Back
      </button>
      <h1>Matches</h1>
      <p>Select a lost item to see similar found items based on image matching.</p>
      <div>
        <label>
          Lost Item:
          <select
            value={selectedLostId}
            onChange={(e) => setSelectedLostId(e.target.value ? Number(e.target.value) : '')}
          >
            <option value="">Select Lost Item</option>
            {lostItems.map((item) => (
              <option key={item.id} value={item.id}>
                #{item.id} - {item.title}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={fetchMatches} disabled={!selectedLostId || loading}>
          View Matches
        </button>
      </div>
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <ul className="item-list">
        {matches.map((m) => (
          <li key={m.item_id} className="item-card">
            <h3>
              Match Score: {m.score.toFixed(3)}
            </h3>
            {m.item ? (
              <>
                <p>
                  <strong>Found Item ID:</strong> {m.item.id}
                </p>
                {m.item.images && m.item.images.length > 0 && (
                  <img
                    src={`http://localhost:8000${m.item.images[0].image_url}`}
                    alt={m.item.title}
                    style={{ maxWidth: '200px', display: 'block', marginBottom: '0.5rem' }}
                  />
                )}
                <p>
                  <strong>Title:</strong> {m.item.title}
                </p>
                {m.item.description && <p>{m.item.description}</p>}
                <p>
                  <strong>Location:</strong> {m.item.location || 'N/A'}
                </p>
              </>
            ) : (
              <p>Details not available for this item.</p>
            )}
          </li>
        ))}
        {!loading && !error && matches.length === 0 && selectedLostId && <p>No matches found.</p>}
      </ul>
    </main>
  );
}

export default MatchesPage;
