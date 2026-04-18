import React from 'react';
import { Plus } from '@phosphor-icons/react';

const TenantManagement = ({ tenants, onAddTenant }) => {
  return (
    <div className="bg-white border border-stone-200 rounded-2xl shadow-sm overflow-hidden">
      <div className="p-6 border-b border-stone-200 flex items-center justify-between">
        <h2 className="text-xl font-medium text-indigo-950">Tenant Management</h2>
        <button
          onClick={onAddTenant}
          className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-emerald-700 rounded-xl hover:bg-emerald-800 transition-all"
          data-testid="add-tenant-button"
        >
          <Plus className="w-4 h-4 mr-2" weight="bold" />
          Add Tenant
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full" data-testid="tenants-table">
          <thead className="bg-stone-50 border-b border-stone-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-stone-500 uppercase">Business Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-stone-500 uppercase">Subdomain</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-stone-500 uppercase">Status</th>
            </tr>
          </thead>
          <tbody>
            {tenants.map((tenant) => (
              <tr key={tenant.id || tenant.subdomain} className="border-b border-stone-200 hover:bg-stone-50">
                <td className="px-6 py-4 text-sm font-medium text-indigo-950">{tenant.business_name}</td>
                <td className="px-6 py-4 text-sm">
                  <a
                    href={`/book/${tenant.subdomain}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-700 hover:underline"
                    data-testid={`tenant-subdomain-link-${tenant.id}`}
                  >
                    {tenant.subdomain}.spancle.com
                  </a>
                </td>
                <td className="px-6 py-4">
                  <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                    tenant.status === 'active'
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-stone-100 text-stone-600'
                  }`}>
                    {tenant.status || 'active'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TenantManagement;
