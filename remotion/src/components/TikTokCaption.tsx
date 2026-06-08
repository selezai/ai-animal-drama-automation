import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

type Props = {
  text: string;
  accentColor?: string;
};

export const TikTokCaption: React.FC<Props> = ({
  text,
  accentColor = '#FFD700',
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const words = text.split(' ');
  const framesPerWord = Math.max(2, Math.floor(fps * 0.12));

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 120,
        left: 48,
        right: 48,
        zIndex: 10,
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'center',
        gap: '6px 10px',
      }}
    >
      {words.map((word, i) => {
        const wordStart = i * framesPerWord;
        const isActive = frame >= wordStart && frame < wordStart + framesPerWord;
        const hasAppeared = frame >= wordStart;

        const opacity = hasAppeared
          ? interpolate(frame, [wordStart, wordStart + 3], [0, 1], {
              extrapolateRight: 'clamp',
            })
          : 0;

        const scale = isActive ? 1.15 : 1.0;
        const y = hasAppeared
          ? interpolate(frame, [wordStart, wordStart + 4], [8, 0], {
              extrapolateRight: 'clamp',
            })
          : 8;

        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              fontSize: 52,
              fontWeight: 800,
              fontFamily: 'Arial Black, Impact, Arial, sans-serif',
              color: isActive ? accentColor : '#FFFFFF',
              textShadow: isActive
                ? `0 0 20px ${accentColor}, 0 3px 8px rgba(0,0,0,0.8)`
                : '0 3px 8px rgba(0,0,0,0.8), 0 1px 3px rgba(0,0,0,0.6)',
              opacity,
              transform: `translateY(${y}px) scale(${scale})`,
              transition: 'color 0.05s, transform 0.05s',
            }}
          >
            {word}
          </span>
        );
      })}
    </div>
  );
};
