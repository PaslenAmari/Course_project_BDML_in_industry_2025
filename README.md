# Personalized Educational Assistant

**Course Project:** Machine Learning for Industrial Data (3rd Semester)

**Students:**
* Siraeva Gulnara [PaslenAmari](https://github.com/PaslenAmari)
* Levon Abramian
* Gaibaliev Emil
* [Gleb Mikloshevich](https://github.com/GlebMikloshevich)

**Instructions:**

To create docker use the following command:


**docker run -d --name kursach -p 27017:27017 mongo:6**


To launch docker use the following command:


**docker start kursach**

From the python terminal launch the ui:


**streamlit run src/ui/app.py**

The landing page:

![Titul](https://github.com/user-attachments/assets/32eb2736-256b-4b05-ac53-f3ffbf633f30)

### Personalized Learning Plan
![Curr](https://github.com/user-attachments/assets/48c9f33c-ef45-41a3-b863-1926b88ea9a2)

The theory:
<img width="1254" height="587" alt="image" src="https://github.com/user-attachments/assets/e0f1b0ab-37f7-4b7b-a985-b9f8adbf761d" />


### Interactive Exercises
<img width="1294" height="522" alt="image" src="https://github.com/user-attachments/assets/9c219091-9f19-43fe-a18b-d8045585a1da" />

### Level-Up Exams
<img width="1885" height="752" alt="image" src="https://github.com/user-attachments/assets/1939accc-e606-427d-aff4-7e0e48985055" />

### Language Selection
<img width="1310" height="366" alt="image" src="https://github.com/user-attachments/assets/115e5069-8153-4b05-b323-bb7892d85a55" />

---

## 🚀 Installation & Running

### Prerequisites
-   [Docker](https://www.docker.com/) and Docker Compose installed.
-   OR Python 3.10+ (for local manual run).

### Option 1: Docker (Recommended)
You can run the entire system (Database + API + UI) with a single command. This ensures all dependencies and the database are configured correctly.

1.  **Build and Run:**
    ```bash
    docker-compose up --build
    ```
2.  **Access Services:**
    *   **Web UI:** [http://localhost:8501](http://localhost:8501)
    *   **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

### Option 2: Manual Local Setup
If you want to run components individually for development:

1.  **Start MongoDB:**
    ```bash
    docker run -d --name kursach_mongo -p 27017:27017 mongo:6
    ```
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run API Backend:**
    ```bash
    uvicorn src.api.main:app --reload --port 8000
    ```
4.  **Run UI Frontend:**
    ```bash
    streamlit run src/ui/app.py
    ```

---

## 🛠️ Configuration
The system uses `python-dotenv` or environment variables for configuration. API keys (e.g., OpenAI, Anthropic) should be set in a `.env` file or passed via Docker environment variables if you are connecting to real LLMs (currently configured for mock/local execution).

```env
# Example .env
MONGODB_URL=mongodb://localhost:27017
OPENAI_API_KEY=sk-...
```

---

