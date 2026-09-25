"use server";

import { UnauthorizedError } from "src/errors";
import { getJWTWithApiKeyLogin } from "src/services/fetch/fetchers/apiKeyLoginFetcher";

import { redirect } from "next/navigation";

type ApiKeyLoginActionState = {
  error?: boolean;
  success?: boolean;
  unauthenticated?: boolean;
};

export const apiKeyLoginAction = async (
  _prevState: ApiKeyLoginActionState,
  loginFormData: FormData,
): Promise<ApiKeyLoginActionState> => {
  const apiKey = loginFormData.get("apiKey");
  if (!apiKey) {
    return { error: true };
  }
  let token: string;
  try {
    token = await getJWTWithApiKeyLogin(apiKey as string);
    if (!token) {
      throw new Error("no token!");
    }
  } catch (e) {
    console.error("Failed login", e);
    // I know, this should be an unauthenticated error, but fixing that is out of scope rn
    if (e instanceof UnauthorizedError) {
      return { unauthenticated: true, success: false };
    }
    return {
      error: true,
      success: false,
    };
  }
  redirect(`/api/auth/callback?token=${token}`);
};
