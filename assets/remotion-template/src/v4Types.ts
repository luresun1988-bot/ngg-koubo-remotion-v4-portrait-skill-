export type SceneType =
  | 'Hook'
  | 'Explanation'
  | 'Proof'
  | 'Process'
  | 'Contrast'
  | 'CleanMaterial'
  | 'CTA';

export type Scene = {
  id: string;
  type: SceneType;
  segmentId?: string;
  startFrame: number;
  endFrame: number;
  semanticRole: string;
  presenterLayout: 'fullscreen' | 'large' | 'side' | 'pip' | 'none';
  materialLayout: 'none' | 'main' | 'stack' | 'clean';
  intent?: string;
  sourceVideo: string;
  narrationText?: string;
};

export type CaptionCue = {
  id: string;
  sceneId?: string;
  startFrame: number;
  endFrame: number;
  text: string;
  highlightWords?: string[];
  keywords?: string[];
};

export type CaptionTimeline = {
  sourceType: 'srt' | 'vtt' | 'alignment-json' | 'asr' | 'segment-video-duration' | 'provided' | string;
  sourcePath?: string;
  method: string;
  generatedBy?: string;
  notes?: string;
};

export type SemanticBeat = {
  id: string;
  sceneId: string;
  startFrame: number;
  endFrame: number;
  text: string;
  semanticIntent: string;
  visualForm: string;
  beatGroupId?: string;
  confidence?: number;
  keywords?: string[];
  requiredChecks?: string[];
  sourceCueIds?: string[];
  semanticModifiers?: string[];
  entities?: string[];
  themeThesisCandidate?: boolean;
  suggestedDepthKeyword?: string;
  requiresApproval?: boolean;
  timingClass?: 'short-lightweight' | 'intentional-clean' | string;
  routingDecision?: string;
};

export type VisualEvent = {
  id: string;
  sceneId: string;
  type:
    | 'kineticTitle'
    | 'captionHighlight'
    | 'cornerChapterLabel'
    | 'infoCard'
    | 'statusSticker'
    | 'iconPulse'
    | 'materialMain'
    | 'materialZoom'
    | 'highlightBox'
    | 'presenterReposition'
    | 'transitionPushZoom'
    | 'ctaTitle'
    | 'bigJudgement'
    | 'dataPunch'
    | 'quoteSource'
    | 'flowPath'
    | 'statusStack'
    | 'platformFanout'
    | 'evidenceWindow'
    | 'ctaRecommend'
    | 'metricSpotlight'
    | 'workflowDashboard'
    | 'capabilityShare'
    | 'sceneLockGrid'
    | 'transformationStack'
    | 'semanticProblemMap'
    | 'automationHandoff'
    | 'topicKeyword'
    | 'claimStrip'
    | 'ratioGallery'
    | 'depthKeyword';
  startFrame: number;
  endFrame: number;
  text?: string;
  subtext?: string;
  title?: string;
  status?: string;
  processingText?: string;
  emphasisWords?: string[];
  iconName?: string;
  numericValue?: number;
  numericPrefix?: string;
  numericSuffix?: string;
  unit?: string;
  maxValue?: number;
  beatGroupId?: string;
  sourceBeatId?: string;
  timingClass?: string;
  timingAnchor?: string;
  anchorCueId?: string;
  densityMode?: 'dense' | 'dense-strong' | 'light' | 'proof-focus' | string;
  densityReason?: string;
  presenterPeakScale?: number;
  /** Legacy compatibility only; presenter-impact-punch now holds presenterPeakScale until semantic exit. */
  presenterSettleScale?: number;
  transformationSourceCueIds?: string[];
  internalSteps?: Array<{
    id?: string;
    label?: string;
    text?: string;
    value?: string;
    iconName?: string;
    status?: string;
    sourceCueIds?: string[];
    role?: 'source' | 'target' | 'driver' | 'result' | string;
  }>;
  assetPath?: string;
  assetStack?: string[];
  foregroundAssetPath?: string;
  approvalStatus?: 'candidate' | 'approved' | 'rejected';
  ctaProvenance?: {
    kind: 'action' | 'keyword' | 'claim' | string;
    sourceText: string;
    action?: string;
    keyword?: string;
  };
  semanticRole: string;
  motionType: string;
  style?: string;
  safeArea?: string;
};

export type AudioCue = {
  id: string;
  type: 'sfx' | 'bgm' | 'source' | 'silence';
  startFrame?: number;
  endFrame?: number;
  durationFrames?: number;
  sfxIntent?: string;
  sfxId?: string;
  path?: string;
  volumeDb?: number;
  duckUnderVoice?: boolean;
  status?: 'active' | 'suggested' | 'pending-selection' | 'pending-generation' | 'disabled' | 'muted' | string;
  confidence?: number;
  sourceBeatId?: string;
  sourceEventId?: string;
  suggestedBy?: string;
  source?: string;
  loop?: boolean;
  fadeInFrames?: number;
  fadeOutFrames?: number;
  notes?: string;
};

export type PresenterAudio = {
  mode: 'embedded' | 'normalized-wav' | 'none';
  path?: string;
  sampleRate?: number;
  syncOffsetFrames?: number;
  syncEvidence?: string;
  normalizationReportPath?: string;
};

export type VisualScript = {
  schemaVersion: 'ngg-koubo-remotion-v4-portrait';
  projectConfigPath?: string;
  metadata?: Record<string, unknown>;
  sourceVideoMode?: 'raw-presenter' | 'segmented-presenter' | 'precomposed-video' | string;
  presenterAudio?: PresenterAudio;
  captionRenderMode?: 'embedded' | 'none';
  packagingDensity?: 'dense' | 'light' | string;
  composition: {
    format: '9:16';
    width: 1080;
    height: 1920;
    fps: number;
    durationFrames: number;
  };
  captionTimeline?: CaptionTimeline;
  researchNotes: unknown[];
  media: unknown[] | Record<string, unknown>;
  scenes: Scene[];
  semanticBeats?: SemanticBeat[];
  captionCues: CaptionCue[];
  visualEvents: VisualEvent[];
  audioCues: AudioCue[];
  qaFrames: unknown[];
};
