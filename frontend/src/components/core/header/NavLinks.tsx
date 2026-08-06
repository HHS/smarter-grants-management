import clsx from "clsx";
import { LOGIN_URL } from "src/constants/auth";
import { useUser } from "src/services/auth/useUser";
import { IndexType } from "src/types/generalTypes";
import { isCurrentPath, isExternalLink } from "src/utils/generalUtils";
import { storeCurrentPage } from "src/utils/userUtils";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Dispatch,
  SetStateAction,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { PrimaryNav } from "@trussworks/react-uswds";

import NavDropdown from "src/components/core/header/NavDropdown";
import { USWDSIcon } from "src/components/core/USWDSIcon";
import { SignOutNavLink } from "./SignOutNavLink";

type PrimaryLink = {
  text?: string;
  href?: string;
  children?: PrimaryLink[];
};

export type LoggedInNavConfig = {
  name: string;
  items: { link: string; displayText: string }[];
};

const homeRegexp = /^\/(?:e[ns])?$/;

const NavLink = ({
  href = "",
  classes,
  onClick,
  text,
}: {
  href?: string;
  classes?: string;
  onClick: () => void;
  text: string;
}) => {
  let iconBtnClass, linkTarget;

  if (isExternalLink(href)) {
    iconBtnClass = "icon-btn";
    linkTarget = "_blank";
  }

  return (
    <Link
      href={href}
      key={href}
      className={classes}
      target={linkTarget}
      onClick={onClick}
    >
      <span className={iconBtnClass}>
        {text}
        {isExternalLink(href) && (
          <USWDSIcon name="launch" className="usa-icon--size-2" />
        )}
      </span>
    </Link>
  );
};

const NavItem = ({
  activeNavDropdownIndex,
  closeDropdownAndMobileNav,
  currentNavItemIndex,
  navLinkConfig,
  setActiveNavDropdownIndex,
  index,
}: {
  activeNavDropdownIndex: IndexType;
  closeDropdownAndMobileNav: () => void;
  currentNavItemIndex: IndexType;
  navLinkConfig: PrimaryLink;
  setActiveNavDropdownIndex: Dispatch<SetStateAction<IndexType>>;
  index: number;
}) => {
  if (!navLinkConfig.text) {
    return <></>;
  }
  if (navLinkConfig.children) {
    const childItems = navLinkConfig.children.map((childLink) => {
      if (!childLink.text) {
        return <></>;
      }
      return (
        <NavLink
          href={childLink.href}
          key={childLink.href}
          onClick={closeDropdownAndMobileNav}
          text={childLink.text}
        />
      );
    });
    return (
      <NavDropdown
        key={navLinkConfig.href}
        activeNavDropdownIndex={activeNavDropdownIndex}
        index={index}
        isCurrent={currentNavItemIndex === index}
        linkText={navLinkConfig.text}
        menuItems={childItems}
        setActiveNavDropdownIndex={setActiveNavDropdownIndex}
      />
    );
  }
  return (
    <NavLink
      href={navLinkConfig.href}
      key={navLinkConfig.href}
      onClick={closeDropdownAndMobileNav}
      text={navLinkConfig.text}
      classes={clsx({
        "usa-nav__link": true,
        "usa-current": currentNavItemIndex === index,
        "text-bold": true,
      })}
    />
  );
};

export const NavLinks = ({
  mobileExpanded,
  onToggleMobileNav,
  loggedInNavConfig,
}: {
  mobileExpanded: boolean;
  onToggleMobileNav: () => void;
  loggedInNavConfig: LoggedInNavConfig;
}) => {
  const t = useTranslations("Header.navLinks");

  const path = usePathname();
  const { user } = useUser();

  const closeMobileNav = useCallback(() => {
    if (mobileExpanded) {
      onToggleMobileNav();
    }
  }, [mobileExpanded, onToggleMobileNav]);

  const [activeNavDropdownIndex, setActiveNavDropdownIndex] =
    useState<IndexType>(null);

  const closeDropdownAndMobileNav = useCallback(() => {
    setActiveNavDropdownIndex(null);
    closeMobileNav();
  }, [closeMobileNav]);

  // this piece should be passed in to make the header flexible for both sides
  const navLinkList = useMemo(() => {
    const anonymousNavLinks: PrimaryLink[] = [{ text: t("home"), href: "/" }];
    if (!user?.token) {
      return anonymousNavLinks;
    }

    return anonymousNavLinks.toSpliced(anonymousNavLinks.length, 0, {
      text: t("opportunities"),
      href: "/opportunities",
    });
  }, [t, user?.token]);

  const getCurrentNavItemIndex = useCallback(
    (currentPath: string): number => {
      // handle base case of home page separately
      if (currentPath.match(homeRegexp)) {
        return 0;
      }
      const index = navLinkList.slice(1).findIndex(({ href, children }) => {
        if (!href) {
          if (!children?.length) {
            return false;
          }
          // mark as current if any child page is active
          return children.some((child) => {
            return child?.href && isCurrentPath(child.href, currentPath);
          });
        } else {
          return isCurrentPath(href, currentPath);
        }
      });
      // account for home path as default / not found
      return index === -1 ? index : index + 1;
    },
    [navLinkList],
  );

  const [currentNavItemIndex, setCurrentNavItemIndex] = useState<number>(
    getCurrentNavItemIndex(path),
  );

  useEffect(() => {
    // TODO #9633
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCurrentNavItemIndex(getCurrentNavItemIndex(path));
  }, [path, getCurrentNavItemIndex]);

  const navItems = useMemo(() => {
    const items = navLinkList.map((navLinkConfig, index) => (
      <NavItem
        key={navLinkConfig.text}
        activeNavDropdownIndex={activeNavDropdownIndex}
        closeDropdownAndMobileNav={closeDropdownAndMobileNav}
        currentNavItemIndex={currentNavItemIndex}
        navLinkConfig={navLinkConfig}
        setActiveNavDropdownIndex={setActiveNavDropdownIndex}
        index={index}
      />
    ));
    // add user account nav depending on login status
    if (!user?.token) {
      items.push(
        <NavLink
          key="sign-in"
          href={LOGIN_URL}
          onClick={() => {
            storeCurrentPage(location.pathname, location.search);
            closeDropdownAndMobileNav();
          }}
          text={t("login")}
          classes={clsx({
            "usa-nav__link": true,
            "text-normal": true,
          })}
        />,
      );
    } else if (loggedInNavConfig) {
      const accountIndex = navLinkList.length;
      items.push(
        <NavDropdown
          key={loggedInNavConfig.name}
          activeNavDropdownIndex={activeNavDropdownIndex}
          index={accountIndex}
          isCurrent={false}
          linkText={loggedInNavConfig.name}
          setActiveNavDropdownIndex={setActiveNavDropdownIndex}
          menuItems={[
            ...loggedInNavConfig.items.map((loggedInNavItem) => (
              <NavLink
                href={loggedInNavItem.link}
                key={loggedInNavItem.displayText}
                onClick={closeDropdownAndMobileNav}
                text={loggedInNavItem.displayText}
              />
            )),
            <SignOutNavLink key="logout" onClick={closeDropdownAndMobileNav} />,
          ]}
        />,
      );
    }
    return items;
  }, [
    t,
    activeNavDropdownIndex,
    closeDropdownAndMobileNav,
    currentNavItemIndex,
    navLinkList,
    setActiveNavDropdownIndex,
    user?.token,
    loggedInNavConfig,
  ]);

  return (
    <PrimaryNav
      items={(navItems as React.ReactNode[]) || []}
      mobileExpanded={mobileExpanded}
      onToggleMobileNav={onToggleMobileNav}
      className="padding-bottom-05"
    ></PrimaryNav>
  );
};
