import React from 'react';
import BookingCalendar from './BookingCalendar';

const BookingPanel = ({ courts, selectedCourt, setSelectedCourt, setActiveTab }) => {
  if (courts.length === 0) {
    return (
      <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-12 text-center">
        <p className="text-stone-500 mb-4">No courts available. Create a venue and add courts to start accepting bookings.</p>
        <button
          onClick={() => setActiveTab('venues')}
          className="px-6 py-3 text-sm font-medium text-white bg-emerald-700 rounded-xl hover:bg-emerald-800"
          data-testid="go-to-venues"
        >
          Go to Venues
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <select
          value={selectedCourt?.id || ''}
          onChange={(e) => {
            const c = courts.find(court => court.id === e.target.value);
            setSelectedCourt(c);
          }}
          className="px-4 py-3 bg-white border border-stone-200 rounded-xl text-indigo-950 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
          data-testid="court-select-for-bookings"
        >
          <option value="">Select a court</option>
          {courts.map((court) => (
            <option key={court.id || court.name} value={court.id}>{court.name}</option>
          ))}
        </select>
      </div>
      {selectedCourt && (
        <BookingCalendar courtId={selectedCourt.id} courtName={selectedCourt.name} />
      )}
    </div>
  );
};

export default BookingPanel;
