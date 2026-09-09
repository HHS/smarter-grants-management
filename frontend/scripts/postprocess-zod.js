const fs = require("fs");
const ts = require("typescript");
const YAML = require("yaml");

const OPENAPI_PATH = "../api/openapi.generated.yml";
const ZOD_PATH = "src/validation-schemas/apiSchemas.zod.ts";

const OPERATOR_EXPRESSIONS = {
  less_than: (left, right) => `${left} < ${right}`,
  less_than_or_equal: (left, right) => `${left} <= ${right}`,
  greater_than: (left, right) => `${left} > ${right}`,
  greater_than_or_equal: (left, right) => `${left} >= ${right}`,
  equal: (left, right) => `${left} === ${right}`,
  not_equal: (left, right) => `${left} !== ${right}`,
};

/**
 * Reads relational validation metadata from the generated OpenAPI document.
 *
 * Relational validations are emitted by the API as an OpenAPI extension:
 *
 * x-relational-validations:
 *   - left_field: award_floor
 *     operator: less_than_or_equal
 *     right_field: award_ceiling
 *
 * The OpenAPI property definitions are retained because we need their types
 * and formats when generating the corresponding Zod validation.
 */
function getRelationalValidations() {
  const openApi = YAML.parse(fs.readFileSync(OPENAPI_PATH, "utf8"));
  const schemas = openApi.components?.schemas ?? {};

  return Object.entries(schemas)
    .filter(([, schema]) => schema["x-relational-validations"]?.length)
    .map(([schemaName, schema]) => ({
      schemaName,
      properties: schema.properties ?? {},
      validations: schema["x-relational-validations"],
    }));
}

/**
 * Returns the non-null OpenAPI types for a property.
 *
 * OpenAPI 3.1 represents nullable fields using a type array. For example:
 *
 *   type: ["string", "null"]
 *
 * becomes:
 *
 *   ["string"]
 *
 * The array does not imply that we expect a field to simultaneously behave
 * as several different non-null types. Removing "null" lets the code below
 * determine the semantic type used by the relational comparison.
 */
function getSchemaTypes(schema) {
  const type = schema?.type;

  if (Array.isArray(type)) {
    return type.filter((value) => value !== "null");
  }

  return type ? [type] : [];
}

/**
 * Builds a runtime guard for a generated relational comparison.
 *
 * We only run the comparison when both values have the expected type. This
 * prevents the relational rule from duplicating ordinary field validation.
 * For example, an invalid date should be reported by the generated date
 * validation rather than also producing a misleading date-order error.
 */
function getValueGuard(schema, expression) {
  const types = getSchemaTypes(schema);

  if (types.includes("string") && schema?.format === "date") {
    return `zod.string().date().safeParse(${expression}).success`;
  }

  if (types.includes("integer") || types.includes("number")) {
    return `typeof ${expression} === "number"`;
  }

  if (types.includes("string")) {
    return `typeof ${expression} === "string"`;
  }

  return null;
}

function getValidationGuards(leftSchema, rightSchema, left, right) {
  return [
    getValueGuard(leftSchema, left),
    getValueGuard(rightSchema, right),
  ].filter(Boolean);
}

/**
 * Determines the semantic comparison type for a relational validation.
 *
 * This value becomes part of the validation message key used by the frontend:
 *
 *   post_date + close_date       -> "date_order"
 *   award_floor + award_ceiling -> "numeric_order"
 *
 * It is not determining sort order. It describes what kind of values are
 * being ordered so the frontend can select an appropriate validation message.
 */
function getRelationalValidationType(
  leftField,
  rightField,
  leftSchema,
  rightSchema,
) {
  const leftTypes = getSchemaTypes(leftSchema);
  const rightTypes = getSchemaTypes(rightSchema);

  const bothDates =
    leftTypes.includes("string") &&
    rightTypes.includes("string") &&
    leftSchema?.format === "date" &&
    rightSchema?.format === "date";

  if (bothDates) {
    return "date_order";
  }

  const leftNumeric =
    leftTypes.includes("integer") || leftTypes.includes("number");

  const rightNumeric =
    rightTypes.includes("integer") || rightTypes.includes("number");

  if (leftNumeric && rightNumeric) {
    return "numeric_order";
  }

  if (leftTypes.includes("string") && rightTypes.includes("string")) {
    return "string_order";
  }

  throw new Error(
    `Unable to determine relational validation type for ` +
      `${leftField} and ${rightField}`,
  );
}

/**
 * Builds the validation message key for one side of a relational validation.
 *
 * Both fields receive an issue so either field can display the relationship
 * error. For:
 *
 *   award_floor <= award_ceiling
 *
 * the generated keys are:
 *
 *   award_floor   -> "award_ceiling_numeric_order"
 *   award_ceiling -> "award_floor_numeric_order"
 */
function getTargetValidationType(
  targetField,
  leftField,
  rightField,
  validationType,
) {
  if (targetField === leftField) {
    return `${rightField}_${validationType}`;
  }

  if (targetField === rightField) {
    return `${leftField}_${validationType}`;
  }

  throw new Error(
    `Relational validation target field ${targetField} is not ` +
      `${leftField} or ${rightField}`,
  );
}

/**
 * Generates one ctx.addIssue call for the .superRefine() callback.
 *
 * Keeping this formatting isolated makes buildSuperRefine easier to read and
 * keeps indentation concerns out of the relational-validation logic.
 */
function buildIssue(field, validationType) {
  return `
      ctx.addIssue({
        code: zod.ZodIssueCode.custom,
        path: [${JSON.stringify(field)}],
        message: ${JSON.stringify(validationType)},
      });`;
}

/**
 * Generates a Zod .superRefine() containing the supplied relational rules.
 *
 * Example OpenAPI metadata:
 *
 *   {
 *     left_field: "award_floor",
 *     operator: "less_than_or_equal",
 *     right_field: "award_ceiling"
 *   }
 *
 * produces validation equivalent to:
 *
 *   .superRefine((data, ctx) => {
 *     if (
 *       data["award_floor"] != null &&
 *       data["award_ceiling"] != null &&
 *       typeof data["award_floor"] === "number" &&
 *       typeof data["award_ceiling"] === "number" &&
 *       !(data["award_floor"] <= data["award_ceiling"])
 *     ) {
 *       ctx.addIssue({
 *         code: zod.ZodIssueCode.custom,
 *         path: ["award_floor"],
 *         message: "award_ceiling_numeric_order",
 *       });
 *       ctx.addIssue({
 *         code: zod.ZodIssueCode.custom,
 *         path: ["award_ceiling"],
 *         message: "award_floor_numeric_order",
 *       });
 *     }
 *   })
 *
 * Null and invalid values are intentionally skipped here. Ordinary generated
 * Zod validation is responsible for reporting those errors.
 */
function buildSuperRefine(validations, properties) {
  const rules = validations
    .map((validation) => {
      const {
        left_field: leftField,
        operator,
        right_field: rightField,
      } = validation;

      const comparison = OPERATOR_EXPRESSIONS[operator];

      if (!comparison) {
        throw new Error(
          `Unsupported relational validation operator: ${operator}`,
        );
      }

      const leftSchema = properties[leftField];
      const rightSchema = properties[rightField];

      if (!leftSchema || !rightSchema) {
        throw new Error(
          `Relational validation references missing fields: ` +
            `${leftField}, ${rightField}`,
        );
      }

      const left = `data[${JSON.stringify(leftField)}]`;
      const right = `data[${JSON.stringify(rightField)}]`;

      const validationType = getRelationalValidationType(
        leftField,
        rightField,
        leftSchema,
        rightSchema,
      );

      const guards = getValidationGuards(leftSchema, rightSchema, left, right);
      const validComparison = comparison(left, right);

      const conditions = [
        `${left} != null`,
        `${right} != null`,
        ...guards,
        `!(${validComparison})`,
      ];

      const issues = [leftField, rightField]
        .map((field) =>
          buildIssue(
            field,
            getTargetValidationType(
              field,
              leftField,
              rightField,
              validationType,
            ),
          ),
        )
        .join("");

      return `
    if (
      ${conditions.join(" &&\n      ")}
    ) {${issues}
    }`;
    })
    .join("\n");

  return `.superRefine((data, ctx) => {${rules}
  })`;
}

/**
 * Finds the source ranges of generated Zod schema initializers.
 *
 * Given generated code such as:
 *
 *   export const OpportunitySchema = zod.object({
 *     award_floor: zod.number(),
 *     award_ceiling: zod.number(),
 *   });
 *
 * this returns the source range containing the zod.object(...) initializer.
 *
 * We use the TypeScript AST rather than matching generated source text with a
 * regular expression so this remains resilient to formatting changes in the
 * generated file.
 */
function findGeneratedSchemaInitializers(sourceText) {
  const sourceFile = ts.createSourceFile(
    ZOD_PATH,
    sourceText,
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.TS,
  );

  const initializers = new Map();

  for (const statement of sourceFile.statements) {
    if (!ts.isVariableStatement(statement)) {
      continue;
    }

    for (const declaration of statement.declarationList.declarations) {
      if (ts.isIdentifier(declaration.name) && declaration.initializer) {
        initializers.set(declaration.name.text, {
          start: declaration.initializer.getStart(sourceFile),
          end: declaration.initializer.getEnd(),
        });
      }
    }
  }

  return initializers;
}

/**
 * Appends generated relational .superRefine() calls to the corresponding
 * generated Zod schemas.
 *
 * Replacements are collected before modifying the source and then applied
 * from the end of the file toward the beginning. This prevents one insertion
 * from invalidating the source positions of later replacements.
 */
function addRelationalValidations(
  sourceText,
  relationalSchemas = getRelationalValidations(),
) {
  const initializers = findGeneratedSchemaInitializers(sourceText);
  const replacements = [];

  for (const { schemaName, validations, properties } of relationalSchemas) {
    const initializer = initializers.get(schemaName);

    if (!initializer) {
      console.warn(
        `Could not find generated Zod schema for OpenAPI schema: ${schemaName}`,
      );
      continue;
    }

    replacements.push({
      start: initializer.start,
      end: initializer.end,
      replacement:
        sourceText.slice(initializer.start, initializer.end) +
        buildSuperRefine(validations, properties),
    });
  }

  // Apply replacements backwards so earlier source positions remain valid.
  replacements.sort((a, b) => b.start - a.start);

  let result = sourceText;

  for (const replacement of replacements) {
    result =
      result.slice(0, replacement.start) +
      replacement.replacement +
      result.slice(replacement.end);
  }

  return result;
}

/**
 * Post-processes the Orval-generated Zod file.
 *
 * Input:
 *   OpenAPI relational metadata + generated apiSchemas.zod.ts
 *
 * Output:
 *   apiSchemas.zod.ts with relational .superRefine() rules appended to the
 *   appropriate schemas.
 *
 * The generated file is also marked @ts-nocheck because it is generated code
 * and should not require manual edits to satisfy project TypeScript rules.
 */
function main() {
  let contents = fs.readFileSync(ZOD_PATH, "utf8");

  contents = addRelationalValidations(contents);

  if (!contents.startsWith("// @ts-nocheck")) {
    contents = `// @ts-nocheck\n${contents}`;
  }

  fs.writeFileSync(ZOD_PATH, contents);
}

if (require.main === module) {
  main();
}

module.exports = {
  addRelationalValidations,
  buildIssue,
  buildSuperRefine,
  findGeneratedSchemaInitializers,
  getRelationalValidations,
  getRelationalValidationType,
  getSchemaTypes,
  getTargetValidationType,
  getValidationGuards,
  getValueGuard,
  main,
};