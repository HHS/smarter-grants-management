"use client";

import SessionStorage from "src/services/sessionStorage/sessionStorage";

import { PostAuthRedirect } from "src/components/core/PostAuthRedirect";

export default function LoginPage() {
  const redirectURL = SessionStorage.getItem("post-auth-redirect");
  return (
    <PostAuthRedirect
      errorMessage="Unable to redirect properly on login"
      checkPiv={true}
      redirectURL={redirectURL}
    />
  );
}
