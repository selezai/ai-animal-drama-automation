import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

export type CatMood = 'alert' | 'attentive' | 'concerned' | 'excited';

type Props = {
  mood: CatMood;
  size?: number;
};

export const AnimatedCat: React.FC<Props> = ({mood, size = 500}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  // Body sway — cats are more fluid
  const bodySway = Math.sin(frame * 0.06) * (mood === 'excited' ? 8 : 3);

  // Tail — S-curve motion
  const tailBase = Math.sin(frame * 0.1) * (mood === 'excited' ? 30 : 12);
  const tailTip = Math.sin(frame * 0.15 + 1) * (mood === 'excited' ? 40 : 18);

  // Ear twitch
  const leftEarTwitch = Math.sin(frame * 0.2) * (mood === 'alert' ? 8 : 3);
  const rightEarTwitch = Math.sin(frame * 0.17 + 0.5) * (mood === 'alert' ? 8 : 3);

  // Eye expression
  const eyeHeight = mood === 'alert' ? 18 : mood === 'concerned' ? 10 : mood === 'excited' ? 16 : 14;
  const pupilSize = mood === 'alert' ? 10 : mood === 'excited' ? 8 : 7;

  // Blink (every ~3 seconds)
  const blinkCycle = frame % 90;
  const blink = blinkCycle < 3 ? interpolate(blinkCycle, [0, 1.5, 3], [1, 0.1, 1]) : 1;

  // Whisker twitch
  const whiskerTwitch = Math.sin(frame * 0.12) * 4;

  // Purr vibration when attentive
  const purr = mood === 'attentive' ? Math.sin(frame * 0.8) * 1 : 0;

  // Breathing
  const breathe = 1 + Math.sin(frame * 0.05) * 0.012;

  // Entrance
  const entrance = spring({fps, frame, config: {damping: 14, stiffness: 90, mass: 0.7}});

  // Head movement
  const headTilt = mood === 'alert'
    ? Math.sin(frame * 0.04) * 6
    : mood === 'attentive'
      ? Math.sin(frame * 0.03) * 4
      : 0;

  // Paw knead when excited
  const leftPawKnead = mood === 'excited' ? Math.abs(Math.sin(frame * 0.2)) * 6 : 0;
  const rightPawKnead = mood === 'excited' ? Math.abs(Math.sin(frame * 0.2 + Math.PI)) * 6 : 0;

  return (
    <div
      style={{
        width: size,
        height: size,
        transform: `scale(${entrance}) translateY(${bodySway}px) translateX(${purr}px)`,
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
          rx={90}
          ry={18}
          fill="rgba(0,0,0,0.12)"
        />

        {/* Tail */}
        <path
          d={`M330,340 Q${370 + tailBase},${300} ${380 + tailTip},${230} Q${385 + tailTip},${210} ${370 + tailBase * 0.5},${220}`}
          fill="none"
          stroke="#808080"
          strokeWidth={14}
          strokeLinecap="round"
        />
        <path
          d={`M330,340 Q${370 + tailBase},${300} ${380 + tailTip},${230} Q${385 + tailTip},${210} ${370 + tailBase * 0.5},${220}`}
          fill="none"
          stroke="#A9A9A9"
          strokeWidth={10}
          strokeLinecap="round"
        />

        {/* Body */}
        <g style={{
          transform: `scale(${breathe})`,
          transformOrigin: '250px 350px',
        }}>
          <ellipse cx={250} cy={340} rx={100} ry={75} fill="#A9A9A9" />
          <ellipse cx={250} cy={350} rx={80} ry={55} fill="#C0C0C0" />
        </g>

        {/* Back legs */}
        <ellipse cx={175} cy={410} rx={28} ry={22} fill="#A9A9A9" />
        <ellipse cx={325} cy={410} rx={28} ry={22} fill="#A9A9A9" />

        {/* Front legs */}
        <g style={{transform: `translateY(${-leftPawKnead}px)`}}>
          <rect x={200} y={385} width={28} height={52} rx={12} fill="#A9A9A9" />
          <ellipse cx={214} cy={437} rx={16} ry={9} fill="#C0C0C0" />
        </g>
        <g style={{transform: `translateY(${-rightPawKnead}px)`}}>
          <rect x={272} y={385} width={28} height={52} rx={12} fill="#A9A9A9" />
          <ellipse cx={286} cy={437} rx={16} ry={9} fill="#C0C0C0" />
        </g>

        {/* Paw pads */}
        <ellipse cx={175} cy={430} rx={18} ry={9} fill="#C0C0C0" />
        <ellipse cx={325} cy={430} rx={18} ry={9} fill="#C0C0C0" />

        {/* Head group */}
        <g style={{
          transform: `rotate(${headTilt}deg) translateY(${bodySway * 0.4}px)`,
          transformOrigin: '250px 230px',
        }}>
          {/* Head */}
          <ellipse cx={250} cy={220} rx={80} ry={72} fill="#A9A9A9" />

          {/* Inner face */}
          <ellipse cx={250} cy={230} rx={60} ry={50} fill="#C0C0C0" />

          {/* Ears */}
          <g style={{transform: `rotate(${-leftEarTwitch}deg)`, transformOrigin: '195px 165px'}}>
            <polygon points="195,165 165,100 220,140" fill="#A9A9A9" />
            <polygon points="197,162 175,115 215,145" fill="#FFB6C1" />
          </g>
          <g style={{transform: `rotate(${rightEarTwitch}deg)`, transformOrigin: '305px 165px'}}>
            <polygon points="305,165 335,100 280,140" fill="#A9A9A9" />
            <polygon points="303,162 325,115 285,145" fill="#FFB6C1" />
          </g>

          {/* Eyes */}
          <g style={{transform: `scaleY(${blink})`, transformOrigin: '220px 210px'}}>
            <ellipse cx={220} cy={210} rx={16} ry={eyeHeight} fill="#90EE90" />
            <ellipse cx={220} cy={210} rx={pupilSize} ry={eyeHeight - 2} fill="#222" />
            <ellipse cx={216} cy={205} rx={4} ry={5} fill="rgba(255,255,255,0.5)" />
          </g>
          <g style={{transform: `scaleY(${blink})`, transformOrigin: '280px 210px'}}>
            <ellipse cx={280} cy={210} rx={16} ry={eyeHeight} fill="#90EE90" />
            <ellipse cx={280} cy={210} rx={pupilSize} ry={eyeHeight - 2} fill="#222" />
            <ellipse cx={276} cy={205} rx={4} ry={5} fill="rgba(255,255,255,0.5)" />
          </g>

          {/* Nose */}
          <polygon points="250,242 244,250 256,250" fill="#FFB6C1" />

          {/* Mouth */}
          <path
            d={`M240,255 Q250,${mood === 'excited' ? 262 : mood === 'concerned' ? 252 : 258} 260,255`}
            fill="none"
            stroke="#888"
            strokeWidth={2.5}
            strokeLinecap="round"
          />

          {/* Whiskers */}
          <g style={{transform: `rotate(${whiskerTwitch}deg)`, transformOrigin: '250px 250px'}}>
            <line x1={180} y1={240} x2={228} y2={248} stroke="#DDD" strokeWidth={2} />
            <line x1={175} y1={252} x2={226} y2={252} stroke="#DDD" strokeWidth={2} />
            <line x1={180} y1={264} x2={228} y2={256} stroke="#DDD" strokeWidth={2} />
            <line x1={320} y1={240} x2={272} y2={248} stroke="#DDD" strokeWidth={2} />
            <line x1={325} y1={252} x2={274} y2={252} stroke="#DDD" strokeWidth={2} />
            <line x1={320} y1={264} x2={272} y2={256} stroke="#DDD" strokeWidth={2} />
          </g>

          {/* Collar */}
          <path
            d="M195,275 Q250,298 305,275"
            fill="none"
            stroke="#6C3FC5"
            strokeWidth={7}
            strokeLinecap="round"
          />
          <circle cx={250} cy={290} r={7} fill="#C4B5FD" />
        </g>
      </svg>
    </div>
  );
};
