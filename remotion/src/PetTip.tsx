import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Sequence,
  staticFile,
  useVideoConfig,
} from 'remotion';
import {HookCard} from './components/HookCard';
import {TipBody} from './components/TipBody';
import {CTACard} from './components/CTACard';

export type PetTipProps = {
  petType: 'dog' | 'cat';
  hook: string;
  teach: string;
  why: string;
  cta: string;
  audioSrc: string;
};

export const PetTip: React.FC<PetTipProps> = ({
  petType,
  hook,
  teach,
  why,
  cta,
  audioSrc,
}) => {
  const {fps} = useVideoConfig();

  const hookDuration = fps * 3;      // 0–3s   (90 frames)
  const teachStart = hookDuration;
  const teachDuration = fps * 17;    // 3–20s  (510 frames)
  const whyStart = teachStart + teachDuration;
  const whyDuration = fps * 5;       // 20–25s (150 frames)
  const ctaStart = whyStart + whyDuration;
  const ctaDuration = fps * 5;       // 25–30s (150 frames)

  return (
    <AbsoluteFill style={{backgroundColor: '#0D0D0D'}}>
      {audioSrc ? (
        <Audio src={staticFile(audioSrc)} />
      ) : null}

      <Sequence from={0} durationInFrames={hookDuration}>
        <HookCard hook={hook} petType={petType} />
      </Sequence>

      <Sequence from={teachStart} durationInFrames={teachDuration + whyDuration}>
        <TipBody teach={teach} why={why} petType={petType} teachDurationFrames={teachDuration} />
      </Sequence>

      <Sequence from={ctaStart} durationInFrames={ctaDuration}>
        <CTACard cta={cta} petType={petType} />
      </Sequence>
    </AbsoluteFill>
  );
};
