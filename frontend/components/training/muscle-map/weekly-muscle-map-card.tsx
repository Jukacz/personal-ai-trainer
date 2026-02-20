import type { TrainingDay } from '@/lib/types';
import { buildWeeklyMuscleIntensity } from '@/lib/muscle-map';
import FrontMap from './front-map';
import BackMap from './back-map';

interface WeeklyMuscleMapCardProps {
  days: TrainingDay[];
}

function LegendItem({ label, color }: { label: string; color: string }) {
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
      <span>{label}</span>
    </div>
  );
}

export default function WeeklyMuscleMapCard({ days }: WeeklyMuscleMapCardProps) {
  const intensityByGroup = buildWeeklyMuscleIntensity(days);

  return (
    <section className="rounded-lg border bg-card/50 p-4">
      <div className="mb-3 space-y-2">
        <p className="text-sm font-semibold">Aktywacja mięśni w skali tygodnia</p>
        <div className="flex flex-wrap items-center gap-3">
          <LegendItem label="Bardzo niska" color="#fde68a" />
          <LegendItem label="Niska" color="#fcd34d" />
          <LegendItem label="Umiarkowana" color="#f59e0b" />
          <LegendItem label="Podwyższona" color="#fb923c" />
          <LegendItem label="Wysoka" color="#ef4444" />
          <LegendItem label="Bardzo wysoka" color="#b91c1c" />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <p className="mb-2 text-center text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Przód
          </p>
          <FrontMap intensityByGroup={intensityByGroup} />
        </div>
        <div>
          <p className="mb-2 text-center text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Tył
          </p>
          <BackMap intensityByGroup={intensityByGroup} />
        </div>
      </div>
    </section>
  );
}
