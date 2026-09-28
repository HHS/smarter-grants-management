import { identity } from "lodash";
import { ApiRequestError } from "src/errors";
import {
  createApplicationPackage,
  saveCompetitionInstructions,
  updateApplicationPackage,
  updateApplicationPackageForms,
} from "src/services/fetch/fetchers/grantorAnnouncementFetcher";
import { ApplicationPackageFormsSubmitApi } from "src/types/applicationPackageResponseTypes";

import {
  applicationPackageFormAction,
  saveApplicationPackage,
} from "./actions";

jest.mock("next-intl/server", () => ({
  getTranslations: () => identity,
}));

jest.mock("src/services/fetch/fetchers/grantorAnnouncementFetcher", () => ({
  createApplicationPackage: jest.fn(),
  saveCompetitionInstructions: jest.fn(),
  updateApplicationPackage: jest.fn(),
  updateApplicationPackageForms: jest.fn(),
}));

const mockRedirect = jest.fn();
jest.mock("next/navigation", () => ({
  redirect: (url: string): void => {
    mockRedirect(url);
  },
}));

const mockCreateApplicationPackage = jest.mocked(createApplicationPackage);
const mockUpdateApplicationPackage = jest.mocked(updateApplicationPackage);
const mockSaveCompetitionInstructions = jest.mocked(
  saveCompetitionInstructions,
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
    application_package_id: "new-application-package-id",
  },
} as Awaited<ReturnType<typeof createApplicationPackage>>;

const successfulUpdateResponse = {
  message: "success",
  status_code: 200,
  data: {
    application_package_id: "existing-application-package-id",
  },
} as Awaited<ReturnType<typeof updateApplicationPackage>>;

function buildValidFormData(overrides?: Record<string, string>) {
  const formData = new FormData();
  formData.set("announcementId", "opp-123");
  formData.set("applicationPackageId", "compete-456");
  formData.set("application_package_title", "Test ApplicationPackage");
  formData.set("opening_timestamp", "2026-06-01");
  formData.set("closing_timestamp", "2026-07-01");
  formData.set("public_application_package_id", "PUBLIC-COMP-789");
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

describe("saveApplicationPackage", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("returns an error when announcementId is missing", async () => {
    const formData = new FormData();
    formData.set("applicationPackageId", "compete-456");

    const result = await saveApplicationPackage(formData, mockRequiredForms);

    expect(result).toEqual({
      errorMessage: "genericError",
    });
  });

  it("calls createApplicationPackage when no applicationPackageId", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");

    mockCreateApplicationPackage.mockResolvedValue(successfulCreateResponse);

    const result = await saveApplicationPackage(formData, mockRequiredForms);

    expect(mockCreateApplicationPackage).toHaveBeenCalledWith(
      "opp-123",
      expect.objectContaining({
        application_package_title: "Test ApplicationPackage",
        opening_timestamp: "2026-06-01T00:00:00.000Z",
        closing_timestamp: "2026-07-01T00:00:00.000Z",
        public_application_package_id: "PUBLIC-COMP-789",
      }),
    );
    expect(result).toEqual({
      successMessage: "success",
    });
  });

  it("updates application package forms with the new application package ID after creating", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");

    mockCreateApplicationPackage.mockResolvedValue(successfulCreateResponse);

    await saveApplicationPackage(formData, mockRequiredForms);

    expect(mockUpdateApplicationPackageForms).toHaveBeenCalledWith({
      announcementId: "opp-123",
      applicationPackageId: "new-application-package-id",
      body: { forms: mockRequiredForms },
    });
  });

  it("calls updateApplicationPackage when applicationPackageId exists", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackage.mockResolvedValue(successfulUpdateResponse);

    const result = await saveApplicationPackage(formData, mockRequiredForms);

    expect(mockUpdateApplicationPackage).toHaveBeenCalledWith(
      "opp-123",
      "compete-456",
      expect.objectContaining({
        application_package_title: "Test ApplicationPackage",
        opening_timestamp: "2026-06-01T00:00:00.000Z",
        closing_timestamp: "2026-07-01T00:00:00.000Z",
        public_application_package_id: "PUBLIC-COMP-789",
      }),
    );
    expect(result).toEqual({
      successMessage: "success",
    });
  });

  it("updates application package forms with the existing application package ID", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackage.mockResolvedValue(successfulUpdateResponse);

    await saveApplicationPackage(formData, mockRequiredForms);

    expect(mockUpdateApplicationPackageForms).toHaveBeenCalledWith({
      announcementId: "opp-123",
      applicationPackageId: "compete-456",
      body: { forms: mockRequiredForms },
    });
  });

  it("saves application instructions when creating an application package with a pending file ID", async () => {
    const formData = buildValidFormData({
      "pending-file-id": "pending-file-789",
    });
    formData.delete("applicationPackageId");

    mockCreateApplicationPackage.mockResolvedValue(successfulCreateResponse);

    const result = await saveApplicationPackage(formData, mockRequiredForms);

    expect(mockSaveCompetitionInstructions).toHaveBeenCalledWith(
      "opp-123",
      "new-application-package-id",
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

    mockUpdateApplicationPackage.mockResolvedValue(successfulUpdateResponse);

    const result = await saveApplicationPackage(formData, mockRequiredForms);

    expect(mockSaveCompetitionInstructions).toHaveBeenCalledWith(
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

    mockUpdateApplicationPackage.mockResolvedValue(successfulUpdateResponse);
    mockSaveCompetitionInstructions.mockRejectedValue(new Error("unexpected"));

    const result = await saveApplicationPackage(formData, mockRequiredForms);

    expect(mockSaveCompetitionInstructions).toHaveBeenCalledWith(
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

    mockUpdateApplicationPackage.mockRejectedValue(
      new ApiRequestError("unauthenticated", "APIRequestError", 401),
    );

    const result = await saveApplicationPackage(formData, mockRequiredForms);

    expect(result).toEqual({
      errorMessage: "unauthenticated",
    });
  });

  it("maps 403 to a forbidden error", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackage.mockRejectedValue(
      new ApiRequestError("forbidden", "APIRequestError", 403),
    );

    const result = await saveApplicationPackage(formData, mockRequiredForms);

    expect(result).toEqual({
      errorMessage: "forbidden",
    });
  });

  it("maps 404 to a not found error", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackage.mockRejectedValue(
      new ApiRequestError("notFound", "APIRequestError", 404),
    );

    const result = await saveApplicationPackage(formData, mockRequiredForms);

    expect(result).toEqual({
      errorMessage: "notFound",
    });
  });

  it("maps 422 to validationErrors with formatted error message", async () => {
    const formData = buildValidFormData();

    const apiError = new ApiRequestError(
      "Validation error",
      "ValidationError",
      422,
      {
        field: "open_to_applicants",
        message: "Shorter than minimum length 1.",
      },
    );

    mockUpdateApplicationPackage.mockRejectedValue(apiError);

    const result = await saveApplicationPackage(formData, mockRequiredForms);

    expect(result).toEqual({
      errorMessage: "validationErrors",
      validationErrors: ["open_to_applicants: Shorter than minimum length 1."],
    });
  });

  it("maps unknown errors to a generic error", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackage.mockRejectedValue(new Error("unexpected"));

    const result = await saveApplicationPackage(formData, mockRequiredForms);

    expect(result).toEqual({
      errorMessage: "genericError",
    });
  });
});

describe("applicationPackageFormAction", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("delegates to saveApplicationPackage and redirects to ../overview for saveAndExit", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackage.mockResolvedValue(successfulUpdateResponse);

    await applicationPackageFormAction(
      "saveAndExit",
      mockRequiredForms,
      formData,
    );

    expect(mockUpdateApplicationPackage).toHaveBeenCalledTimes(1);
    expect(mockRedirect).toHaveBeenCalledWith("../overview");
  });

  it("delegates to saveApplicationPackage and redirects to ../edit for saveAndGoBack", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackage.mockResolvedValue(successfulUpdateResponse);

    await applicationPackageFormAction(
      "saveAndGoBack",
      mockRequiredForms,
      formData,
    );

    expect(mockUpdateApplicationPackage).toHaveBeenCalledTimes(1);
    expect(mockRedirect).toHaveBeenCalledWith("../edit");
  });

  it("delegates to saveApplicationPackage and redirects to ../overview for saveAndContinue", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackage.mockResolvedValue(successfulUpdateResponse);

    await applicationPackageFormAction(
      "saveAndContinue",
      mockRequiredForms,
      formData,
    );

    expect(mockUpdateApplicationPackage).toHaveBeenCalledTimes(1);
    expect(mockRedirect).toHaveBeenCalledWith("../overview");
  });

  it("returns errors without redirecting when saveApplicationPackage returns errorMessage", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackage.mockRejectedValue(
      new ApiRequestError("forbidden", "APIRequestError", 403),
    );

    const result = await applicationPackageFormAction(
      "saveAndContinue",
      mockRequiredForms,
      formData,
    );

    expect(mockUpdateApplicationPackage).toHaveBeenCalledTimes(1);
    expect(mockRedirect).not.toHaveBeenCalled();
    expect(result).toEqual({
      errorMessage: "forbidden",
    });
  });

  it("returns saveResult for unknown submitType without redirecting", async () => {
    const formData = buildValidFormData();

    mockUpdateApplicationPackage.mockResolvedValue(successfulUpdateResponse);

    const result = await applicationPackageFormAction(
      "unknownType",
      mockRequiredForms,
      formData,
    );

    expect(mockUpdateApplicationPackage).toHaveBeenCalledTimes(1);
    expect(mockRedirect).not.toHaveBeenCalled();
    expect(result).toEqual({
      successMessage: "success",
    });
  });
});

describe("buildRequestBody (tested indirectly via saveApplicationPackage)", () => {
  beforeEach(() => {
    jest.resetAllMocks();
  });

  it("builds correct request body for 'both' applicant type", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");

    mockCreateApplicationPackage.mockResolvedValue(successfulCreateResponse);

    await saveApplicationPackage(formData, mockRequiredForms);

    const requestBody = mockCreateApplicationPackage.mock.calls[0][1];
    expect(requestBody.open_to_applicants).toEqual([
      "organization",
      "individual",
    ]);
  });

  it("includes the public application package ID in the request body", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");

    mockCreateApplicationPackage.mockResolvedValue(successfulCreateResponse);

    await saveApplicationPackage(formData, mockRequiredForms);

    const requestBody = mockCreateApplicationPackage.mock.calls[0][1];
    expect(requestBody.public_application_package_id).toBe("PUBLIC-COMP-789");
  });

  it("builds correct request body for 'organizations_only' applicant type", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");
    formData.set("open_to_applicants", "organizations_only");

    mockCreateApplicationPackage.mockResolvedValue(successfulCreateResponse);

    await saveApplicationPackage(formData, mockRequiredForms);

    const requestBody = mockCreateApplicationPackage.mock.calls[0][1];
    expect(requestBody.open_to_applicants).toEqual(["organization"]);
  });

  it("builds correct request body for 'individuals_only' applicant type", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");
    formData.set("open_to_applicants", "individuals_only");

    mockCreateApplicationPackage.mockResolvedValue(successfulCreateResponse);

    await saveApplicationPackage(formData, mockRequiredForms);

    const requestBody = mockCreateApplicationPackage.mock.calls[0][1];
    expect(requestBody.open_to_applicants).toEqual(["individual"]);
  });

  it("concatenates contact info correctly", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");

    mockCreateApplicationPackage.mockResolvedValue(successfulCreateResponse);

    await saveApplicationPackage(formData, mockRequiredForms);

    const requestBody = mockCreateApplicationPackage.mock.calls[0][1];
    expect(requestBody.contact_info).toBe(
      "John Doe | Manager | john@example.com | 555-0100",
    );
  });

  it("converts grace_period to a number when provided", async () => {
    const formData = buildValidFormData({ grace_period: "30" });
    formData.delete("applicationPackageId");

    mockCreateApplicationPackage.mockResolvedValue(successfulCreateResponse);

    await saveApplicationPackage(formData, mockRequiredForms);

    const requestBody = mockCreateApplicationPackage.mock.calls[0][1];
    expect(requestBody.grace_period).toBe(30);
  });

  it("converts opening and closing dates to ISO timestamps", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");

    mockCreateApplicationPackage.mockResolvedValue(successfulCreateResponse);

    await saveApplicationPackage(formData, mockRequiredForms);

    const requestBody = mockCreateApplicationPackage.mock.calls[0][1];
    expect(requestBody.opening_timestamp).toBe("2026-06-01T00:00:00.000Z");
    expect(requestBody.closing_timestamp).toBe("2026-07-01T00:00:00.000Z");
  });

  it("handles empty field values by returning null", async () => {
    const formData = buildValidFormData();
    formData.delete("applicationPackageId");
    formData.set("application_package_title", "");
    formData.set("opening_timestamp", "");
    formData.set("closing_timestamp", "");
    formData.set("public_application_package_id", "");

    mockCreateApplicationPackage.mockResolvedValue(successfulCreateResponse);

    await saveApplicationPackage(formData, mockRequiredForms);

    const requestBody = mockCreateApplicationPackage.mock.calls[0][1];
    expect(requestBody.application_package_title).toBeNull();
    expect(requestBody.opening_timestamp).toBeNull();
    expect(requestBody.closing_timestamp).toBeNull();
    expect(requestBody.public_application_package_id).toBeNull();
  });
});
