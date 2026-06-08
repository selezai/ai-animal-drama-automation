import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  text: string;
  petType: 'dog' | 'cat';
  isHook: boolean;
  isCta: boolean;
};

const ACCENT = {dog: '#FFBE76', cat: '#C4B5FD'};

export const CaptionOverlay: React.FC<Props> = ({text, petType, isHook, isCta}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const accent = ACCENT[petType];

  const slideUp = interpolate(frame, [0, 12], [80, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const opacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: 'clamp',
  });

  const fontSize = isHook ? 58 : isCta ? 56 : 44;
  const fontWeight = isHook || isCta ? 900 : 600;

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 8,
        padding: '0 48px 80px 48px',
        background: 'linear-gradient(transparent 0%, rgba(0,0,0,0.7) 40%, rgba(0,0,0,0.85) 100%)',
        transform: `translateY(${slideUp}px)`,
        opacity,
      }}
    >
      {/* Accent line above text */}
      <div
        style={{
          width: 80,
          height: 6,
          backgroundColor: accent,
          borderRadius: 3,
          marginBottom: 20,
          boxShadow: `0 0 12px ${accent}`,
        }}
      />

      <div
        style={{
          fontSize,
          fontWeight,
          color: '#FFFFFF',
          lineHeight: 1.4,
          fontFamily: isHook || isCta
            ? 'Arial Black, Impact, Arial, sans-serif'
            : 'Arial, Helvetica, sans-serif',
          textShadow: '0 2px 8px rgba(0,0,0,0.5)',
        }}
      >
        {text}
      </div>

      {isCta && (
        <div
          style={{
            marginTop: 24,
            fontSize: 32,
            color: accent,
            fontWeight: 700,
            fontFamily: 'Arial, sans-serif',
          }}
        >
          👆 Tap Follow
        </div>
      )}
    </div>
  );
};
