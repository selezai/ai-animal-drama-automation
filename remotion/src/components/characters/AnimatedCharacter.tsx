import React from 'react';
import {AnimatedDog, DogMood} from './AnimatedDog';
import {AnimatedCat, CatMood} from './AnimatedCat';

export type CharacterMood = 'alert' | 'attentive' | 'concerned' | 'excited';

type Props = {
  petType: 'dog' | 'cat';
  mood: CharacterMood;
  size?: number;
};

export const PILLAR_MOOD_MAP: Record<string, CharacterMood> = {
  safety: 'alert',
  health: 'concerned',
  behaviour: 'attentive',
  training: 'attentive',
  nutrition: 'attentive',
  fun_facts: 'excited',
};

export const SECTION_MOOD_MAP: Record<string, CharacterMood> = {
  hook: 'alert',
  teach: 'attentive',
  why: 'concerned',
  cta: 'excited',
};

export const AnimatedCharacter: React.FC<Props> = ({petType, mood, size = 400}) => {
  if (petType === 'cat') {
    return <AnimatedCat mood={mood as CatMood} size={size} />;
  }
  return <AnimatedDog mood={mood as DogMood} size={size} />;
};
