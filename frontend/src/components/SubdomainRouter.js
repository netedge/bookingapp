import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SubdomainRouter = ({ children }) => {
  const [checking, setChecking] = useState(true);
  const navigate = useNavigate();

  const checkSubdomain = useCallback(async () => {
    const hostname = window.location.hostname;
    const parts = hostname.split('.');
    
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
        if (data.venues && data.venues.length > 0) {
          navigate(`/book/${subdomain}/${data.venues[0].id}`, { replace: true });
        } else {
          navigate(`/book/${subdomain}`, { replace: true });
        }
      } catch (err) {
        setChecking(false);
      }
    } else {
      setChecking(false);
    }
  }, [navigate]);

  useEffect(() => {
    checkSubdomain();
  }, [checkSubdomain]);

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
