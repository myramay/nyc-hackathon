import { analyze } from "../../core/src/analyze.ts";
import { geminiAvailable } from "../../core/src/gemini.ts";

import type { AnalysisResult } from "../../core/src/schema.ts";


export type CameraScanInput = {
  base64: string;
  mimeType: "image/jpeg" | "image/png";
  text?: string;
};


// Maximum image size: 8 MB
const MAX_IMAGE_SIZE = 8 * 1024 * 1024;


// -----------------------------------------
// Analyze a captured image
// -----------------------------------------

export async function scanCameraImage(
  input: CameraScanInput
): Promise<AnalysisResult> {

  // Gemini is necessary to read image-only input.
  if (!geminiAvailable()) {
    throw new Error(
      "GEMINI_API_KEY is required for camera scanning."
    );
  }

  if (
    input.mimeType !== "image/jpeg" &&
    input.mimeType !== "image/png"
  ) {
    throw new Error("Only JPEG and PNG images are supported.");
  }

  // Accept either raw Base64 or a browser data URL.
  const base64 = input.base64.replace(
    /^data:image\/(?:jpeg|png);base64,/,
    ""
  );

  if (!base64 || !/^[A-Za-z0-9+/]*={0,2}$/.test(base64)) {
    throw new Error("Invalid Base64 image.");
  }

  const imageBytes = Buffer.from(base64, "base64");

  if (imageBytes.length === 0) {
    throw new Error("Image cannot be empty.");
  }

  if (imageBytes.length > MAX_IMAGE_SIZE) {
    throw new Error("Image exceeds the 8 MB limit.");
  }

  console.log("Analyzing camera image...");

  const result = await analyze({
    text: input.text,
    image: {
      base64,
      mimeType: input.mimeType
    }
  });

  console.log(`Camera result: ${result.verdict}`);

  return result;
}
