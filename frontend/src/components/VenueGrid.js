import React from 'react';

const VenueGrid = ({ venues }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {venues.map((venue) => (
      <div
        key={venue.id || venue.name}
        className="bg-white border border-stone-200 rounded-2xl shadow-sm overflow-hidden hover:shadow-md transition-all"
        data-testid={`venue-card-${venue.id}`}
      >
        <div className="h-48 bg-stone-200 overflow-hidden">
          <img
            src={venue.image_url || 'https://images.unsplash.com/photo-1765124540460-b884e248ac2b'}
            alt={venue.name}
            className="w-full h-full object-cover"
          />
        </div>
        <div className="p-6">
          <h3 className="text-lg font-medium text-indigo-950 mb-2">{venue.name}</h3>
          <p className="text-sm text-stone-600 mb-2">{venue.description}</p>
          <p className="text-xs text-stone-500">{venue.address}</p>
        </div>
      </div>
    ))}
  </div>
);

export default VenueGrid;
