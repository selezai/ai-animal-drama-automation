import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

type TipBodyProps = {
  teach: string;
  why: string;
  petType: 'dog' | 'cat';
  teachDurationFrames: number;
};

const THEME = {
  dog: {bg1: '#FF6B35', bg2: '#E84545', accent: '#FFBE76', panel: 'rgba(0,0,0,0.55)'},
  cat: {bg1: '#9333EA', bg2: '#6C3FC5', accent: '#C4B5FD', panel: 'rgba(0,0,0,0.55)'},
};

export const TipBody: React.FC<TipBodyProps> = ({teach, why, petType, teachDurationFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {bg1, bg2, accent, panel} = THEME[petType];

  const fadeIn = interpolate(frame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});

  const isWhySection = frame >= teachDurationFrames;

  const totalFrames = teachDurationFrames + fps * 5;
  const progress = interpolate(frame, [0, totalFrames], [0, 100], {extrapolateRight: 'clamp'});

  const gradientShift = Math.sin(frame * 0.03) * 30;

  const whySlideIn = interpolate(
    frame,
    [teachDurationFrames, teachDurationFrames + 15],
    [1920, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const teachSlideOut = interpolate(
    frame,
    [teachDurationFrames - 8, teachDurationFrames],
    [0, -1920],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

  const barWidth = interpolate(frame, [5, 30], [0, 120], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(${150 + gradientShift}deg, ${bg1} 0%, ${bg2} 60%, #1A1A2E 100%)`,
        opacity: fadeIn,
      }}
    >
      {/* Top progress bar */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: `${progress}%`,
          height: 12,
          backgroundColor: accent,
          boxShadow: `0 0 24px ${accent}`,
        }}
      />

      {/* Teach section */}
      {!isWhySection && (
        <AbsoluteFill
          style={{
            justifyContent: 'center',
            padding: 64,
            transform: `translateY(${teachSlideOut}px)`,
          }}
        >
          <div
            style={{
              backgroundColor: panel,
              borderRadius: 32,
              padding: '56px 48px',
              backdropFilter: 'blur(8px)',
              borderLeft: `12px solid ${accent}`,
            }}
          >
            <div
              style={{
                width: barWidth,
                height: 8,
                backgroundColor: accent,
                borderRadius: 4,
                marginBottom: 32,
              }}
            />
            <div
              style={{
                fontSize: 52,
                color: '#FFFFFF',
                lineHeight: 1.5,
                fontFamily: 'Arial, Helvetica, sans-serif',
                fontWeight: 600,
              }}
            >
              {teach}
            </div>
          </div>
        </AbsoluteFill>
      )}

      {/* Why section */}
      {isWhySection && (
        <AbsoluteFill
          style={{
            justifyContent: 'center',
            padding: 64,
            transform: `translateY(${whySlideIn}px)`,
          }}
        >
          <div
            style={{
              backgroundColor: panel,
              borderRadius: 32,
              padding: '56px 48px',
              backdropFilter: 'blur(8px)',
              borderLeft: `12px solid ${accent}`,
            }}
          >
            <div
              style={{
                fontSize: 40,
                color: accent,
                fontWeight: 800,
                fontFamily: 'Arial Black, Arial, sans-serif',
                textTransform: 'uppercase',
                letterSpacing: 6,
                marginBottom: 28,
              }}
            >
              ⚡ WHY IT MATTERS
            </div>
            <div
              style={{
                fontSize: 50,
                color: '#FFFFFF',
                lineHeight: 1.5,
                fontFamily: 'Arial, Helvetica, sans-serif',
                fontWeight: 600,
              }}
            >
              {why}
            </div>
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
