
# Blogger Google Indexing Automation

Automatically submit your Blogger posts to Google's Indexing API for faster search engine indexing. Perfect for technical blogs, AI/ML content creators, and anyone who wants their content discovered quickly.

## Key Features:
- 🎯 Automatic URL discovery from Blogger RSS feeds
- ⚡ Smart rate limiting to respect API quotas
- 🔄 Intelligent reindexing of older content
- 📊 Progress tracking and state management
- 🤖 Fully automated via GitHub Actions
- 📝 Comprehensive logging and error handling
- 💾 Persistent storage of indexed URLs
- 🛡️ Handles API errors gracefully


## Setup

### 1. Google Cloud Setup

1. Create a new project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable the Indexing API
3. Create a service account with "Owner" role
4. Download the JSON key file

### 2. Google Search Console Setup

1. Add your service account email to Search Console as an owner
2. Email format: `service-account@project-id.iam.gserviceaccount.com`

### 3. GitHub Setup

1. Fork this repository
2. Go to Settings → Secrets and variables → Actions
3. Add secrets:
   - `GOOGLE_SERVICE_ACCOUNT_KEY`: Base64 encoded service account JSON
4. Add variables:
   - `BLOGGER_RSS_FEED`: Your blog's RSS feed URL
   - `BLOG_URL`: Your blog's main URL
   - `MAX_REQUESTS_PER_DAY`: 200 (or your quota)

### 4. Local Setup (Optional)

```bash
# Clone the repository
git clone https://github.com/yourusername/blogger-indexing-automation.git
cd blogger-indexing-automation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your settings
# Add your service account JSON file to the project

# Run manually
python src/indexer.py




Built by Dr. Carlos Ruiz Viquez for the AI & Machine Learning community.
