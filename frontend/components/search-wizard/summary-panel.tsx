import type { SummaryRow } from "./types";

type SummaryPanelProps = {
  rows: SummaryRow[];
};

const PANEL_CLASSNAME = "flex flex-col border border-border/70 bg-slate-950 p-4 text-slate-100 shadow-[0_20px_70px_-45px_rgba(15,23,42,0.7)] sm:p-5";

export const SummaryPanel = ({ rows }: SummaryPanelProps) => (
  <aside className={PANEL_CLASSNAME}>
    <div className="space-y-1.5">
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-amber-200/80">
        Search draft
      </p>
      <h3 className="text-base font-semibold sm:text-lg">Answers so far</h3>
    </div>

    <div className="mt-4 space-y-2.5">
      {rows.map((row, index) => (
        <div
          key={row.id}
          className="border border-white/10 bg-white/4 px-3 py-2.5"
        >
          <p className="text-xs uppercase tracking-[0.18em] text-slate-400">
            Step {index + 1}
          </p>
          <p className="mt-1 text-sm font-medium text-slate-100">{row.label}</p>
          <p className="mt-1 text-sm text-slate-300">{row.value}</p>
        </div>
      ))}
    </div>
  </aside>
);
