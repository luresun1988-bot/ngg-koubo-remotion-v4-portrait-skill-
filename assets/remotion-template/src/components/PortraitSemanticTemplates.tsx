import React from 'react';
import {Easing, interpolate, useCurrentFrame} from 'remotion';
import {
  AudioLines,
  AudioWaveform,
  BadgeCheck,
  BrainCircuit,
  Boxes,
  CircleDot,
  CircleX,
  FileText,
  Film,
  Gauge,
  HeartPulse,
  Image as ImageIcon,
  Maximize2,
  Package,
  ScanFace,
  SlidersHorizontal,
  UploadCloud,
  Video,
  WandSparkles,
  Workflow,
  type LucideProps,
} from 'lucide-react';
import type {VisualEvent} from '../v4Types';
import {colors, fontStack, hudRingShadow, hudTextHighlight} from '../v4Styles';

type Step = NonNullable<VisualEvent['internalSteps']>[number];
type IconComponent = React.ComponentType<LucideProps>;

const iconMap: Record<string, IconComponent> = {
  AudioLines,
  AudioWaveform,
  BadgeCheck,
  BrainCircuit,
  Boxes,
  CircleDot,
  CircleX,
  FileText,
  Film,
  Gauge,
  HeartPulse,
  Image: ImageIcon,
  Maximize2,
  Package,
  ScanFace,
  SlidersHorizontal,
  UploadCloud,
  Video,
  WandSparkles,
  Workflow,
};

const clamp = {
  extrapolateLeft: 'clamp' as const,
  extrapolateRight: 'clamp' as const,
};
const ease = Easing.bezier(0.16, 1, 0.3, 1);

const eventProgress = (frame: number, event: VisualEvent): number => {
  const duration = Math.max(1, event.endFrame - event.startFrame);
  const fade = Math.min(18, Math.max(10, Math.floor(duration / 4)));
  return interpolate(
    frame,
    [event.startFrame, event.startFrame + fade, event.endFrame - fade, event.endFrame],
    [0, 1, 1, 0],
    {...clamp, easing: ease},
  );
};

const revealProgress = (frame: number, start: number, duration = 16): number =>
  interpolate(frame, [start, start + duration], [0, 1], {...clamp, easing: ease});

const stepIcon = (step: Step, fallback: IconComponent = CircleDot): IconComponent =>
  iconMap[String(step.iconName ?? '')] ?? fallback;

const panelBase: React.CSSProperties = {
  position: 'absolute',
  width: 350,
  zIndex: 18,
  fontFamily: fontStack,
};

const semanticLabel: React.CSSProperties = {
  color: colors.blue,
  fontSize: 27,
  fontWeight: 900,
  textShadow: hudTextHighlight,
};

const titleStyle: React.CSSProperties = {
  color: colors.white,
  fontSize: 50,
  lineHeight: 1.08,
  fontWeight: 900,
  textShadow: hudTextHighlight,
};

const SemanticRow: React.FC<{
  step: Step;
  progress: number;
  accent?: string;
  detail?: string;
}> = ({step, progress, accent = colors.blue, detail}) => {
  const Icon = stepIcon(step);
  return (
    <div
      style={{
        minHeight: 90,
        borderRadius: 22,
        backgroundColor: 'rgba(5,7,11,0.68)',
        boxShadow: hudRingShadow,
        display: 'flex',
        alignItems: 'center',
        gap: 15,
        padding: '0 19px',
        opacity: progress,
        translate: `${interpolate(progress, [0, 1], [38, 0])}px 0px`,
        scale: interpolate(progress, [0, 0.72, 1], [0.88, 1.04, 1]),
      }}
    >
      <Icon size={38} color={accent} strokeWidth={2.8} />
      <div style={{display: 'flex', flexDirection: 'column', gap: 2}}>
        <span style={{color: colors.white, fontSize: 34, fontWeight: 900, textShadow: hudTextHighlight}}>
          {step.label}
        </span>
        {detail ? (
          <span style={{color: 'rgba(240,240,240,0.78)', fontSize: 22, fontWeight: 700}}>{detail}</span>
        ) : null}
      </div>
    </div>
  );
};

export const PairedInputRailPanel: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const progress = eventProgress(frame, event);
  const steps = (event.internalSteps ?? []).slice(0, 2);
  return (
    <div style={{...panelBase, right: 46, top: 350, opacity: progress}}>
      <div style={semanticLabel}>{event.status ?? '先准备好'}</div>
      <div style={{...titleStyle, marginTop: 5, marginBottom: 19}}>{event.title ?? '两类核心素材'}</div>
      <div style={{display: 'flex', flexDirection: 'column', gap: 15}}>
        {steps.map((step, index) => (
          <SemanticRow
            key={step.id ?? step.label ?? index}
            step={step}
            progress={revealProgress(frame, event.startFrame + 10 + index * 18)}
            accent={index === 0 ? colors.amber : colors.blue}
          />
        ))}
      </div>
    </div>
  );
};

export const FactorTrinityPanel: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const progress = eventProgress(frame, event);
  const steps = (event.internalSteps ?? []).slice(0, 3);
  return (
    <div style={{...panelBase, right: 44, top: 370, width: 356, opacity: progress}}>
      <div style={semanticLabel}>{event.status ?? '并列要素'}</div>
      <div style={{...titleStyle, marginTop: 5}}>{event.title ?? '三个都重要'}</div>
      <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginTop: 24}}>
        {steps.map((step, index) => {
          const itemProgress = revealProgress(frame, event.startFrame + 10 + index * 12);
          const Icon = stepIcon(step);
          const accent = index === 0 ? colors.blue : index === 1 ? colors.white : colors.amber;
          return (
            <div
              key={step.id ?? step.label ?? index}
              style={{
                height: 132,
                borderRadius: 22,
                backgroundColor: 'rgba(5,7,11,0.68)',
                boxShadow: hudRingShadow,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 10,
                opacity: itemProgress,
                translate: `0px ${interpolate(itemProgress, [0, 1], [32, 0])}px`,
                scale: interpolate(itemProgress, [0, 0.75, 1], [0.82, 1.07, 1]),
              }}
            >
              <Icon size={38} color={accent} strokeWidth={2.7} />
              <span style={{color: colors.white, fontSize: 29, fontWeight: 900, textShadow: hudTextHighlight}}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const CausalDriverPanel: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const progress = eventProgress(frame, event);
  const driver = (event.internalSteps ?? []).find((step) => step.role === 'driver');
  const target = (event.internalSteps ?? []).find((step) => step.role === 'target');
  const DriverIcon = stepIcon(driver ?? {}, AudioLines);
  return (
    <div
      style={{
        ...panelBase,
        left: 62,
        top: 370,
        width: 338,
        opacity: progress,
        translate: `${interpolate(progress, [0, 1], [-42, 0])}px 0px`,
      }}
    >
      <div style={{display: 'flex', alignItems: 'center', gap: 12, color: colors.blue}}>
        <DriverIcon size={34} strokeWidth={2.8} />
        <span style={{fontSize: 27, fontWeight: 900, textShadow: hudTextHighlight}}>{event.title ?? '核心机制'}</span>
      </div>
      <div style={{...titleStyle, fontSize: 74, lineHeight: 1.02, marginTop: 12}}>
        {driver?.label}
        <br />
        <span style={{color: colors.amber}}>驱动</span>
      </div>
      <div
        style={{
          marginTop: 22,
          display: 'inline-flex',
          alignItems: 'center',
          gap: 10,
          padding: '11px 15px',
          borderRadius: 16,
          backgroundColor: 'rgba(5,7,11,0.68)',
          boxShadow: hudRingShadow,
          color: colors.white,
          fontSize: 25,
          fontWeight: 900,
          opacity: revealProgress(frame, event.startFrame + 18),
        }}
      >
        <span style={{color: colors.blue}}>→</span>
        {target?.label}
      </div>
    </div>
  );
};

export const FactorPriorityPanel: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const progress = eventProgress(frame, event);
  const steps = (event.internalSteps ?? []).slice(0, 3);
  return (
    <div style={{...panelBase, right: 46, top: 340, opacity: progress}}>
      <div style={{color: colors.amber, fontSize: 27, fontWeight: 900, textShadow: hudTextHighlight}}>
        {event.status ?? '关键因素'}
      </div>
      <div style={{...titleStyle, marginTop: 7, marginBottom: 20}}>{event.title ?? '真正影响效果'}</div>
      <div style={{display: 'flex', flexDirection: 'column', gap: 13}}>
        {steps.map((step, index) => (
          <SemanticRow
            key={step.id ?? step.label ?? index}
            step={step}
            progress={revealProgress(frame, event.startFrame + 12 + index * 16)}
            accent={index === steps.length - 1 ? colors.amber : colors.blue}
          />
        ))}
      </div>
    </div>
  );
};

export const CompactPipelinePanel: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const progress = eventProgress(frame, event);
  const steps = (event.internalSteps ?? []).slice(0, 3);
  return (
    <div style={{...panelBase, right: 48, top: 340, width: 322, opacity: progress}}>
      <div style={semanticLabel}>{event.status ?? '按顺序推进'}</div>
      <div style={{...titleStyle, fontSize: 47, marginTop: 5, marginBottom: 20}}>{event.title ?? '三阶段流程'}</div>
      <div style={{display: 'flex', flexDirection: 'column', gap: 12}}>
        {steps.map((step, index) => {
          const itemProgress = revealProgress(frame, event.startFrame + 10 + index * 16);
          const Icon = stepIcon(step, Workflow);
          return (
            <div key={step.id ?? step.label ?? index} style={{display: 'flex', alignItems: 'center', gap: 12}}>
              <div
                style={{
                  width: 45,
                  height: 45,
                  borderRadius: 23,
                  backgroundColor: index === 2 ? colors.amber : colors.blue,
                  display: 'grid',
                  placeItems: 'center',
                  color: colors.black,
                  fontSize: 24,
                  fontWeight: 900,
                  opacity: itemProgress,
                  scale: interpolate(itemProgress, [0, 0.7, 1], [0.5, 1.13, 1]),
                }}
              >
                {index + 1}
              </div>
              <div
                style={{
                  flex: 1,
                  minHeight: 82,
                  borderRadius: 20,
                  backgroundColor: 'rgba(5,7,11,0.68)',
                  boxShadow: hudRingShadow,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 13,
                  padding: '0 17px',
                  opacity: itemProgress,
                  translate: `${interpolate(itemProgress, [0, 1], [32, 0])}px 0px`,
                }}
              >
                <Icon size={33} color={index === 2 ? colors.amber : colors.white} strokeWidth={2.8} />
                <span style={{color: colors.white, fontSize: 31, fontWeight: 900, textShadow: hudTextHighlight}}>
                  {step.label}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const LimitationWarningPanel: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const progress = eventProgress(frame, event);
  const limitations = (event.internalSteps ?? []).filter((step) => step.role === 'limitation').slice(0, 2);
  return (
    <div
      style={{
        ...panelBase,
        left: 54,
        top: 355,
        width: 356,
        opacity: progress,
        translate: `${interpolate(progress, [0, 1], [-44, 0])}px 0px`,
      }}
    >
      <div style={{display: 'flex', alignItems: 'center', gap: 11, color: colors.red}}>
        <CircleX size={34} strokeWidth={2.9} />
        <span style={{fontSize: 27, fontWeight: 900, textShadow: hudTextHighlight}}>{event.title ?? '能力边界'}</span>
      </div>
      <div style={{...titleStyle, fontSize: 49, marginTop: 14}}>
        {event.text}
        <br />
        <span style={{color: colors.red}}>≠ 万能修复</span>
      </div>
      <div style={{display: 'flex', flexDirection: 'column', gap: 12, marginTop: 22}}>
        {limitations.map((step, index) => (
          <SemanticRow
            key={step.id ?? step.label ?? index}
            step={step}
            progress={revealProgress(frame, event.startFrame + 22 + index * 15)}
            accent={colors.red}
          />
        ))}
      </div>
    </div>
  );
};

const PrerequisitePanel: React.FC<{event: VisualEvent; historicalGreen?: boolean}> = ({
  event,
  historicalGreen = false,
}) => {
  const frame = useCurrentFrame();
  const progress = eventProgress(frame, event);
  const accent = historicalGreen ? colors.green : colors.amber;
  return (
    <div
      style={{
        ...panelBase,
        right: 48,
        top: 385,
        width: 350,
        opacity: progress,
        translate: `${interpolate(progress, [0, 1], [48, 0])}px 0px`,
      }}
    >
      <div
        style={{
          width: 82,
          height: 82,
          borderRadius: 24,
          backgroundColor: accent,
          display: 'grid',
          placeItems: 'center',
          boxShadow: hudRingShadow,
          scale: interpolate(progress, [0, 0.72, 1], [0.55, 1.1, 1]),
        }}
      >
        <BadgeCheck size={50} color={colors.black} strokeWidth={2.8} />
      </div>
      <div style={{...semanticLabel, marginTop: 18}}>{event.title ?? '前提条件'}</div>
      <div style={{...titleStyle, fontSize: 55, marginTop: 8}}>
        {event.text}
        {event.subtext ? (
          <>
            <br />
            <span style={{color: accent}}>{event.subtext}</span>
          </>
        ) : null}
      </div>
      <div
        style={{
          marginTop: 18,
          color: colors.white,
          fontSize: 25,
          fontWeight: 850,
          textShadow: hudTextHighlight,
          opacity: revealProgress(frame, event.startFrame + 16),
        }}
      >
        {event.status ?? '必须先满足'}
      </div>
    </div>
  );
};

export const PriorityConclusionPanel: React.FC<{event: VisualEvent}> = ({event}) => (
  <PrerequisitePanel event={event} />
);

export const HistoricalGreenConclusionPanel: React.FC<{event: VisualEvent}> = ({event}) => (
  <PrerequisitePanel event={event} historicalGreen />
);
