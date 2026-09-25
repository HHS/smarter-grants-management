// TODO(#auth-tracker): Authorization is temporarily bypassed on this page.
// Re-enable in this order:
// 1) Uncomment auth imports and helper types/functions in this file.
// 2) Restore agency query-param parsing (selectedAgencyId) in page inputs.
// 3) Restore getUserAgencies flow and no-agency / unauthorized page states.
// 4) Restore checkRequiredPrivileges and parseUserPrivileges usage.
// 5) Switch header back to agency-aware version and restore agency selector UI.
// 6) Switch fetchOpportunities back to agency-scoped endpoint.
// 7) Replace temporary announcementsAccess with privilege-derived access.
// 8) Update/expand tests to cover agency authorization behavior.

import TopLevelError from "src/app/[locale]/error/page";
import Unauthenticated from "src/app/[locale]/unauthenticated/page";
import { MissingAuthError, UnauthorizedError } from "src/errors";
import { getSession } from "src/services/auth/session";
import { fetchAnnouncements } from "src/services/fetch/fetchers/grantorAnnouncementFetcher";
import { LocalizedPageProps, TFn } from "src/types/intl";
import { WithFeatureFlagProps } from "src/types/uiTypes";
import { formatTimestamp } from "src/utils/generalUtils";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { redirect } from "next/navigation";
import { PropsWithChildren } from "react";
import { Alert, GridContainer } from "@trussworks/react-uswds";

import AnnouncementStatusTag from "src/components/announcement/AnnouncementStatusTag";
import { PopoverMenu } from "src/components/core/PopoverMenu";
import {
  TableCellData,
  TableWithResponsiveHeader,
} from "src/components/core/TableWithResponsiveHeader";
import AnnouncementsPagination from "./_components/AnnouncementsPagination";

type AnnouncementsAccessModel = {
  canView: boolean;
  canCreate: boolean;
  canUpdate: boolean;
};

type AnnouncementListPageStatus =
  "archived" | "closed" | "posted" | "forecasted" | "draft";

type AnnouncementListPageSummary = {
  close_timestamp: string | null;
  is_forecast: boolean;
  post_timestamp: string | null;
  archive_timestamp: string | null;
  funding_instruments: string[];
};

type AnnouncementListPageItem = {
  announcement_id: string;
  announcement_number: string | null;
  announcement_title: string | null;
  created_at: string;
  updated_at: string;
  forecast_summary: AnnouncementListPageSummary | null;
  non_forecast_summary: AnnouncementListPageSummary | null;
};

export const AnnouncementsPageWrapper = ({ children }: PropsWithChildren) => {
  const t = useTranslations("Announcements");
  return (
    <GridContainer>
      <h1 className="margin-top-9 margin-bottom-7">{t("pageTitle")}</h1>
      {children}
    </GridContainer>
  );
};

// --------------------------------------------------
// Components or this page
// --------------------------------------------------

const NoStartedAnnouncements = () => {
  const t = useTranslations("Announcements.noAnnouncementsMessage");
  return (
    <div className="margin-bottom-15">
      <div className="font-sans-xl text-bold margin-bottom-3">
        {t("primary")}
      </div>
      <div>{t("secondary")}</div>
    </div>
  );
};

const AnnouncementsErrorPage = () => {
  const t = useTranslations("Announcements");

  return (
    <AnnouncementsPageWrapper>
      <div className="margin-bottom-15">
        <Alert slim={true} headingLevel="h6" noIcon={true} type="error">
          {t("errorMessage")}
        </Alert>
      </div>
    </AnnouncementsPageWrapper>
  );
};

// TODO(#auth): Re-enable these authorization-specific page states when agency
// authorization is restored for this page.
//
// const AgencyNotAuthorizedPage = ({
//   agencies,
// }: {
//   agencies: RelevantAgencyRecord[];
// }) => {
//   const t = useTranslations("Announcements");
//   return (
//     <OpportunitiesPageWrapper>
//       <div className="margin-bottom-5">
//         <Alert slim={true} headingLevel="h6" noIcon={true} type="error">
//           {t("agencyNotAuthorized")}
//         </Alert>
//       </div>
//       <OpportunitiesHeader
//         userOpportunitiesCount={0}
//         agencyName={""}
//         agencies={agencies}
//         currentAgencyId={""}
//         isSingleAgency={false}
//         canCreate={false}
//       />
//     </OpportunitiesPageWrapper>
//   );
// };
//
// const AgencyNotAuthorizedMessage = () => {
//   const t = useTranslations("Announcements");
//   return (
//     <div className="margin-bottom-15">
//       <div className="font-sans-xl text-bold margin-bottom-3">
//         {t("agencyNotAuthorized")}
//       </div>
//     </div>
//   );
// };
//
// const NoAgenciesPage = () => {
//   const t = useTranslations("Announcements");
//
//   return (
//     <OpportunitiesPageWrapper>
//       <div className="margin-bottom-15">
//         <Alert slim={true} headingLevel="h6" noIcon={true} type="error">
//           {t("noAgencies")}
//         </Alert>
//       </div>
//     </OpportunitiesPageWrapper>
//   );
// };

const ActionMenu = ({
  canUpdate,
  announcementId,
  status,
}: {
  canUpdate: boolean;
  announcementId: string;
  status: string;
}) => {
  const t = useTranslations("Announcements");

  // Only show action menu for editable opportunities
  const isEditable =
    status.toLowerCase() === "draft" ||
    status.toLowerCase() === "forecasted" ||
    status.toLowerCase() === "posted";

  if (!isEditable || !canUpdate) {
    return null;
  }

  return (
    <PopoverMenu>
      <a
        href={`/announcement/${announcementId}/overview`}
        className="usa-button usa-button--unstyled width-full text-left padding-y-1 padding-x-2 hover:bg-base-lighter display-block text-no-underline"
      >
        {t("actionButtons.edit")}
      </a>
      {/* TODO: Add Copy and Delete actions in separate ticket */}
    </PopoverMenu>
  );
};

const transformTableRowData = (
  announcements: AnnouncementListPageItem[],
  canUpdate: boolean,
  _t: TFn,
) => {
  const getAnnouncementStatus = (
    summary: AnnouncementListPageSummary | null,
  ): AnnouncementListPageStatus => {
    if (!summary) {
      return "draft";
    }
    if (summary.is_forecast) {
      return "forecasted";
    }

    const now = Date.now();
    if (summary.archive_timestamp) {
      const archiveTime = new Date(summary.archive_timestamp).getTime();
      if (!Number.isNaN(archiveTime) && archiveTime <= now) {
        return "archived";
      }
    }

    if (summary.close_timestamp) {
      const closeTime = new Date(summary.close_timestamp).getTime();
      if (!Number.isNaN(closeTime) && closeTime <= now) {
        return "closed";
      }
    }

    return "posted";
  };

  return announcements.map((announcement: AnnouncementListPageItem) => {
    const summary =
      announcement.non_forecast_summary ?? announcement.forecast_summary;
    const status = getAnnouncementStatus(summary);
    const announcementTitleUrl =
      status === "draft" && canUpdate
        ? `/announcement/${announcement.announcement_id}/edit`
        : `/announcement/${announcement.announcement_id}`;

    // Get funding instrument types from summary and format them
    const fundingInstruments = summary?.funding_instruments || [];
    const formattedInstruments = fundingInstruments.map((instrument) =>
      instrument
        .split("_")
        .map(
          (word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase(),
        )
        .join(" "),
    );
    const announcementType =
      formattedInstruments.length > 0 ? formattedInstruments.join(", ") : "";

    // Format last updated date
    const lastUpdated = formatTimestamp(announcement.updated_at);

    return [
      {
        cellData: announcementTitleUrl ? (
          <a href={announcementTitleUrl}>{announcement.announcement_title}</a>
        ) : (
          <span>{announcement.announcement_title}</span>
        ),
      },
      { cellData: announcement.announcement_number },
      { cellData: announcementType },
      { cellData: lastUpdated },
      {
        cellData: <AnnouncementStatusTag status={status} />,
      },
      {
        cellData: (
          <ActionMenu
            canUpdate={canUpdate && status !== "draft"}
            announcementId={announcement.announcement_id}
            status={status}
          />
        ),
      },
    ];
  });
};

const AnnouncementsHeader = ({
  userAnnouncementsCount,
  canCreate,
}: {
  userAnnouncementsCount: number;
  canCreate: boolean;
}) => {
  const t = useTranslations("Announcements");

  return (
    <div className="display-flex flex-column gap-3 margin-bottom-4">
      <div className="font-sans-lg text-bold">
        {t("numAnnouncements", { num: userAnnouncementsCount })}
      </div>
      {canCreate && (
        <Link
          href="/announcements/create"
          className="usa-button margin-left-auto"
        >
          {t("createAnnouncementButton")}
        </Link>
      )}
    </div>
  );
};

// TODO(#auth): Restore the agency-aware header once agency selection and
// authorization are re-enabled.
//
// const OpportunitiesHeader = ({
//   userOpportunitiesCount,
//   agencyName,
//   agencies,
//   currentAgencyId,
//   isSingleAgency,
//   canCreate,
// }: {
//   userOpportunitiesCount: number;
//   agencyName: string;
//   agencies: RelevantAgencyRecord[];
//   currentAgencyId: string;
//   isSingleAgency: boolean;
//   canCreate: boolean;
// }) => {
//   const t = useTranslations("Announcements");
//   const showOpportunities = currentAgencyId !== "";
//
//   return (
//     <div className="display-flex flex-column gap-3 margin-bottom-4">
//       {showOpportunities && (
//         <div className="font-sans-lg text-bold">
//           {t("numAnnouncements", { num: userOpportunitiesCount })}
//         </div>
//       )}
//       <div className="display-flex flex-justify flex-align-end">
//         <div className="maxw-mobile-lg width-full">
//           {isSingleAgency ? (
//             <div className="font-sans-md text-bold line-height-sans-3">
//               {t("showingAnnouncementsFor", { agencyName })}
//             </div>
//           ) : (
//             <AgencySelector
//               agencies={agencies}
//               currentAgencyId={currentAgencyId}
//               className="usa-form-group margin-bottom-0"
//             />
//           )}
//         </div>
//         {canCreate && (
//           <Link
//             href={`/announcements/create?agency=${currentAgencyId}`}
//             className="usa-button margin-left-auto"
//           >
//             {t("createAnnouncementButton")}
//           </Link>
//         )}
//       </div>
//     </div>
//   );
// };

const AnnouncementsTable = ({
  announcements,
  canUpdate,
}: {
  announcements: AnnouncementListPageItem[];
  canUpdate: boolean;
}) => {
  const t = useTranslations("Announcements");

  const headerTitles: TableCellData[] = [
    { cellData: t("tableHeadings.title") },
    { cellData: t("tableHeadings.oppNumber") },
    { cellData: t("tableHeadings.fundingInstrumentType") },
    { cellData: t("tableHeadings.lastUpdated") },
    { cellData: t("tableHeadings.status") },
    { cellData: t("tableHeadings.actions") },
  ];

  return (
    <TableWithResponsiveHeader
      headerContent={headerTitles}
      tableRowData={transformTableRowData(announcements, canUpdate, t)}
    />
  );
};

// TODO(#auth): Re-enable agency-based authorization for this page.
// The code below is intentionally preserved as comments so we can restore
// authorization behavior without rebuilding it from scratch.
//
// import { AgencySelector } from "src/app/[locale]/announcements/_components/AgencySelector";
// import { getUserAgencies } from "src/services/fetch/fetchers/agenciesFetcher";
// import { RelevantAgencyRecord } from "src/types/search/searchFilterTypes";
// import {
//   checkRequiredPrivileges,
//   UserPrivilegeRequest,
//   UserPrivilegeResult,
// } from "src/utils/userPrivileges";
//
// type AgencyUserPrivileges = {
//   canView: boolean;
//   canCreate: boolean;
//   canUpdate: boolean;
// };
//
// const getUserPrivilegeDefinition = (
//   agencyId: string,
// ): UserPrivilegeRequest[] => {
//   return [
//     {
//       resourceId: agencyId,
//       resourceType: "agency",
//       privilege: "view_opportunity",
//     },
//     {
//       resourceId: agencyId,
//       resourceType: "agency",
//       privilege: "update_opportunity",
//     },
//     {
//       resourceId: agencyId,
//       resourceType: "agency",
//       privilege: "create_opportunity",
//     },
//   ];
// };
//
// const parseUserPrivileges = (
//   userPrivilegeResult: UserPrivilegeResult[],
// ): AgencyUserPrivileges => {
//   const agencyUserPrivileges: AgencyUserPrivileges = {
//     canView: false,
//     canCreate: false,
//     canUpdate: false,
//   };
//
//   if (userPrivilegeResult.length > 0) {
//     userPrivilegeResult.forEach((result) => {
//       if (result.privilege === "view_opportunity" && result.authorized) {
//         agencyUserPrivileges.canView = true;
//       } else if (
//         result.privilege === "update_opportunity" &&
//         result.authorized
//       ) {
//         agencyUserPrivileges.canUpdate = true;
//       } else if (
//         result.privilege === "create_opportunity" &&
//         result.authorized
//       ) {
//         agencyUserPrivileges.canCreate = true;
//       }
//     });
//   }
//
//   return agencyUserPrivileges;
// };

// TODO(#auth): Restore agency-scoped fetch when agency authorization returns.
//
// const fetchOpportunities = async (agencyId: string, page: number) => {
//   const pageRequest: PaginationRequestBody = {
//     page_offset: page,
//     page_size: 25,
//     sort_order: [
//       {
//         order_by: "created_at",
//         sort_direction: "descending",
//       },
//     ],
//   };
//
//   const json = await searchOpportunitiesByAgency(agencyId, pageRequest);
//   return {
//     opportunities: json.data,
//     totalRecords: json.pagination_info.total_records,
//     totalPages: json.pagination_info.total_pages,
//   };
// };

// --------------------------------------------------
// The Main Page
// --------------------------------------------------
type AnnouncementsListProps = LocalizedPageProps & WithFeatureFlagProps;
export default async function AnnouncementsListPage(
  props: AnnouncementsListProps,
) {
  const { searchParams } = props;
  const resolvedSearchParams: Record<string, string | string[] | undefined> =
    searchParams ? await searchParams : {};
  const parsedPage = Number(resolvedSearchParams.page);
  const currentPage = parsedPage > 0 ? parsedPage : 1;

  // TODO(#auth): Restore this agency-selection parsing when authorization is
  // re-enabled for this page.
  //
  // const selectedAgencyParam: string | string[] | undefined =
  //   resolvedSearchParams.agency;
  // const selectedAgencyId: string | undefined = Array.isArray(
  //   selectedAgencyParam,
  // )
  //   ? selectedAgencyParam[0]
  //   : selectedAgencyParam;

  // A. Check the user's session
  const userSession = await getSession();
  if (!userSession || !userSession.token) {
    return <TopLevelError />;
  }

  // TODO(#auth): Temporary page-local access model while authorization is disabled.
  // Re-enable checkRequiredPrivileges/getUserAgencies and replace this with the
  // computed per-agency authorization result.
  const announcementsAccess: AnnouncementsAccessModel = {
    canView: true,
    canCreate: true,
    canUpdate: true,
  };

  // TODO(#auth): Restore agency-based authorization flow after backend auth changes:
  // 1. Resolve selected agency from query param and user agencies.
  // 2. Evaluate privileges with checkRequiredPrivileges.
  // 3. Derive canView/canCreate/canUpdate from returned privileges.
  // 4. Re-enable unauthorized/no-agency page states.
  //
  // let userAgencies: RelevantAgencyRecord[];
  // try {
  //   userAgencies = await getUserAgencies(userSession.user_id);
  // } catch (error) {
  //   if (error instanceof MissingAuthError) {
  //     return <Unauthenticated />;
  //   }
  //   return <OpportunitiesErrorPage />;
  // }
  //
  // if (!userAgencies.length) {
  //   return <NoAgenciesPage />;
  // }
  //
  // const sortedUserAgencies = [...userAgencies].sort((a, b) =>
  //   a.agency_name.localeCompare(b.agency_name),
  // );
  //
  // if (!selectedAgencyId) {
  //   redirect(`?agency=${sortedUserAgencies[0].agency_id}`);
  // }
  //
  // const selectedAgency = sortedUserAgencies.find(
  //   (a) => a.agency_id.toString() === selectedAgencyId,
  // );
  //
  // if (!selectedAgency) {
  //   return <AgencyNotAuthorizedPage agencies={sortedUserAgencies} />;
  // }
  //
  // let userPrivilegeResult: UserPrivilegeResult[];
  // const userPrivilegeDef: UserPrivilegeRequest[] = getUserPrivilegeDefinition(
  //   selectedAgency.agency_id.toString(),
  // );
  //
  // try {
  //   userPrivilegeResult = await checkRequiredPrivileges(
  //     userSession.user_id,
  //     userPrivilegeDef,
  //   );
  // } catch (error) {
  //   console.error("Error fetching privileges", error);
  //   if (error instanceof UnauthorizedError) {
  //     throw error;
  //   }
  //   return <OpportunitiesErrorPage />;
  // }
  //
  // const agencyUserAcccess = parseUserPrivileges(userPrivilegeResult);

  let totalRecords = 0;
  let totalPages = 0;
  let announcements: AnnouncementListPageItem[] = [];
  try {
    const data = await fetchAnnouncements(currentPage);
    announcements = data.announcements;
    totalRecords = data.totalRecords;
    totalPages = data.totalPages;
  } catch (error) {
    console.error("Error fetching Announcements", error);
    if (error instanceof MissingAuthError) {
      return <Unauthenticated />;
    }
    if (error instanceof UnauthorizedError) {
      throw error;
    }
    return <AnnouncementsErrorPage />;
  }

  if (!announcements.length && totalPages > 0 && currentPage > totalPages) {
    redirect(`?page=${totalPages}`);
  }

  // C. Render the page
  return (
    <AnnouncementsPageWrapper>
      <AnnouncementsHeader
        userAnnouncementsCount={totalRecords}
        canCreate={announcementsAccess.canCreate}
      />

      {!announcements.length && <NoStartedAnnouncements />}

      {announcements.length > 0 && (
        <>
          <AnnouncementsTable
            announcements={announcements}
            canUpdate={announcementsAccess.canUpdate}
          />
          <AnnouncementsPagination totalPages={totalPages} />
        </>
      )}
    </AnnouncementsPageWrapper>
  );
}
