# 🎯 TasteTarget - AI-Powered Cultural Intelligence Platform

TasteTarget is a B2B SaaS platform that helps brands and creators identify and target audiences using cultural intelligence instead of demographics. It generates taste-based customer personas and personalized marketing campaigns in seconds.

## 🚀 Features

- **Taste-Based Personas**: Generate detailed customer personas based on cultural interests and behaviors
- **AI-Powered Copy**: Get personalized taglines, social captions, and ad copy for each persona
- **Cultural Intelligence**: Leverage taste patterns across music, dining, travel, fashion, and more
- **Privacy-First**: No cookies, no personal data - only aggregated cultural patterns
- **Instant Results**: Complete campaign strategy in under 30 seconds
- **Export Options**: Download JSON data or formatted reports

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Streamlit
- **AI/LLM**: GPT-4 (OpenAI API)
- **Cultural Data**: Qloo API (mocked in demo)
- **Deployment**: Docker-ready

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- (Optional) Qloo API key for production use

## 🔧 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/tastetarget.git
cd tastetarget
```

### 2. Set up the Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your_api_key_here
```

### 3. Set up the Frontend

```bash
# Install frontend dependencies
pip install -r requirements-frontend.txt

# Create Streamlit secrets directory
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

## 🚀 Running the Application

### Start the Backend (Terminal 1)

```bash
# Activate virtual environment if not already active
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run FastAPI backend
python main.py
```

The backend will start at `http://localhost:8000`

### Start the Frontend (Terminal 2)

```bash
# In a new terminal, activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run Streamlit frontend
streamlit run app.py
```

The frontend will open automatically at `http://localhost:8501`

## 🎮 Quick Demo

1. Click on one of the demo buttons in the sidebar:
   - 🟢 **Eco Sneakers Demo**
   - ☕ **Artisan Coffee Demo**

2. Or enter your own product:
   - Product name
   - Description
   - Brand values
   - Target mood

3. Click **🚀 Generate Campaign**

4. Explore the results:
   - **Personas**: Detailed taste-based customer segments
   - **Campaign Copy**: Personalized messaging for each persona
   - **Suggestions**: Strategic recommendations
   - **Analytics**: Visual insights about your audience

## 📁 Project Structure

```
tastetarget/
├── main.py                 # FastAPI backend
├── app.py                  # Streamlit frontend
├── requirements.txt        # Backend dependencies
├── requirements-frontend.txt # Frontend dependencies
├── .env.example           # Environment variables template
├── .streamlit/
│   ├── config.toml        # Streamlit configuration
│   └── secrets.toml       # Streamlit secrets
└── README.md              # This file
```

## 🔌 API Endpoints

- `GET /` - Health check
- `POST /api/generate-targeting` - Generate personas and campaigns
- `GET /api/sample-personas` - Get sample personas

## 📝 API Request Format

```json
{
  "product_name": "EcoStride Sneakers",
  "product_description": "Zero-waste vegan sneakers made from recycled ocean plastic",
  "brand_values": ["sustainability", "innovation", "style"],
  "target_mood": ["conscious", "modern", "bold"],
  "campaign_tone": "balanced"
}
```

## 🔐 Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `QLOO_API_KEY` - Your Qloo API key (optional, uses mock data if not provided)
- `API_URL` - Backend API URL (default: http://localhost:8000)

## 🐳 Docker Deployment (Optional)

```bash
# Build Docker image
docker build -t tastetarget .

# Run container
docker run -p 8000:8000 -p 8501:8501 --env-file .env tastetarget
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📈 Business Model

- **Freemium**: Basic personas and copy for startups
- **Pro**: Advanced features, API access, unlimited generations
- **Enterprise**: Custom integrations, white-label options

## 🎯 Use Cases

- **Brands**: Discover new audience segments
- **Agencies**: Speed up campaign development
- **Creators**: Understand your audience better
- **Startups**: Professional marketing without the budget

## 🔧 Troubleshooting

### Backend won't start
- Check if port 8000 is already in use
- Verify your OpenAI API key is correct
- Ensure all dependencies are installed

### Frontend connection error
- Make sure the backend is running first
- Check if the API_URL in `.streamlit/secrets.toml` is correct
- Verify firewall settings allow local connections

### No results generated
- Verify your OpenAI API key has credits
- Check the backend logs for error messages
- Ensure your input is valid (non-empty fields)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built for the Qloo Hackathon
- Powered by OpenAI's GPT-4
- Cultural intelligence inspired by Qloo's Taste AI™

---

**Ready to revolutionize your marketing?** Start using TasteTarget today! 🚀