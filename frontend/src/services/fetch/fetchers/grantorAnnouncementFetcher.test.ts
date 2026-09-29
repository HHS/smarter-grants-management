import { ApiRequestError } from "src/errors";
import {
  createApplicationPackageForGrantor,
  createOpportunity,
  deleteApplicationPackageInstructions,
  saveApplicationPackageInstructions,
  searchOpportunitiesByAgency,
  updateApplicationPackageForGrantor,
} from "src/services/fetch/fetchers/grantorAnnouncementFetcher";
import { ApplicationPackageSaveRequest } from "src/types/applicationPackageResponseTypes";
import { PaginationRequestBody } from "src/types/search/searchRequestTypes";
import { fakeAgencyResponseData } from "src/utils/testing/fixtures";

// Mock the grantor agencies/announcements requesters and the sub-method they call, fetch
const mockFetcher = jest.fn();
const mockFetchGrantorAgenciesWithMethod = jest.fn(
  (_args: unknown) => mockFetcher,
);
const mockFetchGrantorOpportunityWithMethod = jest.fn(
  (_args: unknown) => mockFetcher,
);
jest.mock("src/services/fetch/fetchers/fetchers", () => ({
  fetchGrantorAgenciesWithMethod: (arg: unknown): unknown =>
    mockFetchGrantorAgenciesWithMethod(arg),
  fetchAnnouncementWithMethod: (arg: unknown): unknown =>
    mockFetchGrantorOpportunityWithMethod(arg),
}));

// ---------------------------------------------
// Tests for searchOpportunitiesByAgency
// ---------------------------------------------
const pageRequest: PaginationRequestBody = {
  page_offset: 1,
  page_size: 25,
  sort_order: [
    {
      order_by: "opportunity_title",
      sort_direction: "ascending",
    },
  ],
};
const pageBody: { pagination: PaginationRequestBody } = {
  pagination: pageRequest,
};

describe("searchOpportunitiesByAgency", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });
  it("calls request function with correct parameters", async () => {
    const agencyId = "123-ABC-456-DEF";
    const fakeResponse = {
      status: 200,
      json: () =>
        Promise.resolve({
          data: fakeAgencyResponseData,
          pagination_info: { total_pages: 1, total_records: 4 },
        }),
    };
    mockFetcher.mockResolvedValue(fakeResponse);

    const result = await searchOpportunitiesByAgency(agencyId, pageRequest);

    expect(result).toEqual({
      data: fakeAgencyResponseData,
      pagination_info: { total_pages: 1, total_records: 4 },
    });
    expect(mockFetchGrantorAgenciesWithMethod).toHaveBeenCalledTimes(1);
    expect(mockFetchGrantorAgenciesWithMethod).toHaveBeenCalledWith("POST");
    expect(mockFetcher).toHaveBeenCalledWith({
      subPath: "123-ABC-456-DEF/announcements",
      body: pageBody,
    });
  });

  it("returns first page results with page_size of 2", async () => {
    pageRequest.page_size = 2;
    const firstTwoRows = fakeAgencyResponseData.slice(0, 2);
    const agencyId = "123-ABC-456-DEF";
    const fakeResponse = {
      status: 200,
      json: () =>
        Promise.resolve({
          data: firstTwoRows,
          pagination_info: { total_pages: 2, total_records: 4 },
        }),
    };
    mockFetcher.mockResolvedValue(fakeResponse);

    const result = await searchOpportunitiesByAgency(agencyId, pageRequest);

    expect(result).toEqual({
      data: fakeAgencyResponseData.slice(0, 2),
      pagination_info: { total_pages: 2, total_records: 4 },
    });
    expect(result.data).toHaveLength(2);
    expect(result.pagination_info.total_pages).toBe(2);
    expect(result.pagination_info.total_records).toBe(4);
    expect(result.data[0].agency_code).toEqual("DOCNIST");
    expect(result.data[1].agency_code).toEqual("MOCKNIST");
  });

  it("returns second page results with page_size of 2", async () => {
    pageRequest.page_size = 2;
    pageRequest.page_offset = 2;
    const lastTwoRows = fakeAgencyResponseData.slice(2);
    const agencyId = "123-ABC-456-DEF";
    const fakeResponse = {
      status: 200,
      json: () =>
        Promise.resolve({
          data: lastTwoRows,
          pagination_info: { total_pages: 2, total_records: 4 },
        }),
    };
    mockFetcher.mockResolvedValue(fakeResponse);

    const result = await searchOpportunitiesByAgency(agencyId, pageRequest);

    expect(result).toEqual({
      data: fakeAgencyResponseData.slice(2),
      pagination_info: { total_pages: 2, total_records: 4 },
    });
    expect(result.data).toHaveLength(2);
    expect(result.pagination_info.total_pages).toBe(2);
    expect(result.pagination_info.total_records).toBe(4);
    expect(result.data[0].agency_code).toEqual("MOCKTRASH");
    expect(result.data[1].agency_code).toEqual("FAKEORG");
  });

  it("should return validation error response with 422 status", async () => {
    const agencyId = "123-ABC-456-DEF";
    const errMsg = { errors: { field: "invalid" } };
    const expectedResponse = {
      status_code: 422,
      message: "Validation failed",
      json: () => Promise.resolve({ data: errMsg }),
    };
    mockFetcher.mockResolvedValue(expectedResponse);

    const result = await searchOpportunitiesByAgency(agencyId, pageRequest);

    expect(result).toEqual({
      data: errMsg,
      pagination_info: undefined,
    });
    expect(mockFetchGrantorAgenciesWithMethod).toHaveBeenCalledTimes(1);
    expect(mockFetchGrantorAgenciesWithMethod).toHaveBeenCalledWith("POST");
  });

  it("propagates network errors", async () => {
    mockFetcher.mockRejectedValue(new Error("Network failure"));
    await expect(
      searchOpportunitiesByAgency("any-id", pageRequest),
    ).rejects.toThrow("Network failure");
  });
});

// ---------------------------------------------
// Tests for createOpportunity
// ---------------------------------------------
const createOppSchema = {
  agency_id: "123-ABC-456-DEF",
  opportunity_number: "TEST-OPP-001",
  opportunity_title: "Test Opportunity 001",
  category: "other",
  category_explanation: "Some explanation",
};

describe("createOpportunity", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });
  it("calls request function with correct parameters", async () => {
    const expectedResponse = {
      status_code: 200,
      json: () => Promise.resolve({ data: createOppSchema }),
    };
    mockFetcher.mockResolvedValue(expectedResponse);

    const result = await createOpportunity(createOppSchema);

    expect(result).toEqual(createOppSchema);
    expect(mockFetchGrantorOpportunityWithMethod).toHaveBeenCalledTimes(1);
    expect(mockFetchGrantorOpportunityWithMethod).toHaveBeenCalledWith("POST");
    expect(mockFetcher).toHaveBeenCalledWith({
      body: createOppSchema,
    });
  });

  it("should return validation error response with 422 status", async () => {
    const errMsg = { errors: { field: "invalid" } };
    const expectedResponse = {
      status_code: 422,
      message: "Validation failed",
      json: () => Promise.resolve({ data: errMsg }),
    };
    mockFetcher.mockResolvedValue(expectedResponse);

    const result = await createOpportunity(createOppSchema);

    expect(result).toEqual(errMsg);
    expect(mockFetchGrantorOpportunityWithMethod).toHaveBeenCalledTimes(1);
    expect(mockFetchGrantorOpportunityWithMethod).toHaveBeenCalledWith("POST");
  });

  it("propagates network errors", async () => {
    mockFetcher.mockRejectedValue(new Error("Network failure"));
    await expect(createOpportunity(createOppSchema)).rejects.toThrow(
      "Network failure",
    );
  });
});

// ---------------------------------------------
// Tests for opportunity applicationPackages
// ---------------------------------------------
const applicationPackageData: ApplicationPackageSaveRequest = {
  applicationPackage_title: "",
  opening_date: null,
  closing_date: null,
  contact_info: null,
  open_to_applicants: ["individual", "organization"],
};

describe("createApplicationPackageForGrantor", () => {
  beforeEach(() => {
    mockFetcher.mockResolvedValue({
      json: () =>
        Promise.resolve({
          data: { applicationPackage_id: "new-applicationPackage-id" },
        }),
    });
  });
  afterEach(() => jest.clearAllMocks());

  it("calls fetchAnnouncementWithMethod with POST, the correct subPath, and returns the parsed JSON response", async () => {
    const result = await createApplicationPackageForGrantor(
      "opp-123",
      applicationPackageData,
    );

    expect(mockFetchGrantorOpportunityWithMethod).toHaveBeenCalledTimes(1);
    expect(mockFetchGrantorOpportunityWithMethod).toHaveBeenCalledWith("POST");
    expect(mockFetcher).toHaveBeenCalledWith({
      subPath: "opp-123/application-packages",
      body: applicationPackageData,
      allowedErrorStatuses: [422],
    });
    expect(result).toEqual({
      data: { applicationPackage_id: "new-applicationPackage-id" },
    });
  });

  it("includes public_applicationPackage_id in the request body", async () => {
    const applicationPackageWithPublicId: ApplicationPackageSaveRequest = {
      ...applicationPackageData,
      public_applicationPackage_id: "PUBLIC-COMP-789",
    };

    await createApplicationPackageForGrantor(
      "opp-123",
      applicationPackageWithPublicId,
    );

    expect(mockFetcher).toHaveBeenCalledWith({
      subPath: "opp-123/application-packages",
      body: applicationPackageWithPublicId,
      allowedErrorStatuses: [422],
    });
  });
});

describe("updateApplicationPackageForGrantor", () => {
  beforeEach(() => {
    mockFetcher.mockResolvedValue({ json: () => Promise.resolve({}) });
  });
  afterEach(() => jest.clearAllMocks());

  it("calls fetchAnnouncementWithMethod with PUT and the correct subPath", async () => {
    await updateApplicationPackageForGrantor(
      "opp-123",
      "compete-321",
      applicationPackageData,
    );

    expect(mockFetchGrantorOpportunityWithMethod).toHaveBeenCalledTimes(1);
    expect(mockFetchGrantorOpportunityWithMethod).toHaveBeenCalledWith("PUT");
    expect(mockFetcher).toHaveBeenCalledWith({
      subPath: "opp-123/application-packages/compete-321",
      body: applicationPackageData,
      allowedErrorStatuses: [422],
    });
  });

  it("throws a 422 error with validation error messages", async () => {
    const mockErrors: Array<{
      field: string;
      message: string;
      type: string;
      value: string | null;
    }> = [
      {
        field: "open_to_applicants",
        message: "Shorter than minimum length 1.",
        type: "min_length",
        value: null,
      },
      {
        field: "applicationPackage_title",
        message: "Must not be empty.",
        type: "required",
        value: "",
      },
    ];

    const apiError = new ApiRequestError(
      "Validation error",
      "ValidationError",
      422,
      { errors: mockErrors } as unknown as Record<string, unknown>,
    );
    mockFetcher.mockRejectedValue(apiError);

    // verify that it throws the error
    await expect(
      updateApplicationPackageForGrantor(
        "opp-123",
        "compete-321",
        applicationPackageData,
      ),
    ).rejects.toThrow(ApiRequestError);
  });
});

describe("saveApplicationPackageInstructions", () => {
  afterEach(() => jest.clearAllMocks());

  it("calls fetchAnnouncementWithMethod with POST, the correct subPath and body, and returns the parsed JSON response", async () => {
    const responseBody = {
      data: {
        applicationPackage_instruction_id: "instruction-123",
        file_name: "instructions.pdf",
        created_at: "2026-08-20T00:00:00Z",
      },
    };
    mockFetcher.mockResolvedValue({
      json: () => Promise.resolve(responseBody),
    });

    const result = await saveApplicationPackageInstructions(
      "opp-123",
      "compete-321",
      "pending-file-456",
    );

    expect(mockFetchGrantorOpportunityWithMethod).toHaveBeenCalledTimes(1);
    expect(mockFetchGrantorOpportunityWithMethod).toHaveBeenCalledWith("POST");
    expect(mockFetcher).toHaveBeenCalledWith({
      subPath: "opp-123/application-packages/compete-321/instructions",
      body: { pending_file_id: "pending-file-456" },
    });
    expect(result).toEqual(responseBody);
  });

  it("propagates request errors", async () => {
    mockFetcher.mockRejectedValue(new Error("Network failure"));

    await expect(
      saveApplicationPackageInstructions(
        "opp-123",
        "compete-321",
        "pending-file-456",
      ),
    ).rejects.toThrow("Network failure");
  });
});

describe("deleteApplicationPackageInstructions", () => {
  afterEach(() => jest.clearAllMocks());

  it("calls fetchAnnouncementWithMethod with DELETE, the correct subPath, and returns the parsed JSON response", async () => {
    const responseBody = {
      message: "Instruction deleted successfully",
      status_code: 200,
    };
    mockFetcher.mockResolvedValue({
      json: () => Promise.resolve(responseBody),
    });

    const result = await deleteApplicationPackageInstructions(
      "opp-123",
      "compete-321",
      "instruction-123",
    );

    expect(mockFetchGrantorOpportunityWithMethod).toHaveBeenCalledTimes(1);
    expect(mockFetchGrantorOpportunityWithMethod).toHaveBeenCalledWith(
      "DELETE",
    );
    expect(mockFetcher).toHaveBeenCalledWith({
      subPath:
        "opp-123/application-packages/compete-321/instructions/instruction-123",
    });
    expect(result).toEqual(responseBody);
  });

  it("propagates request errors", async () => {
    mockFetcher.mockRejectedValue(new Error("Network failure"));

    await expect(
      deleteApplicationPackageInstructions(
        "opp-123",
        "compete-321",
        "instruction-123",
      ),
    ).rejects.toThrow("Network failure");
  });
});
