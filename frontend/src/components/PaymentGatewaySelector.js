import React, { useState } from 'react';
import { CreditCard, Wallet, Bank } from '@phosphor-icons/react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PaymentGatewaySelector = ({ bookingId, amount, onSuccess }) => {
  const [selectedGateway, setSelectedGateway] = useState('stripe');
  const [loading, setLoading] = useState(false);

  const handleStripePayment = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(
        `${API}/payments/checkout`,
        {
          booking_id: bookingId,
          origin_url: window.location.origin
        },
        { withCredentials: true }
      );
      
      window.location.href = data.url;
    } catch (error) {
      alert(error.response?.data?.detail || 'Payment failed');
      setLoading(false);
    }
  };

  const handleRazorpayPayment = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(
        `${API}/payments/razorpay/create-order`,
        {
          booking_id: bookingId,
          amount: amount,
          currency: 'INR'
        },
        { withCredentials: true }
      );

      const options = {
        key: data.key_id,
        amount: data.amount,
        currency: data.currency,
        order_id: data.order_id,
        name: 'Kelika Sports',
        description: 'Venue Booking Payment',
        handler: async (response) => {
          try {
            await axios.post(
              `${API}/payments/razorpay/verify`,
              {
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature
              }
            );
            onSuccess();
          } catch (error) {
            alert('Payment verification failed');
          }
        },
        theme: {
          color: '#059669'
        }
      };

      const razorpay = new window.Razorpay(options);
      razorpay.open();
      setLoading(false);
    } catch (error) {
      alert(error.response?.data?.detail || 'Payment failed');
      setLoading(false);
    }
  };

  const handlePayPalPayment = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(
        `${API}/payments/paypal/create-order`,
        {
          booking_id: bookingId,
          return_url: `${window.location.origin}/payment-success`,
          cancel_url: `${window.location.origin}/payment-cancelled`
        },
        { withCredentials: true }
      );

      window.location.href = data.approval_url;
    } catch (error) {
      alert(error.response?.data?.detail || 'Payment failed');
      setLoading(false);
    }
  };

  const handleSkrillPayment = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(
        `${API}/payments/skrill/prepare`,
        {
          booking_id: bookingId,
          return_url: `${window.location.origin}/payment-success`,
          cancel_url: `${window.location.origin}/payment-cancelled`,
          status_url: `${API}/payments/skrill/status`
        }
      );

      window.location.href = data.payment_url;
    } catch (error) {
      alert(error.response?.data?.detail || 'Payment failed');
      setLoading(false);
    }
  };

  const handlePayment = () => {
    if (selectedGateway === 'stripe') {
      handleStripePayment();
    } else if (selectedGateway === 'razorpay') {
      handleRazorpayPayment();
    } else if (selectedGateway === 'paypal') {
      handlePayPalPayment();
    } else if (selectedGateway === 'skrill') {
      handleSkrillPayment();
    }
  };

  const gateways = [
    {
      id: 'stripe',
      name: 'Stripe',
      icon: <CreditCard className="w-6 h-6 text-emerald-700" weight="duotone" />,
      description: 'Credit/Debit Cards',
      currency: '$',
      color: 'emerald'
    },
    {
      id: 'razorpay',
      name: 'Razorpay',
      icon: <Wallet className="w-6 h-6 text-sky-700" weight="duotone" />,
      description: 'UPI, Cards, Netbanking',
      currency: '₹',
      color: 'sky'
    },
    {
      id: 'paypal',
      name: 'PayPal',
      icon: <Bank className="w-6 h-6 text-indigo-700" weight="duotone" />,
      description: 'PayPal Balance, Cards',
      currency: '$',
      color: 'indigo'
    },
    {
      id: 'skrill',
      name: 'Skrill',
      icon: <Wallet className="w-6 h-6 text-orange-600" weight="duotone" />,
      description: 'eWallet, Cards',
      currency: '€',
      color: 'orange'
    }
  ];

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-medium text-indigo-950 mb-4">Select Payment Method</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {gateways.map((gateway) => (
          <button
            key={gateway.id}
            onClick={() => setSelectedGateway(gateway.id)}
            className={`p-4 rounded-xl border-2 transition-all text-left ${
              selectedGateway === gateway.id
                ? `bg-${gateway.color}-50 border-${gateway.color}-600`
                : 'bg-white border-stone-200 hover:border-' + gateway.color + '-300'
            }`}
            data-testid={`payment-${gateway.id}`}
          >
            <div className="flex items-center space-x-3">
              {gateway.icon}
              <div>
                <h4 className="font-medium text-indigo-950">{gateway.name}</h4>
                <p className="text-xs text-stone-600">{gateway.description}</p>
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="p-4 bg-stone-50 border border-stone-200 rounded-xl">
        <div className="flex items-center justify-between">
          <span className="text-sm text-stone-600">Payment Gateway</span>
          <span className="font-medium text-indigo-950 capitalize">{selectedGateway}</span>
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-sm text-stone-600">Amount</span>
          <span className="text-xl font-semibold text-emerald-700">
            {gateways.find(g => g.id === selectedGateway)?.currency}{amount.toFixed(2)}
          </span>
        </div>
      </div>

      <button
        onClick={handlePayment}
        disabled={loading}
        className="w-full px-6 py-4 text-sm font-medium text-white bg-emerald-700 rounded-xl hover:bg-emerald-800 disabled:opacity-50 transition-all"
        data-testid="proceed-payment"
      >
        {loading ? 'Processing...' : `Pay with ${gateways.find(g => g.id === selectedGateway)?.name}`}
      </button>
    </div>
  );
};

export default PaymentGatewaySelector;
