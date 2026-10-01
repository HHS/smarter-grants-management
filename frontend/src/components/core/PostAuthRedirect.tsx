import SessionStorage from "src/services/sessionStorage/sessionStorage";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";
import { Grid, GridContainer } from "@trussworks/react-uswds";

import { USWDSIcon } from "./USWDSIcon";

type PostAuthRedirectProps = {
  checkPiv?: boolean;
  displayMessage?: string;
  errorMessage: string;
  redirectUrl?: string | null;
};

export function PostAuthRedirect({
  checkPiv,
  displayMessage,
  errorMessage,
  redirectUrl,
}: PostAuthRedirectProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  useEffect(() => {
    try {
      SessionStorage.removeItem("post-auth-redirect");
      if (checkPiv && searchParams.get("pivError")) {
        SessionStorage.setItem("showPivError", "true");
      }

      if (redirectUrl?.substring(0, 1) !== "/") {
        router.push("/");
      }
      router.push(redirectUrl || "/");
      return () => {
        return SessionStorage.removeItem("post-auth-redirect");
      };
    } catch (e) {
      console.error(errorMessage, e);
      router.push("/");
    }
  }, [router, searchParams, errorMessage, checkPiv, redirectUrl]);

  return (
    <GridContainer className="margin-y-5">
      <Grid className="flex-align-center display-flex">
        <USWDSIcon name="autorenew" className="usa-icon--size-3" />
        <div className="padding-left-05 padding-top-05 font-sans-md">
          {displayMessage || "Redirecting..."}
        </div>
      </Grid>
    </GridContainer>
  );
}
