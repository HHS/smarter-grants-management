"use client";

import SessionStorage from "src/services/sessionStorage/sessionStorage";

import { PostAuthRedirect } from "src/components/core/PostAuthRedirect";

export default function LogoutPage() {
  const redirectUrl = SessionStorage.getItem("post-auth-redirect");
  return (
    <PostAuthRedirect
      errorMessage="Unable to redirect properly on login"
      checkPiv={true}
      redirectUrl={redirectUrl}
    />
  );
}
