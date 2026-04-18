import React from 'react';
import { motion } from 'framer-motion';
import {
  CurrencyDollar,
  CalendarCheck,
  House,
  Users,
  QrCode,
  TrendUp
} from '@phosphor-icons/react';
import AnalyticsCharts from './AnalyticsCharts';
import BookingLinksSection from './BookingLinksSection';

const DashboardOverview = ({ stats, venues, tenantInfo, user, copiedUrl, setCopiedUrl }) => {
  const statCards = [
    { label: 'Revenue', value: `$${(stats.total_revenue || 0).toFixed(2)}`, icon: CurrencyDollar, color: 'emerald' },
    { label: 'Bookings', value: stats.total_bookings || 0, icon: CalendarCheck, color: 'sky' },
    { label: 'Venues', value: stats.total_venues || 0, icon: House, color: 'orange' },
    { label: 'Customers', value: stats.total_customers || 0, icon: Users, color: 'indigo' },
  ];

  const colorMap = {
    emerald: 'bg-emerald-50 border-emerald-200',
    sky: 'bg-sky-50 border-sky-200',
    orange: 'bg-orange-50 border-orange-200',
    indigo: 'bg-indigo-50 border-indigo-200',
  };

  const iconColorMap = {
    emerald: 'text-emerald-700',
    sky: 'text-sky-700',
    orange: 'text-orange-600',
    indigo: 'text-indigo-800',
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`p-6 rounded-2xl border shadow-sm ${colorMap[stat.color]}`}
            data-testid={`stat-${stat.label.toLowerCase()}`}
          >
            <div className="flex items-center justify-between mb-2">
              <stat.icon className={`w-6 h-6 ${iconColorMap[stat.color]}`} weight="duotone" />
            </div>
            <p className="text-3xl font-semibold text-indigo-950">{stat.value}</p>
            <p className="text-sm text-stone-600">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
        <div className="flex items-center space-x-3 mb-4">
          <TrendUp className="w-6 h-6 text-emerald-700" weight="duotone" />
          <h2 className="text-lg font-medium text-indigo-950">Quick Actions</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <a href="#venues" className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl hover:bg-emerald-100 transition-all" data-testid="quick-action-venues">
            <House className="w-6 h-6 text-emerald-700 mb-2" weight="duotone" />
            <span className="text-sm font-medium text-indigo-950">Manage Venues</span>
          </a>
          <a href="#bookings" className="p-4 bg-sky-50 border border-sky-200 rounded-xl hover:bg-sky-100 transition-all" data-testid="quick-action-bookings">
            <CalendarCheck className="w-6 h-6 text-sky-700 mb-2" weight="duotone" />
            <span className="text-sm font-medium text-indigo-950">View Bookings</span>
          </a>
          <a href="#qr" className="p-4 bg-orange-50 border border-orange-200 rounded-xl hover:bg-orange-100 transition-all" data-testid="quick-action-qr">
            <QrCode className="w-6 h-6 text-orange-600 mb-2" weight="duotone" />
            <span className="text-sm font-medium text-indigo-950">Generate QR Codes</span>
          </a>
        </div>
      </div>

      <AnalyticsCharts />

      <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
        <h3 className="text-lg font-medium text-indigo-950 mb-4">Export Data</h3>
        <div className="flex items-center space-x-4">
          <a
            href={`${process.env.REACT_APP_BACKEND_URL}/api/export/bookings`}
            className="px-6 py-3 text-sm font-medium bg-white border border-stone-200 text-indigo-950 rounded-xl hover:bg-stone-50 transition-all"
            data-testid="export-bookings"
          >
            Export Bookings (CSV)
          </a>
          <a
            href={`${process.env.REACT_APP_BACKEND_URL}/api/export/analytics`}
            className="px-6 py-3 text-sm font-medium bg-white border border-stone-200 text-indigo-950 rounded-xl hover:bg-stone-50 transition-all"
            data-testid="export-analytics"
          >
            Export Analytics (CSV)
          </a>
        </div>
      </div>

      <BookingLinksSection
        venues={venues}
        tenantInfo={tenantInfo}
        user={user}
        copiedUrl={copiedUrl}
        setCopiedUrl={setCopiedUrl}
      />
    </div>
  );
};

export default DashboardOverview;
