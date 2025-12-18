# Render Deployment Checklist - FastAPI Only

## ✅ Changes Made

1. **Removed Streamlit** from `requirements.txt` (API-only deployment)
2. **Added root endpoint** (`/`) to `app/main.py` to fix 404 errors
3. **Updated Dockerfile** to use `$PORT` environment variable
4. **Updated render.yaml** to use native Python runtime (faster than Docker)
5. **Procfile** already configured correctly

## 🚀 Deployment Steps

### 1. Commit and Push Changes
```bash
git add .
git commit -m "Configure for Render API-only deployment"
git push origin main
```

### 2. Render Dashboard Settings

**If using render.yaml (Blueprint):**
- Render will automatically read `render.yaml`
- Just connect your GitHub repo
- Click "Apply" to create the service

**If manually configuring:**
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/health`

### 3. Environment Variables (Optional)
Add these in Render dashboard if you want to customize:
- `OLLAMA_BASE_URL`: http://127.0.0.1:11434 (default)
- `OLLAMA_MODEL`: tinyllama (default)

## 🧪 Testing After Deployment

Once deployed, test these endpoints:

1. **Root endpoint** (should return API info):
   ```
   GET https://your-app.onrender.com/
   ```

2. **Health check**:
   ```
   GET https://your-app.onrender.com/health
   ```

3. **Analyze data** (requires Excel file in sample_files):
   ```
   POST https://your-app.onrender.com/mcp/analyze-data
   {
     "path": "sales_data_pivot_demo.xlsx",
     "sheet": "Sales"
   }
   ```

## 📝 API Endpoints Available

- `GET /` - API information
- `GET /health` - Health check
- `POST /mcp/clean-excel` - Clean Excel data
- `POST /mcp/analyze-data` - Analyze Excel structure
- `POST /mcp/create-pivot-table` - Create pivot tables
- `POST /mcp/insert-formula` - Insert formulas
- `POST /mcp/query-data` - Query data with natural language

## ⚠️ Known Limitations on Render Free Tier

1. **Service spins down after 15 minutes of inactivity**
   - First request after sleep takes ~50 seconds
   
2. **No persistent file storage**
   - Uploaded files are temporary
   - Files reset when service restarts
   
3. **750 hours/month free**
   - Enough for testing and demos

## 🔧 Troubleshooting

### If you still get 404 errors:
1. Check Render logs for startup errors
2. Verify the health check passes: `/health`
3. Ensure `PORT` environment variable is being used

### If dependencies fail to install:
1. Check `requirements.txt` for version conflicts
2. Look at build logs in Render dashboard
3. Try pinning specific versions

### If the app crashes on startup:
1. Check for missing environment variables
2. Verify `sample_files` directory exists
3. Check logs for Python import errors

## 📊 Next Steps After Successful Deployment

1. **Test all endpoints** using Postman or curl
2. **Document the API** using FastAPI's auto-generated docs at `/docs`
3. **Set up monitoring** (Render provides basic metrics)
4. **Consider upgrading** if you need:
   - Persistent storage
   - No cold starts
   - More compute resources

## 🎯 Current Configuration Summary

- **Runtime**: Python 3 (native, not Docker)
- **Framework**: FastAPI + Uvicorn
- **Port**: Dynamic (`$PORT` from Render)
- **Health Check**: `/health` endpoint
- **File Storage**: `sample_files/` directory (temporary)
- **Dependencies**: Minimal (no Streamlit, no Plotly)
