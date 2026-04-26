import type { SummaryRow } from "../types";

import { styles } from "./styles";

type SummaryPanelProps = {
  rows: SummaryRow[];
};

export const SummaryPanel = ({ rows }: SummaryPanelProps) => (
  <aside className={styles.panel}>
    <div className={styles.headerStack}>
      <p className={styles.eyebrow}>Search draft</p>
      <h3 className={styles.title}>Answers so far</h3>
    </div>

    <div className={styles.rowList}>
      {rows.map((row, index) => (
        <div key={row.id} className={styles.rowCard}>
          <p className={styles.rowStep}>Step {index + 1}</p>
          <p className={styles.rowLabel}>{row.label}</p>
          <p className={styles.rowValue}>{row.value}</p>
        </div>
      ))}
    </div>
  </aside>
);
