import { Badge } from "@/components/ui/badge";
import { formatSimilarity } from "@/lib/format";
import type { SimilarPatient } from "@/lib/api-types";

interface SimilarPatientCardProps {
  patient: SimilarPatient;
}

export function SimilarPatientCard({ patient }: SimilarPatientCardProps) {
  return (
    <div className="rounded-lg border p-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">
          {patient.admission_id
            ? `Patient #${patient.admission_id}`
            : "Unknown Patient"}
        </span>
        <Badge variant="secondary" className="font-mono text-xs">
          {formatSimilarity(patient.similarity)} similar
        </Badge>
      </div>
      {patient.shared_codes.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {patient.shared_codes.map((code) => (
            <Badge key={code} variant="outline" className="text-xs">
              {code}
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
