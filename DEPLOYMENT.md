# 🚀 Render Deployment Guide for AutoXL

## ✅ Repository Status
- **GitHub URL**: https://github.com/Ameya-Bhingurde/llm-excel-mcp-server
- **Latest Commit**: Pushed successfully
- **Deployment Files**: ✅ Dockerfile, Procfile, render.yaml

---

## 📋 Deployment Steps

### 1. Go to Render Dashboard
Visit: https://dashboard.render.com/

### 2. Create New Web Service
- Click **"New +"** button (top right)
- Select **"Web Service"**

### 3. Connect Repository
- Click **"Connect account"** if needed
- Select **GitHub**
- Find and select: `Ameya-Bhingurde/llm-excel-mcp-server`
- Click **"Connect"**

### 4. Configure Service

Fill in the following settings:

| Setting | Value |
|---------|-------|
| **Name** | `autoxl` (or your preferred name) |
| **Region** | Select closest to you |
| **Branch** | `main` |
| **Root Directory** | (leave blank) |
| **Environment** | `Docker` |
| **Instance Type** | `Free` |

### 5. Advanced Settings (Optional)

Click **"Advanced"** and add environment variables:

| Key | Value |
|-----|-------|
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | `tinyllama` |

> **Note**: Ollama won't work on Render (local-only), but these prevent errors.

### 6. Deploy

- Click **"Create Web Service"**
- Wait for build (~5-10 minutes)
- Watch the logs for any errors

---

## 🎯 Post-Deployment

### Access Your App
Once deployed, you'll get a URL like:
```
https://autoxl.onrender.com
```

### Test Endpoints
```bash
# Health check
curl https://autoxl.onrender.com/health

# API docs
open https://autoxl.onrender.com/docs
```

---

## ⚠️ Important Limitations

### 1. **Ollama/LLM Features Won't Work**
- Render free tier doesn't support Ollama
- Smart Formula will fail (requires local LLM)
- **Solution**: Use external LLM API (OpenAI, Anthropic, etc.)

### 2. **Cold Starts**
- App spins down after 15 minutes of inactivity
- First request after idle: ~30-60 seconds
- **Solution**: Upgrade to paid plan or use cron-job.org to ping every 10min

### 3. **File Storage is Ephemeral**
- Uploaded files are lost on redeploy
- **Solution**: Use S3, Cloudinary, or similar

### 4. **Streamlit UI Won't Deploy**
- Render free tier: 1 web service = 1 port
- You can only deploy FastAPI backend
- **Solution**: Deploy Streamlit separately on Streamlit Cloud

---

## 🔧 Alternative: Deploy Streamlit UI

### Option A: Streamlit Cloud (Recommended)
1. Go to https://streamlit.io/cloud
2. Connect GitHub repo
3. Select `ui/app.py` as main file
4. Deploy (free)

### Option B: Modify for Render
Create separate `render-ui.yaml`:
```yaml
services:
  - type: web
    name: autoxl-ui
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run ui/app.py --server.port $PORT
```

---

## 📊 What Will Work on Render

| Feature | Status | Notes |
|---------|--------|-------|
| Health Check | ✅ Works | `/health` endpoint |
| API Docs | ✅ Works | `/docs` endpoint |
| Excel Upload | ✅ Works | Ephemeral storage |
| Data Analysis | ✅ Works | pandas operations |
| Pivot Tables | ✅ Works | No LLM needed |
| Data Cleanup | ✅ Works | No LLM needed |
| Smart Formula | ❌ Fails | Requires Ollama (local) |
| Visual Charts | ❌ N/A | Streamlit only |

---

## 🎯 Recommended Production Setup

### Architecture
```
┌─────────────────────┐
│  Streamlit Cloud    │ ← UI (free)
│  (ui/app.py)        │
└──────────┬──────────┘
           │ HTTP
           ▼
┌─────────────────────┐
│  Render Web Service │ ← API (free)
│  (FastAPI backend)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  OpenAI API         │ ← LLM (paid)
│  or Anthropic       │
└─────────────────────┘
```

### Steps
1. Deploy FastAPI to Render (backend)
2. Deploy Streamlit to Streamlit Cloud (UI)
3. Update `ui/app.py` to use Render URL:
   ```python
   API_BASE_URL = "https://autoxl.onrender.com"
   ```
4. Replace Ollama with OpenAI API in `app/llm_service.py`

---

## 🐛 Troubleshooting

### Build Fails
- Check Dockerfile syntax
- Ensure all dependencies in requirements.txt
- View logs in Render dashboard

### App Crashes
- Check environment variables
- View logs: Click "Logs" in Render dashboard
- Common issue: Missing `PORT` env var (Render sets this automatically)

### 502 Bad Gateway
- App is starting (cold start)
- Wait 30-60 seconds and retry
- Check health endpoint: `/health`

---

## 💡 Next Steps

1. **Deploy Backend**: Follow steps above
2. **Test API**: Use Postman or curl
3. **Deploy UI**: Use Streamlit Cloud
4. **Add LLM**: Integrate OpenAI/Anthropic API
5. **Add Storage**: Use S3 for file persistence

---

## 📞 Support

If deployment fails:
1. Check Render logs
2. Open GitHub issue: https://github.com/Ameya-Bhingurde/llm-excel-mcp-server/issues
3. Include error logs and screenshots

---

**Good luck with your deployment! 🚀**
