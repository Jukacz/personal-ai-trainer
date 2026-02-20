import { useEffect, useRef } from 'react';
import FrontSvg from './generated/Front';
import {
  FRONT_GROUP_IDS,
  type AnyMuscleIntensityByGroup,
} from '@/lib/muscle-map';

interface FrontMapProps {
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

export default function FrontMap({ intensityByGroup }: FrontMapProps) {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = rootRef.current;
    if (!root) {
      return;
    }

    const isDarkTheme = document.documentElement.classList.contains('dark');
    const neutralColor = isDarkTheme ? '#000000' : '#ffffff';

    for (const groupId of FRONT_GROUP_IDS) {
      const group = root.querySelector(`#${groupId}`) as SVGGElement | null;
      if (!group) {
        continue;
      }
      group.style.color = levelColor(intensityByGroup[groupId], neutralColor);
    }
  }, [intensityByGroup]);

  return (
    <div ref={rootRef} className="muscle-map-front w-full">
      <FrontSvg className="h-auto w-full" />
    </div>
  );
}
