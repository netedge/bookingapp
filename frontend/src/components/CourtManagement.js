import React, { useState, useEffect } from 'react';
import { Plus, Pencil, Trash, CheckCircle } from '@phosphor-icons/react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CourtManagement = ({ venueId, venueName }) => {
  const [courts, setCourts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    sport_type: 'Tennis',
    capacity: 10,
    indoor: true
  });

  useEffect(() => {
    if (venueId) {
      fetchCourts();
    }
  }, [venueId]);

  const fetchCourts = async () => {
    try {
      const { data } = await axios.get(`${API}/courts?venue_id=${venueId}`, { withCredentials: true });
      setCourts(data);
    } catch (error) {
      console.error('Failed to fetch courts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/courts`, { ...formData, venue_id: venueId }, { withCredentials: true });
      setShowForm(false);
      setFormData({ name: '', sport_type: 'Tennis', capacity: 10, indoor: true });
      fetchCourts();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to create court');
    }
  };

  return (
    <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-medium text-indigo-950">Courts - {venueName}</h3>
        <button
          onClick={() => setShowForm(!showForm)}
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-emerald-700 rounded-xl hover:bg-emerald-800"
          data-testid="add-court-button"
        >
          <Plus className="w-4 h-4 mr-2" weight="bold" />
          Add Court
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="mb-6 p-6 bg-stone-50 border border-stone-200 rounded-xl">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-indigo-950">Court Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 bg-white border border-stone-200 rounded-lg"
                required
                data-testid="court-name-input"
              />
            </div>
            <div>
              <label className="block mb-2 text-sm font-medium text-indigo-950">Sport Type</label>
              <select
                value={formData.sport_type}
                onChange={(e) => setFormData({ ...formData, sport_type: e.target.value })}
                className="w-full px-4 py-2 bg-white border border-stone-200 rounded-lg"
                data-testid="sport-type-select"
              >
                <option>Tennis</option>
                <option>Basketball</option>
                <option>Football</option>
                <option>Badminton</option>
                <option>Volleyball</option>
              </select>
            </div>
            <div>
              <label className="block mb-2 text-sm font-medium text-indigo-950">Capacity</label>
              <input
                type="number"
                value={formData.capacity}
                onChange={(e) => setFormData({ ...formData, capacity: parseInt(e.target.value) })}
                className="w-full px-4 py-2 bg-white border border-stone-200 rounded-lg"
                min="1"
                data-testid="capacity-input"
              />
            </div>
            <div>
              <label className="block mb-2 text-sm font-medium text-indigo-950">Location</label>
              <select
                value={formData.indoor}
                onChange={(e) => setFormData({ ...formData, indoor: e.target.value === 'true' })}
                className="w-full px-4 py-2 bg-white border border-stone-200 rounded-lg"
                data-testid="location-select"
              >
                <option value="true">Indoor</option>
                <option value="false">Outdoor</option>
              </select>
            </div>
          </div>
          <div className="flex items-center space-x-4 mt-4">
            <button
              type="submit"
              className="px-6 py-2 text-sm font-medium text-white bg-emerald-700 rounded-xl hover:bg-emerald-800"
              data-testid="submit-court-button"
            >
              Create Court
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-6 py-2 text-sm font-medium bg-white border border-stone-200 rounded-xl hover:bg-stone-50"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="text-center py-8">
          <div className="w-8 h-8 border-4 border-emerald-700 border-t-transparent rounded-full animate-spin mx-auto"></div>
        </div>
      ) : courts.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-stone-500">No courts yet. Add your first court to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {courts.map((court, idx) => (
            <div
              key={idx}
              className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl"
              data-testid={`court-card-${idx}`}
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-lg font-medium text-indigo-950">{court.name}</h4>
                <CheckCircle className="w-5 h-5 text-emerald-700" weight="fill" />
              </div>
              <p className="text-sm text-stone-600 mb-1">Sport: {court.sport_type}</p>
              <p className="text-sm text-stone-600 mb-1">Capacity: {court.capacity} people</p>
              <p className="text-sm text-stone-600">{court.indoor ? 'Indoor' : 'Outdoor'}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CourtManagement;