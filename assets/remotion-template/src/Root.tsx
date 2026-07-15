import React from 'react';
import {Composition} from 'remotion';
import {V4Composition} from './V4Composition';
import {visualScript} from './generatedVisualScript';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="NGGKouboV4Portrait"
      component={V4Composition}
      durationInFrames={visualScript.composition.durationFrames}
      fps={visualScript.composition.fps}
      width={visualScript.composition.width}
      height={visualScript.composition.height}
      defaultProps={{visualScript}}
      calculateMetadata={({props}) => ({
        durationInFrames: props.visualScript.composition.durationFrames,
        fps: props.visualScript.composition.fps,
        width: props.visualScript.composition.width,
        height: props.visualScript.composition.height,
      })}
    />
  );
};
