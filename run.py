import os
import uvicorn

if __name__ == "__main__":
    port = os.getenv("PORT")
    print("PORT VALUE =", port)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(port) if port else 8000
    )