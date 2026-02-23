"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";
import { useCodeSearch } from "@/hooks/use-code-search";
import { CodeSearchResults } from "./code-search-results";
import type { ICDCode } from "@/lib/api-types";

interface CodeSearchDialogProps {
  onSelect?: (code: ICDCode) => void;
}

export function CodeSearchDialog({ onSelect }: CodeSearchDialogProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const { data, isLoading } = useCodeSearch(query);

  function handleSelect(code: ICDCode) {
    onSelect?.(code);
    setOpen(false);
    setQuery("");
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="gap-1.5">
          <Search className="h-3.5 w-3.5" />
          Search Codes
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Search ICD-9 Codes</DialogTitle>
        </DialogHeader>
        <Input
          placeholder="Search by code or description..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />
        {isLoading ? (
          <div className="p-4 text-center text-sm text-muted-foreground">
            Searching...
          </div>
        ) : data ? (
          <CodeSearchResults codes={data.codes} onSelect={handleSelect} />
        ) : (
          <div className="p-4 text-center text-sm text-muted-foreground">
            Type at least 2 characters to search.
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
