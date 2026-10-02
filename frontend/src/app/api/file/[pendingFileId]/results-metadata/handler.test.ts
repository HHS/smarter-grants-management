/**
 * @jest-environment node
 */

import { NextRequest } from "next/server";

import { getFileResultsMetadata } from "./handler";

const mockFetchFileScanStatus = jest.fn();

jest.mock("src/services/fetch/fetchers/filesFetcher", () => ({
  fetchFileScanStatus: (id: string) => mockFetchFileScanStatus(id) as unknown,
}));

const fakeRequest = new NextRequest("http://arbitrary");

const buildParams = (pendingFileId: string) => ({
  params: Promise.resolve({ pendingFileId }),
});

const encode = (value: unknown) =>
  new TextEncoder().encode(`${JSON.stringify(value)}\n`);

const streamOf = (
  chunks: Uint8Array[],
  {
    close = false,
    cancel,
  }: { close?: boolean; cancel?: UnderlyingSourceCancelCallback } = {},
) =>
  new ReadableStream({
    start(controller) {
      chunks.forEach((chunk) => controller.enqueue(chunk));
      if (close) controller.close();
    },
    cancel,
  });

describe("GET /api/file/:pendingFileId/results-metadata (getFileResultsMetadata)", () => {
  afterEach(() => {
    jest.resetAllMocks();
  });

  it("returns file_metadata from the first chunk once scanning is complete", async () => {
    const fileMetadata = { file_name: "budget.pdf", file_size_bytes: 4096 };
    mockFetchFileScanStatus.mockResolvedValue(
      streamOf([encode({ data: { file_metadata: fileMetadata } })]),
    );

    const response = await getFileResultsMetadata(
      fakeRequest,
      buildParams("pending-1"),
    );

    expect(response.status).toEqual(200);
    expect((await response.json()) as unknown).toEqual({
      file_metadata: fileMetadata,
    });
    expect(mockFetchFileScanStatus).toHaveBeenCalledWith("pending-1");
  });

  it("does not hang waiting for the reader to cancel when the underlying stream's cancellation never resolves", async () => {
    mockFetchFileScanStatus.mockResolvedValue(
      streamOf([encode({ data: { file_metadata: { file_name: "a.pdf" } } })], {
        cancel: () => new Promise(() => {}),
      }),
    );

    const response = await getFileResultsMetadata(
      fakeRequest,
      buildParams("pending-1"),
    );

    expect(response.status).toEqual(200);
  });

  it("returns 409 when the scan has not completed yet", async () => {
    mockFetchFileScanStatus.mockResolvedValue(
      streamOf([encode({ data: { file_metadata: null } })], { close: true }),
    );

    const response = await getFileResultsMetadata(
      fakeRequest,
      buildParams("pending-1"),
    );

    expect(response.status).toEqual(409);
  });

  it("keeps reading past non-terminal chunks until file_metadata appears", async () => {
    const fileMetadata = { file_name: "budget.pdf", file_size_bytes: 4096 };
    mockFetchFileScanStatus.mockResolvedValue(
      streamOf([
        encode({ data: { file_metadata: null } }),
        encode({ data: { file_metadata: null } }),
        encode({ data: { file_metadata: fileMetadata } }),
      ]),
    );

    const response = await getFileResultsMetadata(
      fakeRequest,
      buildParams("pending-1"),
    );

    expect(response.status).toEqual(200);
    expect((await response.json()) as unknown).toEqual({
      file_metadata: fileMetadata,
    });
  });

  it("handles multiple newline delimited lines batched into a single chunk", async () => {
    const fileMetadata = { file_name: "budget.pdf", file_size_bytes: 4096 };
    const batched = new TextEncoder().encode(
      `${JSON.stringify({ data: { file_metadata: null } })}\n${JSON.stringify({ data: { file_metadata: fileMetadata } })}\n`,
    );
    mockFetchFileScanStatus.mockResolvedValue(streamOf([batched]));

    const response = await getFileResultsMetadata(
      fakeRequest,
      buildParams("pending-1"),
    );

    expect(response.status).toEqual(200);
    expect((await response.json()) as unknown).toEqual({
      file_metadata: fileMetadata,
    });
  });

  it("returns 404 when the stream produces no chunk at all", async () => {
    mockFetchFileScanStatus.mockResolvedValue(streamOf([], { close: true }));

    const response = await getFileResultsMetadata(
      fakeRequest,
      buildParams("pending-1"),
    );

    expect(response.status).toEqual(404);
  });

  it("returns 500 when fetchFileScanStatus throws", async () => {
    mockFetchFileScanStatus.mockRejectedValue(new Error("boom"));

    const response = await getFileResultsMetadata(
      fakeRequest,
      buildParams("pending-1"),
    );

    expect(response.status).toEqual(500);
  });

  it("still cancels the reader when a chunk fails to parse mid-loop", async () => {
    const cancel = jest.fn().mockResolvedValue(undefined);
    mockFetchFileScanStatus.mockResolvedValue(
      streamOf([new TextEncoder().encode("not valid json")], { cancel }),
    );

    const response = await getFileResultsMetadata(
      fakeRequest,
      buildParams("pending-1"),
    );

    expect(response.status).toEqual(500);
    // give the non-blocking `void reader.cancel().catch(...)` microtask a tick to run
    await Promise.resolve();
    expect(cancel).toHaveBeenCalledTimes(1);
  });
});
