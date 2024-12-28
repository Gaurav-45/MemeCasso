# MemeCasso Backend Service

The backend service for **MemeCasso** is built using Flask. It processes tagged posts, analyzes their context, and generates hilarious memes and hashtags by interacting with the ImageFlip API.

---

## **What Does the Backend Do?**

1. **Tweet Analysis**: Accepts a tweet or post as input and analyzes it using contextual understanding.
2. **Meme Template Selection**: Calls a language model (LLM) to generate a meme template and caption based on the input.
3. **Meme Generation**: Uses the ImageFlip API to convert the captions and template into an actual meme.
4. **Returns Meme URL**: The generated meme link is returned, which can then be used to respond to posts.

---

## **How to Set Up and Run the Service Locally**

Follow these steps to get the backend service running on your local machine:

### 1. **Create a `.env` File**

Create a `.env` file in the root directory and add the following variables:

```plaintext
GOOGLE_API_KEY=<Your Google API Key>
IMGFLIP_USERNAME=<Your ImgFlip Username>
IMGFLIP_PASSWORD=<Your ImgFlip Password>
BSKY_EMAIL=<Your Bluesky Email>
BSKY_PASS=<Your Bluesky Password>
BSKY_USERNAME=<Your Bluesky Username>
```

### 2. **Set Up a Virtual Environment**

Set up a Python virtual environment to isolate dependencies:
On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

On Windows:

```bash
python -m venv venv
source venv/bin/activate
```

### 3. **Install Dependencies**

Install the required Python packages by running:

```bash
pip install -r requirements.txt
```

### 4. **Start the Flask Service**

Run the Flask application with:

```bash
python app.py
```

---

## **How to Use the Backend API**

**Endpoint**: /generate-meme
**Method**: POST
**Request Body (JSON):**:

```json
{
  "tweet": "YOUR_TWEET"
}
```

**Example**

```bash
curl -X POST http://localhost:5000/generate-meme \
-H "Content-Type: application/json" \
-d '{"tweet": "What a beautiful day to code memes!"}'
```

**Sample response**

```json
{
  "captions": [
    "Waiting for Microsoft to release a Word Processor I own forever",
    ""
  ],
  "hashtags": [
    "#OfficeForever",
    "#WordProcessorNostalgia",
    "#WaitingSkeleton",
    "#SoftwareAsAService",
    "#DigitalFatigue"
  ],
  "success": true,
  "template_used": "Waiting Skeleton",
  "url": "https://i.imgflip.com/9f03v6.jpg"
}
```
