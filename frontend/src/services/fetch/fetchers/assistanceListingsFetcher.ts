import "server-only";

import { APIResponse } from "src/types/apiResponseTypes";
import {
  AssistanceListing,
  AssistanceListingSearchRequestBody,
} from "src/types/assistanceListingTypes";

import { fetchAssistanceListings } from "./fetchers";

// only the first page of matches is returned
const searchPageSize = 15;

// temporary proof of concept for the ALN search, expected to change with the ALN field
// work (#165, #166) and the search changes in #589
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
