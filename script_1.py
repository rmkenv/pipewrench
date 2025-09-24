# Create requirements.txt file
requirements_content = """fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pymongo==4.6.0
redis==5.0.1
celery==5.3.4
anthropic==0.7.8
openai==1.3.7
langchain==0.1.0
langchain-community==0.0.10
langchain-openai==0.0.2
pinecone-client==2.2.4
weaviate-client==3.25.3
sentence-transformers==2.2.2
PyPDF2==3.0.1
python-docx==1.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
aiofiles==23.2.1
httpx==0.25.2
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
streamlit==1.28.2
gradio==4.8.0
requests==2.31.0
pandas==2.1.4
numpy==1.24.3
matplotlib==3.8.2
seaborn==0.13.0
plotly==5.17.0
jinja2==3.1.2
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0
"""

with open("knowledge_capture_mvp/requirements.txt", "w") as f:
    f.write(requirements_content)

print("requirements.txt created!")