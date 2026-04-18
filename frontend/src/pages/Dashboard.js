import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { Plus, UploadSimple } from '@phosphor-icons/react';
import CreateTenantModal from '../components/CreateTenantModal';
import CreateVenueModal from '../components/CreateVenueModal';
import CourtManagement from '../components/CourtManagement';
import SidebarNav from '../components/SidebarNav';
import DashboardOverview from '../components/DashboardOverview';
import TenantManagement from '../components/TenantManagement';
import VenueGrid from '../components/VenueGrid';
import BookingPanel from '../components/BookingPanel';

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
          setTenantInfo(null);
        }
      }
    } catch (error) {
      setStats({ total_bookings: 0, total_venues: 0, total_customers: 0, total_revenue: 0 });
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
      <VenueGrid venues={venues} />
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
      <BookingPanel
        courts={courts}
        selectedCourt={selectedCourt}
        setSelectedCourt={setSelectedCourt}
        setActiveTab={setActiveTab}
      />
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
