import { readFile } from "node:fs/promises";

import { analyze } from "../../core/src/analyze.ts";

import { connectDatabase, saveListing } from "./database.ts";

// -----------------------------------------
// Listing structure
// -----------------------------------------

type Listing = {
  source: string;
  url: string;
  text: string;
  discovered_at: string;
};

// -----------------------------------------
// Read cached listings
// -----------------------------------------

async function loadListings(): Promise<Listing[]> {
  const file = new URL("../data/cached_listings.json", import.meta.url);

  const contents = await readFile(file, "utf-8");

  return JSON.parse(contents);
}

// -----------------------------------------
// Process listings
// -----------------------------------------

async function processListings() {
  console.log("Starting batch analysis...");

  const listings = await loadListings();

  const client = await connectDatabase();

  try {
    for (const listing of listings) {
      console.log(`Analyzing: ${listing.url}`);

      const result = await analyze(
        {
          text: listing.text,
          url: listing.url,
        },
        {
          useGemini: false,
        },
      );

      await saveListing(client, listing, result);

      console.log(`Result: ${result.verdict}`);
    }
  } finally {
    await client.close();

    console.log("Database connection closed.");
  }
}

// -----------------------------------------
// Main
// -----------------------------------------

processListings().catch(console.error);
