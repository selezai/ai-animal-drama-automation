import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

type CTACardProps = {
  cta: string;
  petType: 'dog' | 'cat';
};

const COLORS = {
  dog: {bg1: '#E84545', bg2: '#FF6B35', accent: '#FF8C42'},
  cat: {bg1: '#6C3FC5', bg2: '#9333EA', accent: '#A78BFA'},
};

export const CTACard: React.FC<CTACardProps> = ({cta, petType}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {bg1, bg2, accent} = COLORS[petType];

  const fadeIn = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});

  const scale = spring({fps, frame, config: {damping: 14, stiffness: 180, mass: 0.6}});

  const pawBounce = Math.sin(frame * 0.2) * 10;
  const pawRotate = Math.sin(frame * 0.15) * 8;

  const ringScale = 1 + Math.sin(frame * 0.12) * 0.08;
  const ringOpacity = 0.3 + Math.sin(frame * 0.12) * 0.2;

  const gradientAngle = 160 + Math.sin(frame * 0.04) * 15;

  const arrowBounce = Math.sin(frame * 0.25) * 6;

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(${gradientAngle}deg, ${bg1} 0%, ${bg2} 50%, #1A1A2E 100%)`,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 70,
        opacity: fadeIn,
        transform: `scale(${scale})`,
      }}
    >
      {/* Pulsing ring behind paw */}
      <div
        style={{
          position: 'absolute',
          width: 200,
          height: 200,
          borderRadius: '50%',
          border: `4px solid ${accent}`,
          opacity: ringOpacity,
          transform: `scale(${ringScale})`,
          top: '28%',
        }}
      />

      <div
        style={{
          fontSize: 110,
          transform: `translateY(${pawBounce}px) rotate(${pawRotate}deg)`,
          marginBottom: 40,
          filter: `drop-shadow(0 4px 16px ${accent})`,
        }}
      >
        🐾
      </div>

      <div
        style={{
          fontSize: 68,
          fontWeight: 900,
          color: '#FFFFFF',
          textAlign: 'center',
          lineHeight: 1.3,
          fontFamily: 'Arial Black, Impact, Arial, sans-serif',
          textShadow: '0 4px 20px rgba(0,0,0,0.5)',
        }}
      >
        {cta}
      </div>

      {/* Animated arrow */}
      <div
        style={{
          marginTop: 40,
          fontSize: 48,
          color: accent,
          transform: `translateY(${arrowBounce}px)`,
          filter: `drop-shadow(0 0 8px ${accent})`,
        }}
      >
        👆
      </div>

      <div
        style={{
          marginTop: 20,
          fontSize: 28,
          color: 'rgba(255,255,255,0.7)',
          fontFamily: 'Arial, sans-serif',
          fontWeight: 500,
        }}
      >
        Tap Follow
      </div>
    </AbsoluteFill>
  );
};
