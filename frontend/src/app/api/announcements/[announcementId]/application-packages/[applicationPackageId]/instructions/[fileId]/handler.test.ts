import { NotFoundError } from "src/errors";
import * as sessionModule from "src/services/auth/session";
import * as grantorAnnouncementFetcherModule from "src/services/fetch/fetchers/grantorAnnouncementFetcher";

import { NextRequest, NextResponse } from "next/server";

import { DELETE } from "./handler";

jest.mock("src/services/auth/session");
jest.mock("src/services/fetch/fetchers/grantorAnnouncementFetcher");

jest.mock("src/services/auth/sessionUtils", () => ({
  decrypt: jest.fn(),
  encrypt: jest.fn(),
  CLIENT_JWT_ENCRYPTION_ALGORITHM: "HS256",
  API_JWT_ENCRYPTION_ALGORITHM: "RS256",
  newExpirationDate: () => new Date(0),
}));

const mockSession = {
  user_id: "test-user-id",
  email: "test@example.com",
  token: "test-token",
  session_duration_minutes: 60,
};

jest.mock("next/server", () => ({
  NextRequest: class NextRequest {},
  NextResponse: {
    json: jest.fn(),
  },
}));

const buildContext = (
  announcementId = "announcement-123",
  applicationPackageId = "applicationPackage-123",
  fileId = "instruction-123",
) => ({
  params: Promise.resolve({
    announcementId,
    applicationPackageId: applicationPackageId,
    fileId,
  }),
});

describe("DELETE applicationPackage instruction handler", () => {
  beforeEach(() => {
    jest.clearAllMocks();

    (NextResponse.json as jest.Mock).mockImplementation(
      (data: unknown, init?: ResponseInit) => {
        const status = init?.status || 200;
        return {
          json: jest.fn().mockResolvedValue(data),
          status,
          ok: status >= 200 && status < 300,
        };
      },
    );

    (sessionModule.getSession as jest.Mock).mockResolvedValue(mockSession);
    (
      grantorAnnouncementFetcherModule.deleteApplicationPackageInstructions as jest.Mock
    ).mockResolvedValue({
      data: {},
      status_code: 200,
      message: "Instruction deleted",
    });
  });

  it("deletes a applicationPackage instruction successfully", async () => {
    const response = await DELETE({} as NextRequest, buildContext());

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      data: {
        data: {},
        status_code: 200,
        message: "Instruction deleted",
      },
    });
    expect(sessionModule.getSession).toHaveBeenCalledTimes(1);
    expect(
      grantorAnnouncementFetcherModule.deleteApplicationPackageInstructions,
    ).toHaveBeenCalledWith(
      "announcement-123",
      "applicationPackage-123",
      "instruction-123",
    );
  });

  it.each([
    [
      "announcementId",
      "",
      "applicationPackage-123",
      "instruction-123",
      "Announcement ID is required",
    ],
    [
      "applicationPackageId",
      "announcement-123",
      "",
      "instruction-123",
      "ApplicationPackage ID is required",
    ],
    [
      "fileId",
      "announcement-123",
      "applicationPackage-123",
      "",
      "ApplicationPackage Instruction ID is required",
    ],
  ])(
    "returns 400 when %s is missing",
    async (_name, announcementId, applicationPackageId, fileId, error) => {
      const response = await DELETE(
        {} as NextRequest,
        buildContext(announcementId, applicationPackageId, fileId),
      );

      expect(response.status).toBe(400);
      expect(await response.json()).toEqual({ error });
      expect(sessionModule.getSession).not.toHaveBeenCalled();
      expect(
        grantorAnnouncementFetcherModule.deleteApplicationPackageInstructions,
      ).not.toHaveBeenCalled();
    },
  );

  it("returns 401 when the user is not authenticated", async () => {
    (sessionModule.getSession as jest.Mock).mockResolvedValueOnce(null);

    const response = await DELETE({} as NextRequest, buildContext());

    expect(response.status).toBe(401);
    expect(await response.json()).toEqual({
      error:
        "Not logged in, cannot delete applicationPackage instructions file",
    });
    expect(
      grantorAnnouncementFetcherModule.deleteApplicationPackageInstructions,
    ).not.toHaveBeenCalled();
  });

  it("returns the backend error status when deletion fails", async () => {
    (
      grantorAnnouncementFetcherModule.deleteApplicationPackageInstructions as jest.Mock
    ).mockRejectedValueOnce(new NotFoundError("Instruction file not found"));

    const response = await DELETE({} as NextRequest, buildContext());

    expect(response.status).toBe(404);
    expect(await response.json()).toEqual(
      expect.objectContaining({ error: "Instruction file not found" }),
    );
  });

  it("returns 500 for unexpected errors", async () => {
    (
      grantorAnnouncementFetcherModule.deleteApplicationPackageInstructions as jest.Mock
    ).mockRejectedValueOnce(new Error("Network error"));

    const response = await DELETE({} as NextRequest, buildContext());

    expect(response.status).toBe(500);
    expect(await response.json()).toEqual(
      expect.objectContaining({ error: "Network error" }),
    );
  });
});
