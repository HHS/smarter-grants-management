/**
 * @file Setup the toolbar, styling, and global context for each Storybook story.
 * @see https://storybook.js.org/docs/configure#configure-story-rendering
 */
import { Loader, Preview } from "@storybook/react";
import { useClientFetch } from "src/hooks/useClientFetch";
import { mocked, sb } from "storybook/test";

import "src/styles/styles.scss";

import { defaultLocale, locales } from "src/i18n/config";
import { messages } from "src/i18n/messages/en";

import withMockedClientFetch, {
  useMockedClientFetch,
} from "./decorators/withMockedClientFetch";
import I18nStoryWrapper from "./I18nStoryWrapper";

// stories never call a real API: useClientFetch is replaced in every story by
// useMockedClientFetch (see the withMockedClientFetch decorator)
sb.mock("../src/hooks/useClientFetch.ts");

const parameters = {
  nextjs: {
    appDirectory: true,
  },
  controls: {
    matchers: {
      color: /(background|color)$/i,
      date: /Date$/,
    },
  },
  options: {
    storySort: {
      method: "alphabetical",
      order: [
        "About",
        "Brand",
        "Core Components",
        "Welcome",
        "Core",
        // Storybook infers the title when not explicitly set, but is case-sensitive
        // so we need to explicitly set both casings here for this to properly sort.
        "Components",
        "components",
        "Features",
        "Templates",
        "Pages",
        "pages",
      ],
    },
  },
};

// not using `getMessagesWithFallbacks` as the import asset paths in there
// cause problems during vite compilation. Hardcoding to english for now
const i18nMessagesLoader: Loader = () => {
  return { messages };
};

const preview: Preview = {
  loaders: [i18nMessagesLoader],
  decorators: [I18nStoryWrapper, withMockedClientFetch],
  parameters,
  beforeEach: () => {
    mocked(useClientFetch).mockImplementation(useMockedClientFetch);
  },

  globalTypes: {
    locale: {
      description: "Active language",
      defaultValue: defaultLocale,
      toolbar: {
        icon: "globe",
        items: locales,
      },
    },
  },

  tags: ["autodocs"],
};

export default preview;
