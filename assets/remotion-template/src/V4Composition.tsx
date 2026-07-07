import React from 'react';
import {
  AbsoluteFill,
  Audio,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
} from 'remotion';
import {
  AutomationHandoffPanel,
  CapabilitySharePanel,
  CornerChapterLabel,
  DataPunch,
  FlowListPanel,
  InfoCard,
  KineticTitle,
  MaterialBoard,
  PlatformFanOutPanel,
  SceneLockGridPanel,
  SemanticProblemMap,
  StatusSticker,
  TransformationStackPanel,
  V4Caption,
} from './components/V4Primitives';
import {colors, fontStack, mediaWindowShadow} from './v4Styles';
import type {AudioCue, Scene, VisualEvent, VisualScript} from './v4Types';

type ShadeSide = 'left' | 'right';
type HudLane = ShadeSide | 'center' | 'proof';

const ENABLE_HUD_EDGE_SHADE = false;

const videoStyleFor = (layout: Scene['presenterLayout']): React.CSSProperties => {
  if (layout === 'pip') {
    return {
      position: 'absolute',
      left: 46,
      bottom: 250,
      width: 300,
      height: 176,
      objectFit: 'cover',
      borderRadius: 24,
      border: 'none',
      boxShadow: `${mediaWindowShadow}, 0 20px 48px rgba(0,0,0,0.55)`,
      overflow: 'hidden',
    };
  }
  if (layout === 'side') {
    return {
      position: 'absolute',
      left: 64,
      bottom: 250,
      width: 952,
      height: 536,
      objectFit: 'cover',
      borderRadius: 26,
      border: 'none',
      boxShadow: `${mediaWindowShadow}, 0 24px 64px rgba(0,0,0,0.48)`,
    };
  }
  return {
    position: 'absolute',
    inset: 0,
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  };
};

const SceneVideo: React.FC<{scene: Scene}> = ({scene}) => {
  const duration = scene.endFrame - scene.startFrame;
  return (
    <Sequence from={scene.startFrame} durationInFrames={duration}>
      {scene.sourceVideo ? (
        <OffthreadVideo
          src={staticFile(scene.sourceVideo)}
          startFrom={scene.startFrame}
          style={videoStyleFor(scene.presenterLayout)}
        />
      ) : (
        <div
          style={{
            ...videoStyleFor(scene.presenterLayout),
            display: scene.presenterLayout === 'none' ? 'none' : 'grid',
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
    event.type === 'materialMain' ||
    event.type === 'materialZoom'
  ) {
    return null;
  }

  const placement = `${event.safeArea ?? ''} ${event.style ?? ''} ${event.motionType ?? ''}`.toLowerCase();
  const explicitSide: ShadeSide | null = placement.includes('right')
    ? 'right'
    : placement.includes('left')
      ? 'left'
      : null;

  if (event.type === 'kineticTitle' || event.type === 'bigJudgement' || event.type === 'dataPunch' || event.type === 'quoteSource' || event.type === 'metricSpotlight') return explicitSide ?? 'left';
  if (event.type === 'flowPath' || event.type === 'statusStack' || event.type === 'platformFanout' || event.type === 'workflowDashboard') return explicitSide ?? 'right';
  if (event.type === 'capabilityShare' || event.type === 'sceneLockGrid' || event.type === 'transformationStack') return explicitSide ?? 'left';
  if (event.type === 'highlightBox' && event.semanticRole === 'semantic-problem-map') return 'left';
  if (event.type === 'transitionPushZoom' && event.semanticRole === 'platform-fanout') return 'right';
  if (event.type === 'captionHighlight' && event.semanticRole === 'automation-handoff') return 'left';

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
    event.type === 'presenterReposition'
  ) {
    return null;
  }

  if (event.type === 'ctaTitle') return 'left';
  if (event.type === 'materialMain' || event.type === 'materialZoom') return 'proof';

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
  const activeCaption = visualScript.captionCues.find(
    (caption) => frame >= caption.startFrame && frame < caption.endFrame,
  );
  const rawEvents = activeEvents(visualScript.visualEvents, frame);
  const events = visibleHudEvents(rawEvents, currentScene);
  const materialEvent = rawEvents.find((event) => event.type === 'materialMain');
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
    (event) => event.type === 'highlightBox' && event.semanticRole === 'semantic-problem-map',
  );
  const platformFanouts = events.filter(
    (event) => event.type === 'transitionPushZoom' && event.semanticRole === 'platform-fanout',
  );
  const automationHandoffs = events.filter(
    (event) => event.type === 'captionHighlight' && event.semanticRole === 'automation-handoff',
  );
  const dataPunches = events.filter(
    (event) => event.type === 'dataPunch' || event.type === 'metricSpotlight',
  );
  const flowLists = events.filter(
    (event) => event.type === 'flowPath' || event.type === 'statusStack',
  );
  const capabilityShares = events.filter((event) => event.type === 'capabilityShare');
  const sceneLockGrids = events.filter((event) => event.type === 'sceneLockGrid');
  const transformationStacks = events.filter((event) => event.type === 'transformationStack');
  const titles = events.filter(
    (event) => event.type === 'kineticTitle' || event.type === 'ctaTitle',
  );
  const cornerLabels = events.filter((event) => event.type === 'cornerChapterLabel');
  const stickers = events.filter((event) => event.type === 'statusSticker');
  const visibleTitles = suppressCompetingHud ? titles.filter(isProofEvent) : titles;
  const visibleProblemMaps = suppressCompetingHud ? [] : problemMaps;
  const visiblePlatformFanouts = suppressCompetingHud ? [] : platformFanouts;
  const visibleAutomationHandoffs = suppressCompetingHud ? [] : automationHandoffs;
  const visibleDataPunches = suppressCompetingHud ? [] : dataPunches;
  const visibleFlowLists = suppressCompetingHud ? [] : flowLists;
  const visibleCapabilityShares = suppressCompetingHud ? [] : capabilityShares;
  const visibleSceneLockGrids = suppressCompetingHud ? [] : sceneLockGrids;
  const visibleTransformationStacks = suppressCompetingHud ? [] : transformationStacks;
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
      {visualScript.scenes.filter((scene) => scene.presenterLayout !== 'pip').map((scene) => (
        <SceneVideo key={scene.id} scene={scene} />
      ))}
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

      {currentScene.presenterLayout === 'pip' ? (
        <SceneVideo key={`${currentScene.id}-pip`} scene={currentScene} />
      ) : null}

      {visibleTitles.map((event) => (
        <KineticTitle
          key={event.id}
          event={event}
          align={event.type === 'ctaTitle' ? 'center' : 'left'}
        />
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

      {activeCaption ? (
        <V4Caption
          text={activeCaption.text}
          highlightWords={activeCaption.highlightWords ?? activeCaption.keywords ?? []}
        />
      ) : null}
    </AbsoluteFill>
  );
};
