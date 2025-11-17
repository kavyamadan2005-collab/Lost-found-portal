import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosClient from '../api/axiosClient';

function PostFoundItemPage() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [dateReported, setDateReported] = useState('');
  const [images, setImages] = useState<FileList | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setMessage(null);
    const form = new FormData();
    form.append('title', title);
    form.append('description', description);
    form.append('location', location);
    if (dateReported) form.append('date_reported', dateReported);
    if (images) {
      Array.from(images).forEach((file) => form.append('images', file));
    }
    try {
      await axiosClient.post('/items/found', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMessage('Found item posted successfully');
    } catch (err: any) {
      setMessage(err.response?.data?.detail ?? 'Failed to post found item');
    }
  };

  return (
    <main>
      <button type="button" onClick={() => navigate(-1)}>
        Back
      </button>
      <h1>Post Found Item</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Title</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} required />
        </div>
        <div>
          <label>Description</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <div>
          <label>Location</label>
          <input value={location} onChange={(e) => setLocation(e.target.value)} />
        </div>
        <div>
          <label>Date Reported</label>
          <input type="date" value={dateReported} onChange={(e) => setDateReported(e.target.value)} />
        </div>
        <div>
          <label>Images</label>
          <input type="file" multiple onChange={(e) => setImages(e.target.files)} />
        </div>
        <button type="submit">Submit</button>
      </form>
      {message && <p>{message}</p>}
    </main>
  );
}

export default PostFoundItemPage;
