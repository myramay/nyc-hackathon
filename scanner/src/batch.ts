import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";

import { analyze } from "../../core/src/analyze.ts";
import { connectDatabase, saveListing } from "./database.ts";


type Listing = {
  source: string;
  url: string;
  text: string;
  discovered_at: string;
};


const live = process.argv.includes("--live");

const DB_NAME =
  process.env.MONGODB_DB ?? "voucher_detector";


async function loadListings(): Promise<Listing[]> {
  const file = live
    ? new URL("../python/listings.json", import.meta.url)
    : new URL("../data/cached_listings.json", import.meta.url);

  const contents = await readFile(file, "utf-8");

  const records: unknown = JSON.parse(contents);

  if (!Array.isArray(records)) {
    throw new Error("Expected a JSON array");
  }

  for (const item of records) {
    if (
      !item ||
      typeof item !== "object" ||
      typeof item.source !== "string" ||
      typeof item.url !== "string" ||
      typeof item.text !== "string" ||
      typeof item.discovered_at !== "string"
    ) {
      throw new Error("Invalid listing record");
    }
  }

  return records as Listing[];
}


function hashText(text: string): string {
  return createHash("sha256")
    .update(text)
    .digest("hex");
}


async function main() {
  console.log(`Starting ${live ? "live" : "cached"} batch...`);

  const listings = await loadListings();
  const client = await connectDatabase();

  const collection = client
    .db(DB_NAME)
    .collection("listings");

  let processed = 0;
  let skipped = 0;
  let failed = 0;

  try {
    for (const listing of listings) {
      try {
        const hash = hashText(listing.text);

        // Only skip unchanged records in live mode.
        if (live) {
          const existing = await collection.findOne({
            url: listing.url
          });

          if (
            existing &&
            existing.content_hash === hash
          ) {
            skipped++;
            continue;
          }
        }

        const result = await analyze(
          {
            text: listing.text,
            url: listing.url
          },
          {
            // Cached mode is reliable without Gemini.
            useGemini: live
          }
        );

        await saveListing(client, listing, result);

        await collection.updateOne(
          { url: listing.url },
          {
            $set: {
              content_hash: hash,
              last_seen_at: new Date()
            }
          }
        );

        processed++;

        console.log(
          `${listing.url}: ${result.verdict}`
        );

      } catch (error) {
        failed++;

        console.error(
          `Failed: ${listing.url}`,
          error
        );
      }
    }

  } finally {
    await client.close();
  }

  console.log("\nBatch complete");
  console.log(`Processed: ${processed}`);
  console.log(`Unchanged: ${skipped}`);
  console.log(`Failed: ${failed}`);

  if (failed > 0) {
    process.exitCode = 1;
  }
}


main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
