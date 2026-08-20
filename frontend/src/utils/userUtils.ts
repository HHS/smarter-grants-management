import SessionStorage from "src/services/sessionStorage/sessionStorage";

export const storeCurrentPage = (pathname: string, search: string) => {
  const startURL = `${pathname}${search}`;
  if (startURL !== "") {
    SessionStorage.setItem("login-redirect", startURL);
  }
};
