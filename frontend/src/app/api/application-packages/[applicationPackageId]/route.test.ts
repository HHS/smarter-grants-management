/**
 * @jest-environment node
 */

import { getApplicationPackage } from "src/app/api/application-packages/[applicationPackageId]/handler";
import { ApplicationPackage } from "src/types/applicationPackageResponseTypes";
import { fakeApplicationPackage } from "src/utils/testing/fixtures";

import { NextRequest } from "next/server";

const mockGetApplicationPackageDetails = jest.fn();

jest.mock("src/services/fetch/fetchers/applicationPackagesFetcher", () => ({
  getApplicationPackageDetails: (id: string) =>
    mockGetApplicationPackageDetails(id) as unknown,
}));

describe("application-packages/[applicationPackageId] GET requests", () => {
  afterEach(() => jest.resetAllMocks());
  it("calls opportunityDetails with expected arguments", async () => {
    await getApplicationPackage(new NextRequest("http://hi.gov"), {
      params: Promise.resolve({
        applicationPackageId: "1",
      }),
    });
    expect(mockGetApplicationPackageDetails).toHaveBeenCalledWith("1");
  });

  it("returns a new response with applicationPackage data", async () => {
    mockGetApplicationPackageDetails.mockResolvedValue(fakeApplicationPackage);
    const response = await getApplicationPackage(
      new NextRequest("http://hi.gov"),
      {
        params: Promise.resolve({
          applicationPackageId: "1",
        }),
      },
    );
    expect(response.status).toEqual(200);
    const body = (await response.json()) as ApplicationPackage;
    expect(body).toEqual(fakeApplicationPackage);
  });

  it("returns a new response with with error if error on data fetch", async () => {
    mockGetApplicationPackageDetails.mockRejectedValue(new Error());
    const response = await getApplicationPackage(
      new NextRequest("http://hi.gov"),
      {
        params: Promise.resolve({
          applicationPackageId: "1",
        }),
      },
    );
    expect(response.status).toEqual(500);
  });
});
