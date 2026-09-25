import { identity } from "lodash";
import { ApiRequestError } from "src/errors";
import { updateApplicationPackageForms } from "src/services/fetch/fetchers/applicationPackageFormsFetcher";
import {
  createApplicationPackageForGrantor,
  saveApplicationPackageInstructions,
  updateApplicationPackageForGrantor,
} from "src/services/fetch/fetchers/grantorAnnouncementFetcher";
import {
  ApplicationPackageFormsSubmitApi,
  ApplicationPackageSaveApiResponse,
} from "src/types/applicationPackageResponseTypes";

import {
  applicationPackageFormAction,
  updateApplicationPackage,
} from "./actions";

jest.mock("next-intl/server", () => ({
  getTranslations: () => identity,
}));

jest.mock("src/services/fetch/fetchers/grantorAnnouncementFetcher", () => ({
  createApplicationPackageForGrantor: jest.fn(),
  saveApplicationPackageInstructions: jest.fn(),
  updateApplicationPackageForGrantor: jest.fn(),
}));

jest.mock("src/services/fetch/fetchers/applicationPackageFormsFetcher", () => ({
  updateApplicationPackageForms: jest.fn(),
}));

const mockRedirect = jest.fn();
jest.mock("next/navigation", () => ({
  redirect: (url: string): void => {
    mockRedirect(url);
  },
}));

const mockCreateApplicationPackageForGrantor = jest.mocked(
  createApplicationPackageForGrantor,
);
const mockUpdateApplicationPackageForGrantor = jest.mocked(
  updateApplicationPackageForGrantor,
);
const mockSaveApplicationPackageInstructions = jest.mocked(
  saveApplicationPackageInstructions,
);
const mockUpdateApplicationPackageForms = jest.mocked(
  updateApplicationPackageForms,
);

const mockRequiredForms: ApplicationPackageFormsSubmitApi = [
  {
    form_id: "1623b310-85be-496a-b84b-34bdee22a68a",
    is_required: true,
  },
];

const successfulCreateResponse = {
  message: "success",
  status_code: 201,
  data: {
    applicationPackage_id: "new-applicationPackage-id",
  },
} as Awaited<ReturnType<typeof createApplicationPackageForGrantor>>;

const successfulUpdateResponse = {
  message: "success",
  status_code: 200,
  data: {
    applicationPackage_id: "existing-applicationPackage-id",
  },
} as Awaited<ReturnType<typeof updateApplicationPackageForGrantor>>;

function buildValidFormData(overrides?: Record<string, string>) {
  const formData = new FormData();
  formData.set("announcementId", "opp-123");
  formData.set("applicationPackageId", "compete-456");
  formData.set("applicationPackage_title", "Test ApplicationPackage");
  formData.set("opening_date", "2026-06-01");
  formData.set("closing_date", "2026-07-01");
  formData.set("public_applicationPackage_id", "PUBLIC-COMP-789");
  formData.set("open_to_applicants", "both");
  formData.set("contact_name", "John Doe");
  formData.set("contact_title", "Manager");
  formData.set("contact_email", "john@example.com");
  formData.set("contact_phone", "555-0100");

  if (overrides) {
    Object.entries(overrides).forEach(([key, value]) => {
      formData.set(key, value);
    });
  }

  return formData;
}

describe("updateApplicationPackage", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("returns an error when announcementId is missing", async () => {
    const formData = new FormData();
    formData.set("applicationPackageId", "compete-456");

    const result = await updateApplicationPackage(formData, mockRequiredForms);

    expect(result).toEqual({
      errorMessage: "genericError",
    });
  });

  it("calls createApplicationPackageForGrantor when no applicationPackageId", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");

    mockCreateApplicationPackageForGrantor.mockResolvedValue(
      successfulCreateResponse,
    );

    const result = await updateApplicationPackage(formData, mockRequiredForms);

    expect(mockCreateApplicationPackageForGrantor).toHaveBeenCalledWith(
      "opp-123",
      expect.objectContaining({
        applicationPackage_title: "Test ApplicationPackage",
        opening_date: "2026-06-01",
        closing_date: "2026-07-01",
        public_applicationPackage_id: "PUBLIC-COMP-789",
      }),
    );
    expect(result).toEqual({
      successMessage: "success",
    });
  });

  it("updates applicationPackage forms with the new applicationPackage ID after creating", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");

    mockCreateApplicationPackageForGrantor.mockResolvedValue(
      successfulCreateResponse,
    );

    await updateApplicationPackage(formData, mockRequiredForms);

    expect(mockUpdateApplicationPackageForms).toHaveBeenCalledWith({
      applicationPackageId: "new-applicationPackage-id",
      body: { forms: mockRequiredForms },
    });
  });

  it("calls updateApplicationPackageForGrantor when applicationPackageId exists", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackageForGrantor.mockResolvedValue(
      successfulUpdateResponse,
    );

    const result = await updateApplicationPackage(formData, mockRequiredForms);

    expect(mockUpdateApplicationPackageForGrantor).toHaveBeenCalledWith(
      "opp-123",
      "compete-456",
      expect.objectContaining({
        applicationPackage_title: "Test ApplicationPackage",
        opening_date: "2026-06-01",
        closing_date: "2026-07-01",
        public_applicationPackage_id: "PUBLIC-COMP-789",
      }),
    );
    expect(result).toEqual({
      successMessage: "success",
    });
  });

  it("updates applicationPackage forms with the existing applicationPackage ID", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackageForGrantor.mockResolvedValue(
      successfulUpdateResponse,
    );

    await updateApplicationPackage(formData, mockRequiredForms);

    expect(mockUpdateApplicationPackageForms).toHaveBeenCalledWith({
      applicationPackageId: "compete-456",
      body: { forms: mockRequiredForms },
    });
  });

  it("saves application instructions when creating a applicationPackage with a pending file ID", async () => {
    const formData = buildValidFormData({
      "pending-file-id": "pending-file-789",
    });
    formData.delete("applicationPackageId");

    mockCreateApplicationPackageForGrantor.mockResolvedValue(
      successfulCreateResponse,
    );

    const result = await updateApplicationPackage(formData, mockRequiredForms);

    expect(mockSaveApplicationPackageInstructions).toHaveBeenCalledWith(
      "opp-123",
      "new-applicationPackage-id",
      "pending-file-789",
    );
    expect(result).toEqual({
      successMessage: "success",
    });
  });

  it("saves application instructions when a pending file ID exists", async () => {
    const formData = buildValidFormData({
      "pending-file-id": "pending-file-789",
    });

    mockUpdateApplicationPackageForGrantor.mockResolvedValue(
      successfulUpdateResponse,
    );

    const result = await updateApplicationPackage(formData, mockRequiredForms);

    expect(mockSaveApplicationPackageInstructions).toHaveBeenCalledWith(
      "opp-123",
      "compete-456",
      "pending-file-789",
    );
    expect(result).toEqual({
      successMessage: "success",
    });
  });

  it("returns a generic error when saving application instructions fails", async () => {
    const formData = buildValidFormData({
      "pending-file-id": "pending-file-789",
    });

    mockUpdateApplicationPackageForGrantor.mockResolvedValue(
      successfulUpdateResponse,
    );
    mockSaveApplicationPackageInstructions.mockRejectedValue(
      new Error("unexpected"),
    );

    const result = await updateApplicationPackage(formData, mockRequiredForms);

    expect(mockSaveApplicationPackageInstructions).toHaveBeenCalledWith(
      "opp-123",
      "compete-456",
      "pending-file-789",
    );
    expect(result).toEqual({
      errorMessage: "genericError",
    });
  });

  it("maps 401 to an unauthenticated error", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackageForGrantor.mockRejectedValue(
      new ApiRequestError("unauthenticated", "APIRequestError", 401),
    );

    const result = await updateApplicationPackage(formData, mockRequiredForms);

    expect(result).toEqual({
      errorMessage: "unauthenticated",
    });
  });

  it("maps 403 to a forbidden error", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackageForGrantor.mockRejectedValue(
      new ApiRequestError("forbidden", "APIRequestError", 403),
    );

    const result = await updateApplicationPackage(formData, mockRequiredForms);

    expect(result).toEqual({
      errorMessage: "forbidden",
    });
  });

  it("maps 404 to a not found error", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackageForGrantor.mockRejectedValue(
      new ApiRequestError("notFound", "APIRequestError", 404),
    );

    const result = await updateApplicationPackage(formData, mockRequiredForms);

    expect(result).toEqual({
      errorMessage: "notFound",
    });
  });

  it("maps 422 to validationErrors with formatted error message", async () => {
    const formData = buildValidFormData();

    const mockResponse = {
      status_code: 422,
      errors: [
        {
          field: "open_to_applicants",
          message: "Shorter than minimum length 1.",
        },
      ],
    } as ApplicationPackageSaveApiResponse;

    mockUpdateApplicationPackageForGrantor.mockResolvedValue(mockResponse);

    const result = await updateApplicationPackage(formData, mockRequiredForms);

    expect(result).toEqual({
      validationErrors: {
        open_to_applicants: ["Shorter than minimum length 1."],
      },
    });
  });

  it("maps unknown errors to a generic error", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackageForGrantor.mockRejectedValue(
      new Error("unexpected"),
    );

    const result = await updateApplicationPackage(formData, mockRequiredForms);

    expect(result).toEqual({
      errorMessage: "genericError",
    });
  });
});

describe("applicationPackageFormAction", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("delegates to updateApplicationPackage and redirects to ../overview for saveAndExit", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackageForGrantor.mockResolvedValue(
      successfulUpdateResponse,
    );

    await applicationPackageFormAction(
      "saveAndExit",
      mockRequiredForms,
      formData,
    );

    expect(mockUpdateApplicationPackageForGrantor).toHaveBeenCalledTimes(1);
    expect(mockRedirect).toHaveBeenCalledWith("../overview");
  });

  it("delegates to updateApplicationPackage and redirects to ../edit for saveAndGoBack", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackageForGrantor.mockResolvedValue(
      successfulUpdateResponse,
    );

    await applicationPackageFormAction(
      "saveAndGoBack",
      mockRequiredForms,
      formData,
    );

    expect(mockUpdateApplicationPackageForGrantor).toHaveBeenCalledTimes(1);
    expect(mockRedirect).toHaveBeenCalledWith("../edit");
  });

  it("delegates to updateApplicationPackage and redirects to ../overview for saveAndContinue", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackageForGrantor.mockResolvedValue(
      successfulUpdateResponse,
    );

    await applicationPackageFormAction(
      "saveAndContinue",
      mockRequiredForms,
      formData,
    );

    expect(mockUpdateApplicationPackageForGrantor).toHaveBeenCalledTimes(1);
    expect(mockRedirect).toHaveBeenCalledWith("../overview");
  });

  it("returns errors without redirecting when updateApplicationPackage returns errorMessage", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackageForGrantor.mockRejectedValue(
      new ApiRequestError("forbidden", "APIRequestError", 403),
    );

    const result = await applicationPackageFormAction(
      "saveAndContinue",
      mockRequiredForms,
      formData,
    );

    expect(mockUpdateApplicationPackageForGrantor).toHaveBeenCalledTimes(1);
    expect(mockRedirect).not.toHaveBeenCalled();
    expect(result).toEqual({
      errorMessage: "forbidden",
    });
  });

  it("returns saveResult for unknown submitType without redirecting", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackageForGrantor.mockResolvedValue(
      successfulUpdateResponse,
    );

    const result = await applicationPackageFormAction(
      "unknownType",
      mockRequiredForms,
      formData,
    );

    expect(mockUpdateApplicationPackageForGrantor).toHaveBeenCalledTimes(1);
    expect(mockRedirect).not.toHaveBeenCalled();
    expect(result).toEqual({
      successMessage: "success",
    });
  });
});

describe("buildRequestBody (tested indirectly via updateApplicationPackage)", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("builds correct request body for 'both' applicant type", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");

    mockCreateApplicationPackageForGrantor.mockResolvedValue(
      successfulCreateResponse,
    );

    await updateApplicationPackage(formData, mockRequiredForms);

    const requestBody = mockCreateApplicationPackageForGrantor.mock.calls[0][1];
    expect(requestBody.open_to_applicants).toEqual([
      "organization",
      "individual",
    ]);
  });

  it("includes the public applicationPackage ID in the request body", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");

    mockCreateApplicationPackageForGrantor.mockResolvedValue(
      successfulCreateResponse,
    );

    await updateApplicationPackage(formData, mockRequiredForms);

    const requestBody = mockCreateApplicationPackageForGrantor.mock.calls[0][1];
    expect(requestBody.public_applicationPackage_id).toBe("PUBLIC-COMP-789");
  });

  it("builds correct request body for 'organizations_only' applicant type", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");
    formData.set("open_to_applicants", "organizations_only");

    mockCreateApplicationPackageForGrantor.mockResolvedValue(
      successfulCreateResponse,
    );

    await updateApplicationPackage(formData, mockRequiredForms);

    const requestBody = mockCreateApplicationPackageForGrantor.mock.calls[0][1];
    expect(requestBody.open_to_applicants).toEqual(["organization"]);
  });

  it("builds correct request body for 'individuals_only' applicant type", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");
    formData.set("open_to_applicants", "individuals_only");

    mockCreateApplicationPackageForGrantor.mockResolvedValue(
      successfulCreateResponse,
    );

    await updateApplicationPackage(formData, mockRequiredForms);

    const requestBody = mockCreateApplicationPackageForGrantor.mock.calls[0][1];
    expect(requestBody.open_to_applicants).toEqual(["individual"]);
  });

  it("concatenates contact info correctly", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");

    mockCreateApplicationPackageForGrantor.mockResolvedValue(
      successfulCreateResponse,
    );

    await updateApplicationPackage(formData, mockRequiredForms);

    const requestBody = mockCreateApplicationPackageForGrantor.mock.calls[0][1];
    expect(requestBody.contact_info).toBe(
      "John Doe | Manager | john@example.com | 555-0100",
    );
  });

  it("converts grace_period to a number when provided", async () => {
    const formData = buildValidFormData({ grace_period: "30" });
    formData.delete("applicationPackageId");

    mockCreateApplicationPackageForGrantor.mockResolvedValue(
      successfulCreateResponse,
    );

    await updateApplicationPackage(formData, mockRequiredForms);

    const requestBody = mockCreateApplicationPackageForGrantor.mock.calls[0][1];
    expect(requestBody.grace_period).toBe(30);
  });

  it("handles empty field values by returning null", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");
    formData.set("applicationPackage_title", "");
    formData.set("opening_date", "");
    formData.set("closing_date", "");
    formData.set("public_applicationPackage_id", "");

    mockCreateApplicationPackageForGrantor.mockResolvedValue(
      successfulCreateResponse,
    );

    await updateApplicationPackage(formData, mockRequiredForms);

    const requestBody = mockCreateApplicationPackageForGrantor.mock.calls[0][1];
    expect(requestBody.applicationPackage_title).toBeNull();
    expect(requestBody.opening_date).toBeNull();
    expect(requestBody.closing_date).toBeNull();
    expect(requestBody.public_applicationPackage_id).toBeNull();
  });
});
