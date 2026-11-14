"use client";

import { useId, useState } from "react";
import { TypedButton } from "@/shared/components/notebook";

type Option = { value: string; label: string };

/** Pick from the offered labels, or add your own. A picked label has a red tick. */
export function ChoiceChips({
  options,
  selected,
  onToggle,
  addLink,
  addLabel,
  addPlaceholder,
  addButton,
  showFirst,
  showMoreLabel,
}: {
  options: Option[];
  selected: string[];
  onToggle: (label: string) => void;
  /** The quiet link that reveals the input. */
  addLink: string;
  addLabel: string;
  addPlaceholder: string;
  addButton: string;
  /** Offer only this many at first; the rest behind "show more". Picked ones always show. */
  showFirst?: number;
  showMoreLabel?: (count: number) => string;
}) {
  const inputId = useId();
  const [own, setOwn] = useState("");
  const [showAll, setShowAll] = useState(false);
  const [adding, setAdding] = useState(false);
  const isPicked = (label: string) => selected.some((s) => s.toLocaleLowerCase() === label.toLocaleLowerCase());
  const offered = new Set(options.map((o) => o.label.toLocaleLowerCase()));
  const extra = selected.filter((s) => !offered.has(s.toLocaleLowerCase()));
  const limit = showAll || showFirst === undefined ? options.length : showFirst;
  const shown = options.filter((o, index) => index < limit || isPicked(o.label));
  const hidden = options.length - shown.length;

  const addOwn = () => {
    if (own.trim()) onToggle(own);
    setOwn("");
  };

  return (
    <div>
      <ul className="flex flex-wrap gap-2">
        {[...shown.map((o) => o.label), ...extra].map((label) => {
          const picked = isPicked(label);
          return (
            <li key={label}>
              <button
                type="button"
                aria-pressed={picked}
                onClick={() => onToggle(label)}
                className={
                  "min-h-11 rounded-sm border px-3 font-type text-case font-normal " +
                  (picked
                    ? "border-accent-red bg-paper-card text-accent-red"
                    : "border-rule-card bg-paper-card text-ink")
                }
              >
                <span aria-hidden="true" className="mr-1.5 inline-block w-3">
                  {picked ? "✓" : "+"}
                </span>
                {label}
              </button>
            </li>
          );
        })}
        {hidden > 0 && showMoreLabel ? (
          <li>
            <button
              type="button"
              onClick={() => setShowAll(true)}
              className="min-h-11 px-1 font-type text-case font-normal underline decoration-dotted decoration-2 underline-offset-[5px]"
            >
              {showMoreLabel(hidden)}
            </button>
          </li>
        ) : null}
      </ul>
      {adding ? (
        <div className="mt-3 flex items-end gap-2">
          <div className="min-w-0 flex-1">
            <label htmlFor={inputId} className="font-type text-label-sm text-ink-muted">
              {addLabel}
            </label>
            <input
              id={inputId}
              autoFocus
              value={own}
              maxLength={60}
              placeholder={addPlaceholder}
              onChange={(e) => setOwn(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  addOwn();
                }
              }}
              className="mt-1 h-11 w-full rounded-sm border border-rule-card bg-paper-card px-3 font-story text-body-sm placeholder:text-ink-faint"
            />
          </div>
          <button
            type="button"
            onClick={addOwn}
            className="h-11 shrink-0 rounded-sm border border-ink px-3 font-type text-case"
          >
            {addButton}
          </button>
        </div>
      ) : (
        <TypedButton onClick={() => setAdding(true)} className="mt-1 text-left">
          {addLink}
        </TypedButton>
      )}
    </div>
  );
}
