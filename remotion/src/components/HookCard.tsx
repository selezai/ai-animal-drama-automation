import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

type HookCardProps = {
  hook: string;
  petType: 'dog' | 'cat';
};

const COLORS = {
  dog: {bg1: '#E84545', bg2: '#FF6B35', accent: '#FF8C42', emoji: '🐕'},
  cat: {bg1: '#6C3FC5', bg2: '#9333EA', accent: '#A78BFA', emoji: '🐱'},
};

export const HookCard: React.FC<HookCardProps> = ({hook, petType}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {bg1, bg2, accent, emoji} = COLORS[petType];

  const fadeIn = interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'});

  const emojiScale = spring({fps, frame, config: {damping: 12, stiffness: 200, mass: 0.5}});
  const emojiBounce = Math.sin(frame * 0.1) * 8;

  const textSlide = interpolate(frame, [5, 20], [60, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const gradientAngle = 160 + Math.sin(frame * 0.05) * 20;
  const pulseGlow = 0.4 + Math.sin(frame * 0.15) * 0.15;

  const borderHeight = interpolate(frame, [8, 25], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(${gradientAngle}deg, ${bg1} 0%, ${bg2} 50%, #1A1A2E 100%)`,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 70,
        opacity: fadeIn,
      }}
    >
      <div
        style={{
          fontSize: 140,
          transform: `scale(${emojiScale}) translateY(${emojiBounce}px)`,
          marginBottom: 48,
          filter: `drop-shadow(0 8px 24px rgba(0,0,0,${pulseGlow}))`,
        }}
      >
        {emoji}
      </div>

      <div style={{position: 'relative', display: 'flex', alignItems: 'center'}}>
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: '50%',
            width: 8,
            height: `${borderHeight}%`,
            backgroundColor: accent,
            borderRadius: 4,
            transform: 'translateY(-50%)',
            boxShadow: `0 0 20px ${accent}`,
          }}
        />
        <div
          style={{
            fontSize: 68,
            fontWeight: 900,
            color: '#FFFFFF',
            textAlign: 'center',
            lineHeight: 1.25,
            fontFamily: 'Arial Black, Impact, Arial, sans-serif',
            textShadow: `0 4px 20px rgba(0,0,0,0.5)`,
            transform: `translateY(${textSlide}px)`,
            paddingLeft: 36,
          }}
        >
          {hook}
        </div>
      </div>
    </AbsoluteFill>
  );
};
