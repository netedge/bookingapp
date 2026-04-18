import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SubdomainRouter = ({ children }) => {
  const [checking, setChecking] = useState(true);
  const [tenantData, setTenantData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    checkSubdomain();
  }, []);

  const checkSubdomain = async () => {
    const hostname = window.location.hostname;
    // Check if we're on a subdomain (e.g., elite-sports.spancle.com)
    const parts = hostname.split('.');
    
    // Need at least 3 parts for subdomain: sub.domain.tld
    // Skip www, localhost, and IP addresses
    if (
      parts.length >= 3 &&
      parts[0] !== 'www' &&
      !hostname.match(/^\d+\.\d+\.\d+\.\d+$/) &&
      !hostname.includes('localhost') &&
      !hostname.includes('preview.emergentagent')
    ) {
      const subdomain = parts[0];
      try {
        const { data } = await axios.get(`${API}/public/tenant/${subdomain}`);
        setTenantData(data);
        // If tenant has venues, redirect to the first venue booking page
        if (data.venues && data.venues.length > 0) {
          navigate(`/book/${subdomain}/${data.venues[0].id}`, { replace: true });
        } else {
          navigate(`/book/${subdomain}`, { replace: true });
        }
      } catch (err) {
        // Not a valid tenant subdomain, continue to normal routing
        setChecking(false);
      }
    } else {
      setChecking(false);
    }
  };

  if (checking) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-emerald-700 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return children;
};

export default SubdomainRouter;
