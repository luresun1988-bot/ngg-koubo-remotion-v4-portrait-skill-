import type {CSSProperties} from 'react';

export const colors = {
  black: '#05070b',
  panel: 'rgba(5,7,11,0.62)',
  panelSolid: 'rgba(8, 12, 18, 0.94)',
  panelLight: 'rgba(16, 22, 34, 0.68)',
  white: '#f0f0f0',
  muted: '#cccccc',
  blue: '#067ef6',
  green: '#20e0b0',
  red: '#d83c30',
  amber: '#c08a30',
  purple: '#663684',
  line: 'rgba(255,255,255,0.14)',
};

export const fontStack =
  '"SourceHanSansSC", "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", Arial, sans-serif';

export const hudRingShadow =
  '0 30px 72px rgba(0,0,0,0.68), 0 10px 24px rgba(0,0,0,0.54)';

export const mediaWindowShadow =
  '0 24px 56px rgba(0,0,0,0.66), 0 0 0 5px rgba(5,7,11,0.20)';

export const hudTextHighlight =
  '0 3px 0 rgba(0,0,0,0.82), 0 8px 12px rgba(0,0,0,0.88), 0 18px 38px rgba(0,0,0,0.72), 0 0 2px rgba(255,255,255,0.16)';

export const captionStyle: CSSProperties = {
  position: 'absolute',
  left: '50%',
  bottom: 86,
  transform: 'translateX(-50%)',
  maxWidth: 960,
  padding: '14px 26px',
  borderRadius: 10,
  background: 'rgba(8, 10, 15, 0.72)',
  color: colors.white,
  fontFamily: fontStack,
  fontWeight: 800,
  fontSize: 36,
  lineHeight: 1.16,
  textAlign: 'center',
  boxShadow: '0 18px 40px rgba(0, 0, 0, 0.36)',
  whiteSpace: 'normal',
  overflow: 'visible',
  textOverflow: 'clip',
  overflowWrap: 'break-word',
};

export const cardStyle: CSSProperties = {
  borderRadius: 14,
  background: colors.panel,
  border: 'none',
  boxShadow: hudRingShadow,
  color: colors.white,
  fontFamily: fontStack,
};
