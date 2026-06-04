import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

type HookCardProps = {
  hook: string;
  petType: 'dog' | 'cat';
};

const COLORS = {
  dog: {bg: '#E84545', accent: '#FF8C42', emoji: '🐕'},
  cat: {bg: '#6C3FC5', accent: '#A78BFA', emoji: '🐱'},
};

export const HookCard: React.FC<HookCardProps> = ({hook, petType}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {bg, accent, emoji} = COLORS[petType];

  const opacity = interpolate(frame, [0, 8], [0, 1], {extrapolateRight: 'clamp'});

  const emojiScale = spring({
    fps,
    frame,
    config: {damping: 12, stiffness: 200, mass: 0.5},
  });

  const textSlide = interpolate(frame, [5, 20], [60, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(160deg, ${bg} 0%, #1A1A2E 100%)`,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 70,
        opacity,
      }}
    >
      <div
        style={{
          fontSize: 140,
          transform: `scale(${emojiScale})`,
          marginBottom: 48,
          filter: 'drop-shadow(0 8px 24px rgba(0,0,0,0.4))',
        }}
      >
        {emoji}
      </div>

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
          borderLeft: `8px solid ${accent}`,
          paddingLeft: 28,
        }}
      >
        {hook}
      </div>
    </AbsoluteFill>
  );
};
