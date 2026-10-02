# Contributing to the architecture docs

This folder holds the architecture documentation for Smarter Grants Management: Opportunity. This guide explains how to update it.

## Files

| File | What it is |
| --- | --- |
| `architecture.md` | The architecture document. |
| `architecture.dsl` | Structurizr DSL model. It is the only source for the diagrams in `diagrams/svg/`. |
| `update-diagrams.sh` | Regenerates `diagrams/svg/` from `architecture.dsl`. |
| `diagrams/svg/` | Generated diagrams embedded in `architecture.md`, plus a `-key` legend for each. |

## Making a change

1. **Edit the model.** Change `architecture.dsl`. Never edit the SVGs by hand.
2. **Regenerate the diagrams.** Run the script. It requires Docker, and nothing else, and you can run it from anywhere in the repo:

   ```sh
   documentation/architecture/update-diagrams.sh
   ```

   It stops with an error, naming the line, if `architecture.dsl` doesn't parse.
3. **Update the document.** If the change adds, removes or renames something, update the matching text and tables in `architecture.md`.
4. **Check the result.** Preview `architecture.md` and confirm each diagram shows your change.

## Notes

- **Image versions:** the Docker images are pinned by digest in `update-diagrams.sh`, so every machine produces the same SVGs. To upgrade a tool, update its digest there and check the diagrams.
- **New diagrams:** add a new view to `architecture.dsl`. The script exports every view, so the new SVG appears in `diagrams/svg/`. Embed it in `architecture.md` with an "Open full size" link underneath, like the existing diagrams.
- **Image tool:** use the `structurizr/structurizr` image. The older `structurizr/cli` image is deprecated and does nothing.
