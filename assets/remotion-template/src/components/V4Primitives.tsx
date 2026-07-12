import React from 'react';
import {
  AlignLeft,
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  BarChart3,
  Bot,
  BrainCircuit,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  Check,
  CheckCircle2,
  CircleX,
  ClipboardList,
  CreditCard,
  Cpu,
  ExternalLink,
  FileCheck2,
  FileText,
  FlaskConical,
  Folder,
  Globe2,
  GraduationCap,
  Hash,
  Image,
  Images,
  Landmark,
  Layers,
  Link2,
  ListChecks,
  MapPinned,
  MonitorUp,
  Network,
  Package,
  PackageCheck,
  PanelsTopLeft,
  Repeat2,
  Route,
  ScanSearch,
  Scale,
  SendHorizontal,
  ShieldCheck,
  Tags,
  TextCursorInput,
  TrendingUp,
  Trophy,
  UploadCloud,
  User,
  Users,
  Video,
  Workflow,
  Zap,
  Store,
} from 'lucide-react';
import {
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {
  captionStyle,
  cardStyle,
  colors,
  fontStack,
  hudRingShadow,
  hudTextHighlight,
  mediaWindowShadow,
} from '../v4Styles';
import type {VisualEvent} from '../v4Types';

const iconMap = {
  AlignLeft,
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  BarChart3,
  Bot,
  BrainCircuit,
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  CheckCircle2,
  CircleX,
  ClipboardList,
  CreditCard,
  Cpu,
  ExternalLink,
  FileCheck2,
  FileText,
  FlaskConical,
  Folder,
  Globe2,
  GraduationCap,
  Hash,
  Image,
  Images,
  Landmark,
  Layers,
  Link2,
  ListChecks,
  MapPinned,
  MonitorUp,
  Network,
  Package,
  PackageCheck,
  PanelsTopLeft,
  Repeat2,
  Route,
  ScanSearch,
  Scale,
  SendHorizontal,
  ShieldCheck,
  Tags,
  TextCursorInput,
  TrendingUp,
  Trophy,
  UploadCloud,
  User,
  Users,
  Video,
  Workflow,
  Zap,
  Store,
};

type IconName = keyof typeof iconMap;

const PORTRAIT_FACE_SAFE_CENTER = {
  left: 290,
  right: 790,
  top: 360,
  bottom: 1260,
};

const PORTRAIT_TOP_SAFE = {
  top: 96,
  height: 300,
};

const PORTRAIT_RIGHT_RAIL = {
  right: 42,
  width: 360,
  top: 420,
};

const PORTRAIT_BOTTOM_CAPTION_RESERVED = 260;

const isPortraitCanvas = (width: number, height: number): boolean => height > width;

const shouldUsePortraitCompactHud = (event: VisualEvent, width: number, height: number): boolean => {
  if (!isPortraitCanvas(width, height)) return false;
  const placement = `${event.safeArea ?? ''} ${event.style ?? ''} ${event.motionType ?? ''}`.toLowerCase();
  return !placement.includes('full-panel') && !placement.includes('material-main') && !placement.includes('pip');
};

const semanticIconNameForEvent = (event: VisualEvent): IconName => {
  const role = event.semanticRole;
  const text = `${event.title ?? ''} ${event.text ?? ''} ${event.subtext ?? ''} ${event.status ?? ''}`;
  const hasAny = (terms: string[]) => terms.some((term) => text.includes(term));

  if (role === 'platform-fanout' || hasAny(['\u5e73\u53f0', '\u5206\u53d1', '\u6e20\u9053'])) return 'Network';
  if (role === 'automation-handoff' || hasAny(['\u81ea\u52a8', '\u6267\u884c', 'Codex', '\u7cfb\u7edf'])) return 'Bot';
  if (role === 'capability-share' || hasAny(['\u80fd\u529b', '\u4efd\u989d', '\u6392\u540d', '\u5360\u6bd4'])) return 'BarChart3';
  if (role === 'scene-lock' || hasAny(['\u573a\u666f', '\u7ed1\u5b9a', '\u652f\u4ed8', '\u9ad8\u8003', '\u653f\u52a1'])) return 'Link2';
  if (role === 'transformation-stack' || hasAny(['\u4e2a\u4eba', '\u56e2\u961f', '\u6760\u6746', '\u62a4\u57ce\u6cb3', '\u8f6c\u53d8'])) return 'ArrowRight';
  if (role === 'manual-field' || hasAny(['\u586b\u5199', '\u5b57\u6bb5', '\u6807\u9898', '\u7b80\u4ecb', '\u6807\u7b7e', '\u5c01\u9762'])) return 'ClipboardList';
  if (role === 'semantic-problem-map' || hasAny(['\u4e0d\u662f', '\u800c\u662f', '\u74f6\u9888', '\u98ce\u9669', '\u9519\u8bef'])) return 'AlertTriangle';
  if (role === 'proof-focus' || role === 'proof-material' || hasAny(['\u8bc1\u660e', '\u6765\u6e90', '\u9a8c\u8bc1'])) return 'ShieldCheck';
  if (role === 'cta-resolve' || hasAny(['\u8bc4\u8bba', '\u884c\u52a8', '\u5165\u53e3'])) return 'BadgeCheck';
  if (hasAny(['\u6570\u636e', '\u6bd4\u4f8b', '\u589e\u957f', '\u6570\u5b57'])) return 'BarChart3';
  if (hasAny(['\u89c6\u9891', '\u7d20\u6750\u5305', '\u7d20\u6750'])) return 'Package';
  return 'Workflow';
};
const iconForEvent = (event: VisualEvent, fallback: IconName): (typeof iconMap)[IconName] => {
  const requested = event.iconName as IconName | undefined;
  return (requested ? iconMap[requested] : undefined) ?? iconMap[semanticIconNameForEvent(event)] ?? iconMap[fallback];
};

const iconForFieldStep = (step: NonNullable<VisualEvent['internalSteps']>[number]) => {
  const requested = step.iconName as IconName | undefined;
  if (requested && iconMap[requested]) return iconMap[requested];

  const text = `${step.label ?? ''} ${step.text ?? ''} ${step.value ?? ''}`.toLowerCase();
  if (text.includes('created') || text.includes('date') || text.includes('时间')) return CalendarDays;
  if (text.includes('dir') || text.includes('目录') || text.includes('文件夹') || text.includes('输出')) return Folder;
  if (text.includes('标签') || text.includes('tag')) return Tags;
  if (text.includes('封面') || text.includes('cover') || text.includes('image')) return Image;
  if (text.includes('简介') || text.includes('intro') || text.includes('description')) return AlignLeft;
  return FileText;
};

const clampFade = (local: number, duration: number) => {
  const fadeFrames = Math.min(22, Math.max(12, Math.floor(duration / 4)));
  const holdEnd = Math.max(fadeFrames + 1, duration - fadeFrames);

  return interpolate(local, [0, fadeFrames, holdEnd, duration], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
};

const splitTitle = (text = '') => text.trim().split(/\s+/).filter(Boolean);

const splitKineticTitleLines = (text = ''): string[] => {
  const clean = text.trim();
  if (!clean) return [];
  if (clean.includes('\n')) {
    return clean.split(/\n+/).map((line) => line.trim()).filter(Boolean).slice(0, 3);
  }
  const words = clean.split(/\s+/).filter(Boolean);
  if (words.length === 2) return words;
  if (words.length > 2) return [words.slice(0, -1).join(' '), words[words.length - 1]];

  const brandMatch = clean.match(/^(Codex|OpenAI|Claude|GPT|AI)(.+)$/i);
  if (brandMatch && brandMatch[2]?.trim()) return [brandMatch[1], brandMatch[2].trim()];

  const anchors = ['不是', '别再', '自动', '离谱', '流程', '主图', '分发', '接管'];
  for (const anchor of anchors) {
    const index = clean.indexOf(anchor);
    if (index > 0 && index < clean.length - 1) {
      return [clean.slice(0, index), clean.slice(index)];
    }
  }

  if (clean.length <= 6) return [clean];
  if (clean.length <= 10) return [clean.slice(0, 4), clean.slice(4)];
  return [clean.slice(0, 5), clean.slice(5, 11), clean.slice(11)].filter(Boolean);
};

const emphasisWordsForEvent = (event: VisualEvent): string[] => {
  const words = Array.isArray(event.emphasisWords) ? event.emphasisWords : [];
  if (words.length > 0) return words.filter(Boolean).slice(0, 3);
  return [event.subtext ?? ''].filter(Boolean).slice(0, 1);
};

const titleEmphasisWordsForEvent = (event: VisualEvent): string[] => {
  const title = event.text ?? '';
  const explicit = (Array.isArray(event.emphasisWords) ? event.emphasisWords : []).filter((word) => word && title.includes(word));
  if (explicit.length > 0) return explicit.slice(0, 1);
  const negativeTerms = ['手动', '别再', '不是', '不够分', '重复', '低效', '风险'];
  const inferred = [
    '自动化',
    'Codex',
    '手动',
    '主图',
    '自动',
    '生成',
    '分发',
    '平台',
    '流程',
    '执行',
    '有用',
    '还没有开始',
    '大爆发',
  ].filter((word) => title.includes(word));
  const candidates = [...new Set([...explicit, ...inferred])].sort((a, b) => title.indexOf(a) - title.indexOf(b));
  const negative = candidates.find((word) => negativeTerms.some((term) => word.includes(term)));
  return (negative ? [negative] : candidates.slice(0, 1)).filter(Boolean);
};

const colorForTitleEmphasis = (word: string, event: VisualEvent): string => {
  if ((event.style ?? '').includes('contrarian-hook') || event.semanticRole === 'contrarian-hook') return colors.blue;
  if (['手动', '别再', '不是', '不够分', '重复', '低效', '风险'].some((term) => word.includes(term))) return colors.red;
  if (['主图', '流程', '分发', '平台', '素材包'].some((term) => word.includes(term))) return colors.blue;
  if (['自动化', '自动', '生成', 'Codex', '执行', '有用'].some((term) => word.includes(term))) return colors.green;
  return event.semanticRole === 'negative-friction' ? colors.red : colors.green;
};

const splitByEmphasis = (text: string, words: string[]): string[] => {
  return words.reduce<string[]>((segments, word) => {
    return segments.flatMap((segment) => {
      if (!word || !segment.includes(word)) return [segment];
      const parts = segment.split(word);
      return parts.flatMap((part, index) => (index === parts.length - 1 ? [part] : [part, word]));
    });
  }, [text]).filter((part) => part.length > 0);
};

const compactHudText = (text = '', maxChars = 18): string => {
  const clean = text
    .replace(/\s+/g, '')
    .replace(/[，。？！、；：,.!?;:]/g, '')
    .replace(/而是你把/g, '把')
    .replace(/而是/g, '')
    .replace(/一个/g, '')
    .replace(/好看的/g, '')
    .replace(/了一张/g, '一张')
    .replace(/变成了一条/g, '变成')
    .replace(/变成一条/g, '变成');
  if (clean.includes('不是')) {
    const index = clean.indexOf('不是');
    return clean.slice(index, index + maxChars);
  }
  if (clean.length <= maxChars) return clean;
  const anchors = ['而是', '手动', '自动化', '工作流', '重复', '不值得', '不用再'];
  for (const anchor of anchors) {
    const index = clean.indexOf(anchor);
    if (index >= 0) return clean.slice(index, index + maxChars);
  }
  return clean.slice(0, maxChars);
};

const inferEmphasis = (text: string, fallback: string[], maxChars = 8): string => {
  const fallbackHit = fallback.find((item) => text.includes(item));
  if (fallbackHit) return fallbackHit;
  for (const marker of ['不是', '而是']) {
    const index = text.indexOf(marker);
    if (index >= 0) {
      const tail = text.slice(index + marker.length).replace(/[，。？！、；：,.!?;:]/g, '');
      if (tail) return tail.slice(0, maxChars);
    }
  }
  return '';
};

const emphasisScale = (local: number, fps: number, delay = 34): number => {
  const pop = spring({
    frame: Math.max(0, local - delay),
    fps,
    config: {damping: 12, stiffness: 190},
  });
  const window = interpolate(local - delay, [0, 10, 24, 36], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return 1 + interpolate(pop, [0, 1], [0, 0.16]) * window;
};

const numericPattern = /([+-]?\d+(?:\.\d+)?)/;

const inferNumericTarget = (event: VisualEvent) => {
  const raw = `${event.title ?? ''} ${event.text ?? ''} ${event.subtext ?? ''} ${event.status ?? ''}`;
  const match = raw.match(numericPattern);
  const value = typeof event.numericValue === 'number' ? event.numericValue : match ? Number(match[1]) : 0;
  const prefix = event.numericPrefix ?? (raw.includes('+') && value > 0 ? '+' : '');
  const suffix = event.numericSuffix ?? (raw.includes('%') ? '%' : raw.includes('\u500d') ? '\u500d' : raw.includes('\u4e07') ? '\u4e07' : '');
  const decimals = Math.abs(value) > 0 && Math.abs(value) < 1 ? 2 : Number.isInteger(value) ? 0 : 1;
  return {value, prefix, suffix, decimals};
};

const formatCount = (value: number, decimals: number) =>
  decimals > 0 ? value.toFixed(decimals).replace(/\.0+$/, '') : String(Math.round(value));

export const CornerChapterLabel: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const local = frame - event.startFrame;
  const duration = event.endFrame - event.startFrame;
  const opacity = clampFade(local, duration);
  const x = interpolate(local, [0, 18], [-14, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        left: 34,
        top: 58,
        opacity,
        transform: `translateX(${x}px)`,
        display: 'flex',
        alignItems: 'flex-start',
        gap: 13,
        fontFamily: fontStack,
        textShadow: hudTextHighlight,
        pointerEvents: 'none',
        maxWidth: 430,
      }}
    >
      <div
        style={{
          width: 4,
          height: 56,
          marginTop: 1,
          borderRadius: 2,
          background: colors.blue,
          boxShadow: '0 8px 22px rgba(0,0,0,0.46)',
        }}
      />
      <div>
        <div
          style={{
            color: colors.blue,
            fontSize: 24,
            fontWeight: 950,
            lineHeight: 1,
            letterSpacing: 0,
          }}
        >
          {event.text}
        </div>
        {event.subtext ? (
          <div
            style={{
              marginTop: 7,
              color: colors.white,
              fontSize: 24,
              fontWeight: 950,
              lineHeight: 1,
              letterSpacing: 0,
              display: 'flex',
              alignItems: 'center',
              gap: 9,
            }}
          >
            <span
              style={{
                width: 22,
                height: 2,
                borderRadius: 2,
                background: 'rgba(255,255,255,0.88)',
                boxShadow: '0 6px 16px rgba(0,0,0,0.42)',
              }}
            />
            {event.subtext}
          </div>
        ) : null}
      </div>
    </div>
  );
};

export const V4Caption: React.FC<{text: string; highlightWords: string[]}> = ({
  text,
  highlightWords: _highlightWords,
}) => {
  const {width, height} = useVideoConfig();
  const isPortrait = height > width;
  const weightedLength = Array.from(text).reduce((total, char) => {
    if (/\s/.test(char)) return total + 0.35;
    if (/[\x00-\x7F]/.test(char)) return total + 0.58;
    if (/[，。！？、：；（）《》“”]/.test(char)) return total + 0.45;
    return total + 1;
  }, 0);
  const fontSize = isPortrait
    ? Math.max(weightedLength > 62 ? 22 : 28, Math.min(38, Math.floor(1280 / Math.max(weightedLength, 1))))
    : Math.max(20, Math.min(36, Math.floor(1840 / Math.max(weightedLength, 1))));
  const horizontalPadding = isPortrait ? 24 : weightedLength > 58 ? 18 : weightedLength > 46 ? 22 : 28;
  return (
    <div
      style={{
        ...captionStyle,
        fontSize,
        padding: isPortrait ? `14px ${horizontalPadding}px` : `10px ${horizontalPadding}px`,
        maxWidth: isPortrait ? 960 : 1760,
        whiteSpace: isPortrait ? 'normal' : 'nowrap',
      }}
    >
      <span style={{color: colors.white}}>{text}</span>
    </div>
  );
};

export const KineticTitle: React.FC<{
  event: VisualEvent;
  align?: 'left' | 'center';
}> = ({event, align = 'left'}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const isPortrait = height > width;
  const local = frame - event.startFrame;
  const duration = event.endFrame - event.startFrame;
  const enter = spring({frame: local, fps, config: {damping: 18, stiffness: 125}});
  const opacity = clampFade(local, duration);
  const baseScale =
    event.motionType === 'word-pop'
      ? interpolate(enter, [0, 1], [0.86, 1])
      : interpolate(enter, [0, 0.72, 1], [1.18, 0.96, 1]);
  const isNegative = event.semanticRole === 'negative-friction' || (event.style ?? '').includes('negative');
  const isDelayedSubline = (event.style ?? '').includes('delayed-subline') || isNegative;
  const isCtaAction = (event.style ?? '').includes('cta-action-entry');
  const isCtaTitle = event.type === 'ctaTitle';
  const isContrarianHook = (event.style ?? '').includes('contrarian-hook') || event.semanticRole === 'contrarian-hook';
  const sublineProgress = interpolate(local, [40, 54], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaSublineProgress = interpolate(local, [18, 34], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaStatusProgress = interpolate(local, [32, 52], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const words = event.motionType === 'word-pop' ? splitTitle(event.text) : [];
  const emphasisWords = emphasisWordsForEvent(event);
  const titleEmphasisWords = titleEmphasisWordsForEvent(event);
  const titleLines = splitKineticTitleLines(event.text ?? '');
  const ctaSummaryRows = (event.internalSteps ?? []).slice(0, 3);
  const isCtaSummary = isCtaTitle && (((event.style ?? '').includes('cta-summary')) || ctaSummaryRows.length >= 2);
  const maxLineLength = titleLines.reduce((max, line) => Math.max(max, line.length), 1);
  const stackedFontSize = isCtaAction
    ? isPortrait ? 70 : 88
    : align === 'center'
      ? Math.max(isPortrait ? 46 : 54, Math.min(isPortrait ? 68 : 72, Math.floor((isPortrait ? 620 : 720) / maxLineLength)))
      : Math.max(isPortrait ? 58 : 72, Math.min(isPortrait ? 90 : 104, Math.floor((isPortrait ? 650 : 760) / maxLineLength)));

  if (isContrarianHook) {
    return (
      <div
        style={{
          position: 'absolute',
          left: isPortrait ? 58 : 82,
          top: isPortrait ? 210 : 104,
          width: isPortrait ? 900 : 980,
          opacity,
          transform: `scale(${baseScale})`,
          transformOrigin: 'left center',
          fontFamily: fontStack,
          textAlign: 'left',
          color: colors.white,
          textShadow: hudTextHighlight,
          pointerEvents: 'none',
        }}
      >
        <div style={{fontSize: isPortrait ? 74 : 82, fontWeight: 950, lineHeight: 1.02, letterSpacing: 0}}>
          {titleLines.map((line, lineIndex) => {
            const lineParts = splitByEmphasis(line, titleEmphasisWords);
            return (
              <div key={`${line}-${lineIndex}`} style={{display: 'block', marginTop: lineIndex === 0 ? 0 : 2}}>
                {lineParts.map((part, partIndex) => {
                  const emphasized = titleEmphasisWords.includes(part);
                  return (
                    <span
                      key={`${part}-${partIndex}`}
                      style={{
                        display: emphasized ? 'inline-block' : undefined,
                        color: emphasized ? colorForTitleEmphasis(part, event) : colors.white,
                        transform: emphasized ? `scale(${emphasisScale(local, fps, 32 + lineIndex * 4 + partIndex * 3)})` : undefined,
                        transformOrigin: 'center bottom',
                      }}
                    >
                      {part}
                    </span>
                  );
                })}
              </div>
            );
          })}
        </div>
        {event.status ? (
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginTop: 24,
              minWidth: 148,
              height: 56,
              padding: '0 26px',
              borderRadius: 12,
              color: colors.red,
              fontSize: 31,
              fontWeight: 950,
              lineHeight: 1,
              background: 'rgba(20,8,8,0.62)',
              boxShadow: `${hudRingShadow}, inset 0 0 0 2px rgba(216,60,48,0.92)`,
              opacity: ctaStatusProgress,
              transform: `translateY(${interpolate(ctaStatusProgress, [0, 1], [14, 0])}px)`,
            }}
          >
            {event.status}
          </div>
        ) : null}
        {event.subtext ? (
          <div
            style={{
              marginTop: 16,
              color: colors.white,
              fontSize: 30,
              fontWeight: 900,
              lineHeight: 1.15,
              opacity: sublineProgress,
              transform: `translateY(${interpolate(sublineProgress, [0, 1], [14, 0])}px)`,
            }}
          >
            {event.subtext}
          </div>
        ) : null}
      </div>
    );
  }

  if (isCtaSummary) {
    return (
      <div
        style={{
          position: 'absolute',
          left: isPortrait ? width - PORTRAIT_RIGHT_RAIL.right - (PORTRAIT_RIGHT_RAIL.width + 20) : 96,
          top: isPortrait ? PORTRAIT_TOP_SAFE.top + PORTRAIT_TOP_SAFE.height : 126,
          width: isPortrait ? PORTRAIT_RIGHT_RAIL.width + 20 : 660,
          opacity,
          transform: `scale(${baseScale})`,
          transformOrigin: 'left center',
          fontFamily: fontStack,
          textAlign: 'left',
          color: colors.white,
          textShadow: hudTextHighlight,
        }}
      >
        <div style={{color: colors.blue, fontSize: 28, fontWeight: 950, lineHeight: 1, letterSpacing: 0}}>
          {event.status ?? 'ACTION SUMMARY'}
        </div>
        <div style={{marginTop: 18, fontSize: isPortrait ? 40 : 60, fontWeight: 950, lineHeight: 1.04, letterSpacing: 0}}>
          {event.text}
        </div>
        {event.subtext ? (
          <div
            style={{
              marginTop: 12,
              color: colors.muted,
              fontSize: isPortrait ? 21 : 26,
              fontWeight: 900,
              lineHeight: 1.15,
              opacity: ctaSublineProgress,
              transform: `translateY(${interpolate(ctaSublineProgress, [0, 1], [14, 0])}px)`,
            }}
          >
            {event.subtext}
          </div>
        ) : null}
        <div style={{marginTop: isPortrait ? 24 : 32, width: isPortrait ? PORTRAIT_RIGHT_RAIL.width + 20 : 620, display: 'grid', gap: 12}}>
          {ctaSummaryRows.map((step, index) => {
            const rowProgress = spring({
              frame: Math.max(0, local - 24 - index * 9),
              fps,
              config: {damping: 18, stiffness: 130},
            });
            const rowOpacity = interpolate(local - 24 - index * 9, [0, 12], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            const valueColor = index === 1 ? colors.amber : colors.green;
            const labelText = (step.label ?? `方向 ${String(index + 1).padStart(2, '0')}`).replace(/^方向\s*/, '');
            return (
              <div
                key={`${step.label ?? step.text}-${index}`}
                style={{
                  height: isPortrait ? 52 : 58,
                  borderRadius: 12,
                  display: 'grid',
                  gridTemplateColumns: isPortrait ? '62px minmax(0, 1fr) 74px' : '72px minmax(0, 1fr) 108px',
                  alignItems: 'center',
                  columnGap: 18,
                  padding: '0 22px',
                  background: 'rgba(255,255,255,0.055)',
                  boxShadow: '0 18px 36px rgba(0,0,0,0.34)',
                  opacity: rowOpacity,
                  transform: `translateY(${interpolate(rowProgress, [0, 1], [14, 0])}px)`,
                }}
              >
                <div style={{color: colors.blue, fontSize: isPortrait ? 16 : 22, fontWeight: 950}}>
                  {labelText}
                </div>
                <div style={{color: colors.white, fontSize: isPortrait ? 19 : 24, fontWeight: 950, whiteSpace: 'nowrap', overflow: 'hidden'}}>
                  {step.text ?? step.value ?? ''}
                </div>
                <div style={{color: valueColor, fontSize: isPortrait ? 16 : 22, fontWeight: 950, textAlign: 'right', whiteSpace: 'nowrap'}}>
                  {step.status ?? step.value ?? ''}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  if (isCtaTitle) {
    const ctaParts = splitByEmphasis(event.text ?? '', emphasisWords);
    return (
      <div
        style={{
          position: 'absolute',
          left: isPortrait ? 60 : 96,
          top: isPortrait ? 220 : 138,
          width: isPortrait ? 900 : 760,
          opacity,
          transform: `scale(${baseScale})`,
          transformOrigin: 'left center',
          fontFamily: fontStack,
          textAlign: 'left',
          color: colors.white,
          textShadow: hudTextHighlight,
        }}
      >
        <div style={{fontSize: isPortrait ? 72 : 78, fontWeight: 950, lineHeight: 0.92, letterSpacing: 0}}>
          {ctaParts.map((part, index) => {
            const emphasized = emphasisWords.includes(part);
            return (
              <span
                key={`${part}-${index}`}
                style={{
                  display: emphasized ? 'inline-block' : undefined,
                  color: emphasized ? colors.green : colors.white,
                  transform: emphasized ? `scale(${emphasisScale(local, fps, 34 + index * 4)})` : undefined,
                  transformOrigin: 'center bottom',
                }}
              >
                {part}
              </span>
            );
          })}
        </div>
        {event.subtext ? (
          <div
            style={{
              marginTop: 12,
              fontSize: 30,
              fontWeight: 900,
              lineHeight: 1.12,
              color: colors.white,
              opacity: ctaSublineProgress,
              transform: `translateY(${interpolate(ctaSublineProgress, [0, 1], [14, 0])}px)`,
            }}
          >
            {event.subtext}
          </div>
        ) : null}
        {event.status ? (
          <div
            style={{
              marginTop: 28,
              width: isPortrait ? 640 : 560,
              padding: '18px 24px',
              borderRadius: 14,
              background: 'rgba(4,28,23,0.78)',
              boxShadow: hudRingShadow,
              color: colors.green,
              fontSize: 31,
              fontWeight: 950,
              lineHeight: 1,
              opacity: ctaStatusProgress,
              transform: `translateY(${interpolate(ctaStatusProgress, [0, 1], [16, 0])}px)`,
            }}
          >
            {event.status}
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div
      style={{
        position: 'absolute',
        left: isCtaAction ? (isPortrait ? 58 : 96) : align === 'center' ? '50%' : isPortrait ? 58 : 116,
        top: isCtaAction ? (isPortrait ? 220 : 118) : align === 'center' ? (isPortrait ? 180 : 28) : isPortrait ? 230 : 136,
        maxWidth: isCtaAction ? (isPortrait ? 920 : 940) : align === 'center' ? (isPortrait ? 900 : 960) : isPortrait ? 900 : 1040,
        opacity,
        transform: isCtaAction
          ? `scale(${baseScale})`
          : align === 'center'
            ? `translateX(-50%) scale(${baseScale})`
            : `scale(${baseScale})`,
        transformOrigin: isCtaAction ? 'left center' : align === 'center' ? 'center center' : 'left center',
        fontFamily: fontStack,
        textAlign: isCtaAction ? 'left' : align,
        whiteSpace: 'pre-line',
        fontWeight: 950,
        fontSize: stackedFontSize,
        lineHeight: 1.04,
        letterSpacing: 0,
        color: colors.white,
        textShadow: hudTextHighlight,
      }}
    >
      {words.length > 0 ? (
        <div style={{display: 'flex', flexWrap: 'wrap', gap: 14, justifyContent: align === 'center' ? 'center' : 'flex-start'}}>
          {words.map((word, index) => {
            const pop = spring({
              frame: Math.max(0, local - index * 6),
              fps,
              config: {damping: 16, stiffness: 165},
            });
            const emphasized = titleEmphasisWords.includes(word);
            const secondary = emphasized ? emphasisScale(local, fps, 34 + index * 4) : 1;
            return (
              <span
                key={`${word}-${index}`}
                style={{
                  display: 'inline-block',
                  transform: `scale(${interpolate(pop, [0, 1], [0.78, 1]) * secondary})`,
                  color: emphasized ? colorForTitleEmphasis(word, event) : undefined,
                  opacity: interpolate(local - index * 6, [0, 10], [0, 1], {
                    extrapolateLeft: 'clamp',
                    extrapolateRight: 'clamp',
                  }),
                }}
              >
                {word}
              </span>
            );
          })}
        </div>
      ) : (
        <div>
          {titleLines.map((line, lineIndex) => {
            const lineParts = splitByEmphasis(line, titleEmphasisWords);
            return (
              <div
                key={`${line}-${lineIndex}`}
                style={{
                  display: 'block',
                  marginTop: lineIndex === 0 ? 0 : 4,
                  lineHeight: 0.96,
                }}
              >
                {lineParts.map((part, partIndex) => {
                  const emphasized = titleEmphasisWords.includes(part);
                  return (
                    <span
                      key={`${part}-${partIndex}`}
                      style={{
                        display: emphasized ? 'inline-block' : undefined,
                        transform: emphasized ? `scale(${emphasisScale(local, fps, 34 + lineIndex * 4 + partIndex * 3)})` : undefined,
                        transformOrigin: 'center bottom',
                        color: emphasized ? colorForTitleEmphasis(part, event) : undefined,
                      }}
                    >
                      {part}
                    </span>
                  );
                })}
              </div>
            );
          })}
        </div>
      )}
      {event.subtext ? (
        <div
          style={{
            marginTop: align === 'center' ? 12 : 20,
            color: colors.green,
            fontSize: isCtaAction ? 34 : align === 'center' ? 30 : 40,
            fontWeight: 950,
            letterSpacing: 0,
            textShadow: hudTextHighlight,
            display: isDelayedSubline || isCtaAction ? 'block' : 'inline-block',
            opacity: isDelayedSubline || isCtaAction ? sublineProgress : 1,
            padding: isCtaAction ? '14px 18px' : undefined,
            borderRadius: isCtaAction ? 12 : undefined,
            background: isCtaAction ? 'rgba(5,7,11,0.70)' : undefined,
            boxShadow: isCtaAction ? hudRingShadow : undefined,
            transform: `translateY(${isDelayedSubline || isCtaAction ? interpolate(sublineProgress, [0, 1], [18, 0]) : 0}px) scale(${
              emphasisWords.includes(event.subtext) ? emphasisScale(local, fps, 58) : 1
            })`,
            transformOrigin: 'left center',
          }}
        >
          {event.subtext}
        </div>
      ) : null}
    </div>
  );
};

export const InfoCard: React.FC<{
  event: VisualEvent;
  index: number;
  variant?: 'left' | 'right' | 'material';
}> = ({event, index, variant = 'left'}) => {
  const frame = useCurrentFrame();
  const {fps, width: canvasWidth, height: canvasHeight} = useVideoConfig();
  const isPortrait = canvasHeight > canvasWidth;
  const local = frame - event.startFrame;
  const progress = spring({frame: local - index * 6, fps, config: {damping: 22, stiffness: 105}});
  const opacity = clampFade(local, event.endFrame - event.startFrame);
  const x = interpolate(progress, [0, 1], [variant === 'right' ? 48 : -48, 0]);
  const Icon = iconForEvent(event, 'Workflow');
  const isManualField = event.semanticRole === 'manual-field';
  const left = isManualField
    ? isPortrait ? 442 : 1236
    : variant === 'right' ? (isPortrait ? 560 : 1264) : variant === 'material' ? (isPortrait ? 56 : 92) : (isPortrait ? 56 : 94);
  const top = isManualField
    ? isPortrait ? 210 + index * 96 : 188 + index * 106
    : variant === 'material' ? (isPortrait ? 650 + index * 108 : 250 + index * 116) : (isPortrait ? 620 + index * 112 : 286 + index * 124);
  const width = isManualField ? (isPortrait ? 580 : 540) : variant === 'right' ? (isPortrait ? 440 : 486) : (isPortrait ? 900 : 500);
  const accent = index === 0 ? colors.amber : index === 1 ? colors.red : colors.green;

  if (isManualField) {
    const rawFields = (event.subtext || event.text || '标题 / 简介 / 标签')
      .split(/[\/、,，]+/)
      .map((item) => item.trim())
      .filter(Boolean)
      .slice(0, 3);
    const defaultRows: NonNullable<VisualEvent['internalSteps']> = rawFields.length > 0 ? rawFields.map((field, rowIndex) => ({
      label: field,
      text: field.includes('标题') ? '生成标题' : field.includes('简介') ? '压缩简介' : field.includes('标签') ? '补齐标签' : field,
      status: rowIndex >= 2 ? '执行中' : '完成',
    })) : [
      {label: 'request.json', text: 'request.json', status: '完成', iconName: 'FileText'},
      {label: 'created_at', text: 'created_at', status: '完成', iconName: 'CalendarDays'},
      {label: 'output_dir', text: 'output_dir', status: '执行中', iconName: 'Folder'},
    ];
    const rows = (event.internalSteps && event.internalSteps.length > 0 ? event.internalSteps : defaultRows).slice(0, 3);
    const statusNodes = rows.slice(0, 4).map((step, nodeIndex) => ({
      label: compactHudText(step.label ?? step.text ?? `字段 ${nodeIndex + 1}`, 6),
      state: String(step.status ?? '').includes('执行') || String(step.status ?? '').includes('生成') ? 'active' : 'done',
    }));
    return (
      <div
        style={{
          position: 'absolute',
          right: isPortrait ? 42 : 58,
          top: isPortrait ? 106 : 70,
          width: isPortrait ? 590 : 700,
          minHeight: 650,
          opacity,
          transform: `translateX(${x}px)`,
          fontFamily: fontStack,
          color: colors.white,
          textShadow: hudTextHighlight,
          pointerEvents: 'none',
        }}
      >
        <div style={{position: 'absolute', right: 0, top: 0, width: isPortrait ? 560 : 640}}>
          <div style={{color: colors.blue, fontSize: 29, fontWeight: 950, lineHeight: 1, letterSpacing: 0}}>
            状态进度
          </div>
          <div style={{position: 'relative', marginTop: isPortrait ? 38 : 30, height: 90}}>
            <div
              style={{
                position: 'absolute',
                left: isPortrait ? 42 : 34,
                right: isPortrait ? 42 : 34,
                top: 50,
                height: 5,
                borderRadius: 999,
                background: 'rgba(210,214,220,0.72)',
                boxShadow: '0 10px 22px rgba(0,0,0,0.36)',
              }}
            />
            <div
              style={{
                position: 'absolute',
                left: isPortrait ? 42 : 34,
                top: 50,
                width: isPortrait ? 150 : 154,
                height: 5,
                borderRadius: 999,
                background: colors.green,
              }}
            />
            {statusNodes.map((node, nodeIndex) => {
              const leftPercent = statusNodes.length <= 1 ? 0 : (nodeIndex / (statusNodes.length - 1)) * 100;
              const isDone = node.state === 'done';
              const isActive = node.state === 'active';
              return (
                <div
                  key={node.label}
                  style={{
                    position: 'absolute',
                    left: `${leftPercent}%`,
                    top: 0,
                    transform: 'translateX(-50%)',
                    width: 118,
                    textAlign: 'center',
                  }}
                >
                  <div style={{fontSize: 25, fontWeight: 950, lineHeight: 1, color: colors.white}}>
                    {node.label}
                  </div>
                  <div
                    style={{
                      position: 'absolute',
                      left: '50%',
                      top: 38,
                      width: isActive ? 30 : 27,
                      height: isActive ? 30 : 27,
                      borderRadius: 999,
                      transform: 'translateX(-50%)',
                      display: 'grid',
                      placeItems: 'center',
                      color: isDone ? colors.black : colors.white,
                      background: isDone ? colors.green : isActive ? colors.blue : 'rgba(72,76,84,0.95)',
                      border: isActive ? '3px solid rgba(238,247,255,0.88)' : '3px solid rgba(216,220,226,0.78)',
                      boxShadow: '0 14px 28px rgba(0,0,0,0.44)',
                    }}
                  >
                    {isDone ? <Check size={19} strokeWidth={3.4} /> : null}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div style={{position: 'absolute', right: 0, top: isPortrait ? 360 : 324, width: isPortrait ? 420 : 430}}>
          <div style={{display: 'flex', alignItems: 'flex-start', gap: 16}}>
            <div
              style={{
                width: 5,
                height: isPortrait ? 304 : 302,
                marginTop: 1,
                borderRadius: 3,
                background: colors.blue,
                boxShadow: '0 9px 24px rgba(0,0,0,0.52)',
              }}
            />
            <div>
              <div style={{color: colors.blue, fontSize: 25, fontWeight: 950, lineHeight: 1, letterSpacing: 0}}>
                字段
              </div>
              <div style={{marginTop: 24, color: colors.white, fontSize: 40, fontWeight: 950, lineHeight: 1}}>
                {event.title ?? 'request / created'}
              </div>
            </div>
          </div>

          <div style={{position: 'absolute', left: 22, top: 112, width: isPortrait ? 398 : 410, display: 'grid', gap: 14}}>
          {rows.map((step, rowIndex) => {
            const rowProgress = spring({
              frame: Math.max(0, local - 12 - rowIndex * 8),
              fps,
              config: {damping: 18, stiffness: 130},
            });
            const rowOpacity = interpolate(local - 12 - rowIndex * 8, [0, 12], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            const status = step.status ?? (rowIndex >= rows.length - 1 ? '执行中' : '完成');
            const normalizedStatus = status.toLowerCase();
            const isInProgress =
              status.includes('执行') ||
              status.includes('生成') ||
              status.includes('处理') ||
              normalizedStatus.includes('active') ||
              normalizedStatus.includes('running') ||
              normalizedStatus.includes('pending') ||
              normalizedStatus.includes('progress');
            const statusColor = isInProgress ? colors.blue : colors.green;
            const RowIcon = iconForFieldStep(step);
            return (
              <div
                key={`${step.label ?? step.text}-${rowIndex}`}
                style={{
                  height: 50,
                  borderRadius: 5,
                  display: 'grid',
                  gridTemplateColumns: '46px minmax(0, 1fr) 92px',
                  alignItems: 'center',
                  columnGap: 12,
                  padding: '0 16px',
                  background: 'rgba(5,7,11,0.66)',
                  boxShadow: '0 18px 38px rgba(0,0,0,0.46), 0 5px 14px rgba(0,0,0,0.34)',
                  opacity: rowOpacity,
                  transform: `translateY(${interpolate(rowProgress, [0, 1], [14, 0])}px)`,
                }}
              >
                <div style={{color: colors.blue, display: 'grid', placeItems: 'center'}}>
                  <RowIcon size={28} strokeWidth={2.4} />
                </div>
                <div style={{color: colors.white, fontSize: 24, fontWeight: 950, whiteSpace: 'nowrap', overflow: 'hidden'}}>
                  {step.text ?? step.value ?? step.label ?? ''}
                </div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'flex-end',
                    gap: 14,
                    color: statusColor,
                    fontSize: 22,
                    fontWeight: 950,
                    textAlign: 'right',
                    whiteSpace: 'nowrap',
                  }}
                >
                  <span
                    style={{
                      width: 11,
                      height: 11,
                      borderRadius: 999,
                      background: statusColor,
                      boxShadow: '0 8px 16px rgba(0,0,0,0.34)',
                      flex: '0 0 auto',
                    }}
                  />
                  {isInProgress ? (
                    <span>{status}</span>
                  ) : (
                    <Check size={28} strokeWidth={3.4} />
                  )}
                </div>
              </div>
            );
          })}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        ...cardStyle,
        position: 'absolute',
        left,
        top,
        width,
        minHeight: 104,
        padding: '22px 26px',
        display: 'flex',
        alignItems: 'center',
        gap: 18,
        opacity,
        transform: `translateX(${x}px)`,
        borderLeft: undefined,
        boxShadow: hudRingShadow,
      }}
    >
      <div
        style={{
          width: 58,
          height: 58,
          borderRadius: 14,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
          color: isManualField ? accent : colors.green,
          background: isManualField ? 'rgba(255,255,255,0.08)' : 'rgba(16,163,127,0.12)',
          boxShadow: isManualField ? undefined : '0 10px 22px rgba(0,0,0,0.32)',
          flex: '0 0 auto',
        }}
      >
        <Icon size={33} strokeWidth={2.4} />
      </div>
      <div style={{minWidth: 0, flex: 1}}>
        <div style={{fontSize: 34, fontWeight: 950, lineHeight: 1.12, overflowWrap: 'break-word', textShadow: hudTextHighlight}}>
          {event.title ?? event.text}
        </div>
        {event.status ? (
          <div
            style={{
              display: 'inline-block',
              marginTop: 7,
              padding: '3px 9px',
              borderRadius: 999,
              background: 'rgba(6,126,246,0.16)',
              color: colors.blue,
              fontSize: 17,
              fontWeight: 900,
              letterSpacing: 0,
              textShadow: hudTextHighlight,
            }}
          >
            {event.status}
          </div>
        ) : null}
      </div>
    </div>
  );
};

export const StatusSticker: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const local = frame - event.startFrame;
  const {fps, width: canvasWidth, height: canvasHeight} = useVideoConfig();
  const isPortrait = canvasHeight > canvasWidth;
  const progress = spring({frame: local, fps, config: {damping: 16, stiffness: 150}});
  const opacity = clampFade(local, event.endFrame - event.startFrame);
  const Icon = iconForEvent(event, 'BadgeCheck');
  const isHudLabel = event.motionType === 'hud-slide-fade' || event.semanticRole === 'chapter-label' || event.semanticRole === 'proof-focus';
  const placement = `${event.safeArea ?? ''} ${event.style ?? ''}`.toLowerCase();
  const isTopRight = placement.includes('top-right');

  if (isHudLabel) {
    const x = interpolate(local, [0, 12], [isTopRight ? 18 : -18, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    return (
      <div
        style={{
          position: 'absolute',
          left: isTopRight ? undefined : 46,
          right: isTopRight ? 46 : undefined,
          top: 34,
          maxWidth: isPortrait ? 440 : 520,
          opacity,
          transform: `translateX(${x}px)`,
          fontFamily: fontStack,
          letterSpacing: 0,
          textShadow: hudTextHighlight,
          textAlign: isTopRight ? 'right' : 'left',
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', justifyContent: isTopRight ? 'flex-end' : 'flex-start', gap: 8, color: colors.blue, fontSize: 19, fontWeight: 950, textShadow: hudTextHighlight}}>
          <Icon size={18} strokeWidth={2.5} />
          {event.text}
        </div>
        <div style={{marginTop: 5, color: colors.white, fontSize: 16, fontWeight: 800, textShadow: hudTextHighlight}}>
          {event.status}
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        position: 'absolute',
        left: isPortrait ? 58 : 112,
        top: isPortrait ? 260 : 250,
        transform: `rotate(-5deg) scale(${interpolate(progress, [0, 1], [0.82, 1])})`,
        transformOrigin: 'left center',
        opacity,
        display: 'flex',
        alignItems: 'center',
        gap: 18,
        padding: '22px 30px',
        borderRadius: 18,
        background: 'rgba(216,60,48,0.92)',
        color: colors.white,
        fontFamily: fontStack,
        fontSize: isPortrait ? 44 : 54,
        fontWeight: 950,
        boxShadow: `${hudRingShadow}, 0 20px 55px rgba(0,0,0,0.38)`,
        textShadow: hudTextHighlight,
      }}
    >
      <Icon size={50} strokeWidth={2.8} />
      <div>
        {event.text}
        <div style={{fontSize: 18, marginTop: 8, opacity: 0.9}}>{event.status}</div>
      </div>
    </div>
  );
};

export const DataPunch: React.FC<{event: VisualEvent; side?: 'left' | 'right'}> = ({
  event,
  side = 'left',
}) => {
  const frame = useCurrentFrame();
  const {fps, width: canvasWidth, height: canvasHeight} = useVideoConfig();
  const isPortrait = canvasHeight > canvasWidth;
  const local = frame - event.startFrame;
  const duration = event.endFrame - event.startFrame;
  const enter = spring({frame: local, fps, config: {damping: 18, stiffness: 120}});
  const opacity = clampFade(local, duration);
  const {value, prefix, suffix, decimals} = inferNumericTarget(event);
  const countFrames = Math.max(18, Math.min(52, Math.floor(duration * 0.48)));
  const counted = interpolate(local, [0, countFrames], [0, value], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const suffixPop = spring({frame: Math.max(0, local - countFrames + 5), fps, config: {damping: 14, stiffness: 165}});

  return (
    <div
      style={{
        position: 'absolute',
        left: side === 'left' ? (isPortrait ? 62 : 84) : undefined,
        right: side === 'right' ? (isPortrait ? 62 : 84) : undefined,
        top: isPortrait ? 300 : 152,
        width: isPortrait ? 900 : 690,
        minHeight: 286,
        fontFamily: fontStack,
        opacity,
        transform: `translate(${interpolate(enter, [0, 1], [side === 'left' ? -22 : 22, 0])}px, ${interpolate(enter, [0, 1], [22, 0])}px) scale(${interpolate(enter, [0, 1], [0.96, 1])})`,
        transformOrigin: side === 'left' ? 'left top' : 'right top',
        pointerEvents: 'none',
      }}
    >
      <div style={{display: 'flex', alignItems: 'center', gap: 12, color: colors.blue, fontSize: 20, fontWeight: 950, textShadow: hudTextHighlight}}>
        <TrendingUp size={22} strokeWidth={2.5} />
        <span>{event.status ?? '\u6570\u5b57\u6307\u6807'}</span>
      </div>
      <div
        style={{
          marginTop: 18,
          display: 'flex',
          alignItems: 'baseline',
          gap: 10,
          color: colors.white,
          textShadow: hudTextHighlight,
        }}
      >
        <span style={{fontSize: isPortrait ? 124 : 130, fontWeight: 950, lineHeight: 0.88}}>
          {prefix}
          {formatCount(counted, decimals)}
        </span>
        {suffix ? (
          <span
            style={{
              color: colors.blue,
              fontSize: isPortrait ? 58 : 66,
              fontWeight: 950,
              transform: `scale(${interpolate(suffixPop, [0, 1], [0.82, 1])})`,
              transformOrigin: 'left bottom',
            }}
          >
            {suffix}
          </span>
        ) : null}
      </div>
      <div style={{marginTop: 12, color: colors.white, fontSize: isPortrait ? 32 : 34, fontWeight: 950, lineHeight: 1.08, textShadow: hudTextHighlight}}>
        {event.text}
      </div>
      {event.subtext ? (
        <div style={{marginTop: 10, color: colors.muted, fontSize: 22, fontWeight: 900, lineHeight: 1.25, textShadow: hudTextHighlight}}>
          {event.subtext}
        </div>
      ) : null}
    </div>
  );
};

export const FlowListPanel: React.FC<{event: VisualEvent; side?: 'left' | 'right'}> = ({
  event,
  side = 'right',
}) => {
  const frame = useCurrentFrame();
  const {fps, width: canvasWidth, height: canvasHeight} = useVideoConfig();
  const isPortrait = canvasHeight > canvasWidth;
  const compact = shouldUsePortraitCompactHud(event, canvasWidth, canvasHeight);
  const local = frame - event.startFrame;
  const duration = event.endFrame - event.startFrame;
  const enter = spring({frame: local, fps, config: {damping: 22, stiffness: 100}});
  const opacity = clampFade(local, duration);
  const steps = (event.internalSteps && event.internalSteps.length > 0 ? event.internalSteps : [
    {label: '\u7ed3\u8bba', iconName: 'BadgeCheck'},
    {label: '\u6570\u636e', iconName: 'BarChart3'},
    {label: '\u884c\u52a8', iconName: 'SendHorizontal'},
  ]).slice(0, 6);

  return (
    <div
      style={{
        position: 'absolute',
        left: compact ? undefined : side === 'left' ? (isPortrait ? 60 : 82) : undefined,
        right: compact ? PORTRAIT_RIGHT_RAIL.right : side === 'right' ? (isPortrait ? 60 : 82) : undefined,
        top: compact ? 620 : isPortrait ? 760 : 136,
        width: compact ? PORTRAIT_RIGHT_RAIL.width : isPortrait ? 900 : 650,
        padding: compact ? '22px 24px' : '34px 38px',
        borderRadius: compact ? 14 : 16,
        background: colors.panel,
        boxShadow: hudRingShadow,
        opacity,
        transform: `translateX(${interpolate(enter, [0, 1], [side === 'left' ? -34 : 34, 0])}px)`,
        fontFamily: fontStack,
        pointerEvents: 'none',
      }}
    >
      <div style={{color: colors.blue, fontSize: compact ? 16 : 19, fontWeight: 950, textShadow: hudTextHighlight}}>
        {event.status ?? '\u6d41\u7a0b\u5217\u8868'}
      </div>
      <div style={{marginTop: compact ? 8 : 9, color: colors.white, fontSize: compact ? 30 : 44, fontWeight: 950, lineHeight: 1.08, textShadow: hudTextHighlight}}>
        {event.title ?? event.text}
      </div>
      <div style={{marginTop: compact ? 18 : 26, display: 'grid', gap: compact ? 12 : 18}}>
        {steps.map((step, index) => {
          const Icon = iconMap[(step.iconName as IconName) || 'Workflow'] ?? Workflow;
          const itemProgress = spring({frame: Math.max(0, local - 12 - index * 10), fps, config: {damping: 18, stiffness: 130}});
          const itemOpacity = interpolate(local - 12 - index * 10, [0, 12], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          return (
            <div
              key={`${step.label ?? step.text}-${index}`}
              style={{
                display: 'grid',
                gridTemplateColumns: compact ? '42px 38px 1fr' : '62px 50px 1fr',
                alignItems: 'center',
                gap: 10,
                opacity: itemOpacity,
                transform: `translateY(${interpolate(itemProgress, [0, 1], [12, 0])}px)`,
              }}
            >
              <div style={{color: colors.blue, fontSize: compact ? 24 : 34, fontWeight: 950, textShadow: hudTextHighlight}}>
                {String(index + 1).padStart(2, '0')}
              </div>
              <div style={{width: compact ? 34 : 44, height: compact ? 34 : 44, borderRadius: compact ? 9 : 11, display: 'grid', placeItems: 'center', background: 'rgba(6,126,246,0.13)', color: colors.blue, boxShadow: '0 12px 22px rgba(0,0,0,0.32)'}}>
                <Icon size={compact ? 20 : 25} strokeWidth={2.4} />
              </div>
              <div>
                <div style={{color: colors.white, fontSize: compact ? 20 : 28, fontWeight: 950, lineHeight: 1.1, textShadow: hudTextHighlight}}>
                  {step.label ?? step.text}
                </div>
                {step.status ? (
                  <div style={{marginTop: 4, color: colors.muted, fontSize: compact ? 13 : 16, fontWeight: 850, textShadow: hudTextHighlight}}>
                    {step.status}
                  </div>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const SemanticProblemMap: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const isPortrait = height > width;
  const compact = shouldUsePortraitCompactHud(event, width, height);
  const local = frame - event.startFrame;
  const duration = event.endFrame - event.startFrame;
  const enter = spring({frame: local, fps, config: {damping: 20, stiffness: 120}});
  const opacity = clampFade(local, duration);
  const x = interpolate(enter, [0, 1], [-34, 0]);
  const negativeCard = spring({
    frame: local,
    fps,
    config: {damping: 17, stiffness: 150},
  });
  const positiveCard = spring({
    frame: Math.max(0, local - 32),
    fps,
    config: {damping: 18, stiffness: 145},
  });
  const negativeScale = interpolate(negativeCard, [0, 1], [0.94, 1]);
  const positiveScale = interpolate(positiveCard, [0, 1], [0.94, 1]);
  const positiveOpacity = interpolate(local, [24, 44], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const negativeText = compactHudText(event.text ?? '\u8fd8\u5728\u624b\u52a8', 18);
  const hasPositiveResolution = Boolean(event.subtext?.trim());
  const positiveText = hasPositiveResolution ? compactHudText(event.subtext ?? '', 18) : '';
  const NegativeIcon = iconForEvent(event, 'AlertTriangle');
  const inferredNegativeHighlight =
    (negativeText.includes('\u4e0d\u662f') ? negativeText.split('\u4e0d\u662f', 2)[1].slice(0, 8) : '') ||
    inferEmphasis(negativeText, [
      '\u624b\u52a8',
      '\u4e0d\u591f\u5206',
      '\u751f\u6210\u4e00\u5f20\u56fe',
      '\u91cd\u590d',
      '\u4e0d\u503c\u5f97',
    ]);
  const negativeHighlight =
    (event.emphasisWords?.[0] ?? inferredNegativeHighlight) ||
    (negativeText.includes('\u4e0d\u591f\u5206') ? '\u4e0d\u591f\u5206' :
      negativeText.includes('\u624b\u52a8') ? '\u624b\u52a8' :
        negativeText.includes('\u4e0d\u662f') ? '\u4e0d\u662f' :
          negativeText.includes('\u5931\u8d25') ? '\u5931\u8d25' : '');
  const inferredPositiveHighlight = hasPositiveResolution ? inferEmphasis(positiveText, ['\u5de5\u4f5c\u6d41', '\u81ea\u52a8\u5316', '\u81ea\u52a8', '\u91cd\u590d\u52a8\u4f5c', 'Codex']) : '';
  const positiveHighlight =
    (hasPositiveResolution ? (event.emphasisWords?.[1] ?? inferredPositiveHighlight) : '') ||
    (positiveText.includes('\u81ea\u52a8\u5316') ? '\u81ea\u52a8\u5316' :
      positiveText.includes('\u81ea\u52a8') ? '\u81ea\u52a8' :
        positiveText.includes('\u7528\u4e0a') ? '\u7528\u4e0a' : '');
  const negativeSegments = negativeHighlight ? splitByEmphasis(negativeText, [negativeHighlight]) : [negativeText];
  const positiveSegments = positiveHighlight ? splitByEmphasis(positiveText, [positiveHighlight]) : [positiveText];
  const negativeFontSize = compact ? (negativeText.length > 12 ? 23 : 27) : negativeText.length > 15 ? 34 : 39;
  const positiveFontSize = compact ? (positiveText.length > 12 ? 22 : 26) : positiveText.length > 15 ? 28 : 31;

  return (
    <div
      style={{
        position: 'absolute',
        left: compact ? 54 : isPortrait ? 54 : 58,
        top: compact ? 150 : isPortrait ? 280 : 164,
        width: compact ? 972 : isPortrait ? 930 : 720,
        height: compact ? 136 : isPortrait ? 310 : 286,
        opacity,
        transform: `translateX(${x}px)`,
        fontFamily: fontStack,
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: compact ? (hasPositiveResolution ? 464 : 700) : '100%',
          minHeight: compact ? 118 : 128,
          borderRadius: compact ? 14 : 16,
          background: 'rgba(12,13,17,0.82)',
          boxShadow: `${hudRingShadow}, inset 0 0 0 2px rgba(216,60,48,0.78)`,
          transform: `scale(${negativeScale})`,
          transformOrigin: 'left center',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            position: 'absolute',
              left: compact ? 18 : 26,
              top: compact ? 31 : 29,
              width: compact ? 48 : 62,
              height: compact ? 48 : 62,
              borderRadius: compact ? 11 : 14,
            display: 'grid',
            placeItems: 'center',
            color: colors.red,
            background: 'rgba(216,60,48,0.12)',
            boxShadow: 'inset 0 0 0 2px rgba(216,60,48,0.76), 0 16px 30px rgba(0,0,0,0.32)',
          }}
        >
            <NegativeIcon size={compact ? 28 : 36} strokeWidth={2.5} />
          </div>
        <div style={{position: 'absolute', left: compact ? 82 : 108, top: compact ? 19 : 24, color: colors.red, fontSize: compact ? 14 : 17, fontWeight: 950, letterSpacing: compact ? 3 : 6, textShadow: hudTextHighlight}}>
          {event.status ?? 'WRONG PATH'}
        </div>
        <div style={{position: 'absolute', left: compact ? 82 : 108, right: compact ? 44 : 76, top: compact ? 53 : 60, color: colors.white, fontSize: negativeFontSize, fontWeight: 950, lineHeight: 1.08, textShadow: hudTextHighlight, whiteSpace: 'nowrap', overflow: 'hidden'}}>
          {negativeSegments.map((segment, index) => (
            <span key={`${segment}-${index}`} style={{color: segment === negativeHighlight ? colors.red : colors.white}}>
              {segment}
            </span>
          ))}
        </div>
        <div style={{position: 'absolute', right: compact ? 16 : 26, top: compact ? 44 : 46, color: colors.red, opacity: 0.95}}>
          <CircleX size={compact ? 24 : 30} strokeWidth={2.4} />
        </div>
      </div>

      {hasPositiveResolution ? (
        <div
          style={{
            position: 'absolute',
            left: compact ? 488 : 0,
            top: compact ? 0 : 156,
            width: compact ? 484 : isPortrait ? 780 : 600,
            minHeight: compact ? 118 : 92,
            borderRadius: 14,
            background: 'rgba(7,28,21,0.76)',
            boxShadow: `${hudRingShadow}, inset 0 0 0 2px rgba(32,224,176,0.58)`,
            opacity: positiveOpacity,
            transform: `translateY(${interpolate(positiveCard, [0, 1], [18, 0])}px) scale(${positiveScale})`,
            transformOrigin: 'left center',
          }}
        >
          <div
            style={{
              position: 'absolute',
              left: compact ? 18 : 24,
              top: compact ? 35 : 23,
              width: compact ? 44 : 46,
              height: compact ? 44 : 46,
              borderRadius: compact ? 11 : 12,
              display: 'grid',
              placeItems: 'center',
              color: colors.green,
              background: 'rgba(32,224,176,0.12)',
              boxShadow: 'inset 0 0 0 2px rgba(32,224,176,0.58)',
            }}
          >
            <CheckCircle2 size={compact ? 26 : 28} strokeWidth={2.5} />
          </div>
          <div style={{position: 'absolute', left: compact ? 78 : 88, right: 22, top: compact ? 42 : 26, color: colors.white, fontSize: positiveFontSize, fontWeight: 950, lineHeight: 1.1, textShadow: hudTextHighlight, whiteSpace: 'nowrap', overflow: 'hidden'}}>
            {positiveSegments.map((segment, index) => (
              <span key={`${segment}-${index}`} style={{color: segment === positiveHighlight ? colors.green : colors.white}}>
                {segment}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <div
        style={{
          position: 'absolute',
          left: 4,
          top: compact ? 126 : 135,
          width: compact ? (hasPositiveResolution ? 456 : 220) : 150,
          height: 3,
          background: colors.red,
          opacity: interpolate(local, [10, 26], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
        }}
      />
    </div>
  );
};

export const PlatformFanOutPanel: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const local = frame - event.startFrame;
  const duration = event.endFrame - event.startFrame;
  const enter = spring({frame: local, fps, config: {damping: 24, stiffness: 90}});
  const opacity = clampFade(local, duration);
  const scale = interpolate(enter, [0, 1], [0.96, 1]);
  const compact = shouldUsePortraitCompactHud(event, width, height);
  const positions = [
    {x: 48, y: 142}, {x: 440, y: 142}, {x: 48, y: 344}, {x: 440, y: 344}, {x: 244, y: 374},
  ];
  const palette = [colors.blue, colors.red, colors.green, colors.amber, colors.white];
  const sourceSteps = (event.internalSteps ?? []).slice(0, 5);
  const platforms = (sourceSteps.length ? sourceSteps : [
    {label: '渠道适配', iconName: 'Route'},
    {label: '多端发布', iconName: 'Network'},
    {label: '统一交付', iconName: 'Package'},
  ]).map((step, index) => ({
    name: step.label ?? step.text ?? `渠道 ${index + 1}`,
    icon: iconMap[(step.iconName as IconName) ?? 'Network'] ?? Network,
    color: palette[index % palette.length],
    ...positions[index % positions.length],
  }));

  if (compact) {
    return (
      <div
        style={{
          position: 'absolute',
          right: PORTRAIT_RIGHT_RAIL.right,
          top: 500,
          width: PORTRAIT_RIGHT_RAIL.width,
          minHeight: 540,
          borderRadius: 14,
          background: colors.panel,
          boxShadow: hudRingShadow,
          opacity,
          transform: `translateX(${interpolate(enter, [0, 1], [30, 0])}px) scale(${scale})`,
          transformOrigin: 'right top',
          fontFamily: fontStack,
          pointerEvents: 'none',
        }}
      >
        <div style={{position: 'absolute', left: 24, top: 24, color: colors.blue, fontSize: 17, fontWeight: 950, textShadow: hudTextHighlight}}>
          多平台分发
        </div>
        <div style={{position: 'absolute', left: 24, right: 24, top: 58, color: colors.white, fontSize: 30, fontWeight: 950, lineHeight: 1.08, textShadow: hudTextHighlight}}>
          {event.text}
        </div>
        <div
          style={{
            position: 'absolute',
            left: 24,
            top: 126,
            width: 156,
            height: 56,
            borderRadius: 12,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            background: 'rgba(16,163,127,0.16)',
            color: colors.green,
            fontSize: 20,
            fontWeight: 950,
            boxShadow: '0 16px 34px rgba(0,0,0,0.42)',
            textShadow: hudTextHighlight,
          }}
        >
          <Package size={22} strokeWidth={2.4} />
          素材包
        </div>
        <div style={{position: 'absolute', left: 46, top: 196, bottom: 52, width: 3, borderRadius: 999, background: 'rgba(6,126,246,0.56)'}} />
        <div style={{position: 'absolute', left: 78, right: 22, top: 198, display: 'grid', gap: 14}}>
          {platforms.map((platform, index) => {
            const PlatformIcon = platform.icon;
            const row = interpolate(local - index * 8, [0, 20], [0, 1], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            return (
              <div
                key={platform.name}
                style={{
                  height: 50,
                  borderRadius: 10,
                  display: 'grid',
                  gridTemplateColumns: '34px minmax(0, 1fr)',
                  alignItems: 'center',
                  gap: 10,
                  padding: '0 14px',
                  color: platform.color,
                  background: 'rgba(255,255,255,0.06)',
                  boxShadow: '0 12px 24px rgba(0,0,0,0.30)',
                  fontSize: 18,
                  fontWeight: 950,
                  textShadow: hudTextHighlight,
                  opacity: row,
                  transform: `translateY(${interpolate(row, [0, 1], [12, 0])}px)`,
                }}
              >
                <PlatformIcon size={21} strokeWidth={2.4} />
                <span>{platform.name}</span>
              </div>
            );
          })}
        </div>
        {event.subtext ? (
          <div style={{position: 'absolute', left: 24, right: 24, bottom: 24, color: colors.muted, fontSize: 16, fontWeight: 850, textShadow: hudTextHighlight}}>
            {event.subtext}
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div
      style={{
        position: 'absolute',
        right: 82,
        top: 120,
        width: 620,
        height: 548,
        borderRadius: 16,
        background: colors.panel,
        border: 'none',
        boxShadow: hudRingShadow,
        opacity,
        transform: `scale(${scale})`,
        fontFamily: fontStack,
      }}
    >
      <div style={{position: 'absolute', left: 32, top: 28, color: colors.blue, fontSize: 19, fontWeight: 950, textShadow: hudTextHighlight}}>
        多平台分发
      </div>
      <div style={{position: 'absolute', left: 32, top: 62, color: colors.white, fontSize: 40, fontWeight: 950, textShadow: hudTextHighlight}}>
        {event.text}
      </div>
      <div style={{position: 'absolute', left: 32, bottom: 28, color: colors.muted, fontSize: 20, fontWeight: 800, textShadow: hudTextHighlight}}>
        {event.subtext}
      </div>
      <div
        style={{
          position: 'absolute',
          left: 238,
          top: 246,
          width: 150,
          height: 88,
          borderRadius: 14,
          display: 'grid',
          placeItems: 'center',
          background: 'rgba(16,163,127,0.16)',
          border: 'none',
          color: colors.green,
          fontSize: 24,
          fontWeight: 950,
          boxShadow: `${hudRingShadow}, 0 18px 42px rgba(0,0,0,0.36)`,
          textShadow: hudTextHighlight,
        }}
      >
        <Package size={28} strokeWidth={2.4} />
        素材包
      </div>
      <svg width="620" height="548" viewBox="0 0 620 548" style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}>
        {platforms.map((platform, index) => {
          const line = interpolate(local - index * 9, [0, 34], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          return (
            <line
              key={`${platform.name}-line`}
              x1="313"
              y1="291"
              x2={platform.x + 72}
              y2={platform.y + 36}
              stroke={platform.color}
              strokeWidth="3"
              strokeDasharray="8 8"
              opacity={line * 0.62}
            />
          );
        })}
      </svg>
      {platforms.map((platform, index) => {
        const PlatformIcon = platform.icon;
        const line = interpolate(local - index * 9, [0, 34], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });
        const pop = spring({frame: Math.max(0, local - index * 9), fps, config: {damping: 22, stiffness: 100}});
        return (
          <div
            key={platform.name}
            style={{
              position: 'absolute',
              left: platform.x,
              top: platform.y,
              width: 144,
              height: 72,
              borderRadius: 12,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              color: platform.color,
              background: 'rgba(255,255,255,0.06)',
              border: 'none',
              fontSize: 20,
              fontWeight: 950,
              textShadow: hudTextHighlight,
              opacity: line,
              transform: `scale(${interpolate(pop, [0, 1], [0.92, 1])})`,
            }}
          >
            <PlatformIcon size={22} strokeWidth={2.4} />
            {platform.name}
          </div>
        );
      })}
    </div>
  );
};

export const AutomationHandoffPanel: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const local = frame - event.startFrame;
  const duration = event.endFrame - event.startFrame;
  const enter = spring({frame: local, fps, config: {damping: 24, stiffness: 95}});
  const opacity = clampFade(local, duration);
  const compact = shouldUsePortraitCompactHud(event, width, height);
  const y = interpolate(enter, [0, 1], [24, 0]);
  const handoffProgress = sectionProgress(local, 72, 18);
  const handoffPop = spring({
    frame: Math.max(0, local - 72),
    fps,
    config: {damping: 18, stiffness: 140},
  });
  const fields = [
    {label: '\u4e0a\u4f20', icon: UploadCloud},
    {label: '\u6807\u9898', icon: FileText},
    {label: '\u7b80\u4ecb', icon: AlignLeft},
    {label: '\u6807\u7b7e', icon: Tags},
    {label: '\u5c01\u9762', icon: Image},
  ]

  return (
    <div
      style={{
        position: 'absolute',
        left: compact ? undefined : 70,
        right: compact ? PORTRAIT_RIGHT_RAIL.right : undefined,
        top: compact ? 520 : 168,
        width: compact ? PORTRAIT_RIGHT_RAIL.width : 660,
        height: compact ? 490 : 444,
        borderRadius: 16,
        background: colors.panel,
        border: 'none',
        opacity,
        transform: compact
          ? `translate(${interpolate(enter, [0, 1], [30, 0])}px, ${y}px)`
          : `translateY(${y}px)`,
        fontFamily: fontStack,
        boxShadow: hudRingShadow,
      }}
    >
      <div style={{position: 'absolute', left: compact ? 24 : 32, top: compact ? 24 : 30, color: colors.blue, fontSize: compact ? 17 : 19, fontWeight: 950, textShadow: hudTextHighlight}}>
        自动化交接
      </div>
      <div style={{position: 'absolute', left: compact ? 24 : 32, right: compact ? 24 : undefined, top: compact ? 56 : 66, color: colors.white, fontSize: compact ? 30 : 42, fontWeight: 950, lineHeight: 1.08, textShadow: hudTextHighlight}}>
        {event.text}
      </div>
      <div style={{position: 'absolute', left: compact ? 24 : 32, top: compact ? 128 : 128, display: 'grid', gap: compact ? 10 : 12}}>
        {fields.map((field, index) => {
          const FieldIcon = field.icon;
          const progress = interpolate(local - index * 11, [0, 36], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          const activeIndex = Math.min(fields.length - 1, Math.max(0, Math.floor((local - 12) / 18)));
          const current = activeIndex === index && progress < 1;
          return (
            <div
              key={field.label}
              style={{
                width: compact ? interpolate(progress, [0, 1], [210, 260]) : interpolate(progress, [0, 1], [220, 332]),
                height: compact ? 42 : 46,
                borderRadius: 10,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '0 14px',
                color: colors.white,
                background: current ? 'rgba(255,255,255,0.14)' : 'rgba(255,255,255,0.08)',
                border: 'none',
                fontSize: compact ? 18 : 21,
                fontWeight: 900,
                textShadow: hudTextHighlight,
              }}
            >
              <FieldIcon size={compact ? 19 : 22} color={progress > 0.15 ? colors.blue : colors.muted} strokeWidth={2.4} />
              <span style={{flex: 1}}>{field.label}</span>
              <CheckCircle2 size={compact ? 19 : 22} color={progress > 0.85 ? colors.green : colors.muted} />
            </div>
          );
        })}
      </div>
      <div
        style={{
          position: 'absolute',
          left: compact ? 290 : 392,
          top: compact ? 208 : 178,
          color: colors.green,
          opacity: handoffProgress,
          transform: `translateX(${interpolate(handoffProgress, [0, 1], [-18, 0])}px) scale(${interpolate(handoffPop, [0, 1], [0.82, 1])})`,
          transformOrigin: 'left center',
        }}
      >
        <SendHorizontal size={compact ? 48 : 74} strokeWidth={2.4} />
      </div>
      <div
        style={{
          position: 'absolute',
          right: compact ? 24 : 34,
          top: compact ? 260 : 152,
          width: compact ? 126 : 176,
          height: compact ? 106 : 154,
          borderRadius: 18,
          display: 'grid',
          placeItems: 'center',
          background: 'rgba(16,163,127,0.16)',
          border: 'none',
          color: colors.green,
          fontSize: compact ? 22 : 28,
          fontWeight: 950,
          textAlign: 'center',
          lineHeight: 1.15,
          boxShadow: `${hudRingShadow}, 0 18px 42px rgba(0,0,0,0.36)`,
          textShadow: hudTextHighlight,
          opacity: handoffProgress,
          transform: `translateY(${interpolate(handoffProgress, [0, 1], [18, 0])}px) scale(${interpolate(handoffPop, [0, 1], [0.9, 1])})`,
          transformOrigin: 'center center',
        }}
      >
        Codex
        <br />
        执行
      </div>
      <div style={{position: 'absolute', left: compact ? 24 : 32, right: compact ? 24 : 32, bottom: compact ? 22 : 28, color: colors.muted, fontSize: compact ? 16 : 21, fontWeight: 800, textShadow: hudTextHighlight}}>
        {event.subtext}
      </div>
    </div>
  );
};

const MaterialImage: React.FC<{src: string; fit?: 'cover' | 'contain'}> = ({src, fit = 'cover'}) => (
  <Img
    src={staticFile(src)}
    style={{
      position: 'absolute',
      inset: 0,
      width: '100%',
      height: '100%',
      objectFit: fit,
      filter: 'saturate(1.05) contrast(1.02)',
    }}
  />
);

const isVideoAsset = (src: string): boolean => /\.(mp4|mov|m4v|webm)$/i.test(src);

const MaterialAsset: React.FC<{src: string; fit?: 'cover' | 'contain'; startFrom?: number}> = ({
  src,
  fit = 'cover',
  startFrom = 0,
}) => {
  if (isVideoAsset(src)) {
    return (
      <OffthreadVideo
        src={staticFile(src)}
        startFrom={startFrom}
        muted
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit: fit,
          filter: 'saturate(1.05) contrast(1.02)',
        }}
      />
    );
  }

  return <MaterialImage src={src} fit={fit} />;
};

type InternalStep = NonNullable<VisualEvent['internalSteps']>[number];

const defaultCapabilitySteps: InternalStep[] = [
  {label: '比较对象', iconName: 'Scale', status: '对象'},
  {label: '能力指标', iconName: 'BrainCircuit', status: '指标'},
  {label: '差异结论', iconName: 'BarChart3', status: '结论'},
];

const defaultSceneLockSteps: InternalStep[] = [
  {label: '应用场景', iconName: 'Link2', status: '场景'},
  {label: '目标行业', iconName: 'Building2', status: '行业'},
  {label: '落地结果', iconName: 'BadgeCheck', status: '结果'},
];

const defaultTransformationSteps: InternalStep[] = [
  {label: '原状态', iconName: 'Layers', status: '起点'},
  {label: '目标状态', iconName: 'TrendingUp', status: '目标'},
  {label: '关键驱动', iconName: 'BrainCircuit', status: '驱动'},
  {label: '转化结果', iconName: 'BadgeCheck', status: '结果'},
];

const parsePercent = (value?: string): number => {
  const match = String(value ?? '').match(/(\d+(?:\.\d+)?)/);
  return match ? Math.max(0, Math.min(100, Number(match[1]))) : 0;
};

const sectionProgress = (local: number, start: number, span = 16): number =>
  interpolate(local - start, [0, span], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

export const CapabilitySharePanel: React.FC<{event: VisualEvent; side?: 'left' | 'right'}> = ({
  event,
  side = 'left',
}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const local = frame - event.startFrame;
  const duration = event.endFrame - event.startFrame;
  const enter = spring({frame: local, fps, config: {damping: 22, stiffness: 105}});
  const opacity = clampFade(local, duration);
  const steps = (event.internalSteps && event.internalSteps.length > 0 ? event.internalSteps : defaultCapabilitySteps).slice(0, 4);
  const tileSteps = steps.slice(0, 3);
  const panelProgress = sectionProgress(local, 38, 18);
  const Icon = iconForEvent(event, 'BarChart3');
  const compact = shouldUsePortraitCompactHud(event, width, height);

  return (
    <div
      style={{
        position: 'absolute',
        left: compact ? undefined : side === 'left' ? 70 : undefined,
        right: compact ? PORTRAIT_RIGHT_RAIL.right : side === 'right' ? 70 : undefined,
        top: compact ? 470 : 128,
        width: compact ? PORTRAIT_RIGHT_RAIL.width : 720,
        fontFamily: fontStack,
        opacity,
        transform: `translateX(${interpolate(enter, [0, 1], [side === 'left' ? -28 : 28, 0])}px)`,
        transformOrigin: side === 'left' ? 'left top' : 'right top',
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: compact ? '38px 1fr' : '50px 1fr',
          gap: compact ? 12 : 16,
          alignItems: 'center',
          opacity: sectionProgress(local, 0, 12),
          transform: `translateY(${interpolate(sectionProgress(local, 0, 12), [0, 1], [10, 0])}px)`,
        }}
      >
        <div
          style={{
            width: compact ? 36 : 46,
            height: compact ? 36 : 46,
            borderRadius: 8,
            display: 'grid',
            placeItems: 'center',
            background: 'rgba(6,126,246,0.16)',
            color: colors.blue,
            boxShadow: '0 12px 24px rgba(0,0,0,0.34)',
          }}
        >
          <Icon size={compact ? 22 : 27} strokeWidth={2.4} />
        </div>
        <div>
          <div style={{color: colors.blue, fontSize: compact ? 14 : 17, fontWeight: 950, letterSpacing: compact ? 2 : 3, textShadow: hudTextHighlight}}>
            {event.status ?? 'GLOBAL · CAPABILITY'}
          </div>
          <div style={{marginTop: 6, color: colors.white, fontSize: compact ? 26 : 38, fontWeight: 950, lineHeight: 1.08, textShadow: hudTextHighlight}}>
            {event.text ?? event.title}
          </div>
        </div>
      </div>

      <div style={{display: 'flex', gap: compact ? 10 : 18, marginTop: compact ? 20 : 28}}>
        {tileSteps.map((step, index) => {
          const progress = sectionProgress(local, 16 + index * 8, 12);
          const StepIcon = iconMap[(step.iconName as IconName) || 'BrainCircuit'] ?? BrainCircuit;
          return (
            <div
              key={`${step.label ?? step.text}-${index}`}
              style={{
                width: compact ? 96 : 132,
                height: compact ? 78 : 108,
                borderRadius: compact ? 10 : 14,
                display: 'grid',
                placeItems: 'center',
                gap: 4,
                background: 'rgba(240,240,240,0.92)',
                color: '#05070b',
                opacity: progress,
                transform: `translateY(${interpolate(progress, [0, 1], [12, 0])}px) scale(${interpolate(progress, [0, 1], [0.94, 1])})`,
                boxShadow: '0 18px 36px rgba(0,0,0,0.38)',
                fontWeight: 950,
              }}
            >
              <StepIcon size={compact ? 28 : 39} strokeWidth={2.2} />
              <div style={{fontSize: compact ? 12 : 16, maxWidth: compact ? 82 : 112, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
                {step.label ?? step.text}
              </div>
            </div>
          );
        })}
      </div>

      <div
        style={{
          marginTop: compact ? 20 : 28,
          width: compact ? PORTRAIT_RIGHT_RAIL.width : 680,
          padding: compact ? '18px 18px 20px' : '26px 28px 28px',
          borderRadius: 14,
          background: colors.panel,
          boxShadow: hudRingShadow,
          opacity: panelProgress,
          transform: `translateY(${interpolate(panelProgress, [0, 1], [16, 0])}px)`,
        }}
      >
        <div style={{color: colors.blue, fontSize: compact ? 13 : 16, fontWeight: 950, letterSpacing: compact ? 2 : 3, textShadow: hudTextHighlight}}>
          {event.title ?? 'ENTERPRISE LLM SHARE · 2025'}
        </div>
          <div style={{marginTop: compact ? 14 : 20, display: 'grid', gap: compact ? 11 : 16}}>
          {steps.slice(0, 4).map((step, index) => {
            const progress = sectionProgress(local, 58 + index * 12, 14);
            const pct = parsePercent(step.status);
            const hasPercent = /%/.test(String(step.status ?? ''));
            const bar = interpolate(progress, [0, 1], [0, pct], {
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            });
            return (
              <div
                key={`${step.label ?? step.text}-bar-${index}`}
                style={{
                  display: 'grid',
                  gridTemplateColumns: compact ? '86px 1fr 44px' : '156px 1fr 66px',
                  alignItems: 'center',
                  gap: 18,
                  opacity: progress,
                  transform: `translateX(${interpolate(progress, [0, 1], [-10, 0])}px)`,
                }}
              >
                <div style={{color: colors.white, fontSize: compact ? 15 : 22, fontWeight: 900, textShadow: hudTextHighlight}}>
                  {step.label ?? step.text}
                </div>
                <div style={{height: compact ? 12 : 18, borderRadius: 999, background: 'rgba(255,255,255,0.18)', overflow: 'hidden', boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.12)'}}>
                  <div
                    style={{
                      width: hasPercent ? `${bar}%` : '0%',
                      height: '100%',
                      borderRadius: 999,
                      background: colors.blue,
                      boxShadow: '0 8px 20px rgba(0,0,0,0.34)',
                    }}
                  />
                </div>
                <div style={{color: colors.blue, fontSize: compact ? 17 : 26, fontWeight: 950, textAlign: 'right', textShadow: hudTextHighlight}}>
                  {hasPercent ? `${Math.round(bar)}%` : (step.status ?? '对比项')}
                </div>
              </div>
            );
          })}
        </div>
        {event.subtext ? (
          <div style={{marginTop: 18, color: colors.muted, fontSize: 15, fontWeight: 800, textShadow: hudTextHighlight}}>
            {event.subtext}
          </div>
        ) : null}
      </div>
    </div>
  );
};

export const SceneLockGridPanel: React.FC<{event: VisualEvent; side?: 'left' | 'right'}> = ({
  event,
  side = 'left',
}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const local = frame - event.startFrame;
  const duration = event.endFrame - event.startFrame;
  const enter = spring({frame: local, fps, config: {damping: 22, stiffness: 105}});
  const opacity = clampFade(local, duration);
  const steps = (event.internalSteps && event.internalSteps.length > 0 ? event.internalSteps : defaultSceneLockSteps).slice(0, 4);
  const HeaderIcon = iconForEvent(event, 'Link2');
  const compact = shouldUsePortraitCompactHud(event, width, height);

  return (
    <div
      style={{
        position: 'absolute',
        left: compact ? undefined : side === 'left' ? 72 : undefined,
        right: compact ? PORTRAIT_RIGHT_RAIL.right : side === 'right' ? 72 : undefined,
        top: compact ? 510 : 150,
        width: compact ? PORTRAIT_RIGHT_RAIL.width : 720,
        fontFamily: fontStack,
        opacity,
        transform: `translateX(${interpolate(enter, [0, 1], [side === 'left' ? -24 : 24, 0])}px)`,
        transformOrigin: side === 'left' ? 'left top' : 'right top',
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: compact ? '38px 1fr' : '50px 1fr',
          gap: compact ? 12 : 16,
          alignItems: 'center',
          opacity: sectionProgress(local, 0, 12),
          transform: `translateY(${interpolate(sectionProgress(local, 0, 12), [0, 1], [10, 0])}px)`,
        }}
      >
        <div
          style={{
            width: compact ? 36 : 46,
            height: compact ? 36 : 46,
            borderRadius: 9,
            display: 'grid',
            placeItems: 'center',
            color: colors.green,
            background: 'rgba(16,163,127,0.12)',
            boxShadow: '0 12px 24px rgba(0,0,0,0.34)',
          }}
        >
          <HeaderIcon size={compact ? 22 : 27} strokeWidth={2.5} />
        </div>
        <div>
          <div style={{color: colors.green, fontSize: compact ? 14 : 17, fontWeight: 950, letterSpacing: compact ? 2 : 3, textShadow: hudTextHighlight}}>
            {event.status ?? 'CHINA · SCENE-LOCK'}
          </div>
          <div style={{marginTop: 6, color: colors.white, fontSize: compact ? 27 : 40, fontWeight: 950, lineHeight: 1.08, textShadow: hudTextHighlight}}>
            {event.text ?? event.title}
          </div>
        </div>
      </div>

      <div style={{display: 'grid', gridTemplateColumns: compact ? '1fr' : `repeat(${Math.min(steps.length, 4)}, 1fr)`, gap: compact ? 12 : 18, marginTop: compact ? 20 : 30}}>
        {steps.map((step, index) => {
          const progress = sectionProgress(local, 18 + index * 13, 14);
          const StepIcon = iconMap[(step.iconName as IconName) || 'Link2'] ?? Link2;
          const accent = index === 0 ? colors.blue : index === 1 ? colors.green : index === 2 ? colors.amber : colors.purple;
          return (
            <div
              key={`${step.label ?? step.text}-${index}`}
              style={{
                height: compact ? 56 : 166,
                borderRadius: compact ? 10 : 13,
                display: 'grid',
                gridTemplateColumns: compact ? '42px minmax(0, 1fr) 90px' : undefined,
                placeItems: compact ? undefined : 'center',
                alignItems: compact ? 'center' : undefined,
                gap: compact ? 10 : 8,
                padding: compact ? '0 14px' : '16px 14px',
                background: colors.panel,
                color: colors.white,
                opacity: progress,
                transform: `translateY(${interpolate(progress, [0, 1], [16, 0])}px) scale(${interpolate(progress, [0, 1], [0.95, 1])})`,
                boxShadow: hudRingShadow,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: compact ? 34 : 52,
                  height: compact ? 34 : 52,
                  borderRadius: compact ? 8 : 10,
                  display: 'grid',
                  placeItems: 'center',
                  background: `${accent}22`,
                  color: accent,
                  boxShadow: '0 10px 20px rgba(0,0,0,0.34)',
                }}
              >
                <StepIcon size={compact ? 20 : 31} strokeWidth={2.4} />
              </div>
              <div style={{fontSize: compact ? 20 : 29, fontWeight: 950, lineHeight: 1.05, textShadow: hudTextHighlight}}>
                {step.label ?? step.text}
              </div>
              {step.status ? (
                <div style={{fontSize: compact ? 12 : 15, lineHeight: 1.15, color: colors.muted, fontWeight: 800, whiteSpace: 'nowrap', textShadow: hudTextHighlight}}>
                  {step.status}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const TransformationStackPanel: React.FC<{event: VisualEvent; side?: 'left' | 'right'}> = ({
  event,
  side = 'left',
}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const local = frame - event.startFrame;
  const duration = event.endFrame - event.startFrame;
  const enter = spring({frame: local, fps, config: {damping: 22, stiffness: 105}});
  const opacity = clampFade(local, duration);
  const steps = (event.internalSteps && event.internalSteps.length > 0 ? event.internalSteps : defaultTransformationSteps);
  const source = steps[0] ?? defaultTransformationSteps[0];
  const target = steps[1] ?? defaultTransformationSteps[1];
  const drivers = (steps.length > 3 ? steps.slice(2, -1) : steps.slice(2)).slice(0, 2);
  const result = steps.length >= 4 ? steps[steps.length - 1] : defaultTransformationSteps[4];
  const SourceIcon = iconMap[(source.iconName as IconName) || 'User'] ?? User;
  const TargetIcon = iconMap[(target.iconName as IconName) || 'Users'] ?? Users;
  const resultText = result.label ?? event.title ?? event.text ?? '55%-81%';
  const resultIsRange = /\d+(?:\.\d+)?\s*[%倍万亿]?\s*[-~—]\s*\d+(?:\.\d+)?\s*[%倍万亿]?/.test(resultText);
  const {value, prefix, suffix, decimals} = inferNumericTarget({
    ...event,
    text: resultText,
    status: result.status,
  });
  const metricProgress = sectionProgress(local, 76, 34);
  const counted = value
    ? interpolate(metricProgress, [0, 1], [0, value], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 0;
  const sourceProgress = sectionProgress(local, 0, 12);
  const arrowProgress = sectionProgress(local, 14, 10);
  const targetProgress = sectionProgress(local, 24, 12);
  const resultProgress = sectionProgress(local, 70, 16);
  const compact = shouldUsePortraitCompactHud(event, width, height);

  return (
    <div
      style={{
        position: 'absolute',
        left: compact ? undefined : side === 'left' ? 104 : undefined,
        right: compact ? PORTRAIT_RIGHT_RAIL.right : side === 'right' ? 104 : undefined,
        top: compact ? 500 : 150,
        width: compact ? PORTRAIT_RIGHT_RAIL.width : 760,
        fontFamily: fontStack,
        opacity,
        transform: `translateX(${interpolate(enter, [0, 1], [side === 'left' ? -24 : 24, 0])}px)`,
        transformOrigin: side === 'left' ? 'left top' : 'right top',
        pointerEvents: 'none',
      }}
    >
      <div style={{display: 'flex', alignItems: 'flex-start', gap: compact ? 14 : 26}}>
        <div style={{opacity: sourceProgress, transform: `translateY(${interpolate(sourceProgress, [0, 1], [12, 0])}px)`}}>
          <div style={{width: compact ? 82 : 108, height: compact ? 74 : 104, borderRadius: compact ? 12 : 16, display: 'grid', placeItems: 'center', color: colors.white, background: colors.panel, boxShadow: hudRingShadow}}>
            <SourceIcon size={compact ? 38 : 54} strokeWidth={2.3} />
          </div>
          <div style={{marginTop: 10, color: colors.white, fontSize: compact ? 16 : 22, fontWeight: 850, textAlign: 'center', textShadow: hudTextHighlight}}>
            {source.label ?? source.text}
          </div>
        </div>

        <div style={{paddingTop: compact ? 24 : 34, opacity: arrowProgress, transform: `translateX(${interpolate(arrowProgress, [0, 1], [-8, 0])}px)`, color: colors.blue}}>
          <ArrowRight size={compact ? 32 : 44} strokeWidth={2.6} />
        </div>

        <div style={{opacity: targetProgress, transform: `translateY(${interpolate(targetProgress, [0, 1], [12, 0])}px)`}}>
          <div style={{width: compact ? 98 : 132, height: compact ? 74 : 104, borderRadius: compact ? 12 : 16, display: 'grid', placeItems: 'center', color: colors.blue, background: colors.panel, boxShadow: hudRingShadow}}>
            <TargetIcon size={compact ? 42 : 58} strokeWidth={2.3} />
          </div>
          <div style={{marginTop: 10, color: colors.blue, fontSize: compact ? 16 : 22, fontWeight: 900, textAlign: 'center', textShadow: hudTextHighlight}}>
            {target.label ?? target.text}
          </div>
        </div>
      </div>

      <div style={{display: 'grid', gridTemplateColumns: compact ? '1fr' : `repeat(${Math.max(1, drivers.length)}, 1fr)`, gap: compact ? 12 : 20, marginTop: compact ? 26 : 34, width: compact ? PORTRAIT_RIGHT_RAIL.width : 680}}>
        {drivers.map((driver, index) => {
          const progress = sectionProgress(local, 42 + index * 12, 14);
          const DriverIcon = iconMap[(driver.iconName as IconName) || (index === 0 ? 'ShieldCheck' : 'TrendingUp')] ?? ShieldCheck;
          const accent = index === 0 ? colors.green : colors.blue;
          return (
            <div
              key={`${driver.label ?? driver.text}-${index}`}
              style={{
                height: compact ? 64 : 96,
                borderRadius: 12,
                display: 'grid',
                gridTemplateColumns: '54px 1fr',
                alignItems: 'center',
                gap: 12,
                padding: compact ? '0 16px' : '0 20px',
                background: colors.panel,
                boxShadow: hudRingShadow,
                opacity: progress,
                transform: `translateY(${interpolate(progress, [0, 1], [14, 0])}px)`,
              }}
            >
              <div style={{width: compact ? 36 : 44, height: compact ? 36 : 44, borderRadius: 10, display: 'grid', placeItems: 'center', color: accent, background: `${accent}1f`, boxShadow: '0 10px 20px rgba(0,0,0,0.32)'}}>
                <DriverIcon size={compact ? 21 : 26} strokeWidth={2.5} />
              </div>
              <div>
                <div style={{color: accent, fontSize: compact ? 12 : 15, fontWeight: 950, letterSpacing: 2, textShadow: hudTextHighlight}}>
                  {driver.status ?? (index === 0 ? 'MOAT' : 'LEVERAGE')}
                </div>
                <div style={{marginTop: 4, color: colors.white, fontSize: compact ? 21 : 30, fontWeight: 950, textShadow: hudTextHighlight}}>
                  {driver.label ?? driver.text}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div
        style={{
          marginTop: compact ? 18 : 30,
          width: compact ? PORTRAIT_RIGHT_RAIL.width : 700,
          height: compact ? 76 : 104,
          borderRadius: 12,
          display: 'grid',
          gridTemplateColumns: compact ? '42px auto 1fr' : '58px auto 1fr',
          alignItems: 'center',
          gap: 18,
          padding: compact ? '0 16px' : '0 26px',
          background: 'rgba(5,7,11,0.68)',
          boxShadow: hudRingShadow,
          opacity: resultProgress,
          transform: `translateY(${interpolate(resultProgress, [0, 1], [16, 0])}px)`,
        }}
      >
        <div style={{color: colors.green}}>
          <FlaskConical size={compact ? 28 : 38} strokeWidth={2.4} />
        </div>
        <div style={{color: colors.green, fontSize: compact ? 32 : 50, fontWeight: 950, letterSpacing: 0, textShadow: hudTextHighlight}}>
          {value && !resultIsRange ? `${prefix}${formatCount(counted, decimals)}${suffix}` : resultText}
        </div>
        <div style={{color: colors.muted, fontSize: compact ? 14 : 20, fontWeight: 900, textShadow: hudTextHighlight}}>
          {result.status ?? event.subtext ?? '\u8bed\u4e49\u7ed3\u679c'}
        </div>
      </div>
    </div>
  );
};

export const TopicKeyword: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const local = frame - event.startFrame;
  const enter = spring({frame: local, fps, config: {damping: 17, stiffness: 170}});
  const opacity = clampFade(local, event.endFrame - event.startFrame);
  const chars = Array.from((event.text ?? '本期主题').slice(0, 8));
  return (
    <div style={{position: 'absolute', left: 54, top: 246, width: 560, opacity, fontFamily: fontStack}}>
      <div style={{fontSize: 24, color: colors.blue, fontWeight: 950, letterSpacing: 4, textShadow: hudTextHighlight}}>
        {event.subtext ?? '本期主题'}
      </div>
      <div style={{marginTop: 14, display: 'flex', color: colors.white, fontSize: 94, fontWeight: 950, lineHeight: 1, textShadow: hudTextHighlight}}>
        {chars.map((char, index) => {
          const reveal = interpolate(local - index * 4, [0, 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          return <span key={`${char}-${index}`} style={{opacity: reveal, transform: `translateX(${(1 - reveal) * -24}px) scale(${0.9 + 0.1 * enter})`}}>{char}</span>;
        })}
      </div>
    </div>
  );
};

export const ClaimStrip: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const {fps, width: canvasWidth, height: canvasHeight} = useVideoConfig();
  const isPortrait = canvasHeight > canvasWidth;
  const local = frame - event.startFrame;
  const duration = event.endFrame - event.startFrame;
  const enter = spring({frame: local, fps, config: {damping: 22, stiffness: 135}});
  return (
    <div
      style={{
        position: 'absolute',
        right: 42,
        top: isPortrait ? 150 : 420,
        width: 390,
        minHeight: 96,
        padding: '22px 24px 22px 30px',
        borderRadius: 12,
        background: 'rgba(5,7,11,0.66)',
        boxShadow: hudRingShadow,
        color: colors.white,
        opacity: clampFade(local, duration),
        transform: `translateX(${interpolate(enter, [0, 1], [38, 0])}px)`,
        fontFamily: fontStack,
      }}
    >
      <div style={{position: 'absolute', left: 0, top: 14, bottom: 14, width: 5, borderRadius: 999, background: colors.blue}} />
      <div style={{fontSize: 20, color: colors.blue, fontWeight: 950, letterSpacing: 3}}>观点</div>
      <div style={{marginTop: 8, fontSize: 34, fontWeight: 950, lineHeight: 1.18, textShadow: hudTextHighlight}}>
        {compactHudText(event.text ?? '观点说明', 18)}
      </div>
    </div>
  );
};

export const RatioGallery: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const local = frame - event.startFrame;
  const duration = event.endFrame - event.startFrame;
  const steps = (event.internalSteps ?? []).slice(0, 4);
  const ratios = steps.length ? steps : [
    {label: '横版', iconName: 'PanelsTopLeft'},
    {label: '竖版', iconName: 'Image'},
    {label: '方图', iconName: 'Images'},
  ];
  return (
    <div style={{position: 'absolute', right: 42, top: 350, width: 500, opacity: clampFade(local, duration), fontFamily: fontStack}}>
      <div style={{color: colors.blue, fontSize: 24, fontWeight: 950, letterSpacing: 3, textShadow: hudTextHighlight}}>尺寸输出</div>
      <div style={{marginTop: 22, display: 'flex', alignItems: 'flex-end', gap: 14}}>
        {ratios.map((step, index) => {
          const progress = spring({frame: Math.max(0, local - index * 7), fps, config: {damping: 18, stiffness: 145}});
          const label = step.label ?? `规格 ${index + 1}`;
          const dimensions = label.includes('16:9')
            ? {width: 162, height: 91}
            : label.includes('4:3') && !label.includes('3:4')
              ? {width: 144, height: 108}
              : label.includes('3:4')
                ? {width: 112, height: 149}
                : label.includes('1:1') || label.includes('方')
                  ? {width: 126, height: 126}
                  : label.includes('竖')
                    ? {width: 106, height: 150}
                    : {width: 150, height: 94};
          return (
            <div key={`${label}-${index}`} style={{display: 'grid', gap: 10, justifyItems: 'center', transform: `translateY(${interpolate(progress, [0, 1], [28, 0])}px) scale(${interpolate(progress, [0, 1], [0.9, 1])})`}}>
              <div style={{width: dimensions.width, height: dimensions.height, borderRadius: 10, background: 'rgba(5,7,11,0.68)', boxShadow: hudRingShadow, display: 'grid', placeItems: 'center', color: index === 0 ? colors.blue : index === 1 ? colors.green : colors.white}}>
                {React.createElement(iconMap[(step.iconName as IconName) ?? 'Image'] ?? Image, {size: 34, strokeWidth: 2.4})}
              </div>
              <div style={{fontSize: 21, color: colors.white, fontWeight: 950, textShadow: hudTextHighlight}}>{label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const DepthKeywordLayer: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const local = frame - event.startFrame;
  const chars = Array.from((event.text ?? '').slice(0, 6));
  const foreground = event.foregroundAssetPath;
  const isImage = Boolean(foreground && /\.(png|webp)$/i.test(foreground));
  return (
    <div style={{position: 'absolute', inset: 0, pointerEvents: 'none'}}>
      <div style={{position: 'absolute', left: 48, right: 48, top: 250, display: 'flex', justifyContent: 'center', color: colors.white, fontFamily: fontStack, fontSize: 180, fontWeight: 950, lineHeight: 1, letterSpacing: 2, textShadow: hudTextHighlight}}>
        {chars.map((char, index) => {
          const reveal = interpolate(local - index * 4, [0, 7], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
          return <span key={`${char}-${index}`} style={{opacity: reveal, transform: `translateX(${(1 - reveal) * -34}px)`}}>{char}</span>;
        })}
      </div>
      {foreground ? (
        isImage ? (
          <Img src={staticFile(foreground)} style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'}} />
        ) : (
          <OffthreadVideo src={staticFile(foreground)} muted style={{position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover'}} />
        )
      ) : null}
    </div>
  );
};

export const MaterialBoard: React.FC<{event: VisualEvent}> = ({event}) => {
  const frame = useCurrentFrame();
  const {fps, width: canvasWidth, height: canvasHeight} = useVideoConfig();
  const isPortrait = canvasHeight > canvasWidth;
  const local = frame - event.startFrame;
  const enter = spring({frame: local, fps, config: {damping: 18, stiffness: 110}});
  const scale = interpolate(enter, [0, 1], [0.975, 1]);
  const stack = event.assetStack?.filter(Boolean) ?? [];
  const primary = event.assetPath || stack[0];
  const variant =
    event.style === 'recording-proof' || event.motionType === 'screen-recording-proof'
      ? 'recording'
      : event.style === 'poster-stack-preview' || event.motionType === 'right-poster-stack-pop'
        ? 'poster-stack'
        : stack.length > 1 || event.style === 'cover-gallery'
          ? 'cover-gallery'
          : 'single-proof';

  const boardStyle: React.CSSProperties = {
    position: 'absolute',
    left: isPortrait ? 48 : 470,
    top: isPortrait ? 290 : 88,
    width: isPortrait ? 984 : 1340,
    height: isPortrait ? 1106 : 792,
    borderRadius: 24,
    overflow: 'hidden',
    background: 'linear-gradient(135deg, #101827, #06080d)',
    border: 'none',
    boxShadow: `${mediaWindowShadow}, 0 28px 70px rgba(0,0,0,0.56)`,
    transform: `scale(${scale})`,
    transformOrigin: 'center center',
    fontFamily: fontStack,
  };

  if (variant === 'poster-stack') {
    const assets = stack.length > 0 ? stack.slice(0, 3) : primary ? [primary] : [];
    return (
      <div
        style={{
          position: 'absolute',
          right: isPortrait ? 44 : 86,
          top: isPortrait ? 430 : 148,
          width: isPortrait ? 620 : 680,
          height: 620,
          fontFamily: fontStack,
          transform: `scale(${scale})`,
          transformOrigin: 'center center',
        }}
      >
        {assets.map((asset, index) => {
          const pop = spring({frame: Math.max(0, local - index * 10), fps, config: {damping: 17, stiffness: 145}});
          const positions = [
            {left: 18, top: 110, width: 246, height: 328, angle: -5},
            {left: 210, top: 58, width: 370, height: 278, angle: 0},
            {left: 410, top: 170, width: 380, height: 214, angle: 5},
          ];
          const pos = positions[index] ?? positions[0];
          return (
            <div
              key={`${asset}-${index}`}
              style={{
                position: 'absolute',
                ...pos,
                borderRadius: 0,
                overflow: 'visible',
                background: 'transparent',
                border: 'none',
                boxShadow: '0 34px 70px rgba(0,0,0,0.54), 0 10px 24px rgba(0,0,0,0.42)',
                transform: `translateY(${interpolate(pop, [0, 1], [48, 0])}px) rotate(${pos.angle}deg) scale(${interpolate(pop, [0, 1], [0.82, 1])})`,
                opacity: interpolate(local - index * 10, [0, 12], [0, 1], {
                  extrapolateLeft: 'clamp',
                  extrapolateRight: 'clamp',
                }),
              }}
            >
              <MaterialImage src={asset} fit="cover" />
            </div>
          );
        })}
        <div
          style={{
            position: 'absolute',
            right: 26,
            bottom: 44,
            padding: '12px 18px',
            borderRadius: 12,
            background: 'rgba(5,7,11,0.68)',
            boxShadow: hudRingShadow,
            color: colors.blue,
            fontSize: 20,
            fontWeight: 950,
            textShadow: hudTextHighlight,
          }}
        >
          3 尺寸主图
        </div>
      </div>
    );
  }

  if (variant === 'cover-gallery') {
    const assets = stack.length > 0 ? stack.slice(0, 3) : primary ? [primary] : [];
    return (
      <div style={boardStyle}>
        <div style={{position: 'absolute', inset: 0, background: 'radial-gradient(circle at 50% 28%, rgba(255,255,255,0.10), transparent 44%), rgba(5,7,11,0.92)'}} />
        <div style={{position: 'absolute', left: 42, top: 38, color: colors.white, fontSize: 44, fontWeight: 950, textShadow: hudTextHighlight}}>
          {event.text}
        </div>
        <div style={{position: 'absolute', left: 44, top: 100, color: colors.blue, fontSize: 18, fontWeight: 950, textShadow: hudTextHighlight}}>
          素材图库
        </div>
        {assets.map((asset, index) => {
          const pop = spring({frame: Math.max(0, local - index * 8), fps, config: {damping: 16, stiffness: 150}});
          const positions = [
            {left: 100, top: 170, width: 270, height: 360, angle: -4},
            {left: 440, top: 160, width: 420, height: 315, angle: 0},
            {left: 860, top: 190, width: 480, height: 270, angle: 4},
          ];
          const pos = positions[index] ?? positions[0];
          return (
            <div
              key={`${asset}-${index}`}
              style={{
                position: 'absolute',
                ...pos,
                borderRadius: 0,
                overflow: 'visible',
                background: 'transparent',
                border: 'none',
                boxShadow: '0 30px 60px rgba(0,0,0,0.52), 0 10px 24px rgba(0,0,0,0.38)',
                transform: `rotate(${pos.angle}deg) scale(${interpolate(pop, [0, 1], [0.9, 1])})`,
              }}
            >
              <MaterialImage src={asset} fit="cover" />
            </div>
          );
        })}
      </div>
    );
  }

  if (variant === 'recording') {
    const recordingStyle: React.CSSProperties = {
      ...boardStyle,
      left: 0,
      top: 0,
      width: isPortrait ? canvasWidth : 1920,
      height: isPortrait ? canvasHeight : 1080,
      borderRadius: 0,
      transform: `scale(${scale})`,
      background: '#05070B',
    };
    return (
      <div style={recordingStyle}>
        {primary ? (
          <Sequence from={event.startFrame}>
            <MaterialAsset src={primary} fit="contain" startFrom={0} />
          </Sequence>
        ) : null}
        <div style={{position: 'absolute', inset: 0, background: 'linear-gradient(0deg, rgba(5,7,11,0.24), transparent 30%)'}} />
        <div style={{position: 'absolute', left: 48, top: 40, padding: '12px 18px', borderRadius: 12, background: 'rgba(5,7,11,0.68)', border: 'none', display: 'flex', alignItems: 'center', gap: 10, boxShadow: hudRingShadow}}>
          <Video size={22} color={colors.blue} strokeWidth={2.4} />
          <div style={{color: colors.white, fontSize: 22, fontWeight: 900, textShadow: hudTextHighlight}}>{event.text}</div>
        </div>
        <div style={{position: 'absolute', right: 64, bottom: 76, padding: '12px 18px', borderRadius: 10, color: colors.green, background: 'rgba(5,7,11,0.68)', border: 'none', fontSize: 22, fontWeight: 950, boxShadow: hudRingShadow, textShadow: hudTextHighlight}}>
          视频素材播放中
        </div>
      </div>
    );
  }

  return (
    <div style={boardStyle}>
      {primary ? <MaterialImage src={primary} fit="cover" /> : null}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'linear-gradient(90deg, rgba(5,7,11,0.62), transparent 42%), linear-gradient(0deg, rgba(5,7,11,0.3), transparent 35%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 42,
          top: 38,
          color: colors.white,
          fontSize: 44,
          fontWeight: 950,
          textShadow: hudTextHighlight,
        }}
      >
        {event.text}
      </div>
      <div
        style={{
          position: 'absolute',
          left: 96,
          top: 218,
          width: 360,
          height: 122,
          border: 'none',
          borderRadius: 18,
          boxShadow: '0 18px 36px rgba(0,0,0,0.38)',
        }}
      />
    </div>
  );
};
