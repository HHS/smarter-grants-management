import "server-only";

import { APIResponse } from "src/types/apiResponseTypes";
import {
  AssistanceListing,
  AssistanceListingSearchRequestBody,
} from "src/types/assistanceListingTypes";

import { fetchAssistanceListings } from "./fetchers";

// only the first page of matches is returned
const searchPageSize = 15;

export const getAssistanceListingSearchResults = async (
  query: string,
): Promise<AssistanceListing[]> => {
  const response = await fetchAssistanceListings({
    subPath: "search",
    body: {
      query,
      pagination: { page_offset: 1, page_size: searchPageSize },
    } satisfies AssistanceListingSearchRequestBody,
  });
  const responseBody = (await response.json()) as APIResponse;

  return (responseBody.data as AssistanceListing[]) || [];
};
