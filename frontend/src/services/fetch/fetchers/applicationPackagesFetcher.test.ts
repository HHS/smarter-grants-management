import { getApplicationPackageDetails } from "src/services/fetch/fetchers/applicationPackagesFetcher";

const mockfetchApplicationPackage = jest.fn();
const mockJson = jest.fn();
const fakeResponseBody = { some: "response body" };

jest.mock("src/services/fetch/fetchers/fetchers", () => ({
  fetchApplicationPackage: (params: unknown): unknown => {
    return mockfetchApplicationPackage(params);
  },
}));

describe("getApplicationPackageDetails", () => {
  beforeEach(() => {
    mockJson.mockResolvedValue({ data: fakeResponseBody });
    mockfetchApplicationPackage.mockResolvedValue({
      json: mockJson,
    });
  });
  afterEach(() => jest.clearAllMocks());
  it("calls fetchApplicationPackage with the correct arguments", async () => {
    await getApplicationPackageDetails("an id");
    expect(mockfetchApplicationPackage).toHaveBeenCalledWith({
      subPath: "an id",
    });
  });

  it("returns json from response", async () => {
    const result = await getApplicationPackageDetails("an id");
    expect(mockJson).toHaveBeenCalledTimes(1);
    expect(result).toEqual(fakeResponseBody);
  });
});
