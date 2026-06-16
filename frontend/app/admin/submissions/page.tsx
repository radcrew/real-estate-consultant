import type { Metadata } from "next";

import { AdminSubmissionsView } from "@components/admin/submissions";

export const metadata: Metadata = {
  title: "Submissions",
  description: "Review submitted property listings",
};

const AdminSubmissionsPage = () => <AdminSubmissionsView />;

export default AdminSubmissionsPage;
