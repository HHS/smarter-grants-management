# Unit Testing Patterns

Unit testing for the frontend application presents a number of situations where we can approach problems from a few different angles and achieve similar results. Over time the team has developed some best practices which can reduce the work of figuring out which approach to take, and result in the most accurate and resilient tests. When writing unit tests for the frontend application, please follow these guidelines when possible.

## General

### Test utilities

There are situations where we find ourselves doing the same thing over and over again in our tests, or where testing functionality is complex enough that we don't want it clogging up our test files. In these situations we should consider creating testing utilities to solve these problems.

However, generally you don't need to create new utilities, and they can present an issue if they get to complex to the point where you need to test your testing utilities to make sure they work correctly.

Think twice, but if you do create a new utility for testing, put it in `src/utils/testing`.

### Using fixtures

Writing unit tests will often require creating sets of mock data. If this mock data is only useful in the context of a single test scenario, this mock data can be defined directly within the test file. However, if the data could be used across testing multiple functions or components, it should be placed in a fixture file.

One way to think about this is that each of our important Typescript types that are represented in tests likely should have a fixture defined in the fixture file to be used or expanded on, rather than multiple similar mock data implementations across a variety of tests. Even if we have a need to define different specific data for testing a type across different scenarios, having a common fixture that we can work with should be useful, as most data can likely remain static across different implementations.

At the moment we have only one [fixture file](https://github.com/HHS/smarter-grants-management/blob/main/frontend/src/utils/testing/fixtures.ts), but as our application grows we may want to split out into multiple domain specific fixtures.

### Error handling

When you expect an error in a test things can get a little tricky - especially since Jest doesn't like it when you put expect calls in catch blocks - but we have utility that helps with it. The [wrapForExpectedError](https://github.com/HHS/smarter-grants-management/blob/6b9df82808803094c3de0a2b619f75f8da01cac3/frontend/src/utils/testing/commonTestUtils.ts#L30) function will wrap the function that you expect to error and return the error that is thrown. It will also throw if the the function does not throw an error as expected.

### Anti-patterns

#### Defining types

If you find yourself defining types to use in your tests, you're probably getting too complex with your approach. In these cases you can probably either:

- use `unknown` types or ts-ignores. Typescript is nice but since tests are not production code we don't have to worry that much about type safety here. If you're having trouble getting the perfect type for a situation, don't spend time spinning your wheels on types, feel free to opt out.
- create a utility. Some situations are complex and common enough that they deserve their own utilities. This is rare, but if you find yourself building new types, you may be in this sort of a situation.

## Mocking

In order to keep unit tests focused on the specific functionality they are testing, and to avoid creeping into integration test territory, dependencies should be mocked when possible. Jest provides lots of ways to do this, and sometimes it's hard to figure out how to get mocks to work right, but this guide should help.

### General patterns to use

#### Referencing mock functions in import mocks

One of the most common thing we use mocks for is replacing the functionality of imported dependencies. We can use `jest.mock("src.." ,() => {})` for this. The problem is that something like this doesn't work:

```
const mockDependencyFunction = jest.fn();

jest.mock("src/some-thing", () => ({
	dependencyFunction: mockDependencyFunction
}))
```

This is because the call to `jest.mock` is hoisted and runs before `mockDependencyFunction`.

The workaround for this is to write the mock slightly differently.

```
const mockDependencyFunction = jest.fn();

jest.mock("src/some-thing", () => ({
	dependencyFunction: () => mockDependencyFunction()
}))
```

By replacing `dependencyFunction` with an anonymous function that wraps `mockDependencyFunction`, the call to `jest.mock` no longer depends on `mockDependencyFunction` being defined at the time that the dependency file is mocked, as `mockDependencyFunction` only needs to be defined by the time the anonymous mock function is actually called.

Note that this is only necessary when you want to assert something about the function being mocked, or need to change up its behavior. If you only want to stub it out so it doesn't interfere with your tests, something like should work fine, and will be less complex to implement.

```
const mockDependencyFunction = jest.fn();

jest.mock("src/some-thing", () => ({
	dependencyFunction: () => mockDependencyFunction()
}))
```

#### Default exports

Other than page components we shouldn't have that many files that use default exports, so this shouldn't come up a lot, but if we need to mock a default export we can do it like this:

```
jest.mock(
  "src/dependencyToStub",  () => ({
    functionToStub: () => {}
  }),
);
```

#### Globals

If you need to mock a global function or value, follow a pattern like this:

```
let originalTextDecoder: typeof TextDecoder;
const fakeTextDecoder = jest.fn();

describe("Component", () => {
  beforeEach(() => {
    originalTextDecoder = global.TextDecoder;
    global.TextDecoder = fakeTextDecoder;
    ...
  })
  afterEach(() => {
    global.TextDecoder = originalTextDecoder;
	...
  });
  ...
});
```

Note that some globals, like `location` cannot be easily mocked due to implementations of Jest or JSDDOM. You may need to do some non-ideal workarounds in those situations, good luck.

### Available utilities

#### Translation

**Do not test or recreate any functionality that translates translation keys**

When testing a component that uses translation, always use the [useTranslationsMock](https://github.com/HHS/smarter-grants-management/blob/6b9df82808803094c3de0a2b619f75f8da01cac3/frontend/src/utils/testing/intlMocks.ts#L15) function or an identity function. This way the mock will pass through the translation key as the output value, and remove the need to mock any specific translation messages.

```
jest.mock("next-intl", () => ({
  useTranslations: () => useTranslationsMock(),
}));
```

OR

```
jest.mock("next-intl", () => ({
  useTranslations: () => identity,
}));
```

### Anti-patterns

#### Building new components

There should generally not be any need to create new mock versions of components for testing. There may be temptation to do this to work around different testing issues, especially when testing high level or complex components with a lot of other components in the child render tree, but there is usually a better way:

- sub dependency management
  - often testing a high level component will mean rendering child components with their own dependencies that will need to be mocked. For example, the component being tested may have a child that makes an API request on mount, meaning that fetch behavior needs to be mocked. Rather than completely mocking this component, mock out the sub dependencies.

- DOM complexity and targeting
  - Often, when child components are being mocked, it's a sign that the component being tested is difficult to test in isolation, and the test is becoming more of an integration test than an a unit test. This is ok! Integration tests are valuable, and in this case, usually more valuable than a truly isolated unit test would be.
  - In this case, it's important to focus on reserving testing for any functionality that is controlled by child components to the tests for those components, and writing tests that are specific to the functionality of the component that is being tested.

If you find yourself trying to mock a component, or mocking out a JSX return value, think twice and see if you can solve the problems you're facing with one of the approaches mentioned above. If not, mock only the components that need to be mocked in orer to get your tests working correctly.

### Clearing / resetting

Always run `jest.resetAllMocks()` or `jest.clearAllMocks()` in an `afterEach` block to ensure that mocks are cleared after each test. Do not run this in a `beforeEach` block or an `afterAll` block, as we want to make sure that any set up done for each test is cleared after it is run.

Whether to use `reset` or `clear` is up to you, and depends on whether you want to reset the mock implementatins (`reset`) or not (`clear`). If using `reset`, you will likely want to set up mock implementations in a `beforeEach` block.

### Special cases

## API handlers

### Redirects

Next JS API redirect behavior for some reason relies on throwing errors. As such, testing any handler that uses a redirect will need to catch an error. Use the `wrapForExpectedError` function as described above when running tests on handlers that redirect.
