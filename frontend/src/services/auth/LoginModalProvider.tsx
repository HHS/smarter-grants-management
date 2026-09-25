"use client";

import {
  createContext,
  PropsWithChildren,
  RefObject,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react";
import { ModalRef } from "@trussworks/react-uswds";

import { LoginModal } from "src/components/core/loginModal/LoginModal";

type LoginModalContextValue = {
  loginModalRef: RefObject<ModalRef | null>;
  setHelpText: (text: string) => void;
  setTitleText: (text: string) => void;
  setDescriptionText: (text: string) => void;
  setButtonText: (text: string) => void;
  setCloseText: (text: string) => void;
};

const LoginModalContext = createContext<LoginModalContextValue | null>(null);

// export const useLoginModal = ({
//   helpText = "",
//   titleText = "",
//   descriptionText = "",
//   buttonText = "",
//   closeText = "",
// }) => {
export const useLoginModal = () => {
  const ctx = useContext(LoginModalContext);
  if (ctx === null) {
    throw new Error("useLoginModal must be used within <LoginModalProvider>");
  }
  // ctx.setHelpText(helpText);
  // ctx.setTitleText(titleText);
  // ctx.setDescriptionText(descriptionText);
  // ctx.setButtonText(buttonText);
  // ctx.setCloseText(closeText);
  return ctx;
};

interface LoginProviderProps extends PropsWithChildren {
  helpText?: string;
  titleText?: string;
  descriptionText?: string;
  buttonText?: string;
  closeText?: string;
}
export function LoginModalProvider({
  children,
  helpText = "",
  titleText = "",
  descriptionText = "",
  buttonText = "",
  closeText = "",
}: LoginProviderProps) {
  const loginModalRef = useRef<ModalRef | null>(null);

  const [dynamicHelpText, setHelpText] = useState<string>(helpText);
  const [dynamicTitleText, setTitleText] = useState<string>(titleText);
  const [dynamicDescriptionText, setDescriptionText] =
    useState<string>(descriptionText);
  const [dynamicButtonText, setButtonText] = useState<string>(buttonText);
  const [dynamicCloseText, setCloseText] = useState<string>(closeText);

  const contextValue = useMemo(
    () => ({
      loginModalRef,
      setHelpText,
      setTitleText,
      setDescriptionText,
      setButtonText,
      setCloseText,
    }),
    [
      loginModalRef,
      setHelpText,
      setTitleText,
      setDescriptionText,
      setButtonText,
      setCloseText,
    ],
  );

  return (
    <>
      <LoginModal
        modalRef={loginModalRef as RefObject<ModalRef>}
        helpText={dynamicHelpText}
        titleText={dynamicTitleText}
        descriptionText={dynamicDescriptionText}
        buttonText={dynamicButtonText}
        closeText={dynamicCloseText}
        modalId={"simpler-login-modal"}
      />
      <LoginModalContext.Provider value={contextValue}>
        {children}
      </LoginModalContext.Provider>
    </>
  );
}
