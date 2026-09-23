import { type Page, type TestInfo } from "@playwright/test";

export const summarizeNetworkEvents = (entries: string[]): string => {
  if (!entries.length) {
    return "No network events captured.";
  }

  return entries.slice(-50).join("\n");
};

export const createPageNetworkTracker = (page: Page) => {
  const events: string[] = [];

  const onRequest = (request: { method: () => string; url: () => string }) => {
    events.push(`[request] ${request.method()} ${request.url()}`);
  };

  const onResponse = (response: {
    status: () => number;
    url: () => string;
  }) => {
    events.push(`[response] ${response.status()} ${response.url()}`);
  };

  const onRequestFailed = (request: {
    url: () => string;
    failure?: () => { errorText?: string } | null;
  }) => {
    const failureText = request.failure?.()?.errorText ?? "unknown failure";
    events.push(`[requestFailed] ${request.url()} ${failureText}`);
  };

  page.on("request", onRequest);
  page.on("response", onResponse);
  page.on("requestfailed", onRequestFailed);

  return {
    events,
    dispose: () => {
      page.off("request", onRequest);
      page.off("response", onResponse);
      page.off("requestfailed", onRequestFailed);
    },
  };
};

export async function attachPageFailureDebugArtifacts(
  testInfo: TestInfo,
  page: Page,
  label: string,
  tracker?: ReturnType<typeof createPageNetworkTracker>,
): Promise<void> {
  const networkSummary = tracker
    ? summarizeNetworkEvents(tracker.events)
    : "No network events captured.";

  await testInfo.attach(`${label}-url`, {
    body: `URL: ${page.url()}`,
    contentType: "text/plain",
  });

  await testInfo.attach(`${label}-source`, {
    body: await page.content(),
    contentType: "text/html",
  });

  await testInfo.attach(`${label}-network`, {
    body: networkSummary,
    contentType: "text/plain",
  });

  await testInfo.attach(`${label}-screenshot`, {
    body: await page.screenshot({ fullPage: true }),
    contentType: "image/png",
  });
}
