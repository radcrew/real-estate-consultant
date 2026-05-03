import type { SearchResultsChip } from "@lib/search-results-handoff";

type SearchFilterProps = {
  chips: SearchResultsChip[];
};

export const SearchFilter = ({ chips }: SearchFilterProps) => {
  if (chips.length === 0) {
    return null;
  }

  return (
    <section
      className="rounded-lg border border-border bg-card px-4 py-4 sm:px-5"
      aria-labelledby="criteria-recap-heading"
    >
      <h2
        id="criteria-recap-heading"
        className="text-xs font-semibold uppercase tracking-wide text-muted-foreground"
      >
        Your search
      </h2>
      <ul className="mt-3 flex flex-wrap gap-2">
        {chips.map((chip, index) => (
          <li
            key={`${chip.label}:${chip.value}:${index}`}
            className="inline-flex max-w-full flex-col gap-0.5 rounded-md border border-border/80 bg-muted/40 px-3 py-2 text-left sm:max-w-[280px]"
          >
            <span className="text-[0.65rem] font-medium uppercase tracking-wide text-muted-foreground">
              {chip.label}
            </span>
            <span className="text-sm font-semibold leading-snug text-foreground">{chip.value}</span>
          </li>
        ))}
      </ul>
    </section>
  );
};
