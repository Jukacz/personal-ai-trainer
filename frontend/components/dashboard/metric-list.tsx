'use client';

import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

export interface MetricListItemBase {
  id: string;
  label: string;
  value: number;
  color?: string;
}

interface MetricListProps<T extends MetricListItemBase> {
  items: T[];
  className?: string;
  renderValue?: (item: T) => ReactNode;
}

export function MetricList<T extends MetricListItemBase>({
  items,
  className,
  renderValue,
}: MetricListProps<T>) {
  return (
    <div className={cn('flex flex-wrap gap-4 text-xs text-muted-foreground', className)}>
      {items.map((item) => (
        <div key={item.id} className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: item.color }} />
          <span>
            {item.label}: {renderValue ? renderValue(item) : item.value}
          </span>
        </div>
      ))}
    </div>
  );
}
