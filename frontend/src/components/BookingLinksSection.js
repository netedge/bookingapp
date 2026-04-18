import React from 'react';
import { Globe, Link, Copy, CheckCircle } from '@phosphor-icons/react';

const BookingLinksSection = ({ venues, tenantInfo, user, copiedUrl, setCopiedUrl }) => {
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

  if ((!tenantInfo && user?.role !== 'super_admin') || venues.length === 0) return null;

  return (
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
        {venues.map((venue) => {
          const subdStr = tenantInfo?.subdomain || 'default';
          const urls = getBookingUrl(venue, subdStr);
          return (
            <div key={venue.id || venue.name} className="p-4 bg-stone-50 border border-stone-200 rounded-xl" data-testid={`booking-link-${venue.id}`}>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-indigo-950">{venue.name}</h3>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <Link className="w-4 h-4 text-stone-400 flex-shrink-0" weight="duotone" />
                  <code className="text-xs text-emerald-700 bg-emerald-50 px-2 py-1 rounded flex-1 truncate" data-testid={`booking-url-path-${venue.id}`}>
                    {urls.path}
                  </code>
                  <button
                    onClick={() => copyToClipboard(urls.path)}
                    className="flex items-center space-x-1 px-3 py-1 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-all flex-shrink-0"
                    data-testid={`copy-url-${venue.id}`}
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
                    <code className="text-xs text-sky-700 bg-sky-50 px-2 py-1 rounded flex-1 truncate" data-testid={`booking-url-subdomain-${venue.id}`}>
                      {urls.subdomain}
                    </code>
                    <button
                      onClick={() => copyToClipboard(urls.subdomain)}
                      className="flex items-center space-x-1 px-3 py-1 text-xs font-medium text-sky-700 bg-sky-50 border border-sky-200 rounded-lg hover:bg-sky-100 transition-all flex-shrink-0"
                      data-testid={`copy-subdomain-url-${venue.id}`}
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
  );
};

export default BookingLinksSection;
