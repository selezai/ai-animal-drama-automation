import React from 'react';
import {interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

type WordTimestamp = {word: string; start: number; end: number};

type Props = {
  text: string;
  accentColor?: string;
  wordTimestamps?: WordTimestamp[];
  sceneStartSec?: number;
};

export const TikTokCaption: React.FC<Props> = ({
  text,
  accentColor = '#FFD700',
  wordTimestamps = [],
  sceneStartSec = 0,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const currentSec = sceneStartSec + frame / fps;

  const textWords = text.split(' ').filter(w => w.length > 0);
  const useTimestamps = wordTimestamps.length > 0;

  const framesPerWord = Math.max(2, Math.floor(fps * 0.35));

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
      {textWords.map((word, i) => {
        let wordStartFrame: number;
        let wordEndFrame: number;

        if (useTimestamps && i < wordTimestamps.length) {
          wordStartFrame = Math.round((wordTimestamps[i].start - sceneStartSec) * fps);
          wordEndFrame = Math.round((wordTimestamps[i].end - sceneStartSec) * fps);
        } else {
          wordStartFrame = i * framesPerWord;
          wordEndFrame = wordStartFrame + framesPerWord;
        }

        const isActive = frame >= wordStartFrame && frame < wordEndFrame;
        const hasAppeared = frame >= wordStartFrame;

        const opacity = hasAppeared
          ? interpolate(frame, [wordStartFrame, wordStartFrame + 3], [0, 1], {
              extrapolateRight: 'clamp',
            })
          : 0;

        const scale = isActive ? 1.15 : 1.0;
        const y = hasAppeared
          ? interpolate(frame, [wordStartFrame, wordStartFrame + 4], [8, 0], {
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
