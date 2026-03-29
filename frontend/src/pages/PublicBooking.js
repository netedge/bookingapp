import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { CalendarBlank, Clock, MapPin, CurrencyDollar, CheckCircle, Envelope, Phone, User } from '@phosphor-icons/react';
import axios from 'axios';
import { motion } from 'framer-motion';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PublicBooking = () => {
  const { subdomain, venueId } = useParams();
  const [venue, setVenue] = useState(null);
  const [courts, setCourts] = useState([]);
  const [selectedCourt, setSelectedCourt] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [timeSlots, setTimeSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [bookingSuccess, setBookingSuccess] = useState(false);

  const [customerForm, setCustomerForm] = useState({
    name: '',
    email: '',
    phone: ''
  });

  useEffect(() => {
    fetchVenueData();
  }, [venueId]);

  useEffect(() => {
    if (selectedCourt) {
      generateTimeSlots();
      fetchBookings();
    }
  }, [selectedCourt, selectedDate]);

  const fetchVenueData = async () => {
    try {
      // In real implementation, fetch venue by subdomain
      const venuesRes = await axios.get(`${API}/venues`);
      const venueData = venuesRes.data.find(v => v.id === venueId) || venuesRes.data[0];
      setVenue(venueData);

      const courtsRes = await axios.get(`${API}/courts?venue_id=${venueData.id || venuesRes.data[0].id}`);
      setCourts(courtsRes.data);
      if (courtsRes.data.length > 0) {
        setSelectedCourt(courtsRes.data[0]);
      }
    } catch (error) {
      console.error('Failed to fetch venue:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateTimeSlots = () => {
    const slots = [];
    for (let hour = 6; hour < 22; hour++) {
      slots.push({
        start: `${hour.toString().padStart(2, '0')}:00`,
        end: `${(hour + 1).toString().padStart(2, '0')}:00`,
        price: hour >= 17 ? 50 : 30
      });
    }
    setTimeSlots(slots);
  };

  const fetchBookings = async () => {
    try {
      const courtId = selectedCourt?._id || selectedCourt?.id;
      const { data } = await axios.get(`${API}/bookings?court_id=${courtId}&date=${selectedDate}`);
      setBookings(data);
    } catch (error) {
      console.error('Failed to fetch bookings:', error);
    }
  };

  const isSlotBooked = (startTime) => {
    return bookings.some(
      (booking) =>
        booking.date === selectedDate &&
        booking.start_time === startTime &&
        booking.status !== 'cancelled'
    );
  };

  const handleBooking = async (e) => {
    e.preventDefault();
    
    try {
      const courtId = selectedCourt?._id || selectedCourt?.id;
      await axios.post(`${API}/bookings`, {
        court_id: courtId,
        customer_name: customerForm.name,
        customer_email: customerForm.email,
        customer_phone: customerForm.phone,
        date: selectedDate,
        start_time: selectedSlot.start,
        end_time: selectedSlot.end,
        total_price: selectedSlot.price
      });

      setBookingSuccess(true);
      setSelectedSlot(null);
      setCustomerForm({ name: '', email: '', phone: '' });
      fetchBookings();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to create booking');
    }
  };

  if (loading) {
    return (
      <div className=\"min-h-screen bg-stone-50 flex items-center justify-center\">
        <div className=\"w-16 h-16 border-4 border-emerald-700 border-t-transparent rounded-full animate-spin\"></div>
      </div>
    );
  }

  return (
    <div className=\"min-h-screen bg-stone-50\">
      {/* Header */}
      <div className=\"bg-white border-b border-stone-200\">
        <div className=\"max-w-6xl mx-auto px-6 py-8\">
          <div className=\"flex items-start justify-between\">
            <div>
              <h1 className=\"text-4xl sm:text-5xl font-semibold tracking-tight text-indigo-950 mb-2\">
                {venue?.name || 'Sports Venue'}
              </h1>
              <div className=\"flex items-center space-x-2 text-stone-600\">
                <MapPin className=\"w-5 h-5\" weight=\"duotone\" />
                <span>{venue?.address || 'Address not available'}</span>
              </div>
            </div>
            <div className=\"w-24 h-24 rounded-xl bg-gradient-emerald flex items-center justify-center\">
              <span className=\"text-white font-bold text-3xl\">K</span>
            </div>
          </div>
        </div>
      </div>

      <div className=\"max-w-6xl mx-auto px-6 py-8\">
        {bookingSuccess && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className=\"mb-6 p-6 bg-emerald-50 border border-emerald-200 rounded-2xl\"
            data-testid=\"success-message\"
          >
            <div className=\"flex items-center space-x-3\">
              <CheckCircle className=\"w-8 h-8 text-emerald-700\" weight=\"fill\" />
              <div>
                <h3 className=\"text-lg font-medium text-emerald-900\">Booking Confirmed!</h3>
                <p className=\"text-sm text-emerald-700\">Check your email for confirmation details.</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Court Selection */}
        <div className=\"mb-8\">
          <h2 className=\"text-2xl font-medium text-indigo-950 mb-4\">Select Court</h2>
          <div className=\"grid grid-cols-1 md:grid-cols-3 gap-4\">
            {courts.map((court, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedCourt(court)}
                className={`p-4 rounded-xl border-2 text-left transition-all ${
                  selectedCourt === court
                    ? 'bg-emerald-50 border-emerald-600'
                    : 'bg-white border-stone-200 hover:border-emerald-300'
                }`}
                data-testid={`court-option-${idx}`}
              >
                <h3 className=\"text-lg font-medium text-indigo-950 mb-1\">{court.name}</h3>
                <p className=\"text-sm text-stone-600\">{court.sport_type}</p>
                <p className=\"text-xs text-stone-500 mt-1\">{court.indoor ? 'Indoor' : 'Outdoor'} • Capacity: {court.capacity}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Date Selection */}
        <div className=\"mb-8\">
          <h2 className=\"text-2xl font-medium text-indigo-950 mb-4\">Select Date</h2>
          <div className=\"flex items-center space-x-2\">
            <CalendarBlank className=\"w-5 h-5 text-stone-500\" weight=\"duotone\" />
            <input
              type=\"date\"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className=\"px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500\"
              data-testid=\"date-picker\"
            />
          </div>
        </div>

        {/* Time Slots */}
        <div className=\"mb-8\">
          <h2 className=\"text-2xl font-medium text-indigo-950 mb-4\">Select Time Slot</h2>
          <div className=\"grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3\">
            {timeSlots.map((slot, idx) => {
              const isBooked = isSlotBooked(slot.start);
              const isPeak = slot.price > 30;

              return (
                <button
                  key={idx}
                  onClick={() => !isBooked && setSelectedSlot(slot)}
                  disabled={isBooked}
                  className={`p-3 rounded-xl border-2 transition-all text-left ${
                    isBooked
                      ? 'bg-stone-200 border-stone-400 cursor-not-allowed opacity-50'
                      : selectedSlot === slot
                      ? 'bg-emerald-600 border-emerald-600 text-white'
                      : isPeak
                      ? 'bg-orange-50 border-orange-200 hover:border-orange-600'
                      : 'bg-emerald-50 border-emerald-200 hover:border-emerald-600'
                  }`}
                  data-testid={`time-slot-${slot.start}`}
                >
                  <div className=\"flex items-center space-x-1 mb-1\">
                    <Clock className=\"w-4 h-4\" weight=\"duotone\" />
                    <span className=\"text-sm font-medium\">{slot.start}</span>
                  </div>
                  <div className=\"flex items-center space-x-1\">
                    <CurrencyDollar className=\"w-4 h-4\" weight=\"duotone\" />
                    <span className=\"text-xs\">${slot.price}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Booking Form */}
        {selectedSlot && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className=\"bg-white border border-stone-200 rounded-2xl shadow-sm p-8\"
          >
            <h2 className=\"text-2xl font-medium text-indigo-950 mb-6\">Complete Your Booking</h2>
            
            <form onSubmit={handleBooking} className=\"space-y-4\">
              <div>
                <label className=\"flex items-center space-x-2 mb-2 text-sm font-medium text-indigo-950\">
                  <User className=\"w-4 h-4\" weight=\"duotone\" />
                  <span>Full Name</span>
                </label>
                <input
                  type=\"text\"
                  value={customerForm.name}
                  onChange={(e) => setCustomerForm({ ...customerForm, name: e.target.value })}
                  className=\"w-full px-4 py-3 bg-white border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500\"
                  required
                  data-testid=\"customer-name\"
                />
              </div>

              <div>
                <label className=\"flex items-center space-x-2 mb-2 text-sm font-medium text-indigo-950\">
                  <Envelope className=\"w-4 h-4\" weight=\"duotone\" />
                  <span>Email</span>
                </label>
                <input
                  type=\"email\"
                  value={customerForm.email}
                  onChange={(e) => setCustomerForm({ ...customerForm, email: e.target.value })}
                  className=\"w-full px-4 py-3 bg-white border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500\"
                  required
                  data-testid=\"customer-email\"
                />
              </div>

              <div>
                <label className=\"flex items-center space-x-2 mb-2 text-sm font-medium text-indigo-950\">
                  <Phone className=\"w-4 h-4\" weight=\"duotone\" />
                  <span>Phone (optional)</span>
                </label>
                <input
                  type=\"tel\"
                  value={customerForm.phone}
                  onChange={(e) => setCustomerForm({ ...customerForm, phone: e.target.value })}
                  className=\"w-full px-4 py-3 bg-white border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500\"
                  data-testid=\"customer-phone\"
                />
              </div>

              <div className=\"p-6 bg-emerald-50 border border-emerald-200 rounded-xl\">
                <div className=\"flex items-center justify-between mb-2\">
                  <span className=\"text-sm text-stone-600\">Date</span>
                  <span className=\"font-medium text-indigo-950\">{selectedDate}</span>
                </div>
                <div className=\"flex items-center justify-between mb-2\">
                  <span className=\"text-sm text-stone-600\">Time</span>
                  <span className=\"font-medium text-indigo-950\">{selectedSlot.start} - {selectedSlot.end}</span>
                </div>
                <div className=\"flex items-center justify-between pt-2 border-t border-emerald-300\">
                  <span className=\"text-sm font-medium text-stone-600\">Total</span>
                  <span className=\"text-2xl font-semibold text-emerald-700\">${selectedSlot.price}</span>
                </div>
              </div>

              <button
                type=\"submit\"
                className=\"w-full px-6 py-4 text-sm font-medium text-white bg-emerald-700 rounded-xl hover:bg-emerald-800 transition-all shadow-sm hover:shadow-md\"
                data-testid=\"confirm-booking\"
              >
                Confirm Booking
              </button>
            </form>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default PublicBooking;
