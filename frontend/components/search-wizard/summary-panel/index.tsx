import type { SummaryRow } from "../types";
import { ListChecks } from "lucide-react";

import { styles } from "./styles";

type SummaryPanelProps = {
  rows: SummaryRow[];
};

export const SummaryPanel = ({ rows }: SummaryPanelProps) => (
  <aside className={styles.panel}>
    <div className={styles.header}>
      <div className={styles.headerLeft}>
        <ListChecks className="size-4 text-amber-500" aria-hidden />
        <h3 className={styles.title}>Your Answers</h3>
      </div>
      <span className={styles.badge}>{rows.length}</span>
    </div>

    {rows.length === 0 ? (
      <div className={styles.placeholder}>
        Answers will appear here as you complete each step.
      </div>
    ) : (
      <div className={styles.rowList}>
        {rows.map((row) => (
          <div key={row.id} className={styles.rowItem}>
            <p className={styles.rowLabel}>{row.label}</p>
            <p className={styles.rowValue}>{row.value}</p>
          </div>
        ))}
      </div>
    )}
  </aside>
);
