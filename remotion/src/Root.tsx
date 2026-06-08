import React from 'react';
import {Composition} from 'remotion';
import {PetTip, PetTipProps} from './PetTip';

export const Root: React.FC = () => {
  const defaultProps: PetTipProps = {
    petType: 'dog',
    hook: "Never give your dog grapes — it could be fatal",
    teach: "Grapes and raisins contain a toxic compound that causes acute kidney failure in dogs. Even a single grape can be deadly — there is no safe amount.",
    why: "Signs of poisoning appear within hours: vomiting, lethargy, loss of appetite. Without treatment, kidney failure can occur within 48 hours.",
    cta: "Follow for daily pet tips",
    audioSrc: '',
    pillar: 'safety',
    scenes: [],
    wordTimestamps: [],
  };

  return (
    <Composition
      id="PetTip"
      component={PetTip}
      durationInFrames={900}
      fps={30}
      width={1080}
      height={1920}
      defaultProps={defaultProps}
    />
  );
};
