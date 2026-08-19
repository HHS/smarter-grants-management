import { environment } from "src/constants/environments";
import { ApiMethod } from "src/types/generalTypes";

export interface EndpointConfig {
  basePath: string;
  version: string;
  namespace: string;
  method: ApiMethod;
  requiresAuth?: boolean;
}

export const fetchCompetitionEndpoint = {
  basePath: environment.API_URL,
  version: "alpha",
  namespace: "competitions",
  method: "GET" as ApiMethod,
};

export const fetchAwardRecommendationEndpoint = {
  basePath: environment.API_URL,
  version: "alpha",
  namespace: "award-recommendations",
  method: "GET" as ApiMethod,
  requiresAuth: true,
};

export const toDynamicAwardRecommendationEndpoint = (
  type: "POST" | "PUT" | "DELETE",
) => {
  return {
    basePath: environment.API_URL,
    version: "alpha",
    namespace: "award-recommendations",
    method: type as ApiMethod,
    requiresAuth: true,
  };
};

export const fetchFormsEndpoint = {
  basePath: environment.API_URL,
  version: "v1",
  namespace: "forms",
  method: "GET" as ApiMethod,
};

export const fetchCompetitionFormsEndpoint = {
  basePath: environment.API_URL,
  version: "alpha",
  namespace: "competitions",
  method: "PUT" as ApiMethod,
  requiresAuth: true,
};

export const userLogoutEndpoint = {
  basePath: environment.API_URL,
  version: "v1",
  namespace: "users/token/logout",
  method: "POST" as ApiMethod,
  requiresAuth: true,
};

export const toDynamicUsersEndpoint = (
  type: "POST" | "DELETE" | "PUT" | "GET",
) => {
  return {
    basePath: environment.API_URL,
    version: "v1",
    namespace: "users",
    method: type as ApiMethod,
    requiresAuth: true,
  };
};

export const userRefreshEndpoint = {
  basePath: environment.API_URL,
  version: "v1",
  namespace: "users/token/refresh",
  method: "POST" as ApiMethod,
  requiresAuth: true,
};

export const toDynamicGrantorAgenciesEndpoint = (
  type: "POST" | "GET" | "PUT" | "DELETE",
) => {
  return {
    basePath: environment.API_URL,
    version: "v1",
    namespace: "grantors/agencies",
    method: type as ApiMethod,
    requiresAuth: true,
  };
};

export const toDynamicGrantorOpportunityEndpoint = (
  type: "POST" | "DELETE" | "GET" | "PUT",
) => {
  return {
    basePath: environment.API_URL,
    version: "v1",
    namespace: "grantors/opportunities",
    method: type as ApiMethod,
    requiresAuth: true,
  };
};

export const getLocalUsersEndpoint = {
  basePath: environment.API_URL,
  version: "",
  namespace: "local/local-users",
  method: "GET" as ApiMethod,
};

export const toDynamicFilesEndpoint = (type: "POST" | "GET") => ({
  basePath: environment.API_URL,
  version: "v1",
  namespace: "files",
  method: type as ApiMethod,
  requiresAuth: true,
});
