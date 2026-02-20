import type { TrainingDay } from '@/lib/types';
import { buildMuscleIntensity } from '@/lib/muscle-map';
import FrontMap from './front-map';
import BackMap from './back-map';

interface MuscleMapCardProps {
  day: TrainingDay;
}

function LegendItem({ label, color }: { label: string; color: string }) {
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
      <span>{label}</span>
    </div>
  );
}

export default function MuscleMapCard({ day }: MuscleMapCardProps) {
  const intensityByGroup = buildMuscleIntensity(day);

  return (
    <section className="mb-6 rounded-lg border bg-card/50 p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <p className="text-sm font-semibold">Aktywowane mięśnie</p>
        <div className="flex flex-wrap items-center gap-3">
          <LegendItem label="Niska" color="#fde68a" />
          <LegendItem label="Średnia" color="#fcd34d" />
          <LegendItem label="Wysoka" color="#f59e0b" />
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
