import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

export type DogMood = 'alert' | 'attentive' | 'concerned' | 'excited';

type Props = {
  mood: DogMood;
  size?: number;
};

export const AnimatedDog: React.FC<Props> = ({mood, size = 500}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Body bob — continuous gentle bounce
  const bodyBob = Math.sin(frame * 0.08) * (mood === 'excited' ? 12 : 5);

  // Tail wag — faster when excited
  const tailSpeed = mood === 'excited' ? 0.35 : mood === 'alert' ? 0.15 : 0.2;
  const tailWag = Math.sin(frame * tailSpeed) * (mood === 'excited' ? 35 : 18);

  // Ear flop
  const earFlop = Math.sin(frame * 0.12) * (mood === 'alert' ? 3 : 8);

  // Eye expression
  const eyeScale = mood === 'alert' ? 1.3 : mood === 'concerned' ? 0.8 : 1.0;
  const eyeY = mood === 'concerned' ? 2 : 0;

  // Mouth
  const mouthCurve = mood === 'excited' ? 8 : mood === 'concerned' ? -5 : 3;

  // Tongue (only when excited or attentive)
  const showTongue = mood === 'excited' || mood === 'attentive';
  const tongueWag = Math.sin(frame * 0.18) * 3;

  // Breathing (body scale)
  const breathe = 1 + Math.sin(frame * 0.06) * 0.015;

  // Bounce entrance
  const entrance = spring({fps, frame, config: {damping: 12, stiffness: 100, mass: 0.8}});

  // Head tilt for alert/attentive
  const headTilt = mood === 'alert'
    ? Math.sin(frame * 0.05) * 5
    : mood === 'attentive'
      ? Math.sin(frame * 0.04) * 3
      : 0;

  // Paw lift when excited
  const pawLift = mood === 'excited' ? Math.abs(Math.sin(frame * 0.15)) * 8 : 0;

  const s = size / 500;

  return (
    <div
      style={{
        width: size,
        height: size,
        transform: `scale(${entrance}) translateY(${bodyBob}px)`,
        position: 'relative',
      }}
    >
      <svg
        viewBox="0 0 500 500"
        width={size}
        height={size}
        style={{overflow: 'visible'}}
      >
        {/* Shadow */}
        <ellipse
          cx={250}
          cy={440}
          rx={100}
          ry={20}
          fill="rgba(0,0,0,0.15)"
          style={{
            transform: `scaleX(${1 + Math.sin(frame * 0.08) * 0.05})`,
            transformOrigin: '250px 440px',
          }}
        />

        {/* Tail */}
        <g style={{
          transform: `rotate(${tailWag}deg)`,
          transformOrigin: '320px 300px',
        }}>
          <path
            d="M320,300 Q360,250 380,200 Q390,180 375,190 Q350,220 310,290"
            fill="#C68642"
            stroke="#A0522D"
            strokeWidth={2}
          />
        </g>

        {/* Body */}
        <g style={{
          transform: `scale(${breathe})`,
          transformOrigin: '250px 350px',
        }}>
          <ellipse cx={250} cy={330} rx={110} ry={80} fill="#DEB887" />
          <ellipse cx={250} cy={340} rx={90} ry={60} fill="#F5DEB3" />
        </g>

        {/* Back legs */}
        <rect x={170} y={380} width={35} height={55} rx={14} fill="#DEB887" />
        <rect x={295} y={380} width={35} height={55} rx={14} fill="#DEB887" />

        {/* Front legs */}
        <g style={{transform: `translateY(${-pawLift}px)`}}>
          <rect x={195} y={380} width={32} height={58} rx={14} fill="#DEB887" />
          <ellipse cx={211} cy={438} rx={18} ry={10} fill="#C68642" />
        </g>
        <g style={{transform: `translateY(${-pawLift * 0.7}px)`}}>
          <rect x={273} y={380} width={32} height={58} rx={14} fill="#DEB887" />
          <ellipse cx={289} cy={438} rx={18} ry={10} fill="#C68642" />
        </g>

        {/* Paws (back) */}
        <ellipse cx={187} cy={435} rx={20} ry={10} fill="#C68642" />
        <ellipse cx={313} cy={435} rx={20} ry={10} fill="#C68642" />

        {/* Head group */}
        <g style={{
          transform: `rotate(${headTilt}deg) translateY(${bodyBob * 0.3}px)`,
          transformOrigin: '250px 220px',
        }}>
          {/* Head */}
          <ellipse cx={250} cy={210} rx={85} ry={80} fill="#DEB887" />

          {/* Snout */}
          <ellipse cx={250} cy={250} rx={45} ry={32} fill="#F5DEB3" />

          {/* Nose */}
          <ellipse cx={250} cy={240} rx={14} ry={10} fill="#333" />
          <ellipse cx={247} cy={237} rx={4} ry={3} fill="#666" />

          {/* Eyes */}
          <g style={{transform: `scale(1, ${eyeScale}) translate(0, ${eyeY}px)`}}>
            <ellipse cx={220} cy={200} rx={14} ry={16} fill="white" />
            <ellipse cx={280} cy={200} rx={14} ry={16} fill="white" />
            <ellipse cx={222} cy={202} rx={8} ry={9} fill="#4A3728" />
            <ellipse cx={278} cy={202} rx={8} ry={9} fill="#4A3728" />
            <ellipse cx={224} cy={199} rx={3} ry={3.5} fill="white" />
            <ellipse cx={280} cy={199} rx={3} ry={3.5} fill="white" />
          </g>

          {/* Eyebrows */}
          {mood === 'concerned' && (
            <>
              <line x1={205} y1={182} x2={232} y2={178} stroke="#A0522D" strokeWidth={4} strokeLinecap="round" />
              <line x1={268} y1={178} x2={295} y2={182} stroke="#A0522D" strokeWidth={4} strokeLinecap="round" />
            </>
          )}
          {mood === 'alert' && (
            <>
              <line x1={208} y1={178} x2={232} y2={183} stroke="#A0522D" strokeWidth={4} strokeLinecap="round" />
              <line x1={268} y1={183} x2={292} y2={178} stroke="#A0522D" strokeWidth={4} strokeLinecap="round" />
            </>
          )}

          {/* Mouth */}
          <path
            d={`M230,258 Q250,${258 + mouthCurve} 270,258`}
            fill="none"
            stroke="#A0522D"
            strokeWidth={3}
            strokeLinecap="round"
          />

          {/* Tongue */}
          {showTongue && (
            <g style={{transform: `translateX(${tongueWag}px)`}}>
              <ellipse cx={252} cy={272} rx={10} ry={14} fill="#FF6B8A" />
              <line x1={252} y1={262} x2={252} y2={282} stroke="#E55A7A" strokeWidth={1.5} />
            </g>
          )}

          {/* Ears */}
          <g style={{
            transform: `rotate(${-earFlop}deg)`,
            transformOrigin: '185px 170px',
          }}>
            <ellipse cx={175} cy={155} rx={35} ry={50} fill="#C68642"
              style={{transform: 'rotate(-15deg)', transformOrigin: '175px 155px'}} />
          </g>
          <g style={{
            transform: `rotate(${earFlop}deg)`,
            transformOrigin: '315px 170px',
          }}>
            <ellipse cx={325} cy={155} rx={35} ry={50} fill="#C68642"
              style={{transform: 'rotate(15deg)', transformOrigin: '325px 155px'}} />
          </g>

          {/* Collar */}
          <path
            d="M190,270 Q250,295 310,270"
            fill="none"
            stroke="#E84545"
            strokeWidth={8}
            strokeLinecap="round"
          />
          <circle cx={250} cy={285} r={8} fill="#FFD700" />
        </g>
      </svg>
    </div>
  );
};
