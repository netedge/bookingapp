import React, { useState, useEffect, useCallback } from 'react';
import { CalendarBlank, Clock, CurrencyDollar, CheckCircle } from '@phosphor-icons/react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const BookingCalendar = ({ courtId, courtName }) => {
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [timeSlots, setTimeSlots] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [showBookingForm, setShowBookingForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [bookingForm, setBookingForm] = useState({
    customer_name: '',
    customer_email: '',
    customer_phone: ''
  });

  const generateTimeSlots = useCallback(() => {
    const slots = [];
    for (let hour = 6; hour < 22; hour++) {
      slots.push({
        start: `${hour.toString().padStart(2, '0')}:00`,
        end: `${(hour + 1).toString().padStart(2, '0')}:00`,
        price: hour >= 17 ? 50 : 30
      });
    }
    setTimeSlots(slots);
  }, []);

  const fetchBookings = useCallback(async () => {
    try {
      const { data } = await axios.get(
        `${API}/bookings?court_id=${courtId}&date=${selectedDate}`,
        { withCredentials: true }
      );
      setBookings(data);
    } catch (err) {
      console.error('Failed to fetch bookings:', err);
    }
  }, [courtId, selectedDate]);

  useEffect(() => {
    if (courtId) {
      fetchBookings();
      generateTimeSlots();
    }
  }, [courtId, selectedDate, fetchBookings, generateTimeSlots]);

  const isSlotBooked = (startTime) => {
    return bookings.some(
      (booking) =>
        booking.date === selectedDate &&
        booking.start_time === startTime &&
        booking.status !== 'cancelled'
    );
  };

  const handleSlotClick = (slot) => {
    if (!isSlotBooked(slot.start)) {
      setSelectedSlot(slot);
      setShowBookingForm(true);
    }
  };

  const handleBookingSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(
        `${API}/bookings`,
        {
          court_id: courtId,
          customer_name: bookingForm.customer_name,
          customer_email: bookingForm.customer_email,
          customer_phone: bookingForm.customer_phone,
          date: selectedDate,
          start_time: selectedSlot.start,
          end_time: selectedSlot.end,
          total_price: selectedSlot.price
        },
        { withCredentials: true }
      );

      setShowBookingForm(false);
      setSelectedSlot(null);
      setBookingForm({ customer_name: '', customer_email: '', customer_phone: '' });
      fetchBookings();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create booking');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
      <div className="mb-6">
        <h3 className="text-xl font-medium text-indigo-950 mb-4">Book {courtName}</h3>
        
        <div className="flex items-center space-x-4 mb-4">
          <div className="flex items-center space-x-2">
            <CalendarBlank className="w-5 h-5 text-stone-500" weight="duotone" />
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className="px-4 py-2 bg-white border border-stone-200 rounded-lg text-indigo-950 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
              data-testid="date-picker"
            />
          </div>
        </div>

        <div className="flex items-center space-x-4 text-sm mb-4">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded bg-emerald-100 border-2 border-emerald-600"></div>
            <span className="text-stone-600">Available</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded bg-stone-200 border-2 border-stone-400"></div>
            <span className="text-stone-600">Booked</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded bg-orange-100 border-2 border-orange-600"></div>
            <span className="text-stone-600">Peak Hours</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {timeSlots.map((slot) => {
          const isBooked = isSlotBooked(slot.start);
          const isPeak = slot.price > 30;

          return (
            <button
              key={`${selectedDate}-${slot.start}`}
              onClick={() => handleSlotClick(slot)}
              disabled={isBooked}
              className={`p-3 rounded-xl border-2 transition-all text-left ${
                isBooked
                  ? 'bg-stone-200 border-stone-400 cursor-not-allowed opacity-50'
                  : isPeak
                  ? 'bg-orange-50 border-orange-200 hover:border-orange-600 hover:bg-orange-100'
                  : 'bg-emerald-50 border-emerald-200 hover:border-emerald-600 hover:bg-emerald-100'
              }`}
              data-testid={`time-slot-${slot.start}`}
            >
              <div className="flex items-center space-x-1 mb-1">
                <Clock className="w-4 h-4" weight="duotone" />
                <span className="text-sm font-medium text-indigo-950">{slot.start}</span>
              </div>
              <div className="flex items-center space-x-1">
                <CurrencyDollar className="w-4 h-4" weight="duotone" />
                <span className="text-xs text-stone-600">${slot.price}</span>
              </div>
              {isBooked && (
                <CheckCircle className="w-4 h-4 text-stone-500 mt-1" weight="fill" />
              )}
            </button>
          );
        })}
      </div>

      {showBookingForm && selectedSlot && (
        <div className="mt-6 p-6 bg-stone-50 border border-stone-200 rounded-xl">
          <h4 className="text-lg font-medium text-indigo-950 mb-4">
            Booking Details - {selectedSlot.start} to {selectedSlot.end}
          </h4>
          
          <form onSubmit={handleBookingSubmit} className="space-y-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-indigo-950">Customer Name</label>
              <input
                type="text"
                value={bookingForm.customer_name}
                onChange={(e) => setBookingForm({ ...bookingForm, customer_name: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                required
                data-testid="customer-name-input"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-indigo-950">Customer Email</label>
              <input
                type="email"
                value={bookingForm.customer_email}
                onChange={(e) => setBookingForm({ ...bookingForm, customer_email: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                required
                data-testid="customer-email-input"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-indigo-950">Phone (optional)</label>
              <input
                type="tel"
                value={bookingForm.customer_phone}
                onChange={(e) => setBookingForm({ ...bookingForm, customer_phone: e.target.value })}
                className="w-full px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                data-testid="customer-phone-input"
              />
            </div>

            <div className="flex items-center justify-between p-4 bg-white rounded-lg border border-stone-200">
              <span className="text-sm font-medium text-stone-600">Total Price</span>
              <span className="text-2xl font-semibold text-emerald-700">${selectedSlot.price}</span>
            </div>

            <div className="flex items-center space-x-4">
              <button
                type="button"
                onClick={() => { setShowBookingForm(false); setSelectedSlot(null); }}
                className="flex-1 px-6 py-3 text-sm font-medium bg-white border border-stone-200 text-indigo-950 rounded-xl hover:bg-stone-50"
                data-testid="cancel-booking-button"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-6 py-3 text-sm font-medium text-white bg-emerald-700 rounded-xl hover:bg-emerald-800 disabled:opacity-50"
                data-testid="confirm-booking-button"
              >
                {loading ? 'Booking...' : 'Confirm Booking'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default BookingCalendar;
