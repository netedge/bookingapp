import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import {
  House,
  TrendUp,
  CalendarCheck,
  Users,
  CurrencyDollar,
  SignOut,
  Buildings,
  Plus,
  QrCode,
  ChartBar,
  UploadSimple,
  Link,
  Copy,
  Globe,
  CheckCircle
} from '@phosphor-icons/react';
import { motion } from 'framer-motion';
import CreateTenantModal from '../components/CreateTenantModal';
import CreateVenueModal from '../components/CreateVenueModal';
import BookingCalendar from '../components/BookingCalendar';
import AnalyticsCharts from '../components/AnalyticsCharts';
import CourtManagement from '../components/CourtManagement';

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

  useEffect(() => {
    if (!user) {
      navigate('/login');
    } else {
      fetchDashboardData();
    }
  }, [user, navigate]);

  const fetchDashboardData = async () => {
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

      // Fetch tenant info for booking URLs
      if (user?.tenant_id) {
        try {
          const tenantRes = await axios.get(`${API}/tenants/${user.tenant_id}`, { withCredentials: true });
          setTenantInfo(tenantRes.data);
        } catch (e) {
          console.error('Failed to fetch tenant info');
        }
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const renderSidebar = () => (
    <div className="fixed inset-y-0 left-0 z-40 w-64 bg-indigo-950 border-r border-indigo-900 text-stone-300">
      <div className="p-6 border-b border-indigo-900">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-emerald flex items-center justify-center">
            <span className="text-white font-bold text-xl">S</span>
          </div>
          <span className="text-2xl font-heading font-semibold text-white">Spancle</span>
        </div>
      </div>

      <nav className="p-4 space-y-2">
        <button
          onClick={() => setActiveTab('overview')}
          className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
            activeTab === 'overview'
              ? 'bg-emerald-700 text-white'
              : 'text-stone-400 hover:bg-indigo-900 hover:text-white'
          }`}
          data-testid="nav-overview"
        >
          <ChartBar className="w-5 h-5" weight="duotone" />
          <span>Overview</span>
        </button>

        <button
          onClick={() => setActiveTab('venues')}
          className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
            activeTab === 'venues'
              ? 'bg-emerald-700 text-white'
              : 'text-stone-400 hover:bg-indigo-900 hover:text-white'
          }`}
          data-testid="nav-venues"
        >
          <Buildings className="w-5 h-5" weight="duotone" />
          <span>Venues</span>
        </button>

        <button
          onClick={() => setActiveTab('courts')}
          className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
            activeTab === 'courts'
              ? 'bg-emerald-700 text-white'
              : 'text-stone-400 hover:bg-indigo-900 hover:text-white'
          }`}
          data-testid="nav-courts"
        >
          <Buildings className="w-5 h-5" weight="duotone" />
          <span>Courts</span>
        </button>

        <button
          onClick={() => setActiveTab('bookings')}
          className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
            activeTab === 'bookings'
              ? 'bg-emerald-700 text-white'
              : 'text-stone-400 hover:bg-indigo-900 hover:text-white'
          }`}
          data-testid="nav-bookings"
        >
          <CalendarCheck className="w-5 h-5" weight="duotone" />
          <span>Bookings</span>
        </button>

        {user?.role === 'super_admin' && (
          <button
            onClick={() => setActiveTab('tenants')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === 'tenants'
                ? 'bg-emerald-700 text-white'
                : 'text-stone-400 hover:bg-indigo-900 hover:text-white'
            }`}
            data-testid="nav-tenants"
          >
            <House className="w-5 h-5" weight="duotone" />
            <span>Tenants</span>
          </button>
        )}
      </nav>

      <div className="absolute bottom-0 w-full p-4 border-t border-indigo-900">
        <div className="mb-4 p-3 bg-indigo-900 rounded-xl">
          <p className="text-xs text-stone-400">Signed in as</p>
          <p className="text-sm text-white font-medium truncate">{user?.email}</p>
          <p className="text-xs text-emerald-400 mt-1 capitalize">{user?.role?.replace('_', ' ')}</p>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-orange-600 text-white rounded-xl hover:bg-orange-700 transition-all"
          data-testid="logout-button"
        >
          <SignOut className="w-5 h-5" weight="bold" />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );

  const copyToClipboard = (url) => {
    navigator.clipboard.writeText(url);
    setCopiedUrl(url);
    setTimeout(() => setCopiedUrl(null), 2000);
  };

  const getBookingUrl = (venue, subdomainStr) => {
    const domain = window.location.origin.replace(/https?:\/\//, '').split(':')[0].replace('www.', '');
    const baseHost = domain.includes('.') ? domain.split('.').slice(-2).join('.') : domain;
    return {
      subdomain: `https://${subdomainStr}.${baseHost}/book/${venue.id}`,
      path: `${window.location.origin}/book/${subdomainStr}/${venue.id}`
    };
  };

  const renderOverview = () => (
    <div>
      <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight text-indigo-950 mb-8">
        Dashboard Overview
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6 hover-lift"
          data-testid="stat-revenue"
        >
          <div className="flex items-center justify-between mb-4">
            <CurrencyDollar className="w-8 h-8 text-emerald-700" weight="duotone" />
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-700">Revenue</span>
          </div>
          <p className="text-3xl font-semibold text-indigo-950">${stats.total_revenue.toFixed(2)}</p>
          <p className="text-sm text-stone-500 mt-1">Total earnings</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6 hover-lift"
          data-testid="stat-bookings"
        >
          <div className="flex items-center justify-between mb-4">
            <CalendarCheck className="w-8 h-8 text-sky-700" weight="duotone" />
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-sky-700">Bookings</span>
          </div>
          <p className="text-3xl font-semibold text-indigo-950">{stats.total_bookings}</p>
          <p className="text-sm text-stone-500 mt-1">Total bookings</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6 hover-lift"
          data-testid="stat-venues"
        >
          <div className="flex items-center justify-between mb-4">
            <Buildings className="w-8 h-8 text-orange-600" weight="duotone" />
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-orange-600">Venues</span>
          </div>
          <p className="text-3xl font-semibold text-indigo-950">{stats.total_venues}</p>
          <p className="text-sm text-stone-500 mt-1">Active venues</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6 hover-lift"
          data-testid="stat-customers"
        >
          <div className="flex items-center justify-between mb-4">
            <Users className="w-8 h-8 text-indigo-800" weight="duotone" />
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-800">Customers</span>
          </div>
          <p className="text-3xl font-semibold text-indigo-950">{stats.total_customers}</p>
          <p className="text-sm text-stone-500 mt-1">Total customers</p>
        </motion.div>
      </div>

      <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
        <h2 className="text-2xl font-medium text-indigo-950 mb-6">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => setActiveTab('venues')}
            className="flex items-center space-x-3 p-4 bg-emerald-50 border border-emerald-200 rounded-xl hover:bg-emerald-100 transition-all"
            data-testid="quick-action-venues"
          >
            <Buildings className="w-6 h-6 text-emerald-700" weight="duotone" />
            <span className="text-sm font-medium text-emerald-800">Manage Venues</span>
          </button>
          <button
            onClick={() => setActiveTab('bookings')}
            className="flex items-center space-x-3 p-4 bg-sky-50 border border-sky-200 rounded-xl hover:bg-sky-100 transition-all"
            data-testid="quick-action-bookings"
          >
            <CalendarCheck className="w-6 h-6 text-sky-700" weight="duotone" />
            <span className="text-sm font-medium text-sky-800">View Bookings</span>
          </button>
          <button
            className="flex items-center space-x-3 p-4 bg-orange-50 border border-orange-200 rounded-xl hover:bg-orange-100 transition-all"
            data-testid="quick-action-qr"
          >
            <QrCode className="w-6 h-6 text-orange-600" weight="duotone" />
            <span className="text-sm font-medium text-orange-800">Generate QR Codes</span>
          </button>
        </div>
      </div>

      <div className="mt-8">
        <AnalyticsCharts />
      </div>

      <div className="mt-8 bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
        <h2 className="text-2xl font-medium text-indigo-950 mb-4">Export Data</h2>
        <div className="flex flex-wrap gap-4">
          <a
            href={`${API}/export/bookings`}
            download
            className="inline-flex items-center px-6 py-3 text-sm font-medium text-white bg-sky-700 rounded-xl hover:bg-sky-800"
            data-testid="export-bookings"
          >
            <UploadSimple className="w-5 h-5 mr-2" weight="bold" />
            Export Bookings CSV
          </a>
          <a
            href={`${API}/export/analytics?days=30`}
            download
            className="inline-flex items-center px-6 py-3 text-sm font-medium text-white bg-orange-600 rounded-xl hover:bg-orange-700"
            data-testid="export-analytics"
          >
            <UploadSimple className="w-5 h-5 mr-2" weight="bold" />
            Export Analytics CSV
          </a>
        </div>
      </div>

      {/* My Booking Links */}
      {(tenantInfo || user?.role === 'super_admin') && venues.length > 0 && (
        <div className="mt-8 bg-white border border-stone-200 rounded-2xl shadow-sm p-6" data-testid="booking-links-section">
          <div className="flex items-center space-x-3 mb-6">
            <Globe className="w-6 h-6 text-emerald-700" weight="duotone" />
            <h2 className="text-lg font-medium text-indigo-950">My Public Booking Links</h2>
          </div>
          
          {tenantInfo?.subdomain && (
            <div className="mb-4 p-4 bg-indigo-50 border border-indigo-200 rounded-xl">
              <p className="text-sm text-indigo-700 mb-1">Your Tenant Subdomain</p>
              <p className="text-base font-semibold text-indigo-950" data-testid="tenant-subdomain">
                {tenantInfo.subdomain}.spancle.com
              </p>
            </div>
          )}

          <div className="space-y-3">
            {venues.map((venue, idx) => {
              const subdStr = tenantInfo?.subdomain || 'default';
              const urls = getBookingUrl(venue, subdStr);
              return (
                <div key={idx} className="p-4 bg-stone-50 border border-stone-200 rounded-xl" data-testid={`booking-link-${idx}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-indigo-950">{venue.name}</h3>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Link className="w-4 h-4 text-stone-400 flex-shrink-0" weight="duotone" />
                      <code className="text-xs text-emerald-700 bg-emerald-50 px-2 py-1 rounded flex-1 truncate" data-testid={`booking-url-path-${idx}`}>
                        {urls.path}
                      </code>
                      <button
                        onClick={() => copyToClipboard(urls.path)}
                        className="flex items-center space-x-1 px-3 py-1 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-all flex-shrink-0"
                        data-testid={`copy-url-${idx}`}
                      >
                        {copiedUrl === urls.path ? (
                          <><CheckCircle className="w-3 h-3" weight="fill" /><span>Copied!</span></>
                        ) : (
                          <><Copy className="w-3 h-3" /><span>Copy</span></>
                        )}
                      </button>
                    </div>

                    {tenantInfo?.subdomain && (
                      <div className="flex items-center space-x-2">
                        <Globe className="w-4 h-4 text-stone-400 flex-shrink-0" weight="duotone" />
                        <code className="text-xs text-sky-700 bg-sky-50 px-2 py-1 rounded flex-1 truncate" data-testid={`booking-url-subdomain-${idx}`}>
                          {urls.subdomain}
                        </code>
                        <button
                          onClick={() => copyToClipboard(urls.subdomain)}
                          className="flex items-center space-x-1 px-3 py-1 text-xs font-medium text-sky-700 bg-sky-50 border border-sky-200 rounded-lg hover:bg-sky-100 transition-all flex-shrink-0"
                          data-testid={`copy-subdomain-url-${idx}`}
                        >
                          {copiedUrl === urls.subdomain ? (
                            <><CheckCircle className="w-3 h-3" weight="fill" /><span>Copied!</span></>
                          ) : (
                            <><Copy className="w-3 h-3" /><span>Copy</span></>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          
          {tenantInfo?.subdomain && (
            <p className="mt-4 text-xs text-stone-500">
              Subdomain URLs (e.g., {tenantInfo.subdomain}.spancle.com) require wildcard DNS setup. Path URLs work immediately.
            </p>
          )}
        </div>
      )}
    </div>
  );

  const renderVenues = () => (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight text-indigo-950">Venues</h1>
        <button
          onClick={() => setShowCreateVenue(true)}
          className="inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white transition-all bg-emerald-700 rounded-xl hover:bg-emerald-800 hover:-translate-y-0.5 shadow-sm hover:shadow-md"
          data-testid="create-venue-button"
        >
          <Plus className="w-5 h-5 mr-2" weight="bold" />
          Add Venue
        </button>
      </div>

      {venues.length === 0 ? (
        <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-12 text-center">
          <Buildings className="w-16 h-16 text-stone-400 mx-auto mb-4" weight="duotone" />
          <h3 className="text-xl font-medium text-indigo-950 mb-2">No venues yet</h3>
          <p className="text-base text-stone-600 mb-6">Create your first venue to start accepting bookings</p>
          <button
            onClick={() => setShowCreateVenue(true)}
            className="inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white transition-all bg-emerald-700 rounded-xl hover:bg-emerald-800"
            data-testid="empty-create-venue-button"
          >
            <Plus className="w-5 h-5 mr-2" weight="bold" />
            Create First Venue
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {venues.map((venue, index) => (
            <div
              key={index}
              className="bg-white border border-stone-200 rounded-2xl shadow-sm overflow-hidden hover-lift"
              data-testid={`venue-card-${index}`}
            >
              <img
                src={venue.image_url || 'https://images.unsplash.com/photo-1765124540460-b884e248ac2b'}
                alt={venue.name}
                className="w-full h-48 object-cover"
              />
              <div className="p-6">
                <h3 className="text-xl font-medium text-indigo-950 mb-2">{venue.name}</h3>
                <p className="text-sm text-stone-600 mb-4">{venue.description}</p>
                <p className="text-sm text-stone-500">{venue.address}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-emerald-700 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-stone-600">Loading dashboard...</p>
          </div>
        </div>
      );
    }

    switch (activeTab) {
      case 'overview':
        return renderOverview();
      case 'venues':
        return renderVenues();
      case 'courts':
        return (
          <div>
            <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight text-indigo-950 mb-8">Court Management</h1>
            
            {venues.length === 0 ? (
              <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-12 text-center">
                <Buildings className="w-16 h-16 text-stone-400 mx-auto mb-4" weight="duotone" />
                <h3 className="text-xl font-medium text-indigo-950 mb-2">No venues yet</h3>
                <p className="text-base text-stone-600 mb-6">Create a venue first to add courts</p>
                <button
                  onClick={() => setActiveTab('venues')}
                  className="inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white bg-emerald-700 rounded-xl hover:bg-emerald-800"
                >
                  Go to Venues
                </button>
              </div>
            ) : (
              <div>
                <div className="mb-6">
                  <label className="block mb-2 text-sm font-medium text-indigo-950">Select Venue</label>
                  <select
                    value={selectedVenueForCourts?.id || ''}
                    onChange={(e) => {
                      const venue = venues.find(v => v.id === e.target.value);
                      setSelectedVenueForCourts(venue);
                    }}
                    className="w-full max-w-md px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                    data-testid="venue-select-courts"
                  >
                    <option value="">Choose a venue</option>
                    {venues.map((venue, idx) => (
                      <option key={idx} value={venue.id}>
                        {venue.name}
                      </option>
                    ))}
                  </select>
                </div>

                {selectedVenueForCourts && (
                  <CourtManagement
                    venueId={selectedVenueForCourts.id}
                    venueName={selectedVenueForCourts.name}
                  />
                )}
              </div>
            )}
          </div>
        );
      case 'bookings':
        return (
          <div>
            <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight text-indigo-950 mb-8">Bookings</h1>
            
            {courts.length === 0 ? (
              <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-12 text-center">
                <CalendarCheck className="w-16 h-16 text-stone-400 mx-auto mb-4" weight="duotone" />
                <h3 className="text-xl font-medium text-indigo-950 mb-2">No courts available</h3>
                <p className="text-base text-stone-600 mb-6">Create a venue and add courts to start accepting bookings</p>
                <button
                  onClick={() => setActiveTab('venues')}
                  className="inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white bg-emerald-700 rounded-xl hover:bg-emerald-800"
                >
                  Go to Venues
                </button>
              </div>
            ) : (
              <div>
                <div className="mb-6">
                  <label className="block mb-2 text-sm font-medium text-indigo-950">Select Court</label>
                  <select
                    value={selectedCourt || ''}
                    onChange={(e) => setSelectedCourt(e.target.value)}
                    className="w-full max-w-md px-4 py-3 bg-white border border-stone-200 rounded-lg text-indigo-950 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                    data-testid="court-select"
                  >
                    <option value="">Choose a court</option>
                    {courts.map((court, idx) => (
                      <option key={idx} value={court.id || idx}>
                        {court.name} - {court.sport_type}
                      </option>
                    ))}
                  </select>
                </div>

                {selectedCourt && (
                  <BookingCalendar
                    courtId={selectedCourt}
                    courtName={courts.find(c => (c.id || courts.indexOf(c).toString()) === selectedCourt)?.name}
                  />
                )}
              </div>
            )}
          </div>
        );
      case 'tenants':
        return (
          <div>
            <div className="flex items-center justify-between mb-8">
              <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight text-indigo-950">Tenants</h1>
              <button
                onClick={() => setShowCreateTenant(true)}
                className="inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white transition-all bg-emerald-700 rounded-xl hover:bg-emerald-800 hover:-translate-y-0.5 shadow-sm hover:shadow-md"
                data-testid="create-tenant-button"
              >
                <Plus className="w-5 h-5 mr-2" weight="bold" />
                Add Tenant
              </button>
            </div>
            <div className="bg-white border border-stone-200 rounded-2xl shadow-sm overflow-hidden">
              <table className="w-full">
                <thead className="bg-stone-50 border-b border-stone-200">
                  <tr>
                    <th className="px-6 py-4 text-left text-sm font-medium text-indigo-950">Business Name</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-indigo-950">Subdomain</th>
                    <th className="px-6 py-4 text-left text-sm font-medium text-indigo-950">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {tenants.map((tenant, index) => (
                    <tr key={index} className="border-b border-stone-200 hover:bg-stone-50">
                      <td className="px-6 py-4 text-sm text-stone-600">{tenant.business_name}</td>
                      <td className="px-6 py-4 text-sm">
                        <a 
                          href={`/book/${tenant.subdomain}`} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-emerald-700 hover:underline"
                          data-testid={`tenant-subdomain-link-${index}`}
                        >
                          {tenant.subdomain}.spancle.com
                        </a>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex px-3 py-1 text-xs font-medium rounded-full bg-emerald-50 text-emerald-800">
                          {tenant.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      default:
        return renderOverview();
    }
  };

  return (
    <div className="min-h-screen bg-stone-50">
      {renderSidebar()}
      <div className="ml-64 p-8">
        {renderContent()}
      </div>

      <CreateTenantModal
        isOpen={showCreateTenant}
        onClose={() => setShowCreateTenant(false)}
        onSuccess={fetchDashboardData}
      />

      <CreateVenueModal
        isOpen={showCreateVenue}
        onClose={() => setShowCreateVenue(false)}
        onSuccess={fetchDashboardData}
      />
    </div>
  );
};

export default Dashboard;
