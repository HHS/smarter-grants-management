import { readError } from "src/errors";
import { getSession } from "src/services/auth/session";
import { getAssistanceListingSearchResults } from "src/services/fetch/fetchers/assistanceListingsFetcher";

import { NextRequest } from "next/server";

export async function searchAssistanceListings(request: NextRequest) {
  const currentSession = await getSession();
  if (!currentSession) {
    return Response.json(
      { message: "Not logged in, cannot search assistance listings" },
      { status: 401 },
    );
  }

  const { searchTerm } = (await request.json()) as { searchTerm?: string };
  if (!searchTerm) {
    return Response.json(
      { message: "Search term is required" },
      { status: 400 },
    );
  }

  try {
    const assistanceListings =
      await getAssistanceListingSearchResults(searchTerm);

    return Response.json({ data: assistanceListings });
  } catch (e) {
    const { status, message } = readError(e as Error, 500);
    return Response.json(
      {
        message: `Error attempting to search assistance listings: ${message}`,
      },
      { status },
    );
  }
}
