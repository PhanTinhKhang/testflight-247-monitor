/**
 * TestFlight 24/7 Auto Slot Monitor - Cloudflare Worker (100% Free Serverless)
 * 
 * Runs 24/7 in the cloud on Cloudflare's global edge network.
 * Triggered by Cloudflare Cron Trigger (e.g. every minute) to check TestFlight status
 * and send instant Discord notifications with @everyone ping when a slot opens.
 */

// Configure your targets below or via Cloudflare Environment Variables:
const DEFAULT_LINK_ID = "EgZ8sE2P"; // Target TestFlight link ID
const DEFAULT_DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1542133009984000000/8qzHzXV0YYAeNv7Pj9Mw5bCC-j9JU2Hc7Mi-zSWFzCSW132iAxeNwbfNwkHZAtE3B1sq";

export default {
  // 1. Cron Trigger Handler (Runs on schedule 24/7)
  async scheduled(event, env, ctx) {
    const linkId = env.LINK_ID || DEFAULT_LINK_ID;
    const webhookUrl = env.DISCORD_WEBHOOK || DEFAULT_DISCORD_WEBHOOK;
    
    ctx.waitUntil(checkAndNotify(linkId, webhookUrl, env));
  },

  // 2. HTTP Handler (Allows manual check/trigger from browser)
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const linkId = url.searchParams.get("link_id") || env.LINK_ID || DEFAULT_LINK_ID;
    const webhookUrl = env.DISCORD_WEBHOOK || DEFAULT_DISCORD_WEBHOOK;

    const result = await checkTestFlightSlot(linkId);
    
    if (url.searchParams.get("test_webhook") === "true") {
      await sendDiscordAlert(webhookUrl, linkId, result.appName, result.iconUrl, true);
    } else if (result.isOpen) {
      await sendDiscordAlert(webhookUrl, linkId, result.appName, result.iconUrl, false);
    }

    return new Response(JSON.stringify({
      timestamp: new Date().toISOString(),
      target_link_id: linkId,
      result: result
    }, null, 2), {
      headers: { "Content-Type": "application/json" }
    });
  }
};

async function checkAndNotify(linkId, webhookUrl, env) {
  const result = await checkTestFlightSlot(linkId);
  console.log(`[TestFlight] Check for ${linkId} (${result.appName}): ${result.isOpen ? 'OPEN!' : 'FULL'}`);

  if (result.isOpen) {
    await sendDiscordAlert(webhookUrl, linkId, result.appName, result.iconUrl, false);
  }
}

async function checkTestFlightSlot(linkId) {
  const targetUrl = `https://testflight.apple.com/join/${linkId}`;
  
  try {
    const res = await fetch(targetUrl, {
      headers: {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Accept-Language": "en-US,en;q=0.9,vi;q=0.8"
      }
    });

    if (res.status !== 200) {
      return { isOpen: false, appName: "Unknown", iconUrl: null, status: `HTTP ${res.status}` };
    }

    const html = await res.text();
    const appName = extractAppName(html);
    const iconUrl = extractIconUrl(html);

    const fullPhrases = [
      "this beta is full",
      "is full",
      "isn&#39;t accepting any new testers",
      "isn't accepting any new testers",
      "not accepting any new testers",
      "doesn&#39;t have any available testers",
      "doesn't have any available testers",
      "bản beta này đã đầy",
      "đã đầy",
      "không chấp nhận bất kỳ người thử nghiệm nào",
      "không còn chỗ"
    ];

    const lowerHtml = html.toLowerCase();
    for (const phrase of fullPhrases) {
      if (lowerHtml.includes(phrase)) {
        return { isOpen: false, appName, iconUrl, status: "Beta is full." };
      }
    }

    return { isOpen: true, appName, iconUrl, status: "Slot is AVAILABLE!" };
  } catch (err) {
    return { isOpen: false, appName: "Unknown", iconUrl: null, status: `Error: ${err.message}` };
  }
}

function extractAppName(html) {
  const match = html.match(/<meta property="og:title" content="([^"]+)"/i) || html.match(/<title>(.*?)<\/title>/i);
  if (match && match[1]) {
    return match[1].replace(" - Apple", "").replace("TestFlight - Apple", "").replace("Join the ", "").replace("Tham gia ", "").replace(" beta", "").replace("Beta", "").trim();
  }
  return "TestFlight Beta";
}

function extractIconUrl(html) {
  const match = html.match(/<meta property="og:image" content="([^"]+)"/i) || html.match(/background-image:\s*url\((https:\/\/[^)]+mzstatic\.com[^)]+)\)/i);
  return match && match[1] ? match[1] : null;
}

async function sendDiscordAlert(webhookUrl, linkId, appName, iconUrl, isTest) {
  const joinUrl = `https://testflight.apple.com/join/${linkId}`;
  
  const embed = {
    title: isTest ? `🔔 TestFlight Cloud Monitor Connected: ${appName}` : `🎉 SLOT AVAILABLE: ${appName}`,
    url: joinUrl,
    description: isTest 
      ? `Cloudflare Worker 24/7 Monitor is active and watching **${appName}**!`
      : `🚀 **A slot is open right now!**\n\n👉 [**TAP HERE TO JOIN IN TESTFLIGHT**](${joinUrl})\n\n*(Direct Link: ${joinUrl})*`,
    color: isTest ? 3447003 : 5763719,
    fields: [
      { name: "App Name", value: appName, inline: true },
      { name: "Status", value: isTest ? "📡 24/7 Cloud Active" : "🟢 OPEN!", inline: true },
      { name: "Link ID", value: `\`${linkId}\``, inline: true }
    ],
    footer: {
      text: `Cloudflare 24/7 Worker • ${new Date().toISOString()}`
    }
  };

  if (iconUrl) {
    embed.thumbnail = { url: iconUrl };
  }

  const payload = {
    content: isTest 
      ? `✅ **Cloudflare 24/7 Monitor ONLINE** for **${appName}**!`
      : `@everyone 🚨 **TESTFLIGHT SLOT OPEN FOR ${appName.toUpperCase()}!** 🚨`,
    embeds: [embed]
  };

  await fetch(webhookUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}
