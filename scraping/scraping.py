from google_play_scraper import reviews, app, Sort
import pandas as pd
import time
import json

# Top aplikacije po kategorijama
APPS = {
    "com.spotify.music":           "Spotify",
    "com.instagram.android":       "Instagram",
    "com.whatsapp":                "WhatsApp",
    "com.netflix.mediaclient":     "Netflix",
    "com.google.android.youtube":  "YouTube",
    "com.discord":                 "Discord",
    "com.snapchat.android":        "Snapchat",
    "com.twitter.android":         "Twitter",
    "com.tiktok.android":          "TikTok",
    "com.facebook.katana":         "Facebook",
    "com.duolingo":                "Duolingo",
    "com.google.android.apps.maps":"Google Maps",
    "com.zoom.mantis":             "Zoom",
    "com.microsoft.teams":         "Microsoft Teams",
    "com.reddit.frontpage":        "Reddit",
    "com.linkedin.android":        "LinkedIn",
    "com.canva.editor":            "Canva",
    "com.paypal.android.p2pmobile":"PayPal",
    "com.booking":                 "Booking.com",
    "com.airbnb.android":          "Airbnb",
    "com.ubercab":                 "Uber",
    "com.shazam.android":          "Shazam",
    "com.amazon.mShop.android.shopping": "Amazon",
    "com.google.android.gm":       "Gmail",
    "com.twitter.android":         "Twitter",
}

COUNTRIES = ["us"]
REVIEWS_PER_APP = 10000

all_reviews = []

for package_id, app_name in APPS.items():
    for country in COUNTRIES:
        try:
            print(f"Scraping {app_name} [{country}]...")
            
            result, _ = reviews(
                package_id,
                lang="en",
                country=country,
                sort=Sort.NEWEST,
                count=REVIEWS_PER_APP,
            )
            
            for r in result:
                all_reviews.append({
                    "app_name":    app_name,
                    "package_id":  package_id,
                    "country":     country,
                    "rating":      r["score"],
                    "review_text": r["content"],
                    "thumbs_up":   r["thumbsUpCount"],
                    "app_version": r["reviewCreatedVersion"],
                    "timestamp":   r["at"].isoformat(),
                    "review_id":   r["reviewId"],
                })
            
            time.sleep(2)  # poštuj rate limit
            
        except Exception as e:
            print(f"Greška za {app_name} [{country}]: {e}")
            continue

# Sačuvaj
df = pd.DataFrame(all_reviews)
df.to_csv("google_play_reviews_raw.csv", index=False)
print(f"Skupljeno {len(df)} recenzija, veličina: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")