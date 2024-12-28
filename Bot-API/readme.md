# MemeCasso Daemon API Service

The **MemeCasso Daemon API Service** powers the MemeCasso bot by continuously monitoring mentions on Bluesky. Instead of running a long-lived daemon process, this API-based service relies on external cron jobs to trigger mention monitoring at regular intervals.

---

## **How the Daemon API Service Works**

1. **Monitoring Mentions**:

   - The service exposes an API endpoint (`/`) that, when triggered, checks for mentions on the Bluesky account.

2. **Processing Mentions**:

   - For each mention, it retrieves the parent post where the bot was tagged.
   - The content of the parent post is sent to the backend API for meme generation.

3. **Posting Meme Replies**:

   - Once the meme is generated, the service posts it as a reply in the same thread.
   - The mention is marked as "read" to avoid duplicate processing.

4. **Cron Job Integration**:
   - To automate mention monitoring, a cron job service (e.g., cron-job.org) pings the API's `/` endpoint every minute.

---

## **Setup Project Locally**

Follow these steps to set up the API service on your local machine:

### 1. **Add a `.env` File**

Create a `.env` file in the project root directory with the following variables:

```plaintext
BLUESKY_EMAIL=<Your Bluesky Account Email>
BLUESKY_PASSWORD=<Your Bluesky Account Password>
BLUESKY_USERNAME=<Your Bluesky Account Username>
MEME_API_ENDPOINT=<Backend API Endpoint for Meme Generation>
```

### 2. **Install Dependencies**

Install the required dependencies by running:

```bash
npm i
```

### 3. **Start the Daemon Service**

Run the daemon service with:

```bash
node index.js
```

### 4. **Integrate with a Cron Job**

1. Deploy the API service to a hosting platform (e.g., Heroku, Render, Vercel, etc.).
2. Copy the hosted API URL.
3. Add the API URL to a free cron job service (e.g., cron-job.org) and set it to ping the (`/`) route every minute.

This will ensure that the service continuously monitors mentions and processes them in real time.

OR

To run locally - ping the (`/`) endpoint eveyminute or run the daemon service from (`Bot/`).
