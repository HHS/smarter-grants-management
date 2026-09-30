import { render } from "@testing-library/react";
import SessionStorage from "src/services/sessionStorage/sessionStorage";

import { PostAuthRedirect } from "./PostAuthRedirect";

const mockPush = jest.fn();
const mockUseSearchParams = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  useSearchParams: () => mockUseSearchParams() as unknown,
}));

const mockSetItem = jest.spyOn(SessionStorage, "setItem");
const mockRemoveItem = jest.spyOn(SessionStorage, "removeItem");

describe("PostAuthRedirect", () => {
  beforeEach(() => {
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
  });
  afterEach(() => {
    jest.clearAllMocks();
  });

  it("should redirect to home if no redirect URL is stored", () => {
    render(<PostAuthRedirect errorMessage="oops" />);

    expect(mockRemoveItem).toHaveBeenCalledWith("post-auth-redirect");
    expect(mockPush).toHaveBeenCalledWith("/");
    expect(mockPush).toHaveBeenCalledTimes(2);
  });

  it("should redirect to home if redirect URL is empty", () => {
    render(<PostAuthRedirect errorMessage="oops" redirectURL="" />);

    expect(mockRemoveItem).toHaveBeenCalledWith("post-auth-redirect");
    expect(mockPush).toHaveBeenCalledWith("/");
    expect(mockPush).toHaveBeenCalledTimes(2);
  });

  it("should redirect to home if redirect URL doesn't start with /", () => {
    render(
      <PostAuthRedirect
        errorMessage="oops"
        redirectURL="https://malicious-site.com"
      />,
    );

    expect(mockRemoveItem).toHaveBeenCalledWith("post-auth-redirect");
    expect(mockPush).toHaveBeenCalledWith("/");
    expect(mockPush).toHaveBeenCalledTimes(2);
  });

  it("should display 'Redirecting...' text", () => {
    const { container } = render(
      <PostAuthRedirect errorMessage="oops" redirectURL="/some-path" />,
    );

    expect(container).toHaveTextContent("Redirecting...");
  });

  it("should display custom display text if supplied", () => {
    const { container } = render(
      <PostAuthRedirect
        errorMessage="oops"
        displayMessage="custom..."
        redirectURL="/some-path"
      />,
    );

    expect(container).toHaveTextContent("custom...");
  });

  it("should set pivError if specified and param received", () => {
    mockUseSearchParams.mockReturnValue(
      new URLSearchParams({ pivError: "true" }),
    );
    render(
      <PostAuthRedirect
        errorMessage="oops"
        displayMessage="custom..."
        checkPiv={true}
        redirectURL="/some-path"
      />,
    );

    expect(mockSetItem).toHaveBeenCalledWith("showPivError", "true");
  });
});
