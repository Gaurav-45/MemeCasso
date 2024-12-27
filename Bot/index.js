import { AtpAgent } from "@atproto/api";
import "dotenv/config";
import { CronJob } from "cron";
import axios from "axios";
import sharp from "sharp";

const agent = new AtpAgent({
  service: "https://bsky.social",
});

const MAX_IMAGE_SIZE = 10000000;
let lastLoginTime = null;
const LOGIN_TIMEOUT = 3600000; // 1 hour in milliseconds

const loginToBluesky = async () => {
  const currentTime = Date.now();

  if (lastLoginTime && currentTime - lastLoginTime < LOGIN_TIMEOUT) {
    console.log("Using existing session");
    return;
  }

  try {
    await agent.login({
      identifier: process.env.BLUESKY_USERNAME,
      password: process.env.BLUESKY_PASSWORD,
    });
    lastLoginTime = currentTime;
    console.log("Logged in as:", process.env.BLUESKY_USERNAME);
  } catch (error) {
    console.error("Login failed:", error);
    process.exit(1);
  }
};

const getRootPost = async (uri) => {
  try {
    const response = await agent.app.bsky.feed.getPostThread({
      uri: uri,
      depth: 0,
    });

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
    console.log(error);
    return null;
  }
};

const createHashtagFacets = (hashtags) => {
  const text = hashtags.join(" ");
  const facets = [];
  let position = 0;

  hashtags.forEach((tag) => {
    facets.push({
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
    position += tag.length + 1;
  });

  return { text, facets };
};

const processAndUploadImage = async (imageUrl) => {
  try {
    // Download the image
    const response = await axios.get(imageUrl, { responseType: "arraybuffer" });
    const buffer = Buffer.from(response.data);

    const processedImage = await sharp(buffer)
      .resize(1000, 1000, {
        fit: "inside",
        withoutEnlargement: true,
      })
      .toBuffer();

    if (processedImage.length > MAX_IMAGE_SIZE) {
      throw new Error("Processed image exceeds maximum size limit");
    }

    // Upload to Bluesky
    const uploadResponse = await agent.uploadBlob(processedImage, {
      encoding: "image/jpeg",
    });

    return {
      $type: "app.bsky.embed.images",
      images: [
        {
          alt: "Default response image",
          image: uploadResponse.data.blob,
        },
      ],
    };
  } catch (error) {
    console.error("Error processing image:", error);
    return null;
  }
};

const processMention = async (mention, rootPost) => {
  try {
    const data = JSON.stringify({
      tweet: rootPost.text,
    });

    const response = await axios.post(process.env.MEME_API_ENDPOINT, data, {
      headers: {
        "Content-Type": "application/json",
      },
    });

    const { text, facets } = createHashtagFacets([
      ...response.data.hashtags,
      "#trending",
      "#meme",
    ]);
    const imageEmbed = await processAndUploadImage(response.data.url);

    if (!imageEmbed) {
      throw new Error("Failed to upload image");
    }

    await agent.post({
      text,
      facets,
      reply: {
        root: {
          uri: rootPost?.uri || mention.uri,
          cid: rootPost?.cid || mention.cid,
        },
        parent: {
          uri: mention.uri,
          cid: mention.cid,
        },
      },
      embed: imageEmbed,
    });

    // Mark notifcation as seen and pocessed
    await agent.app.bsky.notification.updateSeen({
      seenAt: new Date().toISOString(),
    });
    console.log("Marked notification as read");
    return true;
  } catch (error) {
    console.error(error);
    return null;
  }
};

const checkMentions = async () => {
  try {
    const response = await agent.app.bsky.notification.listNotifications({
      limit: 50,
    });

    if (!response.data.notifications.length) return;

    const mentions = response.data.notifications.filter(
      (notif) => notif.reason === "mention" && !notif.isRead
    );

    if (mentions.length > 0) {
      for (const mention of mentions) {
        console.log("Processing mention by", mention.author.handle);
        const rootPost = await getRootPost(mention.record.reply?.parent?.uri);
        const reply = processMention(mention, rootPost);
      }
    }
  } catch (error) {
    if (error.message?.includes("auth")) {
      lastLoginTime = null; // Reset login time to force new login
      console.log("Session expired, logging in again...");
      await loginToBluesky();
    } else {
      console.error("Check mentions error:", error);
    }
  }
};

const main = async () => {
  await loginToBluesky();
  await checkMentions();
};

const schedule = "* * * * *";

const job = new CronJob(schedule, main);

job.start();
