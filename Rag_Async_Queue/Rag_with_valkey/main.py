import uvicorn
from dotenv import load_dotenv

load_dotenv()

def main():
    uvicorn.run("server:app", port=8000, host="0.0.0.0", reload=True)

if __name__ == "__main__":
    main()