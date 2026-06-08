import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame} from 'remotion';

type Props = {
  src: string;
  durationInFrames: number;
  direction?: 'zoom-in' | 'zoom-out' | 'pan-left' | 'pan-right';
};

export const SceneImage: React.FC<Props> = ({
  src,
  durationInFrames,
  direction = 'zoom-in',
}) => {
  const frame = useCurrentFrame();

  let transform = '';

  if (direction === 'zoom-in') {
    const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.18], {
      extrapolateRight: 'clamp',
    });
    transform = `scale(${scale})`;
  } else if (direction === 'zoom-out') {
    const scale = interpolate(frame, [0, durationInFrames], [1.18, 1.0], {
      extrapolateRight: 'clamp',
    });
    transform = `scale(${scale})`;
  } else if (direction === 'pan-left') {
    const x = interpolate(frame, [0, durationInFrames], [3, -3], {
      extrapolateRight: 'clamp',
    });
    transform = `scale(1.12) translateX(${x}%)`;
  } else if (direction === 'pan-right') {
    const x = interpolate(frame, [0, durationInFrames], [-3, 3], {
      extrapolateRight: 'clamp',
    });
    transform = `scale(1.12) translateX(${x}%)`;
  }

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      <Img
        src={staticFile(src)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform,
        }}
      />
    </AbsoluteFill>
  );
};
