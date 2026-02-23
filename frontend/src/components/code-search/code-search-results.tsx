import type { ICDCode } from "@/lib/api-types";

interface CodeSearchResultsProps {
  codes: ICDCode[];
  onSelect: (code: ICDCode) => void;
}

export function CodeSearchResults({ codes, onSelect }: CodeSearchResultsProps) {
  if (codes.length === 0) {
    return (
      <div className="p-4 text-center text-sm text-muted-foreground">
        No matching codes found.
      </div>
    );
  }

  return (
    <div className="max-h-64 overflow-y-auto">
      {codes.map((code) => (
        <button
          key={code.code}
          className="flex w-full items-center gap-3 px-4 py-2 text-left text-sm hover:bg-accent transition-colors"
          onClick={() => onSelect(code)}
        >
          <span className="font-mono font-semibold">{code.code}</span>
          <span className="truncate text-muted-foreground">
            {code.description}
          </span>
        </button>
      ))}
    </div>
  );
}
