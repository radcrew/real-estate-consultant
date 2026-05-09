import type { SummaryRow } from "../types";
import { ListChecks } from "lucide-react";

import { STYLES } from "./styles";

type SummaryPanelProps = {
  rows: SummaryRow[];
};

export const SummaryPanel = ({ rows }: SummaryPanelProps) => (
  <aside className={STYLES.panel}>
    <div className={STYLES.header}>
      <div className={STYLES.headerLeft}>
        <ListChecks className="size-4 text-amber-500" aria-hidden />
        <h3 className={STYLES.title}>Your Answers</h3>
      </div>
      <span className={STYLES.badge}>{rows.length}</span>
    </div>

    {rows.length === 0 ? (
      <div className={STYLES.placeholder}>
        Answers will appear here as you complete each step.
      </div>
    ) : (
      <div className={STYLES.rowList}>
        {rows.map((row) => (
          <div key={row.id} className={STYLES.rowItem}>
            <p className={STYLES.rowLabel}>{row.label}</p>
            <p className={STYLES.rowValue}>{row.value}</p>
          </div>
        ))}
      </div>
    )}
  </aside>
);
