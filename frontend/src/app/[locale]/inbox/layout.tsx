import { Metadata } from "next";
import { LayoutProps } from "src/types/generalTypes";

import { AuthenticationGate } from "src/components/core/AuthenticationGate";

export function generateMetadata(): Metadata {
  const meta = {
    title: "Inbox | Smarter Grants Management",
    description: "View tasks and messages for grants management",
  };
  return meta;
}

export default function InboxLayout({ children }: LayoutProps) {
  return <AuthenticationGate>{children}</AuthenticationGate>;
}
