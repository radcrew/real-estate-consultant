import type { Metadata } from "next";

import { AccountPage } from "@components/account/page";

export const metadata: Metadata = {
  title: "Account",
  description: "Manage your RadEstate account profile and security",
};

const Page = () => <AccountPage />;

export default Page;
