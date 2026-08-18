// stringifies query params, unencrypts any encrypted commas, and prepends a ?
export const paramsToFormattedQuery = (params: URLSearchParams): string => {
  if (!params.size) {
    return "";
  }
  return `?${decodeURIComponent(params.toString())}`;
};
