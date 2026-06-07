import type { Metadata } from "next";

import { AgentView } from "@components/agents/view";

type AgentPageProps = {
  params: Promise<{ name: string }>;
};

export const generateMetadata = async ({
  params,
}: AgentPageProps): Promise<Metadata> => {
  const { name } = await params;
  return { title: decodeURIComponent(name) };
};

const AgentPage = async ({ params }: AgentPageProps) => {
  const { name } = await params;
  return <AgentView broker={decodeURIComponent(name)} />;
};

export default AgentPage;
