import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { Plus, UploadSimple } from '@phosphor-icons/react';
import CreateTenantModal from '../components/CreateTenantModal';
import CreateVenueModal from '../components/CreateVenueModal';
import BookingCalendar from '../components/BookingCalendar';
import CourtManagement from '../components/CourtManagement';
import SidebarNav from '../components/SidebarNav';
import DashboardOverview from '../components/DashboardOverview';
import TenantManagement from '../components/TenantManagement';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState({
    total_bookings: 0,
    total_venues: 0,
    total_customers: 0,
    total_revenue: 0
  });
  const [venues, setVenues] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [courts, setCourts] = useState([]);
  const [selectedCourt, setSelectedCourt] = useState(null);
  const [selectedVenueForCourts, setSelectedVenueForCourts] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateVenue, setShowCreateVenue] = useState(false);
  const [showCreateTenant, setShowCreateTenant] = useState(false);
  const [showBulkImport, setShowBulkImport] = useState(false);
  const [copiedUrl, setCopiedUrl] = useState(null);
  const [tenantInfo, setTenantInfo] = useState(null);

  const fetchDashboardData = useCallback(async () => {
    try {
      const [analyticsRes, venuesRes, courtsRes] = await Promise.all([
        axios.get(`${API}/analytics/dashboard`, { withCredentials: true }),
        axios.get(`${API}/venues`, { withCredentials: true }),
        axios.get(`${API}/courts`, { withCredentials: true })
      ]);

      setStats(analyticsRes.data);
      setVenues(venuesRes.data);
      setCourts(courtsRes.data);

      if (user?.role === 'super_admin') {
        const tenantsRes = await axios.get(`${API}/tenants`, { withCredentials: true });
        setTenants(tenantsRes.data);
      }

      if (user?.tenant_id) {
        try {
          const tenantRes = await axios.get(`${API}/tenants/${user.tenant_id}`, { withCredentials: true });
          setTenantInfo(tenantRes.data);
        } catch (e) {
          // silently ignore
        }
      }
    } catch (error) {
      // silently ignore
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (!user) {
      navigate('/login');
    } else {
      fetchDashboardData();
    }
  }, [user, navigate, fetchDashboardData]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const renderVenues = () => (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-heading font-semibold text-indigo-950">Venues</h2>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowBulkImport(!showBulkImport)}
            className="inline-flex items-center px-4 py-2 text-sm font-medium bg-white border border-stone-200 text-indigo-950 rounded-xl hover:bg-stone-50"
            data-testid="bulk-import-button"
          >
            <UploadSimple className="w-4 h-4 mr-2" weight="bold" />
            Bulk Import
          </button>
          <button
            onClick={() => setShowCreateVenue(true)}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-emerald-700 rounded-xl hover:bg-emerald-800"
            data-testid="add-venue-button"
          >
            <Plus className="w-4 h-4 mr-2" weight="bold" />
            Add Venue
          </button>
        </div>
      </div>

      {showBulkImport && <BulkImportSection />}

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
    </div>
  );

  const renderCourts = () => (
    <div>
      <h2 className="text-2xl font-heading font-semibold text-indigo-950 mb-6">Court Management</h2>
      <div className="mb-6">
        <select
          value={selectedVenueForCourts?.id || ''}
          onChange={(e) => {
            const v = venues.find(v => v.id === e.target.value);
            setSelectedVenueForCourts(v);
          }}
          className="px-4 py-3 bg-white border border-stone-200 rounded-xl text-indigo-950 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
          data-testid="venue-select-for-courts"
        >
          <option value="">Select a venue</option>
          {venues.map((venue) => (
            <option key={venue.id} value={venue.id}>{venue.name}</option>
          ))}
        </select>
      </div>
      {selectedVenueForCourts && (
        <CourtManagement venueId={selectedVenueForCourts.id} venueName={selectedVenueForCourts.name} />
      )}
    </div>
  );

  const renderBookings = () => (
    <div>
      <h2 className="text-2xl font-heading font-semibold text-indigo-950 mb-6">Bookings</h2>
      {courts.length > 0 ? (
        <div>
          <div className="mb-6">
            <select
              value={selectedCourt?.id || ''}
              onChange={(e) => {
                const c = courts.find(c => c.id === e.target.value);
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
      ) : (
        <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-12 text-center">
          <p className="text-stone-500 mb-4">No courts available. Create a venue and add courts to start accepting bookings.</p>
          <button onClick={() => setActiveTab('venues')} className="px-6 py-3 text-sm font-medium text-white bg-emerald-700 rounded-xl hover:bg-emerald-800" data-testid="go-to-venues">
            Go to Venues
          </button>
        </div>
      )}
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <DashboardOverview
            stats={stats}
            venues={venues}
            tenantInfo={tenantInfo}
            user={user}
            copiedUrl={copiedUrl}
            setCopiedUrl={setCopiedUrl}
          />
        );
      case 'venues':
        return renderVenues();
      case 'courts':
        return renderCourts();
      case 'bookings':
        return renderBookings();
      case 'tenants':
        return <TenantManagement tenants={tenants} onAddTenant={() => setShowCreateTenant(true)} />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-emerald-700 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50" data-testid="dashboard-container">
      <SidebarNav
        user={user}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onLogout={handleLogout}
      />

      <div className="ml-64 p-8">
        <div className="max-w-7xl mx-auto">
          {renderContent()}
        </div>
      </div>

      <CreateVenueModal
        isOpen={showCreateVenue}
        onClose={() => setShowCreateVenue(false)}
        onSuccess={fetchDashboardData}
      />
      <CreateTenantModal
        isOpen={showCreateTenant}
        onClose={() => setShowCreateTenant(false)}
        onSuccess={fetchDashboardData}
      />
    </div>
  );
};

const BulkImportSection = () => (
  <div className="mb-6 p-6 bg-white border border-stone-200 rounded-2xl shadow-sm">
    <h3 className="text-lg font-medium text-indigo-950 mb-4">Bulk Import Venues</h3>
    <p className="text-sm text-stone-600 mb-4">Upload a CSV file to bulk import venues.</p>
    <input type="file" accept=".csv" className="text-sm text-stone-600" data-testid="csv-upload" />
  </div>
);

export default Dashboard;
