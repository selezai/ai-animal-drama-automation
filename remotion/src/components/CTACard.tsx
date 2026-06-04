import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

type CTACardProps = {
  cta: string;
  petType: 'dog' | 'cat';
};

const COLORS = {
  dog: {bg: '#E84545', paw: '#FF8C42'},
  cat: {bg: '#6C3FC5', paw: '#A78BFA'},
};

export const CTACard: React.FC<CTACardProps> = ({cta, petType}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {bg, paw} = COLORS[petType];

  const opacity = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});

  const scale = spring({
    fps,
    frame,
    config: {damping: 14, stiffness: 180, mass: 0.6},
  });

  const pawPulse = spring({
    fps,
    frame: frame % 30,
    config: {damping: 8, stiffness: 300, mass: 0.3},
  });

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(160deg, ${bg} 0%, #1A1A2E 100%)`,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 70,
        opacity,
        transform: `scale(${scale})`,
      }}
    >
      <div
        style={{
          fontSize: 100,
          transform: `scale(${pawPulse})`,
          marginBottom: 40,
        }}
      >
        🐾
      </div>

      <div
        style={{
          fontSize: 72,
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

      <div
        style={{
          marginTop: 48,
          width: 120,
          height: 6,
          backgroundColor: paw,
          borderRadius: 3,
        }}
      />
    </AbsoluteFill>
  );
};
