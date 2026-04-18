import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, TrendUp, CalendarDots, CreditCard, QrCode, ChartLine } from '@phosphor-icons/react';
import { motion } from 'framer-motion';

const fadeUp = { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 } };
const fadeScale = { initial: { opacity: 0, scale: 0.95 }, animate: { opacity: 1, scale: 1 } };

const Landing = () => {
  const navigate = useNavigate();

  const features = [
    {
      id: 'smart-booking',
      icon: <CalendarDots className="w-8 h-8 text-emerald-700" weight="duotone" />,
      title: 'Smart Booking Calendar',
      description: 'Intelligent slot management with real-time availability and conflict prevention.',
      color: 'bg-emerald-50 border-emerald-200'
    },
    {
      id: 'multi-payments',
      icon: <CreditCard className="w-8 h-8 text-sky-700" weight="duotone" />,
      title: 'Multi-Gateway Payments',
      description: 'Accept payments through Stripe, Razorpay, PayPal, and more payment providers.',
      color: 'bg-sky-50 border-sky-200'
    },
    {
      id: 'qr-booking',
      icon: <QrCode className="w-8 h-8 text-orange-600" weight="duotone" />,
      title: 'QR Code Booking',
      description: 'Generate QR codes for instant venue access and contactless bookings.',
      color: 'bg-orange-50 border-orange-200'
    },
    {
      id: 'analytics',
      icon: <ChartLine className="w-8 h-8 text-indigo-800" weight="duotone" />,
      title: 'Advanced Analytics',
      description: 'Track revenue, occupancy rates, peak hours, and customer insights.',
      color: 'bg-indigo-50 border-indigo-200'
    },
    {
      id: 'dynamic-pricing',
      icon: <TrendUp className="w-8 h-8 text-emerald-700" weight="duotone" />,
      title: 'Dynamic Pricing',
      description: 'Peak hour pricing, weekend rates, and seasonal pricing automation.',
      color: 'bg-emerald-50 border-emerald-200'
    }
  ];

  return (
    <div className="min-h-screen bg-stone-50">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full bg-white/80 backdrop-blur-xl border-b border-stone-200/50">
        <div className="max-w-7xl mx-auto px-6 sm:px-12 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-emerald flex items-center justify-center">
              <span className="text-white font-bold text-xl">S</span>
            </div>
            <span className="text-2xl font-heading font-semibold text-indigo-950">Spancle</span>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/login')}
              className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium transition-colors text-stone-600 rounded-xl hover:text-indigo-950 hover:bg-stone-100"
              data-testid="header-login-button"
            >
              Sign In
            </button>
            <button
              onClick={() => navigate('/register')}
              className="inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white transition-all bg-emerald-700 rounded-xl hover:bg-emerald-800 hover:-translate-y-0.5 shadow-sm hover:shadow-md"
              data-testid="header-signup-button"
            >
              Get Started
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-24 lg:py-32 px-6 sm:px-12">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={fadeUp.initial}
            animate={fadeUp.animate}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-indigo-950 mb-6">
              Transform Your Sports Venue Into a Digital Business
            </h1>
            <p className="text-base text-stone-600 leading-relaxed mb-8 max-w-xl">
              Spancle is a multi-tenant SaaS platform that empowers sports venue owners with white-labeled booking systems, payment processing, and complete business management tools.
            </p>
            <div className="flex flex-wrap gap-4">
              <button
                onClick={() => navigate('/register')}
                className="inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-white transition-all bg-emerald-700 rounded-xl hover:bg-emerald-800 hover:-translate-y-0.5 shadow-sm hover:shadow-md"
                data-testid="hero-get-started-button"
              >
                Start Free Trial
                <ArrowRight className="ml-2 w-5 h-5" weight="bold" />
              </button>
              <button
                onClick={() => navigate('/login')}
                className="inline-flex items-center justify-center px-6 py-3 text-sm font-medium transition-all bg-white border border-stone-200 text-indigo-950 rounded-xl hover:bg-stone-50 hover:border-stone-300 shadow-sm"
                data-testid="hero-demo-button"
              >
                View Demo
              </button>
            </div>
          </motion.div>

          <motion.div
            initial={fadeScale.initial}
            animate={fadeScale.animate}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="relative"
          >
            <div className="relative rounded-3xl overflow-hidden shadow-2xl border border-stone-200">
              <img
                src="https://static.prod-images.emergentagent.com/jobs/e96b9494-564d-4eaf-9ba4-2ffac064b6b1/images/a38b0357570444e03c9e81810c8a3a0daa5d0c118e74c914c2adeb8c20f5b247.png"
                alt="Spancle Dashboard"
                className="w-full h-auto"
              />
            </div>
            <div className="absolute -bottom-6 -right-6 w-32 h-32 bg-orange-600 rounded-full blur-3xl opacity-20"></div>
            <div className="absolute -top-6 -left-6 w-32 h-32 bg-emerald-700 rounded-full blur-3xl opacity-20"></div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6 sm:px-12 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-emerald-700">Features</span>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-medium tracking-tight text-indigo-950 mt-4">
              Everything You Need to Run Your Venue
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.id}
                initial={fadeUp.initial}
                whileInView={fadeUp.animate}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                viewport={{ once: true }}
                className={`bg-white border rounded-2xl shadow-sm transition-all hover:shadow-md p-6 ${feature.color}`}
                data-testid={`feature-card-${index}`}
              >
                <div className="mb-4">{feature.icon}</div>
                <h3 className="text-xl sm:text-2xl font-medium text-indigo-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-base text-stone-600 leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-6 sm:px-12 bg-gradient-space">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-medium tracking-tight text-white mb-6">
            Ready to Transform Your Venue Business?
          </h2>
          <p className="text-base text-stone-300 leading-relaxed mb-8">
            Join hundreds of sports venues already using Spancle to streamline operations and boost revenue.
          </p>
          <button
            onClick={() => navigate('/register')}
            className="inline-flex items-center justify-center px-6 py-3 text-sm font-medium text-indigo-950 transition-all bg-white rounded-xl hover:bg-stone-50 shadow-sm hover:shadow-md"
            data-testid="cta-get-started-button"
          >
            Get Started Now
            <ArrowRight className="ml-2 w-5 h-5" weight="bold" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 sm:px-12 bg-white border-t border-stone-200">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-sm text-stone-500">© 2026 Spancle. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;