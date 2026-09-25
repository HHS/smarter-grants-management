import { readError } from "src/errors";
import { getApplicationPackageDetails } from "src/services/fetch/fetchers/applicationPackagesFetcher";

import { NextRequest } from "next/server";

export const getApplicationPackage = async (
  _request: NextRequest,
  { params }: { params: Promise<{ applicationPackageId: string }> },
): Promise<Response> => {
  const { applicationPackageId } = await params;

  try {
    const applicationPackage =
      await getApplicationPackageDetails(applicationPackageId);
    return new Response(JSON.stringify(applicationPackage), {
      status: 200,
      headers: {
        "Content-Type": "application/json",
      },
    });
  } catch (e) {
    const { status, message } = readError(e as Error, 500);
    return Response.json(
      {
        message: `Error attempting to fetch saved searches: ${message}`,
      },
      { status },
    );
  }
};
