import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RefObject } from "react";
import { ModalRef } from "@trussworks/react-uswds";

import { LoginModal } from "src/components/core/loginModal/LoginModal";

const mockStoreCurrentPage = jest.fn();
const mockApiKeyLoginAction = jest.fn().mockReturnValue({});
const mockRedirect = jest.fn();

jest.mock("src/utils/userUtils", () => ({
  storeCurrentPage: () => mockStoreCurrentPage() as unknown,
}));

jest.mock("src/components/core/loginModal/actions", () => ({
  apiKeyLoginAction: () => mockApiKeyLoginAction() as unknown,
}));

jest.mock("next/navigation", () => ({
  redirect: (url: string): void => {
    mockRedirect(url);
  },
}));

describe("LoginModal", () => {
  const createModalRef = (): RefObject<ModalRef> => ({
    current: {
      modalId: "test-modal",
      modalIsOpen: false,
      toggleModal: jest.fn(),
      focus: jest.fn(),
    } as unknown as ModalRef,
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("should render the login modal", () => {
    const modalRef = createModalRef();
    render(
      <LoginModal
        modalRef={modalRef}
        helpText="Help text"
        titleText="Login"
        descriptionText="Please login"
        buttonText="Sign In"
        closeText="Close"
        modalId="login-modal"
      />,
    );

    expect(screen.getByText("Sign In")).toBeInTheDocument();
    expect(screen.getByText("Close")).toBeInTheDocument();
  });

  it("should render the login button with custom text", () => {
    const modalRef = createModalRef();
    const customButtonText = "Custom Login Text";

    render(
      <LoginModal
        modalRef={modalRef}
        helpText="Help text"
        titleText="Login"
        descriptionText="Please login"
        buttonText={customButtonText}
        closeText="Close"
        modalId="login-modal"
      />,
    );

    expect(screen.getByText(customButtonText)).toBeInTheDocument();
  });
  it("calls storeCurrentPage and runs form action when sign-in is clicked", async () => {
    const modalRef = createModalRef();
    render(
      <LoginModal
        modalRef={modalRef}
        helpText="Help text"
        titleText="Login"
        descriptionText="Please login"
        buttonText="Login Button"
        closeText="Close"
        modalId="login-modal"
      />,
    );
    const loginButton = screen.getByRole("button", { name: "Login Button" });
    await userEvent.click(loginButton);

    expect(mockStoreCurrentPage).toHaveBeenCalled();
    expect(mockApiKeyLoginAction).toHaveBeenCalled();
  });
  it("redirects to auth callback on successful form action", async () => {
    const modalRef = createModalRef();
    mockApiKeyLoginAction.mockReturnValue({ token: "a-token" });
    render(
      <LoginModal
        modalRef={modalRef}
        helpText="Help text"
        titleText="Login"
        descriptionText="Please login"
        buttonText="Login Button"
        closeText="Close"
        modalId="login-modal"
      />,
    );
    const loginButton = screen.getByRole("button", { name: "Login Button" });
    await userEvent.click(loginButton);
    expect(mockRedirect).toHaveBeenCalledWith(
      "/api/auth/callback?token=a-token",
    );
  });
  it("displays errors on unauthenticated form action", async () => {
    const modalRef = createModalRef();
    mockApiKeyLoginAction.mockReturnValue({ unauthenticated: true });
    render(
      <LoginModal
        modalRef={modalRef}
        helpText="Help text"
        titleText="Login"
        descriptionText="Please login"
        buttonText="Login Button"
        closeText="Close"
        modalId="login-modal"
      />,
    );
    const loginButton = screen.getByRole("button", { name: "Login Button" });
    await userEvent.click(loginButton);
    expect(screen.getByText("Invalid API key")).toBeInTheDocument();
  });
  it("displays errors on errored form action", async () => {
    const modalRef = createModalRef();
    mockApiKeyLoginAction.mockReturnValue({ error: true });
    render(
      <LoginModal
        modalRef={modalRef}
        helpText="Help text"
        titleText="Login"
        descriptionText="Please login"
        buttonText="Login Button"
        closeText="Close"
        modalId="login-modal"
      />,
    );
    const loginButton = screen.getByRole("button", { name: "Login Button" });
    await userEvent.click(loginButton);
    expect(screen.getByText("Login error")).toBeInTheDocument();
  });
});
