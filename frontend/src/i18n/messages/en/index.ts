export const messages = {
  Homepage: {
    title: "Smarter Grants Management",
    metaDescription:
      "Grant Smarter with Smarter Grants Management - Replace This Content TKTKTKTKTKTKTK",
  },
  OpportunityEdit: {
    pageTitle: "Edit opportunity",
    metaDescription:
      "Edit draft opportunity information and non-forecast summary fields.",
    navTitle: "On this page",
    button: {
      backToOverview: "Back to overview page",
      saveAndExit: "Save and exit",
      saveAndGoBack: "Save and go back",
      saveAndContinue: "Save and continue",
    },
    sections: {
      fundingDetails: "Funding details",
      eligibility: "Eligibility",
      additionalInformation: "Additional information",
      attachments: "Attachments",
    },
    labels: {
      fundingType: "Funding type",
      costSharing: "Cost sharing or matching requirements?",
      category: "Category",
      expectedNumberOfAwards: "Expected number of awards",
      estimatedTotalProgramFunding: "Estimated total program funding",
      awardMinimum: "Award minimum",
      awardMaximum: "Award maximum",
      publishDate: "Publish date",
      closeDate: "Close date",
      closeDateExplanation: "Close date explanation",
      eligibleApplicants: "Eligible applicants",
      additionalEligibilityInfo: "Additional information on eligibility",
      fundingCategoryExplanation: "Category explanation",
      description: "Description",
      additionalInfoUrl: "Link to additional information",
      additionalInfoUrlText: "Link display text",
      grantorContactDetails: "Grantor contact details",
      contactEmail: "Contact email",
      contactEmailText: "Email display text",
      yes: "Yes",
      no: "No",
      eligibilityBusiness: "Business",
      eligibilityEducation: "Education",
      eligibilityGovernment: "Government entities",
      eligibilityNonprofit: "Nonprofit",
      eligibilityMiscellaneous: "Miscellaneous",
    },
    content: {
      fundingDetailsIntro:
        "Provide the financial structure of this opportunity. This includes the total funding available, expected number of awards, and critical dates for the application window.",
      eligibilityIntro:
        "Define who is eligible to apply for these funds. Select all applicable applicant types and provide any specific requirements or restrictions regarding organizational status or geographic location.",
      additionalInformationIntro:
        "Use this section to provide supplementary context, such as a summary of the program's goals, agency-specific links, and contact information for programmatic or technical inquiries.",
      notAvailable: "Not available",
      fundingTypeHint:
        "Select the legal relationship between the agency and the recipient",
      costSharingHint:
        "Indicate if the applicant is required to provide a specific percentage of non-federal funds.",
      categoryHint: "Choose the primary functional area this funding supports",
      fundingCategoryExplanationHint: "If category is Other",
      expectedNumberOfAwardsHint:
        "Enter the estimated number of individual awards the agency intends to fund.",
      estimatedTotalProgramFundingHint:
        "Enter the total amount of funding available for all awards under this opportunity.",
      awardMinimumHint:
        "Enter the smallest dollar amount that can be awarded to a single recipient.",
      awardMaximumHint:
        "Enter the largest dollar amount that can be awarded to a single recipient.",
      publishDateHint:
        "The date this opportunity will be visible to the public",
      closeDateHint: "The final deadline for all applications to be submitted",
      closeDateExplanationHint:
        "Provide a reason if a specific close date is not set, such as continuous review or a rolling deadline.",
      select: "Select",
      selectFundingCategory: "Select funding category",
      eligibleApplicantsHint:
        "Select all categories of organizations or individuals that may apply for this grant.",
      additionalEligibilityInfoHint:
        "If eligible applicant is Other, provide further clarification on specific requirements",
      descriptionHint:
        "Provide a high-level summary of the funding purpose and the problems it intends to solve.",
      additionalInfoUrlHint:
        "Enter the full web address for more program details.",
      additionalInfoUrlTextHint:
        "Enter the text that will appear as the clickable link.",
      grantorContactDetailsHint:
        "Provide the name or department and phone number for the primary contact.",
      contactEmailHint: "Enter a valid email address.",
      contactEmailTextHint:
        "Enter the text that will be shown as the email link.",
      attachmentsIntro:
        "Upload the official Notice of Funding Opportunity (NOFO) and any supporting templates or guidelines that applicants need to complete their submission.",
      alerts: {
        success: "Saved successfully",
        successBody: "Your changes have been saved.",
        genericError: "Unable to save draft opportunity details.",
        missingSummaryContext: "Missing opportunity summary context for save.",
        unauthenticated: "You must be signed in to update this opportunity.",
        forbidden: "You do not have permission to update this opportunity.",
        notFound: "The opportunity summary could not be found.",
        draftOnly: "Only draft opportunity summaries can be updated.",
        validationErrorHeading: "Error(s) Found",
        validationErrorBody: "Please correct the following errors:",
      },
    },
    validationErrors: {
      title: "Enter a title.",
      awardSelectionMethod: "Select an award selection method.",
      description: "Enter a description.",
      publishDate: "Enter a publish date.",
      closeDate: "Enter a close date.",
      contactEmailRequired: "Enter a contact email.",
      contactEmailInvalid: "Enter a valid contact email.",
      contactEmailText: "Enter email display text.",
      closeDateOrder: "Close date must be on or after publish date.",
      awardMinimum: "Enter an award minimum.",
      awardMaximum: "Enter an award maximum.",
      fundingType: "Select a funding type.",
      fundingCategory: "Select a funding category.",
      expectedNumberOfAwards: "Enter the expected number of awards.",
      estimatedTotalProgramFunding:
        "Enter the estimated total program funding.",
      eligibleApplicants: "Select at least one eligible applicant type.",
      additionalEligibilityInfo: "Enter additional eligibility information.",
      additionalInfoUrl: "Enter an additional information URL.",
      additionalInfoUrlText: "Enter additional information URL text.",
      grantorContactDetails: "Enter grantor contact details.",
      expectedNumberOfAwardsInput:
        "Expected number of awards must be greater than or equal to zero and less than 1,000,000,000,000,000.",
      awardMinCurrencyInput:
        "Award minimum must be greater than or equal to zero and less than $1,000,000,000,000,000.",
      awardMaxCurrencyInput:
        "Award maximum must be greater than or equal to zero and less than $1,000,000,000,000,000.",
      totalFundingCurrencyInput:
        "Estimated total program funding must be greater than or equal to zero and less than $1,000,000,000,000,000.",
      awardMinLessThanTotal:
        "Award minimum cannot exceed the Estimated Total Program Funding.",
      awardMaxLessThanTotal:
        "Award maximum cannot exceed the Estimated Total Program Funding.",
      awardMinLessThanMax: "Award minimum cannot exceed Award maximum.",
      awardMaxGreaterThanMin:
        "Award maximum cannot be less than Award minimum.",
    },
    attachments: {
      uploadLabel: "Upload files",
      uploading: "Uploading...",
      success:
        "Success: File scan complete. Save this form to attach the file.",
      error:
        "Processing failed due to a system error. Try uploading your file again.",
    },
  },
  ErrorPages: {
    genericError: {
      pageTitle: "Error | Simpler.Grants.gov",
    },
    unauthorized: {
      pageTitle: "Unauthorized | Simpler.Grants.gov",
    },
    unauthenticated: {
      pageTitle: "Unauthenticated | Simpler.Grants.gov",
    },
    pageNotFound: {
      pageTitle: "Page Not Found | Simpler.Grants.gov",
      title: "Oops, we can't find that page.",
      messageContent: "It may have been moved or no longer exists.",
      visitHomepageButton: "Visit our homepage",
    },
  },
  Header: {
    navLinks: {
      home: "Home",
      login: "Sign in",
      logout: "Sign out",
      menuToggle: "Menu",
      opportunities: "Opportunities",
      settings: "Settings",
      notifications: "Notifications",
      testApplication: "Test application",
    },
    title: "Simpler.Grants.gov",
    tokenExpired: "You've been logged out. Please sign in again.",
  },
  HeaderLoginModal: {
    title: "Sign in to Simpler.Grants.gov",
    help: "Simpler.Grants.gov uses Login.gov to verify your identity and manage your account securely. You don't need a separate username or password for this site.",
    description:
      "You'll be redirected to Login.gov to sign in or create an account. Then, you'll return to Simpler.Grants.gov as a signed-in user.",
    button: "Sign in with Login.gov",
    close: "Cancel",
  },
  PivRequiredModal: {
    title: "Your account requires additional identity verification.",
    description:
      "You must sign in with your government employee ID. Make sure you've set up your Personal Identity Verification (PIV) or Common Access Card (CAC) as a two-factor authentication method.",
    button: "Sign in using PIV/CAC",
  },
  FormSelectModal: {
    title: "Form Library",
    heading: "Select Forms",
    selectAll: "Select all",
    buttons: {
      cancel: "Cancel",
      save: "Save",
    },
    requiredStates: {
      required: "Required",
      conditional: "Conditionally Required",
      auto: "Auto added",
      always: "Always required",
    },
  },
  Footer: {
    agencyName: "Grants.gov",
    agencyContactCenter: "Grants.gov Program Management Office",
    telephone: "1-800-518-4726",
    returnToTop: "Return to top",
    logoAlt: "Grants.gov logo",
    explore: "Explore",
    siteName: "Smarter Grants Management",
    links: {
      home: "Home",
      search: "Search",
      vision: "Vision",
      roadmap: "Roadmap",
      events: "Events",
      newsletter: "Newsletter",
      subscribe: "Subscribe",
    },
    feedback: "To give feedback, contact: <email>simpler@grants.gov</email>",
    supportCenter: "Grants.gov Support Center",
    techSupport:
      "For technical support, contact: <email>support@grants.gov</email>",
    grantorSupport:
      "Grantors, contact the PMO through your <poc>Agency Point of Contact</poc>.",
  },
  Identifier: {
    identity:
      "An official website of the <hhsLink>U.S. Department of Health and Human Services</hhsLink>",
    govContent:
      "Looking for U.S. government information and services? Visit <usaLink>USA.gov</usaLink>",
    linkAbout: "About HHS",
    linkAccessibility: "Accessibility support",
    linkFoia: "FOIA requests",
    linkFear: "EEO/No Fear Act",
    linkIg: "Office of the Inspector General",
    linkPerformance: "Performance reports",
    linkPrivacy: "Privacy Policy",
    logoAlt: "HHS logo",
  },
  Layout: {
    skipToMain: "Skip to main content",
  },
  Errors: {
    heading: "We're sorry.",
    genericMessage: "There seems to have been an error.",
    tryAgain: "Please try again.",
    unauthorized: "Unauthorized",
    unauthenticated: "Not signed in",
    authorizationFail:
      "Sign in or user authorization failed. Please try again.",
    signInCTA: "Sign in first in order to view this page",
    unauthorizedExplanation: "This content is not available",
  },
  CommonWordLimit: {
    wordsAllowed: "words allowed",
    wordsLeft: "{num, plural, =1 {1 word left} other {# words left}}",
    wordsError:
      "{num, plural, =1 {1 word over limit} other {# words over limit}}",
  },
  Maintenance: {
    heading: "Simpler.Grants.gov Is Currently Undergoing Maintenance",
    body: "Our team is working to improve the site, and we'll have it back up as soon as possible.",
    signOff: "Thank you for your patience.",
    pageTitle: "Simpler.Grants.gov - Maintenance",
  },
  Opportunities: {
    createOpportunityButton: "Create Opportunity",
    numOpportunities:
      "{num, plural, =1 {1 opportunity} other {# opportunities}}",
    errorMessage:
      "We have encountered an error loading your opportunities, please try again later.",
    metaDescription: "View draft and published funding opportunities",
    noOpportunitiesMessage: {
      primary: "You have not started any opportunities yet.",
      secondary:
        "Opportunities you start or work on will be saved here.  Return anytime to view, continue, or manage them.",
    },
    showingOpportunitiesFor: "Showing opportunities for {agencyName}",
    agencySelector: "Select agency",
    agencyNotAuthorized:
      "You do not have access to this agency's opportunities.",
    noAgencies: "You are not associated with any agencies.",
    pageHeading: "Opportunities",
    pageTitle: "Opportunities List",
    pageApplication: "Smarter Grants Management",
    tableContents: {
      agency: "Agency: ",
      draft: "Draft",
      individual: "Individual",
      submitted: "Submitted",
    },
    tableHeadings: {
      agency: "Agency",
      title: "Title",
      status: "Status",
      actions: "Action",
      oppNumber: "Opp. Number",
      fundingInstrumentType: "Funding Instrument Type",
      lastUpdated: "Last Updated",
    },
    actionButtons: {
      edit: "Edit",
      copy: "Copy",
      delete: "Delete",
    },
    statusTag: {
      draft: "Draft",
      posted: "Open",
      forecasted: "Forecasted",
      archived: "Archived",
      closed: "Closed",
    },
  },
  Organizations: {
    errorMessage:
      "We have encountered an error loading your organizations, please try again later.",
    manageUsers: "Manage Users",
    metaDescription: "View your organizations",
    pageHeading: "Organizations",
    pageTitle: "Organizations",
    breadcrumbWorkspace: "Workspace",
    breadcrumbOrganizations: "Organizations",
  },
  AwardRecommendation: {
    list: {
      pageTitle: "Award recommendations",
      pageHeading: "Award recommendations",
      numAwardRecommendations:
        "{num, plural, =1 {1 Award recommendation} other {# Award recommendations}}",
      createRecommendationButton: "Create recommendation",
      agencyNotAuthorized:
        "You do not have access to this agency's award recommendations.",
      noAgencies: "You are not associated with any agencies.",
      empty: "No award recommendations found.",
      fetchError:
        "We have encountered an error loading award recommendations. Please try again.",
      columns: {
        awardRecId: "Award Rec ID",
        opportunityName: "Opportunity name",
        opportunityId: "Opportunity ID",
        applicationsReceived: "Applications received",
        status: "Status",
        action: "Action",
      },
      actions: {
        delete: "Delete",
      },
    },
    summary: {
      showDescription: "Show full description",
      hideSummaryDescription: "Hide full description",
    },
    awardRecs: "Award Recs",
    errorMessage:
      "We have encountered an error loading your award recommendations, please try again later.",
    metaDescription: "View your award recommendations",
    metaDescriptionEdit: "Edit your award recommendations",
    pageTitleEditApplicationSubmissionDetails:
      "Edit application submission details",
    pageHeading: "Award Recommendations",
    heroTitle: "Award Rec #",
    createHeroTitle: "Create recommendation",
    datePrepared: "Date prepared",
    status: "Status",
    onThisPage: "On this page",
    statusTag: {
      draft: "In Progress",
      in_review: "Pending Review",
      approved: "Approved",
    },
    heroButtons: {
      save: "Save",
      cancel: "Cancel",
      create: "Create",
      edit: "Edit",
      preview: "Preview",
      submitForReview: "Submit for review",
      backToEdit: "Back to Edit",
      backToSubmissions: "Back to submissions",
    },
    save: {
      success: "Your changes have been saved.",
      error: "We encountered an error saving your changes. Please try again.",
    },
    submissionEdit: {
      editTitle: "Edit {applicationSubmissionNumber}",
      viewOriginalApplication: "View original application",
    },
    editRecommendations: {
      pageTitle: "Edit recommendations",
      metaDescription: "Edit award recommendations for multiple applications",
      heading: "Edit recommendations",
      pageHeading: "Recommend awards",
      pageDescription:
        "Select one or more applications to edit recommendations. Search by App #, program title, org name of UEI",
      selectAll: "Select all",
      selectRow: "Select row for {appNumber}",
      selectedCount:
        "{count, plural, =1 {1 submission selected} other {# submissions selected}}",
      showingRange: "Showing {start}-{end} of {total}",
      loading: "Loading...",
      errorLoading: "Error loading submissions. Please try again.",
      editButton: "Edit",
      bulkEditPageTitle: "Bulk Edit Recommendations",
      bulkEditMetaDescription:
        "Bulk edit award recommendations for selected applications",
      bulkEditTitle: "Bulk Edit Recommendations",
      selectedApplications: "Selected Applications",
      submissionsSelected: "submissions selected",
      bulkEditHeading: "Update Recommendation",
      bulkEditDescription:
        "Select a recommendation type to apply to all selected applications.",
      recommendationType: "Recommendation Type",
      noSelectionsMessage:
        "No submissions selected. Please select submissions to edit.",
      saveButton: "Save",
      saving: "Saving...",
      cancelButton: "Cancel",
      columns: {
        appNumber: "App #",
        projectTitle: "Project Title",
        orgName: "Org Name",
        uei: "UEI",
        score: "Score",
        recommendation: "Recommendation",
        requested: "Requested",
        recommended: "Recommended",
      },
    },
    pageTitle: "Review your Recommendation",
    pageTitleEdit: "Edit your recommendation",
    description: "Award Recommendation flow coming soon.",
    opportunitySummary: "Opportunity summary",
    selectionMethod: "Selection method",
    meritReview: "Merit Review",
    fundingOpportunityFallback: "Funding Opportunity",
    noDataFallback: "--",
    fundingOppName: "Funding opportunity name",
    fundingOppNumber: "Funding opportunity number",
    noSummaryAvailable: "No summary available",
    otherOpportunityInfo: {
      label: "Other opportunity information",
      description:
        "Any any additional context or information specific to the opportunity that the decision maker may need to know, or leave blank.",
      characterLimit: "1000 characters allowed",
    },
    viewFullDetails: "View Full Details",
    opportunityStatus: "Status",
    agency: "Agency",
    closeDate: "Closing Date",
    readMore: "Read more",
    showLess: "Show less",
    opportunity: "Opportunity",
    editOpportunityDetails: "Edit opportunity details",
    recommendationMethod: {
      label: "Recommendation method",
      description: "Choose the method you'll use to rate",
      meritReviewOnly: "Merit review ranking only",
      meritReviewOther: "Merit review ranking with other factors",
    },
    recommendationMethodDetails: {
      label: "Recommendation method details",
      description:
        "Add any additional information - including the selection factors used in the NOFO",
    },
    otherKeyInformation: {
      label: "Other key information",
      description:
        "Add any relevant information related to this reviewer and decision-maker for this opportunity",
    },
    attachments: {
      heading: "Attachments",
      attachedDocument: "Attached document",
      uploadedBy: "Uploaded by",
      uploadDate: "Upload date",
      standardTermsHeading: "Standard and program terms & conditions",
      enterTermsConditions: "Enter terms & conditions",
      editTermsConditions: "Edit terms & conditions",
      risksHeading: "Specific risks & recommended conditions",
      enterRisks: "Enter risks & recommended conditions",
      editRisks: "Edit risks & recommended conditions",
      riskNumber: "Risk #",
      appNumber: "App #",
      condition: "Condition",
      action: "Action",
      delete: "Delete",
      applications: "applications",
      errorMessage: "Unable to load or update risks. Please try again.",
      otherDocumentsHeading: "Other supporting documents",
      enterSupportingDocuments: "Enter supporting documents",
      editSupportingDocuments: "Edit supporting documents",
    },
    recommendationDetails: {
      heading: "Recommendation details",
      recommendationLabel: "Recommendation",
      recommendationOptions: {
        recommended: "Recommended",
        recommendedWithoutFunding: "Recommended but not funded",
        notRecommended: "Not recommended",
      },
      selectOnePlaceholder: "Select one",
      hasExceptionLabel: "Contains exceptions to selection method",
      commentsLabel: "Recommendation comments",
      commentsDescription:
        "Add any needed context for your recommendations for any selected group or single application.",
      exceptionDetailLabel: "Exceptions to selection method",
      exceptionDetailDescription:
        "Select one or more applications and explain any exceptions to the general selection method. For example, the reasons for any applications skipped on the merit review ranking or other similar exceptions.",
      fundingHeading: "Funding recommendations",
      fundingDescription:
        "Review and provide the updates to recommended funding as needed.",
      applicationIdLabel: "Application ID",
      amountRequestedLabel: "Amount Requested",
      amountRecommendedLabel: "Amount Recommended",
      totalLabel: "Total",
      validationErrorHeading: "There is a problem with your recommendation",
      recommendationRequired: "Select your recommendation",
      exceptionDetailRequired: "Enter a reason for this exception",
      amountRecommendedRequired: "Enter an amount recommended",
    },
    errorHeadingAwardRecommendation:
      "Error fetching award recommendation details",
    errorHeadingAuthentication: "Authentication Error",
    authenticationError:
      "You are not authenticated. Please sign in to view award recommendations.",
    awardRecommendationFetchError:
      "Error fetching award recommendation data. Please try refreshing the page.",
    awardRecommendationNotFound:
      "Award recommendation not found. Please check the ID and try again.",
    errorHeadingAwardRecommendationSubmission:
      "Error fetching application submission details",
    awardRecommendationSubmissionFetchError:
      "Error fetching application submission data. Please try refreshing the page.",
    errorHeadingAwardRecommendationRisk: "Error fetching risk details",
    awardRecommendationRiskFetchError:
      "Error fetching risk data. Please try refreshing the page.",
    recommendations: {
      heading: "Recommendations",
      editPageDescription:
        "Document your award recommendations and the funding strategy used for the period of performance.",
      description:
        "Award recommendations and the funding strategy used for the period of performance.",
      summary: {
        heading: "Summary",
        appsReceived: "Apps received",
        appsRecommended: "Apps recommended",
        totalFundingRecommended: "Total funding recommended",
        totalAvailable: "Total available",
        recommendedWithoutFunding: "Recommended without funding",
        notRecommendedForFunding: "Not recommended for funding",
        applications: "applications",
      },
      fundingStrategy: {
        heading: "Funding strategy",
        description:
          "Explain how you plan to provide funding over time. For example, will the agency award all funding in a single award or in multiple budget periods across a longer period of performance.",
        noFundingStrategyProvided: "No funding strategy provided.",
        showDescription: "Show full description",
        hideSummaryDescription: "Hide full description",
      },
      submissions: {
        errorMessage:
          "Unable to load application submissions. Please try again.",
        columns: {
          appNumber: "App #",
          projectTitle: "Project title",
          orgName: "Org name",
          uei: "UEI",
          score: "Score",
          recommendation: "Recommendation",
          requested: "Requested",
          recommended: "Recommended",
        },
        recommendationOptions: {
          none: "None",
          recommended: "Recommended",
          recommendedWithoutFunding: "Recommended but not funded",
          notRecommended: "Not recommended",
        },
        recommendedAwards: {
          heading: "Recommended awards",
          editDescription:
            "Select applications and use the drop-down box to apply your recommendation for the selected group.",
          editLink: "Edit recommended awards",
        },
        exceptions: {
          heading: "Exceptions to selection method",
        },
      },
    },
    risks: {
      pageTitle: "Risks and Conditions",
      metaDescription: "Manage risks and conditions for award recommendations",
      heading: "Risks and Conditions",
      description:
        "Review and manage risks and conditions for application submissions",
      pageHeading: "Recommend submissions",
      pageDescription: "Select one or more applications to add conditions.",
      editTitle: "Edit risks and conditions",
      editPageTitle: "Edit Risk or Condition",
      editMetaDescription: "Edit risk or condition for selected applications",
      editRiskTitle: "Edit {riskNumber}",
      addPageTitle: "Add Risk or Condition",
      addMetaDescription: "Add risk or condition to selected applications",
      addTitle: "Add risk or condition",
      addHeading: "Add risk or condition",
      addDescription:
        "Add risk details and recommended terms or conditions for the selected applications",
      selectAll: "Select all",
      selectRow: "Select row for {appNumber}",
      selectedCount:
        "{count, plural, =1 {1 submission selected} other {# submissions selected}}",
      selectedApplications: "Selected applications",
      columns: {
        appNumber: "App #",
        projectTitle: "Project Title",
        orgName: "Org Name",
        uei: "UEI",
        score: "Score",
        recommendation: "Recommendation",
        requested: "Requested",
        recommended: "Recommended",
        risk: "Risk",
        condition: "Condition",
      },
      recommendationType: {
        recommended_for_funding: "Recommended",
      },
      riskDetailsHeading: "Risk details",
      riskSummaryLabel: "Risk summary",
      riskSummaryHint:
        "Any program or organization risks already identified at this time",
      riskSummaryRequired: "Risk summary is required.",
      recommendedConditionLabel: "Recommended term or condition",
      recommendedConditionHint:
        "Add any recommended conditions based on the risks identified",
      selectConditionPlaceholder: "Select a condition",
      condition1: "Condition 1",
      condition2: "Condition 2",
      condition3: "Condition 3",
      cancelButton: "Cancel",
      saveButton: "Save",
      savingButton: "Saving...",
      validationError: "Please fill in all required fields before saving.",
      saveError: "Failed to save risk. Please try again.",
      errorMessage: "Unable to load application submissions. Please try again.",
      noSelectionsMessage:
        "No applications selected. Please select applications from the Risks and Conditions page first.",
      defaultNone: "None",
      loading: "Loading submissions...",
      errorLoading: "Error loading submissions. Please try again.",
      showingRange: "Showing {start}-{end} of {total}",
      editButton: "Edit",
    },
    reviewForm: {
      pageTitle: "Submit for Review | Simpler.Grants.gov",
      pageDescription: "Submit award recommendation for review",
      header: "Submit for Review",
      loading: "Loading...",
      contentCreator: {
        title: "Submit for Review",
      },
      reviewer: {
        title: "Review Award Recommendation",
        question:
          "Do you concur on behalf of the Grants Office that this document meets applicable grants management requirements?",
        yesConcur: "Yes, approval obtained (attachment required)",
        noIssues: "No, issues identified, changes needed (attachment required)",
        hold: "Hold, review in progress",
      },
      fmo: {
        title: "FMO Review",
        question:
          "Do you certify the availability of funds to support the recommendation documented in this document?",
        fundsAvailable: "Yes, funds are available",
        fundsContingent: "Yes, funds are contingent upon availability by",
        dateLabel: "Date",
        noCertification: "No, certification cannot be provided, changes needed",
        hold: "Hold, review in progress",
      },
      reviewComment: {
        label: "Review comments",
        description: "Shown on the award recommendation document",
      },
      internalComment: {
        checkboxLabel: "Add internal comments for your team",
        label: "Internal comments",
        description: "Only visible in workflow history",
      },
      supplementalDocuments: {
        label: "Supplemental review documents",
        description: "Choose the documents you'd like to include",
        uploading: "Uploading document...",
        uploadSuccess: "Document uploaded successfully",
        uploadError: "Error uploading document. Please try again.",
      },
      attestation: {
        contentCreator:
          "I attest that I am providing my recommendation of the recipients identified in this document for award consideration",
        reviewer:
          "I attest that I am providing my approval of the recipients identified in this document for award consideration",
      },
      buttons: {
        submit: "Submit review",
        submitting: "Submitting...",
        cancel: "Cancel",
      },
      errors: {
        submitFailed: "Failed to submit review. Please try again.",
        insufficientPrivileges:
          "You do not have the required privileges to review award recommendations.",
        invalidReviewerType:
          "You do not have permission to review at this stage of the workflow.",
        authFailed:
          "Failed to authenticate user. Please sign in and try again.",
        loadingFailed: "Failed to load review form. Please try again.",
        noWorkflow: "No workflow is associated with this award recommendation.",
      },
    },
  },
  CreateAwardRecommendation: {
    pageTitle: "Create recommendation",
    metaDescription: "Create a new award recommendation",
    beforeYouGetStarted: "Before you get started",
    steps: {
      identifyOpportunity: {
        title: "Identify the opportunity",
        description:
          "Identify which funding opportunity is this recommendation is for and provide any additional context including an overview of the program and any legislative requirements the decision maker may need to know.",
      },
      applyRecommendations: {
        title: "Apply your recommendations",
        description:
          "Apply your recommendations to all applications submitted for this opportunity.",
        bullet1: "Explain how you plan to provide funding over time.",
        bullet2:
          "Add any needed context for your recommendations for any selected group or single applications.",
        bullet3:
          "Identify and document any exceptions to you recommendation method.",
      },
      provideAttachments: {
        title: "Provide any attachments",
        description:
          "Include any supplemental documentation to support and inform your recommendations.",
        bullet1: "Standard and Program terms & conditions",
        bullet2: "Specific risks & recommended conditions",
        bullet3: "Other supporting documents",
      },
    },
    buttons: {
      cancel: "Cancel",
      next: "Next",
    },
  },
  OpportunityOverview: {
    pageTitle: "Opportunity Overview",
    pageApplication: "Smarter Grants Management",
    metaDescription: "Opportunity publishing progress overview",
    labels: {
      editOpportunityLink: "Opportunity Summary",
      competitionLink: "Application Package",
      previewButton: "Preview",
      publishButton: "Publish",
    },
  },
  CreateOpportunity: {
    pageTitle: "Create Opportunity",
    pageApplication: "Smarter Grants Management",
    metaDescription: "Create a new funding opportunity",
    errorMessage:
      "We have encountered an error loading this page, please try again later.",
    keyInfo: "Key information",
    basicInstructions:
      "Fill out the basic details below to begin. Once you save this information, a draft will be created, allowing you to return at any time to add more details, upload documents, and finalize your opportunity.",
    cancel: "Cancel",
    saveAndContinue: "Save and continue",
    pending: "Pending...",
    errorHeading: "Error",
    successHeading: "Success",
    CreateOpportunityForm: {
      opportunityNumber: "Opportunity number",
      opportunityNumberDesc:
        "Enter the unique ID assigned to this funding opportunity.",
      opportunityTitle: "Opportunity title",
      opportunityTitleDesc:
        "Provide a concise, descriptive name that helps applicants identify the grant's purpose.",
      tagline: "Tagline",
      taglineDesc:
        "A specific one-sentence purpose statement that summarizes the highest-level goal.",
      purposeStatement: "Purpose statement",
      purposeStatementDesc:
        "Provide a one-line statement that helps applicants understand the grant's purpose.",
      agency: "Agency",
      category: "Grant selection method",
      categoryDesc: "Choose the evaluation process used to award these funds.",
      categoryExplanation: "Grant selection method explanation",
      categoryExplanationDesc:
        'If "Other" was selected, please describe the specific process used to evaluate and award these funds.',
      assistanceListingNumber: "Assistance listing number",
      assistanceListingNumberDesc:
        "Enter the 5-digit code from SAM.gov that identifies the specific federal assistance program (e.g., 10.500)",
      successMessage: "Opportunity started. Continuing shortly...",
    },
  },
  OpportunityCompetition: {
    pageTitle: "Competition",
    metaDescription: "Set up competition details for this opportunity.",
    leftNavTitle: "On this page",
    applicationRequirements: "Application requirements",
    applicationRequirementsSubheader:
      "What applicants must submit, how they'll be scored, and the format rules.",
    button: {
      processing: "Processing...",
      back: "Save and go back",
      saveAndExit: "Save and exit",
      saveAndContinue: "Save and continue",
    },
    alerts: {
      success: "Saved successfully",
      successBody: "Your changes have been saved.",
      genericError: "Unable to save competition updates.",
      unauthenticated: "You must be signed in to update this competition.",
      forbidden: "You do not have permission to update this competition.",
      notFound: "This competition could not be found.",
      networkError: "A network error occurred.",
      validationErrors: "Errors Found",
      validationErrorBody: "Please correct the following errors:",
    },
    sectionSubmissionSetUp: {
      header: "Submission set-up",
      subHeader:
        "A competition is one apply-window inside an opportunity. Most opportunities have only one.",
      publicCompetitionId: "Competition ID",
      publicCompetitionIdHint:
        "An ID if this opportunity has multiple competitions.",
      competitionTitle: "Competition title",
      competitionTitleHint: "Shown to applicants. Plain language is best.",
      whoCanApply: "Who can apply?",
      whoCanApplyHint:
        "Applicants who don't match this type won't see the competition in search.",
      whoCanApplyOrganizationsOnly: "Organizations only",
      whoCanApplyIndividualsOnly: "Individuals only",
      whoCanApplyBoth: "Both organizations and individuals",
    },
    sectionSubmissionWindow: {
      header: "Submission window",
      subHeader: "When applicants can submit through this package.",
      submissionsOpen: "Open date",
      submissionsOpenHint: "First day applicants can apply",
      submissionsClose: "Public close date",
      submissionsCloseHint: "Deadline listed on Grants.gov",
      gracePeriod: "Extension period",
      gracePeriodHint: "Number of days accepted past public close date",
    },
    sectionApplicationChecklist: {
      header: "Application checklist",
    },
    sectionNarrativeFormatInstructions: {
      header: "Narrative format instructions",
    },
    sectionAgencyContact: {
      header: "Agency contact",
      subHeader:
        "Grantor contact details. Provide the name, email, and phone number for the agency contact.",
      fullName: "Full name",
      personTitle: "Title",
      emailAddress: "Email address",
      emailAddressHint: "For example: example@mail.com",
      phoneNumber: "Phone number",
      phoneNumberHint: "10-digit, for example: (999) 999-9999",
      error: {
        requiredFullName: "Full name is required.",
        requiredPhoneNumber: "Phone number is required.",
        requiredEmail: "Email address is required.",
        invalidEmail:
          "Incorrect text format. Please ensure there are no spaces or missing characters.",
      },
    },
    sectionRequiredForms: {
      header: "Forms in this package",
      subHeader: "Select the forms applicants must complete.",
      selectFormsButton: "Select forms",
      labelForm: "Item",
      labelRequirement: "Requirement",
    },
    sectionApplicationInstructions: {
      header: "Application instructions",
      subHeader:
        "Upload any supporting instructions needed for the application.",
      uploadAFile: "Upload a file",
      multipleFiles: "For multiple files, combine them into one zip file.",
      uploadWidget: {
        error:
          "Processing failed due to a system error. Try uploading your file again.",
        success:
          "Success: File scan complete. “Save” this form to attach the file.",
        uploading: "Uploading...",
      },
    },
  },
  FeatureFlagsAdmin: {
    heading: "Refresh your page",
    alertMessage:
      "Hard refresh your page when done changing Flags for the changes to fully apply.",
  },
  OpportunityDetailsHeader: {
    opportunityNumber: "Opportunity #: {number}",
    title: "Title:",
    agency: "Agency:",
    subAgency: "Sub-agency:",
    draft: "Draft",
    lastUpdated: "Last updated:",
    backToOverview: "Back to overview page",
    alerts: {
      newOpportunityHeading: "Opportunity draft started",
      newOpportunityBody:
        "Your initial information has been saved. Complete the sections below to finish your opportunity details",
    },
  },
  AwardRecommendationSelectFundingOpportunity: {
    pageTitle: "Select funding opportunity | Simpler.Grants.gov",
    pageHeading: "Award Recommendations",
    metaDescription:
      "Select a funding opportunity for your award recommendation",
    whichFundingOpportunity: "Which funding opportunity is this for?",
    cancelButtonText: "Cancel",
    startButtonText: "Start",
    columns: {
      fundingOpportunityNumber: "Funding opp #",
      fundingOpportunityName: "Funding opp name",
      submittedApplications: "Submitted applications",
      action: "Action",
    },
  },
  FileInput: {
    existingFiles: {
      savedOn: "Saved on",
      delete: "Delete",
      deleteError: "File could not be deleted. Please try again.",
    },
    statusDisplay: {
      cancel: "Cancel",
      dismiss: "Dismiss",
      processing: "Processing file",
      starting: "Starting upload",
      uploading: "Uploading...",
      startingScan: "Upload complete. Starting security scan",
      scanning: "Upload complete. Running security scan...",
      scanComplete: "Scan complete",
      success: "Success. File uploaded and scanned",
      error: "Error",
      uploadError: "Upload failed",
      scanError: "Error running security scan",
      postUploadError: "Error processing file",
      missingFileId: "Error: missing file id",
      preUploadError: "Pre upload error",
      infected: "Security scan failed. File removed",
      fileTooLarge:
        "This file is too large. The maximum file size is {maxFileSize}.",
    },
    deleteModal: {
      titleText: "Delete",
      cancelDeleteCta: "Cancel",
      cautionDeletingAttachment: "Caution, deleting attachment",
      descriptionText:
        "You may have uploaded this attachment in response to a form question. Check to ensure you no longer need it.",
      deleteFileCta: "Delete file",
      deleteFilesCta: "Delete files",
      deleting: "Deleting...",
    },
  },
  ProgressChecker: {
    notStarted: "Not started",
    inProgress: "In progress",
    complete: "Complete",
  },
};
