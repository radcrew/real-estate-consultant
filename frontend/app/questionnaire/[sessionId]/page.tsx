"use client";

import { useParams, useRouter } from "next/navigation";

import { SearchWizard } from "@components/search/wizard";

export default function QuestionnaireSessionPage() {
  const router = useRouter();
  const params = useParams<{ sessionId?: string | string[] }>();
  const sessionId = Array.isArray(params.sessionId)
    ? params.sessionId[0]
    : params.sessionId;

  return (
    <SearchWizard
      sessionId={sessionId ?? null}
      onClose={() => router.push("/")}
    />
  );
}
