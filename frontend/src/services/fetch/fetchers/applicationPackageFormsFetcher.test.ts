import { updateApplicationPackageForms } from "src/services/fetch/fetchers/applicationPackageFormsFetcher";

const fakeResponseBody = { some: "response body" };
const mockJson = jest.fn(() => fakeResponseBody);

const mockFetchApplicationPackageForm = jest.fn().mockResolvedValue({
  json: mockJson,
});

jest.mock("src/services/fetch/fetchers/fetchers", () => ({
  fetchApplicationPackageForms: (params: unknown): unknown => {
    return mockFetchApplicationPackageForm(params);
  },
}));

describe("getFormDetails", () => {
  afterEach(() => jest.clearAllMocks());
  it("calls fetchForm with the correct arguments", async () => {
    const results = await updateApplicationPackageForms({
      applicationPackageId: "an id",
      body: { forms: [] },
    });
    expect(mockFetchApplicationPackageForm).toHaveBeenCalledWith({
      subPath: "an id/forms",
      body: { forms: [] },
    });
    expect(results).toEqual({ some: "response body" });
  });
});
