"use-client";

import { storeCurrentPage } from "src/utils/userUtils";

import { redirect } from "next/navigation";
import { RefObject, useActionState } from "react";
import {
  Button,
  ButtonGroup,
  ErrorMessage,
  ModalFooter,
  ModalRef,
  ModalToggleButton,
} from "@trussworks/react-uswds";

import { SimplerModal } from "src/components/core/SimplerModal";
import { apiKeyLoginAction } from "./action";

export const LoginModal = ({
  modalRef,
  helpText,
  titleText,
  descriptionText,
  buttonText,
  closeText,
  modalId,
}: {
  modalRef: RefObject<ModalRef>;
  helpText: string;
  titleText: string;
  descriptionText: string;
  buttonText: string;
  closeText: string;
  modalId: string;
}) => {
  return (
    <SimplerModal
      modalId={modalId}
      modalRef={modalRef}
      titleText={titleText}
      className="text-wrap"
    >
      <LoginModalBody
        buttonText={buttonText}
        closeText={closeText}
        descriptionText={descriptionText}
        helpText={helpText}
        modalRef={modalRef}
      />
    </SimplerModal>
  );
};

const toggleModal = (modalRef: RefObject<ModalRef>) =>
  modalRef.current.toggleModal();

const LoginModalBody = ({
  buttonText,
  closeText,
  descriptionText,
  helpText,
  modalRef,
}: {
  buttonText: string;
  closeText: string;
  descriptionText: string;
  helpText: string;
  modalRef: RefObject<ModalRef | null>;
}) => {
  const [formState, formAction] = useActionState(apiKeyLoginAction, {});
  if (formState.token) {
    redirect(`/api/auth/callback?token=${formState.token}`);
  }
  // // may need to check logged in state here to make sure we can open up the modal after login/logout
  // if (formState.success && modalRef) {
  //   toggleModal(modalRef as RefObject<ModalRef>);
  // }
  return (
    <>
      <p>{helpText}</p>
      <p className="font-sans-2xs margin-y-4">{descriptionText}</p>
      <form action={formAction}>
        {formState.error && <ErrorMessage>Login error</ErrorMessage>}
        {formState.unauthenticated && (
          <ErrorMessage>Invalid API key</ErrorMessage>
        )}
        <input name="apiKey" />
        <ModalFooter>
          <ButtonGroup>
            <Button
              type="submit"
              onClick={() => {
                storeCurrentPage(location.pathname, location.search);
              }}
            >
              {buttonText}
            </Button>
            <ModalToggleButton
              modalRef={modalRef}
              closer
              unstyled
              className="padding-105 text-center"
            >
              {closeText}
            </ModalToggleButton>
          </ButtonGroup>
        </ModalFooter>
      </form>
    </>
  );
};
