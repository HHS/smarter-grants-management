import { readError } from "src/errors";
import { getSession } from "src/services/auth/session";
import { deleteApplicationPackageInstructions } from "src/services/fetch/fetchers/grantorAnnouncementFetcher";

import { NextRequest, NextResponse } from "next/server";

export async function DELETE(
  _request: NextRequest,
  context: {
    params: Promise<{
      announcementId: string;
      applicationPackageId: string;
      fileId: string;
    }>;
  },
) {
  const {
    announcementId,
    applicationPackageId: applicationPackageId,
    fileId: applicationPackageInstructionId,
  } = await context.params;

  if (!announcementId) {
    return NextResponse.json(
      { error: "Announcement ID is required" },
      { status: 400 },
    );
  }
  if (!applicationPackageId) {
    return NextResponse.json(
      { error: "ApplicationPackage ID is required" },
      { status: 400 },
    );
  }
  if (!applicationPackageInstructionId) {
    return NextResponse.json(
      { error: "ApplicationPackage Instruction ID is required" },
      { status: 400 },
    );
  }

  const currentSession = await getSession();
  if (!currentSession) {
    return NextResponse.json(
      {
        error:
          "Not logged in, cannot delete applicationPackage instructions file",
      },
      { status: 401 },
    );
  }

  try {
    const response = await deleteApplicationPackageInstructions(
      announcementId,
      applicationPackageId,
      applicationPackageInstructionId,
    );

    return NextResponse.json({ data: response });
  } catch (error) {
    console.error(
      "Error deleting applicationPackage instructions file:",
      error,
    );
    const { status, message, cause } = readError(error as Error, 500);

    return NextResponse.json(
      {
        error: message,
        errorType: cause?.type,
      },
      { status },
    );
  }
}
