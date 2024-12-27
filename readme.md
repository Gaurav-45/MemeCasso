# MemeCasso - Tag. Laugh. Repeat

MemeCasso's official Bluesky page [here](https://bsky.app/profile/did:plc:hihp6s2onmvyqpk5h3xtocs7).

**Your Social Media Buddy for an Enhanced Experience**

MemeCasso is a fully functional Bluesky bot designed to bring a dash of humor to your social media experience. By simply tagging MemeCasso, you can receive the perfect meme response to any post—making your interactions more engaging, entertaining, and fun!

## **What Does MemeCasso Do?**

When users tag `@memecasso.bsky.social` on a Bluesky post, the bot works its magic:

- **Analyzes the tagged post** to understand the context.
- **Finds the best meme template** and generates a meme complete with a relevant caption.
- **Replies to the post** with the freshly created meme, delighting your audience and enhancing their scrolling experience.

How cool is that?

---

## **How to Use MemeCasso**

1. Post something fun, interesting, or just plain random on Bluesky.
2. Tag `@memecasso.bsky.social` in your post.
3. Sit back and watch as MemeCasso delivers the perfect meme response.

That's it—MemeCasso takes care of the rest!

---

## **Technical Overview**

MemeCasso runs on a robust backend system designed for real-time meme generation. Here's how it works:

1. **Monitoring Mentions**:

   - MemeCasso listens for mentions every minute using a daemon script.
   - When a new tag is detected, the bot retrieves the root/parent post where it was mentioned.

2. **Processing the Post**:

   - The parent post is sent to a backend service that processes and analyzes the text/content.
   - The backend identifies the best-fitting meme template and generates a suitable caption for the scenario.

3. **Generating the Meme**:

   - The bot uses the ImageFlip API to create the meme based on the chosen template and caption.
   - The generated meme URL is fetched and embedded in the bot's reply.

4. **Posting the Response**:
   - The bot replies to the original post with the meme, ensuring a seamless and delightful experience for users.

---

## **Why MemeCasso?**

- **Effortless Fun**: Turn any post into a hilarious interaction with zero effort.
- **Highly Relevant Memes**: Enjoy memes that are tailored to your post's context.
- **Interactive and Engaging**: Stand out on Bluesky with personalized meme replies.

---

## **Tech Stack**

- **Backend APIs**: Flask, ImageFlip API.
- **Daemon Service**: Node.js, Express.js, Bluesky APIs

---

**Tag. Laugh. Repeat.**  
Join the fun on Bluesky by tagging `@memecasso.bsky.social` and let the memes roll in!
