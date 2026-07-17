import { useState, useEffect } from 'react';

interface OfflineBannerProps {
  isOnline: boolean;
}

export default function OfflineBanner({ isOnline }: OfflineBannerProps) {
  const [visible, setVisible] = useState(false);
  const [wasOffline, setWasOffline] = useState(false);
  const [showBackOnline, setShowBackOnline] = useState(false);

  useEffect(() => {
    if (!isOnline) {
      setVisible(true);
      setWasOffline(true);
      setShowBackOnline(false);
    } else if (wasOffline) {
      // Just came back online
      setVisible(true);
      setShowBackOnline(true);
      const timer = setTimeout(() => {
        setVisible(false);
        setShowBackOnline(false);
        setWasOffline(false);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [isOnline, wasOffline]);

  if (!visible) return null;

  if (showBackOnline) {
    return (
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          zIndex: 9999,
          background: 'linear-gradient(90deg, #059669, #10b981)',
          color: '#fff',
          textAlign: 'center',
          padding: '10px 16px',
          fontSize: '14px',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          boxShadow: '0 2px 12px rgba(5,150,105,0.4)',
          animation: 'slideDown 0.3s ease',
        }}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M20 6L9 17l-5-5" />
        </svg>
        Back online! All features restored.
      </div>
    );
  }

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 9999,
        background: 'linear-gradient(90deg, #92400e, #d97706)',
        color: '#fff',
        textAlign: 'center',
        padding: '10px 16px',
        fontSize: '14px',
        fontWeight: 600,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '10px',
        boxShadow: '0 2px 12px rgba(217,119,6,0.4)',
      }}
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
        <path d="M1 1l22 22M16.72 11.06A10.94 10.94 0 0 1 19 12.55M5 12.55a10.94 10.94 0 0 1 5.17-2.39M10.71 5.05A16 16 0 0 1 22.54 9M1.42 9a15.91 15.91 0 0 1 4.7-2.88M8.53 16.11a6 6 0 0 1 6.95 0M12 20h.01" />
      </svg>
      <span>
        You're offline — the app is running from cache. Predictions & history still available.
      </span>
    </div>
  );
}
