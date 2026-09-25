import { fetchApiKeyLogin } from "./fetchers";

export const getJWTWithApiKeyLogin = async (
  apiKey: string,
): Promise<string> => {
  const response = await fetchApiKeyLogin({
    additionalHeaders: { "X-API-KEY": apiKey },
  });
  const {
    data: { jwt_token },
  } = (await response.json()) as {
    data: { jwt_token: string };
  };
  return jwt_token;
};
