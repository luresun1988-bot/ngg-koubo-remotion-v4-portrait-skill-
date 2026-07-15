import React from 'react';
import {Audio, Sequence, interpolate, staticFile} from 'remotion';
import type {AudioCue, PresenterAudio, VisualScript} from './v4Types';

export type PresenterAudioTiming = {
  sequenceStartFrame: number;
  trimBeforeFrames: number;
  durationInFrames: number;
};

export const presenterAudioTimingFor = (
  syncOffsetFrames: number,
  compositionDuration: number,
): PresenterAudioTiming => {
  const safeDuration = Math.max(1, Math.trunc(compositionDuration));
  const finiteOffset = Number.isFinite(syncOffsetFrames) ? Math.trunc(syncOffsetFrames) : 0;
  const boundedOffset = Math.max(-(safeDuration - 1), Math.min(safeDuration - 1, finiteOffset));
  const sequenceStartFrame = Math.max(0, boundedOffset);
  const trimBeforeFrames = Math.max(0, -boundedOffset);

  return {
    sequenceStartFrame,
    trimBeforeFrames,
    durationInFrames: Math.max(1, safeDuration - sequenceStartFrame),
  };
};

export const dbToVolume = (volumeDb: number): number => Math.pow(10, volumeDb / 20);

const PresenterAudioLayer: React.FC<{
  config?: PresenterAudio;
  compositionDuration: number;
}> = ({config, compositionDuration}) => {
  if (config?.mode !== 'normalized-wav' || !config.path) return null;

  const timing = presenterAudioTimingFor(config.syncOffsetFrames ?? 0, compositionDuration);

  return (
    <Sequence
      from={timing.sequenceStartFrame}
      durationInFrames={timing.durationInFrames}
      name="Presenter audio"
    >
      <Audio
        src={staticFile(config.path.replaceAll('\\', '/'))}
        trimBefore={timing.trimBeforeFrames || undefined}
        volume={dbToVolume(config.volumeDb ?? 0)}
        name="Normalized presenter narration"
      />
    </Sequence>
  );
};

const defaultCueDb = (cue: AudioCue, schemaVersion: string): number => {
  const portrait = schemaVersion.includes('portrait');
  if (cue.type === 'bgm') return portrait ? -30 : -24;
  if (cue.type === 'sfx') return portrait ? -23 : -18;
  return 0;
};

const cueVolume = (
  cue: AudioCue,
  localFrame: number,
  duration: number,
  schemaVersion: string,
): number => {
  const base = dbToVolume(cue.volumeDb ?? defaultCueDb(cue, schemaVersion));
  const fadeInFrames = Math.max(0, cue.fadeInFrames ?? 0);
  const fadeOutFrames = Math.max(0, cue.fadeOutFrames ?? 0);
  const fadeIn =
    fadeInFrames > 0
      ? interpolate(localFrame, [0, fadeInFrames], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : 1;
  const fadeOut =
    fadeOutFrames > 0
      ? interpolate(localFrame, [Math.max(0, duration - fadeOutFrames), duration], [1, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        })
      : 1;

  return base * fadeIn * fadeOut;
};

export const audioCueDuration = (cue: AudioCue, compositionDuration: number): number => {
  const startFrame = cue.startFrame ?? 0;
  if (typeof cue.durationFrames === 'number' && cue.durationFrames > 0) return cue.durationFrames;
  if (typeof cue.endFrame === 'number' && cue.endFrame > startFrame) return cue.endFrame - startFrame;
  if (cue.type === 'sfx') return 18;
  return Math.max(1, compositionDuration - startFrame);
};

export const shouldRenderAudioCue = (cue: AudioCue): boolean => {
  if (cue.type === 'source' || cue.type === 'silence') return false;
  if (
    cue.status === 'pending-selection' ||
    cue.status === 'pending-generation' ||
    cue.status === 'suggested'
  ) {
    return false;
  }
  if (cue.status === 'disabled' || cue.status === 'muted') return false;
  return Boolean(cue.path);
};

const AudioCueLayer: React.FC<{
  cue: AudioCue;
  compositionDuration: number;
  schemaVersion: string;
}> = ({cue, compositionDuration, schemaVersion}) => {
  if (!shouldRenderAudioCue(cue)) return null;

  const startFrame = cue.startFrame ?? 0;
  const duration = audioCueDuration(cue, compositionDuration);

  return (
    <Sequence from={startFrame} durationInFrames={duration}>
      <Audio
        src={staticFile(cue.path ?? '')}
        loop={cue.loop}
        volume={(frame) => cueVolume(cue, frame, duration, schemaVersion)}
      />
    </Sequence>
  );
};

export const V4AudioLayers: React.FC<{visualScript: VisualScript}> = ({visualScript}) => (
  <>
    <PresenterAudioLayer
      config={visualScript.presenterAudio}
      compositionDuration={visualScript.composition.durationFrames}
    />
    {visualScript.audioCues.map((cue) => (
      <AudioCueLayer
        key={cue.id}
        cue={cue}
        compositionDuration={visualScript.composition.durationFrames}
        schemaVersion={visualScript.schemaVersion}
      />
    ))}
  </>
);

