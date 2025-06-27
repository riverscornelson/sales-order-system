# Local Testing Guide

## Quick Start Testing

### 1. Environment Setup

First, set up your environment variables:

```bash
# Copy the example environment file
cd backend
cp .env.example .env

# Edit .env and add your OpenAI API key
# Replace REPLACE_WITH_YOUR_API_KEY with your actual key
nano .env
```

Your `.env` should look like:
```
ENVIRONMENT=development
DEBUG=true
OPENAI_API_KEY=sk-proj-your-actual-key-here
DATABASE_URL=sqlite:///./sales_orders.db
...
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Generate the parts database (this creates the SQLite database)
python generate_parts_database.py

# Test the secure database connection
python test_database_integration.py

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

In a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

### 4. Access the Application

Open your browser to: http://localhost:5173

## Testing Checklist

### ✅ Security Improvements
- [ ] **Environment Variables**: Backend starts without exposed API keys
- [ ] **Database Security**: No SQL injection errors in logs
- [ ] **Error Handling**: App doesn't crash on invalid inputs

### ✅ Architecture Improvements  
- [ ] **Component Loading**: All React components render without errors
- [ ] **Backend Modularity**: API endpoints respond correctly
- [ ] **WebSocket Connection**: Real-time updates work

### ✅ Performance Improvements
- [ ] **Fast Rendering**: No console warnings about slow renders
- [ ] **Memory Usage**: No memory leaks in browser dev tools
- [ ] **Database Performance**: Fast query responses

### ✅ User Interface Testing
- [ ] **File Upload**: Drag and drop works
- [ ] **Processing Status**: Cards update in real-time  
- [ ] **Error Boundaries**: Graceful error handling
- [ ] **Backend Status**: Connection indicator works

## Detailed Testing Steps

### Test 1: Basic Functionality
1. Upload a test document (PDF, TXT, or email)
2. Verify WebSocket connection (green indicator)
3. Watch processing cards update in real-time
4. Check that results are displayed correctly

### Test 2: Error Handling
1. Try uploading an invalid file type
2. Disconnect internet and test offline behavior
3. Verify error messages are user-friendly

### Test 3: Performance
1. Open browser DevTools → Performance tab
2. Upload a file and record performance
3. Check for console warnings about slow renders
4. Monitor memory usage during processing

### Test 4: Security
1. Check that no API keys appear in browser console
2. Verify database queries use parameterized inputs
3. Test that invalid inputs are rejected gracefully

## Expected Behavior

### Successful Upload Flow:
1. **File Upload** → Green checkmark, file details shown
2. **WebSocket Connection** → Real-time connection established  
3. **Document Processing** → Progress cards update automatically
4. **Semantic Search** → Part matches found and displayed
5. **Final Results** → Complete order processing results

### Performance Expectations:
- **Page Load**: < 2 seconds
- **Component Renders**: < 16ms (no warnings)
- **API Responses**: < 1 second for most operations
- **WebSocket Messages**: Real-time (< 100ms delay)

## Troubleshooting

### Backend Won't Start
```bash
# Check Python environment
python --version  # Should be 3.8+

# Check dependencies
pip install -r requirements.txt

# Check database
python test_database_integration.py
```

### Frontend Issues
```bash
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run type-check
```

### Database Issues
```bash
# Regenerate database
python generate_parts_database.py

# Test database directly
python test_local_database.py
```

### API Key Issues
- Verify your OpenAI API key is valid
- Check you have credits available
- Ensure no typos in the key

## Performance Monitoring

### Browser DevTools
1. **Console**: Should be free of errors and warnings
2. **Network**: API calls should complete quickly
3. **Performance**: No long tasks or memory leaks
4. **Application**: WebSocket connection should be stable

### Backend Logs
- Structured logs with clear information
- No SQL injection attempts logged
- Performance metrics for database queries
- WebSocket connection events

## Success Indicators

### ✅ Everything Working Correctly:
- Backend starts without configuration errors
- Frontend loads without TypeScript errors  
- File uploads process successfully
- Real-time updates work smoothly
- No security warnings in logs
- Fast, responsive user interface
- Graceful error handling

### 🔍 What to Look For:
- **Security**: No exposed secrets, parameterized queries
- **Performance**: Fast renders, efficient memory usage
- **Reliability**: Graceful error recovery, stable connections
- **Usability**: Intuitive interface, clear feedback