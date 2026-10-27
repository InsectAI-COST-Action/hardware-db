# TL;DR

The InsectAI hardware database stores device records as JSON and CSV, with GitHub Actions for form creation, response collection, and index generation.

The image-upload feature is **not yet end-to-end usable through automated form creation**. The generator can copy a template, place its existing upload questions according to the schema, publish the form, and return Google's responder URL. However, Google Forms drops the upload-folder association when the template is copied. The Forms API also rejects attempts to create upload questions or restore their `folderId` afterward. As a result, a freshly generated form has upload questions with no destination folder and requires manual setup in the Forms UI.

This status was verified on 2026-10-27 against a template with restored, active upload folders. The latest test copy was published and accepting responses, but both upload questions had `folderId=None`.

# Current Status

## Working

- `hardware-db_schema.json` is the active schema. The versioned v2 beta schema is in `schemas/hardware-db_schema_v2.0.0-beta.json`.
- `createForm.py` copies the manually authored upload template when the schema declares `file_upload` questions. It leaves those questions unchanged and inserts/moves them into schema order while creating the other sections and questions.
- Newly generated forms are published and set to accept responses. The script retrieves and prints Google's canonical `responderUri`.
- `collectResponses.py` recognizes `fileUploadAnswers` and stores each uploaded file's Drive ID, name, and MIME type in response JSON and CSV data.
- GitHub Actions contain workflows for schema checks, form creation, scheduled response collection, and device-index generation.
- The device-ID checker and data index are in `docs/`.

## Blocking Issue: Upload Folders

Google's Forms API documentation states that file-upload questions cannot be created through the API. The current workflow therefore starts from a manually authored template form and copies it with the Drive API.

Testing established the following:

1. The template's upload questions had valid, non-trashed Drive folder IDs.
2. A new copy made from that template had no `folderId` on either upload question.
3. Assigning the template's existing folder IDs to the copied questions with `forms.batchUpdate` failed with HTTP 400: `Creation of file_upload question not supported.` A regular Drive folder cannot be attached as a substitute.
4. The copy can still report `isPublished=true` and `isAcceptingResponses=true`; publication does not repair the missing upload destination.

Therefore, the current generator cannot create a fresh, upload-ready form without a manual Forms UI step. Reusing the template's upload folders would be acceptable from a storage perspective, but the Forms API does not permit assigning them to a copy. Until this limitation has a supported workaround, automated form creation with file uploads is blocked.

The API also has a separate responder-permissions view. The tested forms had an `anyone` published-reader permission, so the observed failure is not explained by missing link-sharing permission alone.

## Response Collection and Images

The collector currently retrieves response metadata and serializes upload references (`file_id`, `file_name`, `mime_type`) into the database outputs. It does **not** download image bytes from Drive, create image derivatives, or add image assets to the device records or frontend.

Consequently, the complete image pipeline is not implemented. Even after upload-folder provisioning is solved, image files will not yet be copied into the repository or processed into device photos and thumbnails.

## Automation and Local Setup

The GitHub Actions workflows are configured to validate changes, create forms after relevant schema changes, collect responses on a schedule, and regenerate the device index. The form-creation automation must not be treated as production-ready for image uploads until newly created forms can receive upload destinations without manual intervention.

For local development, create and activate a Python environment, then install the project:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e .[ci]
```

Keep OAuth client files and token JSON files in the local, ignored `.secrets` configuration; do not commit credentials. Configuration can also be supplied through CLI arguments and environment variables. When running on Windows, use the `python` command from the activated project environment rather than the `py` launcher if it selects a different interpreter.

Run the focused form tests with:

```powershell
python -m unittest tests.testCreateForm
```

Validate the active schema with:

```powershell
python tests/validateSchema.py hardware-db_schema.json
```

## Data Flow

```text
hardware-db_schema.json -> createForm.py -> Google Form
Google Form -> collectResponses.py -> data/*.json and data/*.csv
data/*.json -> generateIndex.py -> docs/devices_index.json
```

Question IDs in the schema are not sent to Google Forms. Response collection maps form questions back to schema fields by question title, so changing a title requires care. Device record filenames are derived from normalized device names. Existing collision handling detects a submission that would change an existing device record and routes it for maintainer review.

# Roadmap

The checkboxes below distinguish implemented work from work still required for a complete image-upload feature.

- [x] Add optional `file_upload` fields to the schema and validation rules.
- [x] Use a template form to retain manually authored upload questions, without attempting to create or modify those questions through the Forms API.
- [x] Place copied upload questions according to schema order while generating the remaining form items.
- [x] Publish generated forms and retrieve the canonical responder URL.
- [x] Parse uploaded-file metadata from form responses into JSON and CSV outputs.
- [x] Add focused tests for template placement, upload metadata, publication requests, and UTF-8 text handling.
- [ ] Resolve upload-folder provisioning without a per-form manual step. Investigate supported architectures: a single manually initialized form that is updated and reused, a formally supported Google workflow for creating/copying upload destinations, or an external upload service. Do not rely on unsupported Forms API mutations.
- [ ] Confirm the selected architecture with a fresh form, a non-owner responder account, and a real image submission before enabling automated form creation in production.
- [ ] Extend response collection to download uploaded originals from Drive using response file IDs, with handling for permissions, missing files, duplicate submissions, retries, and safe filenames.
- [ ] Define image retention, storage, licensing, privacy, and size policies before committing or publishing respondent images.
- [ ] Post-process images: preserve originals, generate optimized display images and thumbnails, and use the first device-image upload as the cover image while keeping example images separate.
- [ ] Add image paths and relevant metadata to device JSON records and decide how image references should appear in CSV and the device index.
- [ ] Update `generateIndex.py` and the GitHub Pages interface to display cover images and example images.
- [ ] Update the scheduled collection workflow to download and process assets, handle collisions for image changes, and commit or submit them for maintainer review.
- [ ] Add end-to-end tests for image folder availability, response collection, image processing, record updates, and the published responder experience.
- [ ] Re-enable unattended form creation for the upload-enabled schema only after the folder-provisioning blocker is resolved.