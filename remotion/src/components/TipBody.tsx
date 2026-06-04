import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';

type TipBodyProps = {
  teach: string;
  why: string;
  petType: 'dog' | 'cat';
  teachDurationFrames: number;
};

const ACCENT = {dog: '#FF8C42', cat: '#A78BFA'};

export const TipBody: React.FC<TipBodyProps> = ({teach, why, petType, teachDurationFrames}) => {
  const frame = useCurrentFrame();
  const accent = ACCENT[petType];

  const opacity = interpolate(frame, [0, 12], [0, 1], {extrapolateRight: 'clamp'});
  const slideY = interpolate(frame, [0, 15], [50, 0], {extrapolateRight: 'clamp'});

  const isWhySection = frame >= teachDurationFrames;
  const whyOpacity = interpolate(
    frame,
    [teachDurationFrames, teachDurationFrames + 12],
    [0, 1],
    {extrapolateRight: 'clamp'},
  );

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(180deg, #1A1A2E 0%, #0D0D0D 100%)',
        padding: 64,
        justifyContent: 'center',
        opacity,
        transform: `translateY(${slideY}px)`,
      }}
    >
      <div
        style={{
          width: 10,
          height: 80,
          backgroundColor: accent,
          borderRadius: 5,
          marginBottom: 36,
        }}
      />

      {!isWhySection && (
        <div
          style={{
            fontSize: 54,
            color: '#F0F0F0',
            lineHeight: 1.55,
            fontFamily: 'Arial, sans-serif',
            fontWeight: 500,
          }}
        >
          {teach}
        </div>
      )}

      {isWhySection && (
        <div style={{opacity: whyOpacity}}>
          <div
            style={{
              fontSize: 36,
              color: accent,
              fontWeight: 700,
              fontFamily: 'Arial Black, Arial, sans-serif',
              textTransform: 'uppercase',
              letterSpacing: 4,
              marginBottom: 24,
            }}
          >
            Why it matters
          </div>
          <div
            style={{
              fontSize: 52,
              color: '#F0F0F0',
              lineHeight: 1.55,
              fontFamily: 'Arial, sans-serif',
              fontWeight: 500,
            }}
          >
            {why}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
