#!/usr/bin/env python3
"""
Simple test script to verify the backend starts properly
"""

if __name__ == "__main__":
    import uvicorn
    from app.main import app
    
    print("🚀 Starting backend server...")
    print("📍 Host: 127.0.0.1")
    print("🔌 Port: 8000")
    print("🌐 Access at: http://127.0.0.1:8000")
    print("📚 API docs: http://127.0.0.1:8000/docs")
    
    try:
        uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=8000, 
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc()