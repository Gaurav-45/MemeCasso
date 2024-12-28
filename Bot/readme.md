# MemeCasso Daemon Service

The **MemeCasso Daemon Service** powers the MemeCasso bot by continuously monitoring mentions on Bluesky. It processes mentions, generates memes by interacting with the backend API, and posts the generated memes back to the same thread—all in real time.

---

## **How the Daemon Service Works**

1. **Monitoring Mentions**:

   - The daemon service runs continuously and checks for mentions every 1 minute.
   - It retrieves notifications/mentions from the Bluesky account.

2. **Processing Mentions**:

   - For each mention, it identifies the parent post where the bot was tagged.
   - The parent post content is sent to the backend API to generate a meme.

3. **Posting Meme Replies**:
   - Once the meme is generated, the service posts it as a reply in the same thread.
   - The notification is marked as "read" after processing, ensuring no duplication.

---

## **Setup Project Locally**

Follow these steps to set up the daemon service on your local machine:

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

The service will now continuously monitor mentions and process them.
