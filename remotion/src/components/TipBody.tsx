import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';

type TipBodyProps = {
  teach: string;
  why: string;
  petType: 'dog' | 'cat';
  teachDurationFrames: number;
};

const ACCENT = {dog: '#FF8C42', cat: '#A78BFA'};
const BG2 = {dog: '#1F0A0A', cat: '#0F0A1F'};

const WordReveal: React.FC<{text: string; startFrame: number; framesPerWord: number}> = ({
  text,
  startFrame,
  framesPerWord,
}) => {
  const frame = useCurrentFrame();
  const words = text.split(' ');

  return (
    <span>
      {words.map((word, i) => {
        const wordStart = startFrame + i * framesPerWord;
        const opacity = interpolate(frame, [wordStart, wordStart + 4], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        const y = interpolate(frame, [wordStart, wordStart + 5], [12, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        return (
          <span
            key={i}
            style={{
              opacity,
              display: 'inline-block',
              transform: `translateY(${y}px)`,
              marginRight: 12,
            }}
          >
            {word}
          </span>
        );
      })}
    </span>
  );
};

export const TipBody: React.FC<TipBodyProps> = ({teach, why, petType, teachDurationFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const accent = ACCENT[petType];
  const bg2 = BG2[petType];

  const fadeIn = interpolate(frame, [0, 12], [0, 1], {extrapolateRight: 'clamp'});
  const slideY = interpolate(frame, [0, 15], [40, 0], {extrapolateRight: 'clamp'});

  const isWhySection = frame >= teachDurationFrames;

  const totalFrames = teachDurationFrames + fps * 5;
  const progress = interpolate(frame, [0, totalFrames], [0, 100], {extrapolateRight: 'clamp'});

  const teachWords = teach.split(' ').length;
  const teachFramesPerWord = Math.max(2, Math.floor((teachDurationFrames - 20) / teachWords));

  const whyWords = why.split(' ').length;
  const whyFramesPerWord = Math.max(2, Math.floor((fps * 4) / whyWords));

  const whyFadeIn = interpolate(
    frame,
    [teachDurationFrames, teachDurationFrames + 15],
    [0, 1],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const teachFadeOut = interpolate(
    frame,
    [teachDurationFrames - 10, teachDurationFrames],
    [1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

  const glowPulse = 0.3 + Math.sin(frame * 0.08) * 0.15;

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(180deg, #1A1A2E 0%, ${bg2} 100%)`,
        padding: 64,
        justifyContent: 'center',
        opacity: fadeIn,
        transform: `translateY(${slideY}px)`,
      }}
    >
      {/* Progress bar */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: `${progress}%`,
          height: 6,
          backgroundColor: accent,
          boxShadow: `0 0 12px ${accent}`,
          borderRadius: '0 3px 3px 0',
        }}
      />

      {/* Accent bar */}
      <div
        style={{
          width: 8,
          height: 60,
          backgroundColor: accent,
          borderRadius: 4,
          marginBottom: 32,
          boxShadow: `0 0 ${12 + glowPulse * 20}px ${accent}`,
        }}
      />

      {!isWhySection && (
        <div
          style={{
            fontSize: 50,
            color: '#F0F0F0',
            lineHeight: 1.6,
            fontFamily: 'Arial, sans-serif',
            fontWeight: 500,
            opacity: teachFadeOut,
          }}
        >
          <WordReveal text={teach} startFrame={10} framesPerWord={teachFramesPerWord} />
        </div>
      )}

      {isWhySection && (
        <div style={{opacity: whyFadeIn}}>
          <div
            style={{
              fontSize: 34,
              color: accent,
              fontWeight: 700,
              fontFamily: 'Arial Black, Arial, sans-serif',
              textTransform: 'uppercase',
              letterSpacing: 4,
              marginBottom: 24,
            }}
          >
            ⚡ Why it matters
          </div>
          <div
            style={{
              fontSize: 48,
              color: '#F0F0F0',
              lineHeight: 1.55,
              fontFamily: 'Arial, sans-serif',
              fontWeight: 500,
            }}
          >
            <WordReveal text={why} startFrame={teachDurationFrames + 8} framesPerWord={whyFramesPerWord} />
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};
