import React from 'react';
import {
  ChartBar,
  House,
  Buildings,
  CalendarCheck,
  Users,
  SignOut
} from '@phosphor-icons/react';

const SidebarNav = ({ user, activeTab, setActiveTab, onLogout }) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: ChartBar },
    { id: 'venues', label: 'Venues', icon: House },
    { id: 'courts', label: 'Courts', icon: Buildings },
    { id: 'bookings', label: 'Bookings', icon: CalendarCheck },
  ];

  if (user?.role === 'super_admin') {
    navItems.push({ id: 'tenants', label: 'Tenants', icon: Users });
  }

  return (
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
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all ${
              activeTab === item.id
                ? 'bg-emerald-700 text-white'
                : 'text-stone-400 hover:bg-indigo-900 hover:text-white'
            }`}
            data-testid={`nav-${item.id}`}
          >
            <item.icon className="w-5 h-5" weight="duotone" />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-indigo-900">
        <div className="px-4 py-2 mb-2">
          <p className="text-sm font-medium text-white truncate">{user?.email}</p>
          <p className="text-xs text-stone-400">{user?.role?.replace('_', ' ')}</p>
        </div>
        <button
          onClick={onLogout}
          className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-stone-400 hover:bg-indigo-900 hover:text-white transition-all"
          data-testid="logout-button"
        >
          <SignOut className="w-5 h-5" weight="duotone" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
};

export default SidebarNav;
