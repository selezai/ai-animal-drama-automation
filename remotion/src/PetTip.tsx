import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from 'remotion';
import {SceneImage} from './components/SceneImage';
import {TikTokCaption} from './components/TikTokCaption';

export type WordTimestamp = {word: string; start: number; end: number};

export type PetTipProps = {
  petType: 'dog' | 'cat';
  hook: string;
  teach: string;
  why: string;
  cta: string;
  audioSrc: string;
  pillar?: string;
  scenes?: string[];
  wordTimestamps?: WordTimestamp[];
  audioDurationSecs?: number;
  sceneBoundaries?: number[]; // start time in seconds for each of the 4 sections
};

const ACCENT = {dog: '#FFD700', cat: '#C4B5FD'};
const DIRECTIONS: Array<'zoom-in' | 'zoom-out' | 'pan-left' | 'pan-right'> = [
  'zoom-in',
  'pan-right',
  'zoom-out',
  'pan-left',
];

export const PetTip: React.FC<PetTipProps> = ({
  petType,
  hook,
  teach,
  why,
  cta,
  audioSrc,
  scenes = [],
  wordTimestamps = [],
  audioDurationSecs = 30,
  sceneBoundaries = [],
}) => {
  const {fps, durationInFrames} = useVideoConfig();
  const frame = useCurrentFrame();
  const accent = ACCENT[petType];

  const FADE = 8;

  // Convert scene boundary seconds → frames, falling back to even split
  const totalFrames = durationInFrames;
  let boundaries: number[] = sceneBoundaries.length === 4
    ? sceneBoundaries.map(s => Math.round(s * fps))
    : [0, Math.round(totalFrames * 0.10), Math.round(totalFrames * 0.57), Math.round(totalFrames * 0.83)];

  // Guarantee strictly increasing (rounding can create duplicates)
  for (let i = 1; i < boundaries.length; i++) {
    if (boundaries[i] <= boundaries[i - 1]) {
      boundaries[i] = boundaries[i - 1] + 1;
    }
  }

  const sceneStarts = boundaries;
  const sceneDurations = [
    boundaries[1] - boundaries[0],
    boundaries[2] - boundaries[1],
    boundaries[3] - boundaries[2],
    totalFrames - boundaries[3],
  ];

  const captions = [hook, teach, why, cta];

  const progress = interpolate(frame, [0, durationInFrames], [0, 100], {
    extrapolateRight: 'clamp',
  });

  let activeScene = 0;
  for (let i = sceneStarts.length - 1; i >= 0; i--) {
    if (frame >= sceneStarts[i] && sceneDurations[i] > 0) {
      activeScene = i;
      break;
    }
  }

  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      {audioSrc ? <Audio src={staticFile(audioSrc)} /> : null}

      {scenes.map((src, i) => {
        if (!src) return null;
        const start = sceneStarts[i];
        const dur = sceneDurations[i];

        const isFirst = i === 0;
        const isLast = i === scenes.length - 1;
        const maxFade = Math.max(1, Math.floor(dur / 3));
        const fadeIn = isFirst ? 0 : Math.min(FADE, maxFade);
        const fadeOut = isLast ? 0 : Math.min(FADE, maxFade);

        let sceneOpacity = 1;
        if (fadeIn > 0 && fadeOut > 0) {
          sceneOpacity = interpolate(frame,
            [start, start + fadeIn, start + dur - fadeOut, start + dur],
            [0, 1, 1, 0],
            {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        } else if (fadeIn > 0) {
          sceneOpacity = interpolate(frame,
            [start, start + fadeIn],
            [0, 1],
            {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        } else if (fadeOut > 0) {
          sceneOpacity = interpolate(frame,
            [start + dur - fadeOut, start + dur],
            [1, 0],
            {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        }

        return (
          <Sequence key={i} from={start} durationInFrames={dur}>
            <AbsoluteFill style={{opacity: sceneOpacity}}>
              <SceneImage
                src={src}
                durationInFrames={dur}
                direction={DIRECTIONS[i % DIRECTIONS.length]}
              />
            </AbsoluteFill>
          </Sequence>
        );
      })}

      {/* Dark gradient overlay at bottom for caption readability */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: '45%',
          background: 'linear-gradient(transparent 0%, rgba(0,0,0,0.75) 60%, rgba(0,0,0,0.9) 100%)',
          zIndex: 5,
        }}
      />

      {/* Progress bar */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: `${progress}%`,
          height: 8,
          backgroundColor: accent,
          boxShadow: `0 0 12px ${accent}`,
          zIndex: 20,
        }}
      />

      {/* TikTok-style captions — word-level sync per scene */}
      {captions.map((text, i) => {
        const start = sceneStarts[i];
        const dur = sceneDurations[i];
        const sceneStartSec = start / fps;
        const sceneEndSec = (start + dur) / fps;
        const sceneWords = wordTimestamps.length > 0
          ? wordTimestamps.filter(w => w.end > sceneStartSec && w.start < sceneEndSec)
          : [];
        return (
          <Sequence key={`cap-${i}`} from={start} durationInFrames={dur}>
            <TikTokCaption
              text={text}
              accentColor={accent}
              wordTimestamps={sceneWords}
              sceneStartSec={sceneStartSec}
            />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
