import React, { Suspense, useEffect, useState } from 'react';

// Lazy-load so it is not in the main bundle chunk
const LazyCloudField = React.lazy(() =>
  import('@designcodeio/threeui/components/CloudField').then((m) => ({
    default: m.CloudField,
  }))
);

export default function CloudBackdrop() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
    return false;
  });

  const [isLite] = useState(() => {
    if (typeof window !== 'undefined' && window.location) {
      return new URLSearchParams(window.location.search).get('lite') === '1';
    }
    return false;
  });

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handler = (e) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  const wrapperStyle = {
    position: 'fixed',
    inset: 0,
    zIndex: -1,
    pointerEvents: 'none',
    overflow: 'hidden',
    background: prefersReducedMotion
      ? 'linear-gradient(180deg, #050510 0%, #14102a 100%)'
      : '#071010',
  };

  const iframeStyle = isLite
    ? {
        width: '50%',
        height: '50%',
        transform: 'scale(2)',
        transformOrigin: '0 0',
        pointerEvents: 'none',
      }
    : {
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
      };

  return (
    <div
      className="cloud-backdrop-wrapper"
      style={wrapperStyle}
      aria-hidden="true"
    >
      {!prefersReducedMotion && (
        <Suspense fallback={null}>
          <LazyCloudField
            mode="dark"
            hue={0}
            saturation={1}
            brightness={1}
            style={iframeStyle}
          />
        </Suspense>
      )}
    </div>
  );
}
