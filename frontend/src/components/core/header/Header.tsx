"use client";

import clsx from "clsx";
import { applicationTestUserId } from "src/constants/auth";
// import GrantsLogo from "public/img/grants-logo.svg";
import { useSnackbar } from "src/hooks/useSnackbar";
import { useUser } from "src/services/auth/useUser";
import { TestUser } from "src/types/userTypes";

import { useTranslations } from "next-intl";
// import Image from "next/image";
import Link from "next/link";
import { Suspense, useCallback, useEffect, useState } from "react";
import {
  GovBanner,
  NavMenuButton,
  Title,
  Header as USWDSHeader,
} from "@trussworks/react-uswds";

import { RouteChangeWatcher } from "src/components/core/header/RouteChangeWatcher";
import { TestUserSelect } from "src/components/core/header/TestUserSelect";
import { NavLinks } from "./NavLinks";

const Header = ({
  locale,
  localDev = false,
  testUsers = [],
}: {
  locale?: string;
  localDev?: boolean;
  testUsers?: TestUser[];
}) => {
  const t = useTranslations("Header");
  const [isMobileNavExpanded, setIsMobileNavExpanded] =
    useState<boolean>(false);

  const { hasBeenLoggedOut, resetHasBeenLoggedOut, user } = useUser();
  const { showSnackbar, Snackbar, hideSnackbar, snackbarIsVisible } =
    useSnackbar();

  useEffect(() => {
    if (hasBeenLoggedOut) {
      showSnackbar(-1);
      resetHasBeenLoggedOut();
    }
  }, [hasBeenLoggedOut, showSnackbar, resetHasBeenLoggedOut]);

  const closeMenuOnEscape = useCallback((event: KeyboardEvent) => {
    if (event.key === "Escape") {
      setIsMobileNavExpanded(false);
    }
  }, []);

  useEffect(() => {
    if (isMobileNavExpanded) {
      document.addEventListener("keyup", closeMenuOnEscape);
    }
    return () => {
      document.removeEventListener("keyup", closeMenuOnEscape);
    };
  }, [isMobileNavExpanded, closeMenuOnEscape]);

  const language = locale && locale.match("/^es/") ? "spanish" : "english";

  const handleMobileNavToggle = () => {
    setIsMobileNavExpanded(!isMobileNavExpanded);
  };

  return (
    <>
      <Suspense>
        <RouteChangeWatcher />
      </Suspense>
      <div
        className={clsx({
          "usa-overlay": true,
          "desktop:display-none": true,
          "is-visible": isMobileNavExpanded,
        })}
        onClick={() => {
          if (isMobileNavExpanded) {
            setIsMobileNavExpanded(false);
          }
        }}
      />
      <GovBanner language={language} />
      <USWDSHeader
        basic={true}
        className="desktop:position-sticky top-0 desktop:z-500 bg-white border-bottom-2px border-primary-vivid"
      >
        <div className="usa-nav-container display-flex flex-justify">
          <div className="usa-navbar border-bottom-0">
            <Title className="margin-y-2">
              <div className="display-flex flex-align-center">
                <Link href="/" className="position-relative">
                  Smarter Grants
                  {/* <Image
                    alt={t("title")}
                    src={GrantsLogo as string}
                    className="height-4 display-block position-relative desktop:height-auto"
                    unoptimized
                    priority
                    fill
                  /> */}
                </Link>
              </div>
            </Title>
          </div>
          {localDev && testUsers && (
            <TestUserSelect
              testUsers={testUsers}
              isApplicationTestUser={user?.user_id === applicationTestUserId}
            />
          )}
          <div className="usa-navbar order-last desktop:display-none">
            <NavMenuButton
              onClick={handleMobileNavToggle}
              label={t("navLinks.menuToggle")}
              className="usa-menu-btn"
            />
          </div>
          <NavLinks
            mobileExpanded={isMobileNavExpanded}
            onToggleMobileNav={handleMobileNavToggle}
            loggedInNavConfig={{
              items: [
                { link: "/notifications", displayText: "Notifications" },
                { link: "/settings", displayText: "Settings" },
              ],
              name: "Account",
            }}
          />
        </div>
      </USWDSHeader>
      <Snackbar close={hideSnackbar} isVisible={snackbarIsVisible}>
        {t("tokenExpired")}
      </Snackbar>
    </>
  );
};

export default Header;
