import { useEffect, useRef } from 'react';
import BackSvg from './generated/Back';
import {
  BACK_GROUP_IDS,
  type AnyMuscleIntensityByGroup,
} from '@/lib/muscle-map';

interface BackMapProps {
  intensityByGroup: AnyMuscleIntensityByGroup;
}

function levelColor(level: number, neutralColor: string): string {
  if (level === 6) return '#b91c1c';
  if (level === 5) return '#ef4444';
  if (level === 4) return '#fb923c';
  if (level === 3) return '#f59e0b';
  if (level === 2) return '#fcd34d';
  if (level === 1) return '#fde68a';
  return neutralColor;
}

export default function BackMap({ intensityByGroup }: BackMapProps) {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) {
      return;
    }

    const isDarkTheme = document.documentElement.classList.contains('dark');
    const neutralColor = isDarkTheme ? '#000000' : '#ffffff';

    for (const groupId of BACK_GROUP_IDS) {
      const group = root.querySelector(`#${groupId}`) as SVGGElement | null;
      if (!group) {
        continue;
      }
      group.style.color = levelColor(intensityByGroup[groupId], neutralColor);
    }
  }, [intensityByGroup]);

  return (
    <div ref={rootRef} className="muscle-map-back w-full">
      <BackSvg className="h-auto w-full" />
    </div>
  );
}
