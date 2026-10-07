import { getNextRoutes } from "src/utils/getRoutes";

// TODO: https://github.com/navapbc/simpler-grants-gov/issues/98
// Need to move listPaths to a different file and mock it in order to make this more isolated

describe("getNextRoutes", () => {
  it("should get Next.js routes from src directory", () => {
    const result = getNextRoutes("src/app").sort();
    const expectedRoutes = [
      "/award-recommendation/1/application-submissions/[applicationSubmissionId]/edit",
      "/award-recommendation/1/application-submissions/edit/bulk",
      "/award-recommendation/1/application-submissions/edit",
      "/award-recommendation/1/edit",
      "/award-recommendation/1",
      "/award-recommendation/1/risks/[riskId]/edit",
      "/award-recommendation/1/risks/add",
      "/award-recommendation/1/risks",
      "/award-recommendation/1/submit-for-review",
      "/award-recommendation/create",
      "/award-recommendation",
      "/award-recommendation/select-opportunity",
      "/dev/feature-flags",
      "/error",
      "/login",
      "/logout",
      "/maintenance",
      "/announcements/create",
      "/announcements",
      "/announcement/1/application-package",
      "/announcement/1/edit",
      "/announcement/1/overview",
      "/",
      "/unauthenticated",
    ].sort();

    expect(result).toEqual(expectedRoutes);
  });
});
