import { getUserAgencies } from "src/services/fetch/fetchers/agenciesFetcher";
import { fetchUserWithMethod } from "src/services/fetch/fetchers/fetchers";
import { fakeAgencyResponseData } from "src/utils/testing/fixtures";

jest.mock("src/services/fetch/fetchers/fetchers", () => ({
  fetchUserWithMethod: jest.fn(), // Initialize as a mock -- this works
}));

// ------------------------------------------------------
// Fetch user's agencies
// ------------------------------------------------------
describe("getUserAgencies", () => {
  let mockJsonFn: jest.Mock;
  beforeEach(() => {
    jest.clearAllMocks();
    mockJsonFn = jest.fn();
    const mockResponse = { json: mockJsonFn };
    (fetchUserWithMethod as jest.Mock).mockReturnValue(
      jest.fn().mockResolvedValue(mockResponse),
    );
  });
  it("calls request function with correct parameters", async () => {
    const expectedResponse = {
      status_code: 200,
      data: fakeAgencyResponseData,
    };
    mockJsonFn.mockResolvedValue(expectedResponse);

    const result = await getUserAgencies("123-ABC");

    expect(fetchUserWithMethod).toHaveBeenCalledWith("POST");
    expect(result).toEqual(fakeAgencyResponseData);
  });
});
