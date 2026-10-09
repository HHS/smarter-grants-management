import { NextRequest } from "next/server";

import { searchAssistanceListings } from "./handler";

const mockGetSession = jest.fn();
const mockGetAssistanceListingSearchResults = jest.fn();

jest.mock("src/services/auth/session", () => ({
  getSession: (): unknown => mockGetSession(),
}));

jest.mock("src/services/fetch/fetchers/assistanceListingsFetcher", () => ({
  getAssistanceListingSearchResults: (query: string): unknown =>
    mockGetAssistanceListingSearchResults(query),
}));

interface MockResponse {
  json: () => Promise<unknown>;
  status: number;
}

global.Response = class Response {
  constructor(
    public body: unknown,
    public init?: ResponseInit,
  ) {}
  static json(data: unknown, init?: ResponseInit): MockResponse {
    return {
      json: jest.fn().mockResolvedValue(data),
      status: init?.status || 200,
    };
  }
} as unknown as typeof globalThis.Response;

const fakeAssistanceListings = [
  {
    assistance_listing_number: "10.001",
    program_title: "Agricultural Research",
  },
];

const createRequest = (body: Record<string, unknown>) =>
  ({
    json: jest.fn().mockResolvedValue(body),
  }) as unknown as NextRequest;

describe("searchAssistanceListings", () => {
  beforeEach(() => {
    mockGetSession.mockResolvedValue({ token: "a token", user_id: "1" });
    mockGetAssistanceListingSearchResults.mockResolvedValue(
      fakeAssistanceListings,
    );
  });

  afterEach(() => jest.clearAllMocks());

  it("returns the search results for the search term", async () => {
    const response = await searchAssistanceListings(
      createRequest({ searchTerm: "rural" }),
    );

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ data: fakeAssistanceListings });
    expect(mockGetAssistanceListingSearchResults).toHaveBeenCalledWith("rural");
  });

  it("returns 401 without a session", async () => {
    mockGetSession.mockResolvedValue(null);

    const response = await searchAssistanceListings(
      createRequest({ searchTerm: "rural" }),
    );

    expect(response.status).toBe(401);
    expect(await response.json()).toEqual({
      message: "Not logged in, cannot search assistance listings",
    });
    expect(mockGetAssistanceListingSearchResults).not.toHaveBeenCalled();
  });

  it("returns 400 without a search term", async () => {
    const response = await searchAssistanceListings(createRequest({}));

    expect(response.status).toBe(400);
    expect(await response.json()).toEqual({
      message: "Search term is required",
    });
    expect(mockGetAssistanceListingSearchResults).not.toHaveBeenCalled();
  });

  it("returns the backend error status when the search fails", async () => {
    mockGetAssistanceListingSearchResults.mockRejectedValue(
      new Error("Invalid query", { cause: { status: 422 } }),
    );

    const response = await searchAssistanceListings(
      createRequest({ searchTerm: "rural" }),
    );

    expect(response.status).toBe(422);
    expect(await response.json()).toEqual({
      message: "Error attempting to search assistance listings: Invalid query",
    });
  });

  it("returns 500 when the failure has no status", async () => {
    mockGetAssistanceListingSearchResults.mockRejectedValue(
      new Error("Network down"),
    );

    const response = await searchAssistanceListings(
      createRequest({ searchTerm: "rural" }),
    );

    expect(response.status).toBe(500);
    expect(await response.json()).toEqual({
      message: "Error attempting to search assistance listings: Network down",
    });
  });
});
