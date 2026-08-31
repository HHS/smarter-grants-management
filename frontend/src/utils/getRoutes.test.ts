import { getNextRoutes } from "src/utils/getRoutes";

// TODO: https://github.com/navapbc/simpler-grants-gov/issues/98
// Need to move listPaths to a different file and mock it in order to make this more isolated

describe("getNextRoutes", () => {
  it("should get Next.js routes from src directory", () => {
    const result = getNextRoutes("src/app");

    expect(result).toEqual([
      "/award-recommendation/1/application-submissions/[applicationSubmissionId]/edit",
      "/award-recommendation/1/application-submissions/edit/bulk",
      "/award-recommendation/1/application-submissions/edit",
      "/award-recommendation/1/edit",
      "/award-recommendation/1",
      "/award-recommendation/1/risks/[riskId]/edit",
      "/award-recommendation/1/risks/add",
      "/award-recommendation/1/risks",
      "/award-recommendation/create",
      "/award-recommendation",
      "/award-recommendation/select-opportunity",
      "/dev/feature-flags",
      "/error",
      "/login",
      "/logout",
      "/maintenance",
      "/opportunities/create",
      "/opportunities",
      "/opportunity/1/competition",
      "/opportunity/1/edit",
      "/opportunity/1/overview",
      "/",
      "/unauthenticated",
    ]);
  });
});
