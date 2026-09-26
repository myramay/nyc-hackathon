
import { readFile } from "node:fs/promises";

import {
  connectDatabase,
  saveRentalInventory
} from "./database.ts";


// -----------------------------------------
// Define inventory structure
// -----------------------------------------

type RentalInventory = {
  source: string;
  source_id: string;
  url: string;
  address?: string;
  unit?: string;
  neighborhood?: string;
  borough?: string;
  zip_code?: string;
  monthly_rent?: string;
  net_effective_price?: string;
  bedrooms?: string;
  available_date?: string;
  source_group?: string;
  source_type?: string;
  discovered_at: string;
  description_available: boolean;
};


// -----------------------------------------
// Load the JSON created by Python
// -----------------------------------------

async function loadInventory(): Promise<RentalInventory[]> {

  const file = new URL(
    "../python/real_listings.json",
    import.meta.url
  );

  const contents = await readFile(file, "utf-8");

  return JSON.parse(contents);

}


// -----------------------------------------
// Convert CSV strings into numbers
// -----------------------------------------

function toNumber(value?: string): number | undefined {

  if (!value || value.trim() === "") {
    return undefined;
  }

  const number = Number(value);

  return Number.isFinite(number) ? number : undefined;

}


// -----------------------------------------
// Import rental inventory
// -----------------------------------------

async function importInventory() {

  console.log("Starting rental inventory import...");

  const listings = await loadInventory();

  console.log(`Loaded ${listings.length} rental records.`);

  const client = await connectDatabase();

  let successful = 0;
  let failed = 0;

  try {

    for (const listing of listings) {

      try {

        await saveRentalInventory(client, {
          ...listing,

          monthly_rent: toNumber(listing.monthly_rent),

          net_effective_price: toNumber(
            listing.net_effective_price
          ),

          bedrooms: toNumber(listing.bedrooms)
        });

        successful++;

        console.log(`Saved: ${listing.address ?? listing.source_id}`);

      } catch (error) {

        failed++;

        console.error(
          `Failed to save ${listing.source_id}:`,
          error
        );

      }

    }

  } finally {

    await client.close();

    console.log("Database connection closed.");

  }

  console.log(`Successful: ${successful}`);
  console.log(`Failed: ${failed}`);

  if (failed > 0) {
    process.exitCode = 1;
  }

}


// -----------------------------------------
// Main
// -----------------------------------------

importInventory().catch((error) => {

  console.error(error);

  process.exitCode = 1;

});
