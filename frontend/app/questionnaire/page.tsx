"use client";

import { useRouter } from "next/navigation";

import { SearchWizard } from "@components/search-wizard";

export default function QuestionnairePage() {
  const router = useRouter();

  return <SearchWizard onClose={() => router.push("/")} />;
}
