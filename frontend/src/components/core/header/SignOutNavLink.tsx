import { LOGOUT_URL } from "src/constants/auth";
import { storeCurrentPage } from "src/utils/userUtils";

import { useTranslations } from "next-intl";
<<<<<<< HEAD
=======
import { useRouter } from "next/navigation";
import { useCallback } from "react";
>>>>>>> 7462cc802 (copypasta 3)

/** Sign out as a nav dropdown child—same structure as NavLink (Link + div) so it matches other menu items */
export const SignOutNavLink = ({
  closeDropdownAndMobileNav,
}: {
  closeDropdownAndMobileNav: () => void;
}) => {
  const t = useTranslations("Header.navLinks");

  return (
    <a
<<<<<<< HEAD
      key="sign-in"
      href={LOGOUT_URL}
      onClick={() => {
        storeCurrentPage(location.pathname, location.search);
        closeDropdownAndMobileNav();
=======
      href="#"
      onClick={(e) => {
        e.preventDefault();
        handleLogout().catch(() => undefined);
>>>>>>> 7462cc802 (copypasta 3)
      }}
    >
      {t("logout")}
    </a>
  );
};
