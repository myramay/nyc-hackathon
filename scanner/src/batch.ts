import { readFile } from "node:fs/promises";

import { analyze } from "../../core/src/analyze.ts";

import { analyzeUrl } from "./analyzeUrl.ts";

import {
  connectDatabase,
  saveListing
} from "./database.ts";


// -----------------------------------------
// Types
// -----------------------------------------

type Listing = {
  source: string;
  url: string;
  text?: string;
  discovered_at: string;
};


// -----------------------------------------
// Configuration
// -----------------------------------------

const mode = process.argv.includes("--live")
  ? "live"
  : "cached";


// -----------------------------------------
// Load JSON listings
// -----------------------------------------

async function loadListings(): Promise<Listing[]> {

  const file =
    mode === "live"
      ? new URL("../python/listings.json", import.meta.url)
      : new URL("../data/cached_listings.json", import.meta.url);

  const contents = await readFile(file, "utf-8");

  const listings: unknown = JSON.parse(contents);

  if (!Array.isArray(listings)) {
    throw new Error("Expected an array of listings.");
  }

  for (const listing of listings) {

    if (
      !listing ||
      typeof listing !== "object" ||
      typeof listing.source !== "string" ||
      typeof listing.url !== "string" ||
      typeof listing.discovered_at !== "string"
    ) {
      throw new Error("Invalid listing structure.");
    }

    if (mode === "cached" && typeof listing.text !== "string") {
      throw new Error("Cached listing is missing text.");
    }

  }

  return listings as Listing[];

}


// -----------------------------------------
// Process listings
// -----------------------------------------

async function processListings() {

  console.log(`Starting ${mode} batch analysis...`);

  const listings = await loadListings();

  console.log(`Loaded ${listings.length} listings.`);

  if (listings.length === 0) {
    console.log("No listings to process.");
    return;
  }

  const client = await connectDatabase();

  let successful = 0;
  let failed = 0;

  try {

    for (const listing of listings) {

      console.log(`\nAnalyzing: ${listing.url}`);

      try {

        let result;
        let listingText: string;

        if (mode === "live") {

          // Fetch the listing through Myra's existing scanner.
          const analyzed = await analyzeUrl(listing.url);

          result = analyzed.result;

          listingText = analyzed.fetched.text;

        } else {

          // Cached mode doesn't contact external websites
          // or require a Gemini API key.
          listingText = listing.text!;

          result = await analyze(
            {
              text: listingText,
              url: listing.url
            },
            {
              useGemini: false
            }
          );

        }

        await saveListing(
          client,
          {
            source: listing.source,
            url: listing.url,
            text: listingText,
            discovered_at: listing.discovered_at
          },
          result
        );

        console.log(`Result: ${result.verdict}`);

        successful++;

      } catch (error) {

        failed++;

        console.error(
          `Failed to process ${listing.url}:`,
          error
        );

      }

    }

  } finally {

    await client.close();

    console.log("\nDatabase connection closed.");

  }

  console.log(`Successful: ${successful}`);
  console.log(`Failed: ${failed}`);

  if (failed > 0) {
    process.exitCode = 1;
  }

}


// -----------------------------------------
// Run
// -----------------------------------------

processListings().catch((error) => {

  console.error("Batch processing failed:", error);

  process.exitCode = 1;

});
