import { defineConfig } from 'better-auth';
import { nextCookies } from '@better-auth/next-js';

// Note: For Docusaurus, we need to handle auth differently since it doesn't have API routes
// This would typically be used in a separate server, but we'll create a client-side compatible setup

export const auth = defineConfig({
  database: {
    provider: "sqlite",
    url: process.env.DATABASE_URL || "./db.sqlite",
  },
  secret: process.env.AUTH_SECRET || "your-secret-key-here",
  emailAndPassword: {
    enabled: true,
  },
  user: {
    additionalFields: {
      yearsOfExperience: {
        type: "number",
        required: true,
      },
      hardwareKnowledge: {
        type: "boolean",
        required: true,
      },
      favoriteLanguage: {
        type: "string",
        required: true,
      },
    },
  },
});