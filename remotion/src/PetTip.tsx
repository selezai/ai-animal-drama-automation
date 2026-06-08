import React from 'react';
import {
  AbsoluteFill,
  Audio,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
} from 'remotion';
import {AnimatedCharacter, CharacterMood} from './components/characters/AnimatedCharacter';
import {CaptionOverlay} from './components/CaptionOverlay';

export type PetTipProps = {
  petType: 'dog' | 'cat';
  hook: string;
  teach: string;
  why: string;
  cta: string;
  audioSrc: string;
  pillar?: string;
};

const BG = {
  dog: {from: '#FF6B35', via: '#E84545', to: '#1A1A2E'},
  cat: {from: '#9333EA', via: '#6C3FC5', to: '#1A1A2E'},
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
  const frame = useCurrentFrame();

  const hookDuration = fps * 3;
  const teachStart = hookDuration;
  const teachDuration = fps * 17;
  const whyStart = teachStart + teachDuration;
  const whyDuration = fps * 5;
  const ctaStart = whyStart + whyDuration;
  const ctaDuration = fps * 5;
  const totalFrames = hookDuration + teachDuration + whyDuration + ctaDuration;

  const bg = BG[petType];
  const gradientAngle = 150 + Math.sin(frame * 0.02) * 20;

  const progress = interpolate(frame, [0, totalFrames], [0, 100], {extrapolateRight: 'clamp'});

  let currentMood: CharacterMood = 'alert';
  let currentCaption = hook;
  let sectionLabel = '';

  if (frame < hookDuration) {
    currentMood = 'alert';
    currentCaption = hook;
    sectionLabel = '';
  } else if (frame < whyStart) {
    currentMood = 'attentive';
    currentCaption = teach;
    sectionLabel = '💡 DID YOU KNOW';
  } else if (frame < ctaStart) {
    currentMood = 'concerned';
    currentCaption = why;
    sectionLabel = '⚡ WHY IT MATTERS';
  } else {
    currentMood = 'excited';
    currentCaption = cta;
    sectionLabel = '';
  }

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(${gradientAngle}deg, ${bg.from} 0%, ${bg.via} 50%, ${bg.to} 100%)`,
      }}
    >
      {audioSrc ? <Audio src={staticFile(audioSrc)} /> : null}

      {/* Progress bar at top */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: `${progress}%`,
          height: 10,
          backgroundColor: 'rgba(255,255,255,0.8)',
          boxShadow: '0 0 16px rgba(255,255,255,0.5)',
          zIndex: 10,
        }}
      />

      {/* Character — centre stage */}
      <div
        style={{
          position: 'absolute',
          top: '8%',
          left: '50%',
          transform: 'translateX(-50%)',
          zIndex: 5,
        }}
      >
        <AnimatedCharacter petType={petType} mood={currentMood} size={420} />
      </div>

      {/* Section label */}
      {sectionLabel && (
        <div
          style={{
            position: 'absolute',
            top: '55%',
            width: '100%',
            textAlign: 'center',
            zIndex: 6,
          }}
        >
          <span
            style={{
              fontSize: 36,
              fontWeight: 800,
              color: petType === 'dog' ? '#FFBE76' : '#C4B5FD',
              fontFamily: 'Arial Black, Arial, sans-serif',
              textTransform: 'uppercase',
              letterSpacing: 6,
              textShadow: '0 2px 12px rgba(0,0,0,0.6)',
            }}
          >
            {sectionLabel}
          </span>
        </div>
      )}

      {/* Caption overlay at bottom */}
      <CaptionOverlay
        text={currentCaption}
        petType={petType}
        isHook={frame < hookDuration}
        isCta={frame >= ctaStart}
      />
    </AbsoluteFill>
  );
};
