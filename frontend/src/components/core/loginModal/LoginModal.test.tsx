import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { storeCurrentPage } from "src/utils/userUtils";

import { RefObject } from "react";
import { ModalRef } from "@trussworks/react-uswds";

import { LoginModal } from "src/components/core/loginModal/LoginModal";

const mockStoreCurrentPage = jest.fn();
const mockApiKeyLoginAction = jest.fn().mockReturnValue({});

jest.mock("src/utils/userUtils", () => ({
  storeCurrentPage: () => mockStoreCurrentPage() as unknown,
}));

jest.mock("src/components/core/loginModal/actions", () => ({
  apiKeyLoginAction: () => mockApiKeyLoginAction() as unknown,
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
  it("calls storeCurrentPage when sign-in is clicked", async () => {
    // (userUtils.storeCurrentPage as jest.Mock).mockClear();
    // mockUseUser.mockReturnValue({
    //   user: { token: undefined },
    //   hasBeenLoggedOut: false,
    //   resetHasBeenLoggedOut: jest.fn(),
    // });
    // const user = userEvent.setup();
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
  });
});
