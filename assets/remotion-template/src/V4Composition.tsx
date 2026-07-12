import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Easing,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {
  AutomationHandoffPanel,
  CapabilitySharePanel,
  ClaimStrip,
  CornerChapterLabel,
  DataPunch,
  DepthKeywordLayer,
  FlowListPanel,
  InfoCard,
  KineticTitle,
  MaterialBoard,
  PlatformFanOutPanel,
  RatioGallery,
  SceneLockGridPanel,
  SemanticProblemMap,
  StatusSticker,
  TransformationStackPanel,
  TopicKeyword,
  V4Caption,
} from './components/V4Primitives';
import {colors, fontStack, mediaWindowShadow} from './v4Styles';
import type {AudioCue, PresenterAudio, Scene, VisualEvent, VisualScript} from './v4Types';

type ShadeSide = 'left' | 'right';
type HudLane = ShadeSide | 'center' | 'proof';

type PresenterLayoutState = {
  left: number;
  top: number;
  width: number;
  height: number;
  borderRadius: number;
  opacity: number;
  windowChrome: number;
};

type PresenterMotionState = {
  layout: PresenterLayoutState;
  currentLayout: Scene['presenterLayout'];
  previousLayout?: Scene['presenterLayout'];
  transitionProgress: number;
};

const ENABLE_HUD_EDGE_SHADE = false;
const PRESENTER_LAYOUT_TRANSITION_SECONDS = 0.8;

const presenterLayoutStateFor = (
  layout: Scene['presenterLayout'],
  compositionWidth: number,
  compositionHeight: number,
): PresenterLayoutState => {
  const scaleX = compositionWidth / 1080;
  const scaleY = compositionHeight / 1920;
  const radiusScale = Math.min(scaleX, scaleY);
  if (layout === 'pip') {
    return {
      left: 46 * scaleX,
      top: compositionHeight - (250 + 406) * scaleY,
      width: 228 * scaleX,
      height: 406 * scaleY,
      borderRadius: 24 * radiusScale,
      opacity: 1,
      windowChrome: 1,
    };
  }
  if (layout === 'side') {
    return {
      left: 540 * scaleX,
      top: 430 * scaleY,
      width: 500 * scaleX,
      height: 889 * scaleY,
      borderRadius: 26 * radiusScale,
      opacity: 1,
      windowChrome: 1,
    };
  }
  return {
    left: 0,
    top: 0,
    width: compositionWidth,
    height: compositionHeight,
    borderRadius: 0,
    opacity: layout === 'none' ? 0 : 1,
    windowChrome: 0,
  };
};

const mixPresenterLayout = (
  from: PresenterLayoutState,
  to: PresenterLayoutState,
  progress: number,
): PresenterLayoutState => {
  const mix = (start: number, end: number): number => start + (end - start) * progress;
  return {
    left: mix(from.left, to.left),
    top: mix(from.top, to.top),
    width: mix(from.width, to.width),
    height: mix(from.height, to.height),
    borderRadius: mix(from.borderRadius, to.borderRadius),
    opacity: mix(from.opacity, to.opacity),
    windowChrome: mix(from.windowChrome, to.windowChrome),
  };
};

export const presenterMotionStateFor = ({
  scenes,
  sceneIndex,
  frame,
  fps,
  compositionWidth,
  compositionHeight,
}: {
  scenes: Scene[];
  sceneIndex: number;
  frame: number;
  fps: number;
  compositionWidth: number;
  compositionHeight: number;
}): PresenterMotionState => {
  const scene = scenes[sceneIndex];
  const currentLayout = scene.presenterLayout;
  const target = presenterLayoutStateFor(currentLayout, compositionWidth, compositionHeight);
  const previousScene = sceneIndex > 0 ? scenes[sceneIndex - 1] : undefined;
  const nextScene = sceneIndex + 1 < scenes.length ? scenes[sceneIndex + 1] : undefined;
  const transitionFrames = Math.max(1, Math.round(fps * PRESENTER_LAYOUT_TRANSITION_SECONDS));
  const preExitStart = Math.max(scene.startFrame, scene.endFrame - transitionFrames);
  const shouldPreExitPip =
    currentLayout === 'pip' &&
    nextScene &&
    nextScene.presenterLayout !== 'pip' &&
    frame >= preExitStart;

  if (shouldPreExitPip && nextScene) {
    const progress = interpolate(frame, [preExitStart, Math.max(preExitStart + 1, scene.endFrame - 1)], [0, 1], {
      easing: Easing.bezier(0.22, 1, 0.36, 1),
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    return {
      layout: mixPresenterLayout(
        presenterLayoutStateFor(currentLayout, compositionWidth, compositionHeight),
        presenterLayoutStateFor(nextScene.presenterLayout, compositionWidth, compositionHeight),
        progress,
      ),
      currentLayout: nextScene.presenterLayout,
      previousLayout: currentLayout,
      transitionProgress: progress,
    };
  }

  if (!previousScene || previousScene.presenterLayout === currentLayout) {
    return {layout: target, currentLayout, transitionProgress: 1};
  }
  if (previousScene.presenterLayout === 'pip' && currentLayout !== 'pip') {
    return {
      layout: target,
      currentLayout,
      previousLayout: previousScene.presenterLayout,
      transitionProgress: 1,
    };
  }
  const progress = interpolate(frame, [scene.startFrame, scene.startFrame + transitionFrames], [0, 1], {
    easing: Easing.bezier(0.22, 1, 0.36, 1),
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return {
    layout: mixPresenterLayout(
      presenterLayoutStateFor(previousScene.presenterLayout, compositionWidth, compositionHeight),
      target,
      progress,
    ),
    currentLayout,
    previousLayout: previousScene.presenterLayout,
    transitionProgress: progress,
  };
};

const presenterImpactScaleFor = (event: VisualEvent | undefined, frame: number): number => {
  if (!event || event.motionType !== 'presenter-impact-punch') return 1;
  const duration = Math.max(2, event.endFrame - event.startFrame);
  const local = frame - event.startFrame;
  const pushEnd = Math.min(duration - 1, Math.max(4, Math.round(duration * 0.2)));
  const reboundEnd = Math.min(duration - 1, pushEnd + Math.max(4, Math.round(duration * 0.2)));
  const returnStart = Math.max(reboundEnd + 1, duration - Math.max(6, Math.round(duration * 0.32)));
  const lastFrame = Math.max(returnStart + 1, duration - 1);
  return interpolate(
    local,
    [0, pushEnd, reboundEnd, returnStart, lastFrame],
    [1, event.presenterPeakScale ?? 1.08, event.presenterSettleScale ?? 1.04, event.presenterSettleScale ?? 1.04, 1],
    {
      easing: Easing.bezier(0.16, 1, 0.3, 1),
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    },
  );
};

const ContinuousPresenter: React.FC<{
  sourceVideo?: string;
  motion: PresenterMotionState;
  muted: boolean;
  impactScale: number;
  aboveMaterial: boolean;
}> = ({sourceVideo, motion, muted, impactScale, aboveMaterial}) => {
  const {layout} = motion;
  const chrome = layout.windowChrome;
  return (
    <div
      style={{
        position: 'absolute',
        left: layout.left,
        top: layout.top,
        width: layout.width,
        height: layout.height,
        borderRadius: layout.borderRadius,
        opacity: layout.opacity,
        zIndex: aboveMaterial ? 20 : 0,
        overflow: 'hidden',
        boxShadow:
          chrome > 0.001
            ? `${mediaWindowShadow}, 0 ${20 * chrome}px ${48 * chrome}px rgba(0,0,0,${0.55 * chrome})`
            : 'none',
      }}
    >
      {sourceVideo ? (
        <OffthreadVideo
          src={staticFile(sourceVideo)}
          muted={muted}
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            scale: impactScale,
            transformOrigin: '50% 37%',
          }}
        />
      ) : (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: layout.opacity <= 0.001 ? 'none' : 'grid',
            placeItems: 'center',
            background:
              'linear-gradient(135deg, rgba(18,25,38,0.96), rgba(5,7,11,0.96))',
            color: colors.white,
            fontSize: 26,
            fontWeight: 900,
            letterSpacing: 0,
          }}
        >
          源视频缺失
        </div>
      )}
    </div>
  );
};

const PresenterAudioLayer: React.FC<{
  config?: PresenterAudio;
  compositionDuration: number;
}> = ({config, compositionDuration}) => {
  if (config?.mode !== 'normalized-wav' || !config.path) return null;
  const offset = Math.trunc(config.syncOffsetFrames ?? 0);
  const sequenceStart = Math.max(0, offset);
  const trimBefore = Math.max(0, -offset);
  return (
    <Sequence from={sequenceStart} durationInFrames={Math.max(1, compositionDuration - sequenceStart)}>
      <Audio src={staticFile(config.path.replaceAll('\\', '/'))} trimBefore={trimBefore || undefined} />
    </Sequence>
  );
};

const dbToVolume = (volumeDb: number): number => Math.pow(10, volumeDb / 20);

const cueVolume = (cue: AudioCue, localFrame: number, duration: number): number => {
  const defaultDb = cue.type === 'bgm' ? -30 : cue.type === 'sfx' ? -23 : 0;
  const base = dbToVolume(cue.volumeDb ?? defaultDb);
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

const audioCueDuration = (cue: AudioCue, compositionDuration: number): number => {
  const startFrame = cue.startFrame ?? 0;
  if (typeof cue.durationFrames === 'number' && cue.durationFrames > 0) return cue.durationFrames;
  if (typeof cue.endFrame === 'number' && cue.endFrame > startFrame) return cue.endFrame - startFrame;
  if (cue.type === 'sfx') return 18;
  return Math.max(1, compositionDuration - startFrame);
};

const shouldRenderAudioCue = (cue: AudioCue): boolean => {
  if (cue.type === 'source' || cue.type === 'silence') return false;
  if (cue.status === 'pending-selection' || cue.status === 'pending-generation' || cue.status === 'suggested') return false;
  if (cue.status === 'disabled' || cue.status === 'muted') return false;
  return Boolean(cue.path);
};

const AudioCueLayer: React.FC<{cue: AudioCue; compositionDuration: number}> = ({
  cue,
  compositionDuration,
}) => {
  if (!shouldRenderAudioCue(cue)) return null;

  const startFrame = cue.startFrame ?? 0;
  const duration = audioCueDuration(cue, compositionDuration);

  return (
    <Sequence from={startFrame} durationInFrames={duration}>
      <Audio
        src={staticFile(cue.path ?? '')}
        loop={cue.loop}
        volume={(frame) => cueVolume(cue, frame, duration)}
      />
    </Sequence>
  );
};

const GridOverlay: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      inset: 0,
      backgroundImage:
        'linear-gradient(rgba(255,255,255,0.045) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)',
      backgroundSize: '48px 48px',
      opacity: 0.18,
      pointerEvents: 'none',
    }}
  />
);

const sceneForFrame = (scenes: Scene[], frame: number): Scene =>
  scenes.find((scene) => frame >= scene.startFrame && frame < scene.endFrame) ?? scenes[0];

const activeEvents = (events: VisualEvent[], frame: number): VisualEvent[] =>
  events.filter((event) => frame >= event.startFrame && frame < event.endFrame);

const eventShadeSide = (event: VisualEvent, scene: Scene): ShadeSide | null => {
  if (
    event.type === 'cornerChapterLabel' ||
    event.type === 'ctaTitle' ||
    event.type === 'ctaRecommend' ||
    event.type === 'materialMain' ||
    event.type === 'materialZoom' ||
    event.type === 'evidenceWindow' ||
    event.type === 'depthKeyword'
  ) {
    return null;
  }

  const placement = `${event.safeArea ?? ''} ${event.style ?? ''} ${event.motionType ?? ''}`.toLowerCase();
  const explicitSide: ShadeSide | null = placement.includes('right')
    ? 'right'
    : placement.includes('left')
      ? 'left'
      : null;

  if (event.type === 'kineticTitle' || event.type === 'bigJudgement' || event.type === 'dataPunch' || event.type === 'quoteSource' || event.type === 'metricSpotlight' || event.type === 'topicKeyword') return explicitSide ?? 'left';
  if (event.type === 'claimStrip') return explicitSide ?? 'right';
  if (event.type === 'flowPath' || event.type === 'statusStack' || event.type === 'platformFanout' || event.type === 'workflowDashboard' || event.type === 'ratioGallery') return explicitSide ?? 'right';
  if (event.type === 'capabilityShare' || event.type === 'sceneLockGrid' || event.type === 'transformationStack') return explicitSide ?? 'left';
  if (event.type === 'semanticProblemMap' || (event.type === 'highlightBox' && event.semanticRole === 'semantic-problem-map')) return 'left';
  if (event.type === 'transitionPushZoom' && event.semanticRole === 'platform-fanout') return 'right';
  if (event.type === 'automationHandoff' || (event.type === 'captionHighlight' && event.semanticRole === 'automation-handoff')) return 'left';

  if (event.type === 'infoCard') {
    if (event.semanticRole === 'manual-field') return 'right';
    if (explicitSide) return explicitSide;
    return scene.presenterLayout === 'pip' ? null : 'left';
  }

  if (event.type === 'statusSticker') {
    if (
      event.semanticRole === 'chapter-label' ||
      placement.includes('top-left') ||
      placement.includes('corner')
    ) {
      return null;
    }
    return explicitSide;
  }

  return null;
};

const eventHudSide = (event: VisualEvent, scene: Scene, fallback: ShadeSide): ShadeSide => {
  return eventShadeSide(event, scene) ?? fallback;
};

const primaryHudLane = (event: VisualEvent, scene: Scene): HudLane | null => {
  if (
    event.type === 'cornerChapterLabel' ||
    event.type === 'statusSticker' ||
    event.type === 'iconPulse' ||
    event.type === 'presenterReposition' ||
    event.type === 'depthKeyword'
  ) {
    return null;
  }

  if (event.type === 'ctaTitle' || event.type === 'ctaRecommend') return 'left';
  if (event.type === 'materialMain' || event.type === 'materialZoom' || event.type === 'evidenceWindow') return 'proof';

  return eventShadeSide(event, scene);
};

const chooseHudEvent = (current: VisualEvent, candidate: VisualEvent): VisualEvent =>
  candidate.startFrame >= current.startFrame ? candidate : current;

const visibleHudEvents = (events: VisualEvent[], scene: Scene): VisualEvent[] => {
  const selectedByLane = new Map<HudLane, VisualEvent>();

  for (const event of events) {
    const lane = primaryHudLane(event, scene);
    if (!lane) continue;
    const current = selectedByLane.get(lane);
    selectedByLane.set(lane, current ? chooseHudEvent(current, event) : event);
  }

  return events.filter((event) => {
    const lane = primaryHudLane(event, scene);
    return !lane || selectedByLane.get(lane)?.id === event.id;
  });
};

const edgeShadeProgress = (event: VisualEvent, frame: number): number => {
  const localFrame = frame - event.startFrame;
  const duration = Math.max(1, event.endFrame - event.startFrame);
  const fadeFrames = Math.min(22, Math.max(12, Math.floor(duration / 4)));
  const holdEnd = Math.max(fadeFrames + 1, duration - fadeFrames);

  return interpolate(localFrame, [0, fadeFrames, holdEnd, duration], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
};

const HudEdgeShade: React.FC<{
  events: VisualEvent[];
  scene: Scene;
  side: ShadeSide;
  frame: number;
}> = ({events, scene, side, frame}) => {
  const progress = events
    .filter((event) => eventShadeSide(event, scene) === side)
    .reduce((max, event) => Math.max(max, edgeShadeProgress(event, frame)), 0);

  if (progress <= 0) return null;

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        bottom: 0,
        [side]: 0,
        width: 840,
        opacity: progress * 0.82,
        transform: `translateX(${
          side === 'left'
            ? interpolate(progress, [0, 1], [-18, 0])
            : interpolate(progress, [0, 1], [18, 0])
        }px)`,
        background:
          side === 'left'
            ? 'linear-gradient(90deg, rgba(5,7,11,0.92) 0%, rgba(5,7,11,0.68) 42%, rgba(5,7,11,0.30) 74%, rgba(5,7,11,0) 100%)'
            : 'linear-gradient(270deg, rgba(5,7,11,0.92) 0%, rgba(5,7,11,0.68) 42%, rgba(5,7,11,0.30) 74%, rgba(5,7,11,0) 100%)',
        pointerEvents: 'none',
      }}
    />
  );
};

export const V4Composition: React.FC<{visualScript: VisualScript}> = ({visualScript}) => {
  const frame = useCurrentFrame();
  const currentScene = sceneForFrame(visualScript.scenes, frame);
  const currentSceneIndex = Math.max(0, visualScript.scenes.findIndex((scene) => scene.id === currentScene.id));
  const presenterMotion = presenterMotionStateFor({
    scenes: visualScript.scenes,
    sceneIndex: currentSceneIndex,
    frame,
    fps: visualScript.composition.fps,
    compositionWidth: visualScript.composition.width,
    compositionHeight: visualScript.composition.height,
  });
  const activeCaption = visualScript.captionCues.find(
    (caption) => frame >= caption.startFrame && frame < caption.endFrame,
  );
  const rawEvents = activeEvents(visualScript.visualEvents, frame);
  const presenterSource = visualScript.scenes.find((scene) => Boolean(scene.sourceVideo))?.sourceVideo;
  const presenterAudioMode = visualScript.presenterAudio?.mode ?? 'embedded';
  const presenterImpactEvent = rawEvents.find(
    (event) => event.type === 'presenterReposition' && event.motionType === 'presenter-impact-punch',
  );
  const presenterImpactScale = presenterImpactScaleFor(presenterImpactEvent, frame);
  const presenterAboveMaterial =
    currentScene.presenterLayout === 'pip' ||
    presenterMotion.currentLayout === 'pip' ||
    (presenterMotion.previousLayout === 'pip' && presenterMotion.transitionProgress < 1);
  const events = visibleHudEvents(rawEvents, currentScene);
  const materialEvent = rawEvents.find((event) => ['materialMain', 'materialZoom', 'evidenceWindow'].includes(event.type));
  const materialFocusMode =
    Boolean(materialEvent) ||
    currentScene.materialLayout === 'main' ||
    currentScene.materialLayout === 'clean';
  const suppressCompetingHud = materialFocusMode && currentScene.presenterLayout === 'pip';
  const isProofEvent = (event: VisualEvent): boolean =>
    event.semanticRole === 'proof-focus' ||
    event.semanticRole === 'proof-material' ||
    event.semanticRole === 'material-main';
  const infoCards = events.filter(
    (event) => event.type === 'infoCard' && (!suppressCompetingHud || isProofEvent(event)),
  );
  const problemMaps = events.filter(
    (event) => event.type === 'semanticProblemMap' || (event.type === 'highlightBox' && event.semanticRole === 'semantic-problem-map'),
  );
  const platformFanouts = events.filter(
    (event) => event.type === 'platformFanout' || (event.type === 'transitionPushZoom' && event.semanticRole === 'platform-fanout'),
  );
  const automationHandoffs = events.filter(
    (event) => event.type === 'automationHandoff' || (event.type === 'captionHighlight' && event.semanticRole === 'automation-handoff'),
  );
  const dataPunches = events.filter(
    (event) => event.type === 'dataPunch' || event.type === 'metricSpotlight',
  );
  const flowLists = events.filter(
    (event) => event.type === 'flowPath' || event.type === 'statusStack' || event.type === 'workflowDashboard',
  );
  const capabilityShares = events.filter((event) => event.type === 'capabilityShare');
  const sceneLockGrids = events.filter((event) => event.type === 'sceneLockGrid');
  const transformationStacks = events.filter((event) => event.type === 'transformationStack');
  const titles = events.filter(
    (event) => ['kineticTitle', 'bigJudgement', 'ctaTitle', 'ctaRecommend'].includes(event.type),
  );
  const topicKeywords = events.filter((event) => event.type === 'topicKeyword');
  const claimStrips = events.filter((event) => event.type === 'claimStrip' || event.type === 'quoteSource');
  const ratioGalleries = events.filter((event) => event.type === 'ratioGallery');
  const depthKeywords = rawEvents.filter((event) => event.type === 'depthKeyword');
  const cornerLabels = events.filter((event) => event.type === 'cornerChapterLabel');
  const stickers = events.filter((event) => event.type === 'statusSticker' || event.type === 'iconPulse');
  const visibleTitles = suppressCompetingHud ? titles.filter(isProofEvent) : titles;
  const visibleProblemMaps = suppressCompetingHud ? [] : problemMaps;
  const visiblePlatformFanouts = suppressCompetingHud ? [] : platformFanouts;
  const visibleAutomationHandoffs = suppressCompetingHud ? [] : automationHandoffs;
  const visibleDataPunches = suppressCompetingHud ? [] : dataPunches;
  const visibleFlowLists = suppressCompetingHud ? [] : flowLists;
  const visibleCapabilityShares = suppressCompetingHud ? [] : capabilityShares;
  const visibleSceneLockGrids = suppressCompetingHud ? [] : sceneLockGrids;
  const visibleTransformationStacks = suppressCompetingHud ? [] : transformationStacks;
  const visibleTopicKeywords = suppressCompetingHud ? [] : topicKeywords;
  const visibleClaimStrips = suppressCompetingHud ? [] : claimStrips;
  const visibleRatioGalleries = suppressCompetingHud ? [] : ratioGalleries;
  const visibleCornerLabels = suppressCompetingHud ? cornerLabels.filter(isProofEvent) : cornerLabels;
  const visibleStickers = suppressCompetingHud ? stickers.filter(isProofEvent) : stickers;

  return (
    <AbsoluteFill
      style={{
        background: colors.black,
        overflow: 'hidden',
        fontFamily: fontStack,
      }}
    >
      <style>
        {`@font-face {
          font-family: "SourceHanSansSC";
          src: url("${staticFile('fonts/SourceHanSansSC-Regular.otf')}") format("opentype");
          font-weight: 400;
          font-display: block;
        }
        @font-face {
          font-family: "SourceHanSansSC";
          src: url("${staticFile('fonts/SourceHanSansSC-Bold.otf')}") format("opentype");
          font-weight: 700 899;
          font-display: block;
        }
        @font-face {
          font-family: "SourceHanSansSC";
          src: url("${staticFile('fonts/SourceHanSansSC-Heavy.otf')}") format("opentype");
          font-weight: 900 950;
          font-display: block;
        }`}
      </style>
      <ContinuousPresenter
        sourceVideo={presenterSource}
        motion={presenterMotion}
        muted={presenterAudioMode !== 'embedded'}
        impactScale={presenterImpactScale}
        aboveMaterial={presenterAboveMaterial}
      />
      {depthKeywords.map((event) => (
        <DepthKeywordLayer key={event.id} event={event} />
      ))}
      <PresenterAudioLayer
        config={visualScript.presenterAudio}
        compositionDuration={visualScript.composition.durationFrames}
      />
      {visualScript.audioCues.map((cue) => (
        <AudioCueLayer
          key={cue.id}
          cue={cue}
          compositionDuration={visualScript.composition.durationFrames}
        />
      ))}
      <GridOverlay />
      {ENABLE_HUD_EDGE_SHADE ? (
        <>
          <HudEdgeShade events={events} scene={currentScene} side="left" frame={frame} />
          <HudEdgeShade events={events} scene={currentScene} side="right" frame={frame} />
        </>
      ) : null}
      {visibleCornerLabels.map((event) => (
        <CornerChapterLabel key={event.id} event={event} />
      ))}

      {materialEvent ? <MaterialBoard event={materialEvent} /> : null}

      {visibleTitles.map((event) => (
        <KineticTitle
          key={event.id}
          event={event}
          align={event.type === 'ctaTitle' ? 'center' : 'left'}
        />
      ))}

      {visibleTopicKeywords.map((event) => (
        <TopicKeyword key={event.id} event={event} />
      ))}

      {visibleClaimStrips.map((event) => (
        <ClaimStrip key={event.id} event={event} />
      ))}

      {visibleRatioGalleries.map((event) => (
        <RatioGallery key={event.id} event={event} />
      ))}

      {infoCards.map((event, index) => (
        <InfoCard
          key={event.id}
          event={event}
          index={index}
          variant={
            currentScene.presenterLayout === 'pip'
                ? 'material'
                : eventHudSide(event, currentScene, 'left')
          }
        />
      ))}

      {visibleProblemMaps.map((event) => (
        <SemanticProblemMap key={event.id} event={event} />
      ))}

      {visiblePlatformFanouts.map((event) => (
        <PlatformFanOutPanel key={event.id} event={event} />
      ))}

      {visibleAutomationHandoffs.map((event) => (
        <AutomationHandoffPanel key={event.id} event={event} />
      ))}

      {visibleDataPunches.map((event) => (
        <DataPunch key={event.id} event={event} side={eventHudSide(event, currentScene, 'left')} />
      ))}

      {visibleFlowLists.map((event) => (
        <FlowListPanel key={event.id} event={event} side={eventHudSide(event, currentScene, 'right')} />
      ))}

      {visibleCapabilityShares.map((event) => (
        <CapabilitySharePanel key={event.id} event={event} side={eventHudSide(event, currentScene, 'left')} />
      ))}

      {visibleSceneLockGrids.map((event) => (
        <SceneLockGridPanel key={event.id} event={event} side={eventHudSide(event, currentScene, 'left')} />
      ))}

      {visibleTransformationStacks.map((event) => (
        <TransformationStackPanel key={event.id} event={event} side={eventHudSide(event, currentScene, 'left')} />
      ))}

      {visibleStickers.map((event) => (
        <StatusSticker key={event.id} event={event} />
      ))}

      {visualScript.captionRenderMode !== 'none' && activeCaption ? (
        <V4Caption
          text={activeCaption.text}
          highlightWords={activeCaption.highlightWords ?? activeCaption.keywords ?? []}
        />
      ) : null}
    </AbsoluteFill>
  );
};
