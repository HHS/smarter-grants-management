/**
 * @jest-environment node
 */

import { ApiRequestError } from "src/errors";
import { FileUploadDetailsResponse } from "src/types/apiResponseTypes";
import { FileUploadStatusUpdate } from "src/types/fileUploadTypes";
import {
  AdvanceTestStreamTrigger,
  createAdvanceStreamTrigger,
  makeAdvanceableTestStreamForTrigger,
} from "src/utils/testing/streamTestUtils";

import { NextRequest } from "next/server";

import { handleFileUpload } from "./handler";

const mockFetchFileUploadDetails = jest.fn<
  Promise<FileUploadDetailsResponse>,
  [string, string]
>();
const mockFetchFileScanStatus = jest.fn();
const mockUploadFileToS3 = jest.fn<Promise<boolean>, [string, unknown, File]>();
const fakeTextDecoder = jest.fn();

let trigger: AdvanceTestStreamTrigger;
let testStream: ReadableStream;
const testResponseChunks = [
  JSON.stringify({ data: { status: "step 1" } }),
  JSON.stringify({ data: { status: "step 2" } }),
  JSON.stringify({ data: { status: "step 3" } }),
];

jest.mock("src/services/fetch/fetchers/filesFetcher", () => ({
  fetchFileUploadDetails: (fileName: string, mimeType: string) =>
    mockFetchFileUploadDetails(fileName, mimeType),
  fetchFileScanStatus: (id: string) => mockFetchFileScanStatus(id) as unknown,
  uploadFileToS3: (url: string, body: unknown[], file: File) =>
    mockUploadFileToS3(url, body, file),
}));

let originalTextDecoder: typeof TextDecoder;

const makeRequest = (withFile = true) => {
  const testFormData = new FormData();
  if (withFile) {
    testFormData.append(
      "file_attachment",
      new File(["file contents"], "file.txt", {
        type: "application/octet-stream",
      }),
    );
  }
  return new NextRequest("http://arbitrary", {
    method: "POST",
    body: testFormData,
  });
};

const getReader = (response: Response) =>
  response.body?.getReader() as ReadableStreamDefaultReader<FileUploadStatusUpdate>;

describe("POST request handler /api/file (handleFileUpload)", () => {
  beforeEach(() => {
    trigger = createAdvanceStreamTrigger();
    testStream = makeAdvanceableTestStreamForTrigger(
      testResponseChunks,
      trigger,
    );
    mockFetchFileScanStatus.mockResolvedValue(testStream);
    mockFetchFileUploadDetails.mockResolvedValue({
      url: "any url",
      pending_file_id: "fake id",
      body: {
        key: "some sort of body to send in the next request",
      },
    });

    fakeTextDecoder.mockImplementation(() => ({
      decode: (value: unknown) => value,
    }));
    originalTextDecoder = global.TextDecoder;
    global.TextDecoder = fakeTextDecoder;
  });
  afterEach(() => {
    jest.resetAllMocks();
    global.TextDecoder = originalTextDecoder;
  });
  it("returns an error if no file is sent", async () => {
    const response = await handleFileUpload(makeRequest(false));
    expect(response.status).toEqual(400);
  });
  it("calls fetchFileUploadDetails with uploaded file, and streams 'starting' status", async () => {
    const response = await handleFileUpload(makeRequest());
    expect(response.status).toEqual(200);
    expect(response.body).toBeInstanceOf(ReadableStream);

    const reader = getReader(response);
    const firstChunk = await reader.read();
    expect(firstChunk.value).toEqual('{"status":"starting"}');

    expect(mockFetchFileUploadDetails).toHaveBeenCalledTimes(1);
    expect(mockFetchFileUploadDetails).toHaveBeenCalledWith(
      "file.txt",
      "application/octet-stream",
    );
  });
  it("calls uploadFileToS3 with returned data from fetchFileUploadDetails and file, and streams 'uploading' status", async () => {
    const response = await handleFileUpload(makeRequest());
    const reader = getReader(response);

    await reader.read();
    const secondChunk = await reader.read();
    expect(secondChunk.value).toEqual('{"status":"uploading"}');

    expect(mockUploadFileToS3).toHaveBeenCalledTimes(1);
    expect(mockUploadFileToS3).toHaveBeenCalledWith(
      "any url",
      { key: "some sort of body to send in the next request" },
      expect.any(File),
    );
    const fileArg: File = mockUploadFileToS3.mock.calls[0][2];
    expect(fileArg.name).toEqual("file.txt");
  });
  it("calls fetchFileScanStatus with pending_file_id from fetchFileUploadDetails, and streams 'starting-scan' status", async () => {
    const response = await handleFileUpload(makeRequest());
    const reader = getReader(response);

    await reader.read();
    await reader.read();
    const thirdChunk = await reader.read();
    expect(thirdChunk.value).toEqual('{"status":"starting-scan"}');

    expect(mockFetchFileScanStatus).toHaveBeenCalledWith("fake id");
  });
  it("streams data from fetchFileScanStatus into response stream", async () => {
    const response = await handleFileUpload(makeRequest());
    const reader = getReader(response);

    // advance through starting, uploading, and starting-scan states
    await reader.read();
    await reader.read();
    await reader.read();

    trigger.advance();
    expect((await reader.read()).value).toEqual('{"status":"step 1"}');
    trigger.advance();
    expect((await reader.read()).value).toEqual('{"status":"step 2"}');
    trigger.advance();
    expect((await reader.read()).value).toEqual('{"status":"step 3"}');
  });
  it("streams data from fetchFileScanStatus only when data status changes", async () => {
    testStream = makeAdvanceableTestStreamForTrigger(
      [
        JSON.stringify({ data: { status: "step 1" } }),
        JSON.stringify({ data: { status: "step 1" } }),
        JSON.stringify({ data: { status: "step 1" } }),
        JSON.stringify({ data: { status: "step 2" } }),
        JSON.stringify({ data: { status: "step 3" } }),
      ],
      trigger,
    );
    mockFetchFileScanStatus.mockResolvedValue(testStream);
    const response = await handleFileUpload(makeRequest());
    const reader = getReader(response);

    await reader.read();
    await reader.read();
    await reader.read();

    trigger.advance();
    expect((await reader.read()).value).toEqual('{"status":"step 1"}');
    trigger.advance();
    trigger.advance();
    trigger.advance();
    expect((await reader.read()).value).toEqual('{"status":"step 2"}');
    trigger.advance();
    expect((await reader.read()).value).toEqual('{"status":"step 3"}');
  });
  it("handles newline delimited and batched chunks from the scan status stream", async () => {
    testStream = makeAdvanceableTestStreamForTrigger(
      [
        `${JSON.stringify({ data: { status: "step 1" } })}\n`,
        `${JSON.stringify({ data: { status: "step 1" } })}\n${JSON.stringify({ data: { status: "step 2" } })}\n`,
      ],
      trigger,
    );
    mockFetchFileScanStatus.mockResolvedValue(testStream);
    const response = await handleFileUpload(makeRequest());
    const reader = getReader(response);

    await reader.read();
    await reader.read();
    await reader.read();

    trigger.advance();
    expect((await reader.read()).value).toEqual('{"status":"step 1"}');
    trigger.advance();
    expect((await reader.read()).value).toEqual('{"status":"step 2"}');
  });
  it("streams error data if fetchFileUploadDetails returns an error response", async () => {
    mockFetchFileUploadDetails.mockRejectedValue(
      new ApiRequestError("api error"),
    );
    const response = await handleFileUpload(makeRequest());
    // note that we'll still get a 200 response, even in an error case
    expect(response.status).toEqual(200);

    const reader = getReader(response);
    await reader.read();
    const errorChunk = await reader.read();
    expect(errorChunk.value).toEqual('{"status":"error","error":"api error"}');
  });
  it("streams error data if uploadFileToS3 returns an error response", async () => {
    mockUploadFileToS3.mockRejectedValue(new ApiRequestError("api error"));
    const response = await handleFileUpload(makeRequest());
    expect(response.status).toEqual(200);

    const reader = getReader(response);
    await reader.read();
    await reader.read();
    const errorChunk = await reader.read();
    expect(errorChunk.value).toEqual('{"status":"error","error":"api error"}');
  });
  it("streams error data if fetchFileScanStatus returns an error response", async () => {
    mockFetchFileScanStatus.mockRejectedValue(new ApiRequestError("api error"));
    const response = await handleFileUpload(makeRequest());
    expect(response.status).toEqual(200);

    const reader = getReader(response);
    await reader.read();
    await reader.read();
    await reader.read();
    const errorChunk = await reader.read();
    expect(errorChunk.value).toEqual('{"status":"error","error":"api error"}');
  });
  it("streams a pending file id on scan completion", async () => {
    const response = await handleFileUpload(makeRequest());
    const reader = getReader(response);

    await reader.read();
    await reader.read();
    await reader.read();

    trigger.advance();
    await reader.read();
    trigger.advance();
    await reader.read();
    trigger.advance();
    await reader.read();
    trigger.advance();
    const scanCompleteChunk = await reader.read();
    expect(scanCompleteChunk.value).toEqual(
      '{"status":"scan-complete","pendingFileId":"fake id"}',
    );
  });
  it("sets infected error in stream when receiving infected status from API", async () => {
    testStream = makeAdvanceableTestStreamForTrigger(
      [JSON.stringify({ data: { status: "infected" } })],
      trigger,
    );
    mockFetchFileScanStatus.mockResolvedValue(testStream);
    const response = await handleFileUpload(makeRequest());
    const reader = getReader(response);

    await reader.read();
    await reader.read();
    await reader.read();

    trigger.advance();
    const firstChunk = await reader.read();
    expect(firstChunk.value).toEqual(
      '{"status":"error","error":"Virus scan failed, file infected"}',
    );
  });
});
