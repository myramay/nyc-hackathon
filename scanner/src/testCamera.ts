import { readFile } from "node:fs/promises";
import { extname } from "node:path";

import {
  scanCameraImage,
  type CameraScanInput
} from "./cameraScan.ts";


async function main() {

  const imagePath = process.argv[2];

  if (!imagePath) {
    console.error(
      "Usage: bun run scanner/src/testCamera.ts <image-path>"
    );

    process.exit(1);
  }

  const extension = extname(imagePath).toLowerCase();

  let mimeType: CameraScanInput["mimeType"];

  if (extension === ".jpg" || extension === ".jpeg") {
    mimeType = "image/jpeg";
  } else if (extension === ".png") {
    mimeType = "image/png";
  } else {
    throw new Error("Please provide a JPG or PNG image.");
  }

  const imageBuffer = await readFile(imagePath);

  const base64 = imageBuffer.toString("base64");

  const result = await scanCameraImage({
    base64,
    mimeType
  });

  console.log("\n--- CAMERA ANALYSIS ---");

  console.log("Verdict:", result.verdict);

  console.log("Extractor:", result.extractor);

  console.log("\nExtracted text:");
  console.log(result.analyzed_text);

  console.log("\nFlagged clauses:");

  for (const flag of result.flags) {
    console.log(`\n[${flag.rule_id}] ${flag.severity}`);
    console.log("Evidence:", flag.evidence_text);
    console.log("Explanation:", flag.explanation);
  }

  if (result.notes.length > 0) {
    console.log("\nNotes:", result.notes);
  }

}


main().catch(error => {
  console.error("Camera test failed:", error.message);
  process.exitCode = 1;
});
