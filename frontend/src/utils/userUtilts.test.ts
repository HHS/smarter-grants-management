import { storeCurrentPage } from "src/utils/userUtils";

const mockSetItem = jest.fn<void, [string, string]>();

jest.mock("src/services/sessionStorage/sessionStorage", () => {
  return {
    __esModule: true,
    default: {
      setItem: (key: string, value: string): void => mockSetItem(key, value),
    },
  };
});

describe("storeCurrentPage", () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  it("should store URL in session storage if pathname and search", () => {
    storeCurrentPage("path", "/search");
    expect(mockSetItem).toHaveBeenCalledWith(
      "post-auth-redirect",
      "path/search",
    );
  });

  it("should not store URL in session storage if pathname and search are empty", () => {
    storeCurrentPage("", "");
    expect(mockSetItem).not.toHaveBeenCalled();
  });
});
