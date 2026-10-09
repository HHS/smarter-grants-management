import { getAssistanceListingSearchResults } from "src/services/fetch/fetchers/assistanceListingsFetcher";

const mockFetchAssistanceListings = jest.fn();
const mockJson = jest.fn();
const fakeAssistanceListings = [
  {
    assistance_listing_number: "10.001",
    program_title: "Agricultural Research",
  },
];

jest.mock("src/services/fetch/fetchers/fetchers", () => ({
  fetchAssistanceListings: (params: unknown): unknown =>
    mockFetchAssistanceListings(params),
}));

describe("getAssistanceListingSearchResults", () => {
  beforeEach(() => {
    mockJson.mockResolvedValue({ data: fakeAssistanceListings });
    mockFetchAssistanceListings.mockResolvedValue({ json: mockJson });
  });

  afterEach(() => jest.clearAllMocks());

  it("searches the first page of up to 15 results for the query", async () => {
    await getAssistanceListingSearchResults("rural");

    expect(mockFetchAssistanceListings).toHaveBeenCalledWith({
      subPath: "search",
      body: { query: "rural", pagination: { page_offset: 1, page_size: 15 } },
    });
  });

  it("returns the assistance listings from the response", async () => {
    const result = await getAssistanceListingSearchResults("rural");

    expect(result).toEqual(fakeAssistanceListings);
  });

  it("returns an empty list when the response has no data", async () => {
    mockJson.mockResolvedValue({});

    const result = await getAssistanceListingSearchResults("rural");

    expect(result).toEqual([]);
  });
});
