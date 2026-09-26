import { MongoClient } from "mongodb";

import type { AnalysisResult } from "../../core/src/schema.ts";


// -----------------------------------------
// Database configuration
// -----------------------------------------

const MONGODB_URI = process.env.MONGODB_URI;

const DATABASE_NAME =
  process.env.MONGODB_DB ?? "voucher_detector";


// -----------------------------------------
// Connect to MongoDB
// -----------------------------------------

export async function connectDatabase() {

  if (!MONGODB_URI) {
    throw new Error("MONGODB_URI is missing from .env");
  }

  const client = new MongoClient(MONGODB_URI, {
    serverSelectionTimeoutMS: 10000,
    connectTimeoutMS: 10000,
  });

  console.log("Connecting to MongoDB Atlas...");

  await client
    .db(DATABASE_NAME)
    .collection("listings")
    .createIndex({ url: 1 }, { unique: true });

  await client
    .db(DATABASE_NAME)
    .collection("rental_inventory")
    .createIndex(
      { source: 1, source_id: 1 },
      { unique: true }
    );

  console.log("Connected to MongoDB!");

  return client;
}


// -----------------------------------------
// Save an analyzed listing
// -----------------------------------------

export async function saveListing(
  client: MongoClient,
  listing: {
    source: string;
    url: string;
    text: string;
    discovered_at: string;
  },
  result: AnalysisResult
) {

  const database = client.db(DATABASE_NAME);

  const collection = database.collection("listings");

  // Update an existing listing instead of inserting duplicates.
  await collection.updateOne(
    { url: listing.url },
    {
      $set: {
        ...listing,
        analysis: result,
        updated_at: new Date()
      }
    },
    { upsert: true }
  );

}


// -----------------------------------------
// Save rental inventory records
// -----------------------------------------

export async function saveRentalInventory(
  client: MongoClient,
  listing: {
    source: string;
    source_id: string;
    url: string;
    address?: string;
    unit?: string;
    neighborhood?: string;
    borough?: string;
    zip_code?: string;
    monthly_rent?: number;
    net_effective_price?: number;
    bedrooms?: number;
    available_date?: string;
    source_group?: string;
    source_type?: string;
    discovered_at: string;
    description_available: boolean;
  }
) {

  const database = client.db(DATABASE_NAME);

  const collection = database.collection("rental_inventory");

  await collection.updateOne(
    {
      source: listing.source,
      source_id: listing.source_id
    },
    {
      $set: {
        ...listing,
        updated_at: new Date()
      }
    },
    {
      upsert: true
    }
  );

}
