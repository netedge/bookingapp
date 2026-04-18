import React, { useState, useEffect, useCallback } from 'react';
import { TrendUp, ChartBar } from '@phosphor-icons/react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AnalyticsCharts = () => {
  const [revenueTrend, setRevenueTrend] = useState({ dates: [], revenue: [], bookings: [] });
  const [courtOccupancy, setCourtOccupancy] = useState([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  const fetchAnalytics = useCallback(async () => {
    try {
      const [trendRes, occupancyRes] = await Promise.all([
        axios.get(`${API}/analytics/revenue-trend?days=${days}`, { withCredentials: true }),
        axios.get(`${API}/analytics/court-occupancy`, { withCredentials: true })
      ]);

      setRevenueTrend(trendRes.data);
      setCourtOccupancy(occupancyRes.data);
    } catch (error) {
      // silently ignore
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="w-12 h-12 border-4 border-emerald-700 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const maxRevenue = Math.max(...revenueTrend.revenue, 1);

  const getOccupancyGradient = (rate) => {
    if (rate > 75) return 'linear-gradient(90deg, #059669 0%, #047857 100%)';
    if (rate > 50) return 'linear-gradient(90deg, #ea580c 0%, #c2410c 100%)';
    return 'linear-gradient(90deg, #0284c7 0%, #0369a1 100%)';
  };

  return (
    <div className="space-y-6">
      {/* Revenue Trend Chart */}
      <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <TrendUp className="w-6 h-6 text-emerald-700" weight="duotone" />
            <h3 className="text-xl font-medium text-indigo-950">Revenue Trend</h3>
          </div>
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-4 py-2 bg-white border border-stone-200 rounded-lg text-sm text-indigo-950 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
            data-testid="days-select"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>

        {revenueTrend.dates.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-stone-500">No revenue data available</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-end justify-between space-x-2 h-64">
              {revenueTrend.revenue.map((revenue, idx) => (
                <div key={revenueTrend.dates[idx] || `rev-${idx}`} className="flex-1 flex flex-col items-center justify-end space-y-2">
                  <div className="w-full bg-gradient-to-t from-emerald-600 to-emerald-400 rounded-t-lg transition-all hover:opacity-80"
                    style={{ height: `${(revenue / maxRevenue) * 100}%`, minHeight: revenue > 0 ? '4px' : '0' }}
                    title={`$${revenue.toFixed(2)}`}
                  ></div>
                  {idx % Math.ceil(revenueTrend.dates.length / 7) === 0 && (
                    <span className="text-xs text-stone-500 transform -rotate-45 origin-left whitespace-nowrap">
                      {new Date(revenueTrend.dates[idx]).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </span>
                  )}
                </div>
              ))}
            </div>

            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-stone-200">
              <div>
                <p className="text-sm text-stone-600">Total Revenue</p>
                <p className="text-2xl font-semibold text-emerald-700">
                  ${revenueTrend.revenue.reduce((a, b) => a + b, 0).toFixed(2)}
                </p>
              </div>
              <div>
                <p className="text-sm text-stone-600">Total Bookings</p>
                <p className="text-2xl font-semibold text-sky-700">
                  {revenueTrend.bookings.reduce((a, b) => a + b, 0)}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Court Occupancy Chart */}
      <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
        <div className="flex items-center space-x-3 mb-6">
          <ChartBar className="w-6 h-6 text-sky-700" weight="duotone" />
          <h3 className="text-xl font-medium text-indigo-950">Court Occupancy</h3>
        </div>

        {courtOccupancy.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-stone-500">No court data available</p>
          </div>
        ) : (
          <div className="space-y-4">
            {courtOccupancy.map((court) => (
              <div key={court.court_id || court.court_name} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-indigo-950">{court.court_name}</p>
                    <p className="text-xs text-stone-500">{court.sport_type}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-emerald-700">{court.occupancy_rate.toFixed(1)}%</p>
                    <p className="text-xs text-stone-500">{court.bookings} bookings</p>
                  </div>
                </div>
                <div className="w-full bg-stone-200 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${court.occupancy_rate}%`,
                      background: getOccupancyGradient(court.occupancy_rate)
                    }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalyticsCharts;
