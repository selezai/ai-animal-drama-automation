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

export type PetTipProps = {
  petType: 'dog' | 'cat';
  hook: string;
  teach: string;
  why: string;
  cta: string;
  audioSrc: string;
  pillar?: string;
  scenes?: string[];
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
}) => {
  const {fps, durationInFrames} = useVideoConfig();
  const frame = useCurrentFrame();
  const accent = ACCENT[petType];

  const FADE = 8;

  const sceneDurations = [
    fps * 5,
    fps * 12,
    fps * 8,
    fps * 5,
  ];
  const sceneStarts = [0, sceneDurations[0], sceneDurations[0] + sceneDurations[1], sceneDurations[0] + sceneDurations[1] + sceneDurations[2]];

  const captions = [hook, teach, why, cta];

  const progress = interpolate(frame, [0, durationInFrames], [0, 100], {
    extrapolateRight: 'clamp',
  });

  let activeScene = 0;
  for (let i = sceneStarts.length - 1; i >= 0; i--) {
    if (frame >= sceneStarts[i]) {
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

        const sceneOpacity = interpolate(
          frame,
          [start, start + FADE, start + dur - FADE, start + dur],
          [0, 1, 1, i < scenes.length - 1 ? 0 : 1],
          {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
        );

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

      {/* TikTok-style captions — one per scene */}
      {captions.map((text, i) => {
        const start = sceneStarts[i];
        const dur = sceneDurations[i];
        return (
          <Sequence key={`cap-${i}`} from={start} durationInFrames={dur}>
            <TikTokCaption text={text} accentColor={accent} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
