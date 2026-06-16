import type { Metadata } from "next";

import { AdminIngestView } from "@components/admin/ingest";

export const metadata: Metadata = {
  title: "Ingestion",
  description: "Trigger and monitor listing ingestion runs",
};

const AdminIngestPage = () => <AdminIngestView />;

export default AdminIngestPage;
