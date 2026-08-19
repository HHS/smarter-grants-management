import { getSimpleTranslationsSync } from "src/i18n/getMessagesSync";

describe("getSimpleTranslationsSync", () => {
  it("returns original string for string that is not in namespace", () => {
    const result = getSimpleTranslationsSync({
      nameSpace: "Homepage",
      translateableString: "NOT A REAL KEY",
    });
    expect(result).toBe("NOT A REAL KEY");
    expect(typeof result).toBe("string");
  });

  it("returns actual translations for correct string", () => {
    const result = getSimpleTranslationsSync({
      nameSpace: "Homepage",
      translateableString: "title",
    });
    expect(result).toBe("Smarter Grants Management");
    expect(typeof result).toBe("string");
  });
});
