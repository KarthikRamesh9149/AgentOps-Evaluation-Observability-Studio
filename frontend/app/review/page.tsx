"use client";

import { useEffect, useState } from "react";
import { DataTable } from "@/components/DataTable";
import { ErrorState, LoadingState } from "@/components/State";
import { client } from "@/lib/api";

export default function ReviewPage() {
  const [reviews, setReviews] = useState<unknown[]>();
  const [error, setError] = useState<unknown>();
  useEffect(() => {
    client.projects().then(async (projects) => setReviews(projects[0] ? await client.reviews(projects[0].project_id) : [])).catch(setError);
  }, []);
  if (error) return <ErrorState error={error} />;
  if (!reviews) return <LoadingState />;
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-semibold">Human Review</h1>
      <DataTable rows={reviews as Record<string, string>[]} columns={[
        { header: "Case", cell: (r) => r.case_id ?? "No reviews yet" },
        { header: "Label", cell: (r) => r.reviewer_label ?? "" },
        { header: "Note", cell: (r) => r.reviewer_note ?? "" }
      ]} />
    </div>
  );
}
