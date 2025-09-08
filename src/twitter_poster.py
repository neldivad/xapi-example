import requests
import time
import json
from datetime import datetime
from dotenv import load_dotenv, find_dotenv
import os

# Load environment variables
load_dotenv(find_dotenv())

class TwitterPoster:
    def __init__(self):
        self.api_key = os.getenv("twitterapiio_key")
        if not self.api_key:
            raise RuntimeError("twitterapiio_key not set in environment")
        
        self.base_url = "https://api.twitterapi.io"
        self.login_cookies = None
        
        # Proxy configuration - update these with your actual proxy details
        self.proxy = {
            "http": os.getenv("PROXY_HTTP", "http://username:password@proxy_ip:port"),
            "https": os.getenv("PROXY_HTTP", "http://username:password@proxy_ip:port")  # Use same proxy for both
        }
        
        # Headers for API requests - TwitterAPI.io expects X-API-Key (capitalized)
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def login_simple(self, max_retries: int = 3) -> bool:
        """
        Smart login with retry logic and block handling
        """
        for attempt in range(max_retries):
            print(f"Login attempt {attempt + 1}/{max_retries}...")
            
            url = f"{self.base_url}/twitter/user_login_v2"
            payload = {
                "user_name": os.getenv("TWITTER_USERNAME"),
                "email": os.getenv("TWITTER_EMAIL"),
                "password": os.getenv("TWITTER_PASSWORD"),
                "proxy": self.proxy["http"],
                "totp_secret": os.getenv("TOTP_SECRET"),
            }
            
            try:
                response = requests.post(url, headers=self.headers, json=payload, proxies=self.proxy)
                response.raise_for_status()
                
                data = response.json()
                print(f"API Response: {data}")
                
                if data.get("status") == "success":
                    self.login_cookies = data.get("login_cookies")
                    if self.login_cookies:
                        print("✅ Login successful - Got login_cookies")
                        return True
                    else:
                        print("❌ Login succeeded but no cookies received")
                        return False
                else:
                    message = data.get('message', 'Unknown error')
                    print(f"❌ Login failed: {message}")
                    
                    # Handle specific block messages
                    if "blocked" in message.lower() or "wait" in message.lower():
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 60  # 1min, 2min, 3min
                            print(f"🔄 Account blocked. Waiting {wait_time} seconds before retry...")
                            print("💡 Try logging in normally on Twitter to unblock it!")
                            time.sleep(wait_time)
                            continue
                        else:
                            print("🚫 Max retries reached. Account still blocked.")
                            print("🔓 Manual steps to unblock:")
                            print("   1. Go to Twitter Settings > Security")
                            print("   2. Look for 'Login verification'")
                            print("   3. Click 'Yes, it's me' if prompted")
                            print("   4. Wait 15-30 minutes and try again")
                            return False
                    else:
                        return False
                        
            except requests.exceptions.RequestException as e:
                print(f"❌ Login error: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"🔄 Retrying in 30 seconds...")
                    time.sleep(30)
                    continue
                return False
        
        return False
    

    
    def post_tweet(self, text: str, reply_to_tweet_id: str = None, attachment_url: str = None) -> bool:
        """
        Post a tweet using the v2 API with login_cookies
        """
        if not self.login_cookies:
            print("❌ No login_cookies available. Complete authentication first.")
            return False
        
        print(f"Posting tweet: {text[:50]}...")
        
        url = f"{self.base_url}/twitter/create_tweet_v2"
        payload = {
            "login_cookies": self.login_cookies,
            "tweet_text": text,
            "proxy": self.proxy["http"]
        }
        
        # Optional parameters
        if reply_to_tweet_id:
            payload["reply_to_tweet_id"] = reply_to_tweet_id
        if attachment_url:
            payload["attachment_url"] = attachment_url
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, proxies=self.proxy)
            response.raise_for_status()
            
            data = response.json()
            print(f"Tweet API Response: {data}")  # Debug: see full response
            
            if data.get("status") == "success":
                print("✅ Tweet posted successfully!")
                return True
            else:
                print(f"❌ Tweet posting failed: {data.get('message', 'Unknown error')}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Tweet posting error: {str(e)}")
            return False
    


def main():
    """
    Example usage of the TwitterPoster class
    """
    print("🐦 Twitter API Poster - Programmatic Tweet Posting")
    print("=" * 50)
    
    # Initialize the poster
    try:
        poster = TwitterPoster()
    except RuntimeError as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    # Check if credentials are available
    username = os.getenv("TWITTER_USERNAME")
    email = os.getenv("TWITTER_EMAIL")
    password = os.getenv("TWITTER_PASSWORD")
    totp_secret = os.getenv("TOTP_SECRET")
    
    if not all([username, email, password, totp_secret]):
        print("❌ Missing credentials in .env file")
        print("Required: TWITTER_USERNAME, TWITTER_EMAIL, TWITTER_PASSWORD, TOTP_SECRET")
        return
    
    print(f"Using credentials for: @{username}")
    
    # Simple login
    if not poster.login_simple():
        print("❌ Authentication failed")
        return
    
    print("\n✅ Authentication successful! You can now post tweets.")
    
    # Interactive menu
    while True:
        print("\n" + "=" * 30)
        print("Choose an action:")
        print("1. Post a tweet")
        print("2. Post reply tweet")
        print("3. Post tweet with attachment")
        print("4. Exit")
        
        choice = input("Enter your choice (1-4): ").strip()
        
        if choice == "1":
            tweet_text = input("Enter your tweet text: ").strip()
            if tweet_text:
                poster.post_tweet(tweet_text)
        
        elif choice == "2":
            tweet_text = input("Enter your reply text: ").strip()
            reply_id = input("Enter tweet ID to reply to: ").strip()
            if tweet_text and reply_id:
                poster.post_tweet(tweet_text, reply_to_tweet_id=reply_id)
        
        elif choice == "3":
            tweet_text = input("Enter your tweet text: ").strip()
            attachment_url = input("Enter attachment URL: ").strip()
            if tweet_text and attachment_url:
                poster.post_tweet(tweet_text, attachment_url=attachment_url)
        
        elif choice == "4":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
