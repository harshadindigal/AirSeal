# AirSeal

**Automated Airgapping Dependency Packaging Tool**  
Easily package your code dependencies into a Docker image for secure, airgapped environments.

### Features
- **Currently Supports**: Python, Java, Javascript, Go, Rust 
- **Coming Soon**: Support for additional programming languages

---

### 🚀 Quick Start

1. **Clone the Repository**  
   `git clone https://github.com/harshadindigal/AirSeal`

2. **Set Up Your Virtual Environment**  
   - For macOS/Linux:
     `python3 -m venv venv`  
     `source venv/bin/activate`
   - For Windows:
     `python -m venv venv`  
     `venv\Scripts\activate`

3. **Install Dependencies**  
   `pip install -r requirements.txt`

4. **Configure Environment**  
   Create a `.env` file in the project root and add:  
   `DOCKER_BUILD_DIR=/path/to/temporary/build/directory`

5. **Run the Application**  
   - For **Streamlit** version:  
     `streamlit run app.py`
   - For **H2O Wave** version:  
     `wave run app2.py`

---

### 🛠 Development Scripts

- `dependency_analyzer.py`: Analyze and list project dependencies.
- `docker_builder.py`: Generate a Docker image with your dependencies.
- `app.py`: UI for users to upload their code/download docker image

---

### 📦 Usage Workflow

1. **Upload your Python file**
2. **View detected dependencies**
3. **Generate Docker image**
4. **Download or use the generated Docker image**

---

### ⚠️ Troubleshooting

- **Docker Issues**: Ensure Docker is running before executing commands.
- **Python Version**: Verify Python version 3.9+ is installed.
- **Dependency Problems**: Check the console output for any specific error messages related to dependencies or environment setup.

---

### 📋 Prerequisites

- Python 3.9+
- Docker
- pip
- git
