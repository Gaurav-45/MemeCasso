import express from "express";
import { AtpAgent } from "@atproto/api";
import "dotenv/config";
import axios from "axios";
import sharp from "sharp";
import cors from "cors";

const app = express();
app.use(cors());
app.use(express.json());

const agent = new AtpAgent({
  service: "https://bsky.social",
});

const MAX_IMAGE_SIZE = 10000000;
let lastLoginTime = null;
const LOGIN_TIMEOUT = 3600000;

const loginToBluesky = async () => {
  const currentTime = Date.now();
  if (lastLoginTime && currentTime - lastLoginTime < LOGIN_TIMEOUT) return;

  try {
    await agent.login({
      identifier: process.env.BLUESKY_USERNAME,
      password: process.env.BLUESKY_PASSWORD,
    });
    lastLoginTime = currentTime;
  } catch (error) {
    console.error("Login failed:", error);
    throw error;
  }
};

const getRootPost = async (uri) => {
  try {
    const response = await agent.app.bsky.feed.getPostThread({ uri, depth: 0 });
    if (response.data.thread?.post) {
      const post = response.data.thread.post;
      return {
        text: post.record.text,
        uri: post.uri,
        cid: post.cid,
        embed: post.record.embed,
      };
    }
    return null;
  } catch (error) {
    console.error(error);
    return null;
  }
};

const createHashtagFacets = (hashtags) => {
  const text = hashtags.join(" ");
  const facets = hashtags.reduce((acc, tag, index) => {
    const position = index === 0 ? 0 : acc.length + 1;
    acc.push({
      index: {
        byteStart: position,
        byteEnd: position + tag.length,
      },
      features: [
        {
          $type: "app.bsky.richtext.facet#tag",
          tag: tag.replace("#", ""),
        },
      ],
    });
    return acc;
  }, []);
  return { text, facets };
};

const processAndUploadImage = async (imageUrl) => {
  try {
    const response = await axios.get(imageUrl, { responseType: "arraybuffer" });
    const processedImage = await sharp(Buffer.from(response.data))
      .resize(1000, 1000, { fit: "inside", withoutEnlargement: true })
      .toBuffer();

    if (processedImage.length > MAX_IMAGE_SIZE) {
      throw new Error("Processed image exceeds maximum size limit");
    }

    const uploadResponse = await agent.uploadBlob(processedImage, {
      encoding: "image/jpeg",
    });

    return {
      $type: "app.bsky.embed.images",
      images: [
        { alt: "Default response image", image: uploadResponse.data.blob },
      ],
    };
  } catch (error) {
    console.error(error);
    return null;
  }
};

const processMention = async (mention, rootPost) => {
  try {
    const response = await axios.post(
      process.env.MEME_API_ENDPOINT,
      { tweet: rootPost.text },
      { headers: { "Content-Type": "application/json" } }
    );

    const { text, facets } = createHashtagFacets([
      ...response.data.hashtags,
      "#trending",
      "#meme",
    ]);

    const imageEmbed = await processAndUploadImage(response.data.url);
    if (!imageEmbed) throw new Error("Failed to upload image");

    await agent.post({
      text,
      facets,
      reply: {
        root: {
          uri: rootPost?.uri || mention.uri,
          cid: rootPost?.cid || mention.cid,
        },
        parent: { uri: mention.uri, cid: mention.cid },
      },
      embed: imageEmbed,
    });

    await agent.app.bsky.notification.updateSeen({
      seenAt: new Date().toISOString(),
    });

    return true;
  } catch (error) {
    console.error(error);
    return null;
  }
};

app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

app.get("/", async (req, res) => {
  try {
    await loginToBluesky();

    const response = await agent.app.bsky.notification.listNotifications({
      limit: 50,
    });

    const mentions = response.data.notifications.filter(
      (notif) => notif.reason === "mention" && !notif.isRead
    );

    const results = await Promise.all(
      mentions.map(async (mention) => {
        const rootPost = await getRootPost(mention.record.reply?.parent?.uri);
        return processMention(mention, rootPost);
      })
    );

    res.json({
      success: true,
      processedMentions: results.filter(Boolean).length,
    });
  } catch (error) {
    if (error.message?.includes("auth")) {
      lastLoginTime = null;
      res.status(401).json({ error: "Authentication failed" });
    } else {
      res.status(500).json({ error: error.message });
    }
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

export default app;
